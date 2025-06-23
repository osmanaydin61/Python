# auth.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from functools import wraps
from models import db, User # db ve User modelini import edin

auth_routes = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def roles_required(role_param):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('auth.login'))

            user_role_in_session = session.get('role')

            if user_role_in_session and user_role_in_session == role_param:
                return f(*args, **kwargs)
            else:
                return "<h3>Erişim Engellendi: Bu sayfa için yetkiniz yok.</h3><a href='/'>Ana Sayfa</a>"
        return wrapped
    return decorator

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    with current_app.app_context(): # DB işlemleri için bağlam
        # Veritabanında hiç kullanıcı yoksa varsayılan kullanıcıları oluştur
        if User.query.count() == 0:
            # Admin kullanıcısını oluştur
            admin_email = os.getenv("ADMIN_USER_EMAIL")
            admin_password = os.getenv("ADMIN_USER_PASSWORD")
            admin_role = os.getenv("ADMIN_USER_ROLE") or 'admin'

            if admin_email and admin_password:
                existing_admin = User.query.filter_by(email=admin_email).first()
                if not existing_admin:
                    new_admin = User(email=admin_email, role=admin_role)
                    new_admin.set_password(admin_password)
                    db.session.add(new_admin)
                    print(f"DEBUG: Varsayılan admin kullanıcısı '{admin_email}' oluşturuldu.")
            else:
                print("DEBUG: ADMIN_USER_EMAIL veya ADMIN_USER_PASSWORD .env'de tanımlı değil, varsayılan admin oluşturulamadı.")

            # READONLY kullanıcısını oluştur - YENİ EKLENDİ
            readonly_email = os.getenv("READONLY_USER_EMAIL")
            readonly_password = os.getenv("READONLY_USER_PASSWORD")
            readonly_role = os.getenv("READONLY_USER_ROLE") or 'readonly'

            if readonly_email and readonly_password:
                existing_readonly = User.query.filter_by(email=readonly_email).first()
                if not existing_readonly:
                    new_readonly = User(email=readonly_email, role=readonly_role)
                    new_readonly.set_password(readonly_password)
                    db.session.add(new_readonly)
                    print(f"DEBUG: Varsayılan readonly kullanıcısı '{readonly_email}' oluşturuldu.")
            else:
                print("DEBUG: READONLY_USER_EMAIL veya READONLY_USER_PASSWORD .env'de tanımlı değil, varsayılan readonly oluşturulamadı.")

            db.session.commit() # Tüm yeni kullanıcıları tek bir commit ile kaydet
        else:
            print(f"DEBUG: Veritabanında {User.query.count()} kullanıcı mevcut. Otomatik kullanıcı oluşturma atlandı.")

# Giriş kontrol
    if request.method == "POST":
        email_form = request.form.get("email")
        password_form = request.form.get("password")

        with current_app.app_context(): 
            user = User.query.filter_by(email=email_form).first()

            if user and user.check_password(password_form):
                session['user'] = user.email
                session['role'] = user.role
                return redirect(url_for('dashboard.home'))
            else:
                error = "❌ Geçersiz e-posta veya şifre."
            
    return render_template('login.html', error=error)

@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))