"""
build_index.py -- RAG bilgi tabani indeksini olusturur (ChromaDB + sentence-transformers).

Bilgi tabani kaynaklari (Bolum 3.2 / final 3.2):
  - CrossRef / OpenAlex'ten cekilen gercek makale metadata + abstract'lari
  - (istege bagli) MITRE ATT&CK / NVD ozetleri

Her dokuman "Baslik. Yazarlar (Yil). Yer. Abstract..." biciminde tek metne donusturulur,
gomulur (embedding) ve ChromaDB koleksiyonunda saklanir. Retrieval asamasinda bir
referans dizgesi sorgu olarak kullanilir; en yakin k kayit dondurulur.

Kullanim:
  python -m src.rag.build_index --papers data/raw/papers.json --chroma-dir data/chroma
papers.json -> [{"title","authors","year","venue","doi","abstract"}, ...]
(build_dataset.py'nin online modu bu dosyayi da uretebilir; ya da ayrica toplanir.)
"""
from __future__ import annotations

import argparse
import json
import os
from typing import List, Dict, Any


def doc_text(p: Dict[str, Any]) -> str:
    authors = ", ".join(p.get("authors", []) or [])
    return (f"{p.get('title','')}. {authors} ({p.get('year','')}). "
            f"{p.get('venue','')}. {p.get('abstract','')}").strip()


def build(papers: List[Dict[str, Any]], chroma_dir: str,
          embedding_model: str, collection: str = "bibhallu") -> int:
    import chromadb
    from sentence_transformers import SentenceTransformer

    os.makedirs(chroma_dir, exist_ok=True)
    embedder = SentenceTransformer(embedding_model)
    client = chromadb.PersistentClient(path=chroma_dir)
    # Temiz kurulum
    try:
        client.delete_collection(collection)
    except Exception:
        pass
    col = client.create_collection(collection, metadata={"hnsw:space": "cosine"})

    docs, ids, metas = [], [], []
    for i, p in enumerate(papers):
        t = doc_text(p)
        if not t:
            continue
        docs.append(t)
        ids.append(str(i))
        metas.append({"title": p.get("title", ""), "year": p.get("year", ""),
                      "doi": p.get("doi") or ""})
    embeddings = embedder.encode(docs, show_progress_bar=True,
                                 normalize_embeddings=True).tolist()
    # ChromaDB'ye toplu ekleme (buyuk koleksiyonlar icin parcala)
    B = 256
    for s in range(0, len(docs), B):
        col.add(ids=ids[s:s+B], documents=docs[s:s+B],
                embeddings=embeddings[s:s+B], metadatas=metas[s:s+B])
    print(f"[+] {len(docs)} dokuman indekslendi -> {chroma_dir} (koleksiyon: {collection})")
    return len(docs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", required=True)
    ap.add_argument("--chroma-dir", default="data/chroma")
    ap.add_argument("--embedding-model",
                    default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()
    with open(args.papers, encoding="utf-8") as f:
        papers = json.load(f)
    build(papers, args.chroma_dir, args.embedding_model)


if __name__ == "__main__":
    main()
