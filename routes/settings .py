
# routes/settings.py — Alarm eşikleri ve ayarlar paneli
from flask import Blueprint, render_template_string, request, redirect, url_for
from auth import login_required, roles_required

settings_routes = Blueprint("settings", __name__)
cpu_threshold = 80
ram_threshold = 85
disk_threshold = 90
email_recipient = "ornek@example.com"

@settings_routes.route("/ayarlar", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def ayarlar():
    global cpu_threshold, ram_threshold, disk_threshold, email_recipient, alarm_enabled, aggressive_mode
    if request.method == "POST":
        cpu_threshold = int(request.form["cpu"])
        ram_threshold = int(request.form["ram"])
        disk_threshold = int(request.form["disk"])
        email_recipient = request.form["email"]
        alarm_enabled = "alarm" in request.form
        aggressive_mode = "aggressive" in request.form
        return redirect(url_for("ayarlar"))
    return render_template_string("""
        <h2>⚙️ Alarm Ayarları</h2>
        <form method='post'>
            <label>CPU Alarm Eşiği (%):</label>
            <input type='number' name='cpu' value='{{cpu}}'><br><br>
            <label>RAM Alarm Eşiği (%):</label>
            <input type='number' name='ram' value='{{ram}}'><br><br>
            <label>Disk Alarm Eşiği (%):</label>
            <input type='number' name='disk' value='{{disk}}'><br><br>
            <label>E-posta Adresi:</label>
            <input type='email' name='email' value='{{email}}'><br><br>
            <label>Alarm Aktif:</label>
            <input type='checkbox' name='alarm' {% if alarm %}checked{% endif %}><br>
            <label>Otomatik Müdahale:</label>
            <input type='checkbox' name='aggressive' {% if aggressive %}checked{% endif %}><br><br>
            <button type='submit'>Kaydet</button>
        </form>
        <a href='/'>⬅ Geri dön</a>
    """, cpu=cpu_threshold, ram=ram_threshold, disk=disk_threshold, email=email_recipient, alarm=alarm_enabled, aggressive=aggressive_mode)
