from flask import Flask, jsonify,request, redirect, url_for
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.disk import disk_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from utils.network_monitor import check_network_usage
from utils.resource_cleaner import clean_ram
from cloudwatch.CloudWatch import send_email_alert
from utils.anomaly_detector import detect_and_log_anomaly
import subprocess
import psutil
import time
import threading
import random
import pandas as pd
app = Flask(__name__)
app.secret_key = 'gizli_anahtar'

# Blueprint kayıtları
app.register_blueprint(auth_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(disk_routes)
app.register_blueprint(settings_routes)
app.register_blueprint(anomaly_routes)
app.register_blueprint(tavsiye_routes)
anomaly_records = []
metrics = {"cpu": 0, "ram": 0, "disk": 0}

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
        
@app.route("/killprocess", methods=["POST"])
@login_required
@roles_required("admin")
def kill_process():
    process_name = request.form.get("process")
    if process_name:
        try:
            subprocess.call(['pkill', '-f', process_name])

            # CSV'den anomaliyi sil
            df = pd.read_csv("metrics_history.csv")
            df = df[~df['top_cpu_processes'].str.contains(process_name, na=False)]
            df.to_csv("metrics_history.csv", index=False)

            return jsonify({"message": f"✅ {process_name} işlemi sonlandırıldı ve anomali kaydı silindi."})
        except Exception as e:
            return jsonify({"message": f"❌ Hata: {str(e)}"})
    return jsonify({"message": "❌ Process adı bulunamadı."})


@app.route("/metrics")
def get_metrics():
    return jsonify(metrics)
@app.context_processor
def inject_helpers():
    import random
    return dict(random=random.random, zip=zip)

@app.context_processor
def inject_random():
    import random
    return dict(random=random.random)

if __name__ == "__main__":
    threading.Thread(target=background_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
