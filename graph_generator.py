
import psutil
import matplotlib.pyplot as plt
from datetime import datetime
import os
from logger import log_event

def generate_system_graphs():
    log_event("📊 Sistem grafikleri oluşturuluyor...")

    # Sistem verilerini al
    psutil.cpu_percent(interval=None)  # ilk boş okuma
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Grafiklerin kaydedileceği klasör
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)

    # CPU Grafiği
    plt.figure()
    plt.title("CPU Kullanımı (%)")
    plt.bar(["CPU"], [cpu_percent])
    plt.ylim(0, 100)
    plt.ylabel("%")
    plt.text(0, cpu_percent + 2, f"{cpu_percent:.1f}%", ha='center', fontsize=12, fontweight='bold')
    plt.savefig(os.path.join(static_dir, "cpu.png"))
    plt.close()

    # RAM Grafiği
    plt.figure()
    plt.title("RAM Kullanımı (%)")
    plt.bar(["RAM"], [ram.percent])
    plt.ylim(0, 100)
    plt.ylabel("%")
    plt.text(0, ram.percent + 2, f"{ram.percent:.1f}%", ha='center', fontsize=12, fontweight='bold')
    plt.savefig(os.path.join(static_dir, "ram.png"))
    plt.close()

    # Disk Grafiği
    plt.figure()
    plt.title("Disk Kullanımı (%)")
    plt.bar(["Disk"], [disk.percent])
    plt.ylim(0, 100)
    plt.ylabel("%")
    plt.text(0, disk.percent + 2, f"{disk.percent:.1f}%", ha='center', fontsize=12, fontweight='bold')
    plt.savefig(os.path.join(static_dir, "disk.png"))
    plt.close()

    log_event("✅ Grafikler oluşturuldu: cpu.png, ram.png, disk.png")

if __name__ == "__main__":
    generate_system_graphs()
