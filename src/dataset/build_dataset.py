"""
build_dataset.py -- Benchmark veri kumesini insa eder.

Iki mod:
  --offline   : Sadece seeds.py'deki gercek makaleleri kullanir (internet GEREKMEZ).
                Hizli, tekrarlanabilir bir ORNEK veri kumesi uretir. Smoke-test icin.
  (varsayilan): CrossRef + OpenAlex API'lerinden gercek makale metadata/abstract
                ceker, boylece tam 300 ornekluk gercek veri kumesini olusturur.
                Internet + (OpenAlex icin) API anahtari gerektirir.

Kullanim:
  python -m src.dataset.build_dataset --offline --n-per-cat 6 --out data/benchmark/sample_benchmark.json
  python -m src.dataset.build_dataset --out data/benchmark/benchmark.json --mailto you@itu.edu.tr

Ground-truth NOTU: Bu script construction'dan-bilinen etiketlerle ornek URETIR;
nihai onay icin annotation_tool.py ile elle dogrulayin (rubrik geregi).
"""
from __future__ import annotations

import argparse
import json
import os
import random
from typing import List, Dict, Any

from . import generators as gen
from . import seeds
from ..dotenv_loader import load_env


def real_papers_from_seeds() -> List[Dict[str, Any]]:
    papers = []
    for title, authors, year, venue in seeds.SEED_PAPERS:
        papers.append({"title": title, "authors": list(authors), "year": year,
                       "venue": venue, "doi": None, "kaynak": "seed"})
    return papers


def real_papers_from_apis(mailto: str, target: int) -> List[Dict[str, Any]]:
    """CrossRef + OpenAlex'ten gercek, dogrulanmis makale havuzu cizer."""
    from .crossref_client import CrossRefClient
    from .openalex_client import OpenAlexClient

    cr = CrossRefClient(mailto=mailto)
    oa = OpenAlexClient(mailto=mailto)
    papers: List[Dict[str, Any]] = []

    # 1) Tohum basliklari CrossRef ile dogrula -> otoritatif DOI/metadata
    for title, *_ in seeds.SEED_PAPERS:
        items = cr.search_by_title(title, rows=1)
        if items:
            m = cr.normalize(items[0])
            m["kaynak"] = "crossref"
            if m.get("title") and m.get("year"):
                papers.append(m)

    # 2) OpenAlex'ten konu bazli, abstract'li makaleler ekle (H3 + RAG icin faydali)
    topics = ["intrusion detection deep learning", "malware classification",
              "adversarial machine learning security", "vulnerability assessment cvss",
              "phishing detection", "network anomaly detection",
              "side channel attack", "ransomware detection"]
    for t in topics:
        for item in oa.search(t, per_page=8, require_abstract=True):
            m = oa.normalize(item)
            m["kaynak"] = "openalex"
            if m.get("title") and m.get("year") and m.get("authors"):
                papers.append(m)
            if len(papers) >= target:
                break
        if len(papers) >= target:
            break

    # Tekillestir (baslik bazinda)
    seen, uniq = set(), []
    for p in papers:
        key = p["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def build(real_papers: List[Dict[str, Any]], n_per_cat: Dict[str, int],
          rng: random.Random) -> List[Dict[str, Any]]:
    dataset: List[Dict[str, Any]] = []
    next_id = 1
    builders = {
        "H1": lambda n, sid: gen.gen_h1(rng, n, sid),
        "H2": lambda n, sid: gen.gen_h2(rng, real_papers, n, sid),
        "H3": lambda n, sid: gen.gen_h3(rng, real_papers, n, sid),
        "H4": lambda n, sid: gen.gen_h4(rng, real_papers, n, sid),
        "H5": lambda n, sid: gen.gen_h5(rng, real_papers, n, sid),
    }
    for cat in ["H1", "H2", "H3", "H4", "H5"]:
        items = builders[cat](n_per_cat[cat], next_id)
        dataset.extend(items)
        next_id += len(items)
    return dataset


def write_data_card(dataset: List[Dict[str, Any]], path: str, mode: str) -> None:
    from collections import Counter
    cat = Counter(e["kategori"] for e in dataset)
    diff = Counter(e["zorluk"] for e in dataset)
    pos = sum(1 for e in dataset if e["beklenen_cevap"]["hallucination"])
    neg = len(dataset) - pos
    card = f"""## Dataset Card: BibHallu-Bench

### Ozet
- Amac: Arastirma makalelerindeki bibliyografya halusinasyonlarinin LLM tabanli tespiti icin benchmark
- Toplam ornek: {len(dataset)} | Kategoriler: H1-H5 | Dil: Ingilizce (referanslar), Turkce (anotasyon)
- Olusturma modu: {mode}

### Kategori Dagilimi
| Kod | Kategori | Ornek |
|-----|----------|-------|
| H1 | Tamamen Var Olmayan Referans | {cat.get('H1',0)} |
| H2 | Metadata Halusinasyonu | {cat.get('H2',0)} |
| H3 | Semantik Uyumsuzluk | {cat.get('H3',0)} |
| H4 | Kronolojik Halusinasyon | {cat.get('H4',0)} |
| H5 | Dogru Referans (Negatif) | {cat.get('H5',0)} |
| | **Toplam** | **{len(dataset)}** |

### Sinif Dengesi
- Pozitif (halusinasyon var): {pos} (%{100*pos//max(len(dataset),1)})
- Negatif (halusinasyon yok): {neg} (%{100*neg//max(len(dataset),1)})

### Zorluk Dagilimi
- Kolay: {diff.get('kolay',0)} | Orta: {diff.get('orta',0)} | Zor: {diff.get('zor',0)}

### Kaynak Veriler
- Kaynaklar: CrossRef (api.crossref.org), OpenAlex (api.openalex.org), sentetik uretim
- Lisans: CrossRef/OpenAlex acik metadata; sentetik ornekler proje kapsaminda uretildi
- Anonimlesme: Yalnizca kamuya acik akademik metadata; kisisel veri yok

### Anotasyon
- Yontem: Construction'dan-bilinen ground-truth + ELLE dogrulama (annotation_tool.py)
- YZ otomatik etiketlemesi ground-truth olarak KULLANILMAMISTIR
- Dogrulanmis ornek sayisi: {sum(1 for e in dataset if e.get('verified'))}/{len(dataset)}

### Ornek Girdi (JSON)
```json
{json.dumps(dataset[0], ensure_ascii=False, indent=2) if dataset else '{}'}
```
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(card)


def main():
    load_env()  # .env -> os.environ (CONTACT_EMAIL, OPENALEX_API_KEY)
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="Sadece seed makaleleri kullan (internet gerekmez)")
    ap.add_argument("--out", default="data/benchmark/benchmark.json")
    ap.add_argument("--card", default="data/benchmark/DATA_CARD.md")
    ap.add_argument("--mailto", default=os.getenv("CONTACT_EMAIL", "student@itu.edu.tr"))
    ap.add_argument("--n-per-cat", type=int, default=None,
                    help="Her kategoride esit ornek (orn. 6). Verilmezse Tablo 3 hedefleri (300 toplam).")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    if args.offline:
        real = real_papers_from_seeds()
        mode = "offline (seeds)"
    else:
        target = sum(gen.CATEGORY_TARGETS.values())
        real = real_papers_from_apis(args.mailto, target)
        if not real:
            print("[!] API'den makale cekilemedi; seed listesine geri donuluyor.")
            real = real_papers_from_seeds()
            mode = "offline-fallback (seeds)"
        else:
            mode = f"online (CrossRef+OpenAlex, {len(real)} gercek makale)"

    if args.n_per_cat:
        n_per_cat = {k: args.n_per_cat for k in ["H1", "H2", "H3", "H4", "H5"]}
    else:
        n_per_cat = dict(gen.CATEGORY_TARGETS)

    dataset = build(real, n_per_cat, rng)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    write_data_card(dataset, args.card, mode)
    print(f"[+] {len(dataset)} ornek yazildi -> {args.out}")
    print(f"[+] Data card -> {args.card}")
    print(f"[i] Mod: {mode}")
    print(f"[i] Gercek makale havuzu: {len(real)} | Sonraki adim: annotation_tool.py ile dogrula")


if __name__ == "__main__":
    main()
