"""Atlas Kütüphane — Flask uygulaması."""

from __future__ import annotations

import os
from datetime import date
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database as db
from database import KUTUPHANE

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "atlas-kutuphane-odev-2026")


def _safe_next_url(candidate: str | None, fallback: str) -> str:
    """Yalnızca aynı sitedeki göreli yollara yönlendir (açık yönlendirme engeli)."""
    if not candidate:
        return fallback
    candidate = candidate.strip()
    parsed = urlparse(candidate)
    if parsed.scheme or parsed.netloc:
        return fallback
    if not candidate.startswith("/") or candidate.startswith("//"):
        return fallback
    return candidate


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "personel_id" not in session:
            return redirect(url_for("giris"))
        return view(*args, **kwargs)

    return wrapped


def uye_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "uye_id" not in session:
            return redirect(url_for("uye_giris"))
        return view(*args, **kwargs)

    return wrapped


def _kitap_form_data() -> dict:
    return {
        "isbn": request.form.get("isbn", "").strip(),
        "ad": request.form.get("ad", "").strip(),
        "yazar": request.form.get("yazar", "").strip(),
        "yayinevi": request.form.get("yayinevi", "").strip(),
        "yayin_yili": request.form.get("yayin_yili", "2024"),
        "kategori": request.form.get("kategori", "Roman"),
        "toplam_adet": request.form.get("toplam_adet", "1"),
        "raf_konumu": request.form.get("raf_konumu", "").strip(),
    }


def _uye_form_data() -> dict:
    return {
        "ad": request.form.get("ad", "").strip(),
        "soyad": request.form.get("soyad", "").strip(),
        "eposta": request.form.get("eposta", "").strip(),
        "telefon": request.form.get("telefon", "").strip(),
        "tip": request.form.get("tip", "Öğrenci"),
    }


@app.context_processor
def inject_globals():
    personel = None
    uye = None
    uye_ozet = None
    if "personel_id" in session:
        personel = db.get_personel(session["personel_id"])
    if "uye_id" in session:
        uye = db.get_uye(session["uye_id"])
        if uye:
            uye_ozet = db.uye_ozet_sayilar(session["uye_id"])
    return {
        "personel": personel,
        "uye": uye,
        "uye_ozet": uye_ozet,
        "kutuphane": KUTUPHANE,
        "bugun": date.today(),
    }


@app.route("/")
def index():
    if "personel_id" in session:
        return redirect(url_for("panel"))
    if "uye_id" in session:
        return redirect(url_for("uye_panel"))
    return render_template("index.html")


@app.route("/giris", methods=["GET", "POST"])
def giris():
    if request.method == "POST":
        kullanici = request.form.get("kullanici_adi", "").strip()
        sifre = request.form.get("sifre", "")
        personel = db.authenticate(kullanici, sifre)
        if personel:
            session.clear()
            session["personel_id"] = personel.personel_id
            flash("Giriş başarılı. Hoş geldiniz.", "success")
            return redirect(url_for("panel"))
        flash("Kullanıcı adı veya şifre hatalı.", "error")
    return render_template("giris.html")


@app.route("/cikis")
def cikis():
    session.clear()
    flash("Oturum kapatıldı.", "success")
    return redirect(url_for("index"))


@app.route("/panel")
@login_required
def panel():
    stats = db.panel_istatistikleri()
    return render_template("panel.html", stats=stats, active="panel")


@app.route("/kitaplar", methods=["GET", "POST"])
@login_required
def kitaplar():
    if request.method == "POST":
        eylem = request.form.get("eylem", "ekle")
        try:
            if eylem == "ekle":
                db.add_kitap(_kitap_form_data())
                flash("Kitap kaydedildi.", "success")
            elif eylem == "guncelle":
                db.update_kitap(int(request.form["kitap_id"]), _kitap_form_data())
                flash("Kitap güncellendi.", "success")
            elif eylem == "sil":
                db.delete_kitap(int(request.form["kitap_id"]))
                flash("Kitap silindi.", "success")
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
        return redirect(url_for("kitaplar", q=request.args.get("q", ""), kategori=request.args.get("kategori", "all")))

    q = request.args.get("q", "").strip()
    kategori = request.args.get("kategori", "all")
    duzenle_id = request.args.get("duzenle", type=int)
    kitap_listesi = db.list_kitaplar(q=q, kategori=kategori)
    kategoriler = db.list_kategoriler()
    musait = sum(1 for k in kitap_listesi if k.musait_mi())
    duzenlenecek = db.get_kitap(duzenle_id) if duzenle_id else None
    return render_template(
        "kitaplar.html",
        kitaplar=kitap_listesi,
        kategoriler=kategoriler,
        q=q,
        kategori=kategori,
        musait=musait,
        duzenlenecek=duzenlenecek,
        active="kitaplar",
    )


@app.route("/uyeler", methods=["GET", "POST"])
@login_required
def uyeler():
    if request.method == "POST":
        eylem = request.form.get("eylem", "ekle")
        try:
            if eylem == "ekle":
                data = _uye_form_data()
                data["uye_no"] = request.form.get("uye_no") or db.next_uye_no()
                data["sifre"] = request.form.get("sifre") or "uye123"
                db.add_uye(data)
                flash(
                    "Üye kaydedildi. Portal şifresi atandı (belirtilmediyse varsayılan demo şifre).",
                    "success",
                )
            elif eylem == "guncelle":
                db.update_uye(int(request.form["uye_id"]), _uye_form_data())
                flash("Üye bilgileri güncellendi.", "success")
            elif eylem == "pasif":
                db.set_uye_aktif(int(request.form["uye_id"]), False)
                flash("Üye pasife alındı. Artık ödünç alamaz.", "success")
            elif eylem == "aktif":
                db.set_uye_aktif(int(request.form["uye_id"]), True)
                flash("Üye yeniden aktifleştirildi.", "success")
            elif eylem == "sifre_sifirla":
                yeni = request.form.get("yeni_sifre") or "uye123"
                db.uye_sifre_sifirla(int(request.form["uye_id"]), yeni)
                flash("Üye şifresi sıfırlandı. Yeni şifreyi üye ile güvenli kanaldan paylaşın.", "success")
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
        fallback = url_for("uyeler", q=request.args.get("q", ""), durum=request.args.get("durum", "all"))
        return redirect(_safe_next_url(request.form.get("next"), fallback))

    q = request.args.get("q", "").strip()
    durum = request.args.get("durum", "all")
    duzenle_id = request.args.get("duzenle", type=int)
    uye_listesi = db.list_uyeler(q=q, durum=durum)
    duzenlenecek = db.get_uye(duzenle_id) if duzenle_id else None
    return render_template(
        "uyeler.html",
        uyeler=uye_listesi,
        q=q,
        durum=durum,
        sonraki_no=db.next_uye_no(),
        duzenlenecek=duzenlenecek,
        active="uyeler",
    )


@app.route("/odunc", methods=["GET", "POST"])
@login_required
def odunc():
    if request.method == "POST":
        eylem = request.form.get("eylem")
        filtre = request.form.get("filtre") or request.args.get("filtre", "acik")
        q = request.form.get("q") or request.args.get("q", "")
        try:
            if eylem == "ver":
                uye_no = request.form.get("uye_no", "").strip()
                kitap_kod = request.form.get("kitap_kod", "").strip()
                uye_id = request.form.get("uye_id")
                kitap_id = request.form.get("kitap_id")

                if uye_no:
                    uye = db.find_uye_hizli(uye_no)
                    if not uye:
                        raise ValueError(f"Üye bulunamadı: {uye_no}")
                    uye_id = uye.uye_id
                if kitap_kod:
                    kitap = db.find_kitap_hizli(kitap_kod)
                    if not kitap:
                        raise ValueError(f"Kitap bulunamadı: {kitap_kod}")
                    kitap_id = kitap.kitap_id

                if not uye_id or not kitap_id:
                    raise ValueError("Üye ve kitap seçin veya üye no / ISBN girin.")

                db.odunc_ver(int(uye_id), int(kitap_id), session["personel_id"])
                flash("Ödünç verildi.", "success")
            elif eylem == "iade":
                ceza = db.iade_al(int(request.form["odunc_id"]))
                if ceza:
                    flash(
                        f"İade alındı. {ceza.gun_sayisi} gün gecikme → {ceza.toplam_tutar} TL ceza oluştu.",
                        "error",
                    )
                else:
                    flash("İade alındı. Ceza yok.", "success")
            elif eylem == "uzat":
                o = db.sure_uzat(int(request.form["odunc_id"]))
                flash(
                    f"Süre {KUTUPHANE.uzatma_gun} gün uzatıldı. Yeni iade: {o.planlanan_iade.strftime('%d.%m.%Y')}",
                    "success",
                )
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
        return redirect(url_for("odunc", filtre=filtre, q=q))

    filtre = request.args.get("filtre", "acik")
    q = request.args.get("q", "").strip()
    oduncler = db.list_oduncler(filtre=filtre, q=q)
    return render_template(
        "odunc.html",
        oduncler=oduncler,
        uyeler=db.list_uyeler(durum="aktif"),
        kitaplar=[k for k in db.list_kitaplar() if k.musait_mi()],
        filtre=filtre,
        q=q,
        active="odunc",
    )


@app.route("/cezalar", methods=["GET", "POST"])
@login_required
def cezalar():
    if request.method == "POST":
        try:
            db.ceza_ode(int(request.form["ceza_id"]))
            flash("Ceza ödendi olarak işaretlendi.", "success")
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
        return redirect(url_for("cezalar", filtre=request.args.get("filtre", "all")))

    filtre = request.args.get("filtre", "all")
    ceza_listesi = db.list_cezalar(filtre=filtre)
    toplam = sum(float(c.toplam_tutar) for c in ceza_listesi)
    odenen = sum(float(c.toplam_tutar) for c in ceza_listesi if c.odendi)
    bekleyen = sum(float(c.toplam_tutar) for c in ceza_listesi if not c.odendi)
    return render_template(
        "cezalar.html",
        cezalar=ceza_listesi,
        filtre=filtre,
        toplam=toplam,
        odenen=odenen,
        bekleyen=bekleyen,
        active="cezalar",
    )


@app.route("/raporlar")
@login_required
def raporlar():
    return render_template(
        "raporlar.html",
        rapor=db.rapor_verileri(),
        active="raporlar",
    )


@app.route("/uyeler/<int:uye_id>")
@login_required
def uye_detay(uye_id: int):
    try:
        detay = db.uye_detay(uye_id)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("uyeler"))
    return render_template("uye_detay.html", detay=detay, active="uyeler")


@app.route("/ara")
@login_required
def ara():
    q = request.args.get("q", "").strip()
    return render_template(
        "ara.html",
        q=q,
        sonuc=db.global_ara(q) if q else {"uyeler": [], "kitaplar": [], "oduncler": []},
        active="panel",
    )


# --- Üye portalı ---


@app.route("/uye/giris", methods=["GET", "POST"])
def uye_giris():
    if request.method == "POST":
        try:
            uye = db.authenticate_uye(
                request.form.get("kimlik", ""),
                request.form.get("sifre", ""),
            )
            if uye:
                session.clear()
                session["uye_id"] = uye.uye_id
                flash(f"Hoş geldiniz, {uye.ad}.", "success")
                return redirect(url_for("uye_panel"))
            flash("Üye no / e-posta veya şifre hatalı.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("uye_giris.html")


@app.route("/uye/kayit", methods=["GET", "POST"])
def uye_kayit():
    if request.method == "POST":
        try:
            uye = db.kayit_uye(
                {
                    "ad": request.form.get("ad", "").strip(),
                    "soyad": request.form.get("soyad", "").strip(),
                    "eposta": request.form.get("eposta", "").strip(),
                    "telefon": request.form.get("telefon", "").strip(),
                    "sifre": request.form.get("sifre", ""),
                },
                sifre_tekrar=request.form.get("sifre_tekrar", ""),
            )
            session.clear()
            session["uye_id"] = uye.uye_id
            flash(f"Kayıt tamam. Üye numaranız: {uye.uye_no}", "success")
            return redirect(url_for("uye_panel"))
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
    return render_template("uye_kayit.html")


@app.route("/uye/cikis")
def uye_cikis():
    session.clear()
    flash("Üye oturumu kapatıldı.", "success")
    return redirect(url_for("index"))


@app.route("/uye")
@app.route("/uye/panel")
@uye_login_required
def uye_panel():
    return render_template(
        "uye_panel.html",
        ozet=db.uye_panel_ozet(session["uye_id"]),
        active="panel",
    )


@app.route("/uye/katalog")
@uye_login_required
def uye_katalog():
    q = request.args.get("q", "").strip()
    kategori = request.args.get("kategori", "all")
    sadece_rafta = request.args.get("rafta") == "1"
    kitaplar = db.list_kitaplar(q=q, kategori=kategori)
    if sadece_rafta:
        kitaplar = [k for k in kitaplar if k.musait_mi()]
    return render_template(
        "uye_katalog.html",
        kitaplar=kitaplar,
        kategoriler=db.list_kategoriler(),
        q=q,
        kategori=kategori,
        sadece_rafta=sadece_rafta,
        toplam_eser=db.count_kitaplar(),
        active="katalog",
    )


@app.route("/uye/oduncler")
@uye_login_required
def uye_oduncler():
    filtre = request.args.get("filtre", "acik")
    tum = db.list_oduncler_uye(session["uye_id"], filtre="hepsi")
    if filtre == "acik":
        oduncler = [o for o in tum if o.durum != "iade"]
    elif filtre == "geciken":
        oduncler = [o for o in tum if o.gecikti_mi()]
    elif filtre == "iade":
        oduncler = [o for o in tum if o.durum == "iade"]
    else:
        oduncler = tum
    sayilar = {
        "hepsi": len(tum),
        "acik": len([o for o in tum if o.durum != "iade"]),
        "geciken": len([o for o in tum if o.gecikti_mi()]),
        "iade": len([o for o in tum if o.durum == "iade"]),
    }
    aciklar = [o for o in tum if o.durum != "iade"]
    siradaki = min((o.planlanan_iade for o in aciklar), default=None)
    return render_template(
        "uye_oduncler.html",
        oduncler=oduncler,
        filtre=filtre,
        sayilar=sayilar,
        acik_sayisi=len(aciklar),
        siradaki_iade=siradaki,
        active="oduncler",
    )


@app.route("/uye/cezalar")
@uye_login_required
def uye_cezalar():
    cezalar = db.list_cezalar_uye(session["uye_id"])
    bekleyen_list = [c for c in cezalar if not c.odendi]
    odenen_list = [c for c in cezalar if c.odendi]
    bekleyen = sum(float(c.toplam_tutar) for c in bekleyen_list)
    odenen = sum(float(c.toplam_tutar) for c in odenen_list)
    return render_template(
        "uye_cezalar.html",
        cezalar=cezalar,
        bekleyen_list=bekleyen_list,
        odenen_list=odenen_list,
        bekleyen=bekleyen,
        odenen=odenen,
        active="cezalar",
    )


@app.route("/uye/profil", methods=["GET", "POST"])
@uye_login_required
def uye_profil():
    if request.method == "POST":
        eylem = request.form.get("eylem")
        try:
            if eylem == "profil":
                db.update_uye_profil(
                    session["uye_id"],
                    {
                        "ad": request.form.get("ad", "").strip(),
                        "soyad": request.form.get("soyad", "").strip(),
                        "eposta": request.form.get("eposta", "").strip(),
                        "telefon": request.form.get("telefon", "").strip(),
                    },
                )
                flash("Profil güncellendi.", "success")
            elif eylem == "sifre":
                db.uye_sifre_degistir(
                    session["uye_id"],
                    request.form.get("eski_sifre", ""),
                    request.form.get("yeni_sifre", ""),
                )
                flash("Şifre değiştirildi.", "success")
        except Exception as exc:  # noqa: BLE001
            flash(str(exc), "error")
        return redirect(url_for("uye_profil"))
    return render_template("uye_profil.html", active="profil")


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, port=5000)
