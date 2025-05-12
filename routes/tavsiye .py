
# routes/tavsiye.py — Tavsiye sistemi (işlem önerileri)
from flask import Blueprint, render_template_string
from auth import login_required
import psutil

tavsiye_routes = Blueprint("tavsiye", __name__)

@tavsiye_routes.route("/tavsiye")
@login_required
def tavsiye():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    high_cpu_processes = [(p.info['pid'], p.info['name'], p.info['cpu_percent'])
                          for p in psutil.process_iter(['pid', 'name', 'cpu_percent']) if p.info['cpu_percent'] > 30]
    high_ram_processes = [(p.info['pid'], p.info['name'], p.info['memory_percent'])
                          for p in psutil.process_iter(['pid', 'name', 'memory_percent']) if p.info['memory_percent'] > 30]

    tavsiye = "🧠 Sistem Durumu Analizi:<br><br>"

    if cpu > cpu_threshold:
        tavsiye += f"⚠️ CPU kullanımı yüksek: {cpu:.2f}%<br>"
    else:
        tavsiye += f"✅ CPU kullanımı normal: {cpu:.2f}%<br>"

    if ram > ram_threshold:
        tavsiye += f"⚠️ RAM kullanımı yüksek: {ram:.2f}%<br>"
    else:
        tavsiye += f"✅ RAM kullanımı normal: {ram:.2f}%<br>"

    if disk > disk_threshold:
        tavsiye += f"⚠️ Disk doluluk oranı çok yüksek: {disk:.2f}%<br>"
        tavsiye += f"<a href='/disktemizle' style='color:green;'>🧹 Şimdi Disk Temizle</a><br>"
    else:
        tavsiye += f"✅ Disk kullanımı normal: {disk:.2f}%<br>"

    if high_cpu_processes:
        tavsiye += "<br>🔍 Yüksek CPU kullanan işlemler:<br>"
        for pid, name, cpu_use in high_cpu_processes:
            tavsiye += f"- {name} (PID: {pid}) → {cpu_use:.2f}% CPU<br>"

    if high_ram_processes:
        tavsiye += "<br>🔍 Yüksek RAM kullanan işlemler:<br>"
        for pid, name, ram_use in high_ram_processes:
            tavsiye += f"- {name} (PID: {pid}) → {ram_use:.2f}% RAM<br>"

    return render_template_string(f"""
        <h2>🧠 Sistem Yorum ve Öneri</h2>
        <p>{tavsiye}</p>
        <a href='/'>⬅ Geri dön</a>
    """)
