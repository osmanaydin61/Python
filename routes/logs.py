# routes/logger.py
import logging
import os
from flask import render_template, request, current_app

# --- Loglama Ayarları ve Fonksiyonları ---

# LOG_FILE_PATH'i Flask uygulamasının kök dizinine göre dinamik olarak tanımlayın
# __file__ routes/logger.py'nin konumudur. os.pardir ile routes'dan bir üst dizine (proje köküne) çıkıyoruz.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOG_FOLDER_PATH = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "system.log")

# Log klasörünü oluştur
os.makedirs(LOG_FOLDER_PATH, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def get_logs_page():
    # Bu route'un çalışması için templates/logs_page.html dosyası olmalı
    try:
        return render_template('logs_page.html')
    except Exception as e:
        print(f"Log sayfası render edilirken hata: {e}")
        return "Log sayfası yüklenemedi. Şablon dosyasını kontrol edin.", 500

def get_logs_content():
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r") as f:
                return f.read()
        except Exception as e:
            log_error(f"Log dosyası okunurken hata: {e}")
            return "Log dosyası okunamadı.", 500
    else:
        log_error(f"Log dosyası bulunamadı: {LOG_FILE_PATH}")
        return "Henüz log dosyası oluşturulmadı veya bulunamadı.", 404