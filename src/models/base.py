"""
base.py -- Tum model istemcileri icin ortak arayuz + saglam JSON ayiklama.

Her istemci .predict(reference, context=None) cagrisinda ham metni dondurur ve
.last_latency_ms / .last_token_count alanlarini gunceller. parse_prediction()
modelin (bazen bozuk) ciktisini standart sozluge cevirir:
    {"hallucination": bool, "confidence": float, "type": "H1..H5|none", "reason": str}
"""
from __future__ import annotations

import abc
import json
import re
from typing import Optional, Dict, Any


class ModelClient(abc.ABC):
    """Tum modeller (yerel/API) bu arayuzu uygular."""

    def __init__(self, name: str, temperature: float = 0.0):
        self.name = name
        self.temperature = temperature
        self.last_latency_ms: float = 0.0
        self.last_token_count: int = 0

    @abc.abstractmethod
    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """Saglayiciya ozgu uretim. Ham metin dondurur."""
        raise NotImplementedError

    def predict(self, system_prompt: str, user_prompt: str) -> str:
        return self._generate(system_prompt, user_prompt)


# --- Saglam JSON ayiklama ------------------------------------------------------
_VALID_TYPES = {"H1", "H2", "H3", "H4", "H5", "none"}


def _extract_json_block(text: str) -> Optional[str]:
    """Metindeki ilk dengeli {...} blogunu bulur (markdown cit/aciklama olsa bile)."""
    # ```json ... ``` cevreleyicilerini temizle
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_prediction(raw: str) -> Dict[str, Any]:
    """
    Ham model ciktisini standart karara cevirir. Llama gibi modeller zaman zaman
    serbest metin dondurur; bu durumda anahtar kelimelerle geri donus (fallback)
    yapilir. Hicbir sey ayiklanamazsa parse_ok=False ile guvenli varsayilan doner.
    """
    result = {"hallucination": False, "confidence": 0.0, "type": "none",
              "reason": "", "parse_ok": False, "raw": raw}
    block = _extract_json_block(raw)
    if block:
        try:
            obj = json.loads(block)
            h = obj.get("hallucination")
            if isinstance(h, str):
                h = h.strip().lower() in ("true", "yes", "evet", "1")
            result["hallucination"] = bool(h)
            result["confidence"] = float(obj.get("confidence", 0.0) or 0.0)
            t = str(obj.get("type", "none")).strip().upper()
            t = "none" if t in ("NONE", "", "NULL", "H5_NEGATIVE") else t
            result["type"] = t if t in _VALID_TYPES else "none"
            result["reason"] = str(obj.get("reason", ""))[:500]
            result["parse_ok"] = True
            return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # Fallback: serbest metinden anahtar kelime cikarimi
    low = raw.lower()
    pos_kw = ("hallucinat", "fabricat", "fake", "does not exist", "var olmayan",
              "uydurma", "yanlis", "incorrect", "mismatch", "true")
    neg_kw = ("legitimate", "valid", "genuine", "gercek", "dogru referans",
              "no hallucination", "false")
    if any(k in low for k in pos_kw) and not any(
            k in low for k in ("no hallucination", "not a hallucination", "halusinasyon yok")):
        result["hallucination"] = True
    m = re.search(r"\bH[1-5]\b", raw)
    if m:
        result["type"] = m.group(0)
    result["reason"] = raw.strip()[:500]
    return result
