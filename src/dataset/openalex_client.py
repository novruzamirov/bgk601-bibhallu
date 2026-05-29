"""
openalex_client.py -- OpenAlex API istemcisi.

OpenAlex, acik erisimli akademik metadata + makale soyutlari (abstract) saglar.
H3 (semantik uyumsuzluk) ornekleri icin makale soyutlari buradan cekilir; ayrica
RAG bilgi tabani da OpenAlex/CrossRef icerikleriyle beslenebilir.

ONEMLI (Subat 2026 itibariyla): OpenAlex API artik bir API anahtari gerektirir
(gunde ~1 USD'ye kadar ucretsiz kullanim; ~10 istek/sn). Anahtar .env icindeki
OPENALEX_API_KEY ile saglanir. mailto parametresi yine onerilir.

OpenAlex, abstract'i "abstract_inverted_index" (kelime -> pozisyonlar) biciminde
dondurur; bu modul onu duz metne geri cevirir.
"""
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any, List

import requests

BASE_URL = "https://api.openalex.org/works"


class OpenAlexClient:
    def __init__(self, mailto: str, api_key: Optional[str] = None,
                 timeout: int = 20, max_retries: int = 4):
        self.mailto = mailto
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    def _get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        params = dict(params)
        params["mailto"] = self.mailto
        if self.api_key:
            params["api_key"] = self.api_key
        delay = 1.0
        for _ in range(self.max_retries):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                if r.status_code == 200:
                    return r.json()
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(delay)
                    delay *= 2
                    continue
                return None
            except requests.RequestException:
                time.sleep(delay)
                delay *= 2
        return None

    def search(self, query: str, per_page: int = 5,
               require_abstract: bool = True) -> List[Dict[str, Any]]:
        params = {"search": query, "per-page": per_page}
        if require_abstract:
            params["filter"] = "has_abstract:true"
        data = self._get(BASE_URL, params)
        if not data:
            return []
        return data.get("results", [])

    @staticmethod
    def invert_abstract(inv_index: Optional[Dict[str, List[int]]]) -> str:
        """abstract_inverted_index -> duz metin."""
        if not inv_index:
            return ""
        positions: List[tuple] = []
        for word, idxs in inv_index.items():
            for i in idxs:
                positions.append((i, word))
        positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in positions)

    def normalize(self, item: Dict[str, Any]) -> Dict[str, Any]:
        authors = []
        for a in item.get("authorships", []) or []:
            name = (a.get("author") or {}).get("display_name", "")
            if name:
                authors.append(name)
        return {
            "title": item.get("title") or item.get("display_name") or "",
            "authors": authors,
            "year": item.get("publication_year"),
            "venue": ((item.get("primary_location") or {}).get("source") or {}).get(
                "display_name", ""),
            "doi": (item.get("doi") or "").replace("https://doi.org/", "") or None,
            "abstract": self.invert_abstract(item.get("abstract_inverted_index")),
        }
