"""
Fast Q&A retrieval — master prompt section 9:

  Question -> Normalization -> Acronym Expansion -> Synonym/Terminology
  Mapping -> Context Enrichment -> Exact Match -> Keyword/BM25 Match ->
  Embedding Similarity -> Hybrid Q&A Score -> Evidence/Match Quality Gate

Result is one of:
  FAST_QA_RESPONSE  -> strong match, answer directly from the Q&A data
  MARKDOWN_RAG       -> weak/no match, hand off to document search (not built yet)
  CLARIFY            -> multiple close candidates, ask the user which one they mean

The threshold numbers below are starting points, not tuned values — the
master prompt is explicit that these must come from real evaluation later,
not be guessed once and trusted forever.
"""

import re
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from backend.app.models.embeddings import embed, embed_query
from backend.app.qa.glossary import GlossaryEntry, expand_query, load_glossary
from backend.app.qa.loader import QARecord, load_qa_records

STRONG_MATCH_THRESHOLD = 0.80
WEAK_MATCH_THRESHOLD = 0.45
CLARIFY_GAP_RATIO = 0.92  # 2nd-best score this close to the best = too close to call


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> list[str]:
    return _normalize(text).split()


@dataclass
class QAMatch:
    route: str
    record: QARecord | None
    score: float
    candidates: list[tuple[QARecord, float]]


class QAIndex:
    def __init__(self) -> None:
        self.records: list[QARecord] = load_qa_records()
        self.glossary: list[GlossaryEntry] = load_glossary()

        # one search-corpus entry per (record, match_text) pair, so a
        # record with several question variations gets several chances to match
        self._entry_records: list[QARecord] = []
        self._entry_texts: list[str] = []
        for record in self.records:
            for text in record.match_texts:
                self._entry_records.append(record)
                self._entry_texts.append(text)

        tokenized_corpus = [_tokenize(t) for t in self._entry_texts]
        self._bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        self._entry_embeddings = embed(self._entry_texts)

    def search(self, raw_query: str) -> QAMatch:
        if not self.records:
            return QAMatch(route="MARKDOWN_RAG", record=None, score=0.0, candidates=[])

        normalized_query = _normalize(raw_query)
        enriched_query = expand_query(raw_query, self.glossary)

        # 1. exact match short-circuits everything else
        for record in self.records:
            if any(_normalize(t) == normalized_query for t in record.match_texts):
                return QAMatch(route="FAST_QA_RESPONSE", record=record, score=1.0, candidates=[(record, 1.0)])

        # 2. BM25 (keyword) score, best entry per qa_id, normalized 0-1
        bm25_scores = self._bm25.get_scores(_tokenize(enriched_query))
        max_bm25 = max(float(bm25_scores.max()), 1e-6)
        bm25_by_qa_id: dict[str, float] = {}
        for record, raw_score in zip(self._entry_records, bm25_scores):
            normalized_score = raw_score / max_bm25
            bm25_by_qa_id[record.qa_id] = max(bm25_by_qa_id.get(record.qa_id, 0.0), normalized_score)

        # 3. embedding similarity (cosine == dot product, embeddings are normalized)
        query_embedding = embed_query([enriched_query])[0]
        similarities = self._entry_embeddings @ query_embedding
        embedding_by_qa_id: dict[str, float] = {}
        for record, similarity in zip(self._entry_records, similarities):
            embedding_by_qa_id[record.qa_id] = max(embedding_by_qa_id.get(record.qa_id, 0.0), float(similarity))

        # 4. hybrid score
        hybrid_by_qa_id = {
            record.qa_id: 0.4 * bm25_by_qa_id.get(record.qa_id, 0.0) + 0.6 * embedding_by_qa_id.get(record.qa_id, 0.0)
            for record in self.records
        }
        ranked = sorted(self.records, key=lambda r: hybrid_by_qa_id[r.qa_id], reverse=True)
        candidates = [(r, hybrid_by_qa_id[r.qa_id]) for r in ranked[:3]]
        best_record, best_score = candidates[0]

        # 5. evidence / match quality gate
        if best_score < WEAK_MATCH_THRESHOLD:
            return QAMatch(route="MARKDOWN_RAG", record=None, score=best_score, candidates=candidates)

        if best_score < STRONG_MATCH_THRESHOLD and len(candidates) > 1:
            second_score = candidates[1][1]
            if second_score >= best_score * CLARIFY_GAP_RATIO:
                return QAMatch(route="CLARIFY", record=None, score=best_score, candidates=candidates)

        if best_score >= STRONG_MATCH_THRESHOLD:
            return QAMatch(route="FAST_QA_RESPONSE", record=best_record, score=best_score, candidates=candidates)

        return QAMatch(route="MARKDOWN_RAG", record=None, score=best_score, candidates=candidates)


_index: QAIndex | None = None


def get_qa_index() -> QAIndex:
    global _index
    if _index is None:
        _index = QAIndex()
    return _index
