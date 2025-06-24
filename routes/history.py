# routes/history.py

from flask import Blueprint, render_template, jsonify, flash
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import func

from extensions import db
from models import Metric

history_routes = Blueprint('history', __name__)

@history_routes.route('/history')
def history_page():
    """
    Bu fonksiyon, "Geçmiş" sayfası için gerekli olan TÜM verileri
    (ana metrikler, saatlik ve günlük anomali trendleri) tek seferde toplar ve gönderir.
    """
    try:
        now_istanbul = datetime.now(ZoneInfo("Europe/Istanbul"))

        # 1. Ana Metrik Verilerini Çek (Son 24 saat)
        time_filter_24h = now_istanbul - timedelta(hours=24)
        metrics = db.session.query(Metric).filter(Metric.timestamp >= time_filter_24h).order_by(Metric.timestamp).all()
        
        main_data = {
            "timestamps": [], "cpu_percents": [], "ram_percents": [], "disk_percents": []
        }
        for metric in metrics:
            local_ts = metric.timestamp.astimezone(ZoneInfo("Europe/Istanbul"))
            main_data["timestamps"].append(local_ts.strftime('%Y-%m-%dT%H:%M:%S'))
            main_data["cpu_percents"].append(metric.cpu_percent)
            main_data["ram_percents"].append(metric.ram_percent)
            main_data["disk_percents"].append(metric.disk_percent)

        # 2. Saatlik Anomali Trend Verisini Çek (Son 72 saat)
        time_filter_72h = now_istanbul - timedelta(hours=72)
        hourly_group_expression = func.strftime('%Y-%m-%d %H:00', Metric.timestamp)
        hourly_results = db.session.query(
            hourly_group_expression, func.count(Metric.id)
        ).filter(
            Metric.is_anomaly == True, Metric.timestamp >= time_filter_72h
        ).group_by(hourly_group_expression).order_by(hourly_group_expression).all() 
        hourly_trend_data = [{"time": row[0], "count": row[1]} for row in hourly_results]

        # 3. Günlük Anomali Trend Verisini Çek (Son 30 gün)
        time_filter_30d = now_istanbul - timedelta(days=30)
        daily_group_expression = func.strftime('%Y-%m-%d', Metric.timestamp)
        daily_results = db.session.query(
            daily_group_expression, func.count(Metric.id)
        ).filter(
            Metric.is_anomaly == True, Metric.timestamp >= time_filter_30d
        ).group_by(daily_group_expression).order_by(daily_group_expression).all() 
        daily_trend_data = [{"time": row[0], "count": row[1]} for row in daily_results]

        # Tüm verileri JSON'a çevirip şablona gönder
        return render_template(
            'history_page.html',
            data_json=json.dumps(main_data),
            hourly_anomaly_json=json.dumps(hourly_trend_data),
            daily_anomaly_json=json.dumps(daily_trend_data)
        )

    except Exception as e:
        print(f"Error fetching history data from DB: {e}")
        flash(f"Geçmiş verileri yüklenirken bir hata oluştu: {e}", "danger")
        return render_template(
            'history_page.html',
            data_json=json.dumps({}),
            hourly_anomaly_json=json.dumps([]),
            daily_anomaly_json=json.dumps([])
        )