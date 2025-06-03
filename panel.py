from flask import Flask, jsonify, request, redirect, url_for
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from routes.network_monitor import get_network_page, get_network_content
from utils.resource_cleaner import clean_ram
from utils.clean_disk_utils import clean_disk
from cloudwatch.CloudWatch import send_email_alert
from utils.anomaly_detector import detect_and_log_anomaly
from routes.logger import get_logs_page, get_logs_content,log_info
import psutil
import time
import threading
import pandas as pd
import logging
import getpass
app = Flask(__name__)
app.secret_key = 'gizli_anahtar'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Blueprint kayıtları
app.register_blueprint(auth_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(settings_routes)
app.register_blueprint(anomaly_routes)
app.register_blueprint(tavsiye_routes)

# Global veriler
anomaly_records = []
metrics = {"cpu": 0, "ram": 0, "disk": 0}

# Arka planda metrik toplama
def background_thread():
    global metrics, anomaly_records
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        metrics = {"cpu": cpu, "ram": ram, "disk": disk}
        anomaly = detect_and_log_anomaly(cpu, ram, disk)
        if anomaly:
            anomaly_records.append(anomaly)

        time.sleep(2)

# İşlem sonlandırma
@app.route("/killprocess", methods=["POST"])
@login_required
@roles_required("admin")
def kill_process():
    process_name = request.form.get("process")
    if not process_name:
        return "❌ Process adı bulunamadı."
    
    current_user = getpass.getuser()
    killed = []
    skipped = []

    # Süreçleri tara, komut satırında ismi geçenleri seç
    for proc in psutil.process_iter(["pid", "cmdline", "username"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
            if process_name in cmd:
                if proc.info["username"] == current_user:
                    try:
                        proc.terminate()            # önce nazikçe terminate
                        proc.wait(timeout=3)       # bekle
                        killed.append(proc.pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        skipped.append(proc.pid)
                else:
                    skipped.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # CSV'den kaydı sil
    df = pd.read_csv("metrics_history.csv")
    df = df[~df['top_cpu_processes'].str.contains(process_name, na=False)]
    df.to_csv("metrics_history.csv", index=False)

    msg_parts = []
    if killed:
        msg_parts.append(f"✅ Sonlandırıldı: {', '.join(map(str, killed))}")
    if skipped:
        msg_parts.append(f"⚠️ Atlandı (izin yok veya sistem süreci): {', '.join(map(str, skipped))}")
    if not msg_parts:
        msg_parts.append("❌ Eşleşen süreç bulunamadı.")

    from flask import jsonify


    return jsonify({"message": "<br>".join(msg_parts)})


# RAM temizleme
@app.route("/clean")
@login_required
@roles_required("admin")
def clean():
    result = clean_ram()
    log_info(result)
    return result

# Disk temizleme
@app.route("/disktemizle")
@login_required
@roles_required("admin")
def disktemizle():
    result = clean_disk()
    log_info(result)
    return result

# Test mail
@app.route("/testmail")
@login_required
def testmail():
    try:
        send_email_alert("🔔 Test Mail", "Bu bir test mesajıdır.")
        return "<p>✅ Test mail gönderildi.</p><a href='/'>⬅ Geri dön</a>"
    except Exception as e:
        return f"<p>❌ Mail gönderilemedi: {str(e)}</p><a href='/'>⬅ Geri dön</a>"

# Metrikler (JSON)
@app.route("/metrics")
def get_metrics():
    return jsonify(metrics)

# Context
@app.context_processor
def inject_helpers():
    import random
    return dict(random=random.random, zip=zip)

@app.context_processor
def inject_random():
    import random
    return dict(random=random.random)

@app.route("/logs")
@login_required
def logs_page():
    return get_logs_page()

@app.route("/getlogs")
@login_required
def get_logs():
    return get_logs_content()
@app.route("/network")
@login_required
def network():
    return get_network_page()

@app.route("/getnetwork")
@login_required
def getnetwork():
    return get_network_content()
# Çalıştır
if __name__ == "__main__":
    threading.Thread(target=background_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
