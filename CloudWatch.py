import psutil
import boto3
import time
import platform
import matplotlib.pyplot as plt

# AWS CloudWatch için Log Grup ve Log Stream Tanımları
LOG_GROUP = "SunucuPerformansLoglari"  # Özel karakter olmamalı
LOG_STREAM = "EC2_Instance_Log"

# AWS CloudWatch bağlantısı
client = boto3.client('logs')

# Performans verilerini al
import psutil
import platform

import psutil
import platform

def get_system_metrics():
    metrics = {
        "CPU Usage": psutil.cpu_percent(),
        "RAM Usage": psutil.virtual_memory().percent,
        "Disk Usage": psutil.disk_usage('/').percent,
        "Network Sent (MB)": psutil.net_io_counters().bytes_sent / (1024 * 1024),
        "Network Received (MB)": psutil.net_io_counters().bytes_recv / (1024 * 1024),
        
    }

    
    
    return metrics

import json

# CloudWatch'a veri gönder
import time

def send_to_cloudwatch():
    """Ölçüm verilerini CloudWatch'a JSON formatında gönderir."""
    log_entry = {  # Liste yerine direkt sözlük oluştur
        "timestamp": int(time.time() * 1000),
        "message": json.dumps({  # JSON string formatına çevir
            "CPU Usage": psutil.cpu_percent(),
            "RAM Usage": psutil.virtual_memory().percent,
            "Disk Usage": psutil.disk_usage('/').percent,
            "Network Sent (MB)": psutil.net_io_counters().bytes_sent / (1024 * 1024),
            "Network Received (MB)": psutil.net_io_counters().bytes_recv / (1024 * 1024)
        })
    }

    try:
        response = client.put_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=LOG_STREAM,
            logEvents=[log_entry]  # ← Burada liste içinde tek bir dict olmalı!
    )
        print("Log başarıyla CloudWatch'a gönderildi:", response)
    except Exception as e:
        print("Hata oluştu:", e)

# Performans verilerini grafikle göster
def plot_metrics():
    metrics = get_system_metrics()
    
    labels = list(metrics.keys())
    values = [v if v is not None else 0 for v in metrics.values()]  # None değerlerini sıfır yap
    
    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color=['blue', 'green', 'red', 'purple', 'orange'])
    
    plt.xlabel("Metrikler")
    plt.ylabel("Değerler")
    plt.title("Sunucu Performans Metrikleri")
    plt.xticks(rotation=45)
    plt.grid(axis="y")

    plt.savefig("plot.png")  # 📌 Grafik dosyasını kaydet
    print("Grafik başarıyla kaydedildi: plot.png")

plot_metrics()



if __name__ == "__main__":
    send_to_cloudwatch()
    plot_metrics()
