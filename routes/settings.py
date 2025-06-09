from flask import Blueprint, request, render_template, current_app
from auth import login_required, roles_required
from cloudwatch.CloudWatch import send_email_alert # E-posta gönderme fonksiyonu hala kullanılacak

# VERİTABANI İMPORTLARI
from models import db, Setting # db ve Setting modelini import edin

settings_routes = Blueprint("settings", __name__)

# Yardımcı fonksiyon: Ayarı veritabanına kaydeder
def save_setting(key, value, value_type):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value) # String olarak sakla
        setting.value_type = value_type
    else:
        setting = Setting(key=key, value=str(value), value_type=value_type)
        db.session.add(setting)
    db.session.commit()
    # current_app.config'i de anında güncelle
    current_app.config[key] = convert_value_to_type(str(value), value_type)


# Yardımcı fonksiyon: Veritabanından okunan string değeri doğru tipine çevirir
def convert_value_to_type(value_str, value_type):
    if value_type == 'int':
        return int(value_str)
    elif value_type == 'float':
        return float(value_str)
    elif value_type == 'bool':
        return value_str.lower() == 'true'
    return value_str # string ise olduğu gibi döndür


@settings_routes.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def settings():
    message = ""
    with current_app.app_context():
        if request.method == "POST":
            # ... (mevcut ayar kayıtları aynı kalır)
            save_setting('CPU_THRESHOLD', request.form["cpu"], 'int')
            save_setting('RAM_THRESHOLD', request.form["ram"], 'int')
            save_setting('DISK_THRESHOLD', request.form["disk"], 'int')
            save_setting('EMAIL_RECIPIENT', request.form["email"], 'string')
            save_setting('ALARM_ENABLED', "alarm" in request.form, 'bool')
            save_setting('AGGRESSIVE_MODE', "aggressive" in request.form, 'bool')
            
            save_setting('METRICS_RECORD_INTERVAL', request.form["metrics_interval"], 'int')
            save_setting('ANOMALY_CONTAMINATION', request.form["anomaly_contamination"], 'float')
            save_setting('MIN_SAMPLES_FOR_ML_CONFIG', request.form["min_samples_ml"], 'int')
            save_setting('RAM_CLEAN_THRESHOLD', request.form["ram_clean_threshold"], 'float')
            save_setting('DISK_CLEAN_THRESHOLD_PERCENT', request.form["disk_clean_threshold_percent"], 'float')
            save_setting('LOG_RETENTION_DAYS', request.form["log_retention_days"], 'int')

            # Yeni: Varsayılan ağ arayüzü ayarı
            save_setting('DEFAULT_NETWORK_INTERFACE', request.form["default_network_interface"], 'string')


            message = "✅ Ayarlar başarıyla güncellendi."

        config_settings = {}
        all_settings = Setting.query.all()
        for setting in all_settings:
            config_settings[setting.key] = convert_value_to_type(setting.value, setting.value_type)
        
        # ... (setdefault ile varsayılan değerleri kontrol etme kısmı aynı kalır)
        # Yeni eklediğimiz ayarlar için setdefault
        config_settings.setdefault('METRICS_RECORD_INTERVAL', current_app.config.get('METRICS_RECORD_INTERVAL'))
        config_settings.setdefault('ANOMALY_CONTAMINATION', current_app.config.get('ANOMALY_CONTAMINATION'))
        config_settings.setdefault('MIN_SAMPLES_FOR_ML_CONFIG', current_app.config.get('MIN_SAMPLES_FOR_ML_CONFIG'))
        config_settings.setdefault('RAM_CLEAN_THRESHOLD', current_app.config.get('RAM_CLEAN_THRESHOLD'))
        config_settings.setdefault('DISK_CLEAN_THRESHOLD_PERCENT', current_app.config.get('DISK_CLEAN_THRESHOLD_PERCENT'))
        config_settings.setdefault('LOG_RETENTION_DAYS', current_app.config.get('LOG_RETENTION_DAYS'))
        config_settings.setdefault('DEFAULT_NETWORK_INTERFACE', current_app.config.get('DEFAULT_NETWORK_INTERFACE', 'lo')) # Yeni ayar için varsayılan

    return render_template('settings_page.html', config_settings=config_settings, message=message)