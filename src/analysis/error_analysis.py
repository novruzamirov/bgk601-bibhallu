"""
error_analysis.py -- Hata analizi (final raporu gereksinimi).

results/<model>.json kayitlarindan:
  - Modelin yanildigi ornek turleri (kategori x zorluk kirilimi)
  - En cok karistirilan kategoriler (confusion)
  - Nitel inceleme icin 5-10 ornek (yanlis siniflandirilan, gerekceleriyle)

Kullanim:
  python -m src.analysis.error_analysis --result results/llama_3_1_8b.json --n 8
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict


def analyze(result: dict, n_cases: int = 8):
    examples = result["examples"]
    wrong = []
    by_cat = defaultdict(lambda: {"total": 0, "wrong": 0})
    by_diff = defaultdict(lambda: {"total": 0, "wrong": 0})
    confusion = Counter()  # (gercek_tip -> tahmin_tip)

    for e in examples:
        cat = e["kategori"]
        gt_h = e["gt_hallucination"]
        pr_h = e["majority_hallucination"]
        by_cat[cat]["total"] += 1
        by_diff[e["zorluk"]]["total"] += 1
        is_wrong = (gt_h != pr_h)
        if is_wrong:
            by_cat[cat]["wrong"] += 1
            by_diff[e["zorluk"]]["wrong"] += 1
            confusion[(e["gt_type"], e["majority_type"])] += 1
            wrong.append(e)

    print(f"\n=== Hata Analizi: {result['model']} ===")
    print(f"Toplam ornek: {len(examples)} | Yanlis: {len(wrong)} "
          f"(%{100*len(wrong)//max(len(examples),1)})")

    print("\nKategori bazinda hata orani:")
    for c in ["H1", "H2", "H3", "H4", "H5"]:
        d = by_cat[c]
        if d["total"]:
            print(f"  {c}: {d['wrong']}/{d['total']} "
                  f"(%{100*d['wrong']//d['total']})")

    print("\nZorluk bazinda hata orani:")
    for z in ["kolay", "orta", "zor"]:
        d = by_diff[z]
        if d["total"]:
            print(f"  {z}: {d['wrong']}/{d['total']} (%{100*d['wrong']//d['total']})")

    print("\nEn sik karisiklik (gercek_tip -> tahmin_tip):")
    for (gt, pr), cnt in confusion.most_common(6):
        print(f"  {gt} -> {pr}: {cnt}")

    print(f"\nNitel inceleme icin {min(n_cases, len(wrong))} yanlis ornek:")
    for e in wrong[:n_cases]:
        last = e["runs"][-1] if e["runs"] else {}
        print(f"  [id {e['id']} | {e['kategori']}/{e['zorluk']}] "
              f"gercek={e['gt_hallucination']} tahmin={e['majority_hallucination']} "
              f"| model gerekce: {str(last.get('reason',''))[:90]}")

    return {"n_wrong": len(wrong),
            "by_category": {c: dict(by_cat[c]) for c in by_cat},
            "by_difficulty": {z: dict(by_diff[z]) for z in by_diff},
            "confusion": {f"{k[0]}->{k[1]}": v for k, v in confusion.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = json.load(open(args.result, encoding="utf-8"))
    summary = analyze(result, args.n)
    if args.out:
        json.dump(summary, open(args.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\n[+] Ozet -> {args.out}")


if __name__ == "__main__":
    main()
