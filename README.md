# OptiGuard: Gerçek Zamanlı Sunucu İzleme ve Proaktif Optimizasyon Sistemi


OptiGuard, Python ve Flask kullanılarak geliştirilmiş, web tabanlı bir sunucu izleme ve proaktif optimizasyon sistemidir. Sistem yöneticilerinin sunucu kaynaklarını (CPU, RAM, Disk, Ağ) anlık olarak takip etmesini, anormal aktiviteleri tespit etmesini ve olası sorunlara anında müdahale etmesini sağlamak amacıyla tasarlanmıştır. Bu proje, bir bitirme projesi olarak geliştirilmiştir.

## ✨ Temel Özellikler

- **Gerçek Zamanlı Sistem İzleme:** CPU, RAM ve Disk kullanımını anlık ve dinamik grafiklerle izleme.
- **Eşik Tabanlı Anomali Tespiti:** Yönetici tarafından belirlenen kaynak kullanım eşikleri aşıldığında otomatik olarak anomali tespiti ve görsel raporlama.
- **Veritabanı Tabanlı Kayıt:** Tüm metrik ve anomali verilerinin, yeniden başlatmalarda kaybolmayan, kalıcı bir SQLite veritabanında saklanması.
- **Geçmişe Yönelik Analiz:** Kaydedilen tüm metriklerin ve anomali sıklığının geçmişe dönük olarak grafikler üzerinde incelenmesi.
- **Proaktif Müdahale Araçları:** Anomaliye neden olan işlemlerin tek tıkla sonlandırılması, RAM ve Disk temizleme araçları.
- **Kullanıcı ve Rol Yönetimi:** `admin` ve `readonly` rollerine sahip kullanıcıları yönetme imkanı.
- **Yapılandırılabilir Ayarlar:** Alarm eşikleri, bildirim e-postası, otomatik müdahale modu gibi birçok sistem ayarının arayüz üzerinden dinamik olarak değiştirilebilmesi.
- **Geri Bildirim Sistemi:** Kullanıcıların sisteme geri bildirimde bulunmasına ve adminlerin bu geri bildirimleri yanıtlamasına olanak tanıyan entegre iletişim modülü.

## 🚀 Kullanılan Teknolojiler

- **Backend:**
  - Python 3
  - Flask (Web Çatısı)
  - Flask-SQLAlchemy (Veritabanı ORM)
  - Flask-Bcrypt (Şifreleme)
  - Flask-Mail (E-posta Gönderimi)
  - Psutil (Sistem Metrikleri)
  - Matplotlib (Anomali Grafikleri)
- **Frontend:**
  - HTML5
  - CSS3
  - JavaScript
  - Chart.js (Dinamik Grafikler)
- **Veritabanı:**
  - SQLite

## 🔧 Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1.  **Depoyu Klonlayın:**
    ```bash
    git clone <bu-projenin-github-linki>
    cd <proje-klasoru>
    ```

2.  **Sanal Ortam Oluşturun ve Aktif Edin:**
    ```bash
    # Python sanal ortamı oluşturun
    python3 -m venv venv

    # Sanal ortamı aktif edin
    # Windows için:
    # venv\Scripts\activate
    # macOS/Linux için:
    source venv/bin/activate
    ```

3.  **Gerekli Paketleri Yükleyin:**
    Proje için gerekli tüm kütüphaneleri `requirements.txt` dosyasından yükleyin.
    ```bash
    pip install -r requirements.txt
    ```
    *(Eğer `requirements.txt` dosyanız yoksa, `pip freeze > requirements.txt` komutu ile oluşturabilirsiniz.)*

4.  **Ortam Değişkenlerini Ayarlayın (`.env` dosyası):**
    Proje ana dizininde `.env` adında bir dosya oluşturun. Bu dosya, gizli anahtar ve ilk kullanıcı bilgileri gibi hassas verileri içerecektir. Aşağıdaki şablonu kullanabilirsiniz.
    ```ini
    # .env
    FLASK_SECRET_KEY='cok_gizli_ve_uzun_bir_anahtar_girmelisiniz'

    # İlk kullanıcı bilgileri
    ADMIN_USER_EMAIL='admin@example.com'
    ADMIN_USER_PASSWORD='guclu_bir_sifre_'
    READONLY_USER_EMAIL='readonly@example.com'
    READONLY_USER_PASSWORD='baska_bir_sifre'

    # E-posta gönderimi için (Gmail App Password kullanılması önerilir)
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME='gmail_adresiniz@gmail.com'
    MAIL_PASSWORD='gmail_uygulama_sifreniz'
    ```

5.  **Uygulamayı Çalıştırın:**
    Aşağıdaki komut ile Flask sunucusunu başlatın.
    ```bash
    python3 panel.py
    ```
    Uygulama artık `http://13.48.193.0:8080` (IP kullandığınız işletim sistemine göre değişir) çalışıyor olacaktır. İlk çalıştırmada, `instance/site.db` adında bir veritabanı dosyası ve varsayılan kullanıcılar otomatik olarak oluşturulacaktır.

## ⚙️ Yapılandırma

Sistemin çoğu ayarı (alarm eşikleri, otomatik müdahale modu vb.), admin olarak giriş yaptıktan sonra "Ayarlar" sayfası üzerinden kolayca yapılandırılabilir.

