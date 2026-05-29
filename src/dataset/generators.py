"""
generators.py -- Bes halusinasyon kategorisi (H1-H5) icin ornek uretici fonksiyonlar.

Tasarim ilkesi: "construction'dan bilinen ground-truth".
- H1, H4: tamamen sentetik -> etiket insasi geregi kesindir.
- H2: gercek bir makalenin TEK bir alani bozulur -> etiket kesindir.
- H3: gercek bir makale + alakasiz atif baglami -> etiket kesindir.
- H5: gercek, dogrulanmis makale -> negatif (halusinasyon yok).

Bu deterministik insa, "YZ otomatik etiketlemesi" DEGILDIR; etiket, ornegin nasil
uretildiginin matematiksel sonucudur. Yine de proje rubrigi geregi her ornek
annotation_tool.py ile bir insan tarafindan gozden gecirilip onaylanir
(verified=true). Boylece ground-truth nihai olarak insan denetimine dayanir.

Cikti semasi (her ornek):
{
  "id": int,
  "kategori": "H1".."H5",
  "zorluk": "kolay|orta|zor",
  "girdi": "<IEEE bicimli referans dizgesi>",
  "baglam": "<sadece H3 icin atif baglami; digerlerinde ''>",
  "beklenen_cevap": {"hallucination": bool, "type": "H1..H5|none", "reason": str},
  "metadata": {"title","authors","year","venue","doi"},
  "kaynak": "synthetic|crossref|openalex|seed",
  "aciklama": "<insa notu>",
  "verified": false
}
"""
from __future__ import annotations

import random
from typing import Dict, Any, List

from . import seeds


def format_ieee(meta: Dict[str, Any]) -> str:
    """Metadata sozlugunden IEEE benzeri bir referans dizgesi olusturur."""
    authors = meta.get("authors") or []
    if len(authors) > 4:
        author_str = ", ".join(authors[:3]) + " et al."
    else:
        author_str = ", ".join(authors)
    title = meta.get("title", "")
    venue = meta.get("venue", "")
    year = meta.get("year", "")
    doi = meta.get("doi")
    s = f'{author_str}, "{title}," in {venue}, {year}.'
    if doi:
        s += f" doi: {doi}."
    return s


# --- H1: Tamamen var olmayan referans -----------------------------------------
def gen_h1(rng: random.Random, n: int, start_id: int) -> List[Dict[str, Any]]:
    out = []
    for i in range(n):
        n_auth = rng.randint(2, 4)
        authors = [f"{rng.choice(seeds.FAKE_INITIALS)} {rng.choice(seeds.FAKE_SURNAMES)}"
                   for _ in range(n_auth)]
        title = f"{rng.choice(seeds.FAKE_TITLE_PREFIX)} {rng.choice(seeds.FAKE_TITLE_TOPIC)}"
        venue = rng.choice(seeds.FAKE_VENUES)
        year = rng.randint(2015, 2024)
        meta = {"title": title, "authors": authors, "year": year,
                "venue": venue, "doi": None}
        # Zorluk: gercekciligi yuksek (taninmis venue + makul yil) = zor
        difficulty = rng.choices(["kolay", "orta", "zor"], weights=[3, 4, 3])[0]
        out.append({
            "id": start_id + i,
            "kategori": "H1",
            "zorluk": difficulty,
            "girdi": format_ieee(meta),
            "baglam": "",
            "beklenen_cevap": {
                "hallucination": True, "type": "H1",
                "reason": "Tamamen uydurma referans: bu baslik/yazar kombinasyonuna "
                          "sahip yayimlanmis bir makale yoktur."},
            "metadata": meta,
            "kaynak": "synthetic",
            "aciklama": "Sentetik olarak uretilmis, hicbir veritabaninda bulunmayan referans.",
            "verified": False,
        })
    return out


# --- H2: Metadata halusinasyonu (gercek makale, bozuk alan) -------------------
def gen_h2(rng: random.Random, real_papers: List[Dict[str, Any]],
           n: int, start_id: int) -> List[Dict[str, Any]]:
    out = []
    for i in range(n):
        base = dict(rng.choice(real_papers))
        meta = dict(base)
        meta["authors"] = list(base.get("authors") or [])
        field = rng.choice(["author", "year", "venue"])
        if field == "author" and meta["authors"]:
            wrong = f"{rng.choice(seeds.FAKE_INITIALS)} {rng.choice(seeds.FAKE_SURNAMES)}"
            meta["authors"] = [wrong] + meta["authors"][1:]
            reason = "Birinci yazar yanlis: bu makalenin gercek yazar listesiyle uyusmuyor."
            difficulty = "orta"
        elif field == "year":
            delta = rng.choice([-2, -1, 1, 2, 3])
            meta["year"] = (base.get("year") or 2018) + delta
            reason = "Yayin yili gercek kayittan farkli (metadata uyumsuzlugu)."
            difficulty = "zor" if abs(delta) == 1 else "orta"
        else:
            meta["venue"] = rng.choice([v for v in seeds.FAKE_VENUES
                                        if v != base.get("venue")])
            reason = "Yayin yeri (dergi/konferans) gercek kayitla celisiyor."
            difficulty = "orta"
        # DOI'yi koru: gercek DOI + bozuk metadata = klasik metadata halusinasyonu
        out.append({
            "id": start_id + i,
            "kategori": "H2",
            "zorluk": difficulty,
            "girdi": format_ieee(meta),
            "baglam": "",
            "beklenen_cevap": {"hallucination": True, "type": "H2", "reason": reason},
            "metadata": meta,
            "kaynak": base.get("kaynak", "seed"),
            "aciklama": f"Gercek makalenin '{field}' alani kasitli olarak bozuldu.",
            "verified": False,
        })
    return out


# --- H3: Semantik uyumsuzluk (gercek makale, alakasiz baglam) -----------------
def gen_h3(rng: random.Random, real_papers: List[Dict[str, Any]],
           n: int, start_id: int) -> List[Dict[str, Any]]:
    out = []
    for i in range(n):
        base = dict(rng.choice(real_papers))
        context = rng.choice(seeds.UNRELATED_CONTEXTS)
        difficulty = rng.choices(["kolay", "orta", "zor"], weights=[2, 4, 4])[0]
        out.append({
            "id": start_id + i,
            "kategori": "H3",
            "zorluk": difficulty,
            "girdi": format_ieee(base),
            "baglam": context,
            "beklenen_cevap": {
                "hallucination": True, "type": "H3",
                "reason": "Referans gercek olsa da, atif yapilan baglamin konusuyla "
                          "anlamsal olarak ilgisiz (semantik uyumsuzluk)."},
            "metadata": base,
            "kaynak": base.get("kaynak", "seed"),
            "aciklama": "Gercek makale, konusuyla alakasiz bir atif baglamina yerlestirildi.",
            "verified": False,
        })
    return out


# --- H4: Kronolojik halusinasyon (imkansiz/gelecek tarih) ---------------------
def gen_h4(rng: random.Random, real_papers: List[Dict[str, Any]],
           n: int, start_id: int) -> List[Dict[str, Any]]:
    out = []
    for i in range(n):
        base = dict(rng.choice(real_papers))
        meta = dict(base)
        mode = rng.choice(["future", "impossible_before"])
        if mode == "future":
            meta["year"] = rng.choice([2027, 2028, 2030, 2031])
            reason = "Yayin yili gelecekte (imkansiz tarih)."
            difficulty = "kolay"
        else:
            # Teknolojiden once: orn. "Transformer" makalesini 1995'e atfetmek
            meta["year"] = rng.choice([1985, 1990, 1995])
            reason = "Yayin yili, konunun/teknolojinin var olusundan once (kronolojik celiski)."
            difficulty = "orta"
        out.append({
            "id": start_id + i,
            "kategori": "H4",
            "zorluk": difficulty,
            "girdi": format_ieee(meta),
            "baglam": "",
            "beklenen_cevap": {"hallucination": True, "type": "H4", "reason": reason},
            "metadata": meta,
            "kaynak": base.get("kaynak", "seed"),
            "aciklama": f"Gercek makaleye kronolojik olarak imkansiz yil atandi ({mode}).",
            "verified": False,
        })
    return out


# --- H5: Dogru referans (negatif) ---------------------------------------------
def gen_h5(rng: random.Random, real_papers: List[Dict[str, Any]],
           n: int, start_id: int) -> List[Dict[str, Any]]:
    out = []
    pool = list(real_papers)
    rng.shuffle(pool)
    for i in range(n):
        base = dict(pool[i % len(pool)])
        difficulty = rng.choices(["kolay", "orta", "zor"], weights=[4, 4, 2])[0]
        out.append({
            "id": start_id + i,
            "kategori": "H5",
            "zorluk": difficulty,
            "girdi": format_ieee(base),
            "baglam": "",
            "beklenen_cevap": {
                "hallucination": False, "type": "none",
                "reason": "Tum alanlar (baslik, yazar, yil, yer) dogrulanmis; halusinasyon yok."},
            "metadata": base,
            "kaynak": base.get("kaynak", "seed"),
            "aciklama": "Dogrulanmis gercek referans (negatif ornek).",
            "verified": False,
        })
    return out


# Kategori -> hedef ornek sayisi (ara rapordaki Tablo 3 ile uyumlu, toplam 300)
CATEGORY_TARGETS = {"H1": 80, "H2": 60, "H3": 60, "H4": 40, "H5": 60}
