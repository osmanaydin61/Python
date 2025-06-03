from flask import Blueprint, render_template_string
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

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Anomali Tespiti</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #121212; color: #f0f0f0; font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
        .anomaly-card { border: 1px solid #444; border-radius: 10px; padding: 15px; margin: 20px auto; max-width: 800px; background-color: #1f1f1f; }
        canvas { width: 850px !important; height: 500px !important; background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; margin: 20px auto; display: block; }
        a { color: #00adb5; text-decoration: none; }
        a:hover { text-decoration: underline; }
        button { background-color: #ff4444; color: white; padding: 8px 16px; border: none; border-radius: 6px; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <div id="popup" style="display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: rgba(30,30,30,0.95); color: white; padding: 20px 40px; border-radius: 8px; font-size: 18px; z-index: 9999; text-align: center; box-shadow: 0 0 10px rgba(0,0,0,0.7);"></div>

    <h1>🧠 Anomali Tespiti</h1>

    <canvas id="liveChart"></canvas>

    {% if filtered_rows %}
        {% for row in filtered_rows %}
            <div class="anomaly-card" id="anomaly-{{ loop.index }}">
                <p>🕒 {{ row['timestamp'] }} | 🔥 CPU: {{ row['cpu_percent'] }}% | 💾 RAM: {{ row['ram_percent'] }}% | 📀 Disk: {{ row['disk_percent'] }}%</p>
                <p>⚙️ CPU İşlemleri: {{ row['top_cpu_processes'] }}<br>💾 RAM İşlemleri: {{ row['top_ram_processes'] }}</p>
                <form class="kill-form" data-id="anomaly-{{ loop.index }}">
                    <input type="hidden" name="process" value="{{ row['top_cpu_processes'].split(',')[0].split('(')[0].strip() }}">
                    <button type="submit">❌ İşlemi Sonlandır</button>
                </form>
            </div>
        {% endfor %}
    {% else %}
        <p>✅ Şu anda anomali bulunmuyor.</p>
    {% endif %}

    <a href="/">⬅ Geri Dön</a>

<script>
    const labels = [];
    const cpuData = [];
    const ramData = [];
    const diskData = [];
    let anomalyCounter = null;
    let anomalyAlertShown = false;

    const chart = new Chart(document.getElementById('liveChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'CPU', borderColor: 'red', data: [], pointRadius: 6, pointStyle: 'circle', backgroundColor: 'red' },
                { label: 'RAM', borderColor: 'blue', data: [], pointRadius: 6, pointStyle: 'circle', backgroundColor: 'blue' },
                { label: 'Disk', borderColor: 'green', data: [], pointRadius: 6, pointStyle: 'circle', backgroundColor: 'green' }
            ]
        },
        options: { animation: false, scales: { y: { min: 0, max: 105 } } }
    });

    function fetchData() {
        if (anomalyAlertShown) {
            chart.update(); // Sadece chartı güncelle, veri çekme
             return;
        }

        fetch('/metrics').then(r => r.json()).then(data => {
            const now = new Date().toLocaleTimeString();
            labels.push(now);
            cpuData.push(data.cpu);
            ramData.push(data.ram);
            diskData.push(data.disk);
            chart.data.labels = labels;
            chart.data.datasets[0].data = cpuData;
            chart.data.datasets[1].data = ramData;
            chart.data.datasets[2].data = diskData;
            if (labels.length > 20) { labels.shift(); cpuData.shift(); ramData.shift(); diskData.shift(); }
            chart.update();

            if ((data.cpu > 80 || data.ram > 80 || data.disk > 95) && anomalyCounter === null) {
                anomalyCounter = 5;
            }
            if (anomalyCounter !== null) {
                anomalyCounter--;
                if (anomalyCounter === 0 && !anomalyAlertShown) {
                    alert("Anomali tespit edildi! Grafik donduruldu.");
                    anomalyAlertShown = true;
                }
            }
        });
    }

    setInterval(fetchData, 2000);

    document.querySelectorAll(".kill-form").forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            const cardId = form.getAttribute("data-id");
            fetch("/killprocess", { method: "POST", body: formData }).then(r => r.json()).then(data => {
                showPopup(data.message);
                const card = document.getElementById(cardId);
                if (card) card.remove();
            });
        });
    });

    function showPopup(message) {
        const popup = document.getElementById('popup');
        popup.innerText = message;
        popup.style.display = 'block';
        setTimeout(() => { popup.style.display = 'none'; }, 3000);
    }
</script>

</body>
</html>
""", filtered_rows=filtered_rows)
