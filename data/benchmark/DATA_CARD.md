## Dataset Card: BibHallu-Bench

### Ozet
- Amac: Arastirma makalelerindeki bibliyografya halusinasyonlarinin LLM tabanli tespiti icin benchmark
- Toplam ornek: 300 | Kategoriler: H1-H5 | Dil: Ingilizce (referanslar), Turkce (anotasyon)
- Olusturma modu: online (CrossRef+OpenAlex, 84 gercek makale)

### Kategori Dagilimi
| Kod | Kategori | Ornek |
|-----|----------|-------|
| H1 | Tamamen Var Olmayan Referans | 80 |
| H2 | Metadata Halusinasyonu | 60 |
| H3 | Semantik Uyumsuzluk | 60 |
| H4 | Kronolojik Halusinasyon | 40 |
| H5 | Dogru Referans (Negatif) | 60 |
| | **Toplam** | **300** |

### Sinif Dengesi
- Pozitif (halusinasyon var): 240 (%80)
- Negatif (halusinasyon yok): 60 (%20)

### Zorluk Dagilimi
- Kolay: 72 | Orta: 154 | Zor: 74

### Kaynak Veriler
- Kaynaklar: CrossRef (api.crossref.org), OpenAlex (api.openalex.org), sentetik uretim
- Lisans: CrossRef/OpenAlex acik metadata; sentetik ornekler proje kapsaminda uretildi
- Anonimlesme: Yalnizca kamuya acik akademik metadata; kisisel veri yok

### Anotasyon
- Yontem: Construction'dan-bilinen ground-truth + ELLE dogrulama (annotation_tool.py)
- YZ otomatik etiketlemesi ground-truth olarak KULLANILMAMISTIR
- Dogrulanmis ornek sayisi: 0/300

### Ornek Girdi (JSON)
```json
{
  "id": 1,
  "kategori": "H1",
  "zorluk": "orta",
  "girdi": "D. Anderson, J. Halloran, H. Esposito, D. Vasquez, \"Privacy-Preserving Zero-Day Exploit Forecasting,\" in Proc. USENIX Security Symposium, 2024.",
  "baglam": "",
  "beklenen_cevap": {
    "hallucination": true,
    "type": "H1",
    "reason": "Tamamen uydurma referans: bu baslik/yazar kombinasyonuna sahip yayimlanmis bir makale yoktur."
  },
  "metadata": {
    "title": "Privacy-Preserving Zero-Day Exploit Forecasting",
    "authors": [
      "D. Anderson",
      "J. Halloran",
      "H. Esposito",
      "D. Vasquez"
    ],
    "year": 2024,
    "venue": "Proc. USENIX Security Symposium",
    "doi": null
  },
  "kaynak": "synthetic",
  "aciklama": "Sentetik olarak uretilmis, hicbir veritabaninda bulunmayan referans.",
  "verified": false
}
```
