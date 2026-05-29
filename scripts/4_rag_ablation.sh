#!/usr/bin/env bash
# RAG'li vs RAG'siz ablasyon (acik kaynak modeller)
set -e
set -a; source .env 2>/dev/null || true; set +a
python -m src.rag.rag_pipeline --config config/config.yaml \
    --benchmark data/benchmark/benchmark.json --runs 3
