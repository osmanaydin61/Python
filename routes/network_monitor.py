import psutil
import os

def get_network_page():
    return f"""
    <html>
    <head>
        <title>Ağ İzleme</title>
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
        <h1>🌐 Ağ İzleme</h1>
        <pre id="networkContent">Yükleniyor...</pre>
        <a href="/">⬅ Geri dön</a>
        <script>
            function fetchNetwork() {{
                fetch('/getnetwork')
                    .then(response => response.text())
                    .then(data => {{
                        document.getElementById('networkContent').innerText = data;
                    }});
            }}
            fetchNetwork();
            setInterval(fetchNetwork, 3000);
        </script>
    </body>
    </html>
    """

def get_network_content():
    import psutil

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
            elif ":" in ip:
                ip_clean = ip
                protokol = "IPv6"
            else:
                ip_clean = ip
                protokol = "IPv4"
            aktifler.append(f"- {ip_clean}:{port} ({protokol})")

    if aktifler:
        content.extend(aktifler)
    else:
        content.append("- Aktif bağlantı bulunamadı.")

    return "\n".join(content)

