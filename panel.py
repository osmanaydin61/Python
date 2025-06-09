# panel.py

import os
from dotenv import load_dotenv
load_dotenv()
import time
import threading
import pandas as pd
import logging
import getpass
import psutil
from flask_wtf.csrf import CSRFProtect
from flask import Flask, jsonify, request, redirect, url_for, current_app # current_app'i import edin
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from routes.network import get_network_page, get_network_content
from routes.logs import get_logs_page, get_logs_content,log_info
from utils.resource_cleaner import clean_ram
from utils.clean_disk_utils import clean_disk
from cloudwatch.CloudWatch import send_email_alert
from utils.anomaly_detector import detect_and_log_anomaly, is_critical_process # is_critical_process'i import ediyoruz
from routes.history import history_routes

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'
app.config.from_object('config.Config')
csrf = CSRFProtect(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Blueprint kayıtları
app.register_blueprint(auth_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(settings_routes)
app.register_blueprint(anomaly_routes)
app.register_blueprint(tavsiye_routes)
app.register_blueprint(history_routes)
# Global veriler
anomaly_records = []
metrics = {"cpu": 0, "ram": 0, "disk": 0}

# Arka planda metrik toplama
def background_thread():
    global metrics, anomaly_records
    # Uygulama bağlamı oluşturun
    with app.app_context(): # <-- BU SATIRI EKLEYİN
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            metrics = {"cpu": cpu, "ram": ram, "disk": disk}
            anomaly_result = detect_and_log_anomaly(cpu, ram, disk)
            
            if anomaly_result and anomaly_result['anomaly'] == -1: 
                anomaly_records.append(anomaly_result)
                log_info(f"Anomali tespit edildi: CPU:{cpu:.1f}%, RAM:{ram:.1f}%, Disk:{disk:.1f}% - Tip: {anomaly_result['anomaly_type']}")

                # Otomatik Müdahale (Aggressive Mode) kontrolü
                # Bu satır artık uygulama bağlamı içinde çalışacak
                if current_app.config.get('AGGRESSIVE_MODE', False): 
                    log_info("Otomatik Müdahale modu aktif. Anomali için otomatik temizlik deneniyor...")
                    
                    clean_ram_result = clean_ram()
                    log_info(f"Otomatik RAM Temizliği Sonucu: {clean_ram_result}")
                    clean_disk_result = clean_disk()
                    log_info(f"Otomatik Disk Temizliği Sonucu: {clean_disk_result}")
                else:
                    log_info("Otomatik Müdahale modu pasif. Temizlik yapılmadı.")


            time.sleep(2)


# İşlem sonlandırma
@app.route("/killprocess", methods=["POST"])
@login_required
@roles_required("admin")
def kill_process():
    process_name = request.form.get("process")
    if not process_name:
        log_info("Kill Process: İşlem adı bulunamadı.")
        return jsonify({"message": "❌ İşlem adı bulunamadı."})
    
    current_user = getpass.getuser()
    killed = []
    skipped = []
    
    target_process_name_lower = process_name.lower()

    for proc in psutil.process_iter(["pid", "name", "cmdline", "username"]):
        try:
            proc_cmdline = " ".join(proc.info.get("cmdline", [])).lower()
            proc_name_lower = proc.info.get("name", "").lower()
            
            is_target_process = target_process_name_lower in proc_name_lower or \
                                (target_process_name_lower != "python" and target_process_name_lower in proc_cmdline)

            if is_target_process:
                if proc.pid == os.getpid():
                    skipped.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - Kendi Uygulamamız")
                    log_warning(f"Kill Process: Kendi uygulamamız ({proc.info['name']}) sonlandırma isteği atlandı.")
                    continue

                if is_critical_process(process_name=proc_name_lower, cmdline=proc.info.get('cmdline', []), username=proc.info.get('username', '')):
                    skipped.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - Kritik Sistem Süreci")
                    log_warning(f"Kill Process: Kritik sistem süreci ({proc_name_lower}) sonlandırma isteği atlandı.")
                    continue

                if proc.info.get("username") == current_user:
                    try:
                        target_proc = psutil.Process(proc.pid) 
                        target_proc.terminate()            
                        target_proc.wait(timeout=3)       
                        killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                        log_info(f"Process sonlandırıldı: {proc.info['name']} (PID: {proc.info['pid']})")
                    except psutil.NoSuchProcess:
                        skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Zaten Sonlanmış")
                        log_info(f"Kill Process: Process '{proc.info['name']}' zaten sonlanmış.")
                    except psutil.AccessDenied:
                        skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Erişim Reddedildi")
                        log_error(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) için erişim reddedildi. Yetki sorunu olabilir.")
                    except psutil.TimeoutExpired:
                        try:
                            target_proc.kill() 
                            killed.append(f"{proc.info['name']} (PID: {proc.pid}) [Force Killed]")
                            log_info(f"Process zorla sonlandırıldı: {proc.info['name']} (PID: {proc.pid})")
                        except psutil.NoSuchProcess:
                            skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Zaten Sonlanmış (Timeout sonrası)")
                            log_info(f"Kill Process: Process '{proc.info['name']}' zaten sonlanmış (Timeout sonrası).")
                        except psutil.AccessDenied:
                            skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Erişim Reddedildi (Kill)")
                            log_error(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) için kill erişimi reddedildi. Yetki sorunu olabilir.")
                else:
                    skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Farklı Kullanıcı ({proc.info.get('username', 'Bilinmiyor')})")
                    log_warning(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) farklı kullanıcı '{proc.info.get('username', 'Bilinmiyor')}' tarafından çalıştırıldığı için atlandı.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            log_error(f"Kill Process: Process listeleme sırasında hata: {e} - PID: {proc.pid if 'proc' in locals() else 'N/A'}")
            continue
        except Exception as e:
            log_error(f"Kill Process: Beklenmedik hata: {e} - Process: {proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'})")
            skipped.append(f"{proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'}) - Hata: {str(e)}")
            continue

    if os.path.exists("metrics_history.csv"):
        df = pd.read_csv("metrics_history.csv")
        df_original_len = len(df)
        df = df[~df['top_cpu_processes'].str.contains(process_name, na=False)]
        if len(df) < df_original_len:
            df.to_csv("metrics_history.csv", index=False)
            log_info(f"'{process_name}' içeren anomali kayıtları CSV'den temizlendi.")
        else:
            log_warning(f"CSV'den '{process_name}' içeren anomali kaydı bulunamadı/silinemedi.")

    msg_parts = []
    if killed:
        msg_parts.append(f"✅ Sonlandırıldı: {', '.join(map(str, killed))}")
    if skipped:
        msg_parts.append(f"⚠️ Atlandı: {', '.join(map(str, skipped))}")
    if not msg_parts:
        msg_parts.append("❌ Eşleşen süreç bulunamadı veya sonlandırılamadı.")
        log_info(f"Kill Process: '{process_name}' için eşleşen süreç bulunamadı veya sonlandırılamadı.")

    return jsonify({"message": "<br>".join(msg_parts)})


# RAM temizleme
@app.route("/clean")
@login_required
@roles_required("admin")
def clean():
    result = clean_ram()
    log_info(result)
    return result

# Disk temizleme
@app.route("/disktemizle")
@login_required
@roles_required("admin")
def disktemizle():
    result = clean_disk()
    log_info(result)
    return result

# panel.py (/testmail route'u için önerilen düzeltme)
@app.route("/testmail")
@login_required
def testmail():
    try:
        test_recipient = os.getenv("ADMIN_USER_EMAIL")
        if not test_recipient:
            return "<p>❌ Test alıcı e-postası yapılandırılmamış.</p><a href='/'>⬅ Geri dön</a>"

        from cloudwatch.CloudWatch import send_email_alert 
        send_email_alert(test_recipient, "🔔 Panelden Test Mail", "Bu bir test mesajıdır.")
        return "<p>✅ Test mail gönderildi.</p><a href='/'>⬅ Geri dön</a>"
    except Exception as e:
        return f"<p>❌ Mail gönderilemedi: {str(e)}</p><a href='/'>⬅ Geri dön</a>"
# Metrikler (JSON)
@app.route("/metrics")
def get_metrics():
    return jsonify(metrics)

# Context
@app.context_processor
def inject_helpers():
    import random
    return dict(random=random.random, zip=zip)

@app.context_processor
def inject_random():
    import random
    return dict(random=random.random)

@app.route("/logs")
@login_required
def logs_page():
    return get_logs_page()

@app.route("/getlogs")
@login_required
def get_logs():
    return get_logs_content()
@app.route("/network")
@login_required
def network():
    return get_network_page()

@app.route("/getnetwork")
@login_required
def getnetwork():
    return get_network_content()
# Çalıştır
if __name__ == "__main__":
    threading.Thread(target=background_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, debug=True)