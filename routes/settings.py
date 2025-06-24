# routes/settings.py

from flask import Blueprint, request, render_template, current_app, flash
from auth import login_required, roles_required
from models import  Setting
from extensions import db
settings_routes = Blueprint("settings", __name__)

# Ayarı veritabanına kaydeder
def save_setting(key, value, value_type):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
        setting.value_type = value_type
    else:
        setting = Setting(key=key, value=str(value), value_type=value_type)
        db.session.add(setting)
    db.session.commit()
    
    current_app.config[key] = convert_value_to_type(str(value), value_type)


# Veritabanından okunan string değeri doğru tipine çevirir
def convert_value_to_type(value_str, value_type):
    if value_type == 'int':
        try:
            return int(value_str)
        except (ValueError, TypeError):
            return 0
    elif value_type == 'float':
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return 0.0
    elif value_type == 'bool':
        return str(value_str).lower() == 'true'
    return value_str

@settings_routes.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def settings():
    if request.method == "POST":
        secilen_yontem = request.form.get('anomaly_detection_method', 'threshold')
        print(f"--- AYAR KAYDEDİLİYOR: Formdan gelen 'anomaly_detection_method' değeri: '{secilen_yontem}' ---")
    
        # Formdan gelen tüm değerleri al ve veritabanına kaydet
        save_setting('CPU_THRESHOLD', request.form["cpu"], 'int')
        save_setting('RAM_THRESHOLD', request.form["ram"], 'int')
        save_setting('DISK_THRESHOLD', request.form["disk"], 'int')
        save_setting('EMAIL_RECIPIENT', request.form["email"], 'string')
        save_setting('ALARM_ENABLED', "alarm" in request.form, 'bool')
        save_setting('AGGRESSIVE_MODE', "aggressive" in request.form, 'bool')

        # Yüzde olarak gelen hassasiyeti ondalık formata çevirip kaydet
        contamination_percent = float(request.form.get('anomaly_contamination', 5))
        contamination_float = contamination_percent / 100.0
        save_setting('ANOMALY_CONTAMINATION', contamination_float, 'float')

        # Diğer gelişmiş ayarlar
        save_setting('METRICS_RECORD_INTERVAL', request.form["metrics_interval"], 'int')
        save_setting('MIN_SAMPLES_FOR_ML_CONFIG', request.form.get('min_samples_ml', 100), 'int')
        save_setting('RAM_CLEAN_THRESHOLD', request.form.get('ram_clean_threshold', 20.0), 'float')
        save_setting('DISK_CLEAN_THRESHOLD_PERCENT', request.form.get('disk_clean_threshold_percent', 90.0), 'float')
        save_setting('LOG_RETENTION_DAYS', request.form["log_retention_days"], 'int')
        save_setting('DEFAULT_NETWORK_INTERFACE', request.form["default_network_interface"], 'string')
        save_setting('ANOMALY_DETECTION_METHOD', secilen_yontem, 'string')
        flash("Ayarlar başarıyla güncellendi.", "success")

    # Ayarları veritabanından çek ve sayfaya gönder (GET isteği için)
    config_settings = {}
    all_settings = Setting.query.all()
    for setting in all_settings:
        config_settings[setting.key] = convert_value_to_type(setting.value, setting.value_type)
    
    # Veritabanında olmayan ayarlar için varsayılan değerleri ata
    # Bu sayfanın ilk kez yüklenmesinde hata vermesini engeller
    defaults = {
        'CPU_THRESHOLD': 95, 'RAM_THRESHOLD': 95, 'DISK_THRESHOLD': 95,
        'EMAIL_RECIPIENT': 'osmanaydin2016@yandex.com', 'ALARM_ENABLED': True,
        'AGGRESSIVE_MODE': False, 'ANOMALY_DETECTION_METHOD': 'threshold',
        'ANOMALY_CONTAMINATION': 0.1, 'METRICS_RECORD_INTERVAL': 1,
        'MIN_SAMPLES_FOR_ML_CONFIG': 100, 'RAM_CLEAN_THRESHOLD': 20.0,
        'DISK_CLEAN_THRESHOLD_PERCENT': 90.0, 'LOG_RETENTION_DAYS': 30,
        'DEFAULT_NETWORK_INTERFACE': 'lo'
    }
    for key, val in defaults.items():
        config_settings.setdefault(key, val)

    return render_template('settings_page.html', config_settings=config_settings)