# utils/anomaly_detector.py (Yeniden Düzenlenmiş, Verimli ve Modüler Hali)

import matplotlib
import pandas as pd
from sklearn.ensemble import IsolationForest
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import psutil
from flask import current_app

# Gerekli importlar
from extensions import db
from models import Metric, Setting

# --- SABİTLER ---
ANOMALY_DIR = 'static/anomalies'
os.makedirs(ANOMALY_DIR, exist_ok=True)

# Kritik olarak kabul edilen ve sonlandırılmayacak sistem süreçleri
SYSTEM_PROCESS_KEYWORDS = [
    "systemd", "kernel", "init", "kthreadd", "dbus", "gnome", "kde", "Xorg",
    "pulseaudio", "udev", "rsyslog", "crond", "sshd", "nginx", "apache2",
    "mysqld", "postgres", "mongod", "docker", "containerd", "polkitd", "bash", 
    "chronyd", "sd-pam"
]
SYSTEM_USERNAMES = ["root"]


# --- YARDIMCI FONKSİYONLAR (İŞLEM YÖNETİMİ) ---

def is_critical_process(p_info: dict) -> bool:
    """Bir işlemin, verilen bilgilere göre kritik olup olmadığını kontrol eder."""
    if not p_info:
        return True
    
    # Sistemin kendisi veya uygulamanın kendisi kritik kabul edilir
    if p_info.get('username') in SYSTEM_USERNAMES:
        return True
    if p_info.get('name') and "python" in p_info.get('name', '').lower():
        if p_info.get('cmdline') and "panel.py" in " ".join(p_info.get('cmdline', [])):
            return True
            
    check_string = (p_info.get('name') or "").lower() + " " + (" ".join(p_info.get('cmdline') or [])).lower()
    return any(keyword in check_string for keyword in SYSTEM_PROCESS_KEYWORDS)

def _get_process_snapshot() -> tuple[list, list]:
    """
    Sistemdeki işlemleri SADECE BİR KEZ tarar ve hem CPU hem de RAM'e göre
    sıralanmış iki ayrı liste olarak döndürür. Bu, performansı artırır.
    """
    procs_info = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            procs_info.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    sorted_by_cpu = sorted(procs_info, key=lambda p: p.get('cpu_percent', 0), reverse=True)
    sorted_by_ram = sorted(procs_info, key=lambda p: p.get('memory_percent', 0), reverse=True)
    return sorted_by_cpu, sorted_by_ram

def get_top_processes_str(sorted_procs: list, key: str, limit=5, min_threshold=1.0) -> str:
    """Verilen sıralanmış işlem listesinden, eşiği aşanları formatlayarak metin oluşturur."""
    significant_procs = [p for p in sorted_procs if p.get(key, 0) > min_threshold]
    if not significant_procs:
        return "Kayda değer bir işlem bulunamadı."
        
    top_procs = significant_procs[:limit]
    return ', '.join([f"{p.get('name', 'N/A')}({p.get(key, 0):.1f}%)" for p in top_procs])

def get_top_offending_process(sorted_procs: list) -> dict:
    """Verilen sıralanmış listedeki ilk kritik olmayan işlemi bulur."""
    for p_info in sorted_procs:
        if not is_critical_process(p_info):
            return {'pid': p_info.get('pid'), 'name': p_info.get('name')}
    return {'pid': None, 'name': None}


# --- YARDIMCI FONKSİYONLAR (ANOMALİ TESPİTİ VE RAPORLAMA) ---

def _run_ml_detection(cpu_val, ram_val, disk_val) -> bool:
    """Isolation Forest modelini çalıştırır ve anomali olup olmadığını döndürür."""
    min_samples = current_app.config.get('MIN_SAMPLES_FOR_ML_CONFIG', 100)
    recent_metrics = Metric.query.order_by(Metric.timestamp.desc()).limit(min_samples).all()
    
    if len(recent_metrics) < min_samples:
        return False # Yeterli veri yoksa anomali tespiti yapma

    df = pd.DataFrame([(m.cpu_percent, m.ram_percent, m.disk_percent) for m in recent_metrics], columns=['cpu', 'ram', 'disk'])
    
    contamination_setting = Setting.query.filter_by(key='ANOMALY_CONTAMINATION').first()
    contamination = float(contamination_setting.value) if contamination_setting else 0.05
    
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(df)
    
    prediction = model.predict(pd.DataFrame([[cpu_val, ram_val, disk_val]], columns=['cpu', 'ram', 'disk']))
    return prediction[0] == -1

def _run_threshold_detection(cpu_val, ram_val, disk_val) -> str | None:
    """Eşik değerlerine göre anomali tespiti yapar ve anomali tipini döndürür."""
    if cpu_val > current_app.config.get('CPU_THRESHOLD', 90):
        return 'Eşik - CPU Anomalisi'
    if ram_val > current_app.config.get('RAM_THRESHOLD', 90):
        return 'Eşik - RAM Anomalisi'
    if disk_val > current_app.config.get('DISK_THRESHOLD', 95):
        return 'Eşik - Disk Anomalisi'
    return None

def _create_anomaly_plot(filepath: str, anomaly_type: str, cpu_val, ram_val, disk_val):
    """Verilen bilgilere göre anomali grafiğini oluşturur ve kaydeder."""
    recent_metrics = db.session.query(Metric.cpu_percent, Metric.ram_percent, Metric.disk_percent).order_by(Metric.timestamp.desc()).limit(30).all()
    recent_metrics.reverse()
    
    df_plot = pd.DataFrame(recent_metrics, columns=['cpu_percent', 'ram_percent', 'disk_percent'])
    current_df = pd.DataFrame([{'cpu_percent': cpu_val, 'ram_percent': ram_val, 'disk_percent': disk_val}])
    df_plot = pd.concat([df_plot, current_df], ignore_index=True)
    
    plt.figure(figsize=(10, 5))
    plt.plot(df_plot.index, df_plot['cpu_percent'], label='CPU (%)', color='red', marker='.')
    plt.plot(df_plot.index, df_plot['ram_percent'], label='RAM (%)', color='blue', marker='.')
    plt.plot(df_plot.index, df_plot['disk_percent'], label='Disk (%)', color='green', marker='.')
    plt.axvline(x=len(df_plot)-1, color='black', linestyle='--', label='Anomali Anı')
    plt.title(f"Anomali Tespiti ({anomaly_type})")
    plt.ylabel("Kullanım %")
    plt.xlabel("Zaman")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()


# --- ANA FONKSİYON ---

def detect_and_log_anomaly(cpu_val, ram_val, disk_val) -> dict | None:
    """
    Ana anomali tespit fonksiyonu. Ayarlara göre doğru yöntemi seçer,
    tespit yapar ve gerekirse rapor oluşturur.
    """
    anomaly_type = None
    detection_method = 'threshold'
    if detection_method == 'ml':
        if _run_ml_detection(cpu_val, ram_val, disk_val):
            anomaly_type = 'ML - Isolation Forest Anomalisi'
    else: 
        anomaly_type = _run_threshold_detection(cpu_val, ram_val, disk_val)

    # Eğer bir anomali tespit edildiyse, raporlama işlemlerini yap
    if not anomaly_type:
        return None

    # Anomali varsa, işlemleri SADECE BİR KEZ tara
    procs_by_cpu, procs_by_ram = _get_process_snapshot()
    
    # Suçlu işlemi bul
    if 'CPU' in anomaly_type or ('ML' in anomaly_type and cpu_val > ram_val):
        offending_process = get_top_offending_process(procs_by_cpu)
    elif 'RAM' in anomaly_type or 'ML' in anomaly_type:
        offending_process = get_top_offending_process(procs_by_ram)
    else: # Disk anomalisi
        offending_process = {'pid': None, 'name': None}
        
    # Grafik oluştur
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    filename = f"anomaly_{now.strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(ANOMALY_DIR, filename)
    _create_anomaly_plot(filepath, anomaly_type, cpu_val, ram_val, disk_val)

    # Sonuç sözlüğünü oluştur ve döndür
    return {
        'is_anomaly': True,
        'anomaly_type': anomaly_type,
        'pid': offending_process.get('pid'),
        'process_name': offending_process.get('name'),
        'top_cpu_processes': get_top_processes_str(procs_by_cpu, 'cpu_percent'),
        'top_ram_processes': get_top_processes_str(procs_by_ram, 'memory_percent'),
        'anomaly_image': filename
    }