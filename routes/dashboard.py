from flask import Blueprint, render_template_string, session
from auth import login_required

dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/")
@login_required
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 0;
                padding: 20px;
            }
            .chart-grid {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
            }
            canvas {
                width: 300px !important;
                height: 200px !important;
                background-color: #111;
                border-radius: 8px;
                border: 1px solid #333;
                padding: 5px;
            }
            .button-grid {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 15px;
                margin-top: 30px;
            }
            .button-grid a {
                background-color: #444;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 16px;
                text-decoration: none;
                width: 180px;
                transition: background 0.3s;
            }
            .button-grid a:hover {
                background-color: #666;
            }
            .status-label {
                font-size: 20px;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <h1>ADMİN PANEL</h1>

        <div class="chart-grid">
            <div>
                <div class="status-label" id="cpuLabel">CPU: %0</div>
                <canvas id="cpuChart"></canvas>
            </div>
            <div>
                <div class="status-label" id="ramLabel">RAM: %0</div>
                <canvas id="ramChart"></canvas>
            </div>
            <div>
                <div class="status-label" id="diskLabel">Disk: %0</div>
                <canvas id="diskChart"></canvas>
            </div>
        </div>

        <div class="button-grid">
            <a href='/clean'>🧹 RAM Temizle</a>
            <a href='/disktemizle'>💾 Disk Temizle</a>
            <a href='/network'>🌐 Ağ İzle</a>
            <a href='/logs'>📜 Logları Gör</a>
            <a href='/settings'>⚙️ Ayarlar</a>
            <a href='/anomali'>📈 Anomali</a>
            <a href='/tavsiye'>🧠 Tavsiye</a>
            <a href='/testmail'>📨 Test Mail</a>
        </div>

        <script>
            const cpuLabels = [];
            const cpuData = [];
            const ramData = [];
            const diskData = [];
            const limit = 5;  // Son 5 veriyi tut

            const cpuChart = new Chart(document.getElementById('cpuChart').getContext('2d'), {
                type: 'line',
                data: { labels: cpuLabels, datasets: [{ data: cpuData, borderColor: 'red', borderWidth: 3, pointRadius: 2, tension: 0.3 }] },
                options: { animation: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }
            });

            const ramChart = new Chart(document.getElementById('ramChart').getContext('2d'), {
                type: 'line',
                data: { labels: cpuLabels, datasets: [{ data: ramData, borderColor: 'blue', borderWidth: 3, pointRadius: 2, tension: 0.3 }] },
                options: { animation: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }
            });

            const diskChart = new Chart(document.getElementById('diskChart').getContext('2d'), {
                type: 'line',
                data: { labels: cpuLabels, datasets: [{ data: diskData, borderColor: 'green', borderWidth: 3, pointRadius: 2, tension: 0.3 }] },
                options: { animation: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }
            });

            function fetchData() {
                fetch('/metrics')
                    .then(response => response.json())
                    .then(data => {
                        const time = new Date().toLocaleTimeString();

                        cpuLabels.push(time);
                        cpuData.push(data.cpu);
                        ramData.push(data.ram);
                        diskData.push(data.disk);

                        if (cpuLabels.length > limit) {
                            cpuLabels.shift();
                            cpuData.shift();
                            ramData.shift();
                            diskData.shift();
                        }

                        cpuChart.update(); ramChart.update(); diskChart.update();
                        document.getElementById('cpuLabel').innerText = `CPU: %${data.cpu.toFixed(1)}`;
                        document.getElementById('ramLabel').innerText = `RAM: %${data.ram.toFixed(1)}`;
                        document.getElementById('diskLabel').innerText = `Disk: %${data.disk.toFixed(1)}`;
                    });
            }

            fetchData();
            setInterval(fetchData, 2000);

            // Popup sistemi
            function showPopup(message) {
                const popup = document.getElementById('popup');
                popup.innerText = message;
                popup.style.display = 'block';
            }

            document.querySelector("a[href='/clean']").addEventListener('click', function(event) {
                event.preventDefault();
                showPopup('RAM temizleniyor...');
                fetch('/clean')
                    .then(response => response.text())
                    .then(result => {
                        setTimeout(() => {
                            showPopup(result);
                            setTimeout(() => { document.getElementById('popup').style.display = 'none'; }, 3000);
                        }, 3000);
                    });
            });
        </script>

        <div id="popup" style="
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(30,30,30,0.95);
            color: white;
            padding: 20px 40px;
            border-radius: 8px;
            font-size: 18px;
            z-index: 9999;
            text-align: center;
            box-shadow: 0 0 10px rgba(0,0,0,0.7);
        "></div>

    </body>
    </html>
    """, user=session.get("user"))
