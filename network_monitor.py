
import psutil
from logger import log_event

def check_network_usage():
    log_event("🌐 Ağ trafiği kontrolü başlatıldı.")
    try:
        net_io = psutil.net_io_counters(pernic=True)
        for interface, stats in net_io.items():
            sent_mb = stats.bytes_sent / (1024 ** 2)
            recv_mb = stats.bytes_recv / (1024 ** 2)
            log_event(f"📡 Interface: {interface} - Gönderilen: {sent_mb:.2f} MB | Alınan: {recv_mb:.2f} MB")
    except Exception as e:
        log_event(f"Ağ kontrolünde hata oluştu: {e}", level="error")

if __name__ == "__main__":
    check_network_usage()
