# utils/anomaly_detector.py
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import psutil

CSV_PATH = 'metrics_history.csv'
ANOMALY_DIR = 'static/anomalies'
os.makedirs(ANOMALY_DIR, exist_ok=True)
MAX_ROWS = 500

def detect_and_log_anomaly(cpu_val, ram_val, disk_val):
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Yeni veri hazırla
    new_data = {
        'timestamp': now_str,
        'cpu_percent': cpu_val,
        'ram_percent': ram_val,
        'disk_percent': disk_val,
        'top_cpu_processes': get_top_processes('cpu'),
        'top_ram_processes': get_top_processes('ram'),
        'anomaly': -1 if cpu_val > 80 or ram_val > 80 or disk_val > 95 else 0,
        'anomaly_image': ''
    }

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame(columns=new_data.keys())

    # Anomali varsa grafik oluştur
    if new_data['anomaly'] == -1:
        filename = f"anomaly_{now.strftime('%Y%m%d_%H%M%S')}.png"
        new_data['anomaly_image'] = filename
        filepath = os.path.join(ANOMALY_DIR, filename)

        plt.figure(figsize=(8,4))
        plt.plot(df['timestamp'], df['cpu_percent'], label='CPU', color='red')
        plt.plot(df['timestamp'], df['ram_percent'], label='RAM', color='blue')
        plt.plot(df['timestamp'], df['disk_percent'], label='Disk', color='green')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        plt.title(f"Anomali - {now_str}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()

    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    if len(df) > MAX_ROWS:
        df = df.tail(MAX_ROWS)

    df.to_csv(CSV_PATH, index=False)

    return new_data if new_data['anomaly'] == -1 else None

def get_top_processes(metric):
    if metric == 'cpu':
        procs = [(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:3]
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    elif metric == 'ram':
        procs = [(p.info['name'], p.info['memory_percent']) for p in psutil.process_iter(['name', 'memory_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:3]
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    return ''
