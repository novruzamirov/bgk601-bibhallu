"""
make_plots.py -- results/ ciktilarindan rapor/sunum gorselleri uretir.

Uretilen grafikler (results/figures/):
  - f1_comparison.png        : model bazinda F1 + bootstrap %95 CI hata cubuklari
  - category_f1_heatmap.png  : model x kategori (H1-H5) F1 isi haritasi
  - cost_performance.png     : maliyet-basarim dengesi (scatter)
  - rag_ablation.png         : RAG'li/RAG'siz F1 (varsa)

Kullanim: python -m src.analysis.make_plots --results results
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def _load(results_dir, config_path="config/config.yaml"):
    summary_path = os.path.join(results_dir, "summary.json")
    summary = json.load(open(summary_path, encoding="utf-8")) if os.path.exists(summary_path) else {}
    # Yalnizca config'te tanimli modelleri grafiklere al; eski / mock JSON'lari
    # filtrele (orn. smoke testten kalma gemini, claude vb.).
    allowed = None
    if os.path.exists(config_path):
        try:
            import yaml
            cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
            allowed = {m["name"] for m in cfg.get("models", [])}
        except Exception:
            allowed = None
    per_model = {}
    for p in glob.glob(os.path.join(results_dir, "*.json")):
        base = os.path.basename(p)
        if base in ("summary.json", "rag_ablation.json"):
            continue
        if base.endswith("_rag.json") or base.endswith("_norag.json"):
            continue
        d = json.load(open(p, encoding="utf-8"))
        if "model" not in d or "binary" not in d:
            continue
        if allowed is not None and d["model"] not in allowed:
            continue
        per_model[d["model"]] = d
    return summary, per_model


def plot_all(results_dir: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figdir = os.path.join(results_dir, "figures")
    os.makedirs(figdir, exist_ok=True)
    summary, per_model = _load(results_dir)
    if not per_model:
        print("[!] results/ icinde model ciktisi yok. Once run_eval calistirin.")
        return

    names = list(per_model.keys())

    # 1) F1 + CI
    f1 = [per_model[n]["binary"]["f1"] for n in names]
    lo = [per_model[n]["f1_ci"]["ci_low"] for n in names]
    hi = [per_model[n]["f1_ci"]["ci_high"] for n in names]
    err_low = [f - l for f, l in zip(f1, lo)]
    err_high = [h - f for f, h in zip(f1, hi)]
    plt.figure(figsize=(8, 5))
    plt.bar(names, f1, yerr=[err_low, err_high], capsize=6, color="#3b6ea5")
    plt.ylabel("F1 (halusinasyon tespiti)")
    plt.title("Model Bazinda F1 (%95 bootstrap GA)")
    plt.ylim(0, 1)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(figdir, "f1_comparison.png"), dpi=150)
    plt.close()

    # 2) Kategori F1 isi haritasi
    cats = ["H1", "H2", "H3", "H4", "H5"]
    mat = [[per_model[n]["category_f1"].get(c, 0.0) for c in cats] for n in names]
    plt.figure(figsize=(7, 0.8 * len(names) + 2))
    im = plt.imshow(mat, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
    plt.colorbar(im, label="F1")
    plt.xticks(range(len(cats)), cats)
    plt.yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(cats)):
            plt.text(j, i, f"{mat[i][j]:.2f}", ha="center", va="center", fontsize=8)
    plt.title("Kategori Bazinda F1 (model x H1-H5)")
    plt.tight_layout()
    plt.savefig(os.path.join(figdir, "category_f1_heatmap.png"), dpi=150)
    plt.close()

    # 3) Maliyet-basarim
    plt.figure(figsize=(8, 5))
    for n in names:
        x = per_model[n]["cost_per_correct_usd"]
        y = per_model[n]["binary"]["f1"]
        plt.scatter(x, y, s=80)
        plt.annotate(n, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=8)
    plt.xlabel("Dogru tespit basina maliyet ($)")
    plt.ylabel("F1")
    plt.title("Maliyet-Basarim Dengesi")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(figdir, "cost_performance.png"), dpi=150)
    plt.close()

    # 4) RAG ablasyonu (varsa)
    abl_path = os.path.join(results_dir, "rag_ablation.json")
    if os.path.exists(abl_path):
        abl = json.load(open(abl_path, encoding="utf-8"))
        if abl:
            ms = [a["model"] for a in abl]
            no = [a["f1_norag"] for a in abl]
            yes = [a["f1_rag"] for a in abl]
            x = range(len(ms))
            w = 0.35
            plt.figure(figsize=(8, 5))
            plt.bar([i - w/2 for i in x], no, w, label="RAG'siz", color="#9aa0a6")
            plt.bar([i + w/2 for i in x], yes, w, label="RAG'li", color="#2e7d32")
            plt.xticks(list(x), ms, rotation=15, ha="right")
            plt.ylabel("F1")
            plt.ylim(0, 1)
            plt.title("RAG Ablasyonu: RAG'li vs RAG'siz")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(figdir, "rag_ablation.png"), dpi=150)
            plt.close()

    print(f"[+] Grafikler yazildi -> {figdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    args = ap.parse_args()
    plot_all(args.results)


if __name__ == "__main__":
    main()
