# BibHallu-Bench: Araştırma Makalelerinde Bibliyografya Halüsinasyonlarının LLM Tabanlı Tespiti

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/models-4_LLM-orange?style=flat-square" alt="4 LLM models">
  <img src="https://img.shields.io/badge/benchmark-300_examples-purple?style=flat-square" alt="300 examples">
  <img src="https://img.shields.io/badge/RAG-ChromaDB%20%2B%20Sentence--Transformers-teal?style=flat-square" alt="RAG">
  <img src="https://img.shields.io/badge/status-academic_research-yellow?style=flat-square" alt="Research">
</p>

> **BGK601 — Bilgi Güvenliği Alanında Makine Öğrenmesi Yöntemleri** · İTÜ Siber Güvenlik Mühendisliği ve Kriptografi · Bahar 2025–2026
> Öğrenci: **Novruz Amirov (707241004)** · Ders Koordinatörü: Prof. Dr. Kemal Bıçakçı

LLM tarafından üretilen veya destekli yazılan akademik makalelerin **bibliyografya bölümlerindeki halüsinasyonları** (uydurma, metadata-hatalı, semantik-uyumsuz, kronolojik-imkânsız atıflar) otomatik olarak tespit etmek için **çok modelli** ve **RAG-güçlendirilmiş** bir değerlendirme çerçevesi. 4 LLM (2 closed-source API + 2 open-source yerel) ortak bir 300-örnekli benchmark üzerinde sistematik olarak karşılaştırıldı; istatistiksel anlamlılık bootstrap ve McNemar testleriyle raporlandı.

---

## 📊 Anahtar Sonuçlar

| Model | Tür | F1 (RAG'sız) | F1 (RAG'lı) | ΔF1 | USD/doğru karar |
|---|---|:---:|:---:|:---:|:---:|
| **GPT-4o** | closed-source | **0.911** | — | — | $0.0020 |
| **GPT-4o-mini** | closed-source | 0.862 | — | — | $0.0003 |
| **Llama 3.1-8B** | open-source | 0.560 | **0.792** | **+0.231** | $0.00 |
| **Qwen2.5-7B** | open-source | 0.071 | 0.480 | **+0.409** | $0.00 |

> **Başlık bulgu:** RAG, küçük açık kaynak modellere büyük kazanç sağlıyor. RAG'lı Llama (0.792), GPT-4o-mini'ye (0.862) yalnız 0.07 puan farkla yaklaşıyor — **sıfır API maliyetiyle**.

Tüm pairwise farklar McNemar testiyle p < 0.01 düzeyinde anlamlı; Fleiss κ = 0.90–1.00 (yüksek tutarlılık).

---

## ⚡ 60 saniyede dene (offline)

```bash
git clone https://github.com/novruzamirov/bgk601-bibhallu.git
cd bgk601-bibhallu
pip install -r requirements.txt
bash scripts/smoke_test.sh
```

**11/11 birim test geçer · 30-örnekli mock veri kümesi üretilir · 4 model mock ile değerlendirilir · RAG ablasyon simüle edilir · grafikler çıkar.**
*Mock = test çift'i; gerçek model değil. Pipeline'ın doğru çalıştığını dakikalar içinde kanıtlar.*

---

## 🧩 Halüsinasyon Kategorileri (H1–H5)

| Kod | Kategori | Tanım | Örnek sayısı |
|---|---|---|:---:|
| **H1** | Var olmayan referans | LLM uydurması, hiç yayımlanmamış | 80 |
| **H2** | Metadata halüsinasyonu | Gerçek makale, yanlış yazar / yıl / dergi | 60 |
| **H3** | Semantik uyumsuzluk | Gerçek makale, atıf bağlamıyla ilgisiz | 60 |
| **H4** | Kronolojik halüsinasyon | İmkânsız tarih (gelecek / teknolojiden önce) | 40 |
| **H5** | Doğru referans (negatif) | Tüm alanlar doğrulanmış | 60 |

---

## 🎯 Proje Gereksinim Haritası (BGK601 rubriği)

| Gereksinim | Bu repoda |
|---|---|
| ≥4 model (≥2 closed API + ≥2 open yerel) | `config/config.yaml` → GPT-4o, GPT-4o-mini + Llama 3.1-8B, Qwen2.5-7B |
| ≥200 örnek, her kategori ≥20, 3+ alt kategori | 300 örnek, 5 kategori |
| Manual annotation (YZ etiketi ground-truth değil) | `src/dataset/annotation_tool.py` (CLI ile elle onay) |
| Değerlendirme protokolü (≥3 çalıştırma, T=0, çoğunluk) | `src/evaluation/eval_framework.py` |
| Metrikler (F1, Precision, Recall, MCC) | `src/evaluation/metrics.py` |
| **RAG (zorunlu) + ablasyon** | `src/rag/` → ChromaDB + sentence-transformers |
| İstatistik (bootstrap CI + McNemar) | `src/evaluation/statistics.py` |
| Hata analizi + maliyet-başarım | `src/analysis/` |
| Tekrarlanabilirlik (kod + README + ortam) | bu README + `requirements.txt` + `.env.example` |

---

## 📁 Dizin Yapısı

```
bgk601-bibhallu/
├── config/config.yaml          # 4 modelin tanımı + RAG ayarları
├── data/
│   ├── benchmark/              # benchmark.json + DATA_CARD.md
│   └── raw/                    # RAG korpusu (CrossRef'ten çekilen 400+ makale)
├── src/
│   ├── dataset/                # CrossRef + OpenAlex istemcileri, H1-H5 üreticileri, annotation aracı
│   ├── models/                 # Provider-agnostik istemci (Ollama, OpenAI, Anthropic, Gemini, mock)
│   ├── evaluation/             # Prompt, metrik, istatistik, eval runner
│   ├── rag/                    # build_corpus, build_index, retriever, ablation
│   └── analysis/               # Grafik üretimi, hata analizi
├── scripts/                    # Numaralı kabuk betikleri (0–5) + smoke_test
├── tests/                      # 11 birim test
├── report/                     # LaTeX rapor + IEEE bibliyografya
└── results/                    # Çıktılar (git'e dahil değil)
```

---

## 🚀 Gerçek Çalıştırma (4 adım, ~5 saat çoğunlukla gözetimsiz)

### 0) Kurulum (~20 dk, bir defalık)

```bash
bash scripts/0_setup.sh             # Python deps + Ollama modelleri
cp .env.example .env                # API anahtarlarını gir
```

**Ollama** gerekli (yerel modeller için): https://ollama.com
İhtiyaç duyduğun anahtarlar (en az birini gir):
- `OPENAI_API_KEY` (GPT-4o + mini) — ücretli, deneyin tamamı ~$3
- `ANTHROPIC_API_KEY` (Claude) — opsiyonel
- `GOOGLE_API_KEY` (Gemini) — ücretsiz katman var
- `OPENALEX_API_KEY` — RAG korpusunu zenginleştirmek için (opsiyonel)

### 1) Veri kümesi + manuel anotasyon

```bash
bash scripts/1_build_dataset.sh
python -m src.dataset.annotation_tool --in data/benchmark/benchmark.json
```

### 2) Tüm modellerde değerlendirme (~1.5–2 saat)

```bash
bash scripts/2_run_eval.sh
```
→ `results/<model>.json` + `results/summary.json`

### 3) RAG kur + ablasyon (~3–4 saat)

```bash
bash scripts/3_build_rag.sh          # CrossRef korpusu + ChromaDB indeksi
bash scripts/4_rag_ablation.sh       # open modeller: RAG'lı vs RAG'sız
```
→ `results/rag_ablation.json`

### 4) Grafikler + hata analizi (~1 dk)

```bash
bash scripts/5_analyze.sh
```
→ `results/figures/*.png` + her model için `*_errors.json`

---

## 🔬 Değerlendirme Protokolü

- **Sıcaklık (temperature):** `0.0` — deterministik çıktı
- **Çalıştırma:** her örnek için **3 bağımsız** koşu → **çoğunluk kararı**
- **Yapılandırılmış çıktı:** sağlayıcı-tarafında zorlanır (OpenAI `response_format=json_object`, Ollama `format=json`)
- **Çıktı:** `{"hallucination": bool, "confidence": float, "type": "H1..H5|none", "reason": str}`
- **Tutarlılık:** Fleiss κ (3+ çalıştırma için doğru ölçüt; Cohen κ yalnız 2 değerlendirici için)
- **Anlamlılık:** F1 için n=2000 bootstrap %95 GA; iki model arasında McNemar (sürekli düzeltmeli χ², df=1)

---

## 💻 Donanım Notu (Apple M2 Pro, 16 GB)

Apple Silicon **Unified Memory Architecture** kullanır — ayrı VRAM yoktur. 7–8B modeller **Q4 nicemleme** (~4.7 GB) ile Metal GPU hızlandırmasıyla rahatça çalışır. `num_ctx=8192` 16 GB için uygundur.

Stage 1 (4 model · 300 × 3) ~1.5 saat sürer. Stage 2 (RAG ablasyon · 2 open model × 2 koşul × 300 × 3) ~3–4 saat. Toplam ~5 saat, çoğu gözetimsiz.

`caffeinate -i &` ile Mac uykuya geçmez.

---

## 🤖 Yapay Zeka Araçları Kullanım Notu

Bu repo geliştirilirken **Claude (Anthropic)** ve **ChatGPT (OpenAI)** kod iskeleti, dokümantasyon, rapor metni ve sunum slaytlarının düzenlenmesi amacıyla kullanılmıştır.

**Benchmark anotasyonu, deney çalıştırma, hata analizi ve final metin sorumluluğu öğrenciye aittir.** YZ otomatik etiketlemesi ground-truth olarak kullanılmamıştır (`annotation_tool.py` insan onayını zorunlu kılar).

---

## ⚖️ Etik ve Güvenlik Sınırları

- Yalnızca **kamuya açık** akademik metadata (CrossRef, OpenAlex) kullanılır
- Kişisel veri işlenmez; özgün makaleler sisteme yüklenmez
- Sistem çıktıları **"şüpheli"** etiketidir; nihai doğrulama insan uzmandadır
- Akademik etik / dezenformasyon / sosyal mühendislik vektörleri kapsamında siber güvenlik problemi olarak konumlanır

---

## 📄 Final Rapor + Sunum

- 📘 **Rapor** (19 sayfa, IEEE atıf stili, 25 akademik kaynak): `report/main.tex` + derlenmiş `BGK601_Final_Raporu.pdf`
- 🎯 **Sunum** (20 slayt): `BGK601_Sunum.pptx`

---

## 📚 Atıf

Bu çalışmayı atıf yapmak isterseniz:

```bibtex
@misc{amirov2026bibhallu,
  author       = {Amirov, Novruz},
  title        = {{BibHallu-Bench}: Araştırma Makalelerinde Bibliyografya
                  Halüsinasyonlarının LLM Tabanlı Tespiti},
  year         = {2026},
  howpublished = {BGK601 Final Project, Istanbul Technical University},
  url          = {https://github.com/novruzamirov/bgk601-bibhallu}
}
```

---

## 🛠️ Teknoloji Yığını

| Katman | Araç |
|---|---|
| LLM API | OpenAI SDK, Anthropic SDK, Google GenAI |
| Yerel LLM | Ollama (Llama 3.1-8B, Qwen2.5-7B; Q4_K_M) |
| Embedding | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector DB | ChromaDB (HNSW + cosine) |
| RAG Pipeline | LangChain-style |
| Akademik Metadata | CrossRef REST API, OpenAlex |
| Değerlendirme | scikit-learn, scipy, custom statistics |
| Görselleştirme | matplotlib |
| Test | pytest (11 unit test) |

---

## 📜 Lisans

[MIT](LICENSE) — kod açık kaynak, yeniden kullanım serbest, atıf rica olunur.

---

## ✉️ İletişim

**Novruz Amirov** · İTÜ Siber Güvenlik Mühendisliği ve Kriptografi
📧 [amirov20@itu.edu.tr](mailto:amirov20@itu.edu.tr)
🐙 [GitHub @novruzamirov](https://github.com/novruzamirov)
