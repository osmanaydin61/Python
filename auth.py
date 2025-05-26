from flask import Blueprint, render_template_string, request, redirect, url_for, session
from functools import wraps

auth_routes = Blueprint("auth", __name__)

# Kullanıcı verisi
users = {
    'osmanaydin2016@yandex.com': {'password': 'admin123', 'role': 'admin'},
    'readonly@gmail.com': {'password': 'read123', 'role': 'readonly'}
}

# Giriş kontrolü
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# Rol kontrolü
def roles_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_info = users.get(session.get('user'), {})
            if user_info.get('role') != role:
                return "<h3>Erişim Engellendi: Bu sayfa için yetkiniz yok.</h3><a href='/'>Ana Sayfa</a>"
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Giriş ekranı
@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('dashboard.home'))
        else:
            error = "❌ Geçersiz e-posta veya şifre."
    return render_template_string("""
        <h2>🔐 Giriş Yap</h2>
        <form method='post'>
            E-posta: <input type='email' name='email'><br><br>
            Şifre: <input type='password' name='password'><br><br>
            <button type='submit'>Giriş Yap</button>
        </form>
        <p style='color:red;'>{{ error }}</p>
    """, error=error)

# Çıkış işlemi
@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
