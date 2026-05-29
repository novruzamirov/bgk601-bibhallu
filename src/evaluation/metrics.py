"""
metrics.py -- Degerlendirme metrikleri.

- Ikili tespit (halusinasyon var/yok): accuracy, precision, recall, F1, MCC
- Kategori bazinda F1 (H1-H5 cok-sinifli tip tahmini)
- Agirlikli genel skor (ara rapor Tablo 2 agirliklari)
- Fleiss' kappa (3+ bagimsiz calistirmada yanit tutarliligi)

scikit-learn varsa kullanir; yoksa saf-Python geri donus uygulamasi devreye girer.
"""
from __future__ import annotations

from typing import List, Dict, Sequence
import math

try:
    from sklearn.metrics import (precision_score, recall_score, f1_score,
                                 accuracy_score, matthews_corrcoef)
    _HAS_SK = True
except Exception:  # pragma: no cover
    _HAS_SK = False


def binary_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, float]:
    """y=1 -> halusinasyon var (pozitif sinif)."""
    if _HAS_SK:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "mcc": float(matthews_corrcoef(y_true, y_pred)) if len(set(y_true)) > 1 else 0.0,
        }
    # --- saf-Python geri donus ---
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    n = max(len(y_true), 1)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denom if denom else 0.0
    return {"accuracy": (tp + tn) / n, "precision": prec, "recall": rec,
            "f1": f1, "mcc": mcc}


def per_category_f1(examples: List[dict], preds: List[dict]) -> Dict[str, float]:
    """
    Her kategori (H1-H5) icin tip tahmininin F1'i. Bir ornek icin "dogru" sayilma:
    H1-H4 -> tahmin edilen type, gercek type ile ayni; H5 -> hallucination=False.
    """
    cats = ["H1", "H2", "H3", "H4", "H5"]
    out = {}
    for c in cats:
        # one-vs-rest: bu kategoriye ait mi?
        yt, yp = [], []
        for ex, pr in zip(examples, preds):
            true_c = ex["kategori"]
            if true_c == "H5":
                pred_c = "H5" if not pr["hallucination"] else "pos"
            else:
                pred_c = pr["type"] if pr["hallucination"] else "none"
            yt.append(1 if true_c == c else 0)
            yp.append(1 if pred_c == c else 0)
        out[c] = binary_metrics(yt, yp)["f1"]
    return out


# Ara rapor Tablo 2 agirliklari (toplam = 1.0)
DEFAULT_WEIGHTS = {
    "teknik_dogruluk": 0.35,      # F1
    "alt_tur_tespiti": 0.25,      # makro kategori F1
    "yanit_tutarliligi": 0.10,    # Fleiss kappa (normalize)
    "rag_katkisi": 0.15,          # ablasyon (yoksa 0 katki)
    "gecikme": 0.05,              # hizli=iyi (normalize)
    "maliyet_etkinligi": 0.10,    # ucuz=iyi (normalize)
}


def weighted_overall_score(f1: float, macro_cat_f1: float, kappa: float,
                           rag_delta_f1: float, latency_score: float,
                           cost_score: float,
                           weights: Dict[str, float] = None) -> float:
    """Tum bilesenleri [0,1]'e normalize edip agirlikli toplar."""
    w = weights or DEFAULT_WEIGHTS
    kappa_n = max(0.0, min(1.0, kappa))           # kappa zaten ~[0,1]
    rag_n = max(0.0, min(1.0, rag_delta_f1 / 0.10))  # +0.10 deltayi tam puan say
    comp = {
        "teknik_dogruluk": f1,
        "alt_tur_tespiti": macro_cat_f1,
        "yanit_tutarliligi": kappa_n,
        "rag_katkisi": rag_n,
        "gecikme": latency_score,
        "maliyet_etkinligi": cost_score,
    }
    return sum(w[k] * comp[k] for k in w)


def fleiss_kappa(runs: List[List[int]]) -> float:
    """
    Fleiss' kappa: N ornek x R degerlendirici(=calistirma), 2 kategori (0/1).
    runs[i] = i'inci ornek icin R calistirmanin ikili kararlari listesi.
    3+ calistirma icin uygundur (Cohen's kappa yalnizca 2 degerlendiricilik).
    """
    if not runs:
        return 0.0
    R = len(runs[0])
    if R < 2:
        return 0.0
    N = len(runs)
    # her ornekte kategori sayimlari (n0, n1)
    P_i = []
    col_tot = [0, 0]
    for r in runs:
        n1 = sum(r)
        n0 = R - n1
        col_tot[0] += n0
        col_tot[1] += n1
        P_i.append((n0 * (n0 - 1) + n1 * (n1 - 1)) / (R * (R - 1)))
    P_bar = sum(P_i) / N
    p_j = [c / (N * R) for c in col_tot]
    P_e = sum(p * p for p in p_j)
    if abs(1 - P_e) < 1e-12:
        return 1.0
    return (P_bar - P_e) / (1 - P_e)
