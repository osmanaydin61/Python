# utils/anomaly_detector.py (Sadece Eşik Değerlerine Göre Çalışan Sadeleştirilmiş Hali)

import matplotlib
import pandas as pd
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import psutil
from flask import current_app

# DOĞRU IMPORT'LAR
from extensions import db
from models import Metric

ANOMALY_DIR = 'static/anomalies'
os.makedirs(ANOMALY_DIR, exist_ok=True)

# Kritik süreçleri tanımlayan listeler (değişiklik yok)
SYSTEM_PROCESS_KEYWORDS = [
    "systemd", "kernel", "init", "kthreadd", "dbus", "gnome", "kde", "Xorg",
    "pulseaudio", "udev", "rsyslog", "crond", "sshd", "nginx", "apache2",
    "mysqld", "postgres", "mongod", "docker", "containerd", "polkitd", "bash", "chronyd"
]
SYSTEM_USERNAMES = ["root"]

def is_critical_process(process_name=None, cmdline=None, username=None):
    if username in SYSTEM_USERNAMES:
        return True
    if process_name and "python" in process_name.lower():
        if cmdline and "panel.py" in " ".join(cmdline):
            return True
    check_string = (process_name or "").lower() + " " + (" ".join(cmdline or [])).lower()
    return any(keyword in check_string for keyword in SYSTEM_PROCESS_KEYWORDS)

def get_top_processes_str(metric='cpu', limit=5):
    try:
        key = 'cpu_percent' if metric == 'cpu' else 'memory_percent'
        procs = sorted(psutil.process_iter(['name', key]), key=lambda p: p.info.get(key, 0), reverse=True)
        return ', '.join([f"{p.info.get('name', 'N/A')}({p.info.get(key, 0):.1f}%)" for p in procs[:limit]])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "N/A"
    return ''

def get_top_offending_process(metric='cpu'):
    try:
        sort_key = 'cpu_percent' if metric == 'cpu' else 'memory_percent'
        procs = sorted(psutil.process_iter(['pid', 'name', 'username', 'cmdline', sort_key]), key=lambda p: p.info.get(sort_key, 0), reverse=True)
        for p in procs:
            if not is_critical_process(p.info.get('name'), p.info.get('cmdline'), p.info.get('username')):
                return {'pid': p.info['pid'], 'name': p.info.get('name')}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return {'pid': None, 'name': None}

# --- ANA FONKSİYON (SADELEŞTİRİLMİŞ) ---
def detect_and_log_anomaly(cpu_val, ram_val, disk_val):
    """Sadece eşik değerlerine göre anomali tespiti yapar."""
    
    anomaly_type = None
    offending_process = {'pid': None, 'name': None}

    # Ayarlar sayfasından alınan eşik değerlerini kontrol et
    if cpu_val > current_app.config.get('CPU_THRESHOLD', 90):
        anomaly_type = 'Eşik - CPU Anomalisi'
        offending_process = get_top_offending_process('cpu')
    elif ram_val > current_app.config.get('RAM_THRESHOLD', 90):
        anomaly_type = 'Eşik - RAM Anomalisi'
        offending_process = get_top_offending_process('ram')
    elif disk_val > current_app.config.get('DISK_THRESHOLD', 95):
        anomaly_type = 'Eşik - Disk Anomalisi'
        # Disk anomalisinde genellikle belirli bir işlem olmaz

    # Eğer bir anomali bulunduysa (anomaly_type boş değilse)
    if anomaly_type:
        now = datetime.now(ZoneInfo("Europe/Istanbul"))
        filename = f"anomaly_{now.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(ANOMALY_DIR, filename)

        # Grafik oluşturma
        # Geçmiş verileri sadece grafik çizimi için çekiyoruz
        recent_metrics = db.session.query(Metric.cpu_percent, Metric.ram_percent, Metric.disk_percent).order_by(Metric.timestamp.desc()).limit(30).all()
        recent_metrics.reverse()
        
        # DataFrame oluştur
        df_plot = pd.DataFrame(recent_metrics, columns=['cpu_percent', 'ram_percent', 'disk_percent'])
        current_df = pd.DataFrame([{'cpu_percent': cpu_val, 'ram_percent': ram_val, 'disk_percent': disk_val}])
        df_plot = pd.concat([df_plot, current_df], ignore_index=True)
        
        plt.figure(figsize=(10, 5))
        plt.plot(df_plot.index, df_plot['cpu_percent'], label='CPU (%)', color='red', marker='.')
        plt.plot(df_plot.index, df_plot['ram_percent'], label='RAM (%)', color='blue', marker='.')
        plt.plot(df_plot.index, df_plot['disk_percent'], label='Disk (%)', color='green', marker='.')
        plt.axvline(x=len(df_plot)-1, color='black', linestyle='--', label=f'Anomali Anı')
        plt.title(f"Anomali Tespiti - {now.strftime('%Y-%m-%d %H:%M:%S')} ({anomaly_type})")
        plt.ylabel("Kullanım %")
        plt.xlabel("Zaman (Önceki Kayıtlar -> Şimdiki)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()

        return {
            'is_anomaly': True,
            'anomaly_type': anomaly_type,
            'pid': offending_process['pid'],
            'process_name': offending_process['name'],
            'top_cpu_processes': get_top_processes_str('cpu'),
            'top_ram_processes': get_top_processes_str('ram'),
            'anomaly_image': filename
        }
        
    return None # Anomali yoksa None döndür