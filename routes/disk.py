
# routes/disk.py — Disk temizleme işlemleri
from flask import Blueprint, redirect, url_for
from auth import login_required, roles_required
from utils.clean_disk_utils import clean_disk

disk_routes = Blueprint("disk", __name__)
last_freed_space = 0

@disk_routes.route("/disktemizle")
@login_required
@roles_required('admin')
def disktemizle():
    global last_freed_space
    last_freed_space = clean_disk()
    return redirect(url_for("disk.disktemizle_sonuc"))

@disk_routes.route("/disktemizle_sonuc")
@login_required
@roles_required('admin')
def disktemizle_sonuc():
    global last_freed_space
    return f"<h2>🧹 {last_freed_space} MB alan açıldı.</h2><a href='/'>⬅ Geri</a>"
