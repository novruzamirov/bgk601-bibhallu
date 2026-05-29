#!/usr/bin/env bash
# Tam 300 ornekluk veri kumesini insa et (internet + OpenAlex anahtari gerekir)
set -e
source .env 2>/dev/null || true
python -m src.dataset.build_dataset --out data/benchmark/benchmark.json \
    --mailto "${CONTACT_EMAIL:-student@itu.edu.tr}"
echo ">> Simdi elle dogrulayin: python -m src.dataset.annotation_tool --in data/benchmark/benchmark.json"
