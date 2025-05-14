import psutil
import subprocess
import os

def clean_disk(aggressive=False):
    before = psutil.disk_usage('/').free

    try:
        subprocess.run(["find", "/tmp", "-type", "f", "-delete"], check=True)
        subprocess.run(["find", "/tmp", "-type", "d", "-empty", "-delete"], check=True)
    except Exception as e:
        print("TMP temizliği hatası:", e)

    if aggressive:
        try:
            subprocess.run(["journalctl", "--vacuum-size=100M"], check=True)
        except Exception as e:
            print("Journal temizliği hatası:", e)

        try:
            subprocess.run(["apt-get", "clean"], check=True)
            subprocess.run(["apt-get", "autoclean"], check=True)
        except Exception as e:
            print("APT temizliği hatası:", e)

    after = psutil.disk_usage('/').free
    freed_space = (after - before) / (1024 * 1024)
    return round(freed_space, 2)
