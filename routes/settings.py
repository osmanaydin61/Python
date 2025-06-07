
from flask import Blueprint, request, render_template, current_app # current_app'i import edin
from auth import login_required, roles_required
from cloudwatch.CloudWatch import send_email_alert

settings_routes = Blueprint("settings", __name__)

# global cpu_threshold, ram_threshold, ... satırlarını SİLİN.

@settings_routes.route("/settings", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def settings():
    message = ""
    if request.method == "POST":
        # Ayarları app.config üzerinden güncelle
        current_app.config['CPU_THRESHOLD'] = int(request.form["cpu"])
        current_app.config['RAM_THRESHOLD'] = int(request.form["ram"])
        current_app.config['DISK_THRESHOLD'] = int(request.form["disk"])
        current_app.config['EMAIL_RECIPIENT'] = request.form["email"]
        current_app.config['ALARM_ENABLED'] = "alarm" in request.form
        current_app.config['AGGRESSIVE_MODE'] = "aggressive" in request.form

        if "testmail" in request.form:
            try:
                # E-posta alıcısını config'den al
                recipient_from_config = current_app.config.get('EMAIL_RECIPIENT', 'varsayilan@mail.com')
                send_email_alert(recipient_from_config, "Test Mail", "Bu bir test mailidir.")
                message = "✅ Test maili başarıyla gönderildi."
            except Exception as e:
                message = f"❌ Test maili gönderilemedi: {str(e)}"
        else:
            message = "✅ Ayarlar başarıyla güncellendi."

    # Mevcut ayarları template'e göndermek için:
    config_settings = {
        'cpu': current_app.config.get('CPU_THRESHOLD'),
        'ram': current_app.config.get('RAM_THRESHOLD'),
        'disk': current_app.config.get('DISK_THRESHOLD'),
        'email': current_app.config.get('EMAIL_RECIPIENT'),
        'alarm': current_app.config.get('ALARM_ENABLED'),
        'aggressive': current_app.config.get('AGGRESSIVE_MODE')
    }

    return render_template('settings_page.html', config_settings=config_settings, message=message) # message'ı da context'e ekledik