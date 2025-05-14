from flask import Blueprint, render_template_string, session
from auth import login_required

dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/")
@login_required
def home():
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
                font-size: 28px;
            }
            .logout {
                position: absolute;
                top: 15px;
                right: 20px;
            }
            .logout a {
                color: white;
                text-decoration: none;
                background-color: #444;
                padding: 8px 12px;
                border-radius: 5px;
            }
            .logout a:hover {
                background-color: #666;
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
        <div class="logout">
            <a href='/logout'>Çıkış Yap</a>
        </div>
        <h1>🛠️ Hoş gelme, {{ user }}!</h1>
                                  
        <img src="/static/cpu.png" width="300">
        <img src="/static/ram.png" width="300">
        <img src="/static/disk.png" width="300">

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
    </body>
    </html>
    """, user=session.get("user"))
