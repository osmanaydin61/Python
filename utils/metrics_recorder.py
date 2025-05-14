
import psutil
import pandas as pd
from datetime import datetime
import os

def record_metrics(csv_path='metrics_history.csv'):
    now = datetime.now()
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # En çok CPU kullanan 3 işlem
    top_cpu = sorted([(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])],
                     key=lambda x: x[1], reverse=True)[:3]
    cpu_proc_str = ', '.join([f"{name}({percent:.1f}%)" for name, percent in top_cpu])

    # En çok RAM kullanan 3 işlem
    top_ram = sorted([(p.info['name'], p.info['memory_info'].rss / (1024 * 1024)) for p in psutil.process_iter(['name', 'memory_info'])],
                     key=lambda x: x[1], reverse=True)[:3]
    ram_proc_str = ', '.join([f"{name}({mb:.1f}MB)" for name, mb in top_ram])

    row = {
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
        'cpu_percent': cpu,
        'ram_percent': ram,
        'disk_percent': disk,
        'top_cpu_processes': cpu_proc_str,
        'top_ram_processes': ram_proc_str
    }

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(csv_path, index=False)
