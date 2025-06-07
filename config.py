# config.py
import os

class Config:
    # Flask Uygulaması Temel Ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_cok_gizli_bir_anahtar_burada_olmali_123!' # .env'den okumak en iyisi
    DEBUG = os.environ.get('FLASK_DEBUG') or False # Geliştirme için True, production için False

    # Ayarlar sayfasındaki mevcut global değişkenler için varsayılanlar
    CPU_THRESHOLD = int(os.environ.get('CPU_THRESHOLD', 90))
    RAM_THRESHOLD = int(os.environ.get('RAM_THRESHOLD', 90))
    DISK_THRESHOLD = int(os.environ.get('DISK_THRESHOLD', 99))
    EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'ornek@example.com')
    ALARM_ENABLED = os.environ.get('ALARM_ENABLED', 'True').lower() == 'true'
    AGGRESSIVE_MODE = os.environ.get('AGGRESSIVE_MODE', 'False').lower() == 'true'

    # Diğer sabit kodlanmış değerler için
    METRICS_HISTORY_CSV = os.environ.get('METRICS_HISTORY_CSV') or 'metrics_history.csv'
    TAVSIYE_CSV = os.environ.get('TAVSIYE_CSV') or 'tavsiyeler.csv'
    CEVAP_CSV = os.environ.get('CEVAP_CSV') or 'cevaplar.csv'
    ANOMALY_DIR = os.environ.get('ANOMALY_DIR') or 'static/anomalies'
    LOG_GROUP = os.environ.get('LOG_GROUP') or 'SunucuPerformansLoglari'
    LOG_STREAM = os.environ.get('LOG_STREAM') or 'EC2_Instance_Log'
    LAST_ALERT_FILE = os.environ.get('LAST_ALERT_FILE') or '/tmp/last_alert_time.txt'
