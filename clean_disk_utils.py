
import psutil
import os
import subprocess

def clean_disk():
    before = psutil.disk_usage('/').free

    # Güvenli /tmp temizliği
    try:
        subprocess.run("sudo find /tmp -type f -delete", shell=True, check=True)
        subprocess.run("sudo find /tmp -type d -empty -delete", shell=True, check=True)
    except Exception as e:
        print("TMP temizliği hatası:", e)

    # Journal loglarını küçült
    try:
        subprocess.run("sudo journalctl --vacuum-size=100M", shell=True, check=True)
    except Exception as e:
        print("Journal temizliği hatası:", e)

    # apt cache temizliği
    try:
        subprocess.run("sudo apt-get clean", shell=True, check=True)
        subprocess.run("sudo apt-get autoclean", shell=True, check=True)
    except Exception as e:
        print("APT temizliği hatası:", e)

    after = psutil.disk_usage('/').free

    # Açılan alan hesapla (MB)
    freed_space = (after - before) / (1024 * 1024)
    return round(freed_space, 2)
