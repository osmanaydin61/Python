
from flask import Flask, render_template_string
import pandas as pd
import os
from utils.anomaly_detector import detect_anomalies
from utils.metrics_recorder import record_metrics

app = Flask(__name__, static_folder='static')

@app.route("/anomali")
def anomali():
    # Kayıt + anomali hesapla
    record_metrics()
    detect_anomalies()

    if not os.path.exists("metrics_history.csv"):
        return "<p>Veri dosyası bulunamadı.</p>"

    df = pd.read_csv("metrics_history.csv")
    anomaly_rows = df[df['anomaly'] == -1][['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 'top_cpu_processes', 'top_ram_processes']]

    yorum = ""
    if not anomaly_rows.empty:
        yorum += "<h3>🔍 Anomali Tespit Edilen Zamanlar ve İlgili İşlemler:</h3><ul>"
        for _, row in anomaly_rows.iterrows():
            yorum += f"<li><b>{row['timestamp']}</b><br>CPU: {row['cpu_percent']}%, RAM: {row['ram_percent']}%, Disk: {row['disk_percent']}%<br>"
            yorum += f"⚙️ CPU İşlemleri: {row['top_cpu_processes']}<br>💾 RAM İşlemleri: {row['top_ram_processes']}</li><br>"
        yorum += "</ul>"
    else:
        yorum = "<p>✅ Şu anda anomali bulunmuyor.</p>"

    return render_template_string("""
        <h1>🧠 Anomali Tespiti</h1>
        <h2>CPU Kullanımı Anomalileri</h2>
        <img src='/static/cpu_anomaly.png' width='500'><br>
        <h2>RAM Kullanımı Anomalileri</h2>
        <img src='/static/ram_anomaly.png' width='500'><br>
        <h2>Disk Kullanımı Anomalileri</h2>
        <img src='/static/disk_anomaly.png' width='500'><br><br>
        {{ yorum | safe }}
        <a href='/'>⬅ Ana Sayfaya Dön</a>
    """, yorum=yorum)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
