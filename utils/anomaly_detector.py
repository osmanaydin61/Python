# utils/anomaly_detector.py

import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import psutil
from sklearn.ensemble import IsolationForest 
import getpass 

CSV_PATH = 'metrics_history.csv'
ANOMALY_DIR = 'static/anomalies'
os.makedirs(ANOMALY_DIR, exist_ok=True)
MAX_ROWS = 500

# Hayati sistem süreçlerinin veya kök kullanıcıya ait süreçlerin listesi
SYSTEM_PROCESS_KEYWORDS = [
    "systemd", "kernel", "init", "kthreadd", "root", 
    "dbus", "gnome", "kde", "Xorg", "pulseaudio",     
    "udev", "rsyslog", "crond", "sshd", "nginx", "apache2", 
    "mysqld", "postgres", "mongod",                   
    "python", # Kendi Python uygulamanızı yanlışlıkla sonlandırmamak için dikkatli olun!
]

def is_critical_process(process_name=None, cmdline=None, username=None):
    if username == "root":
        return True

    if process_name:
        process_name_lower = process_name.lower()
        for keyword in SYSTEM_PROCESS_KEYWORDS:
            if keyword in process_name_lower:
                return True
    
    if cmdline:
        cmdline_lower = " ".join(cmdline).lower()
        for keyword in SYSTEM_PROCESS_KEYWORDS:
            if keyword in cmdline_lower:
                return True

    return False


def get_top_processes(metric):
    if metric == 'cpu':
        procs = [(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:5] # İlk 5 süreç
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    elif metric == 'ram':
        procs = [(p.info['name'], p.info['memory_percent']) for p in psutil.process_iter(['name', 'memory_percent'])]
        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:5] # İlk 5 süreç
        return ', '.join([f"{name}({val:.1f}%)" for name, val in procs])
    return ''


def detect_and_log_anomaly(cpu_val, ram_val, disk_val):
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    expected_columns = ['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 
                        'top_cpu_processes', 'top_ram_processes', 'anomaly', 
                        'anomaly_image', 'anomaly_type']

    df = pd.DataFrame(columns=expected_columns) 
    
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        try:
            df_existing = pd.read_csv(CSV_PATH)
            for col in expected_columns:
                if col not in df_existing.columns:
                    df_existing[col] = '' 
            df = df_existing[expected_columns].copy() 
            df['anomaly'] = df['anomaly'].fillna(0).astype(int) 
        except pd.errors.EmptyDataError:
            pass 

    anomaly_prediction = 0 
    anomaly_type = '' 

    # --- YENİ: new_data_dict'in doğru tanımlandığı yer ---
    # Model eğitimi için yeni veri setini burada oluşturuyoruz
    current_data_for_training_dict = {
        'cpu_percent': cpu_val, 
        'ram_percent': ram_val, 
        'disk_percent': disk_val
    }
    current_data_for_training = pd.DataFrame([current_data_for_training_dict])


    if not df.empty:
        X_historical = df[['cpu_percent', 'ram_percent', 'disk_percent']]
        X_combined = pd.concat([X_historical, current_data_for_training], ignore_index=True)
    else:
        X_combined = current_data_for_training 

    MIN_SAMPLES_FOR_ML = 10 

    if len(X_combined) >= MIN_SAMPLES_FOR_ML:
        model = IsolationForest(random_state=42, contamination=0.05) 
        model.fit(X_combined) 
        anomaly_prediction = model.predict(current_data_for_training)[0]
    else:
        if cpu_val > 20 or ram_val > 70 or disk_val > 80: 
            anomaly_prediction = -1 
        else:
            anomaly_prediction = 0

    # Anomali tespit edildiyse, anomali tipini belirle
    if anomaly_prediction == -1:
        metrics_dict = {'CPU': cpu_val, 'RAM': ram_val, 'Disk': disk_val}
        max_metric = max(metrics_dict, key=metrics_dict.get)
        anomaly_type = f"{max_metric} Anomalisi"
    
    # --- YENİ: 'new_data_record' değişkenini burada tanımlıyoruz ---
    # Bu değişken, CSV'ye kaydedilecek ve kartta gösterilecek tek bir kayıt için kullanılacak
    new_data_record = {
        'timestamp': now_str,
        'cpu_percent': cpu_val,
        'ram_percent': ram_val,
        'disk_percent': disk_val,
        'top_cpu_processes': get_top_processes('cpu'),
        'top_ram_processes': get_top_processes('ram'),
        'anomaly': anomaly_prediction, 
        'anomaly_image': '',
        'anomaly_type': anomaly_type 
    }

    # Sütun hizalamasını sağlamak için pd.Series kullanarak DataFrame'e dönüştür
    new_data_series_for_concat = pd.Series(new_data_record, index=expected_columns) 
    new_data_df_for_concat = pd.DataFrame([new_data_series_for_concat]) # Tek satırlık DataFrame

    # Ana DataFrame'i güncelleyin
    df = pd.concat([df, new_data_df_for_concat], ignore_index=True) 

    # --- GRAFİK OLUŞTURMA KISMI ---
    # Bu blokta da new_data_record veya new_data_df_for_concat kullanılacak
    if new_data_record['anomaly'] == -1: # new_data_record kullanıldı
        filename = f"anomaly_{now.strftime('%Y%m%d_%H%M%S')}.png"
        new_data_record['anomaly_image'] = filename # new_data_record kullanıldı
        filepath = os.path.join(ANOMALY_DIR, filename)

        # Plot için df'yi ve yeni veriyi birleştirirken de uyarıyı önle
        # df_for_plot = pd.concat([df.tail(20), pd.DataFrame([new_data_record])], ignore_index=True) # ESKİ HATA VEREN KISIM
        # YENİSİ:
        df_for_plot = pd.concat([df[expected_columns].tail(20).reset_index(drop=True), new_data_df_for_concat.reset_index(drop=True)], ignore_index=True)


        plt.figure(figsize=(10, 5))
        plt.plot(df_for_plot['timestamp'], df_for_plot['cpu_percent'], label='CPU', color='red', marker='o', markersize=4)
        plt.plot(df_for_plot['timestamp'], df_for_plot['ram_percent'], label='RAM', color='blue', marker='o', markersize=4)
        plt.plot(df_for_plot['timestamp'], df_for_plot['disk_percent'], label='Disk', color='green', marker='o', markersize=4)
        
        # Grafik üzerinde anomali noktasını işaretlerken de new_data_record kullanın
        # new_data_df_for_concat'ın sadece bir satırı olduğu için iloc[0] ile erişim daha güvenlidir
        plt.plot(new_data_df_for_concat['timestamp'].iloc[0], new_data_df_for_concat['cpu_percent'].iloc[0], 'X', color='black', markersize=10, label='Anomaly (CPU)')
        plt.plot(new_data_df_for_concat['timestamp'].iloc[0], new_data_df_for_concat['ram_percent'].iloc[0], 'X', color='black', markersize=10, label='Anomaly (RAM)')
        plt.plot(new_data_df_for_concat['timestamp'].iloc[0], new_data_df_for_concat['disk_percent'].iloc[0], 'X', color='black', markersize=10, label='Anomaly (Disk)')


        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        plt.title(f"Anomali - {now_str} ({anomaly_type})")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()

    # --- ÖNEMLİ: BU SATIR TEKRARLANIYORDU, KALDIRDIM ---
    # df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True) # Bu satır yukarıda zaten yapıldı!

    if len(df) > MAX_ROWS:
        df = df.tail(MAX_ROWS)

    df.to_csv(CSV_PATH, index=False)

    return new_data_record if new_data_record['anomaly'] == -1 else None # new_data_record döndürülüyor