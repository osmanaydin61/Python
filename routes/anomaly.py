from flask import Blueprint, render_template
from auth import login_required
import os
import pandas as pd
import psutil

anomaly_routes = Blueprint("anomaly", __name__)

@anomaly_routes.route("/anomali")
@login_required
def anomaly():
    if not os.path.exists("metrics_history.csv"):
        return "<p>Veri dosyası bulunamadı.</p>"
    
    df = pd.read_csv("metrics_history.csv")
    anomaly_rows = df[df['anomaly'] == -1][['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 'top_cpu_processes', 'top_ram_processes']]
    anomaly_rows = anomaly_rows.drop_duplicates(subset=['top_cpu_processes'], keep='last')
    anomaly_rows = anomaly_rows.tail(5)

    # Aktif çalışan process isimlerini al
    active_processes = [p.info['name'] for p in psutil.process_iter(['name'])]

    # Aktif processlere göre filtrele
    filtered_rows = []
    for _, row in anomaly_rows.iterrows():
        proc_name = row['top_cpu_processes'].split(',')[0].split('(')[0].strip()
        if proc_name in active_processes:
            filtered_rows.append(row)

    return render_template('anomaly_page.html', filtered_rows=filtered_rows)
