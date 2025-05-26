import csv
import psutil
import datetime
import os
import pandas as pd

CSV_PATH = 'metrics_history.csv'
MAX_ROWS = 500  # 🔥 Maksimum 500 satır tut

def record_metrics():
    fields = ['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 'top_cpu_processes', 'top_ram_processes', 'anomaly']

    # Dosya yoksa başlık ekle
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    top_cpu = sorted([(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])], key=lambda x: x[1], reverse=True)[:3]
    top_ram = sorted([(p.info['name'], p.info['memory_info'].rss / (1024*1024)) for p in psutil.process_iter(['name', 'memory_info'])], key=lambda x: x[1], reverse=True)[:3]
    top_cpu_str = ', '.join([f"{name}({cpu:.1f}%)" for name, cpu in top_cpu])
    top_ram_str = ', '.join([f"{name}({ram:.1f}MB)" for name, ram in top_ram])

    row = {
        'timestamp': timestamp,
        'cpu_percent': cpu,
        'ram_percent': ram,
        'disk_percent': disk,
        'top_cpu_processes': top_cpu_str,
        'top_ram_processes': top_ram_str,
        'anomaly': ''
    }

    # Yaz ve maksimum satır sayısını koru
    df = pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame(columns=fields)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    if len(df) > MAX_ROWS:
        df = df.tail(MAX_ROWS)
    df.to_csv(CSV_PATH, index=False)

    print("[METRICS]", row)
