import psutil
import os
import signal

def clean_ram():
    threshold = 20.0  # %20'den fazla RAM kullananlar kapatılacak
    killed = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            if proc.info['memory_percent'] > threshold:
                os.kill(proc.info['pid'], signal.SIGKILL)
                killed.append(f"{proc.info['name']} (PID: {proc.info['pid']}) - %{proc.info['memory_percent']:.1f}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"✅ RAM temizlendi. Kapatılanlar: " + ", ".join(killed)
    else:
        return "✅ Kapatılacak işlem yok."
