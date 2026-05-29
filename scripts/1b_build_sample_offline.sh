#!/usr/bin/env bash
# Internet olmadan hizli ORNEK veri kumesi (smoke-test icin)
set -e
python -m src.dataset.build_dataset --offline --n-per-cat 6 \
    --out data/benchmark/sample_benchmark.json
