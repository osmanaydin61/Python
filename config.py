# config.py
import os

class Config:
    # Flask Uygulaması Temel Ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cok-gizli-bir-anahtar-girmelisin'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Veritabanı Yolu
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///../instance/site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uygulama Ayarları için Varsayılanlar
    CPU_THRESHOLD = int(os.environ.get('CPU_THRESHOLD', 90))
    RAM_THRESHOLD = int(os.environ.get('RAM_THRESHOLD', 90))
    DISK_THRESHOLD = int(os.environ.get('DISK_THRESHOLD', 95))
    EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', 'ornek@example.com')
    ALARM_ENABLED = os.environ.get('ALARM_ENABLED', 'True').lower() == 'true'
    AGGRESSIVE_MODE = os.environ.get('AGGRESSIVE_MODE', 'False').lower() == 'true'
    METRICS_RECORD_INTERVAL = int(os.environ.get('METRICS_RECORD_INTERVAL', 1)) 
    ANOMALY_CONTAMINATION = float(os.environ.get('ANOMALY_CONTAMINATION', 0.1))
    MIN_SAMPLES_FOR_ML_CONFIG = int(os.environ.get('MIN_SAMPLES_FOR_ML_CONFIG', 100))
    RAM_CLEAN_THRESHOLD = float(os.environ.get('RAM_CLEAN_THRESHOLD', 80.0))
    DISK_CLEAN_THRESHOLD_PERCENT = float(os.environ.get('DISK_CLEAN_THRESHOLD_PERCENT', 40.0))
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))
    DEFAULT_NETWORK_INTERFACE = os.environ.get('DEFAULT_NETWORK_INTERFACE', 'lo')