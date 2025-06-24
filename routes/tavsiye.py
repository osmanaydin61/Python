from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from datetime import datetime
from zoneinfo import ZoneInfo

from models import Suggestion, Response
from cloudwatch.CloudWatch import send_email_alert
from extensions import db
tavsiye_routes = Blueprint("tavsiye", __name__)

@tavsiye_routes.route("/tavsiye", methods=["GET", "POST"])
def tavsiye():
    message = ""
    with current_app.app_context(): 

        # Tavsiye Gönderme (Kullanıcı)
        if request.method == "POST" and request.form.get("mode") == "tavsiye":
            user_email = session.get("user", "Anonim")
            tavsiye_metni = request.form.get("tavsiye")
            category = request.form.get("category")
            
            if not tavsiye_metni:
                message = "Tavsiye metni boş olamaz."
            else:
                new_suggestion = Suggestion(
                    user_email=user_email,
                    tavsiye_text=tavsiye_metni,
                    timestamp=datetime.now(ZoneInfo("Europe/Istanbul")),
                    status='Yeni',
                    category=category,
                    priority='Düşük'
                )
                db.session.add(new_suggestion)
                db.session.commit()
                message = "Tavsiyeniz başarıyla gönderildi."

        # Admin Cevaplama
        elif request.method == "POST" and request.form.get("mode") == "cevap":
            if session.get("role") != "admin":
                return "Yetkisiz işlem.", 403
            
            suggestion_id = request.form.get("suggestion_id")
            cevap_text = request.form.get("cevap")
            
            original_suggestion = Suggestion.query.get(suggestion_id)

            if not original_suggestion:
                message = "Cevaplanacak tavsiye bulunamadı veya daha önce cevaplandı."
            elif not cevap_text:
                message = "Cevap metni boş olamaz."
            else:
                new_response = Response(
                    user_email=original_suggestion.user_email,
                    tavsiye_text=original_suggestion.tavsiye_text,
                    tavsiye_timestamp=original_suggestion.timestamp,
                    cevap_text=cevap_text,
                    cevap_timestamp=datetime.now(ZoneInfo("Europe/Istanbul"))
                )
                db.session.add(new_response)
                
                # Cevaplanan tavsiyeyi silmek yerine durumunu 'Cevaplandı' olarak güncelle
                original_suggestion.status = 'Cevaplandı' 
                db.session.commit()
                message = f"Tavsiye '{original_suggestion.user_email}' tarafından başarıyla cevaplandı."

                # Kullanıcıya cevaplanan maili gönder
                try:
                    recipient_email = original_suggestion.user_email
                    alert_enabled = current_app.config.get('ALARM_ENABLED', False)
                    if alert_enabled and recipient_email != "Anonim":
                        mail_subject = f"Tavsiyenize Cevap Geldi: {original_suggestion.tavsiye_text[:30]}..."
                        mail_body = f"Sayın {recipient_email},\n\n" \
                                    f"Gönderdiğiniz tavsiyeye bir cevap geldi:\n" \
                                    f"Tavsiye: \"{original_suggestion.tavsiye_text}\"\n" \
                                    f"Cevap: \"{cevap_text}\"\n\n" \
                                    f"OptiGuard Yönetim Paneli"
                        send_email_alert(recipient_email, mail_subject, mail_body)
                        message += " (E-posta ile bilgilendirildi)"
                except Exception as e:
                    message += f" (E-posta gönderilemedi: {str(e)})"
            
        # Admin Durum/Öncelik Güncelleme 
        elif request.method == "POST" and request.form.get("mode") == "update_status_priority":
            if session.get("role") != "admin":
                return "Yetkisiz işlem.", 403
            
            suggestion_id = request.form.get("suggestion_id")
            new_status = request.form.get("new_status")
            new_priority = request.form.get("new_priority")

            suggestion_to_update = Suggestion.query.get(suggestion_id)
            if suggestion_to_update:
                suggestion_to_update.status = new_status
                suggestion_to_update.priority = new_priority
                db.session.commit()
                message = f"Tavsiye ID:{suggestion_id} durumu '{new_status}', önceliği '{new_priority}' olarak güncellendi."
            else:
                message = "Güncellenecek tavsiye bulunamadı."
        
        # Admin Cevap Silme
        elif request.method == "POST" and request.form.get("mode") == "delete_response":
            if session.get("role") != "admin":
                return "Yetkisiz işlem.", 403
            
            response_id = request.form.get("response_id")
            response_to_delete = Response.query.get(response_id)

            if response_to_delete:
                db.session.delete(response_to_delete)
                db.session.commit()
                message = f"Cevap ID:{response_id} başarıyla silindi."
            else:
                message = "Silinecek cevap bulunamadı."


        # Verileri veritabanından çek 
        # Adminler tüm tavsiyeleri ve cevapları görür
        if session.get("role") == "admin":
            # Sadece 'Cevaplandı' durumunda olmayan tavsiyeleri göster
            tavsiyeler_query = Suggestion.query.filter(Suggestion.status != 'Cevaplandı').order_by(Suggestion.timestamp.desc()).all()
            cevaplar_query = Response.query.order_by(Response.cevap_timestamp.desc()).all()
        else: # Normal kullanıcılar sadece kendi tavsiyelerini ve kendilerine verilen cevapları görür
            user_email = session.get("user")
            tavsiyeler_query = Suggestion.query.filter_by(user_email=user_email).filter(Suggestion.status != 'Cevaplandı').order_by(Suggestion.timestamp.desc()).all()
            cevaplar_query = Response.query.filter_by(user_email=user_email).order_by(Response.cevap_timestamp.desc()).all()


        tavsiyeler = []
        for t in tavsiyeler_query:
            tavsiyeler.append({
                'id': t.id,
                'user': t.user_email,
                'tavsiye': t.tavsiye_text,
                'timestamp': t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'status': t.status,
                'category': t.category,
                'priority': t.priority
            })

        cevaplar = []
        for c in cevaplar_query:
            cevaplar.append({
                'id': c.id, 
                'user': c.user_email,
                'tavsiye': c.tavsiye_text,
                'tavsiye_tarih': c.tavsiye_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'cevap': c.cevap_text,
                'cevap_tarih': c.cevap_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        is_admin = session.get("role") == "admin"
        if not is_admin:
            user_email = session.get("user")
            cevaplar = [c for c in cevaplar if c['user'] == user_email]

    return render_template('tavsiye_page.html', tavsiyeler=tavsiyeler, cevaplar=cevaplar, is_admin=is_admin, message=message)