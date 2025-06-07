# routes/logger.py
import logging
import os
from flask import render_template, request

# --- Loglama Ayarları ve Fonksiyonları ---
LOG_FILE_PATH = os.path.join("logs", "system.log")
os.makedirs("logs", exist_ok=True)

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
    return render_template('logs_page.html')
   

def get_logs_content():
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as f:
            return f.read()
    else:
        return "Henüz log dosyası oluşturulmadı."