# routes/history.py

from flask import Blueprint, render_template
from auth import login_required
import os
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo # zoneinfo import edildi

history_routes = Blueprint("history", __name__)

@history_routes.route("/history")
@login_required
def history():
    # Tüm veri değişkenlerini başlangıçta boş listelerle başlatın.
    # Bu, dosya yoksa veya boşsa JS'e her zaman geçerli boş verilerin gitmesini sağlar.
    history_data = {
        'timestamps': [], 
        'cpu_percents': [], 
        'ram_percents': [], 
        'disk_percents': []
    }
    hourly_anomaly_data = {'labels': [], 'counts': []}
    daily_anomaly_data = {'labels': [], 'counts': []}

    df = pd.DataFrame() # df'yi başlangıçta boş bir DataFrame olarak tanımlayın

    # metrics_history.csv dosyasının varlığını ve boş olup olmadığını kontrol et
    if os.path.exists("metrics_history.csv") and os.path.getsize("metrics_history.csv") > 0:
        try:
            df = pd.read_csv("metrics_history.csv")
            # 'anomaly' ve 'anomaly_type' sütunlarının varlığını ve tiplerini garanti et
            if 'anomaly' not in df.columns:
                df['anomaly'] = 0
            df['anomaly'] = df['anomaly'].fillna(0).astype(int) # NaN değerleri 0'a çevir
            if 'anomaly_type' not in df.columns:
                df['anomaly_type'] = ''
        except pd.errors.EmptyDataError:
            df = pd.DataFrame() # Dosya varsa ama boşsa, df'yi yine boş bırak


    print(f"DEBUG: pd.read_csv sonrası df.empty: {df.empty}")

    # --- Genel Metrik Geçmişi Verilerini Hazırlama ---
    if not df.empty: # Sadece df boş değilse işlem yap
        MAX_HISTORY_POINTS = 20 # En fazla 20 veri noktası göster
        df_display = df.tail(MAX_HISTORY_POINTS)

        # df_display'in tail() işleminden sonra boş olup olmadığını kontrol et
        # (örn. df 10 satır ama MAX_HISTORY_POINTS 20 ise df_display yine de boş olmaz, 10 satır olur)
        # Ama eğer df baştan boşsa, df_display de boş olacaktır.
        if not df_display.empty:
            history_data = {
                'timestamps': df_display['timestamp'].tolist() if 'timestamp' in df_display.columns else [],
                'cpu_percents': df_display['cpu_percent'].tolist() if 'cpu_percent' in df_display.columns else [],
                'ram_percents': df_display['ram_percent'].tolist() if 'ram_percent' in df_display.columns else [],
                'disk_percents': df_display['disk_percent'].tolist() if 'disk_percent' in df_display.columns else []
            }
            print(f"DEBUG: history_data dolduruldu. İlk timestamp: {history_data['timestamps'][:1]}, son timestamp: {history_data['timestamps'][-1:]}")
        else:
            print("DEBUG: df_display boş olduğu için history_data doldurulmadı.")
    else:
        print("DEBUG: df boş olduğu için history_data doldurulmadı.")

    # --- Anomali Trend Grafiği Verilerini Hazırlama ---
    ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")
    
    # df boş değilse VE 'anomaly' sütunu varsa anomali verilerini işle
    if not df.empty and 'anomaly' in df.columns: 
        anomalies_df = df[df['anomaly'] == -1].copy()

        if not anomalies_df.empty:
            anomalies_df['timestamp'] = pd.to_datetime(anomalies_df['timestamp'])
            # Eğer timestamp'ler naive (saat dilimi bilgisi yok) ise, tz_localize ile başlayın.
            if anomalies_df['timestamp'].dt.tz is None: 
                anomalies_df['timestamp'] = anomalies_df['timestamp'].dt.tz_localize('Europe/Istanbul')
            else: # Eğer saat dilimi bilgisi varsa, direkt dönüştür
                anomalies_df['timestamp'] = anomalies_df['timestamp'].dt.tz_convert('Europe/Istanbul')

            # Saatlik anomali sayıları (son 24 saat için)
            end_time_hourly = datetime.now(ISTANBUL_TZ)
            start_time_hourly = end_time_hourly - timedelta(hours=24)
            hourly_time_points = [start_time_hourly + timedelta(hours=i) for i in range(25)]
            
            recent_anomalies_hourly = anomalies_df[anomalies_df['timestamp'] >= start_time_hourly].copy() 
            recent_anomalies_hourly.loc[:, 'hour_floor'] = recent_anomalies_hourly['timestamp'].dt.floor('h') 
            
            hourly_counts_raw = recent_anomalies_hourly.groupby('hour_floor').size()
            
            hourly_labels_filled = []
            hourly_counts_filled = []
            for i in range(len(hourly_time_points)): 
                current_hour_point = hourly_time_points[i]
                hourly_labels_filled.append(current_hour_point.strftime('%H:%M'))
                count = hourly_counts_raw.get(current_hour_point, 0)
                hourly_counts_filled.append(int(count))

            hourly_anomaly_data = {
                'labels': hourly_labels_filled,
                'counts': hourly_counts_filled
            }
            print(f"DEBUG: hourly_anomaly_data dolduruldu. Labels count: {len(hourly_anomaly_data['labels'])}")

            # Günlük anomali sayıları (son 7 gün için)
            end_time_daily = datetime.now(ISTANBUL_TZ)
            start_time_daily = end_time_daily - timedelta(days=7)
            daily_time_points = [start_time_daily + timedelta(days=i) for i in range(8)]

            recent_anomalies_daily = anomalies_df[anomalies_df['timestamp'] >= start_time_daily].copy()
            recent_anomalies_daily.loc[:, 'date_floor'] = recent_anomalies_daily['timestamp'].dt.floor('D')
            
            daily_counts_raw = recent_anomalies_daily.groupby('date_floor').size()

            daily_labels_filled = []
            daily_counts_filled = []
            for i in range(len(daily_time_points)):
                current_day_point = daily_time_points[i]
                daily_labels_filled.append(current_day_point.strftime('%Y-%m-%d'))
                count = daily_counts_raw.get(current_day_point, 0)
                daily_counts_filled.append(int(count))

            daily_anomaly_data = {
                'labels': daily_labels_filled,
                'counts': daily_counts_filled
            }
            print(f"DEBUG: daily_anomaly_data dolduruldu. Labels count: {len(daily_anomaly_data['labels'])}")
        else:
            print("DEBUG: anomalies_df boş olduğu için anomali trend verileri doldurulmadı.")
    else:
        print("DEBUG: df boş veya 'anomaly' sütunu eksik, anomali trend verileri doldurulmadı.")

    print("DEBUG: history_page.html render ediliyor.")
    return render_template('history_page.html',
                           history_data=history_data,
                           hourly_anomaly_data=hourly_anomaly_data,
                           daily_anomaly_data=daily_anomaly_data)