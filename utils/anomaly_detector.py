# utils/anomaly_detector.py

import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import psutil
from sklearn.ensemble import IsolationForest 
import getpass 

from models import db, Metric # db ve Metric modelini import ettiğinizden emin olun
from flask import current_app 

# ... (CSV_PATH, ANOMALY_DIR, MAX_ROWS yorum satırı/kaldırılmış olmalı)
ANOMALY_DIR = 'static/anomalies'
os.makedirs(ANOMALY_DIR, exist_ok=True)

# Hayati sistem süreçleri ve get_top_processes fonksiyonu aynı kalır
SYSTEM_PROCESS_KEYWORDS = [
    "systemd", "kernel", "init", "kthreadd", "root", 
    "dbus", "gnome", "kde", "Xorg", "pulseaudio",     
    "udev", "rsyslog", "crond", "sshd", "nginx", "apache2", 
    "mysqld", "postgres", "mongod",                   
    "python", 
]

def is_critical_process(process_name=None, cmdline=None, username=None):
    if username == "root":
        return True
    if process_name:
        process_name_lower = process_name.lower()
        for keyword in SYSTEM_PROCESS_KEYWORDS:
            if keyword in process_name_lower:
                return True
    if cmdline:
        cmdline_lower = " ".join(cmdline).lower()
        for keyword in SYSTEM_PROCESS_KEYWORDS:
            if keyword in cmdline_lower:
                return True
    return False

def get_top_processes(metric):
    if metric == 'cpu':
        procs = [(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:5] 
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    elif metric == 'ram':
        procs = [(p.info['name'], p.info['memory_percent']) for p in psutil.process_iter(['name', 'memory_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:5] 
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    return ''

def detect_and_log_anomaly(cpu_val, ram_val, disk_val):
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    expected_columns = ['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 
                        'top_cpu_processes', 'top_ram_processes', 'anomaly', 
                        'anomaly_image', 'anomaly_type']

    # Bu df artık CSV okuma için kullanılmıyor, ancak ML mantığı için gerekli
    # Başlangıçta boş ve doğru sütunlarla başlatılıyor.
    df = pd.DataFrame(columns=expected_columns) 

    # config'den ML için minimum örnek sayısını oku
    MIN_SAMPLES_FOR_ML = current_app.config.get('MIN_SAMPLES_FOR_ML_CONFIG', 50)
    
    # Veritabanından en son metrik objelerini al
    fetch_limit_for_ml = max(MIN_SAMPLES_FOR_ML * 2, 200) # ML için en az 200 veya 2 katı örnek çek
    
    # --- HATA DÜZELTME: Metric objelerinin tamamını seçin ---
    recent_metrics_objects = db.session.execute(
        db.select(Metric) # Metrik objelerinin tamamını seçiyoruz
        .order_by(Metric.timestamp.desc()) # En yeniden en eskiye doğru sırala
        .limit(fetch_limit_for_ml) 
    ).scalars().all() # scalars() burada her bir Metric objesini döndürecektir

    # Veritabanından gelen Metric objelerini Pandas DataFrame'e dönüştür
    # List comprehension'ı Metric objesinden değerleri alacak şekilde güncelleyin
    df_for_ml_and_context = pd.DataFrame([
        {
            'cpu_percent': m.cpu_percent, 
            'ram_percent': m.ram_percent, 
            'disk_percent': m.disk_percent,
            'timestamp': m.timestamp, # datetime objesi olarak kalsın
            'top_cpu_processes': m.top_cpu_processes, 
            'top_ram_processes': m.top_ram_processes,
            'anomaly': m.anomaly,
            'anomaly_image': m.anomaly_image # anomaly_image de buraya eklendi
        }
        for m in recent_metrics_objects # m artık bir Metric objesidir
    ])
    
    # DataFrame'i tersine çeviriyoruz ki en eski veri başta olsun, ML için doğru sıralama
    df_for_ml_and_context = df_for_ml_and_context.iloc[::-1].reset_index(drop=True) 

    anomaly_prediction = 0 
    anomaly_type = '' 

    current_data_for_training_dict = {
        'cpu_percent': cpu_val, 
        'ram_percent': ram_val, 
        'disk_percent': disk_val
    }
    current_data_for_training = pd.DataFrame([current_data_for_training_dict])


    if not df_for_ml_and_context.empty:
        X_historical = df_for_ml_and_context[['cpu_percent', 'ram_percent', 'disk_percent']]
        X_combined = pd.concat([X_historical, current_data_for_training], ignore_index=True)
    else:
        X_combined = current_data_for_training 

    ANOMALY_CONTAMINATION = current_app.config.get('ANOMALY_CONTAMINATION', 0.05)


    if len(X_combined) >= MIN_SAMPLES_FOR_ML:
        model = IsolationForest(random_state=42, contamination=ANOMALY_CONTAMINATION) 
        model.fit(X_combined) 
        anomaly_prediction = model.predict(current_data_for_training)[0]
    else:
        CPU_THRESHOLD = current_app.config.get('CPU_THRESHOLD', 80)
        RAM_THRESHOLD = current_app.config.get('RAM_THRESHOLD', 80)
        DISK_THRESHOLD = current_app.config.get('DISK_THRESHOLD', 95)

        if cpu_val > CPU_THRESHOLD or ram_val > RAM_THRESHOLD or disk_val > DISK_THRESHOLD: 
            anomaly_prediction = -1 
        else:
            anomaly_prediction = 0

    if anomaly_prediction == -1:
        metrics_dict = {'CPU': cpu_val, 'RAM': ram_val, 'Disk': disk_val}
        max_metric = max(metrics_dict, key=metrics_dict.get)
        anomaly_type = f"{max_metric} Anomalisi"
    
    new_data_record = {
        'timestamp': now_str,
        'cpu_percent': cpu_val,
        'ram_percent': ram_val,
        'disk_percent': disk_val,
        'top_cpu_processes': get_top_processes('cpu'),
        'top_ram_processes': get_top_processes('ram'),
        'anomaly': anomaly_prediction, 
        'anomaly_image': '',
        'anomaly_type': anomaly_type 
    }

    if new_data_record['anomaly'] == -1: 
        filename = f"anomaly_{now.strftime('%Y%m%d_%H%M%S')}.png"
        new_data_record['anomaly_image'] = filename 
        filepath = os.path.join(ANOMALY_DIR, filename)

        df_plot_context = df_for_ml_and_context.tail(20).copy() # Son 20 kaydı al
        new_record_df = pd.DataFrame([new_data_record])
        new_record_df['timestamp'] = pd.to_datetime(new_record_df['timestamp'])

        df_for_plot = pd.concat([df_plot_context.reset_index(drop=True), new_record_df.reset_index(drop=True)], ignore_index=True)

        plot_timestamps = [ts.strftime('%H:%M:%S') for ts in df_for_plot['timestamp']] # Sadece saat:dakika:saniye göster
        
        plt.figure(figsize=(10, 5))
        plt.plot(plot_timestamps, df_for_plot['cpu_percent'], label='CPU', color='red', marker='o', markersize=4)
        plt.plot(plot_timestamps, df_for_plot['ram_percent'], label='RAM', color='blue', marker='o', markersize=4)
        plt.plot(plot_timestamps, df_for_plot['disk_percent'], label='Disk', color='green', marker='o', markersize=4)
        
        anomaly_ts_str = datetime.strptime(new_data_record['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
        plt.plot(anomaly_ts_str, new_data_record['cpu_percent'], 'X', color='black', markersize=10, label='Anomaly (CPU)')
        plt.plot(anomaly_ts_str, new_data_record['ram_percent'], 'X', color='black', markersize=10, label='Anomaly (RAM)')
        plt.plot(anomaly_ts_str, new_data_record['disk_percent'], 'X', color='black', markersize=10, label='Anomaly (Disk)')


        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        plt.title(f"Anomali - {now_str} ({anomaly_type})")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()

    return new_data_record if new_data_record['anomaly'] == -1 else None
