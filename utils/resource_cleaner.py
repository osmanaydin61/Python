
import psutil
import os
import subprocess
from utils.logger import log_event
import time
def clean_ram():
    # RAM temizleme simülasyonu
    before = psutil.virtual_memory().available
    time.sleep(1)  # Simülasyon
    after = psutil.virtual_memory().available
    freed = max((after - before) / (1024*1024), 0)
    return round(freed, 2)


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
