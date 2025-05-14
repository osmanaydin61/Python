import boto3
import json
import matplotlib.pyplot as plt
import datetime

# AWS CloudWatch bağlantısı
client = boto3.client("logs")

# Log grubu ve akış adı
LOG_GROUP = "SunucuPerformansLoglari"
LOG_STREAM = "EC2_Instance_Log"

def fetch_logs():
    """CloudWatch'tan en son logları çeker"""
    try:
        response = client.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=LOG_STREAM,
            limit=10
        )
        return response["events"]
    except Exception as e:
        print(f"Hata: {e}")
        return []

def extract_metric(log_message, key):
    """JSON içindeki metrik değerlerini çeker"""
    try:
        log_data = json.loads(log_message.replace("'", "\""))  # Tek tırnakları düzelt
        return float(log_data.get(key, 0))  # Değer yoksa 0 dön
    except (json.JSONDecodeError, ValueError):
        return None

def generate_graph():
    """CPU ve RAM kullanım grafiğini oluşturur"""
    events = fetch_logs()
    
    timestamps, cpu_usage, ram_usage = [], [], []
    for event in events:
        timestamp = datetime.datetime.fromtimestamp(event["timestamp"] / 1000)
        cpu = extract_metric(event["message"], "CPU Kullanımı")
        ram = extract_metric(event["message"], "RAM Kullanımı")

        if cpu is not None and ram is not None:
            timestamps.append(timestamp.strftime("%H:%M:%S"))
            cpu_usage.append(cpu)
            ram_usage.append(ram)

    # Grafik çizimi
    plt.figure(figsize=(8, 6))
    plt.plot(timestamps, cpu_usage, 'r-o', label="CPU Kullanımı (%)")
    plt.plot(timestamps, ram_usage, 'b-s', label="RAM Kullanımı (%)")
    plt.xlabel("Zaman")
    plt.ylabel("Kullanım Oranı (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()

    # PNG olarak kaydet
    plt.savefig("/home/ubuntu/Python/output.png")
    plt.close()
