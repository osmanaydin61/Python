
# routes/dashboard.py — Ana panel ve grafik sayfaları
from flask import Blueprint, render_template_string, session
from auth import login_required
from graph_generator import generate_system_graphs
dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/")
@login_required
def home():
    generate_system_graphs()
    return render_template_string("""
        <html>
        <head>
            <style>
                body {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: Arial, sans-serif;
                    text-align: center;
                }
                h1 {
                    margin-top: 20px;
                    font-size: 32px;
                }
                img {
                    margin: 10px;
                    border: 2px solid #444;
                    border-radius: 10px;
                }
                .button-grid {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    margin: 30px 0;
                    gap: 15px;
                }
                .button-grid a {
                    display: inline-block;
                    background-color: #444;
                    color: white;
                    padding: 15px 25px;
                    border-radius: 8px;
                    font-size: 18px;
                    text-decoration: none;
                    transition: background 0.3s;
                    width: 200px;
                    text-align: center;
                }
                .button-grid a:hover {
                    background-color: #666;
                }
            </style>
        </head>
        <body>
            <h1>🛠️ Sistem Kontrol Paneli</h1>
            <div>
                <img src='/static/cpu.png' width='300'>
                <img src='/static/ram.png' width='300'>
                <img src='/static/disk.png' width='300'>
            </div>
            <div class="button-grid">
                <a href='/logs'>📜 Logları Görüntüle</a>
                <a href='/testmail'>📨 Test Mail Gönder</a>
                <a href='/network'>🌐 Ağ Trafiğini Görüntüle</a>
                <a href='/tavsiye'>🧠 Yorum ve Öneri</a>
                <a href='/anomali'>📈 Anomali Tespiti</a>
                <a href='/clean'>🧹 RAM Temizliği Yap</a>
                <a href='/disktemizle'>🧹 Disk Temizliği</a>
                <a href='/ayarlar'>⚙️ Alarm Ayarları</a>                  
            </div>
        </body>
        </html>
    
    """)