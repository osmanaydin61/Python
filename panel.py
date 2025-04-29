
from flask import Flask, render_template_string, redirect, url_for, request
import os
from resource_cleaner import clean_ram, clean_disk
from network_monitor import check_network_usage
from graph_generator import generate_system_graphs
from CloudWatch import send_email_alert  # Doğru fonksiyon adı düzeltildi

app = Flask(__name__, static_folder='static')

cpu_threshold = 80
ram_threshold = 80
disk_threshold = 90
alarm_enabled = True
email_recipient = "ornek@example.com"

@app.route("/")
def home():
    generate_system_graphs()
    return render_template_string("""
        <h1>🛠️ Sistem Kontrol Paneli</h1>
        <h2>📊 Canlı Sistem Grafikleri</h2>
        <img src='/static/cpu.png' width='300'>
        <img src='/static/ram.png' width='300'>
        <img src='/static/disk.png' width='300'>
        <hr>
        <p><a href='/clean'>🧹 RAM & Disk Temizliği Yap</a></p>
        <p><a href='/network'>🌐 Ağ Trafiğini Görüntüle</a></p>
        <p><a href='/logs'>📜 Olay Loglarını Görüntüle</a></p>
        <p><a href='/testmail'>📨 Test Mail Gönder</a></p>
        <p><a href='/ayarlar'>⚙️ Alarm Ayarları</a></p>
    """)

@app.route("/clean")
def clean():
    clean_ram()
    clean_disk()
    return redirect(url_for("home"))

@app.route("/network")
def network():
    from io import StringIO
    import sys

    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result

    check_network_usage()

    sys.stdout = old_stdout
    output = result.getvalue().replace("\n", "<br>")
    return f"<h2>🌐 Ağ Kullanımı</h2><p>{output}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/logs")
def logs():
    try:
        with open("logs/events.log", "r") as f:
            content = f.read().replace("\n", "<br>")
    except FileNotFoundError:
        content = "Log dosyası bulunamadı."
    return f"<h2>📜 Loglar</h2><p>{content}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/testmail")
def testmail():
    try:
        if alarm_enabled:
            send_email_alert("🔔 Test Mail", f"Bu bir test mesajıdır. Alıcı: {email_recipient}")
            return "<p>✅ Test mail gönderildi.</p><a href='/'>⬅ Geri dön</a>"
        else:
            return "<p>⚠️ Alarm sistemi devre dışı.</p><a href='/'>⬅ Geri dön</a>"
    except Exception as e:
        return f"<p>❌ Mail gönderilemedi: {str(e)}</p><a href='/'>⬅ Geri dön</a>"

@app.route("/ayarlar", methods=["GET", "POST"])
def ayarlar():
    global cpu_threshold, ram_threshold, disk_threshold, email_recipient, alarm_enabled
    if request.method == "POST":
        cpu_threshold = int(request.form["cpu"])
        ram_threshold = int(request.form["ram"])
        disk_threshold = int(request.form["disk"])
        email_recipient = request.form["email"]
        alarm_enabled = "alarm" in request.form
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
            <input type='checkbox' name='alarm' {% if alarm %}checked{% endif %}><br><br>
            <button type='submit'>Kaydet</button>
        </form>
        <a href='/'>⬅ Geri dön</a>
    """, cpu=cpu_threshold, ram=ram_threshold, disk=disk_threshold, email=email_recipient, alarm=alarm_enabled)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
