#!/usr/bin/env bash
# Grafikler + hata analizi
set -e
python -m src.analysis.make_plots --results results
for f in results/gpt_4o.json results/gemini_1_5_flash.json results/llama_3_1_8b.json results/qwen2_5_7b.json; do
  [ -f "$f" ] && python -m src.analysis.error_analysis --result "$f" --n 8 --out "${f%.json}_errors.json"
done
