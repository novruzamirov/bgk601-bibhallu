#!/usr/bin/env bash
# Tum modelleri benchmark uzerinde calistir (Ollama + API anahtarlari)
set -e
set -a; source .env 2>/dev/null || true; set +a
python -m src.evaluation.run_eval --config config/config.yaml \
    --benchmark data/benchmark/benchmark.json --runs 3
