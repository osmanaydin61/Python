
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import os

def detect_anomalies(csv_path='metrics_history.csv', output_dir='static'):
    if not os.path.exists(csv_path):
        print("Metric history not found!")
        return

    df = pd.read_csv(csv_path)

    # Modeli eğit
    features = df[['cpu_percent', 'ram_percent', 'disk_percent']]
    model = IsolationForest(contamination=0.1, random_state=42)
    df['anomaly'] = model.fit_predict(features)

    # anomaly sütununu dosyaya yaz
    df.to_csv(csv_path, index=False)

    os.makedirs(output_dir, exist_ok=True)

    # CPU grafiği
    plt.figure()
    plt.plot(df['timestamp'], df['cpu_percent'], label='CPU Kullanımı (%)')
    anomalies = df[df['anomaly'] == -1]
    plt.scatter(anomalies['timestamp'], anomalies['cpu_percent'], color='red', label='Anomali', s=40)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.title("CPU Kullanımı ve Anomaliler")
    plt.savefig(os.path.join(output_dir, 'cpu_anomaly.png'))
    plt.close()

    # RAM grafiği
    plt.figure()
    plt.plot(df['timestamp'], df['ram_percent'], label='RAM Kullanımı (%)')
    plt.scatter(anomalies['timestamp'], anomalies['ram_percent'], color='red', label='Anomali', s=40)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.title("RAM Kullanımı ve Anomaliler")
    plt.savefig(os.path.join(output_dir, 'ram_anomaly.png'))
    plt.close()

    # Disk grafiği
    plt.figure()
    plt.plot(df['timestamp'], df['disk_percent'], label='Disk Kullanımı (%)')
    plt.scatter(anomalies['timestamp'], anomalies['disk_percent'], color='red', label='Anomali', s=40)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.title("Disk Kullanımı ve Anomaliler")
    plt.savefig(os.path.join(output_dir, 'disk_anomaly.png'))
    plt.close()
