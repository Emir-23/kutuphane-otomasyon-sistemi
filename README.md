# Atlas Kütüphane Otomasyon Sistemi

Üniversite ödevi için hazırlanmış web tabanlı kütüphane otomasyonu.
Arayüz **Stitch** ile tasarlandı; uygulama **Python Flask + SQLite** ile yazıldı.

İki kapı var:

1. **Personel paneli** — kitap, üye, ödünç, iade, ceza, rapor
2. **Üye portalı** — katalog, kendi ödünç/ceza kayıtları, profil

Ödünç verme ve iade bankoda görevli tarafından yapılır; üye yalnızca takip eder.

---

## Kurallar (özet)

| Kural | Değer |
|--------|--------|
| Standart ödünç süresi | 14 gün |
| Günlük gecikme cezası | 15 TL |
| Süre uzatma | +7 gün, bir kez (gecikmişte yok) |
| Limit | Öğrenci 5 · İdari 8 · Akademisyen 15 |

Yeni ödünç engellenir: pasif üye, ödenmemiş ceza, gecikmiş kitap, aynı kitaptan ikinci açık ödünç, limit dolu.

---

## Teknolojiler

| Katman | Seçim | Neden |
|--------|--------|--------|
| Dil | Python 3 | OOP / sınıf diyagramı |
| Web | Flask | Küçük proje, hızlı kurulum |
| Veri | SQLite (`kutuphane.db`) | Tek dosya, kurulum yok |
| Arayüz | Jinja2 + Tailwind CDN + Material Symbols | Stitch çıktısına yakın |
| Şifre | Werkzeug hash | Düz metin tutulmaz |

---

## Mimari

```
templates/     →  ekranlar (personel + üye)
app.py         →  rotalar, oturum, form
models.py      →  domain sınıfları (diyagram temeli)
database.py    →  SQLite şema, sorgular, seed, iş kuralları
kutuphane.db   →  kalıcı veri (ilk çalıştırmada oluşur)
```

- Session: personel → `personel_id`, üye → `uye_id`
- Üye üst barındaki sayılar hafif sorgu (`uye_ozet_sayilar`); özet sayfası listeleri ayrıca çeker
- Ödünç limiti tek kaynak: `Uye.max_odunc_hakki()` → `Kutuphane.max_odunc_icin()`
- Form sonrası `next` yalnızca aynı sitedeki göreli yollara yönlendirilir
- `SECRET_KEY` ortam değişkeninden okunur; yoksa ödev varsayılanı kullanılır

Tablolar: `kategori`, `kitap`, `uye`, `personel`, `odunc`, `ceza`.

---

## Klasör yapısı

```
Kütüphane Otomasyon Sistemi/
├── app.py
├── models.py
├── database.py
├── kutuphane.db          # ilk çalıştırmada oluşur
├── requirements.txt
├── README.md
├── .gitignore
└── templates/
    ├── index.html            # kapı seçimi
    ├── base.html             # personel kabuğu
    ├── giris.html, panel.html, kitaplar.html, uyeler.html
    ├── uye_detay.html, odunc.html, cezalar.html, raporlar.html, ara.html
    ├── uye_base.html         # üye kabuğu (üst menü + meta bar)
    ├── uye_giris.html, uye_kayit.html, uye_panel.html
    ├── uye_katalog.html, uye_oduncler.html, uye_cezalar.html, uye_profil.html
    └── _empty.html
```

---

## Kurulum ve çalıştırma

Python 3 yüklü olmalı.

```powershell
cd "C:\Users\memir\Desktop\Kütüphane Otomasyon Sistemi"
pip install -r requirements.txt
python app.py
```

Adres:

```
http://127.0.0.1:5000
```

İsteğe bağlı (üretim benzeri oturum anahtarı):

```powershell
$env:SECRET_KEY = "kendi-gizli-anahtarin"
python app.py
```

Durdurmak: terminalde `Ctrl + C`.

Veritabanını sıfırlamak için `kutuphane.db` dosyasını silip uygulamayı yeniden çalıştırın.

---

## Demo girişler

**Personel** — `/giris`

| Alan | Değer |
|------|--------|
| Kullanıcı adı | `mehmet` |
| Şifre | `1234` |

**Üye** — `/uye/giris`

| Alan | Değer |
|------|--------|
| Üye no / e-posta | `1001` veya `ayse@mail.com` |
| Şifre | `uye123` |

Diğer örnek üyeler (1002, 1003, …) aynı şifreyi kullanır.
Ana sayfa (`/`) üye / personel seçimi gösterir.

---

## Sayfalar

### Ortak
| Yol | Açıklama |
|-----|----------|
| `/` | Üye / personel seçimi |

### Personel
| Yol | Açıklama |
|-----|----------|
| `/giris` | Personel girişi |
| `/panel` | Özet, yakın iadeler, gecikenler |
| `/kitaplar` | Kitap CRUD, kategori filtresi |
| `/uyeler` | Üye CRUD, pasif/aktif, şifre sıfırlama |
| `/uyeler/<id>` | Üye detay (geçmiş + işlemler) |
| `/odunc` | Ödünç ver, iade al, süre uzat |
| `/cezalar` | Ceza listesi, ödendi işaretle |
| `/raporlar` | Basit istatistikler |
| `/ara` | Global arama (üye / kitap / ödünç) |

### Üye portalı
| Yol | Açıklama |
|-----|----------|
| `/uye/giris` | Giriş (üye no veya e-posta) |
| `/uye/kayit` | Yeni üye kaydı |
| `/uye/panel` | Özet (kota, aktif ödünçler, cezalar) |
| `/uye/katalog` | Katalog arama (ödünç vermez) |
| `/uye/oduncler` | Kişisel ödünçler (filtre + arama) |
| `/uye/cezalar` | Bekleyen / ödenmiş cezalar |
| `/uye/profil` | İletişim bilgisi ve şifre |

---

## Sınıflar (ödev / diyagram)

`models.py`:

- **Kategori** — ad, açıklama
- **Kitap** — ISBN, ad, yazar, adet, raf; `musait_mi()`, `adet_azalt()`, `adet_artir()`
- **Uye** — üye no, iletişim; `tam_ad()`, `aktif_mi()`, `pasife_al()`, `aktiflestir()`, `max_odunc_hakki()`
- **Personel** — kullanıcı adı, rol
- **Odunc** — alış / planlanan iade / gerçek iade; `gecikti_mi()`, `gecikme_gunu()`, `iade_et()`, `sure_uzat()`
- **Ceza** — gün, tutar, ödendi; `tutar_hesapla()`, `ode()`
- **Kutuphane** — süre, ceza, limitler; `planlanan_iade_hesapla()`, `ceza_hesapla()`, `max_odunc_icin()`

Kalıcılık `database.py` üzerinden yapılır. `Kitap.adet_azalt/adet_artir`, `Uye.pasife_al/aktiflestir`, `Ceza.tutar_hesapla/ode` gibi metotlar **sınıf ve object diyagramında domain davranışını göstermek** için durur; çalışan akışta aynı kurallar SQL güncellemeleriyle uygulanır.

**Object diyagramı örneği:** Ayşe Yılmaz (1001) → Suç ve Ceza → Mehmet Demir → bir `Odunc` kaydı.

**Deployment:**

```
[ Tarayıcı ]  --HTTP-->  [ Flask (app.py :5000) ]  --SQL-->  [ kutuphane.db ]
```

Hepsi aynı makinede; ayrı veritabanı sunucusu yok.

---

## Örnek veriler (seed)

İlk açılışta yüklenir:

- Kitaplar: Suç ve Ceza, Saatleri Ayarlama Enstitüsü, Nutuk, Sapiens, Devlet, Tutunamayanlar, Beyaz Kale
- Üyeler: 1001 Ayşe Yılmaz, 1002 Kerem Acar, 1003 Deniz Koç, …
- Personel: Mehmet Demir (`mehmet`)
- Birkaç açık / gecikmiş ödünç ve örnek ceza

---

## Ödev teslimi

- Class diyagramı → `models.py` sınıfları
- Object diyagramı → tek ödünç senaryosu (yukarıdaki örnek)
- Deployment diyagramı → tarayıcı / Flask / SQLite
- Kod → bu klasör

Diyagramlar duyuruya göre A3 veya A4 kâğıda çizilip poşet dosyada verilir.

---

## Bilinen sınırlar

- Flask development server (üretim sunucusu değil)
- Tek demo personel hesabı
- Rezervasyon, e-posta bildirimi, barkod yazıcı yok
- Tailwind CDN için internet gerekir
- CSRF yok (ödev prototipi)
- Flash mesajlarında düz şifre gösterilmez; sıfırlama sonrası şifreyi güvenli kanaldan paylaşın

---

## Kontrol listesi

- [ ] `pip install -r requirements.txt`
- [ ] `python app.py`
- [ ] Personel: `mehmet` / `1234` → kitap → üye → ödünç → iade
- [ ] Gecikmede ceza oluştuğunu kontrol et
- [ ] Üye: `1001` / `uye123` → özet, katalog, ödünçler, cezalar, profil
- [ ] Raporlar ve global arama
- [ ] Diyagramları çiz
