# utils/resource_cleaner.py

import psutil
import os
import signal
from utils.anomaly_detector import is_critical_process # is_critical_process'i import ediyoruz
from routes.logs import log_info, log_warning, log_error # Loglama fonksiyonlarını import ediyoruz
import getpass # current_user için

def clean_ram():
    threshold = 20.0  # %20'den fazla RAM kullananlar kapatılacak
    killed = []
    skipped = []
    current_user = getpass.getuser() # Mevcut kullanıcıyı alıyoruz

    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cmdline', 'username']):
        try:
            # Önce RAM eşiğini kontrol et
            if proc.info['memory_percent'] > threshold:
                proc_name = proc.info.get('name', '')
                proc_pid = proc.info.get('pid', 'N/A')
                proc_cmdline = proc.info.get('cmdline', [])
                proc_username = proc.info.get('username', '')

                # 1. Kendi uygulamasını sonlandırmayı engelle
                if proc_pid == os.getpid():
                    skipped.append(f"{proc_name} (PID: {proc_pid}) - Kendi Uygulamamız")
                    log_warning(f"RAM Temizle: Kendi uygulamamız ({proc_name}) sonlandırma isteği atlandı.")
                    continue

                # 2. Kritik sistem süreçlerini atla
                if is_critical_process(process_name=proc_name, cmdline=proc_cmdline, username=proc_username):
                    skipped.append(f"{proc_name} (PID: {proc_pid}) - Kritik Sistem Süreci")
                    log_warning(f"RAM Temizle: Kritik sistem süreci ({proc_name}) sonlandırma isteği atlandı.")
                    continue

                # 3. Sadece mevcut kullanıcının çalıştırdığı işlemleri hedefle (root veya farklı kullanıcılar için kapatmayı engelle)
                # Bu kuralı çok dikkatli düşünün. Eğer sunucuyu sadece kendi kullanıcınızla yönetiyorsanız mantıklıdır.
                # Ancak farklı servisler farklı kullanıcılar altında çalışıyorsa, onları yönetemeyebilirsiniz.
                # Şimdilik güvenli bir yaklaşım olarak kendi kullanıcınızın süreçlerini hedefleyelim.
                if proc_username == current_user:
                    try:
                        target_proc = psutil.Process(proc_pid)
                        target_proc.terminate() # Önce nazikçe terminate
                        target_proc.wait(timeout=3) # 3 saniye bekle
                        killed.append(f"{proc_name} (PID: {proc_pid}) - %{proc.info['memory_percent']:.1f}")
                        log_info(f"RAM Temizle: Sonlandırıldı: {proc_name} (PID: {proc_pid}) - %{proc.info['memory_percent']:.1f}")
                    except psutil.NoSuchProcess:
                        skipped.append(f"{proc_name} (PID: {proc_pid}) - Zaten Sonlanmış")
                        log_info(f"RAM Temizle: Process '{proc_name}' zaten sonlanmış.")
                    except psutil.AccessDenied:
                        skipped.append(f"{proc_name} (PID: {proc_pid}) - Erişim Reddedildi")
                        log_error(f"RAM Temizle: Process '{proc_name}' (PID: {proc_pid}) için erişim reddedildi. Yetki sorunu olabilir.")
                    except psutil.TimeoutExpired:
                        try:
                            target_proc.kill() # 3 saniye içinde kapanmazsa zorla kapat
                            killed.append(f"{proc_name} (PID: {proc_pid}) - %{proc.info['memory_percent']:.1f} [Force Killed]")
                            log_warning(f"RAM Temizle: Zorla sonlandırıldı: {proc_name} (PID: {proc_pid}) - %{proc.info['memory_percent']:.1f}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            skipped.append(f"{proc_name} (PID: {proc_pid}) - Zorla Kapatılamadı / Erişilemiyor")
                            log_error(f"RAM Temizle: Process '{proc_name}' (PID: {proc_pid}) zorla kapatılamadı veya erişilemiyor.")
                else:
                    skipped.append(f"{proc_name} (PID: {proc_pid}) - Farklı Kullanıcı ({proc_username})")
                    log_warning(f"RAM Temizle: Process '{proc_name}' (PID: {proc_pid}) farklı kullanıcı '{proc_username}' tarafından çalıştırıldığı için atlandı.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            # Sürecin zaten kapanmış olması veya izin olmaması durumu (döngü sırasında)
            log_warning(f"RAM Temizle: Process iterasyonunda hata: {e} - PID: {proc.pid if 'proc' in locals() else 'N/A'}")
            continue
        except Exception as e:
            # Diğer beklenmedik hatalar
            log_error(f"RAM Temizle: Beklenmedik hata oluştu: {e} - Process: {proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'})")
            skipped.append(f"{proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'}) - Hata: {str(e)}")
            continue

    msg_parts = []
    if killed:
        msg_parts.append(f"✅ RAM temizlendi. Kapatılanlar: " + ", ".join(killed))
    if skipped:
        msg_parts.append(f"⚠️ Atlananlar: " + ", ".join(skipped))
    if not msg_parts:
        msg_parts.append("✅ Kapatılacak işlem yok.")
    
    return "<br>".join(msg_parts) # HTML'e uygun şekilde birleştiriyoruz