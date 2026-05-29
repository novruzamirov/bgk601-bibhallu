# Final Raporu — LaTeX kaynagi

## Derleme

**Gereken:** MacTeX (veya TeX Live), `biber` (LaTeX dagıtımıyla gelir).

```bash
cd report/
latexmk -pdf main.tex          # tek komut: pdflatex + biber + pdflatex x2
# veya elle:
pdflatex main && biber main && pdflatex main && pdflatex main
```

Çıktı: `main.pdf`.

## Doldurulması gereken kısımlar

Sonuçlar henüz boş. Stage 1–3 bittikten sonra:

```bash
grep -n "BURAYA EKLENECEK\|\\\\TBD" main.tex
```
komutu, doldurulması gereken her satırı listeler. Şu blokları doldur:

- **Tablo 4 (`tab:overall`)** ← `../results/summary.json`'daki `ranking` alanından
- **Tablo 5 (`tab:catf1`)** ← her `results/<model>.json`'un `category_f1` alanından
- **Tablo 6 (`tab:rag`)** ← `../results/rag_ablation.json`
- **Şekiller** (`figplaceholder` makroları): `\figplaceholder{...}{...}` → `\includegraphics[width=0.9\linewidth]{../results/figures/<dosya>.png}` ile değiştir
- **`\todoresult{...}` blokları:** yorumla, ya açıklayıcı paragrafla değiştir ya da sil

## Yerel önizleme

VSCode'da **LaTeX Workshop** eklentisi, `Cmd+Alt+B` ile otomatik derler ve sağda PDF gösterir.

## Atıf stili

IEEE (biblatex, `style=ieee`). Yeni atıf eklemek için `refs.bib` içine ekle, sonra `\cite{anahtar}` ile çağır.

## Dil

Türkçe (babel + utf8); teknik terimler İngilizce bırakılabilir (rubrik onayı).
