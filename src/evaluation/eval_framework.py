"""
eval_framework.py -- Benchmark Degerlendirme Cercevesi (proje Ek C'nin genisletilmis hali).

Her ornek icin n_runs (>=3) bagimsiz calistirma yapar, cogunluk kararini alir,
ham ciktilari ve metrikleri toplar. RAG retriever verilirse baglam prompt'a eklenir.

Cikti: results dict (model bazli ozet + ornek bazli kayitlar) -> JSON'a yazilir.
"""
from __future__ import annotations

import json
import statistics as _stats
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable

from ..models.base import ModelClient, parse_prediction
from ..models.factory import MockClient
from . import prompts
from . import metrics as M
from . import statistics as S


@dataclass
class ExampleResult:
    id: int
    kategori: str
    zorluk: str
    gt_hallucination: bool
    gt_type: str
    runs: List[Dict[str, Any]] = field(default_factory=list)  # her run'in parse'i
    majority_hallucination: bool = False
    majority_type: str = "none"
    mean_latency_ms: float = 0.0
    mean_tokens: float = 0.0
    parse_fail_rate: float = 0.0


class BenchmarkEvaluator:
    def __init__(self, model: ModelClient, benchmark: List[Dict[str, Any]],
                 system_prompt: str = prompts.SYSTEM_PROMPT_BASE,
                 retriever: Optional[Callable[[str], str]] = None,
                 cost_per_1k_tokens: float = 0.0):
        self.model = model
        self.benchmark = benchmark
        self.system_prompt = system_prompt
        self.retriever = retriever          # callable(reference)->rag_context str
        self.cost_per_1k = cost_per_1k_tokens
        self.examples: List[ExampleResult] = []

    def run(self, n_runs: int = 3, verbose: bool = True) -> Dict[str, Any]:
        for k, ex in enumerate(self.benchmark):
            gt_h = ex["beklenen_cevap"]["hallucination"]
            gt_t = ex["beklenen_cevap"]["type"]
            rag_ctx = self.retriever(ex["girdi"]) if self.retriever else ""
            user_prompt = prompts.build_user_prompt(
                ex["girdi"], ex.get("baglam", ""), rag_ctx)

            er = ExampleResult(id=ex["id"], kategori=ex["kategori"],
                               zorluk=ex["zorluk"], gt_hallucination=gt_h, gt_type=gt_t)
            lats, toks, parsed_runs, fails = [], [], [], 0
            for _ in range(n_runs):
                # MockClient: pipeline testi icin ground-truth ipucu ver
                if isinstance(self.model, MockClient):
                    self.model.set_gt_hint(gt_h, gt_t)
                raw = self.model.predict(self.system_prompt, user_prompt)
                pred = parse_prediction(raw)
                if not pred["parse_ok"]:
                    fails += 1
                parsed_runs.append(pred)
                lats.append(self.model.last_latency_ms)
                toks.append(self.model.last_token_count)

            # Cogunluk karari
            votes_h = sum(1 for p in parsed_runs if p["hallucination"])
            er.majority_hallucination = votes_h > n_runs / 2
            types = [p["type"] for p in parsed_runs if p["hallucination"]]
            er.majority_type = max(set(types), key=types.count) if types else "none"
            er.runs = parsed_runs
            er.mean_latency_ms = _stats.mean(lats) if lats else 0.0
            er.mean_tokens = _stats.mean(toks) if toks else 0.0
            er.parse_fail_rate = fails / max(n_runs, 1)
            self.examples.append(er)
            if verbose and (k + 1) % 25 == 0:
                print(f"  [{self.model.name}] {k+1}/{len(self.benchmark)} islendi")
        return self.aggregate()

    def aggregate(self) -> Dict[str, Any]:
        y_true = [1 if e.gt_hallucination else 0 for e in self.examples]
        y_pred = [1 if e.majority_hallucination else 0 for e in self.examples]
        bm = M.binary_metrics(y_true, y_pred)
        ci = S.bootstrap_ci_f1(y_true, y_pred)

        ex_dicts = [{"kategori": e.kategori} for e in self.examples]
        pred_dicts = [{"hallucination": e.majority_hallucination,
                       "type": e.majority_type} for e in self.examples]
        cat_f1 = M.per_category_f1(ex_dicts, pred_dicts)
        macro_cat_f1 = sum(cat_f1.values()) / len(cat_f1)

        # Tutarlilik: Fleiss kappa (run bazinda ikili kararlar)
        runs_matrix = [[1 if r["hallucination"] else 0 for r in e.runs]
                       for e in self.examples if e.runs]
        kappa = M.fleiss_kappa(runs_matrix) if runs_matrix else 0.0

        lat = sorted(e.mean_latency_ms for e in self.examples)
        p50 = lat[len(lat) // 2] if lat else 0.0
        p95 = lat[int(len(lat) * 0.95) - 1] if lat else 0.0
        total_tokens = sum(e.mean_tokens for e in self.examples)
        cost = total_tokens / 1000.0 * self.cost_per_1k
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        cost_per_correct = cost / correct if correct else 0.0

        # Normalize edilmis alt-skorlar (agirlikli genel skor icin)
        latency_score = max(0.0, 1.0 - (p50 / 5000.0))   # 5s'de 0'a duser
        cost_score = max(0.0, 1.0 - (cost_per_correct / 0.01))  # $0.01 esik
        overall = M.weighted_overall_score(
            f1=bm["f1"], macro_cat_f1=macro_cat_f1, kappa=kappa,
            rag_delta_f1=0.0, latency_score=latency_score, cost_score=cost_score)

        return {
            "model": self.model.name,
            "n_examples": len(self.examples),
            "binary": bm,
            "f1_ci": ci,
            "category_f1": cat_f1,
            "macro_category_f1": macro_cat_f1,
            "fleiss_kappa": kappa,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "mean_tokens_per_ref": total_tokens / max(len(self.examples), 1),
            "cost_usd_total": cost,
            "cost_per_correct_usd": cost_per_correct,
            "parse_fail_rate": sum(e.parse_fail_rate for e in self.examples) /
                               max(len(self.examples), 1),
            "weighted_overall_score": overall,
            "_y_true": y_true,
            "_y_pred": y_pred,
            "examples": [asdict(e) for e in self.examples],
        }


def save_results(results: Dict[str, Any], path: str) -> None:
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
