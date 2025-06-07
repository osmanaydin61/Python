import os
from flask import Blueprint, render_template, request, redirect, url_for, session 
from functools import wraps
from werkzeug.security import check_password_hash # Bu import çok önemli!

auth_routes = Blueprint("auth", __name__)

# Kullanıcı verisini ortam değişkenlerinden al
admin_email_env = os.getenv("ADMIN_USER_EMAIL")
readonly_email_env = os.getenv("READONLY_USER_EMAIL")

users = {} # Boş bir sözlükle başlıyoruz

# .env dosyasından okunan ADMIN kullanıcısı için bilgiler
if admin_email_env: # Sadece .env'de ADMIN_USER_EMAIL tanımlıysa bu bloğa girer
    users[admin_email_env] = {
        'password': os.getenv("ADMIN_USER_PASSWORD"), # .env'deki HASH'li şifreyi alır
        'role': os.getenv("ADMIN_USER_ROLE")
    }

# .env dosyasından okunan READONLY kullanıcısı için bilgiler
if readonly_email_env: # Sadece .env'de READONLY_USER_EMAIL tanımlıysa bu bloğa girer
    users[readonly_email_env] = {
        'password': os.getenv("READONLY_USER_PASSWORD"), # .env'deki HASH'li şifreyi alır
        'role': os.getenv("READONLY_USER_ROLE")
    }

# Giriş kontrolü decorator'ı
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# Rol kontrolü decorator'ı
def roles_required(role_param): # Fonksiyona gelen beklenen rol (örn: 'admin')
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # 1. Session'da 'user' var mı diye bak (login_required zaten bunu yapar ama ekstra kontrol)
            if 'user' not in session:
                return redirect(url_for('auth.login')) # Kullanıcı giriş yapmamışsa login'e yönlendir

            # 2. Session'dan kullanıcının kaydedilmiş rolünü al
            user_role_in_session = session.get('role')

            # 3. Session'da rol var mı ve beklenen rolle uyuşuyor mu diye kontrol et
            if user_role_in_session and user_role_in_session == role_param:
                return f(*args, **kwargs) # Yetkisi var, sayfayı göster
            else:
                # Yetkisi yoksa veya session'da rol bilgisi bir şekilde eksikse
                # (Kullanıcı bilgilerini users sözlüğünden tekrar okumak yerine doğrudan session'a güveniriz)
                return "<h3>Erişim Engellendi: Bu sayfa için yetkiniz yok.</h3><a href='/'>Ana Sayfa</a>"
        return wrapped
    return decorator

# Giriş (Login) route'u
@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email_form = request.form.get("email")          # Kullanıcının forma girdiği e-posta
        password_form = request.form.get("password")    # Kullanıcının forma girdiği şifre

        # 1. Adım: Kullanıcı .env'den yüklenen 'users' sözlüğünde var mı?
        if email_form in users:
            stored_user_data = users[email_form]
            stored_hash = stored_user_data.get('password') # .env'den gelen hash'li şifre

            # 2. Adım: Kayıtlı hash var mı ve girilen şifre bu hash ile uyuşuyor mu?
            if stored_hash and check_password_hash(stored_hash, password_form):
                session['user'] = email_form
                session['role'] = stored_user_data.get('role') # ROLÜ DE SESSION'A EKLİYORUZ!
                return redirect(url_for('dashboard.home'))
            else:
                error = "❌ Geçersiz e-posta veya şifre." # Hash uyuşmadı veya kayıtlı hash yok
        else:
            error = "❌ Geçersiz e-posta veya şifre." # Kullanıcı bulunamadı
            
    return render_template('login.html', error=error)

# Çıkış işlemi
@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
