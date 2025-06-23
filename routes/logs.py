# routes/logs.py (Zaman Dilimi Düzeltilmiş Hali)

import logging
import os
from flask import render_template
from datetime import datetime
from zoneinfo import ZoneInfo

# Proje kök dizinini ve log dosyasının yolunu belirle
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOG_FOLDER_PATH = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "system.log")

# Log klasörünü oluştur
os.makedirs(LOG_FOLDER_PATH, exist_ok=True)

# Zaman dilimini dikkate alan özel Formatter sınıfı
class TimezoneFormatter(logging.Formatter):
    """Log kayıt zamanını yerel saat dilimine çeviren formatlayıcı."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, ZoneInfo("Europe/Istanbul"))
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Eğer logger'a daha önce handler eklenmediyse (yeniden başlatmalarda çift logu önler)
if not logger.handlers:
    # Dosyaya yazacak bir handler oluştur
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    
    # Özel formatlayıcımızı oluştur ve handler'a ata
    formatter = TimezoneFormatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    # Handler'ı ana logger'a ekle
    logger.addHandler(file_handler)

def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)


def get_logs_page():
    try:
        return render_template('logs_page.html')
    except Exception as e:
        print(f"Log sayfası render edilirken hata: {e}")
        return "Log sayfası yüklenemedi. Şablon dosyasını kontrol edin.", 500

def get_logs_content():
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log_error(f"Log dosyası okunurken hata: {e}")
            return "Log dosyası okunamadı.", 500
    else:
        log_error(f"Log dosyası bulunamadı: {LOG_FILE_PATH}")
        return "Henüz log dosyası oluşturulmadı veya bulunamadı.", 404