# config.py
import os

class Config:
    # Flask Uygulaması Temel Ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_cok_gizli_bir_anahtar_burada_olmali_123!'
    DEBUG = os.environ.get('FLASK_DEBUG') or False

    # Veritabanı Ayarları - YENİ
    # projenizin kök dizininde 'site_data.db' adında bir SQLite veritabanı oluşturulacak
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site_data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Gereksiz uyarıları önlemek için False yapın

    # Ayarlar sayfasındaki mevcut global değişkenler için varsayılanlar
    CPU_THRESHOLD = int(os.environ.get('CPU_THRESHOLD', 90))
    RAM_THRESHOLD = int(os.environ.get('RAM_THRESHOLD', 90))
    DISK_THRESHOLD = int(os.environ.get('DISK_THRESHOLD', 99))
    EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'ornek@example.com')
    ALARM_ENABLED = os.environ.get('ALARM_ENABLED', 'True').lower() == 'true'
    AGGRESSIVE_MODE = os.environ.get('AGGRESSIVE_MODE', 'False').lower() == 'true'

    # Yeni eklenen ayarlar için varsayılanlar (Ayarlar sayfasında gösterilecek)
    METRICS_RECORD_INTERVAL = int(os.environ.get('METRICS_RECORD_INTERVAL', 2)) # Saniye cinsinden
    ANOMALY_CONTAMINATION = float(os.environ.get('ANOMALY_CONTAMINATION', 0.05)) # ML model contamination
    MIN_SAMPLES_FOR_ML_CONFIG = int(os.environ.get('MIN_SAMPLES_FOR_ML_CONFIG', 50)) # ML için min örnek sayısı
    RAM_CLEAN_THRESHOLD = float(os.environ.get('RAM_CLEAN_THRESHOLD', 20.0)) # RAM temizleme eşiği
    DISK_CLEAN_THRESHOLD_PERCENT = float(os.environ.get('DISK_CLEAN_THRESHOLD_PERCENT', 90.0)) # Disk temizleme % eşiği
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30)) # Log tutma süresi (gün)


    # Diğer sabit kodlanmış değerler için (şimdilik kalsın, bazıları veritabanına taşınabilir)
    METRICS_HISTORY_CSV = os.environ.get('METRICS_HISTORY_CSV') or 'metrics_history.csv' # Geçici olarak kalsın, sonra kaldıracağız
    TAVSIYE_CSV = os.environ.get('TAVSIYE_CSV') or 'tavsiyeler.csv' # Geçici olarak kalsın
    CEVAP_CSV = os.environ.get('CEVAP_CSV') or 'cevaplar.csv' # Geçici olarak kalsın
    ANOMALY_DIR = os.environ.get('ANOMALY_DIR') or 'static/anomalies'
    LOG_GROUP = os.environ.get('LOG_GROUP') or 'SunucuPerformansLoglari'
    LOG_STREAM = os.environ.get('LOG_STREAM') or 'EC2_Instance_Log'
    LAST_ALERT_FILE = os.environ.get('LAST_ALERT_FILE') or '/tmp/last_alert_time.txt'

    ALARM_ENABLED = os.environ.get('ALARM_ENABLED', 'True').lower() == 'true'
    AGGRESSIVE_MODE = os.environ.get('AGGRESSIVE_MODE', 'False').lower() == 'true'