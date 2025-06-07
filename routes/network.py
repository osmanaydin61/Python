# routes/network_monitor.py
import psutil
from flask import render_template, request # request ekle (eğer kullanılıyorsa)
# ... (diğer importlar)

def get_network_page():
    # Bu route'un çalışması için templates/network_page.html dosyası olmalı
    return render_template('network_page.html')

def get_network_content():
    # ... (ağ metrikleri toplama mantığı) ...
    net_io = psutil.net_io_counters()
    interfaces = psutil.net_if_addrs()
    connections = psutil.net_connections()

    content = []
    content.append(f"🛜 Toplam Gönderilen (Upload): {net_io.bytes_sent / (1024*1024):.2f} MB (Sistemden dışa gönderilen toplam veri miktarı)")
    content.append(f"🛜 Toplam Alınan (Download): {net_io.bytes_recv / (1024*1024):.2f} MB (Sisteme dışarıdan alınan toplam veri miktarı)")

    content.append("\n🌐 Ağ Arayüzleri (Bağlantı Noktaları):")
    for iface in interfaces:
        açıklama = " (Sanal ağ)" if iface.startswith("docker") or iface.startswith("br-") else " (Ana ağ kartı veya Wi-Fi)" if iface.startswith("eth") or iface.startswith("ens") or iface.startswith("wlan") else " (Sistem içi - localhost)" if iface == "lo" else ""
        content.append(f"- {iface}{açıklama}")

    content.append("\n🔗 Aktif Bağlantılar:")
    aktifler = []
    for conn in connections:
        if conn.status == 'ESTABLISHED' and conn.raddr:
            ip = conn.raddr.ip
            port = conn.raddr.port
            if ip.startswith("::ffff:"):
                ip_clean = ip.split("::ffff:")[-1]
                protokol = "IPv4"
            elif ":" in ip: # IPv6 adresleri için
                ip_clean = ip
                protokol = "IPv6"
            else: # Varsayılan IPv4
                ip_clean = ip
                protokol = "IPv4"
            aktifler.append(f"  - {ip_clean}:{port} ({conn.laddr.ip}:{conn.laddr.port}) | {protokol} | Durum: {conn.status}")
    if not aktifler:
        content.append("  - Aktif bağlantı bulunamadı.")
    else:
        content.extend(aktifler)

    return "\n".join(content)