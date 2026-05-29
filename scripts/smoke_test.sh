#!/usr/bin/env bash
# Internet/GPU/anahtar GEREKMEZ: tum pipeline'i mock ile uctan uca dogrular
set -e
echo "== Birim testler =="
python tests/test_metrics.py
echo "== Offline ornek veri kumesi =="
python -m src.dataset.build_dataset --offline --n-per-cat 6 --out data/benchmark/sample_benchmark.json
echo "== Mock degerlendirme =="
python -m src.evaluation.run_eval --config config/config.yaml --benchmark data/benchmark/sample_benchmark.json --mock --runs 3
echo "== Mock RAG ablasyonu =="
python -m src.rag.rag_pipeline --config config/config.yaml --benchmark data/benchmark/sample_benchmark.json --mock --runs 3
echo "== Grafikler =="
python -m src.analysis.make_plots --results results
echo "SMOKE TEST TAMAM."
