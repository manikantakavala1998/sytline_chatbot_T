"""
Unified knowledge retrieval over BOTH sources — master prompt section 27,
using the replica project's pattern of one shared index:

  query -> for each source (Excel Q&A, Markdown):
             vector search (Milvus, filtered by source_type) + BM25 -> RRF fusion
             -> top 10 candidates per source
        -> ONE cross-encoder reranks all 20 candidates against the query
        -> guaranteed-include rescue for a near-exact vector match (>= 0.80)
        -> evidence check -> top context, each item tagged with its source

Because both sources are scored by the same reranker, their scores are
directly comparable: the orchestrator answers with the curated Excel answer
verbatim when that is the single most confident candidate, and otherwise
generates an answer from the strongest evidence of either source.

Ingestion (embed + index both sources) runs once at startup, same
drop-and-recreate philosophy as the rest of the project.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

from backend.app.config import BASE_DIR, settings
from backend.app.models.embeddings import embed, embed_query
from backend.app.qa.loader import QARecord, load_qa_records
from backend.app.rag import milvus_store
from backend.app.rag.markdown_processor import MarkdownChunk, process_all_markdown
from backend.app.rag.reranker import rerank
from backend.app.utils.logger import get_logger

KNOWLEDGE_ROOT = BASE_DIR / "data" / "knowledge" / "prospect_to_cash"

logger = get_logger(__name__)

SOURCES = ("excel", "markdown")
CANDIDATES_PER_SOURCE = 10
TOP_K_RERANKED = 5
RRF_K = 60
GUARANTEED_INCLUDE_VECTOR_SCORE = 0.80  # replica §7 step 8
CONTEXT_CHAR_BUDGET = 6000

# Cross-encoder ms-marco-MiniLM-L-6-v2 outputs an unbounded logit, roughly
# negative for irrelevant pairs and positive for relevant ones in practice.
# Starter value from this project's own data, NOT a benchmarked number —
# master prompt section 33 expects real evaluation before production.
EVIDENCE_THRESHOLD = -2.0


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1.0 / (k + rank)
    return scores


def _qa_record_as_chunk(record: QARecord) -> MarkdownChunk:
    """Represent a curated Excel row in the same shape as a Markdown chunk, so
    both sources flow through one rerank / evidence / answer pipeline."""
    # Variations are included so the reranker can recognise paraphrases of the row's
    # question, not just its canonical wording.
    also_asked = "; ".join(record.match_texts[1:])
    return MarkdownChunk(
        chunk_id=record.qa_id,
        document_id=record.level,
        text=(
            f"Q: {record.canonical_question}\n"
            + (f"Also asked as: {also_asked}\n" if also_asked else "")
            + f"A: {record.answer}"
        ),
        embed_text=" ".join(record.match_texts),
        level=record.level,
        section_level1=record.process,
        section_level2="",
        section_level3="",
        full_context_path=f"Curated Q&A {record.qa_id}: {record.canonical_question}",
        source_file=f"{record.level}.xlsx",
        chunk_index=1,
        total_chunks=1,
        keywords=record.keywords,
    )


@dataclass
class RagResult:
    has_evidence: bool
    chunks: list[MarkdownChunk]
    scores: list[float]
    source_types: list[str] = field(default_factory=list)
    best_score_by_source: dict[str, float] = field(default_factory=dict)


class RagIndex:
    def __init__(self) -> None:
        markdown_chunks = process_all_markdown(KNOWLEDGE_ROOT)
        self.qa_records: dict[str, QARecord] = {r.qa_id: r for r in load_qa_records()}
        excel_chunks = [_qa_record_as_chunk(r) for r in self.qa_records.values()]

        self.chunks: list[MarkdownChunk] = markdown_chunks + excel_chunks
        self._chunks_by_id = {c.chunk_id: c for c in self.chunks}
        self._source_type = {c.chunk_id: "markdown" for c in markdown_chunks}
        self._source_type.update({c.chunk_id: "excel" for c in excel_chunks})

        logger.info("Connecting to Milvus at %s ...", settings.milvus_uri)
        milvus_store.reset_collection()
        logger.info("Milvus collection '%s' created (dropped + recreated fresh)", milvus_store.COLLECTION_NAME)

        rows = [
            {
                "id": c.chunk_id, "source_type": "markdown", "chunk_id": c.chunk_id,
                "source_file": c.source_file, "level": c.level, "full_context_path": c.full_context_path,
                "qa_id": "", "question": "", "text": c.text,
                "chunk_index": c.chunk_index, "total_chunks": c.total_chunks,
                "_embed": c.embed_text,
            }
            for c in markdown_chunks
        ]
        # One vector per question wording, so every variation can match (replica
        # embeds the question text only, never the answer).
        for record in self.qa_records.values():
            for n, question in enumerate(record.match_texts):
                rows.append(
                    {
                        "id": f"{record.qa_id}::q{n}", "source_type": "excel", "chunk_id": record.qa_id,
                        "source_file": f"{record.level}.xlsx", "level": record.level,
                        "full_context_path": record.canonical_question,
                        "qa_id": record.qa_id, "question": question, "text": record.answer,
                        "chunk_index": n, "total_chunks": len(record.match_texts),
                        "_embed": question,
                    }
                )

        if rows:
            logger.info(
                "Embedding %d vector(s): %d Markdown chunk(s) + %d Excel question(s) from %d Q&A row(s) ...",
                len(rows), len(markdown_chunks), len(rows) - len(markdown_chunks), len(self.qa_records),
            )
            embeddings = embed([row.pop("_embed") for row in rows])
            for row, vector in zip(rows, embeddings):
                row["vector"] = vector.tolist()
            milvus_store.insert_rows(rows)
            logger.info("Milvus insert complete: %d vector(s) stored in '%s'", len(rows), milvus_store.COLLECTION_NAME)

        self._bm25: dict[str, tuple[BM25Okapi, list[MarkdownChunk]]] = {}
        for source in SOURCES:
            source_chunks = [c for c in self.chunks if self._source_type[c.chunk_id] == source]
            if source_chunks:
                corpus = [_tokenize(f"{c.embed_text} {c.keywords}") for c in source_chunks]
                self._bm25[source] = (BM25Okapi(corpus), source_chunks)
            logger.info("BM25 keyword index: %d %s item(s)", len(source_chunks), source)
        logger.info("Knowledge index ready (Excel + Markdown in one collection).")

    def source_type(self, chunk_id: str) -> str:
        return self._source_type.get(chunk_id, "markdown")

    def _candidates(self, query: str, query_vector: list[float], source: str) -> tuple[list[str], dict[str, float]]:
        hits = milvus_store.search(query_vector, top_k=CANDIDATES_PER_SOURCE * 3, source_type=source)
        vector_ranking: list[str] = []
        best_vector: dict[str, float] = {}
        for hit in hits:
            chunk_id = hit["chunk_id"]
            if chunk_id not in best_vector:
                vector_ranking.append(chunk_id)
            best_vector[chunk_id] = max(best_vector.get(chunk_id, -1.0), float(hit["vector_score"]))

        bm25_ranking: list[str] = []
        if source in self._bm25:
            bm25, source_chunks = self._bm25[source]
            scores = bm25.get_scores(_tokenize(query))
            order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            bm25_ranking = [source_chunks[i].chunk_id for i in order[: CANDIDATES_PER_SOURCE * 2] if scores[i] > 0]

        fused = _reciprocal_rank_fusion([vector_ranking, bm25_ranking])
        top_ids = sorted(fused, key=fused.get, reverse=True)[:CANDIDATES_PER_SOURCE]
        return [cid for cid in top_ids if cid in self._chunks_by_id], best_vector

    def search(self, query: str) -> RagResult:
        if not self.chunks:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        query_vector = embed_query([query])[0].tolist()
        candidate_ids: list[str] = []
        best_vector: dict[str, float] = {}
        for source in SOURCES:
            ids, vectors = self._candidates(query, query_vector, source)
            candidate_ids.extend(ids)
            best_vector.update(vectors)

        if not candidate_ids:
            return RagResult(has_evidence=False, chunks=[], scores=[])

        candidates = [self._chunks_by_id[cid] for cid in candidate_ids]
        rerank_scores = rerank(query, [c.text for c in candidates])
        ranked = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)

        best_score_by_source: dict[str, float] = {}
        for chunk, score in ranked:
            best_score_by_source.setdefault(self.source_type(chunk.chunk_id), float(score))

        top = ranked[:TOP_K_RERANKED]

        # Guaranteed include: a near-exact vector match the reranker pushed out
        # of the finalists is appended, never dropped (replica §7 step 8).
        if best_vector:
            nearest_id = max(best_vector, key=best_vector.get)
            finalist_ids = {c.chunk_id for c, _ in top}
            if best_vector[nearest_id] >= GUARANTEED_INCLUDE_VECTOR_SCORE and nearest_id not in finalist_ids:
                rescued = next(((c, s) for c, s in ranked if c.chunk_id == nearest_id), None)
                if rescued:
                    top.append((rescued[0], max(rescued[1], EVIDENCE_THRESHOLD)))

        if not top or top[0][1] < EVIDENCE_THRESHOLD:
            return RagResult(has_evidence=False, chunks=[], scores=[], best_score_by_source=best_score_by_source)

        chunks: list[MarkdownChunk] = []
        scores: list[float] = []
        running_chars = 0
        for chunk, score in top:
            if score < EVIDENCE_THRESHOLD:
                continue
            if chunks and running_chars + len(chunk.text) > CONTEXT_CHAR_BUDGET:
                break
            chunks.append(chunk)
            scores.append(float(score))
            running_chars += len(chunk.text)

        return RagResult(
            has_evidence=True,
            chunks=chunks,
            scores=scores,
            source_types=[self.source_type(c.chunk_id) for c in chunks],
            best_score_by_source=best_score_by_source,
        )


_index: RagIndex | None = None


def get_rag_index() -> RagIndex:
    global _index
    if _index is None:
        _index = RagIndex()
    return _index
