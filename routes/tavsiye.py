from flask import Blueprint, render_template, request, redirect, url_for, session
import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo

tavsiye_routes = Blueprint("tavsiye", __name__)
TAVSIYE_FILE = "tavsiyeler.csv"
CEVAP_FILE = "cevaplar.csv"

@tavsiye_routes.route("/tavsiye", methods=["GET", "POST"])
def tavsiye():
    # Tavsiye Gönderme (readonly)
    if request.method == "POST" and request.form.get("mode") == "tavsiye":
        user = session.get("user", "Anonim")
        tavsiye_metni = request.form.get("tavsiye")
        timestamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M:%S")
        new_entry = pd.DataFrame([[user, tavsiye_metni, timestamp]], columns=["user", "tavsiye", "timestamp"])

        if os.path.exists(TAVSIYE_FILE):
            df = pd.read_csv(TAVSIYE_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(TAVSIYE_FILE, index=False)
        return redirect(url_for("tavsiye.tavsiye"))

    # Admin Cevaplama
    if request.method == "POST" and request.form.get("mode") == "cevap":
        if session.get("user") != "osmanaydin2016@yandex.com":
            return "Yetkisiz işlem."
        user = request.form.get("user")
        tavsiye_text = request.form.get("tavsiye")
        timestamp = request.form.get("timestamp")
        cevap = request.form.get("cevap")
        cevap_timestamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M:%S")

        # Cevabı kaydet
        new_entry = pd.DataFrame([[user, tavsiye_text, cevap, timestamp, cevap_timestamp]],
                                 columns=["user", "tavsiye", "cevap", "tavsiye_tarih", "cevap_tarih"])
        if os.path.exists(CEVAP_FILE):
            df = pd.read_csv(CEVAP_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(CEVAP_FILE, index=False)

        # Tavsiyeyi sil
        df_tavsiye = pd.read_csv(TAVSIYE_FILE)
        df_tavsiye = df_tavsiye[~((df_tavsiye['user'] == user) & (df_tavsiye['tavsiye'] == tavsiye_text) & (df_tavsiye['timestamp'] == timestamp))]
        df_tavsiye.to_csv(TAVSIYE_FILE, index=False)
        return redirect(url_for("tavsiye.tavsiye"))

    # Verileri hazırla
    tavsiyeler = []
    cevaplar = []
    if os.path.exists(TAVSIYE_FILE):
        tavsiyeler = pd.read_csv(TAVSIYE_FILE).to_dict(orient="records")

    if os.path.exists(CEVAP_FILE):
        df = pd.read_csv(CEVAP_FILE)
    if session.get("user") == "osmanaydin2016@yandex.com":
        cevaplar = df.to_dict(orient="records")  # Admin tüm cevapları görür
    else:
        user = session.get("user")
        cevaplar = df[df['user'] == user].to_dict(orient="records")  # Sadece kendi cevaplarını görür


    is_admin = session.get("user") == "osmanaydin2016@yandex.com"

    return render_template('tavsiye_page.html', tavsiyeler=tavsiyeler, cevaplar=cevaplar, is_admin=is_admin)
