"""
Cross-encoder reranker (master prompt section 31) — a small, fast MS
MARCO cross-encoder, not the larger bge-reranker-v2-m3. Scores each
(query, chunk) pair directly, which is more accurate than comparing
separate embeddings but too slow to run over a whole corpus — only used
on the already-narrowed candidate pool from hybrid search.
"""

import threading

from sentence_transformers import CrossEncoder

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_lock = threading.Lock()
_model: CrossEncoder | None = None


def get_model() -> CrossEncoder:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _model


def rerank(query: str, texts: list[str]) -> list[float]:
    if not texts:
        return []
    pairs = [[query, text] for text in texts]
    scores = get_model().predict(pairs)
    return [float(s) for s in scores]
