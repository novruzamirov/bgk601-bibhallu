"""
crossref_client.py -- CrossRef REST API istemcisi.

CrossRef, DOI dogrulamasi ve metadata (yazar/yil/dergi) kontrolu icin kullanilir.
H2 (metadata halusinasyonu) ve H5 (dogru referans) ornekleri bu kaynaktan turetilir.

Kibar havuz (polite pool): istekte ?mailto=... gondererek daha yuksek ve kararli
hiz limiti elde edilir. CrossRef sabit "saniyede 5 istek" YERINE dinamik bir limit
uygular (~50 istek/sn'ye kadar); guncel limit X-Rate-Limit-Limit ve
X-Rate-Limit-Interval yanit basliklarindan okunabilir.

Bu modul internet erisimi gerektirir; ogrencinin makinesinde calistirilir.
"""
from __future__ import annotations

import time
from typing import Optional, Dict, Any, List

import requests

BASE_URL = "https://api.crossref.org/works"


class CrossRefClient:
    def __init__(self, mailto: str, timeout: int = 20, max_retries: int = 4):
        # mailto -> CrossRef "polite pool"; dogru bir e-posta vermek onemlidir.
        self.mailto = mailto
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": f"BGK601-BibHallu/1.0 (mailto:{mailto})"}
        )
        self.last_rate_limit: Dict[str, str] = {}

    def _get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        params = dict(params)
        params["mailto"] = self.mailto
        delay = 1.0
        for attempt in range(self.max_retries):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                # Hiz limiti bilgisini sakla (raporlama/teshis icin)
                self.last_rate_limit = {
                    "limit": r.headers.get("X-Rate-Limit-Limit", "?"),
                    "interval": r.headers.get("X-Rate-Limit-Interval", "?"),
                }
                if r.status_code == 200:
                    return r.json()
                if r.status_code in (429, 500, 502, 503, 504):
                    # Exponential backoff
                    time.sleep(delay)
                    delay *= 2
                    continue
                return None
            except requests.RequestException:
                time.sleep(delay)
                delay *= 2
        return None

    def search_by_title(self, title: str, rows: int = 1) -> List[Dict[str, Any]]:
        """Baslikla arama yapar, en olasi eslesmeleri dondurur."""
        data = self._get(BASE_URL, {"query.bibliographic": title, "rows": rows})
        if not data:
            return []
        return data.get("message", {}).get("items", [])

    def search(self, query: str, rows: int = 20,
               filter_: str = "type:journal-article,type:proceedings-article"
               ) -> List[Dict[str, Any]]:
        """Konu/anahtar kelime ile genel arama (RAG korpusu icin coklu kayit)."""
        data = self._get(BASE_URL, {"query": query, "rows": rows, "filter": filter_})
        if not data:
            return []
        return data.get("message", {}).get("items", [])

    def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """DOI ile dogrudan kayit ceker. DOI gercekten varsa metadata doner."""
        data = self._get(f"{BASE_URL}/{doi}", {})
        if not data:
            return None
        return data.get("message")

    @staticmethod
    def normalize(item: Dict[str, Any]) -> Dict[str, Any]:
        """CrossRef kaydini projemizin sade metadata semasina cevirir."""
        authors = []
        for a in item.get("author", []) or []:
            given = a.get("given", "")
            family = a.get("family", "")
            initials = " ".join(p[0] + "." for p in given.split()) if given else ""
            authors.append(f"{initials} {family}".strip())
        title = (item.get("title") or [""])[0]
        venue = (item.get("container-title") or [""])
        venue = venue[0] if venue else ""
        year = None
        for k in ("published-print", "published-online", "issued", "created"):
            parts = (item.get(k) or {}).get("date-parts")
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
                break
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": item.get("DOI"),
        }
