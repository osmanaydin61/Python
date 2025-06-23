import psutil
import boto3
import time
import platform
import json
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv() # Bu satır .env dosyasındaki bilgileri yükler

LOG_GROUP = "SunucuPerformansLoglari"
LOG_STREAM = "EC2_Instance_Log"
client = boto3.client('logs')

def should_send_email():
    """Son e-postadan bu yana 10 dakika geçtiyse True döner."""
    status_file = "/tmp/last_alert_time.txt"

    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            last_time_str = f.read().strip()
            try:
                last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_time < timedelta(minutes=10):
                    return False
            except:
                pass

    with open(status_file, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return True

# 📧 E-posta uyarı fonksiyonu
# E-posta uyarı fonksiyonu
def send_email_alert(receiver_email, subject, body):
    sender = "losmanaydin61@gmail.com"  # Bunu da .env'den alabilirsiniz: os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_SENDER_PASSWORD")

    if not password:
        print("E-posta gönderim hatası: EMAIL_SENDER_PASSWORD ortam değişkeni ayarlanmamış.")
        return
    if not receiver_email:
        print("E-posta gönderim hatası: Alıcı e-posta adresi belirtilmemiş.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', _charset='utf-8')) # Hata almamak için _charset='utf-8' eklemeyi unutmayın!

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver_email, msg.as_string())
        print(f"📧 E-posta {receiver_email} adresine gönderildi!")
    except Exception as e:
        print(f"E-posta gönderim hatası ({receiver_email}):", e)

# 🔧 Yüksek CPU kullanan işlemleri bul
def find_high_cpu_processes(threshold=80.0):
    result = subprocess.run(['ps', '-eo', 'pid,pcpu,comm', '--sort=-pcpu'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8').splitlines()[1:]  # Başlığı atla
    processes = []
    for line in output:
        try:
            pid, cpu, cmd = line.strip().split(None, 2)
            if float(cpu) >= threshold:
                processes.append((pid, cpu, cmd))
        except:
            continue
    return processes

def get_system_metrics():
    return {
        "CPU Usage": psutil.cpu_percent(),
        "RAM Usage": psutil.virtual_memory().percent,
        "Disk Usage": psutil.disk_usage('/').percent,
        "Network Sent (MB)": psutil.net_io_counters().bytes_sent / (1024 * 1024),
        "Network Received (MB)": psutil.net_io_counters().bytes_recv / (1024 * 1024)
    }

def send_to_cloudwatch(metrics):
    log_entry = {
        "timestamp": int(time.time() * 1000),
        "message": json.dumps(metrics)
    }

    try:
        client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=LOG_STREAM,
            logEvents=[log_entry]
        )
        print("☁️ CloudWatch'a log gönderildi.")
    except Exception as e:
        print("CloudWatch gönderim hatası:", e)

def check_and_alert(metrics):
    alerts = []
    if metrics["CPU Usage"] > 95:
        alerts.append("⚠️ CPU kullanımı yüksek: {:.2f}%".format(metrics["CPU Usage"]))
    if metrics["RAM Usage"] > 95:
        alerts.append("⚠️ RAM kullanımı yüksek: {:.2f}%".format(metrics["RAM Usage"]))
    if metrics["Disk Usage"] > 95:
        alerts.append("⚠️ Disk kullanımı yüksek: {:.2f}%".format(metrics["Disk Usage"]))

    if alerts:
        print("\n".join(alerts))

        if should_send_email():
            processes = find_high_cpu_processes()
            process_info = "\n".join(f"PID: {p[0]} | CPU: {p[1]}% | Process: {p[2]}" for p in processes)
            body = "\n".join(alerts) + "\n\n🔍 Yüksek CPU kullanan işlemler:\n" + process_info
            send_email_alert("Sunucu Uyarısı", body)
        else:
            print("📫 Uyarı gönderilmedi: 10 dakikalık sınır aktif.")


def plot_metrics(metrics):
    labels = list(metrics.keys())
    values = [metrics[k] if metrics[k] is not None else 0 for k in labels]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color=['blue', 'green', 'red', 'purple', 'orange'])
    plt.xlabel("Metrikler")
    plt.ylabel("Değerler")
    plt.title("Sunucu Performans Metrikleri")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.savefig("plot.png")
    print("📊 Grafik kaydedildi: plot.png")

if __name__ == "__main__":
    metrics = get_system_metrics()
    send_to_cloudwatch(metrics)
    check_and_alert(metrics)
    plot_metrics(metrics)