from extensions import db
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import bcrypt

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    cpu_percent = db.Column(db.Float, nullable=False)
    ram_percent = db.Column(db.Float, nullable=False)
    disk_percent = db.Column(db.Float, nullable=False)
    top_cpu_processes = db.Column(db.Text, nullable=True)
    top_ram_processes = db.Column(db.Text, nullable=True)
    anomaly = db.Column(db.Integer, default=0, nullable=False)
    anomaly_image = db.Column(db.String(255), nullable=True)
    anomaly_type = db.Column(db.String(50), nullable=True)
    is_anomaly = db.Column(db.Boolean, default=False)
    is_ignored = db.Column(db.Boolean, default=False)
    pid = db.Column(db.Integer, nullable=True)
    process_name = db.Column(db.String(255), nullable=True)
    active_processes = db.Column(db.Integer, nullable=True)
    total_processes = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Metric {self.timestamp}>"

class NetworkMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    interface_name = db.Column(db.String(50), nullable=False)
    bytes_sent = db.Column(db.BigInteger, nullable=False)
    bytes_recv = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return f"<NetworkMetric {self.timestamp}>"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='readonly')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    value_type = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}: {self.value}>"

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    tavsiye_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    status = db.Column(db.String(50), default='Yeni', nullable=False)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), default='Düşük', nullable=False)

    def __repr__(self):
        return f"<Suggestion {self.user_email} - {self.status}>"

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    tavsiye_text = db.Column(db.Text, nullable=False)
    tavsiye_timestamp = db.Column(db.DateTime, nullable=False)
    cevap_text = db.Column(db.Text, nullable=False)
    cevap_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<Response to {self.user_email}>"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_email = db.Column(db.String(120), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    message_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Message from {self.sender_email}>"