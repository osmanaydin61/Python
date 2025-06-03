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
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>Giriş Yap</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #4c6ef5, #b197fc);
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .login-container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                    width: 350px;
                    text-align: center;
                }
                .login-container h2 {
                    margin-bottom: 20px;
                    font-size: 28px;
                    color: #4c6ef5;
                }
                .login-container input[type="email"],
                .login-container input[type="password"] {
                    width: 100%;
                    padding: 12px;
                    margin: 8px 0 20px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    font-size: 16px;
                }
                .login-container button {
                    width: 100%;
                    padding: 12px;
                    background-color: #4c6ef5;
                    border: none;
                    color: white;
                    font-size: 18px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                .login-container button:hover {
                    background-color: #3b5bdb;
                }
                .login-container .lock-icon {
                    font-size: 40px;
                    color: #4c6ef5;
                    margin-bottom: 10px;
                }
                .error-message {
                    color: red;
                    margin-top: 10px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>OptiGuard Yönetim Paneli</h2>
                <form method="POST">
                    <input type="email" name="email" placeholder="E-posta" required>
                    <input type="password" name="password" placeholder="Şifre" required>
                    <button type="submit">Giriş Yap</button>
                </form>
                {% if error %}
                    <p class="error-message">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
    """, error=error)

# Çıkış işlemi
@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
