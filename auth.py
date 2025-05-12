# auth.py — Kullanıcı giriş, çıkış ve yetkilendirme işlemleri
from flask import Blueprint, render_template_string, redirect, url_for, request, session
from functools import wraps

auth_routes = Blueprint("auth", __name__)

users = {
    'osmanaydin2016@yandex.com': {'password': '123', 'role': 'admin'},
    'readonly@example.com': {'password': 'readonly123', 'role': 'readonly'}
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user' not in session or users[session['user']]['role'] != role:
                return "<h3>Erişim Engellendi: Bu sayfa için yetkiniz yok.</h3><a href='/'>Ana Sayfa</a>"
            return f(*args, **kwargs)
        return wrapped
    return decorator

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('home'))
        else:
            error = "Geçersiz giriş bilgisi."
    return render_template_string("""
        <h2>🔐 Kullanıcı Girişi</h2>
        <form method="post">
            E-posta: <input type="email" name="email"><br><br>
            Şifre: <input type="password" name="password"><br><br>
            <button type="submit">Giriş Yap</button>
        </form>
        <p style="color:red;">{{ error }}</p>
    """, error=error)

@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
