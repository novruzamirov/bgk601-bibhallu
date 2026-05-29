"""
build_corpus.py -- RAG bilgi tabani korpusunu toplar (data/raw/papers.json).

RAG'in mantigi: bir referans dizgesi sorgu olarak verilir; bilgi tabaninda
buna yakin gercek bir kayit BULUNAMAZSA, referansin uydurma (H1) olma olasiligi
yukselir. Bu nedenle korpus, gercek akademik makalelerden olusmalidir.

Kaynaklar:
  - CrossRef (anahtar GEREKMEZ): konu bazli yuzlerce gercek makale metadata'si
  - OpenAlex (anahtar varsa): ayni makalelere abstract ekler (daha zengin retrieval)

Kullanim:
  python -m src.rag.build_corpus --out data/raw/papers.json \
      --mailto novruz.amirov@itu.edu.tr --n 400
"""
from __future__ import annotations

import argparse
import json
import os
import re

from ..dotenv_loader import load_env
from ..dataset.crossref_client import CrossRefClient
from ..dataset.openalex_client import OpenAlexClient

TOPICS = [
    "intrusion detection deep learning", "malware classification machine learning",
    "adversarial machine learning", "vulnerability assessment CVSS",
    "phishing detection", "network anomaly detection", "side channel attack",
    "ransomware detection", "threat intelligence NLP", "binary code analysis",
    "intrusion prevention", "botnet detection", "spam filtering",
    "privacy preserving machine learning", "federated learning security",
    "explainable AI security", "large language model security",
    "transformer attention", "neural network robustness", "data poisoning attack",
]

_JATS = re.compile(r"<[^>]+>")


def _clean_abstract(s: str) -> str:
    return _JATS.sub("", s or "").strip()


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw/papers.json")
    ap.add_argument("--mailto", default=os.getenv("CONTACT_EMAIL", "student@itu.edu.tr"))
    ap.add_argument("--n", type=int, default=400, help="hedef makale sayisi")
    args = ap.parse_args()

    cr = CrossRefClient(mailto=args.mailto)
    rows_per_topic = max(5, args.n // len(TOPICS) + 5)

    papers, seen = [], set()
    for topic in TOPICS:
        for item in cr.search(topic, rows=rows_per_topic):
            m = cr.normalize(item)
            key = (m.get("title") or "").strip().lower()
            if not key or key in seen or not m.get("year"):
                continue
            seen.add(key)
            m["abstract"] = _clean_abstract(
                (item.get("abstract") or "")) if item.get("abstract") else ""
            m["kaynak"] = "crossref"
            papers.append(m)
        print(f"  [{topic}] -> toplam {len(papers)} makale")
        if len(papers) >= args.n:
            break

    # OpenAlex anahtari varsa abstract'lari zenginlestir
    if os.getenv("OPENALEX_API_KEY"):
        oa = OpenAlexClient(mailto=args.mailto)
        enriched = 0
        for p in papers:
            if p.get("abstract"):
                continue
            hits = oa.search(p["title"], per_page=1, require_abstract=True)
            if hits:
                p["abstract"] = oa.normalize(hits[0]).get("abstract", "")
                enriched += 1
            if enriched >= 100:   # gunluk ucretsiz kotayi koru
                break
        print(f"  OpenAlex ile {enriched} abstract eklendi")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    n_abs = sum(1 for p in papers if p.get("abstract"))
    print(f"\n[+] {len(papers)} makale -> {args.out}  (abstract'li: {n_abs})")
    if not papers:
        print("[!] Hic makale cekilemedi (internet/CrossRef erisimini kontrol edin).")


if __name__ == "__main__":
    main()
