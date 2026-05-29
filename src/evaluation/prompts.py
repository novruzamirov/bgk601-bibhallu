"""
prompts.py -- Sistem ve kullanici prompt sablonlari (Bolum 3.3 protokolu ile uyumlu).

Iki sistem promptu:
- SYSTEM_PROMPT_BASE      : standart (zero-shot) talimat
- SYSTEM_PROMPT_COT       : chain-of-thought (H3 semantik uyumsuzluk icin guclendirme)

build_user_prompt(), RAG baglaminin (varsa) prompt'a nasil eklenecegini de yonetir.
"""

SYSTEM_PROMPT_BASE = (
    "Sen akademik referans dogrulama uzmanisin. Verilen referansin gercek bir "
    "akademik yayin olup olmadigini ve metadata tutarliligini analiz et. "
    "Su halusinasyon turlerini ayirt et: "
    "H1 = tamamen var olmayan referans; "
    "H2 = metadata halusinasyonu (yanlis yazar/yil/dergi); "
    "H3 = semantik uyumsuzluk (referans gercek ama atif baglamiyla ilgisiz); "
    "H4 = kronolojik halusinasyon (imkansiz/gelecek tarih); "
    "none = dogru referans (halusinasyon yok). "
    'Yalnizca su JSON semasiyla yanit ver: '
    '{"hallucination": true/false, "confidence": 0.0-1.0, '
    '"type": "H1|H2|H3|H4|none", "reason": "kisa gerekce"}'
)

SYSTEM_PROMPT_COT = (
    SYSTEM_PROMPT_BASE +
    " Karar vermeden once adim adim dusun: (1) baslik-yazar-yil-dergi ic tutarliligi, "
    "(2) referansin gercekte var olup olamayacagi, (3) verilmisse atif baglamiyla "
    "anlamsal uyum. Dusunceni 'reason' alaninda ozetle."
)


def build_user_prompt(reference: str, context: str = "",
                      rag_context: str = "") -> str:
    parts = [f"REFERANS:\n{reference}"]
    if context:
        parts.append(f"\nATIF BAGLAMI (referansin alintilandigi metin):\n{context}")
    if rag_context:
        parts.append(
            "\nBILGI TABANINDAN GETIRILEN ILGILI KAYITLAR (RAG):\n" + rag_context +
            "\n(Yukaridaki kayitlari referansin gercekligini dogrulamak icin kullan; "
            "referans bu kayitlarla eslesmiyorsa halusinasyon olabilir.)")
    parts.append("\nBu referansi analiz et ve JSON karari ver.")
    return "\n".join(parts)
