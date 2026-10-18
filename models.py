"""Kütüphane otomasyonu domain sınıfları."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class Kategori:
    kategori_id: int
    ad: str
    aciklama: str = ""

    def kategori_bilgisi(self) -> str:
        return f"{self.ad}: {self.aciklama}" if self.aciklama else self.ad


@dataclass
class Kitap:
    kitap_id: int
    isbn: str
    ad: str
    yazar: str
    yayinevi: str
    yayin_yili: int
    toplam_adet: int
    musait_adet: int
    raf_konumu: str
    kategori_id: int
    kategori_ad: str = ""

    def musait_mi(self) -> bool:
        return self.musait_adet > 0

    def adet_azalt(self) -> None:
        if self.musait_adet <= 0:
            raise ValueError("Rafta müsait kopya yok.")
        self.musait_adet -= 1

    def adet_artir(self) -> None:
        if self.musait_adet >= self.toplam_adet:
            raise ValueError("Müsait adet toplam adedi aşamaz.")
        self.musait_adet += 1

    def durum_metni(self) -> str:
        return "Müsait" if self.musait_mi() else "Rafta yok"


@dataclass
class Uye:
    uye_id: int
    uye_no: str
    ad: str
    soyad: str
    eposta: str
    telefon: str
    kayit_tarihi: date
    aktif: bool = True
    tip: str = "Öğrenci"
    sifre: str = ""

    def tam_ad(self) -> str:
        return f"{self.ad} {self.soyad}"

    def aktif_mi(self) -> bool:
        return self.aktif

    def pasife_al(self) -> None:
        self.aktif = False

    def aktiflestir(self) -> None:
        self.aktif = True

    def max_odunc_hakki(self) -> int:
        """Limit tek kaynaktan: Kutuphane.max_odunc_icin."""
        return Kutuphane().max_odunc_icin(self.tip)


@dataclass
class Personel:
    personel_id: int
    ad: str
    soyad: str
    kullanici_adi: str
    sifre: str
    rol: str = "Görevli"

    def tam_ad(self) -> str:
        return f"{self.ad} {self.soyad}"


@dataclass
class Odunc:
    odunc_id: int
    alis_tarihi: date
    planlanan_iade: date
    gercek_iade: Optional[date]
    durum: str
    kitap_id: int
    uye_id: int
    personel_id: int
    kitap_ad: str = ""
    uye_ad: str = ""
    personel_ad: str = ""
    uye_no: str = ""
    kitap_isbn: str = ""
    kitap_yazar: str = ""
    raf_konumu: str = ""
    kategori_ad: str = ""
    uzatildi: bool = False

    def gecikti_mi(self, bugun: Optional[date] = None) -> bool:
        bugun = bugun or date.today()
        if self.durum == "iade":
            return False
        return bugun > self.planlanan_iade

    def gecikme_gunu(self, bugun: Optional[date] = None) -> int:
        bugun = bugun or date.today()
        if not self.gecikti_mi(bugun):
            return 0
        return (bugun - self.planlanan_iade).days

    def iade_et(self, tarih: Optional[date] = None) -> None:
        self.gercek_iade = tarih or date.today()
        self.durum = "iade"

    def sure_uzatilabilir_mi(self, bugun: Optional[date] = None) -> bool:
        bugun = bugun or date.today()
        return self.durum == "acik" and not self.gecikti_mi(bugun) and not self.uzatildi

    def sure_uzat(self, ekstra_gun: int = 7, bugun: Optional[date] = None) -> None:
        if not self.sure_uzatilabilir_mi(bugun):
            raise ValueError("Bu ödünç kaydı uzatılamaz (gecikmiş veya daha önce uzatılmış).")
        self.planlanan_iade = self.planlanan_iade + timedelta(days=ekstra_gun)
        self.uzatildi = True


@dataclass
class Ceza:
    ceza_id: int
    gun_sayisi: int
    gunluk_tutar: Decimal
    toplam_tutar: Decimal
    odendi: bool
    odunc_id: int
    uye_ad: str = ""
    kitap_ad: str = ""
    uye_no: str = ""

    def tutar_hesapla(self) -> Decimal:
        self.toplam_tutar = Decimal(self.gun_sayisi) * self.gunluk_tutar
        return self.toplam_tutar

    def ode(self) -> None:
        self.odendi = True


@dataclass
class Kutuphane:
    ad: str = "Atlas Kütüphane"
    odunc_suresi_gun: int = 14
    gunluk_ceza: Decimal = Decimal("15.00")
    uzatma_gun: int = 7
    ogrenci_max_odunc: int = 5
    akademisyen_max_odunc: int = 15
    idari_max_odunc: int = 8

    def planlanan_iade_hesapla(self, alis: Optional[date] = None) -> date:
        alis = alis or date.today()
        return alis + timedelta(days=self.odunc_suresi_gun)

    def ceza_hesapla(self, gecikme_gunu: int) -> Decimal:
        return Decimal(gecikme_gunu) * self.gunluk_ceza

    def max_odunc_icin(self, tip: str) -> int:
        tip_l = (tip or "").lower()
        if "akadem" in tip_l:
            return self.akademisyen_max_odunc
        if "idari" in tip_l:
            return self.idari_max_odunc
        return self.ogrenci_max_odunc
