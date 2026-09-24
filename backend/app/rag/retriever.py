"""
Markdown RAG retrieval — master prompt section 27:
  Query -> vector search + BM25 (parallel) -> RRF fusion -> cross-encoder
  rerank -> evidence check -> top context.

This is the deeper search used when Fast Q&A (qa/retriever.py) doesn't
have a confident match. Ingestion (chunk + embed + index) runs once at
startup, same drop-and-recreate philosophy as the Q&A side (master
prompt section 6 / section 11).
"""

import re
from collections import defaultdict
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from backend.app.config import BASE_DIR
from backend.app.models.embeddings import embed, embed_query
from backend.app.rag import milvus_store
from backend.app.rag.markdown_processor import MarkdownChunk, process_all_markdown
from backend.app.rag.reranker import rerank

KNOWLEDGE_ROOT = BASE_DIR / "data" / "knowledge" / "prospect_to_cash"

TOP_K_HYBRID = 10
TOP_K_RERANKED = 5
RRF_K = 60

# Cross-encoder ms-marco-MiniLM-L-6-v2 outputs an unbounded logit, roughly
# negative for irrelevant pairs and positive for relevant ones in practice.
# This is a starter value from a quick check against this project's own
# dummy data, NOT a benchmarked number — master prompt section 33 expects
# real evaluation before trusting a threshold like this in production.
EVIDENCE_THRESHOLD = -2.0


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1.0 / (k + rank)
    return scores


@dataclass
class RagResult:
    has_evidence: bool
    chunks: list[MarkdownChunk]
    scores: list[float]


class RagIndex:
    def __init__(self) -> None:
        self.chunks: list[MarkdownChunk] = process_all_markdown(KNOWLEDGE_ROOT)
        self._chunks_by_id = {c.chunk_id: c for c in self.chunks}

        milvus_store.reset_collection()
        if self.chunks:
            embeddings = embed([c.embed_text for c in self.chunks])
            rows = [
                {
                    "id": c.chunk_id,
                    "vector": embeddings[i].tolist(),
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "text": c.text,
                    "level": c.level,
                    "full_context_path": c.full_context_path,
                    "source_file": c.source_file,
                    "chunk_index": c.chunk_index,
                    "total_chunks": c.total_chunks,
                }
                for i, c in enumerate(self.chunks)
            ]
            milvus_store.insert_rows(rows)

        tokenized_corpus = [_tokenize(c.embed_text) for c in self.chunks]
        self._bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    def search(self, query: str) -> RagResult:
        if not self.chunks or self._bm25 is None:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        query_vector = embed_query([query])[0].tolist()
        vector_hits = milvus_store.search(query_vector, top_k=TOP_K_HYBRID * 2)
        vector_ranking = [hit["chunk_id"] for hit in vector_hits]

        bm25_scores = self._bm25.get_scores(_tokenize(query))
        bm25_ranked_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
        bm25_ranking = [
            self.chunks[i].chunk_id for i in bm25_ranked_indices[: TOP_K_HYBRID * 2] if bm25_scores[i] > 0
        ]

        if not vector_ranking and not bm25_ranking:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        fused_scores = _reciprocal_rank_fusion([vector_ranking, bm25_ranking])
        candidate_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[: TOP_K_HYBRID * 2]
        candidates = [self._chunks_by_id[cid] for cid in candidate_ids if cid in self._chunks_by_id]

        if not candidates:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        rerank_scores = rerank(query, [c.text for c in candidates])
        ranked = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)
        top = ranked[:TOP_K_RERANKED]

        has_evidence = bool(top) and top[0][1] >= EVIDENCE_THRESHOLD
        if not has_evidence:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        # only pass genuinely relevant chunks downstream — being in the
        # top 5 isn't enough on its own if the score says "not related"
        top_chunks = [c for c, score in top if score >= EVIDENCE_THRESHOLD]
        top_scores = [score for _, score in top if score >= EVIDENCE_THRESHOLD]

        # simple contextual compression: cap total context sent downstream
        # rather than a token-accurate budget — good enough for Phase 1
        compressed_chunks: list[MarkdownChunk] = []
        compressed_scores: list[float] = []
        running_chars = 0
        for chunk, score in zip(top_chunks, top_scores):
            if running_chars + len(chunk.text) > 6000 and compressed_chunks:
                break
            compressed_chunks.append(chunk)
            compressed_scores.append(score)
            running_chars += len(chunk.text)

        return RagResult(has_evidence=True, chunks=compressed_chunks, scores=compressed_scores)


_index: RagIndex | None = None


def get_rag_index() -> RagIndex:
    global _index
    if _index is None:
        _index = RagIndex()
    return _index
