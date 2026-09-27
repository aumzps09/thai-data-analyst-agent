"""Doc agent — placeholder retriever (reuse Project 1 interface)."""

from __future__ import annotations

import os


def _query_chroma(question: str, k: int = 4) -> list[dict]:
    try:
        import chromadb

        client = chromadb.HttpClient(host=os.getenv("CHROMA_HOST", "localhost"), port=8001)
        col = client.get_collection("docs")
        res = col.query(query_texts=[question], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"text": d[:800], **(m or {})} for d, m in zip(docs, metas)]
    except Exception:
        return []


def doc_agent_node(state: dict) -> dict:
    docs = _query_chroma(state.get("question", ""))
    if not docs:  # offline fallback: search local policies table text is handled by sql path
        docs = [{"text": "(mock) เชื่อม Chroma จาก Project 1 ที่ CHROMA_HOST เพื่อเปิด doc retrieval จริง", "source": "mock"}]
    return {"docs": docs}
