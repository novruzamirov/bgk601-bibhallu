"""
run_eval.py -- config'teki tum modelleri benchmark uzerinde calistirir.

Kullanim:
  # Offline pipeline testi (internet/GPU gerekmez, mock modeller):
  python -m src.evaluation.run_eval --config config/config.yaml \
      --benchmark data/benchmark/sample_benchmark.json --mock --runs 3

  # Gercek calistirma (Ollama + API anahtarlari hazirken):
  python -m src.evaluation.run_eval --config config/config.yaml \
      --benchmark data/benchmark/benchmark.json --runs 3

Cikti: her model icin results/<model>.json + results/summary.json (karsilastirma).
"""
from __future__ import annotations

import argparse
import json
import os

import yaml

from ..dotenv_loader import load_env
from ..models.factory import build_model
from . import prompts
from .eval_framework import BenchmarkEvaluator, save_results
from .statistics import mcnemar_test


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    load_env()  # .env -> os.environ (API anahtarlari)
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--benchmark", default="data/benchmark/benchmark.json")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--mock", action="store_true",
                    help="Tum modelleri MockClient ile degistir (offline pipeline testi)")
    ap.add_argument("--cot", action="store_true",
                    help="Chain-of-thought sistem promptu kullan")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    with open(args.benchmark, encoding="utf-8") as f:
        benchmark = json.load(f)

    system_prompt = prompts.SYSTEM_PROMPT_COT if args.cot else prompts.SYSTEM_PROMPT_BASE
    os.makedirs(args.outdir, exist_ok=True)

    summary = []
    per_model_results = {}
    for i, spec in enumerate(cfg["models"]):
        if args.mock:
            spec = {**spec, "provider": "mock", "accuracy": spec.get("mock_accuracy", 0.8),
                    "seed": i}
        print(f"\n=== {spec['name']} ({spec['provider']}) ===")
        try:
            model = build_model(spec)
        except Exception as e:
            print(f"  [!] Model olusturulamadi: {e}  (atlaniyor)")
            continue
        ev = BenchmarkEvaluator(
            model=model, benchmark=benchmark, system_prompt=system_prompt,
            cost_per_1k_tokens=spec.get("cost_per_1k_tokens", 0.0))
        res = ev.run(n_runs=args.runs)
        per_model_results[spec["name"]] = res
        save_results(res, os.path.join(args.outdir, _slug(spec["name"]) + ".json"))
        summary.append({
            "model": res["model"], "kind": spec.get("kind", "?"),
            "accuracy": round(res["binary"]["accuracy"], 3),
            "precision": round(res["binary"]["precision"], 3),
            "recall": round(res["binary"]["recall"], 3),
            "f1": round(res["binary"]["f1"], 3),
            "f1_ci": [round(res["f1_ci"]["ci_low"], 3), round(res["f1_ci"]["ci_high"], 3)],
            "macro_cat_f1": round(res["macro_category_f1"], 3),
            "fleiss_kappa": round(res["fleiss_kappa"], 3),
            "p50_ms": round(res["latency_p50_ms"], 1),
            "p95_ms": round(res["latency_p95_ms"], 1),
            "cost_per_correct_usd": round(res["cost_per_correct_usd"], 5),
            "parse_fail_rate": round(res["parse_fail_rate"], 3),
            "overall": round(res["weighted_overall_score"], 3),
        })
        print(f"  F1={summary[-1]['f1']}  acc={summary[-1]['accuracy']}  "
              f"overall={summary[-1]['overall']}")

    # Siralama + McNemar (en iyi iki modeli karsilastir)
    summary.sort(key=lambda r: r["overall"], reverse=True)
    for rank, row in enumerate(summary, 1):
        row["rank"] = rank
    pairwise = []
    names = list(per_model_results.keys())
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            ra, rb = per_model_results[names[a]], per_model_results[names[b]]
            ca = [1 if t == p else 0 for t, p in zip(ra["_y_true"], ra["_y_pred"])]
            cb = [1 if t == p else 0 for t, p in zip(rb["_y_true"], rb["_y_pred"])]
            if len(ca) == len(cb):
                mc = mcnemar_test(ca, cb)
                pairwise.append({"model_a": names[a], "model_b": names[b], **mc})

    with open(os.path.join(args.outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"ranking": summary, "mcnemar_pairwise": pairwise}, f,
                  ensure_ascii=False, indent=2)
    print("\n=== SIRALAMA ===")
    for row in summary:
        print(f"  {row['rank']}. {row['model']:28s} F1={row['f1']:.3f} "
              f"overall={row['overall']:.3f}")
    print(f"\n[+] Ozet -> {os.path.join(args.outdir, 'summary.json')}")


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s).strip("_").lower()


if __name__ == "__main__":
    main()
