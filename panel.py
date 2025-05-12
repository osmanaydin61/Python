
from flask import Flask, render_template_string, redirect, url_for, request
import os
import psutil
import pandas as pd
from resource_cleaner import clean_ram
from network_monitor import check_network_usage
from CloudWatch import send_email_alert

app = Flask(__name__, static_folder='static')
cpu_threshold = 90
ram_threshold = 90
disk_threshold = 90
alarm_enabled = True
email_recipient = "ornek@example.com"
aggressive_mode = False
last_freed_space = 0

@app.route("/")
@app.route("/clean")
def clean():
    clean_ram()
    return redirect(url_for("home"))

@app.route("/logs")
def logs():
    try:
        with open("logs/events.log", "r") as f:
            content = f.read().replace("\n", "<br>")
    except FileNotFoundError:
        content = "Log dosyası bulunamadı."
    return f"<h2>📜 Loglar</h2><p>{content}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/network")
def network():
    from io import StringIO
    import sys

    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result

    check_network_usage()

    sys.stdout = old_stdout
    output = result.getvalue().replace("\n", "<br>")
    return f"<h2>🌐 Ağ Kullanımı</h2><p>{output}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/testmail")
def testmail():
    try:
        if alarm_enabled:
            send_email_alert("🔔 Test Mail", f"Bu bir test mesajıdır. Alıcı: {email_recipient}")
            return "<p>✅ Test mail gönderildi.</p><a href='/'>⬅ Geri dön</a>"
        else:
            return "<p>⚠️ Alarm sistemi devre dışı.</p><a href='/'>⬅ Geri dön</a>"
    except Exception as e:
        return f"<p>❌ Mail gönderilemedi: {str(e)}</p><a href='/'>⬅ Geri dön</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
