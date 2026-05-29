"""
ollama_client.py -- Yerel acik kaynak modeller icin Ollama istemcisi.

Onkosul: `ollama serve` calisiyor olmali ve model cekilmis olmali:
    ollama pull llama3.1:8b
    ollama pull qwen2.5:7b
Apple M2 Pro (16 GB birlesik bellek): 7-8B modeller Q4 nicemlemeyle (~4.7 GB)
Metal GPU hizlandirmasiyla rahatca calisir.

format="json" parametresi, Ollama'nin gecerli JSON dondurmesini zorlar
(constrained decoding'in hafif bir bicimi) -- Llama'nin JSON tutarsizligini azaltir.
"""
from __future__ import annotations

import time

import requests

from .base import ModelClient


class OllamaClient(ModelClient):
    def __init__(self, name: str, model: str, host: str = "http://localhost:11434",
                 temperature: float = 0.0, num_ctx: int = 8192,
                 force_json: bool = True, timeout: int = 180):
        super().__init__(name=name, temperature=temperature)
        self.model = model
        self.host = host.rstrip("/")
        self.num_ctx = num_ctx
        self.force_json = force_json
        self.timeout = timeout

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.force_json:
            payload["format"] = "json"
        t0 = time.time()
        r = requests.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
        self.last_latency_ms = (time.time() - t0) * 1000.0
        r.raise_for_status()
        data = r.json()
        # Ollama token sayaclari
        self.last_token_count = int(data.get("prompt_eval_count", 0)) + \
            int(data.get("eval_count", 0))
        return data.get("message", {}).get("content", "")
