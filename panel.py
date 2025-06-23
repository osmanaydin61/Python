# panel.py
import os
import time
import threading
import logging
import psutil
from flask import Flask, jsonify, request, current_app
from dotenv import load_dotenv
import getpass
load_dotenv()

# Önce eklentileri ve modelleri import et
from extensions import db, csrf, mail, bcrypt
from models import Metric, Setting

# Sonra diğerlerini
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from routes.history import history_routes
from routes.user_management import user_management_routes
from routes.network import network_routes
from routes.logs import get_logs_page, get_logs_content, log_info, log_error, log_warning
from utils.resource_cleaner import clean_ram
from utils.clean_disk_utils import clean_disk
from utils.anomaly_detector import detect_and_log_anomaly, is_critical_process

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'
app.config.from_object('config.Config')
# Eklentileri Başlat
db.init_app(app)
csrf.init_app(app)
mail.init_app(app)
bcrypt.init_app(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Blueprint kayıtları
app.register_blueprint(auth_routes)
app.register_blueprint(dashboard_routes)
app.register_blueprint(settings_routes)
app.register_blueprint(anomaly_routes)
app.register_blueprint(tavsiye_routes)
app.register_blueprint(history_routes)
app.register_blueprint(network_routes)
app.register_blueprint(user_management_routes)

# Global veriler
metrics = {"cpu": 0, "ram": 0, "disk": 0} 
prev_net_io = psutil.net_io_counters(pernic=True)
last_net_time = time.time()

# Yardımcı fonksiyon: Veritabanından okunan string değeri doğru tipine çevirir
def convert_value_to_type(value_str, value_type):
    if value_type == 'int':
        return int(value_str)
    elif value_type == 'float':
        return float(value_str)
    elif value_type == 'bool':
        return value_str.lower() == 'true'
    return value_str 

# Uygulama başlatıldığında veritabanındaki ayarları yükle
def load_settings_from_db():
    with app.app_context():
        default_settings = {
            'CPU_THRESHOLD': {'value': str(app.config.get('CPU_THRESHOLD')), 'type': 'int'},
            'RAM_THRESHOLD': {'value': str(app.config.get('RAM_THRESHOLD')), 'type': 'int'},
            'DISK_THRESHOLD': {'value': str(app.config.get('DISK_THRESHOLD')), 'type': 'int'},
            'EMAIL_RECIPIENT': {'value': str(app.config.get('EMAIL_RECIPIENT')), 'type': 'string'},
            'ALARM_ENABLED': {'value': str(app.config.get('ALARM_ENABLED')), 'type': 'bool'},
            'AGGRESSIVE_MODE': {'value': str(app.config.get('AGGRESSIVE_MODE')), 'type': 'bool'},
            'METRICS_RECORD_INTERVAL': {'value': str(app.config.get('METRICS_RECORD_INTERVAL')), 'type': 'int'},
            'ANOMALY_CONTAMINATION': {'value': str(app.config.get('ANOMALY_CONTAMINATION')), 'type': 'float'},
            'MIN_SAMPLES_FOR_ML_CONFIG': {'value': str(app.config.get('MIN_SAMPLES_FOR_ML_CONFIG')), 'type': 'int'},
            'RAM_CLEAN_THRESHOLD': {'value': str(app.config.get('RAM_CLEAN_THRESHOLD')), 'type': 'float'},
            'DISK_CLEAN_THRESHOLD_PERCENT': {'value': str(app.config.get('DISK_CLEAN_THRESHOLD_PERCENT')), 'type': 'float'},
            'LOG_RETENTION_DAYS': {'value': str(app.config.get('LOG_RETENTION_DAYS')), 'type': 'int'},
            'DEFAULT_NETWORK_INTERFACE': {'value': str(app.config.get('DEFAULT_NETWORK_INTERFACE', 'lo')), 'type': 'string'}, 
        }

        for key, default_val in default_settings.items():
            setting = Setting.query.filter_by(key=key).first()
            if not setting: 
                new_setting = Setting(key=key, value=default_val['value'], value_type=default_val['type'])
                db.session.add(new_setting)
            else: 
                app.config[setting.key] = convert_value_to_type(setting.value, setting.value_type)
        db.session.commit()
        log_info("Veritabanındaki ayarlar yüklendi veya varsayılanlar eklendi.")


# Arka planda metrik toplama
def background_thread():
    global metrics
    with app.app_context():
        psutil.cpu_percent(interval=None) 
        time.sleep(1)
        while True:
            try:
                # Metrikleri topla
                cpu = psutil.cpu_percent(interval=1) 
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                metrics = {"cpu": cpu, "ram": ram, "disk": disk}

                # Anomali tespiti için fonksiyonu çağır
                anomaly_data = detect_and_log_anomaly(cpu, ram, disk)

                # Yeni metrik kaydını oluştur
                metric_entry = Metric(
                    timestamp=datetime.now(ZoneInfo("Europe/Istanbul")),
                    cpu_percent=cpu,
                    ram_percent=ram,
                    disk_percent=disk
                )
                
                # Eğer anomali tespit edildiyse, metrik kaydına anomali bilgilerini ekle
                if anomaly_data:
                    
                    metric_entry.is_anomaly = anomaly_data.get('is_anomaly', False)
                    metric_entry.anomaly_type = anomaly_data.get('anomaly_type')
                    metric_entry.pid = anomaly_data.get('pid')
                    metric_entry.process_name = anomaly_data.get('process_name')
                    metric_entry.top_cpu_processes = anomaly_data.get('top_cpu_processes')
                    metric_entry.top_ram_processes = anomaly_data.get('top_ram_processes')
                    metric_entry.anomaly_image = anomaly_data.get('anomaly_image')

                db.session.add(metric_entry)
                db.session.commit()
                # Otomatik müdahale modu kontrolü
                
                if anomaly_data and anomaly_data.get('is_anomaly'):
                    log_info(f"Anomali tespit edildi: Tip: {anomaly_data['anomaly_type']}")
                    if current_app.config.get('AGGRESSIVE_MODE', False):
                        log_info("Otomatik Müdahale modu aktif. Temizlik deneniyor...")
                        clean_ram()
                        clean_disk()
                    else:
                        log_info("Otomatik Müdahale modu pasif.")

                # Ayarlanan aralık kadar bekle
                sleep_time = max(1, current_app.config.get('METRICS_RECORD_INTERVAL', 5) - 1)
                time.sleep(sleep_time)

            except Exception as e:
                log_error(f"Arka plan iş parçacığında kritik hata: {e}")
                time.sleep(10) # Hata durumunda biraz daha uzun bekle

# İşlem sonlandırma
@app.route("/killprocess", methods=["POST"])
@login_required
@roles_required("admin")
def kill_process():
    pid = request.form.get('pid', type=int)
    if not pid:
        log_warning("Kill Process: Geçersiz PID gönderildi.")
        return jsonify({"message": "❌ Geçersiz işlem kimliği."}), 400

    try:
        # Gerekli tüm bilgileri en başta tek seferde alalım
        proc = psutil.Process(pid)
        proc_info = proc.as_dict(attrs=['pid', 'name', 'username', 'cmdline'])

        # Güvenlik Kontrolü 1: Kendi uygulamasını sonlandırmayı engelle
        if proc_info.get('pid') == os.getpid():
            log_warning(f"Kill Process: Kendi uygulamasını (PID: {pid}) sonlandırma engellendi.")
            return jsonify({"message": "⚠️ Kendi çalışan uygulamanızı sonlandıramazsınız."}), 403
            
        
        # Artık fonksiyona tek bir bilgi paketi (proc_info) gönderiyoruz.
        if is_critical_process(proc_info):
            log_warning(f"Kill Process: Kritik süreç '{proc_info.get('name')}' (PID: {pid}) sonlandırma engellendi.")
            return jsonify({"message": f"⚠️ '{proc_info.get('name')}' kritik bir sistem sürecidir, sonlandırılamaz."}), 403

        # İşlemi Sonlandır
        proc_name = proc_info.get('name', 'N/A')
        proc.terminate()
        try:
            proc.wait(timeout=3) # İşlemin sonlanması için 3 saniye bekle
            log_info(f"İşlem sonlandırıldı: {proc_name} (PID: {pid})")
            return jsonify({"message": f"✅ İşlem '{proc_name}' (PID: {pid}) başarıyla sonlandırıldı."})
        except psutil.TimeoutExpired:
            proc.kill() # Kapanmazsa zorla kapat
            log_warning(f"İşlem zorla sonlandırıldı (kill): {proc_name} (PID: {pid})")
            return jsonify({"message": f"✅ İşlem '{proc_name}' (PID: {pid}) zorla sonlandırıldı."})

    except psutil.NoSuchProcess:
        log_warning(f"Kill Process: Sonlandırılmak istenen işlem (PID: {pid}) zaten mevcut değil.")
        return jsonify({"message": f"🤷‍♀️ İşlem (PID: {pid}) zaten çalışmıyor."}), 404
    except psutil.AccessDenied as e:
        log_error(f"Kill Process: İşlem (PID: {pid}) için erişim engellendi. Hata: {e}")
        return jsonify({"message": f"❌ Yetki Hatası: İşlemi (PID: {pid}) sonlandırma izniniz yok."}), 403
    except Exception as e:
        log_error(f"Kill Process: Beklenmedik bir hata oluştu: {e}")
        return jsonify({"message": "💥 Beklenmedik bir hata oluştu."}), 500


# RAM temizleme
@app.route("/clean")
@login_required
@roles_required("admin")
def clean():
    result = clean_ram()
    log_info(result)
    return result

# Disk temizleme
@app.route("/disktemizle")
@login_required
@roles_required("admin")
def disktemizle():
    result = clean_disk()
    log_info(result)
    return result

# Metrikler (JSON)
@app.route("/metrics")
def get_metrics():
    return jsonify(metrics)

# Context
@app.context_processor
def inject_helpers():
    import random
    return dict(random=random.random, zip=zip)

@app.context_processor
def inject_random():
    import random
    return dict(random=random.random)

@app.route("/logs")
@login_required
def logs_page():
    return get_logs_page()

@app.route("/getlogs")
@login_required
def get_logs():
    return get_logs_content()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_settings_from_db()
        log_info("Veritabanı tabloları oluşturuldu/kontrol edildi ve ayarlar yüklendi.")
        
            
    threading.Thread(target=background_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, debug=True)