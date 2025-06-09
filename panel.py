# panel.py

import os
from dotenv import load_dotenv
load_dotenv()
import time
import threading
# import pandas as pd # Kaldırıldı
import logging
import getpass
import psutil
from flask_wtf.csrf import CSRFProtect
from flask import Flask, jsonify, request, redirect, url_for, current_app
from models import db, Metric, User, Suggestion, Response, Setting, Message, NetworkMetric
from datetime import datetime,UTC
from zoneinfo import ZoneInfo
from auth import auth_routes, login_required, roles_required
from routes.dashboard import dashboard_routes
from routes.settings import settings_routes
from routes.anomaly import anomaly_routes
from routes.tavsiye import tavsiye_routes
from routes.history import history_routes
from routes.user_management import user_management_routes
from routes.network import network_routes 
from routes.logs import get_logs_page, get_logs_content,log_info,log_error,log_warning
from utils.resource_cleaner import clean_ram
from utils.clean_disk_utils import clean_disk
from utils.anomaly_detector import detect_and_log_anomaly, is_critical_process


app = Flask(__name__)
app.secret_key = 'gizli_anahtar'
app.config.from_object('config.Config')
db.init_app(app)
csrf = CSRFProtect(app)
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
# anomaly_records = [] # Kaldırıldı
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
    global metrics, prev_net_io, last_net_time 
    ISTANBUL_TZ = ZoneInfo("Europe/Istanbul") # <-- BURAYI EKLEYİN
    with app.app_context(): 
        while True:
            current_timestamp_istanbul = datetime.now(ISTANBUL_TZ) # <-- BURAYI GÜNCELLEYİN
            current_interval_time = time.time()
            interval_diff = current_interval_time - last_net_time
            
            cpu = psutil.cpu_percent(interval=None) 
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            metrics = {"cpu": cpu, "ram": ram, "disk": disk}
            
            # anomaly_detector'a İstanbul zaman damgasını göndermemiz gerekebilir
            anomaly_data_from_detector = detect_and_log_anomaly(cpu, ram, disk) 

            new_metric_entry = Metric(
                timestamp=current_timestamp_istanbul, # İstanbul zaman damgası
                cpu_percent=cpu,
                ram_percent=ram,
                disk_percent=disk,
                top_cpu_processes=anomaly_data_from_detector.get('top_cpu_processes', '') if anomaly_data_from_detector else '',
                top_ram_processes=anomaly_data_from_detector.get('top_ram_processes', '') if anomaly_data_from_detector else '',
                anomaly=anomaly_data_from_detector.get('anomaly', 0) if anomaly_data_from_detector else 0,
                anomaly_image=anomaly_data_from_detector.get('anomaly_image', '') if anomaly_data_from_detector else '',
                anomaly_type=anomaly_data_from_detector.get('anomaly_type', '') if anomaly_data_from_detector else ''
            )
            db.session.add(new_metric_entry)
            
            current_net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in current_net_io.items():
                if interface in prev_net_io and interval_diff > 0: 
                    new_network_metric = NetworkMetric(
                        timestamp=current_timestamp_istanbul, # İstanbul zaman damgası
                        interface_name=interface,
                        bytes_sent=stats.bytes_sent, 
                        bytes_recv=stats.bytes_recv
                    )
                    db.session.add(new_network_metric)
            
            prev_net_io = current_net_io 
            last_net_time = current_interval_time

            db.session.commit() 
            log_info(f"Metrikler (CPU:{cpu:.1f}%, RAM:{ram:.1f}%, Disk:{disk:.1f}%) ve Ağ metrikleri veritabanına kaydedildi.")


            if anomaly_data_from_detector and anomaly_data_from_detector['anomaly'] == -1: 
                log_info(f"Anomali tespit edildi: CPU:{cpu:.1f}%, RAM:{ram:.1f}%, Disk:{disk:.1f}% - Tip: {anomaly_data_from_detector['anomaly_type']}")

                if current_app.config.get('AGGRESSIVE_MODE', False): 
                    log_info("Otomatik Müdahale modu aktif. Anomali için otomatik temizlik deneniyor...")
                    
                    clean_ram_result = clean_ram()
                    log_info(f"Otomatik RAM Temizliği Sonucu: {clean_ram_result}")
                    clean_disk_result = clean_disk()
                    log_info(f"Otomatik Disk Temizliği Sonucu: {clean_disk_result}")
                else:
                    log_info("Otomatik Müdahale modu pasif. Temizlik yapılmadı.")


            time.sleep(current_app.config.get('METRICS_RECORD_INTERVAL', 2))

# İşlem sonlandırma
@app.route("/killprocess", methods=["POST"])
@login_required
@roles_required("admin")
def kill_process():
    process_name = request.form.get("process")
    if not process_name:
        log_info("Kill Process: İşlem adı bulunamadı.")
        return jsonify({"message": "❌ İşlem adı bulunamadı."})
    
    current_user = getpass.getuser()
    killed = []
    skipped = []
    
    target_process_name_lower = process_name.lower()

    for proc in psutil.process_iter(["pid", "name", "cmdline", "username"]):
        try:
            proc_cmdline = " ".join(proc.info.get("cmdline", [])).lower()
            proc_name_lower = proc.info.get("name", "").lower()
            
            is_target_process = target_process_name_lower in proc_name_lower or \
                                (target_process_name_lower != "python" and target_process_name_lower in proc_cmdline)

            if is_target_process:
                if proc.pid == os.getpid():
                    skipped.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - Kendi Uygulamamız")
                    log_warning(f"Kill Process: Kendi uygulamamız ({proc.info['name']}) sonlandırma isteği atlandı.")
                    continue

                if is_critical_process(process_name=proc_name_lower, cmdline=proc.info.get('cmdline', []), username=proc.info.get('username', '')):
                    skipped.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - Kritik Sistem Süreci")
                    log_warning(f"Kill Process: Kritik sistem süreci ({proc_name_lower}) sonlandırma isteği atlandı.")
                    continue

                if proc.info.get("username") == current_user:
                    try:
                        target_proc = psutil.Process(proc.pid) 
                        target_proc.terminate()            
                        target_proc.wait(timeout=3)       
                        killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
                        log_info(f"Process sonlandırıldı: {proc.info['name']} (PID: {proc.info['pid']})")
                    except psutil.NoSuchProcess:
                        skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Zaten Sonlanmış")
                        log_info(f"Kill Process: Process '{proc.info['name']}' zaten sonlanmış.")
                    except psutil.AccessDenied:
                        skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Erişim Reddedildi")
                        log_error(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) için erişim reddedildi. Yetki sorunu olabilir.")
                    except psutil.TimeoutExpired:
                        try:
                            target_proc.kill() 
                            killed.append(f"{proc.info['name']} (PID: {proc.pid}) [Force Killed]")
                            log_info(f"Process zorla sonlandırıldı: {proc.info['name']} (PID: {proc.pid})")
                        except psutil.NoSuchProcess:
                            skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Zaten Sonlanmış (Timeout sonrası)")
                            log_info(f"Kill Process: Process '{proc.info['name']}' zaten sonlanmış (Timeout sonrası).")
                        except psutil.AccessDenied:
                            skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Erişim Reddedildi (Kill)")
                            log_error(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) için kill erişimi reddedildi. Yetki sorunu olabilir.")
                else:
                    skipped.append(f"{proc.info['name']} (PID: {proc.pid}) - Farklı Kullanıcı ({proc.info.get('username', 'Bilinmiyor')})")
                    log_warning(f"Kill Process: Process '{proc.info['name']}' (PID: {proc.pid}) farklı kullanıcı '{proc.info.get('username', 'Bilinmiyor')}' tarafından çalıştırıldığı için atlandı.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            log_error(f"Kill Process: Process listeleme sırasında hata: {e} - PID: {proc.pid if 'proc' in locals() else 'N/A'}")
            continue
        except Exception as e:
            log_error(f"Kill Process: Beklenmedik hata: {e} - Process: {proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'})")
            skipped.append(f"{proc.info.get('name', 'N/A')} (PID: {proc.pid if 'proc' in locals() else 'N/A'}) - Hata: {str(e)}")
            continue

    msg_parts = []
    if killed:
        msg_parts.append(f"✅ Sonlandırıldı: {', '.join(map(str, killed))}")
    if skipped:
        msg_parts.append(f"⚠️ Atlandı: {', '.join(map(str, skipped))}")
    if not msg_parts:
        msg_parts.append("❌ Eşleşen süreç bulunamadı veya sonlandırılamadı.")
        log_info(f"Kill Process: '{process_name}' için eşleşen süreç bulunamadı veya sonlandırılamadı.")

    return jsonify({"message": "<br>".join(msg_parts)})


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

# Çalıştır
with app.app_context():
    db.create_all()
    load_settings_from_db()
    log_info("Veritabanı tabloları oluşturuldu/kontrol edildi ve ayarlar yüklendi.")

if __name__ == "__main__":
    threading.Thread(target=background_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8080, debug=True)