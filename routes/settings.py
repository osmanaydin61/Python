from flask import Blueprint, request
from auth import login_required, roles_required
from cloudwatch.CloudWatch import send_email_alert

settings_routes = Blueprint("settings", __name__)
cpu_threshold = 90
ram_threshold = 90
disk_threshold = 99
email_recipient = "ornek@example.com"
alarm_enabled = True
aggressive_mode = False

@settings_routes.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def settings():
    global cpu_threshold, ram_threshold, disk_threshold, email_recipient, alarm_enabled, aggressive_mode
    message = ""
    if request.method == "POST":
        cpu_threshold = int(request.form["cpu"])
        ram_threshold = int(request.form["ram"])
        disk_threshold = int(request.form["disk"])
        email_recipient = request.form["email"]
        alarm_enabled = "alarm" in request.form
        aggressive_mode = "aggressive" in request.form

        if "testmail" in request.form:
            try:
                send_email_alert(email_recipient, "Test Mail", "Bu bir test mailidir.")
                message = "✅ Test maili başarıyla gönderildi."
            except Exception as e:
                message = f"❌ Test maili gönderilemedi: {str(e)}"
        else:
            message = "✅ Ayarlar başarıyla güncellendi."

    return f"""
    <html>
    <head>
        <title>Ayarlar</title>
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
            form {{
                background-color: #1f1f1f;
                padding: 20px;
                border-radius: 6px;
                max-width: 500px;
                margin: auto;
                border: 1px solid #00adb5;
            }}
            label {{
                display: block;
                margin: 10px 0 5px;
                font-weight: bold;
            }}
            input[type='number'], input[type='email'] {{
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: none;
                background-color: #333;
                color: #fff;
            }}
            input[type='checkbox'] {{
                margin-right: 8px;
            }}
            button {{
                margin-top: 15px;
                padding: 8px 16px;
                background: #00adb5;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{
                background: #009baa;
            }}
            .testmail {{
                background: #2196f3;
            }}
            .testmail:hover {{
                background: #1976d2;
            }}
            p {{
                text-align: center;
                margin-top: 20px;
                color: #00ff7f;
            }}
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
        <h1>⚙️ Ayarlar</h1>
        <form method="POST">
            <label>CPU Alarm Eşiği (%)</label>
            <input type="number" name="cpu" value="{cpu_threshold}" required>

            <label>RAM Alarm Eşiği (%)</label>
            <input type="number" name="ram" value="{ram_threshold}" required>

            <label>Disk Alarm Eşiği (%)</label>
            <input type="number" name="disk" value="{disk_threshold}" required>

            <label>E-posta Adresi</label>
            <input type="email" name="email" value="{email_recipient}" required>

            <label><input type="checkbox" name="alarm" {'checked' if alarm_enabled else ''}> Alarm Aktif</label>
            <label><input type="checkbox" name="aggressive" {'checked' if aggressive_mode else ''}> Otomatik Müdahale</label>

            <button type="submit">Kaydet</button>
            <button type="submit" name="testmail" class="testmail">📨 Test Mail Gönder</button>
        </form>
        <p>{message}</p>
        <a href="/">⬅ Geri Dön</a>
    </body>
    </html>
    """
