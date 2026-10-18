# Atlas Kütüphane Otomasyon Sistemi 📚

Bu proje, üniversite ödevi kapsamında geliştirilmiş web tabanlı bir kütüphane otomasyon sistemidir. Backend tarafında **Python (Flask)** ve **SQLite** kullanılarak geliştirilmiş, ön yüz tasarımı ise **Stitch** baz alınarak **Tailwind CSS** ve **Jinja2** şablon motoruyla hazırlanmıştır. 

Sistem temel olarak iki farklı kullanıcı profiline hizmet verir:
1. **Personel Paneli:** Kütüphane görevlilerinin kitap, üye, ödünç/iade işlemleri ile ceza ve rapor takibini yaptığı yönetim kısmı.
2. **Üye Portalı:** Üyelerin kütüphane kataloğunu inceleyebildiği, kendi ödünç geçmişlerini, cezalarını ve profil bilgilerini takip edebildiği kişisel alan.

*(Not: Tüm fiziksel ödünç verme ve iade alma işlemleri bankodaki personel tarafından yapılır; üyeler sistem üzerinden sadece durumlarını takip edebilirler.)*

---

## 📌 Temel Kurallar ve İş Mantığı (Özet)

Uygulama içerisinde aşağıdaki iş kuralları (business rules) kodlanmıştır:

| Kural | Değer / Açıklama |
| :--- | :--- |
| **Standart Ödünç Süresi** | 14 gün |
| **Gecikme Cezası** | Günlük 15 TL |
| **Süre Uzatma** | Sadece 1 kez, +7 gün uzatılabilir. (Gecikmiş kitaplarda uzatma yapılamaz.) |
| **Ödünç Alma Limitleri** | Öğrenci: 5 Kitap <br> İdari Personel: 8 Kitap <br> Akademisyen: 15 Kitap |

**Ödünç İşlemini Engelleyen Durumlar:**
Bir üyeye yeni kitap verilebilmesi için; üyenin hesabının "aktif" olması, ödenmemiş cezasının bulunmaması, elinde gecikmiş bir kitap olmaması, aynı kitaptan ikinci bir kopyayı almamış olması ve kendi üyelik tipine ait ödünç limitini doldurmamış olması gerekir.

---

## 🛠️ Kullanılan Teknolojiler ve Tercih Nedenleri

| Katman | Teknoloji | Neden Tercih Ettim? |
| :--- | :--- | :--- |
| **Dil** | Python 3 | Nesne Yönelimli Programlama (OOP) yapısına uygunluğu ve UML diyagramları ile birebir eşleşebilmesi. |
| **Web Çerçevesi** | Flask | Proje ölçeğine uygun, gereksiz bağımlılıklardan uzak ve hızlı ayağa kaldırılabilir olması. |
| **Veritabanı** | SQLite (`kutuphane.db`) | Ekstra bir sunucu kurulumu gerektirmemesi ve veritabanının tek bir dosyada tutulabilmesi. |
| **Arayüz (Frontend)** | Jinja2 + Tailwind CSS (CDN) + Material Symbols | Flask ile dinamik sayfa oluşturma kolaylığı ve hızlı, modern bir görünüm elde etmek. |
| **Güvenlik** | Werkzeug (Hash) | Kullanıcı ve üye şifrelerinin veritabanında düz metin (plain text) yerine şifrelenerek tutulması. |

---

## 🏗️ Proje Mimarisi ve Klasör Yapısı

Uygulama temel olarak MVC (Model-View-Controller) mantığına yakın, hafif bir yapıda kurgulandı:

```text
Kütüphane Otomasyon Sistemi/
├── app.py               # (Controller) Yönlendirmeler, oturum yönetimi ve form işlemleri
├── models.py            # (Model) Nesne sınıfları (UML diyagramımızın temel kaynağı)
├── database.py          # Veritabanı bağlantısı, şema oluşturma, seed veriler ve SQL sorguları
├── kutuphane.db         # Kalıcı veritabanı (Uygulama ilk kez çalıştığında otomatik oluşur)
├── requirements.txt     # Gerekli kütüphaneler listesi
├── README.md            # Proje dökümantasyonu
└── templates/           # (View) HTML arayüz dosyaları
    ├── index.html       # Karşılama ve portal seçimi
    ├── base.html        # Personel paneli ana şablonu
    ├── uye_base.html    # Üye portalı ana şablonu
    └── ... Diğer sayfa tasarımları
