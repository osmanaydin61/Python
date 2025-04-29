
import logging
import os
from datetime import datetime

# Log klasörü kontrolü
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log dosyasının adı
log_filename = os.path.join(LOG_DIR, "events.log")

# Logger yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

def log_event(message, level="info"):
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    else:
        logging.debug(message)
