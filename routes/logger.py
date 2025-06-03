import logging
import os

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
    return f"""
    <html>
    <head>
        <title>Canlı Loglar</title>
        <style>
            body {{
                background-color: #0f111a;
                color: #e0e0e0;
                font-family: monospace;
                padding: 20px;
            }}
            h1 {{
                color: #00adb5;
                text-align: center;
            }}
            pre {{
                background-color: #1f1f1f;
                padding: 15px;
                border-radius: 6px;
                max-height: 600px;
                overflow-y: scroll;
                border: 1px solid #00adb5;
                line-height: 1.5;
                font-size: 14px;
            }}
            .info {{ color: #00ff7f; }}
            .warning {{ color: #ffae42; }}
            .error {{ color: #ff4d4d; }}
            a {{
                color: #00adb5;
                text-decoration: none;
                display: block;
                margin-top: 20px;
                text-align: center;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <h1>📜 Canlı Loglar</h1>
        <pre id="logContent">Yükleniyor...</pre>
        <a href="/">⬅ Geri dön</a>
        <script>
            function fetchLogs() {{
                fetch('/getlogs')
                    .then(response => response.text())
                    .then(data => {{
                        let lines = data.trim().split('\\n').reverse().join('\\n');
                        lines = lines.replace(/INFO/g, '<span class="info">INFO</span>')
                                     .replace(/WARNING/g, '<span class="warning">WARNING</span>')
                                     .replace(/ERROR/g, '<span class="error">ERROR</span>');
                        document.getElementById('logContent').innerHTML = lines;
                    }});
            }}
            fetchLogs();
            setInterval(fetchLogs, 2000);
        </script>
    </body>
    </html>
    """

def get_logs_content():
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "r") as f:
            return f.read()
    else:
        return "Henüz log dosyası oluşturulmadı."
