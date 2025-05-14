
import psutil
import os
import subprocess
from utils.logger import log_event

def clean_ram(top_n=3):
    log_event("🔍 RAM kontrolü başlatıldı.")
    processes = [(p.pid, p.info['name'], p.info['memory_info'].rss)
                 for p in psutil.process_iter(['name', 'memory_info']) if p.info['memory_info']]
    processes.sort(key=lambda x: x[2], reverse=True)

    for pid, name, memory in processes[:top_n]:
        try:
            log_event(f"⚠️ Yüksek RAM kullanan işlem: {name} (PID: {pid}) - {memory / (1024 ** 2):.2f} MB")
            # İsteğe bağlı olarak sonlandır:
            # psutil.Process(pid).terminate()
        except Exception as e:
            log_event(f"Hata RAM işleminde: {e}", level="error")

def clean_disk():
    log_event("🧹 Disk temizliği başlatıldı.")
    try:
        # Geçici dosyaları temizleme
        os.system("rm -rf /tmp/*")
        os.system("rm -rf ~/.cache/*")
        os.system("sudo apt-get clean")

        # Disk kullanımını göster
        usage = psutil.disk_usage('/')
        log_event(f"💾 Disk kullanımı: {usage.percent}%")

    except Exception as e:
        log_event(f"Hata disk temizliğinde: {e}", level="error")

if __name__ == "__main__":
    clean_ram()
    clean_disk()
