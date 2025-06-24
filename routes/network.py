# routes/network.py

from flask import Blueprint, render_template, request, jsonify, current_app, session
import psutil
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from extensions import db
from models import NetworkMetric, Metric
from auth import login_required 

network_routes = Blueprint("network", __name__)
# Yardımcı fonksiyon: Byte değerlerini okunabilir formata çevirir (KB, MB, GB)
def convert_bytes(bytes_val):
    if bytes_val is None:
        return "N/A"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


@network_routes.route("/network", methods=["GET", "POST"])
@login_required 
def network_page():
    message = ""
    selected_interface = current_app.config.get('DEFAULT_NETWORK_INTERFACE', 'lo') 

    with current_app.app_context():
        # Tüm mevcut ağ arayüzlerini al
        interfaces = psutil.net_io_counters(pernic=True)
        interface_names = sorted(list(interfaces.keys()))

        if request.method == "POST":
            # Kullanıcı arayüz seçimini kaydet
            selected_interface = request.form.get("selected_interface", selected_interface)
            current_app.config['DEFAULT_NETWORK_INTERFACE'] = selected_interface
            message = f"✅ Ağ arayüzü '{selected_interface}' olarak ayarlandı."
        
        # NetworkMetric objelerini çek
        recent_network_metrics = db.session.execute(
            db.select(NetworkMetric)
            .filter_by(interface_name=selected_interface)
            .order_by(NetworkMetric.timestamp.desc())
            .limit(21) # Hız hesaplamak için n+1 kayıt gerekli
        ).scalars().all()

        
        recent_network_metrics.reverse() 
        
        network_timestamps = []
        bytes_sent_rates = []
        bytes_recv_rates = []

        if len(recent_network_metrics) > 1:
            for i in range(1, len(recent_network_metrics)):
                prev_m = recent_network_metrics[i-1]
                curr_m = recent_network_metrics[i]
                
                time_diff_seconds = (curr_m.timestamp - prev_m.timestamp).total_seconds()
                
                if time_diff_seconds > 0:
                    sent_diff = curr_m.bytes_sent - prev_m.bytes_sent
                    recv_diff = curr_m.bytes_recv - prev_m.bytes_recv

                    # Hız hesapla (bayt/saniye)
                    bytes_sent_rates.append(sent_diff / time_diff_seconds)
                    bytes_recv_rates.append(recv_diff / time_diff_seconds)
                    network_timestamps.append(curr_m.timestamp.strftime('%H:%M:%S')) 

        # Anlık trafik istatistikleri 
        current_interface_stats = interfaces.get(selected_interface, None)
        total_bytes_sent = current_interface_stats.bytes_sent if current_interface_stats else 0
        total_bytes_recv = current_interface_stats.bytes_recv if current_interface_stats else 0
        
        # Aktif Ağ Bağlantıları 
        connections = []
        for conn in psutil.net_connections(kind='inet'): # Sadece IPv4/IPv6 bağlantıları
            conn_info = {
                'pid': conn.pid,
                'laddr_ip': conn.laddr.ip if conn.laddr else 'N/A',
                'laddr_port': conn.laddr.port if conn.laddr else 'N/A',
                'raddr_ip': conn.raddr.ip if conn.raddr else 'N/A',
                'raddr_port': conn.raddr.port if conn.raddr else 'N/A',
                'status': conn.status
            }
            # Eğer PID varsa proses adını da ekle
            try:
                if conn.pid:
                    proc = psutil.Process(conn.pid)
                    conn_info['process_name'] = proc.name()
                else:
                    conn_info['process_name'] = 'N/A'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                conn_info['process_name'] = 'N/A'
            
            connections.append(conn_info)


    return render_template('network_page.html', 
                           interface_names=interface_names, 
                           selected_interface=selected_interface,
                           total_bytes_sent=convert_bytes(total_bytes_sent),
                           total_bytes_recv=convert_bytes(total_bytes_recv),
                           network_timestamps=network_timestamps,
                           bytes_sent_rates=bytes_sent_rates,
                           bytes_recv_rates=bytes_recv_rates,
                           connections=connections, 
                           message=message)
