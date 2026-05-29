"""
statistics.py -- Istatistiksel anlamlilik (final raporu gereksinimi).

- bootstrap_ci_f1   : F1 icin yuzde-bootstrap guven araligi
- mcnemar_test      : iki modelin esli (ayni ornekler) dogru/yanlis kararlarinda
                      anlamli fark var mi? (McNemar testi)
"""
from __future__ import annotations

import random
from typing import List, Sequence, Tuple, Dict

from .metrics import binary_metrics


def bootstrap_ci_f1(y_true: Sequence[int], y_pred: Sequence[int],
                    n_boot: int = 2000, alpha: float = 0.05,
                    seed: int = 42) -> Dict[str, float]:
    """F1 icin (1-alpha) yuzdelik bootstrap guven araligi."""
    rng = random.Random(seed)
    n = len(y_true)
    idx = list(range(n))
    stats = []
    for _ in range(n_boot):
        sample = [rng.choice(idx) for _ in range(n)]
        yt = [y_true[i] for i in sample]
        yp = [y_pred[i] for i in sample]
        stats.append(binary_metrics(yt, yp)["f1"])
    stats.sort()
    lo = stats[int((alpha / 2) * n_boot)]
    hi = stats[int((1 - alpha / 2) * n_boot) - 1]
    point = binary_metrics(y_true, y_pred)["f1"]
    return {"f1": point, "ci_low": lo, "ci_high": hi, "n_boot": n_boot}


def mcnemar_test(correct_a: Sequence[int], correct_b: Sequence[int]
                 ) -> Dict[str, float]:
    """
    correct_a[i], correct_b[i] in {0,1}: i'inci ornekte ilgili model dogru mu?
    b = A dogru & B yanlis;  c = A yanlis & B dogru.
    Sureklilik duzeltmeli McNemar chi-kare (df=1). Kucuk n icin de makuldur.
    """
    b = sum(1 for a, bb in zip(correct_a, correct_b) if a == 1 and bb == 0)
    c = sum(1 for a, bb in zip(correct_a, correct_b) if a == 0 and bb == 1)
    if b + c == 0:
        return {"b": b, "c": c, "chi2": 0.0, "p_value": 1.0}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p = _chi2_sf_df1(chi2)
    return {"b": b, "c": c, "chi2": chi2, "p_value": p}


def _chi2_sf_df1(x: float) -> float:
    """df=1 ki-kare hayatta kalma fonksiyonu (SciPy'siz). p = erfc(sqrt(x/2))."""
    if x <= 0:
        return 1.0
    import math
    return math.erfc(math.sqrt(x / 2.0))
