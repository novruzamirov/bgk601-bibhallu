"""
retriever.py -- ChromaDB uzerinden cosine-similarity tabanli retrieval.

ChromaRetriever, bir referans dizgesini sorgu olarak alir, en yakin k kaydi
dondurur ve prompt'a eklenecek "rag_context" metnini olusturur. Cagrilabilir
(callable) oldugu icin dogrudan BenchmarkEvaluator(retriever=...) ile kullanilir.

build_index.py ile ayni embedding modeli kullanilmalidir.
"""
from __future__ import annotations

from typing import List, Dict, Any


class ChromaRetriever:
    def __init__(self, chroma_dir: str, embedding_model: str,
                 collection: str = "bibhallu", top_k: int = 4):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer(embedding_model)
        self.client = chromadb.PersistentClient(path=chroma_dir)
        self.col = self.client.get_collection(collection)
        self.top_k = top_k

    def query(self, reference: str) -> List[Dict[str, Any]]:
        emb = self.embedder.encode([reference], normalize_embeddings=True).tolist()
        res = self.col.query(query_embeddings=emb, n_results=self.top_k,
                             include=["documents", "metadatas", "distances"])
        out = []
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                                   res["distances"][0]):
            out.append({"document": doc, "metadata": meta,
                        "similarity": 1.0 - dist})  # cosine distance -> similarity
        return out

    def __call__(self, reference: str) -> str:
        """Prompt'a gomulecek RAG baglam metnini dondurur."""
        hits = self.query(reference)
        if not hits:
            return "(Bilgi tabaninda eslesen kayit bulunamadi.)"
        lines = []
        for i, h in enumerate(hits, 1):
            lines.append(f"[{i}] (benzerlik={h['similarity']:.2f}) {h['document'][:300]}")
        return "\n".join(lines)
