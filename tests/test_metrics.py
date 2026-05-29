"""
test_metrics.py -- Cekirdek metrik/istatistik/ayiklama birim testleri.
Calistirma: python -m pytest tests/  (veya) python tests/test_metrics.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluation.metrics import binary_metrics, fleiss_kappa
from src.evaluation.statistics import mcnemar_test, bootstrap_ci_f1
from src.models.base import parse_prediction


def approx(a, b, tol=1e-6):
    return abs(a - b) < tol


def test_binary_perfect():
    m = binary_metrics([1, 0, 1, 0], [1, 0, 1, 0])
    assert approx(m["f1"], 1.0) and approx(m["accuracy"], 1.0)


def test_binary_known():
    # tp=2 fp=1 fn=1 tn=1 -> prec=2/3, rec=2/3, f1=2/3
    m = binary_metrics([1, 1, 0, 0, 1], [1, 0, 1, 0, 1])
    assert approx(m["precision"], 2/3) and approx(m["recall"], 2/3)
    assert approx(m["f1"], 2/3)


def test_fleiss_perfect_agreement():
    # 3 ornek, 3 calistirma, hepsi ayni -> kappa = 1
    assert approx(fleiss_kappa([[1, 1, 1], [0, 0, 0], [1, 1, 1]]), 1.0)


def test_fleiss_range():
    k = fleiss_kappa([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
    assert -1.0 <= k <= 1.0


def test_mcnemar_symmetry():
    r = mcnemar_test([1, 1, 0, 0], [1, 1, 0, 0])
    assert r["b"] == 0 and r["c"] == 0 and approx(r["p_value"], 1.0)


def test_mcnemar_pvalue_range():
    r = mcnemar_test([1, 1, 1, 0, 1, 1], [0, 0, 0, 0, 0, 0])
    assert 0.0 <= r["p_value"] <= 1.0 and r["b"] >= r["c"]


def test_bootstrap_ci_bounds():
    yt = [1, 0] * 20
    yp = [1, 0] * 20
    ci = bootstrap_ci_f1(yt, yp, n_boot=200)
    assert ci["ci_low"] <= ci["f1"] <= ci["ci_high"]


def test_parse_clean_json():
    p = parse_prediction('{"hallucination": true, "confidence": 0.9, "type": "H1", "reason": "x"}')
    assert p["parse_ok"] and p["hallucination"] and p["type"] == "H1"


def test_parse_markdown_fenced():
    raw = 'Sure!\n```json\n{"hallucination": false, "type": "none", "reason": "ok"}\n```'
    p = parse_prediction(raw)
    assert p["parse_ok"] and not p["hallucination"] and p["type"] == "none"


def test_parse_freetext_fallback():
    p = parse_prediction("This reference appears to be fabricated and does not exist. H1")
    assert p["hallucination"] and p["type"] == "H1" and not p["parse_ok"]


def test_parse_invalid_type_coerced():
    p = parse_prediction('{"hallucination": true, "type": "H9", "reason": "x"}')
    assert p["type"] == "none"  # gecersiz tip -> none


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            print(f"ERROR {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} test gecti")
    sys.exit(0 if passed == len(fns) else 1)
