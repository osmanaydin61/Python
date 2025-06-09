import csv
import psutil
import datetime
import os
import pandas as pd

CSV_PATH = 'metrics_history.csv'
MAX_ROWS = 500  # 🔥 Maksimum 500 satır tut

def record_metrics():
    # Tüm beklenen sütunları tanımlayın
    expected_columns = ['timestamp', 'cpu_percent', 'ram_percent', 'disk_percent', 
                        'top_cpu_processes', 'top_ram_processes', 'anomaly', 
                        'anomaly_type']

    df = pd.DataFrame(columns=expected_columns) # Tüm beklenen sütunlarla boş bir DataFrame başlatın

    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        try:
            df_existing = pd.read_csv(CSV_PATH)
            # Mevcut DataFrame'in tüm beklenen sütunlara sahip olduğundan emin olun
            for col in expected_columns:
                if col not in df_existing.columns:
                    df_existing[col] = '' 
            df = df_existing[expected_columns].copy() 
            # 'anomaly' sütununu int tipine dönüştür
            if 'anomaly' in df.columns:
                df['anomaly'] = df['anomaly'].fillna(0).astype(int)
            # 'anomaly_type' sütunu yoksa ekle (geriye dönük uyumluluk)
            if 'anomaly_type' not in df.columns:
                df['anomaly_type'] = ''

        except pd.errors.EmptyDataError:
            pass # Dosya boşsa df boş bir DataFrame olarak kalır


    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    top_cpu = sorted([(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])], key=lambda x: x[1], reverse=True)[:5]
    top_ram = sorted([(p.info['name'], p.info['memory_info'].rss / (1024*1024)) for p in psutil.process_iter(['name', 'memory_info'])], key=lambda x: x[1], reverse=True)[:5]
    top_cpu_str = ', '.join([f"{name}({cpu:.1f}%)" for name, cpu in top_cpu])
    top_ram_str = ', '.join([f"{name}({ram:.1f}MB)" for name, ram in top_ram])

    row_data_dict = {
        'timestamp': timestamp,
        'cpu_percent': cpu,
        'ram_percent': ram,
        'disk_percent': disk,
        'top_cpu_processes': top_cpu_str,
        'top_ram_processes': top_ram_str,
        'anomaly': 0, 
        'anomaly_type': '' 
    }
    
    # Sütun hizalamasını sağlamak için pd.Series kullanarak DataFrame'e dönüştür
    new_row_series = pd.Series(row_data_dict, index=expected_columns)
    new_row_df = pd.DataFrame([new_row_series])

    # pd.concat işlemini new_row_df ile yapın
    df = pd.concat([df, new_row_df], ignore_index=True) 

    if len(df) > MAX_ROWS:
        df = df.tail(MAX_ROWS)
    df.to_csv(CSV_PATH, index=False)

    print("[METRICS]", row_data_dict)