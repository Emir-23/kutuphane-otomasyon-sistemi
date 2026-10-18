"""SQLite bağlantısı, şema ve örnek veri."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from models import Ceza, Kitap, Kutuphane, Odunc, Personel, Uye
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "kutuphane.db"
KUTUPHANE = Kutuphane()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kategori (
                kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL UNIQUE,
                aciklama TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS kitap (
                kitap_id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT NOT NULL,
                ad TEXT NOT NULL,
                yazar TEXT NOT NULL,
                yayinevi TEXT NOT NULL,
                yayin_yili INTEGER NOT NULL,
                toplam_adet INTEGER NOT NULL,
                musait_adet INTEGER NOT NULL,
                raf_konumu TEXT NOT NULL,
                kategori_id INTEGER NOT NULL,
                FOREIGN KEY (kategori_id) REFERENCES kategori(kategori_id)
            );

            CREATE TABLE IF NOT EXISTS uye (
                uye_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uye_no TEXT NOT NULL UNIQUE,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                eposta TEXT NOT NULL,
                telefon TEXT NOT NULL,
                kayit_tarihi TEXT NOT NULL,
                aktif INTEGER NOT NULL DEFAULT 1,
                tip TEXT NOT NULL DEFAULT 'Öğrenci',
                sifre TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS personel (
                personel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                kullanici_adi TEXT NOT NULL UNIQUE,
                sifre TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'Görevli'
            );

            CREATE TABLE IF NOT EXISTS odunc (
                odunc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                alis_tarihi TEXT NOT NULL,
                planlanan_iade TEXT NOT NULL,
                gercek_iade TEXT,
                durum TEXT NOT NULL,
                kitap_id INTEGER NOT NULL,
                uye_id INTEGER NOT NULL,
                personel_id INTEGER NOT NULL,
                uzatildi INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (kitap_id) REFERENCES kitap(kitap_id),
                FOREIGN KEY (uye_id) REFERENCES uye(uye_id),
                FOREIGN KEY (personel_id) REFERENCES personel(personel_id)
            );

            CREATE TABLE IF NOT EXISTS ceza (
                ceza_id INTEGER PRIMARY KEY AUTOINCREMENT,
                gun_sayisi INTEGER NOT NULL,
                gunluk_tutar TEXT NOT NULL,
                toplam_tutar TEXT NOT NULL,
                odendi INTEGER NOT NULL DEFAULT 0,
                odunc_id INTEGER NOT NULL UNIQUE,
                FOREIGN KEY (odunc_id) REFERENCES odunc(odunc_id)
            );
            """
        )

        odunc_cols = {
            r["name"]
            for r in conn.execute("PRAGMA table_info(odunc)").fetchall()
        }
        if "uzatildi" not in odunc_cols:
            conn.execute(
                "ALTER TABLE odunc ADD COLUMN uzatildi INTEGER NOT NULL DEFAULT 0"
            )

        uye_cols = {
            r["name"]
            for r in conn.execute("PRAGMA table_info(uye)").fetchall()
        }
        if "sifre" not in uye_cols:
            conn.execute("ALTER TABLE uye ADD COLUMN sifre TEXT NOT NULL DEFAULT ''")

        # Eski üyelere demo şifre ata
        default_hash = generate_password_hash("uye123")
        conn.execute(
            "UPDATE uye SET sifre = ? WHERE sifre IS NULL OR sifre = ''",
            (default_hash,),
        )

        personel_var = conn.execute("SELECT COUNT(*) AS c FROM personel").fetchone()["c"]
        if personel_var == 0:
            _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    kategoriler = [
        ("Roman", "Kurgu edebiyat"),
        ("Tarih", "Tarih ve belgesel"),
        ("Bilim", "Popüler bilim"),
        ("Felsefe", "Felsefe eserleri"),
        ("Sanat", "Sanat ve mimari"),
    ]
    for ad, aciklama in kategoriler:
        conn.execute(
            "INSERT INTO kategori (ad, aciklama) VALUES (?, ?)",
            (ad, aciklama),
        )

    kitaplar = [
        ("978-975-07-2856-2", "Suç ve Ceza", "Fyodor Dostoyevski", "İş Bankası", 2020, 5, 2, "A-12", 1),
        ("978-975-99-5238-7", "Saatleri Ayarlama Enstitüsü", "Ahmet Hamdi Tanpınar", "Dergâh", 2019, 3, 0, "B-04", 1),
        ("978-975-16-0158-2", "Nutuk", "Mustafa Kemal Atatürk", "Atatürk Araştırma", 2018, 4, 4, "C-01", 2),
        ("978-605-7941-12-8", "Sapiens", "Yuval Noah Harari", "Kolektif", 2021, 2, 1, "D-08", 3),
        ("978-975-458-154-8", "Devlet", "Platon", "Türkiye İş Bankası", 2017, 3, 3, "E-03", 4),
        ("978-975-07-0001-1", "Tutunamayanlar", "Oğuz Atay", "İletişim", 2022, 3, 1, "A-20", 1),
        ("978-975-08-1234-5", "Beyaz Kale", "Orhan Pamuk", "YKY", 2016, 2, 1, "A-22", 1),
    ]
    for row in kitaplar:
        conn.execute(
            """
            INSERT INTO kitap
            (isbn, ad, yazar, yayinevi, yayin_yili, toplam_adet, musait_adet, raf_konumu, kategori_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    uye_sifre = generate_password_hash("uye123")
    uyeler = [
        ("1001", "Ayşe", "Yılmaz", "ayse@mail.com", "532 000 00 01", "2026-09-12", 1, "Öğrenci", uye_sifre),
        ("1002", "Kerem", "Acar", "kerem@mail.com", "533 000 00 02", "2026-10-03", 1, "Akademisyen", uye_sifre),
        ("1003", "Deniz", "Koç", "deniz@mail.com", "534 000 00 03", "2026-01-18", 1, "Öğrenci", uye_sifre),
        ("1004", "Zeynep", "Kaya", "zeynep@mail.com", "535 000 00 04", "2026-02-22", 1, "Öğrenci", uye_sifre),
        ("1008", "Burak", "Yılmaz", "burak@mail.com", "536 000 00 08", "2026-03-10", 1, "Öğrenci", uye_sifre),
    ]
    for row in uyeler:
        conn.execute(
            """
            INSERT INTO uye
            (uye_no, ad, soyad, eposta, telefon, kayit_tarihi, aktif, tip, sifre)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    conn.execute(
        """
        INSERT INTO personel (ad, soyad, kullanici_adi, sifre, rol)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "Mehmet",
            "Demir",
            "mehmet",
            generate_password_hash("1234"),
            "Görevli",
        ),
    )

    bugun = date.today()
    oduncler = [
        # Deniz - gecikmiş
        (
            (bugun - timedelta(days=17)).isoformat(),
            (bugun - timedelta(days=3)).isoformat(),
            None,
            "gecikti",
            6,
            3,
            1,
        ),
        # Ayşe - açık
        (
            (bugun - timedelta(days=8)).isoformat(),
            (bugun + timedelta(days=6)).isoformat(),
            None,
            "acik",
            1,
            1,
            1,
        ),
        # Kerem - açık
        (
            (bugun - timedelta(days=6)).isoformat(),
            (bugun + timedelta(days=8)).isoformat(),
            None,
            "acik",
            2,
            2,
            1,
        ),
        # Burak - gecikmiş (ceza için)
        (
            (bugun - timedelta(days=16)).isoformat(),
            (bugun - timedelta(days=2)).isoformat(),
            None,
            "gecikti",
            7,
            5,
            1,
        ),
    ]
    for row in oduncler:
        conn.execute(
            """
            INSERT INTO odunc
            (alis_tarihi, planlanan_iade, gercek_iade, durum, kitap_id, uye_id, personel_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    for gun, gunluk, toplam, odendi, odunc_id in [
        (3, "15.00", "45.00", 0, 1),
        (2, "15.00", "30.00", 0, 4),
    ]:
        conn.execute(
            """
            INSERT INTO ceza (gun_sayisi, gunluk_tutar, toplam_tutar, odendi, odunc_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (gun, gunluk, toplam, odendi, odunc_id),
        )


def authenticate(kullanici_adi: str, sifre: str) -> Optional[Personel]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM personel WHERE kullanici_adi = ?",
            (kullanici_adi,),
        ).fetchone()
    if not row or not check_password_hash(row["sifre"], sifre):
        return None
    return Personel(
        personel_id=row["personel_id"],
        ad=row["ad"],
        soyad=row["soyad"],
        kullanici_adi=row["kullanici_adi"],
        sifre=row["sifre"],
        rol=row["rol"],
    )


def get_personel(personel_id: int) -> Optional[Personel]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM personel WHERE personel_id = ?",
            (personel_id,),
        ).fetchone()
    if not row:
        return None
    return Personel(
        personel_id=row["personel_id"],
        ad=row["ad"],
        soyad=row["soyad"],
        kullanici_adi=row["kullanici_adi"],
        sifre=row["sifre"],
        rol=row["rol"],
    )


def list_kategoriler() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM kategori ORDER BY ad").fetchall()
    return [dict(r) for r in rows]


def _kitap_from_row(r: sqlite3.Row) -> Kitap:
    return Kitap(
        kitap_id=r["kitap_id"],
        isbn=r["isbn"],
        ad=r["ad"],
        yazar=r["yazar"],
        yayinevi=r["yayinevi"],
        yayin_yili=r["yayin_yili"],
        toplam_adet=r["toplam_adet"],
        musait_adet=r["musait_adet"],
        raf_konumu=r["raf_konumu"],
        kategori_id=r["kategori_id"],
        kategori_ad=r["kategori_ad"] if "kategori_ad" in r.keys() else "",
    )


def _uye_from_row(r: sqlite3.Row) -> Uye:
    keys = r.keys()
    return Uye(
        uye_id=r["uye_id"],
        uye_no=r["uye_no"],
        ad=r["ad"],
        soyad=r["soyad"],
        eposta=r["eposta"],
        telefon=r["telefon"],
        kayit_tarihi=date.fromisoformat(r["kayit_tarihi"]),
        aktif=bool(r["aktif"]),
        tip=r["tip"],
        sifre=r["sifre"] if "sifre" in keys else "",
    )


def list_kitaplar(q: str = "", kategori: str = "") -> list[Kitap]:
    sql = """
        SELECT k.*, c.ad AS kategori_ad
        FROM kitap k
        JOIN kategori c ON c.kategori_id = k.kategori_id
        WHERE 1=1
    """
    params: list[Any] = []
    if q:
        sql += " AND (k.ad LIKE ? OR k.yazar LIKE ? OR k.isbn LIKE ? OR CAST(k.kitap_id AS TEXT) = ?)"
        like = f"%{q}%"
        params.extend([like, like, like, q])
    if kategori and kategori != "all":
        sql += " AND c.ad = ?"
        params.append(kategori)
    sql += " ORDER BY k.ad"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_kitap_from_row(r) for r in rows]


def count_kitaplar() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM kitap").fetchone()["c"]


def get_kitap(kitap_id: int) -> Optional[Kitap]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT k.*, c.ad AS kategori_ad
            FROM kitap k
            JOIN kategori c ON c.kategori_id = k.kategori_id
            WHERE k.kitap_id = ?
            """,
            (kitap_id,),
        ).fetchone()
    return _kitap_from_row(row) if row else None


def find_kitap_hizli(sorgu: str) -> Optional[Kitap]:
    sorgu = sorgu.strip()
    if not sorgu:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT k.*, c.ad AS kategori_ad
            FROM kitap k
            JOIN kategori c ON c.kategori_id = k.kategori_id
            WHERE k.isbn = ?
               OR CAST(k.kitap_id AS TEXT) = ?
               OR REPLACE(LOWER(k.isbn), '-', '') = REPLACE(LOWER(?), '-', '')
            LIMIT 1
            """,
            (sorgu, sorgu, sorgu),
        ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT k.*, c.ad AS kategori_ad
                FROM kitap k
                JOIN kategori c ON c.kategori_id = k.kategori_id
                WHERE k.ad LIKE ? AND k.musait_adet > 0
                ORDER BY k.ad LIMIT 1
                """,
                (f"%{sorgu}%",),
            ).fetchone()
    return _kitap_from_row(row) if row else None


def add_kitap(data: dict[str, Any]) -> None:
    with get_connection() as conn:
        kategori = conn.execute(
            "SELECT kategori_id FROM kategori WHERE ad = ?",
            (data["kategori"],),
        ).fetchone()
        if not kategori:
            raise ValueError("Kategori bulunamadı.")
        adet = int(data["toplam_adet"])
        conn.execute(
            """
            INSERT INTO kitap
            (isbn, ad, yazar, yayinevi, yayin_yili, toplam_adet, musait_adet, raf_konumu, kategori_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["isbn"],
                data["ad"],
                data["yazar"],
                data["yayinevi"],
                int(data["yayin_yili"]),
                adet,
                adet,
                data["raf_konumu"],
                kategori["kategori_id"],
            ),
        )


def update_kitap(kitap_id: int, data: dict[str, Any]) -> None:
    with get_connection() as conn:
        mevcut = conn.execute(
            "SELECT * FROM kitap WHERE kitap_id = ?",
            (kitap_id,),
        ).fetchone()
        if not mevcut:
            raise ValueError("Kitap bulunamadı.")
        kategori = conn.execute(
            "SELECT kategori_id FROM kategori WHERE ad = ?",
            (data["kategori"],),
        ).fetchone()
        if not kategori:
            raise ValueError("Kategori bulunamadı.")

        yeni_toplam = int(data["toplam_adet"])
        odunc_adet = mevcut["toplam_adet"] - mevcut["musait_adet"]
        if yeni_toplam < odunc_adet:
            raise ValueError(
                f"Toplam adet, ödünçteki kopya sayısından ({odunc_adet}) az olamaz."
            )
        yeni_musait = yeni_toplam - odunc_adet
        conn.execute(
            """
            UPDATE kitap SET
                isbn = ?, ad = ?, yazar = ?, yayinevi = ?, yayin_yili = ?,
                toplam_adet = ?, musait_adet = ?, raf_konumu = ?, kategori_id = ?
            WHERE kitap_id = ?
            """,
            (
                data["isbn"],
                data["ad"],
                data["yazar"],
                data["yayinevi"],
                int(data["yayin_yili"]),
                yeni_toplam,
                yeni_musait,
                data["raf_konumu"],
                kategori["kategori_id"],
                kitap_id,
            ),
        )


def delete_kitap(kitap_id: int) -> None:
    with get_connection() as conn:
        acik = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE kitap_id = ? AND durum IN ('acik', 'gecikti')
            """,
            (kitap_id,),
        ).fetchone()["c"]
        if acik:
            raise ValueError("Açık ödüncü olan kitap silinemez.")
        gecmis = conn.execute(
            "SELECT COUNT(*) AS c FROM odunc WHERE kitap_id = ?",
            (kitap_id,),
        ).fetchone()["c"]
        if gecmis:
            raise ValueError("Ödünç geçmişi olan kitap silinemez; kaydı saklayın.")
        conn.execute("DELETE FROM kitap WHERE kitap_id = ?", (kitap_id,))


def list_uyeler(q: str = "", durum: str = "all") -> list[Uye]:
    sql = "SELECT * FROM uye WHERE 1=1"
    params: list[Any] = []
    if q:
        sql += " AND (ad LIKE ? OR soyad LIKE ? OR uye_no LIKE ? OR eposta LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])
    if durum == "aktif":
        sql += " AND aktif = 1"
    elif durum == "pasif":
        sql += " AND aktif = 0"
    sql += " ORDER BY uye_no"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_uye_from_row(r) for r in rows]


def get_uye(uye_id: int) -> Optional[Uye]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM uye WHERE uye_id = ?", (uye_id,)).fetchone()
    return _uye_from_row(row) if row else None


def find_uye_hizli(sorgu: str) -> Optional[Uye]:
    sorgu = sorgu.strip()
    if not sorgu:
        return None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM uye WHERE uye_no = ? LIMIT 1",
            (sorgu,),
        ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT * FROM uye
                WHERE ad LIKE ? OR soyad LIKE ? OR (ad || ' ' || soyad) LIKE ?
                ORDER BY aktif DESC, uye_no LIMIT 1
                """,
                (f"%{sorgu}%", f"%{sorgu}%", f"%{sorgu}%"),
            ).fetchone()
    return _uye_from_row(row) if row else None


def update_uye(uye_id: int, data: dict[str, Any]) -> None:
    with get_connection() as conn:
        mevcut = conn.execute(
            "SELECT uye_id FROM uye WHERE uye_id = ?",
            (uye_id,),
        ).fetchone()
        if not mevcut:
            raise ValueError("Üye bulunamadı.")
        conn.execute(
            """
            UPDATE uye SET ad = ?, soyad = ?, eposta = ?, telefon = ?, tip = ?
            WHERE uye_id = ?
            """,
            (
                data["ad"],
                data["soyad"],
                data["eposta"],
                data["telefon"],
                data.get("tip", "Öğrenci"),
                uye_id,
            ),
        )


def set_uye_aktif(uye_id: int, aktif: bool) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM uye WHERE uye_id = ?", (uye_id,)).fetchone()
        if not row:
            raise ValueError("Üye bulunamadı.")
        if not aktif:
            acik = conn.execute(
                """
                SELECT COUNT(*) AS c FROM odunc
                WHERE uye_id = ? AND durum IN ('acik', 'gecikti')
                """,
                (uye_id,),
            ).fetchone()["c"]
            if acik:
                raise ValueError("Açık ödüncü olan üye pasife alınamaz.")
        conn.execute(
            "UPDATE uye SET aktif = ? WHERE uye_id = ?",
            (1 if aktif else 0, uye_id),
        )


def next_uye_no() -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT uye_no FROM uye ORDER BY CAST(uye_no AS INTEGER) DESC LIMIT 1"
        ).fetchone()
    if not row:
        return "1001"
    return str(int(row["uye_no"]) + 1)


def add_uye(data: dict[str, Any]) -> None:
    sifre_duz = data.get("sifre") or "uye123"
    with get_connection() as conn:
        ayni_eposta = conn.execute(
            "SELECT uye_id FROM uye WHERE LOWER(eposta) = LOWER(?)",
            (data["eposta"],),
        ).fetchone()
        if ayni_eposta:
            raise ValueError("Bu e-posta ile kayıtlı üye var.")
        conn.execute(
            """
            INSERT INTO uye
            (uye_no, ad, soyad, eposta, telefon, kayit_tarihi, aktif, tip, sifre)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                data["uye_no"],
                data["ad"],
                data["soyad"],
                data["eposta"],
                data["telefon"],
                date.today().isoformat(),
                data.get("tip", "Öğrenci"),
                generate_password_hash(sifre_duz),
            ),
        )


def authenticate_uye(kimlik: str, sifre: str) -> Optional[Uye]:
    kimlik = kimlik.strip()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM uye
            WHERE uye_no = ? OR LOWER(eposta) = LOWER(?)
            LIMIT 1
            """,
            (kimlik, kimlik),
        ).fetchone()
    if not row:
        return None
    if not row["sifre"] or not check_password_hash(row["sifre"], sifre):
        return None
    uye = _uye_from_row(row)
    if not uye.aktif:
        raise ValueError("Hesabınız pasif. Kütüphane görevlisine başvurun.")
    return uye


def kayit_uye(data: dict[str, Any], sifre_tekrar: str = "") -> Uye:
    if len(data.get("sifre", "")) < 4:
        raise ValueError("Şifre en az 4 karakter olmalı.")
    if sifre_tekrar and data.get("sifre") != sifre_tekrar:
        raise ValueError("Şifreler eşleşmiyor.")
    data = {
        **data,
        "uye_no": next_uye_no(),
        "tip": "Öğrenci",
    }
    add_uye(data)
    uye = find_uye_hizli(data["uye_no"])
    if not uye:
        raise ValueError("Kayıt oluşturulamadı.")
    return uye


def update_uye_profil(uye_id: int, data: dict[str, Any]) -> None:
    with get_connection() as conn:
        ayni = conn.execute(
            """
            SELECT uye_id FROM uye
            WHERE LOWER(eposta) = LOWER(?) AND uye_id != ?
            """,
            (data["eposta"], uye_id),
        ).fetchone()
        if ayni:
            raise ValueError("Bu e-posta başka bir üyede kayıtlı.")
        conn.execute(
            """
            UPDATE uye SET ad = ?, soyad = ?, eposta = ?, telefon = ?
            WHERE uye_id = ?
            """,
            (data["ad"], data["soyad"], data["eposta"], data["telefon"], uye_id),
        )


def uye_sifre_degistir(uye_id: int, eski: str, yeni: str) -> None:
    if len(yeni) < 4:
        raise ValueError("Yeni şifre en az 4 karakter olmalı.")
    with get_connection() as conn:
        row = conn.execute("SELECT sifre FROM uye WHERE uye_id = ?", (uye_id,)).fetchone()
        if not row or not check_password_hash(row["sifre"], eski):
            raise ValueError("Mevcut şifre hatalı.")
        conn.execute(
            "UPDATE uye SET sifre = ? WHERE uye_id = ?",
            (generate_password_hash(yeni), uye_id),
        )


def uye_sifre_sifirla(uye_id: int, yeni: str = "uye123") -> str:
    if len(yeni) < 4:
        raise ValueError("Şifre en az 4 karakter olmalı.")
    with get_connection() as conn:
        row = conn.execute("SELECT uye_id FROM uye WHERE uye_id = ?", (uye_id,)).fetchone()
        if not row:
            raise ValueError("Üye bulunamadı.")
        conn.execute(
            "UPDATE uye SET sifre = ? WHERE uye_id = ?",
            (generate_password_hash(yeni), uye_id),
        )
    return yeni


def uye_detay(uye_id: int) -> dict[str, Any]:
    uye = get_uye(uye_id)
    if not uye:
        raise ValueError("Üye bulunamadı.")
    oduncler = list_oduncler_uye(uye_id, "hepsi")
    cezalar = list_cezalar_uye(uye_id)
    acik = [o for o in oduncler if o.durum in ("acik", "gecikti")]
    return {
        "uye": uye,
        "limit": uye.max_odunc_hakki(),
        "acik_sayisi": len(acik),
        "oduncler": oduncler,
        "cezalar": cezalar,
        "bekleyen_ceza": sum(float(c.toplam_tutar) for c in cezalar if not c.odendi),
    }


def global_ara(q: str) -> dict[str, Any]:
    q = q.strip()
    if not q:
        return {"uyeler": [], "kitaplar": [], "oduncler": []}
    return {
        "uyeler": list_uyeler(q=q)[:8],
        "kitaplar": list_kitaplar(q=q)[:8],
        "oduncler": list_oduncler(filtre="acik", q=q)[:8],
    }


def list_oduncler_uye(uye_id: int, filtre: str = "acik") -> list[Odunc]:
    sql = """
        SELECT o.*,
               k.ad AS kitap_ad,
               k.isbn AS kitap_isbn,
               k.yazar AS kitap_yazar,
               k.raf_konumu AS raf_konumu,
               c.ad AS kategori_ad,
               u.ad || ' ' || u.soyad AS uye_ad,
               u.uye_no AS uye_no,
               p.ad || ' ' || p.soyad AS personel_ad
        FROM odunc o
        JOIN kitap k ON k.kitap_id = o.kitap_id
        JOIN kategori c ON c.kategori_id = k.kategori_id
        JOIN uye u ON u.uye_id = o.uye_id
        JOIN personel p ON p.personel_id = o.personel_id
        WHERE o.uye_id = ?
    """
    params: list[Any] = [uye_id]
    if filtre == "acik":
        sql += " AND o.durum IN ('acik', 'gecikti')"
    elif filtre == "geciken":
        sql += " AND o.durum = 'gecikti'"
    elif filtre == "iade":
        sql += " AND o.durum = 'iade'"
    # filtre == "hepsi" → ek koşul yok
    sql += " ORDER BY o.planlanan_iade DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    bugun = date.today()
    sonuc: list[Odunc] = []
    for r in rows:
        odunc = _odunc_from_row(r)
        if odunc.durum != "iade" and odunc.gecikti_mi(bugun) and odunc.durum != "gecikti":
            with get_connection() as conn:
                conn.execute(
                    "UPDATE odunc SET durum = 'gecikti' WHERE odunc_id = ?",
                    (odunc.odunc_id,),
                )
            odunc.durum = "gecikti"
        sonuc.append(odunc)
    return sonuc


def list_cezalar_uye(uye_id: int) -> list[Ceza]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*,
                   u.ad || ' ' || u.soyad AS uye_ad,
                   u.uye_no AS uye_no,
                   k.ad AS kitap_ad
            FROM ceza c
            JOIN odunc o ON o.odunc_id = c.odunc_id
            JOIN uye u ON u.uye_id = o.uye_id
            JOIN kitap k ON k.kitap_id = o.kitap_id
            WHERE o.uye_id = ?
            ORDER BY c.odendi ASC, c.ceza_id DESC
            """,
            (uye_id,),
        ).fetchall()
    return [
        Ceza(
            ceza_id=r["ceza_id"],
            gun_sayisi=r["gun_sayisi"],
            gunluk_tutar=Decimal(r["gunluk_tutar"]),
            toplam_tutar=Decimal(r["toplam_tutar"]),
            odendi=bool(r["odendi"]),
            odunc_id=r["odunc_id"],
            uye_ad=r["uye_ad"],
            kitap_ad=r["kitap_ad"],
            uye_no=r["uye_no"],
        )
        for r in rows
    ]


def uye_ozet_sayilar(uye_id: int) -> dict[str, Any]:
    """Üst bar için hafif özet (liste çekmez)."""
    with get_connection() as conn:
        acik = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND durum IN ('acik', 'gecikti')
            """,
            (uye_id,),
        ).fetchone()["c"]
        geciken = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND durum = 'gecikti'
            """,
            (uye_id,),
        ).fetchone()["c"]
        # Planlanan iadesi geçmiş ama durumu henüz güncellenmemiş açık kayıtlar
        bugun = date.today().isoformat()
        geciken_plan = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND durum = 'acik' AND planlanan_iade < ?
            """,
            (uye_id, bugun),
        ).fetchone()["c"]
        bekleyen = conn.execute(
            """
            SELECT COALESCE(SUM(CAST(c.toplam_tutar AS REAL)), 0) AS t
            FROM ceza c
            JOIN odunc o ON o.odunc_id = c.odunc_id
            WHERE o.uye_id = ? AND c.odendi = 0
            """,
            (uye_id,),
        ).fetchone()["t"]
    return {
        "acik_odunc": acik,
        "geciken": geciken + geciken_plan,
        "bekleyen_ceza": float(bekleyen or 0),
    }


def uye_panel_ozet(uye_id: int) -> dict[str, Any]:
    """Özet sayfası: sayılar + son ödünç/ceza listeleri."""
    sayilar = uye_ozet_sayilar(uye_id)
    oduncler = list_oduncler_uye(uye_id, "acik")
    cezalar = list_cezalar_uye(uye_id)
    return {
        **sayilar,
        "oduncler": oduncler[:5],
        "cezalar": [c for c in cezalar if not c.odendi][:5],
    }


def _odunc_from_row(r: sqlite3.Row) -> Odunc:
    keys = r.keys()
    return Odunc(
        odunc_id=r["odunc_id"],
        alis_tarihi=date.fromisoformat(r["alis_tarihi"]),
        planlanan_iade=date.fromisoformat(r["planlanan_iade"]),
        gercek_iade=date.fromisoformat(r["gercek_iade"]) if r["gercek_iade"] else None,
        durum=r["durum"],
        kitap_id=r["kitap_id"],
        uye_id=r["uye_id"],
        personel_id=r["personel_id"],
        kitap_ad=r["kitap_ad"] if "kitap_ad" in keys else "",
        uye_ad=r["uye_ad"] if "uye_ad" in keys else "",
        personel_ad=r["personel_ad"] if "personel_ad" in keys else "",
        uye_no=r["uye_no"] if "uye_no" in keys else "",
        kitap_isbn=r["kitap_isbn"] if "kitap_isbn" in keys else "",
        kitap_yazar=r["kitap_yazar"] if "kitap_yazar" in keys else "",
        raf_konumu=r["raf_konumu"] if "raf_konumu" in keys else "",
        kategori_ad=r["kategori_ad"] if "kategori_ad" in keys else "",
        uzatildi=bool(r["uzatildi"]) if "uzatildi" in keys else False,
    )


def list_oduncler(filtre: str = "acik", q: str = "") -> list[Odunc]:
    sql = """
        SELECT o.*,
               k.ad AS kitap_ad,
               k.isbn AS kitap_isbn,
               u.ad || ' ' || u.soyad AS uye_ad,
               u.uye_no AS uye_no,
               p.ad || ' ' || p.soyad AS personel_ad
        FROM odunc o
        JOIN kitap k ON k.kitap_id = o.kitap_id
        JOIN uye u ON u.uye_id = o.uye_id
        JOIN personel p ON p.personel_id = o.personel_id
        WHERE 1=1
    """
    params: list[Any] = []
    if filtre == "acik":
        sql += " AND o.durum IN ('acik', 'gecikti')"
    elif filtre == "geciken":
        sql += " AND o.durum = 'gecikti'"
    elif filtre == "iade":
        sql += " AND o.durum = 'iade'"
    if q:
        sql += """
            AND (
                u.uye_no LIKE ? OR u.ad LIKE ? OR u.soyad LIKE ?
                OR k.ad LIKE ? OR k.isbn LIKE ? OR CAST(k.kitap_id AS TEXT) = ?
            )
        """
        like = f"%{q}%"
        params.extend([like, like, like, like, like, q])
    sql += " ORDER BY CASE WHEN o.durum = 'gecikti' THEN 0 ELSE 1 END, o.planlanan_iade"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    bugun = date.today()
    sonuc: list[Odunc] = []
    for r in rows:
        odunc = _odunc_from_row(r)
        if odunc.durum != "iade" and odunc.gecikti_mi(bugun) and odunc.durum != "gecikti":
            with get_connection() as conn:
                conn.execute(
                    "UPDATE odunc SET durum = 'gecikti' WHERE odunc_id = ?",
                    (odunc.odunc_id,),
                )
            odunc.durum = "gecikti"
        sonuc.append(odunc)
    return sonuc


def odunc_ver(uye_id: int, kitap_id: int, personel_id: int) -> None:
    with get_connection() as conn:
        uye = conn.execute("SELECT * FROM uye WHERE uye_id = ?", (uye_id,)).fetchone()
        kitap = conn.execute("SELECT * FROM kitap WHERE kitap_id = ?", (kitap_id,)).fetchone()
        if not uye or not kitap:
            raise ValueError("Üye veya kitap bulunamadı.")
        if not uye["aktif"]:
            raise ValueError("Pasif üye ödünç alamaz.")

        ayni_kitap = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND kitap_id = ? AND durum IN ('acik', 'gecikti')
            """,
            (uye_id, kitap_id),
        ).fetchone()["c"]
        if ayni_kitap:
            raise ValueError("Üyenin bu kitaptan zaten açık ödüncü var.")

        if kitap["musait_adet"] <= 0:
            raise ValueError("Rafta müsait kopya yok.")

        borc = conn.execute(
            """
            SELECT COUNT(*) AS c FROM ceza c
            JOIN odunc o ON o.odunc_id = c.odunc_id
            WHERE o.uye_id = ? AND c.odendi = 0
            """,
            (uye_id,),
        ).fetchone()["c"]
        if borc:
            raise ValueError("Üyenin ödenmemiş cezası var.")

        geciken = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND durum = 'gecikti'
            """,
            (uye_id,),
        ).fetchone()["c"]
        if geciken:
            raise ValueError("Üyenin gecikmiş kitabı var.")

        acik_sayisi = conn.execute(
            """
            SELECT COUNT(*) AS c FROM odunc
            WHERE uye_id = ? AND durum IN ('acik', 'gecikti')
            """,
            (uye_id,),
        ).fetchone()["c"]
        limit = KUTUPHANE.max_odunc_icin(uye["tip"])
        if acik_sayisi >= limit:
            raise ValueError(
                f"Ödünç limiti dolu ({uye['tip']}: en fazla {limit} kitap)."
            )

        alis = date.today()
        iade = KUTUPHANE.planlanan_iade_hesapla(alis)
        conn.execute(
            "UPDATE kitap SET musait_adet = musait_adet - 1 WHERE kitap_id = ?",
            (kitap_id,),
        )
        conn.execute(
            """
            INSERT INTO odunc
            (alis_tarihi, planlanan_iade, gercek_iade, durum, kitap_id, uye_id, personel_id, uzatildi)
            VALUES (?, ?, NULL, 'acik', ?, ?, ?, 0)
            """,
            (alis.isoformat(), iade.isoformat(), kitap_id, uye_id, personel_id),
        )


def sure_uzat(odunc_id: int) -> Odunc:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT o.*,
                   k.ad AS kitap_ad,
                   k.isbn AS kitap_isbn,
                   u.ad || ' ' || u.soyad AS uye_ad,
                   u.uye_no AS uye_no,
                   p.ad || ' ' || p.soyad AS personel_ad
            FROM odunc o
            JOIN kitap k ON k.kitap_id = o.kitap_id
            JOIN uye u ON u.uye_id = o.uye_id
            JOIN personel p ON p.personel_id = o.personel_id
            WHERE o.odunc_id = ?
            """,
            (odunc_id,),
        ).fetchone()
        if not row:
            raise ValueError("Ödünç kaydı bulunamadı.")
        odunc = _odunc_from_row(row)
        odunc.sure_uzat(KUTUPHANE.uzatma_gun)
        conn.execute(
            """
            UPDATE odunc
            SET planlanan_iade = ?, uzatildi = 1, durum = 'acik'
            WHERE odunc_id = ?
            """,
            (odunc.planlanan_iade.isoformat(), odunc_id),
        )
        return odunc


def iade_al(odunc_id: int) -> Optional[Ceza]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM odunc WHERE odunc_id = ?", (odunc_id,)).fetchone()
        if not row or row["durum"] == "iade":
            raise ValueError("Geçerli açık ödünç kaydı yok.")

        odunc = _odunc_from_row(row)
        bugun = date.today()
        gun = odunc.gecikme_gunu(bugun)
        odunc.iade_et(bugun)
        conn.execute(
            """
            UPDATE odunc SET gercek_iade = ?, durum = 'iade'
            WHERE odunc_id = ?
            """,
            (bugun.isoformat(), odunc_id),
        )
        conn.execute(
            "UPDATE kitap SET musait_adet = musait_adet + 1 WHERE kitap_id = ?",
            (odunc.kitap_id,),
        )

        if gun <= 0:
            return None

        tutar = KUTUPHANE.ceza_hesapla(gun)
        mevcut = conn.execute(
            "SELECT ceza_id FROM ceza WHERE odunc_id = ?",
            (odunc_id,),
        ).fetchone()
        if mevcut:
            conn.execute(
                """
                UPDATE ceza SET gun_sayisi = ?, toplam_tutar = ?, odendi = 0
                WHERE odunc_id = ?
                """,
                (gun, str(tutar), odunc_id),
            )
            ceza_id = mevcut["ceza_id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO ceza (gun_sayisi, gunluk_tutar, toplam_tutar, odendi, odunc_id)
                VALUES (?, ?, ?, 0, ?)
                """,
                (gun, str(KUTUPHANE.gunluk_ceza), str(tutar), odunc_id),
            )
            ceza_id = cur.lastrowid

        return Ceza(
            ceza_id=ceza_id,
            gun_sayisi=gun,
            gunluk_tutar=KUTUPHANE.gunluk_ceza,
            toplam_tutar=tutar,
            odendi=False,
            odunc_id=odunc_id,
        )


def list_cezalar(filtre: str = "all") -> list[Ceza]:
    sql = """
        SELECT c.*,
               u.ad || ' ' || u.soyad AS uye_ad,
               u.uye_no AS uye_no,
               k.ad AS kitap_ad
        FROM ceza c
        JOIN odunc o ON o.odunc_id = c.odunc_id
        JOIN uye u ON u.uye_id = o.uye_id
        JOIN kitap k ON k.kitap_id = o.kitap_id
        WHERE 1=1
    """
    if filtre == "unpaid":
        sql += " AND c.odendi = 0"
    elif filtre == "paid":
        sql += " AND c.odendi = 1"
    sql += " ORDER BY c.odendi ASC, c.ceza_id DESC"

    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [
        Ceza(
            ceza_id=r["ceza_id"],
            gun_sayisi=r["gun_sayisi"],
            gunluk_tutar=Decimal(r["gunluk_tutar"]),
            toplam_tutar=Decimal(r["toplam_tutar"]),
            odendi=bool(r["odendi"]),
            odunc_id=r["odunc_id"],
            uye_ad=r["uye_ad"],
            kitap_ad=r["kitap_ad"],
            uye_no=r["uye_no"],
        )
        for r in rows
    ]


def ceza_ode(ceza_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE ceza SET odendi = 1 WHERE ceza_id = ?", (ceza_id,))


def panel_istatistikleri() -> dict[str, Any]:
    with get_connection() as conn:
        kitap = conn.execute("SELECT COUNT(*) AS c FROM kitap").fetchone()["c"]
        uye = conn.execute("SELECT COUNT(*) AS c FROM uye WHERE aktif = 1").fetchone()["c"]
        acik = conn.execute(
            "SELECT COUNT(*) AS c FROM odunc WHERE durum IN ('acik', 'gecikti')"
        ).fetchone()["c"]
        geciken = conn.execute(
            "SELECT COUNT(*) AS c FROM odunc WHERE durum = 'gecikti'"
        ).fetchone()["c"]
        bekleyen_ceza = conn.execute(
            "SELECT COALESCE(SUM(CAST(toplam_tutar AS REAL)), 0) AS t FROM ceza WHERE odendi = 0"
        ).fetchone()["t"]
        bugun_iade = conn.execute(
            """
            SELECT o.*,
                   k.ad AS kitap_ad,
                   u.ad || ' ' || u.soyad AS uye_ad,
                   u.uye_no AS uye_no
            FROM odunc o
            JOIN kitap k ON k.kitap_id = o.kitap_id
            JOIN uye u ON u.uye_id = o.uye_id
            WHERE o.durum IN ('acik', 'gecikti')
              AND o.planlanan_iade <= date('now', '+1 day')
            ORDER BY o.planlanan_iade
            LIMIT 8
            """
        ).fetchall()
        cezalar = conn.execute(
            """
            SELECT c.*,
                   u.ad || ' ' || u.soyad AS uye_ad,
                   k.ad AS kitap_ad
            FROM ceza c
            JOIN odunc o ON o.odunc_id = c.odunc_id
            JOIN uye u ON u.uye_id = o.uye_id
            JOIN kitap k ON k.kitap_id = o.kitap_id
            WHERE c.odendi = 0
            ORDER BY CAST(c.toplam_tutar AS REAL) DESC
            LIMIT 5
            """
        ).fetchall()
        acil_gecikenler = conn.execute(
            """
            SELECT o.*,
                   k.ad AS kitap_ad,
                   k.isbn AS kitap_isbn,
                   u.ad || ' ' || u.soyad AS uye_ad,
                   u.uye_no AS uye_no,
                   CAST(julianday('now') - julianday(o.planlanan_iade) AS INTEGER) AS gecikme_gun
            FROM odunc o
            JOIN kitap k ON k.kitap_id = o.kitap_id
            JOIN uye u ON u.uye_id = o.uye_id
            WHERE o.durum = 'gecikti'
            ORDER BY o.planlanan_iade ASC
            LIMIT 6
            """
        ).fetchall()

    return {
        "kitap": kitap,
        "uye": uye,
        "acik": acik,
        "geciken": geciken,
        "bekleyen_ceza": bekleyen_ceza,
        "bugun_iade": [dict(r) for r in bugun_iade],
        "odenmemis_cezalar": [dict(r) for r in cezalar],
        "acil_gecikenler": [dict(r) for r in acil_gecikenler],
    }


def rapor_verileri() -> dict[str, Any]:
    with get_connection() as conn:
        populer = conn.execute(
            """
            SELECT k.kitap_id, k.ad, k.yazar, k.isbn, COUNT(o.odunc_id) AS odunc_sayisi
            FROM kitap k
            LEFT JOIN odunc o ON o.kitap_id = k.kitap_id
            GROUP BY k.kitap_id
            ORDER BY odunc_sayisi DESC, k.ad
            LIMIT 10
            """
        ).fetchall()
        aktif_uyeler = conn.execute(
            """
            SELECT u.uye_id, u.uye_no, u.ad || ' ' || u.soyad AS tam_ad,
                   COUNT(o.odunc_id) AS odunc_sayisi
            FROM uye u
            LEFT JOIN odunc o ON o.uye_id = u.uye_id
            GROUP BY u.uye_id
            ORDER BY odunc_sayisi DESC, u.uye_no
            LIMIT 10
            """
        ).fetchall()
        ceza_ozet = conn.execute(
            """
            SELECT
                COUNT(*) AS kayit,
                COALESCE(SUM(CAST(toplam_tutar AS REAL)), 0) AS toplam,
                COALESCE(SUM(CASE WHEN odendi = 1 THEN CAST(toplam_tutar AS REAL) ELSE 0 END), 0) AS odenen,
                COALESCE(SUM(CASE WHEN odendi = 0 THEN CAST(toplam_tutar AS REAL) ELSE 0 END), 0) AS bekleyen
            FROM ceza
            """
        ).fetchone()
        kategori_dagilim = conn.execute(
            """
            SELECT c.ad AS kategori, COUNT(k.kitap_id) AS adet
            FROM kategori c
            LEFT JOIN kitap k ON k.kategori_id = c.kategori_id
            GROUP BY c.kategori_id
            ORDER BY adet DESC
            """
        ).fetchall()
        durumlar = conn.execute(
            """
            SELECT
                SUM(CASE WHEN durum = 'acik' THEN 1 ELSE 0 END) AS acik,
                SUM(CASE WHEN durum = 'gecikti' THEN 1 ELSE 0 END) AS gecikti,
                SUM(CASE WHEN durum = 'iade' THEN 1 ELSE 0 END) AS iade
            FROM odunc
            """
        ).fetchone()

    return {
        "populer_kitaplar": [dict(r) for r in populer],
        "aktif_uyeler": [dict(r) for r in aktif_uyeler],
        "ceza_ozet": dict(ceza_ozet),
        "kategori_dagilim": [dict(r) for r in kategori_dagilim],
        "odunc_durumlar": dict(durumlar) if durumlar else {"acik": 0, "gecikti": 0, "iade": 0},
    }
