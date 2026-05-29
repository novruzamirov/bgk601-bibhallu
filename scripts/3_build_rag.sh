#!/usr/bin/env bash
# RAG bilgi tabani: once korpusu topla (CrossRef), sonra ChromaDB indeksini kur
set -e
set -a; source .env 2>/dev/null || true; set +a
echo "[1/2] RAG korpusu toplaniyor (CrossRef)..."
python -m src.rag.build_corpus --out data/raw/papers.json \
    --mailto "${CONTACT_EMAIL:-student@itu.edu.tr}" --n 400
echo "[2/2] ChromaDB indeksi olusturuluyor..."
python -m src.rag.build_index --papers data/raw/papers.json --chroma-dir data/chroma
