"""
rag_pipeline.py -- RAG ablasyon calistiricisi (Bolum 3.2 "Ablasyon calismasi").

Acik kaynak modelleri benchmark uzerinde HEM RAG ile HEM RAG olmadan calistirir;
ΔF1, ΔPrecision, ΔRecall hesaplar (hedef: ΔF1 >= +0.05).

Kullanim:
  # Gercek RAG (once build_index.py calistirilmali):
  python -m src.rag.rag_pipeline --config config/config.yaml \
      --benchmark data/benchmark/benchmark.json --runs 3

  # Offline pipeline testi (mock model + mock retriever):
  python -m src.rag.rag_pipeline --config config/config.yaml \
      --benchmark data/benchmark/sample_benchmark.json --mock --runs 3
"""
from __future__ import annotations

import argparse
import json
import os
import random

import yaml

from ..dotenv_loader import load_env
from ..models.factory import build_model
from ..evaluation import prompts
from ..evaluation.eval_framework import BenchmarkEvaluator, save_results


class MockRetriever:
    """Offline test icin sahte retriever: kategoriden bagimsiz jenerik baglam."""
    def __init__(self, boost: float = 0.0):
        self.boost = boost

    def __call__(self, reference: str) -> str:
        return ("[1] (benzerlik=0.71) Ilgili gercek kayit ozeti (mock). "
                "[2] (benzerlik=0.66) Baska bir aday kayit (mock).")


def _slug(s):
    return "".join(c if c.isalnum() else "_" for c in s).strip("_").lower()


def run_ablation(spec, benchmark, retriever, runs, outdir, system_prompt):
    # RAG'siz
    m1 = build_model(spec)
    ev1 = BenchmarkEvaluator(m1, benchmark, system_prompt=system_prompt,
                             cost_per_1k_tokens=spec.get("cost_per_1k_tokens", 0.0))
    r_no = ev1.run(n_runs=runs, verbose=False)
    # RAG'li
    m2 = build_model(spec)
    ev2 = BenchmarkEvaluator(m2, benchmark, system_prompt=system_prompt,
                             retriever=retriever,
                             cost_per_1k_tokens=spec.get("cost_per_1k_tokens", 0.0))
    r_yes = ev2.run(n_runs=runs, verbose=False)

    save_results(r_no, os.path.join(outdir, _slug(spec["name"]) + "_norag.json"))
    save_results(r_yes, os.path.join(outdir, _slug(spec["name"]) + "_rag.json"))

    delta = {
        "model": spec["name"],
        "f1_norag": round(r_no["binary"]["f1"], 3),
        "f1_rag": round(r_yes["binary"]["f1"], 3),
        "delta_f1": round(r_yes["binary"]["f1"] - r_no["binary"]["f1"], 3),
        "delta_precision": round(r_yes["binary"]["precision"] - r_no["binary"]["precision"], 3),
        "delta_recall": round(r_yes["binary"]["recall"] - r_no["binary"]["recall"], 3),
        "target_met": (r_yes["binary"]["f1"] - r_no["binary"]["f1"]) >= 0.05,
    }
    return delta


def main():
    load_env()  # .env -> os.environ (API anahtarlari)
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--benchmark", default="data/benchmark/benchmark.json")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(args.benchmark, encoding="utf-8") as f:
        benchmark = json.load(f)

    apply_kinds = cfg.get("rag", {}).get("apply_to_kinds", ["open"])

    # Retriever sec
    if args.mock:
        retriever = MockRetriever()
    else:
        from .retriever import ChromaRetriever
        rcfg = cfg["rag"]
        retriever = ChromaRetriever(rcfg["chroma_dir"], rcfg["embedding_model"],
                                    top_k=rcfg.get("top_k", 4))

    os.makedirs(args.outdir, exist_ok=True)
    deltas = []
    for i, spec in enumerate(cfg["models"]):
        if spec.get("kind") not in apply_kinds:
            continue
        s = spec
        if args.mock:
            # RAG, acik kaynak modelin dogrulugunu biraz artirsin (test sinyali)
            s = {**spec, "provider": "mock",
                 "accuracy": min(0.99, spec.get("mock_accuracy", 0.72)), "seed": i}
        print(f"\n=== RAG ablasyonu: {spec['name']} ===")
        # RAG'li kosu icin mock dogrulugu hafifce yukselt (sentetik iyilesme)
        if args.mock:
            d = _mock_ablation(spec, i, benchmark, retriever, args.runs, args.outdir)
        else:
            d = run_ablation(s, benchmark, retriever, args.runs, args.outdir,
                             prompts.SYSTEM_PROMPT_BASE)
        deltas.append(d)
        print(f"  F1: {d['f1_norag']} -> {d['f1_rag']}  (ΔF1={d['delta_f1']:+.3f}, "
              f"hedef {'KARSILANDI' if d['target_met'] else 'karsilanmadi'})")

    with open(os.path.join(args.outdir, "rag_ablation.json"), "w", encoding="utf-8") as f:
        json.dump(deltas, f, ensure_ascii=False, indent=2)
    print(f"\n[+] RAG ablasyon ozeti -> {os.path.join(args.outdir, 'rag_ablation.json')}")


def _mock_ablation(spec, i, benchmark, retriever, runs, outdir):
    """Mock modunda RAG'in olcumlenebilir bir iyilesme yarattigini simule eder."""
    base_acc = spec.get("mock_accuracy", 0.72)
    no = build_model({**spec, "provider": "mock", "accuracy": base_acc, "seed": i})
    yes = build_model({**spec, "provider": "mock",
                       "accuracy": min(0.99, base_acc + 0.08), "seed": i + 100})
    from ..evaluation.eval_framework import BenchmarkEvaluator as BE
    r_no = BE(no, benchmark).run(n_runs=runs, verbose=False)
    r_yes = BE(yes, benchmark).run(n_runs=runs, verbose=False)
    save_results(r_no, os.path.join(outdir, _slug(spec["name"]) + "_norag.json"))
    save_results(r_yes, os.path.join(outdir, _slug(spec["name"]) + "_rag.json"))
    return {
        "model": spec["name"],
        "f1_norag": round(r_no["binary"]["f1"], 3),
        "f1_rag": round(r_yes["binary"]["f1"], 3),
        "delta_f1": round(r_yes["binary"]["f1"] - r_no["binary"]["f1"], 3),
        "delta_precision": round(r_yes["binary"]["precision"] - r_no["binary"]["precision"], 3),
        "delta_recall": round(r_yes["binary"]["recall"] - r_no["binary"]["recall"], 3),
        "target_met": (r_yes["binary"]["f1"] - r_no["binary"]["f1"]) >= 0.05,
        "_note": "MOCK ablasyon -- yalnizca pipeline testi, gercek sonuc degildir.",
    }


if __name__ == "__main__":
    main()
