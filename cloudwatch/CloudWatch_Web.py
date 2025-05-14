from flask import Flask, Response, jsonify
import boto3
import datetime
import matplotlib.pyplot as plt
import io
import time
import ast

app = Flask(__name__)

# AWS CloudWatch bağlantısı
client = boto3.client("logs")

LOG_GROUP = "SunucuPerformansLoglari"
LOG_STREAM = "EC2_Instance_Log"

def fetch_logs():
    """CloudWatch'tan son 10 logu çeker"""
    response = client.get_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=LOG_STREAM,
        limit=100  # Daha fazla veri çekip en son 10 taneyi almak için büyük bir limit koyuyoruz.
    )

    events = response["events"]

    # Zaman damgasına göre sıralayarak en son 10 logu al
    sorted_events = sorted(events, key=lambda x: x["timestamp"], reverse=True)
    return sorted_events[:10]  # En yeni 10 log


def extract_metric(log_message, english_key, turkish_key):
    """Log mesajından belirtilen metrik değerini alır"""
    try:
        log_data = ast.literal_eval(log_message)  # Güvenli dönüşüm
        
        # İngilizce veya Türkçe anahtarı kontrol et
        if english_key in log_data:
            return float(log_data[english_key])
        elif turkish_key in log_data:
            return float(log_data[turkish_key])
        else:
            return None  # Anahtar bulunamazsa None döndür
    except (ValueError, SyntaxError, KeyError):
        print(f"Hatalı veri: {log_message}")  # Hata ayıklamak için
        return None

@app.route('/plot.png')
def plot():
    """Matplotlib ile canlı grafik oluştur ve PNG olarak döndür"""
    events = fetch_logs()

    timestamps, cpu_usage, ram_usage = [], [], []
    now = datetime.datetime.now()  # Şu anki zaman

    for event in events:
        timestamp = datetime.datetime.fromtimestamp(event["timestamp"] / 1000)

        # Gelecekteki logları filtrele (AWS'nin hatalı timestamp sorunlarını önlemek için)
        if timestamp > now:
            print(f"Atlanan Gelecek Tarihli Log: {timestamp}")  # Konsola yaz
            continue  

        cpu = extract_metric(event["message"], "CPU Usage", "CPU Kullanımı")
        ram = extract_metric(event["message"], "RAM Usage", "RAM Kullanımı")

        if cpu is not None and ram is not None:
            timestamps.append(timestamp)
            cpu_usage.append(cpu)
            ram_usage.append(ram)

    if not timestamps:
        return Response("Yeterli veri yok", status=400)

    # Timestamps'i sıralayalım (düzgün eksen için)
    timestamps, cpu_usage, ram_usage = zip(*sorted(zip(timestamps, cpu_usage, ram_usage)))

    # X eksenini zamana göre normalize et
    time_diffs = [(t - now).total_seconds() / 60 for t in timestamps]  # Dakika cinsinden

    plt.switch_backend('Agg')  # Sunucu tarafında çizim için
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(time_diffs, cpu_usage, 'r-o', label="CPU Kullanımı (%)")
    ax.plot(time_diffs, ram_usage, 'b-s', label="RAM Kullanımı (%)")

    ax.set_xlabel("Geçen Süre (dakika)")
    ax.set_ylabel("Kullanım Oranı (%)")
    ax.legend()
    plt.grid()

    # X ekseni etiketlerini "Şimdi, -5 dk, -10 dk" olarak göster
    ax.set_xticks(time_diffs)
    ax.set_xticklabels([f"{int(t)} dk" if t != 0 else "Şimdi" for t in time_diffs], rotation=45)

    # Grafiği belleğe kaydet
    output = io.BytesIO()
    plt.savefig(output, format='png')
    plt.close(fig)
    output.seek(0)

    return Response(output.getvalue(), mimetype='image/png')

@app.route('/data')
def get_data():
    """Ham JSON verileri döndür"""
    logs = fetch_logs()  
    return jsonify(logs)

@app.route('/')
def index():
    """Ana sayfa: Canlı grafiği otomatik yenileyen bir HTML sayfası"""
    return '''
    <html>
        <head>
            <title>CloudWatch Canlı İzleme</title>
            <meta http-equiv="refresh" content="5">  <!-- Her 5 saniyede bir yenile -->
        </head>
        <body>
            <h1>Sunucu Performans İzleme</h1>
            <img src="/plot.png" alt="Canlı Grafik">
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)