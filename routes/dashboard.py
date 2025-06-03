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
    <title>Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
    body {
        background-color: #0f111a;
        color: #ffffff;
        font-family: monospace;
        margin: 0;
        padding: 20px;
    }
    h1 {
        text-align: center;
        color: #00adb5;
        margin-bottom: 30px;
    }
    .chart-grid {
    display: flex;
    justify-content: center;
    align-items: flex-start;   /* label’lar canvas’la aynı hizada başlasın */
    gap: 30px;
    margin-bottom: 40px;
    }

    .chart-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    }

    .chart-label {
    font-size: 20px;        /* istediğin büyüklük */
    font-weight: bold;
    color: #00adb5;
    margin-bottom: 8px;
    text-transform: uppercase; /* dilersen */
    }

    canvas {
        width: 300px !important;
        height: 200px !important;
        background-color: #1f1f1f;
        border: 1px solid #00adb5;
        border-radius: 8px;
    }

    /* Ortak buton stili */
    .btn {
        border-radius: 8px;
        transition: all 0.3s;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        text-align: center;
    }

    /* Container (buton grubunun kendisi) */
    .main-buttons {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;  /* butonları ortaya alır */
        gap: 20px;
        width: 100%;              /* tam genişlik */
        margin: 0 auto 40px;      /* alttan boşluk, yatayda ortala */
    }

    /* Butonlar */
    .main-buttons a {
        border-radius: 8px;
        transition: all 0.3s;
        text-decoration: none;
        font-weight: bold;
        text-align: center;
        background-color: #1f1f1f;
        color: #00adb5;
        padding: 20px 30px;
        min-width: 200px;         /* butonun minimum genişliği */
        border: 1px solid #00adb5;
        font-size: 18px;
    }

    /* Hover etkisi */
    .main-buttons a:hover {
        background-color: #00adb5;
        color: #0f111a;
    }


    /* Temizleme butonları */
    .btn-clean {
        /* .btn özellikleri */
        border-radius: 8px;
        transition: all 0.3s;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        text-align: center;

        background: linear-gradient(135deg, #6b5b95, #8e44ad);
        border: 1px solid #5d3f7b;
        color: #fff;
        padding: 12px 24px;
        font-size: 16px;
    }
    .btn-clean:hover {
        background: linear-gradient(135deg, #8e44ad, #6b5b95);
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }

    .secondary-buttons {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-top: 30px;
    }

    .logout-button {
        position: absolute;
        top: 20px;
        right: 20px;
        background-color: #ff4444;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
    }
    .logout-button:hover {
        background-color: #ff0000;
    }

    #popup {
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.8);
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: #fff;
        padding: 30px 60px;
        border-radius: 12px;
        font-size: 22px;
        z-index: 9999;
        text-align: center;
        box-shadow: 0 0 25px rgba(0,0,0,0.8);
        border: 2px solid #00adb5;
        opacity: 0;
        transition: all 0.3s ease-in-out;
    }
    #popup.show {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }
</style>

</head>
<body>
    <a href="/logout" class="logout-button">Çıkış</a>
    <h1>ADMİN PANEL</h1>

    <div class="chart-grid">
    <div class="chart-item">
        <div class="chart-label">CPU Kullanımı</div>
        <canvas id="cpuChart"></canvas>
    </div>
    <div class="chart-item">
        <div class="chart-label">RAM Kullanımı</div>
        <canvas id="ramChart"></canvas>
    </div>
    <div class="chart-item">
        <div class="chart-label">Disk Kullanımı</div>
        <canvas id="diskChart"></canvas>
    </div>
    </div>


    <div class="main-buttons">
        <a href="/network"    class="btn">🌐 Ağ İzle</a>
        <a href="/logs"       class="btn">📜 Logları Gör</a>
        <a href="/settings"   class="btn">⚙️ Ayarlar</a>
        <a href="/anomali"    class="btn">📈 Anomali</a>
        <a href="/tavsiye"    class="btn">💡 Tavsiye</a>
    </div>

    <div class="secondary-buttons">
        <a href="/clean"       class="btn-clean">🧹 RAM Temizle</a>
        <a href="/disktemizle" class="btn-clean">💾 Disk Temizle</a>
    </div>

    <div id="popup"></div>

    <script>
        const cpuLabels = [], cpuData = [], ramData = [], diskData = [], limit = 5;
        const cpuChart = new Chart(document.getElementById('cpuChart').getContext('2d'), {
            type:'line', data:{ labels:cpuLabels, datasets:[{ data:cpuData, borderColor:'red', borderWidth:3, pointRadius:2, tension:0.3 }]},
            options:{ animation:false, plugins:{ legend:{ display:false }}, scales:{ y:{ min:0, max:100 }}}
        });
        const ramChart = new Chart(document.getElementById('ramChart').getContext('2d'), {
            type:'line', data:{ labels:cpuLabels, datasets:[{ data:ramData, borderColor:'blue', borderWidth:3, pointRadius:2, tension:0.3 }]},
            options:{ animation:false, plugins:{ legend:{ display:false }}, scales:{ y:{ min:0, max:100 }}}
        });
        const diskChart = new Chart(document.getElementById('diskChart').getContext('2d'), {
            type:'line', data:{ labels:cpuLabels, datasets:[{ data:diskData, borderColor:'green', borderWidth:3, pointRadius:2, tension:0.3 }]},
            options:{ animation:false, plugins:{ legend:{ display:false }}, scales:{ y:{ min:0, max:100 }}}
        });

        function fetchData(){
            fetch('/metrics').then(r=>r.json()).then(data=>{
                const t=new Date().toLocaleTimeString();
                cpuLabels.push(t); cpuData.push(data.cpu);
                ramData.push(data.ram); diskData.push(data.disk);
                if(cpuLabels.length>limit){cpuLabels.shift(); cpuData.shift(); ramData.shift(); diskData.shift();}
                cpuChart.update(); ramChart.update(); diskChart.update();
            });
        }
        fetchData(); setInterval(fetchData,2000);

        function showPopup(msg){
            const p=document.getElementById('popup');
            p.innerText=msg; p.style.display='block'; p.classList.add('show');
        }
        function hidePopup(){
            const p=document.getElementById('popup');
            p.classList.remove('show'); setTimeout(()=>p.style.display='none',300);
        }
        document.querySelector("a[href='/clean']").addEventListener('click',e=>{
            e.preventDefault(); showPopup('🧹 RAM temizleniyor...');
            fetch('/clean').then(r=>r.text()).then(res=>{
                setTimeout(()=>{ showPopup(res); setTimeout(hidePopup,3500);},3000);
            });
        });
        document.querySelector("a[href='/disktemizle']").addEventListener('click',e=>{
            e.preventDefault(); showPopup('💾 Disk temizleniyor...');
            fetch('/disktemizle').then(r=>r.text()).then(res=>{
                setTimeout(()=>{ showPopup(res); setTimeout(hidePopup,3500);},3000);
            });
        });
    </script>
""", user=session.get("user"))
