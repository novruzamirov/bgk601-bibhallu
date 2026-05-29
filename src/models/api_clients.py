"""
api_clients.py -- Kapali kaynak (API tabanli) modeller.

Saglayicilar: OpenAI (GPT-4o/4o-mini), Anthropic (Claude), Google (Gemini).
Her saglayicinin SDK'si yalnizca o istemci olusturuldugunda import edilir; boylece
yalnizca kullandiginiz saglayicinin paketini kurmaniz yeterlidir.

UCRETSIZ YOL (anahtarsiz baslangic icin): Google Gemini'nin gercek bir ucretsiz
katmani vardir (gemini-1.5-flash / gemini-2.0-flash). "2 kapali kaynak model"
gereksinimini ucretsiz karsilamak icin iki Gemini varyanti kullanilabilir; butce
varsa GPT-4o ekleyerek saglayici cesitliligi artirilir.

Anahtarlar .env dosyasindan okunur: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY.
"""
from __future__ import annotations

import os
import time

from .base import ModelClient

_JSON_HINT = ' Yanitini yalnizca gecerli JSON olarak ver.'


class OpenAIClient(ModelClient):
    def __init__(self, name: str, model: str = "gpt-4o", temperature: float = 0.0):
        super().__init__(name=name, temperature=temperature)
        from openai import OpenAI  # lazy import
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        t0 = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt + _JSON_HINT},
                {"role": "user", "content": user_prompt},
            ],
        )
        self.last_latency_ms = (time.time() - t0) * 1000.0
        if resp.usage:
            self.last_token_count = resp.usage.total_tokens
        return resp.choices[0].message.content or ""


class AnthropicClient(ModelClient):
    def __init__(self, name: str, model: str = "claude-sonnet-4-5",
                 temperature: float = 0.0, max_tokens: int = 1024):
        super().__init__(name=name, temperature=temperature)
        import anthropic  # lazy import
        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        t0 = time.time()
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt + _JSON_HINT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.last_latency_ms = (time.time() - t0) * 1000.0
        self.last_token_count = (resp.usage.input_tokens + resp.usage.output_tokens
                                 if resp.usage else 0)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


class GeminiClient(ModelClient):
    def __init__(self, name: str, model: str = "gemini-1.5-flash",
                 temperature: float = 0.0):
        super().__init__(name=name, temperature=temperature)
        import google.generativeai as genai  # lazy import
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = model
        self._genai = genai
        self.model = genai.GenerativeModel(model)

    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        t0 = time.time()
        resp = self.model.generate_content(
            f"{system_prompt}{_JSON_HINT}\n\n{user_prompt}",
            generation_config=self._genai.types.GenerationConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
            ),
        )
        self.last_latency_ms = (time.time() - t0) * 1000.0
        try:
            self.last_token_count = resp.usage_metadata.total_token_count
        except Exception:
            self.last_token_count = 0
        return resp.text or ""
