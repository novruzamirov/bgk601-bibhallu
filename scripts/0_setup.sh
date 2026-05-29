#!/usr/bin/env bash
# Ortam kurulumu: bagimliliklar + Ollama modelleri
set -e
echo "[1/3] Python bagimliliklari kuruluyor..."
pip install -r requirements.txt
echo "[2/3] Ollama modelleri cekiliyor (Ollama kurulu olmali: https://ollama.com)..."
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
echo "[3/3] .env hazirligi"
[ -f .env ] || cp .env.example .env
echo "Bitti. .env dosyasina API anahtarlarinizi girin (GOOGLE_API_KEY ucretsiz)."
