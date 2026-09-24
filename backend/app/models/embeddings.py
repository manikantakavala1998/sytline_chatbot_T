"""
Loads the embedding model (sentence-transformers) exactly once and reuses
it everywhere — loading it is slow, so every caller (Q&A search now,
Markdown search later) shares this one instance.
"""

import threading

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.config import settings

_lock = threading.Lock()
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = SentenceTransformer(settings.embedding_model)
    return _model


QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def embed(texts: list[str]) -> np.ndarray:
    """Embeds passage/answer-side text (Q&A questions, document chunks).
    Returns one L2-normalized vector per text (so cosine similarity is
    just a dot product)."""
    if not texts:
        return np.zeros((0, settings.embedding_dim))
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)


def embed_query(texts: list[str]) -> np.ndarray:
    """Embeds a user's search query. bge-base-en-v1.5 was trained to expect
    this instruction prefix on the query side only — passages/documents are
    embedded without it (see embed() above). Skipping this on one side but
    not the other is what caused short technical phrases like "order line"
    vs "customer order" to get confused in early testing."""
    if not texts:
        return np.zeros((0, settings.embedding_dim))
    return embed([QUERY_INSTRUCTION + t for t in texts])
