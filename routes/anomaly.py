# routes/anomaly.py

from flask import Blueprint, render_template, request, jsonify
from auth import login_required
import os
import pandas as pd
import psutil
from utils.anomaly_detector import is_critical_process
# from datetime import datetime, timedelta # Artık burada gerek yok, history.py'ye taşındı

anomaly_routes = Blueprint("anomaly", __name__)

@anomaly_routes.route("/anomali")
@login_required
def anomaly():
    if not os.path.exists("metrics_history.csv"):
        return "<p>Veri dosyası bulunamadı.</p>"
    
    df = pd.read_csv("metrics_history.csv")
    
    anomaly_rows = df[
        (df['anomaly'] == -1) & 
        (df['top_cpu_processes'].notna()) & 
        (df['top_cpu_processes'] != '')
    ].copy() # .copy() ekleyelim, filtreleme sonrası yeni DataFrame oluşturmak için

    # 'anomaly_type' sütunu yoksa, hata almamak için varsayılan bir değer atayalım
    if 'anomaly_type' not in anomaly_rows.columns:
        anomaly_rows['anomaly_type'] = ''

    anomaly_rows = anomaly_rows.drop_duplicates(subset=['top_cpu_processes'], keep='last')
    anomaly_rows = anomaly_rows.tail(5) # En son 5 anomaliliği göster

    active_processes_info = []
    # psutil.process_iter'a ek olarak 'pid' de ekleyelim
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'username']): 
        try:
            active_processes_info.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    filtered_rows = []
    for index, row in anomaly_rows.iterrows(): # index'i de alalım, daha sonra kullanabiliriz
        proc_name_full_str = row['top_cpu_processes'].split(',')[0].strip()
        proc_name = proc_name_full_str.split('(')[0].strip() if '(' in proc_name_full_str else proc_name_full_str

        live_proc_found_and_not_critical = False
        for live_proc_info in active_processes_info:
            live_proc_name_lower = live_proc_info.get('name', '').lower()
            live_proc_cmdline_lower = " ".join(live_proc_info.get('cmdline', [])).lower()
            live_proc_username = live_proc_info.get('username', '')

            # Canlı süreç eşleşmesini kontrol et (proc_name genellikle "yes" olacak)
            is_matching_process = (proc_name.lower() == live_proc_name_lower) or \
                                  (proc_name.lower() in live_proc_cmdline_lower)

            if is_matching_process:
                # Canlı işlem bulundu, şimdi kritik olup olmadığını kontrol et
                # 'yes' komutu genellikle kritik bir sistem süreci değildir.
                if not is_critical_process(process_name=live_proc_name_lower, cmdline=live_proc_info.get('cmdline', []), username=live_proc_username):
                    live_proc_found_and_not_critical = True
                    break # Eşleşen ve kritik olmayan bir süreç bulduk, döngüyü kır
        
        if live_proc_found_and_not_critical:
            filtered_rows.append(row.to_dict()) 
        # else:
        #     # DEBUG için: Neden filtrelendiğini anlamak için buraya print ekleyebilirsiniz.
        #     # print(f"DEBUG: Anomali kartı filtrelendi (Canlı değil veya kritik): {row['top_cpu_processes']}") 

    return render_template('anomaly_page.html', filtered_rows=filtered_rows)


@anomaly_routes.route("/ignore_anomaly", methods=["POST"])
@login_required
def ignore_anomaly():
    # ... (Aynı kalacak)
    timestamp = request.form.get("timestamp")
    cpu = float(request.form.get("cpu"))
    ram = float(request.form.get("ram"))
    disk = float(request.form.get("disk"))

    if not os.path.exists("metrics_history.csv"):
        return jsonify({"message": "❌ Veri dosyası bulunamadı."}), 404
    
    try:
        df = pd.read_csv("metrics_history.csv")
        
        if 'anomaly_type' not in df.columns:
            df['anomaly_type'] = ''

        df_filtered = df[
            (df['timestamp'] == timestamp) &
            (abs(df['cpu_percent'] - cpu) < 0.1) & 
            (abs(df['ram_percent'] - ram) < 0.1) &
            (abs(df['disk_percent'] - disk) < 0.1) &
            (df['anomaly'] == -1) 
        ]

        if not df_filtered.empty:
            df_updated = df.drop(df_filtered.index)
            df_updated.to_csv("metrics_history.csv", index=False)
            return jsonify({"message": "✅ Anomali uyarısı başarıyla silindi."})
        else:
            return jsonify({"message": "❌ Eşleşen anomali kaydı bulunamadı."}), 404

    except Exception as e:
        return jsonify({"message": f"❌ Anomali silinirken bir hata oluştu: {str(e)}"}), 500