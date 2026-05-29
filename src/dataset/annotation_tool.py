"""
annotation_tool.py -- Elle anotasyon / dogrulama araci (CLI).

Proje rubrigi: "Benchmark veri kumesinin anotasyonu tamamen ogrenci tarafindan
yapilmalidir; YZ otomatik etiketlemesi ground-truth olarak kullanilamaz."

Bu arac, build_dataset.py'nin urettigi her ornegi tek tek gosterir; ogrenci
etiketi ONAYLAR (verified=true), gerekirse DUZELTIR veya ornegi ATAR. Boylece
nihai ground-truth bir insan denetiminden gecmis olur.

Kullanim:
  python -m src.dataset.annotation_tool --in data/benchmark/benchmark.json
Komutlar (her ornekte):
  [Enter] onayla   d) etiketi degistir   z) zorlugu degistir
  x) ornegi sil    s) kaydet-cik         q) kaydetmeden cik
"""
from __future__ import annotations

import argparse
import json


def show(e):
    gt = e["beklenen_cevap"]
    print("\n" + "=" * 70)
    print(f"id={e['id']}  kategori={e['kategori']}  zorluk={e['zorluk']}  "
          f"verified={e.get('verified')}")
    print(f"GIRDI : {e['girdi']}")
    if e.get("baglam"):
        print(f"BAGLAM: {e['baglam']}")
    print(f"ETIKET: hallucination={gt['hallucination']}  type={gt['type']}")
    print(f"GEREKCE: {gt['reason']}")
    print("=" * 70)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--start", type=int, default=0, help="Bu indeksten devam et")
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8") as f:
        data = json.load(f)

    i = args.start
    while i < len(data):
        e = data[i]
        show(e)
        cmd = input(f"[{i+1}/{len(data)}] Enter=onayla d=etiket z=zorluk "
                    f"x=sil s=kaydet-cik q=cik > ").strip().lower()
        if cmd == "":
            e["verified"] = True
            i += 1
        elif cmd == "d":
            val = input("  hallucination (t/f): ").strip().lower()
            e["beklenen_cevap"]["hallucination"] = val in ("t", "true", "1", "e")
            typ = input("  type (H1-H5/none): ").strip()
            if typ:
                e["beklenen_cevap"]["type"] = typ
            e["verified"] = True
            i += 1
        elif cmd == "z":
            z = input("  zorluk (kolay/orta/zor): ").strip()
            if z in ("kolay", "orta", "zor"):
                e["zorluk"] = z
        elif cmd == "x":
            data.pop(i)
        elif cmd in ("s", "q"):
            break

    if cmd != "q":
        with open(args.inp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        verified = sum(1 for e in data if e.get("verified"))
        print(f"\n[+] Kaydedildi. Dogrulanmis: {verified}/{len(data)}")
    else:
        print("\n[i] Kaydedilmeden cikildi.")


if __name__ == "__main__":
    main()
