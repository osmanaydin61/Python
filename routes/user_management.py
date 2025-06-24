import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from auth import login_required, roles_required
from models import User 
from extensions import db
user_management_routes = Blueprint("user_management", __name__)

@user_management_routes.route("/users", methods=["GET", "POST"])
@login_required
@roles_required('admin')
def manage_users():
    add_message = ""
    with current_app.app_context():
        if request.method == "POST":
            action = request.form.get("action")

            if action == "add_user":
                email = request.form.get("email")
                password = request.form.get("password")
                role = request.form.get("role")

                if not email or not password or not role:
                    add_message = "Tüm alanları doldurmak zorunludur."
                else:
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user:
                        add_message = f"'{email}' e-posta adresine sahip bir kullanıcı zaten mevcut."
                    else:
                        new_user = User(email=email, role=role)
                        new_user.set_password(password)
                        db.session.add(new_user)
                        db.session.commit()
                        add_message = f"'{email}' kullanıcısı başarıyla eklendi."
            
            elif action == "delete_user":
                user_id = request.form.get("user_id")
                user_to_delete = User.query.get(user_id)
                
                if user_to_delete:
                    # Adminin kendi hesabını silmesini engelle
                    if user_to_delete.email == session.get('user'):
                        add_message = "Kendi hesabınızı silemezsiniz!"
                    # Son admin hesabını silmeyi engelle
                    elif user_to_delete.role == 'admin' and User.query.filter_by(role='admin').count() == 1:
                        add_message = "Sistemde en az bir admin hesabı bulunmak zorundadır. Son admini silemezsiniz!"
                    else:
                        db.session.delete(user_to_delete)
                        db.session.commit()
                        add_message = f"Kullanıcı '{user_to_delete.email}' başarıyla silindi."
                else:
                    add_message = "Silinecek kullanıcı bulunamadı."
            

        # Mevcut kullanıcıları veritabanından çek ve tabloya gönder
        users = User.query.all()
        users_for_template = [{'id': u.id, 'email': u.email, 'role': u.role} for u in users]
        
    return render_template('user_management_page.html', users=users_for_template, add_message=add_message)