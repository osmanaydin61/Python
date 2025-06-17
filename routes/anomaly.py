# routes/anomaly.py (Nihai ve Tam Hali)

from flask import Blueprint, render_template, jsonify, flash
import psutil

from extensions import db
from models import Metric
from auth import login_required, roles_required
from utils.anomaly_detector import is_critical_process

anomaly_routes = Blueprint('anomaly', __name__)

@anomaly_routes.route('/anomali')
@login_required
def anomaly_page():
    """Veritabanından 'is_anomaly' ve 'is_ignored' false olan son 5 kaydı çeker."""
    try:
        anomalies_from_db = db.session.query(Metric).filter(
            Metric.is_anomaly == True,
            Metric.is_ignored == False
        ).order_by(Metric.timestamp.desc()).limit(5).all() # <-- DEĞİŞİKLİK: Sadece son 5 kaydı al

        active_anomalies = []
        for anomaly in anomalies_from_db:
            # PID'si olan ve hala çalışan ve kritik olmayan işlemleri filtrele
            if anomaly.pid and psutil.pid_exists(anomaly.pid):
                if not is_critical_process(process_name=anomaly.process_name):
                    active_anomalies.append(anomaly)
            # PID'si olmayan disk anomalileri gibi durumları da göster
            elif not anomaly.pid:
                 active_anomalies.append(anomaly)
        
        return render_template('anomaly_page.html', anomalies=active_anomalies)

    except Exception as e:
        print(f"Error fetching anomalies from DB: {e}")
        flash('Anomaliler yüklenirken bir hata oluştu.', 'danger')
        return render_template('anomaly_page.html', anomalies=[])

@anomaly_routes.route('/ignore_anomaly/<int:anomaly_id>', methods=['POST'])
@login_required
@roles_required("admin")
def ignore_anomaly(anomaly_id):
    """Veritabanındaki ilgili anomali kaydının 'is_ignored' sütununu True yapar."""
    try:
        anomaly_to_ignore = db.session.query(Metric).get(anomaly_id)
        if anomaly_to_ignore:
            anomaly_to_ignore.is_ignored = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Anomali yoksayıldı.'})
        else:
            return jsonify({'success': False, 'message': 'Anomali bulunamadı.'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error ignoring anomaly: {e}")
        return jsonify({'success': False, 'message': 'İşlem sırasında bir hata oluştu.'}), 500