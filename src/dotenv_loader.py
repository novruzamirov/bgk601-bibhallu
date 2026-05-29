"""
dotenv_loader.py -- Sifir bagimlilikli .env yukleyici.

Tum CLI giris noktalari (run_eval, rag_pipeline, build_dataset) baslangicta
load_env() cagirir; boylece .env icindeki anahtarlar (OPENAI_API_KEY vb.) otomatik
olarak os.environ'a yuklenir. Kullanicinin elle 'export' yapmasina gerek kalmaz.

Onceden tanimli ortam degiskenleri (gercek export'lar) KORUNUR (uzerine yazilmaz).
"""
from __future__ import annotations

import os


def load_env(path: str = ".env") -> bool:
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
        return True
    except OSError:
        return False
