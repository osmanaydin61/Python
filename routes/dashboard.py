from flask import Blueprint, render_template, session 
from auth import login_required

dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/")
@login_required
def home():
    return render_template('home.html', user=session.get("user"))
