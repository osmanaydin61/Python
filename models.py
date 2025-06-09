# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

# Metrik Geçmişi Tablosu
class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)
    cpu_percent = db.Column(db.Float, nullable=False)
    ram_percent = db.Column(db.Float, nullable=False)
    disk_percent = db.Column(db.Float, nullable=False)
    top_cpu_processes = db.Column(db.String(500), nullable=True)
    top_ram_processes = db.Column(db.String(500), nullable=True)
    anomaly = db.Column(db.Integer, default=0, nullable=False) # -1 (anomali) veya 0 (normal)
    anomaly_image = db.Column(db.String(255), nullable=True) # Anomali grafiği dosya yolu
    anomaly_type = db.Column(db.String(50), nullable=True) # CPU Anomalisi, RAM Anomalisi vb.

    def __repr__(self):
        return f"<Metric {self.timestamp} CPU:{self.cpu_percent}% RAM:{self.ram_percent}%>"

# Yeni Ağ Metrikleri Tablosu - YENİ MODEL
class NetworkMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)
    interface_name = db.Column(db.String(50), nullable=False) # Arayüz adı (eth0, lo vb.)
    bytes_sent = db.Column(db.BigInteger, nullable=False)
    bytes_recv = db.Column(db.BigInteger, nullable=False)
    
    def __repr__(self):
        return f"<NetworkMetric {self.timestamp} {self.interface_name} Sent:{self.bytes_sent} Recv:{self.bytes_recv}>"

# Kullanıcılar Tablosu (Opsiyonel - Eğer auth.py'deki sözlüğü VT'ye taşırsak)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='readonly') # 'admin' veya 'readonly'

    def __repr__(self):
        return f"<User {self.email}>"

    # Şifre yönetimi için yardımcı fonksiyonlar
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_email = db.Column(db.String(120), nullable=False) # Gönderen (admin)
    recipient_email = db.Column(db.String(120), nullable=False) # Alıcı (bir kullanıcı veya 'all_admins', 'all_users')
    subject = db.Column(db.String(255), nullable=True) # Mesaj konusu
    message_text = db.Column(db.Text, nullable=False) # Mesaj içeriği
    timestamp = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False) # Mesaj okundu mu?

    def __repr__(self):
        return f"<Message from {self.sender_email} to {self.recipient_email} - {self.subject}>"


class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    tavsiye_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)
    status = db.Column(db.String(50), default='Yeni', nullable=False) # 'Yeni', 'İnceleniyor', 'Cevaplandı', 'Çözüldü', 'Reddedildi'
    category = db.Column(db.String(50), nullable=True) # 'Hata Raporu', 'Özellik İsteği', 'Genel Geri Bildirim'
    priority = db.Column(db.String(50), default='Düşük', nullable=False) # 'Düşük', 'Orta', 'Yüksek'
    
    def __repr__(self):
        return f"<Suggestion {self.user_email} - {self.status}>"

# Cevaplar Tablosu
class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    tavsiye_text = db.Column(db.Text, nullable=False) # Orijinal tavsiye metni
    tavsiye_timestamp = db.Column(db.DateTime, nullable=False) # Orijinal tavsiyenin kaydedildiği zaman
    cevap_text = db.Column(db.Text, nullable=False)
    cevap_timestamp = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<Response to {self.user_email} at {self.cevap_timestamp}>"
# Ayarlar Tablosu (Opsiyonel - Eğer ayarları VT'ye taşımak istersek)
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False) # Ayar adı (örn: 'CPU_THRESHOLD')
    value = db.Column(db.String(255), nullable=False) # Ayar değeri (string olarak saklanır)
    value_type = db.Column(db.String(50), nullable=True) # 'int', 'float', 'bool', 'string'

    def __repr__(self):
        return f"<Setting {self.key}: {self.value}>"
    
    