from flask import Blueprint, render_template_string, request, redirect, url_for, session
import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo

tavsiye_routes = Blueprint("tavsiye", __name__)
TAVSIYE_FILE = "tavsiyeler.csv"
CEVAP_FILE = "cevaplar.csv"

@tavsiye_routes.route("/tavsiye", methods=["GET", "POST"])
def tavsiye():
    # Tavsiye Gönderme (readonly)
    if request.method == "POST" and request.form.get("mode") == "tavsiye":
        user = session.get("user", "Anonim")
        tavsiye_metni = request.form.get("tavsiye")
        timestamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M:%S")
        new_entry = pd.DataFrame([[user, tavsiye_metni, timestamp]], columns=["user", "tavsiye", "timestamp"])

        if os.path.exists(TAVSIYE_FILE):
            df = pd.read_csv(TAVSIYE_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(TAVSIYE_FILE, index=False)
        return redirect(url_for("tavsiye.tavsiye"))

    # Admin Cevaplama
    if request.method == "POST" and request.form.get("mode") == "cevap":
        if session.get("user") != "osmanaydin2016@yandex.com":
            return "Yetkisiz işlem."
        user = request.form.get("user")
        tavsiye_text = request.form.get("tavsiye")
        timestamp = request.form.get("timestamp")
        cevap = request.form.get("cevap")
        cevap_timestamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M:%S")

        # Cevabı kaydet
        new_entry = pd.DataFrame([[user, tavsiye_text, cevap, timestamp, cevap_timestamp]],
                                 columns=["user", "tavsiye", "cevap", "tavsiye_tarih", "cevap_tarih"])
        if os.path.exists(CEVAP_FILE):
            df = pd.read_csv(CEVAP_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(CEVAP_FILE, index=False)

        # Tavsiyeyi sil
        df_tavsiye = pd.read_csv(TAVSIYE_FILE)
        df_tavsiye = df_tavsiye[~((df_tavsiye['user'] == user) & (df_tavsiye['tavsiye'] == tavsiye_text) & (df_tavsiye['timestamp'] == timestamp))]
        df_tavsiye.to_csv(TAVSIYE_FILE, index=False)
        return redirect(url_for("tavsiye.tavsiye"))

    # Verileri hazırla
    tavsiyeler = []
    cevaplar = []
    if os.path.exists(TAVSIYE_FILE):
        tavsiyeler = pd.read_csv(TAVSIYE_FILE).to_dict(orient="records")

    if os.path.exists(CEVAP_FILE):
        df = pd.read_csv(CEVAP_FILE)
    if session.get("user") == "osmanaydin2016@yandex.com":
        cevaplar = df.to_dict(orient="records")  # Admin tüm cevapları görür
    else:
        user = session.get("user")
        cevaplar = df[df['user'] == user].to_dict(orient="records")  # Sadece kendi cevaplarını görür


    is_admin = session.get("user") == "osmanaydin2016@yandex.com"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>Tavsiye ve Cevaplar</title>
        <style>
            body {
                background-color: #0f111a;
                color: #e0e0e0;
                font-family: monospace;
                padding: 20px;
            }
            h1 {
                color: #00adb5;
                text-align: center;
            }
            textarea {
                width: 100%;
                height: 80px;
                border-radius: 6px;
                padding: 8px;
                background-color: #1f1f1f;
                border: 1px solid #00adb5;
                color: white;
            }
            button {
                margin-top: 10px;
                padding: 8px 16px;
                background: #00adb5;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #009baa;
            }
            .card {
                background: #1f1f1f;
                border: 1px solid #00adb5;
                padding: 12px;
                margin: 15px 0;
                border-radius: 6px;
            }
            h2 {
                color: #00adb5;
                border-bottom: 1px solid #00adb5;
                padding-bottom: 5px;
                text-align: center;
            }
            a {
                color: #00adb5;
                text-decoration: none;
                display: block;
                text-align: center;
                margin-top: 20px;
            }
            a:hover {
                text-decoration: underline;
            }
            p {
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <h1>💡 Tavsiye ve Cevaplar</h1>

        {% if not is_admin %}
            <h2>💬 Tavsiyenizi Yazın</h2>
            <form method="POST">
                <input type="hidden" name="mode" value="tavsiye">
                <textarea name="tavsiye" placeholder="Sistem ile ilgili tavsiyenizi yazın..." required></textarea><br>
                <button type="submit">Gönder</button>
            </form>
        {% endif %}

        {% if is_admin and tavsiyeler %}
            <h2>📝 Gelen Tavsiyeler</h2>
            {% for t in tavsiyeler %}
                <div class="card">
                    <p><strong>{{ t.user }}</strong> - {{ t.timestamp }}</p>
                    <p>{{ t.tavsiye }}</p>
                    <form method="POST">
                        <input type="hidden" name="mode" value="cevap">
                        <input type="hidden" name="user" value="{{ t.user }}">
                        <input type="hidden" name="tavsiye" value="{{ t.tavsiye }}">
                        <input type="hidden" name="timestamp" value="{{ t.timestamp }}">
                        <textarea name="cevap" placeholder="Cevabınızı yazın..." required></textarea><br>
                        <button type="submit">📩 Cevapla</button>
                    </form>
                </div>
            {% endfor %}
        {% endif %}

        <h2>📬 Admin Cevapları</h2>
        {% if cevaplar %}
            {% for c in cevaplar %}
                <div class="card">
                    <p><strong>{{ c.user }}</strong> ({{ c.tavsiye_tarih }})</p>
                    <p>📝 Tavsiye: {{ c.tavsiye }}</p>
                    <p>📩 Cevap: {{ c.cevap }}</p>
                    <p>📅 Cevap Tarihi: {{ c.cevap_tarih }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>Henüz cevap yok.</p>
        {% endif %}

        <a href="/">⬅ Geri Dön</a>
    </body>
    </html>
    """, tavsiyeler=tavsiyeler, cevaplar=cevaplar, is_admin=is_admin)
