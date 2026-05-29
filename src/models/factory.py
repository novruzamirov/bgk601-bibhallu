"""
factory.py -- config'teki tanima gore dogru ModelClient'i uretir.

config/config.yaml -> models: listesindeki her giris:
    - name: "Claude Sonnet 4.5"
      provider: anthropic        # openai | anthropic | gemini | ollama | mock
      model: "claude-sonnet-4-5"
      kind: closed               # closed | open  (raporlama/gruplandirma icin)
"""
from __future__ import annotations

import random
import time
from typing import Dict, Any

from .base import ModelClient


class MockClient(ModelClient):
    """
    SADECE TEST/SMOKE amaclidir. Gercek model degildir; ground-truth'u taklit eden
    ama gurultu/hata ekleyen bir test-cift'idir. ASLA gercek deney sonucu olarak
    raporlanmamalidir. Pipeline'i (metrik, istatistik, grafik) internet/GPU olmadan
    uctan uca dogrulamak icindir.
    """
    def __init__(self, name: str = "MockModel", accuracy: float = 0.8,
                 seed: int = 0, latency_ms: float = 50.0):
        super().__init__(name=name)
        self.accuracy = accuracy
        self.rng = random.Random(seed)
        self.base_latency = latency_ms
        self._gt_hint = None  # eval harness, dogru cevabi ipucu olarak verir

    def set_gt_hint(self, hallucination: bool, htype: str):
        self._gt_hint = (hallucination, htype)

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        import json
        time.sleep(0.0)
        self.last_latency_ms = self.base_latency * (0.8 + 0.4 * self.rng.random())
        self.last_token_count = self.rng.randint(80, 200)
        if self._gt_hint is None:
            h, t = self.rng.random() < 0.5, self.rng.choice(["H1", "none"])
        else:
            h, t = self._gt_hint
            if self.rng.random() > self.accuracy:   # hata enjekte et
                h = not h
                t = "none" if not h else self.rng.choice(["H1", "H2", "H3", "H4"])
        return json.dumps({"hallucination": h, "confidence": round(self.rng.random(), 2),
                           "type": t if h else "none", "reason": "mock"})


def build_model(spec: Dict[str, Any], temperature: float = 0.0) -> ModelClient:
    provider = spec["provider"].lower()
    name = spec["name"]
    model = spec.get("model", "")
    if provider == "ollama":
        from .ollama_client import OllamaClient
        return OllamaClient(name=name, model=model, temperature=temperature,
                            num_ctx=spec.get("num_ctx", 8192))
    if provider == "openai":
        from .api_clients import OpenAIClient
        return OpenAIClient(name=name, model=model, temperature=temperature)
    if provider == "anthropic":
        from .api_clients import AnthropicClient
        return AnthropicClient(name=name, model=model, temperature=temperature)
    if provider == "gemini":
        from .api_clients import GeminiClient
        return GeminiClient(name=name, model=model, temperature=temperature)
    if provider == "mock":
        return MockClient(name=name, accuracy=spec.get("accuracy", 0.8),
                          seed=spec.get("seed", 0))
    raise ValueError(f"Bilinmeyen provider: {provider}")
