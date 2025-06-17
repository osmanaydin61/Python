# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mail = Mail()