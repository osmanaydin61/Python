from flask import Flask, redirect, url_for, render_template_string
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.disk import disk_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from utils.network_monitor import check_network_usage
from utils.graph_generator import generate_system_graphs
from utils.resource_cleaner import clean_ram
from utils.clean_disk_utils import clean_disk
from utils.metrics_recorder import record_metrics
from utils.anomaly_detector import detect_anomalies
from cloudwatch.CloudWatch import send_email_alert
import os
import psutil
import pandas as pd

app = Flask(__name__, static_folder='static')
app.secret_key = 'gizli_anahtar'

# Global sistem ayarları
cpu_threshold = 90
ram_threshold = 90
disk_threshold = 90
alarm_enabled = True
email_recipient = "ornek@example.com"
aggressive_mode = False
last_freed_space = 0

# Blueprint kayıtları
app.register_blueprint(auth_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(disk_routes)
app.register_blueprint(settings_routes)
app.register_blueprint(anomaly_routes)
app.register_blueprint(tavsiye_routes)

@app.route("/clean")
@login_required
@roles_required("admin")
def clean():
    clean_ram()
    return redirect(url_for("dashboard.home"))

@app.route("/logs")
@login_required
def logs():
    try:
        with open("logs/events.log", "r") as f:
            content = f.read().replace("\n", "<br>")
    except FileNotFoundError:
        content = "Log dosyası bulunamadı."
    return f"<h2>📜 Loglar</h2><p>{content}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/network")
@login_required
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
@login_required
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
