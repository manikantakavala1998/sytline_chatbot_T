"""Selective query preprocessing for routing and retrieval."""

import re
import unicodedata
from functools import lru_cache

from backend.app.classification.taxonomy import QueryTransformResult
from backend.app.context.manager import RequestContext
from backend.app.qa.glossary import GlossaryEntry, expand_query, load_glossary
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

_SPELLING = {
    "costumer": "customer",
    "custmer": "customer",
    "qoute": "quote",
    "qoutation": "quotation",
    "recievable": "receivable",
    "shipement": "shipment",
    "inovice": "invoice",
    "payement": "payment",
}


@lru_cache(maxsize=1)
def _glossary() -> tuple[GlossaryEntry, ...]:
    return tuple(load_glossary())


def _normalize(query: str) -> str:
    text = unicodedata.normalize("NFKC", query)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fix_spelling(query: str) -> tuple[str, bool]:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        word = match.group(0)
        replacement = _SPELLING.get(word.lower())
        if replacement is None:
            return word
        changed = True
        return replacement.capitalize() if word[0].isupper() else replacement

    return re.sub(r"\b[A-Za-z]+\b", replace, query), changed


def _extract_entities(query: str) -> dict[str, list[str]]:
    lowered = query.lower()
    entities: dict[str, list[str]] = {}

    business_entities = [
        "prospect",
        "lead",
        "opportunity",
        "estimate",
        "quotation",
        "customer order",
        "order line",
        "customer",
        "credit limit",
        "shipment",
        "invoice",
        "payment",
        "receivable",
    ]
    found = [name for name in business_entities if re.search(rf"\b{re.escape(name)}s?\b", lowered)]
    if found:
        entities["business_entity"] = found

    identifiers = re.findall(r"\b[A-Z]{1,6}[-_]?[0-9]{2,}\b", query)
    if identifiers:
        entities["identifier"] = list(dict.fromkeys(identifiers))

    return entities


def _decompose(query: str) -> list[str]:
    parts = re.split(
        r"(?:\?\s+|;\s+|\band\b(?=\s+(?:what|how|why|show|list|open|create|update|compare)\b))",
        query,
        flags=re.IGNORECASE,
    )
    cleaned = [part.strip(" ,?.") for part in parts if part.strip(" ,?.")]
    return cleaned if len(cleaned) > 1 else []


def transform_query(query: str, context: RequestContext) -> QueryTransformResult:
    transformations: list[str] = []
    normalized = _normalize(query)
    if normalized != query:
        transformations.append("unicode_whitespace_normalization")

    rewritten, spelling_changed = _fix_spelling(normalized)
    if spelling_changed:
        transformations.append("spell_normalization")

    expanded = expand_query(rewritten, list(_glossary()))
    if expanded != rewritten:
        transformations.append("business_glossary_expansion")

    entities = _extract_entities(expanded)
    if entities:
        transformations.append("entity_extraction")

    subqueries = _decompose(rewritten)
    if subqueries:
        transformations.append("query_decomposition")

    result = QueryTransformResult(
        normalized_query=normalized,
        rewritten_query=rewritten,
        expanded_query=expanded,
        entities=entities,
        subqueries=subqueries,
        transformations=transformations,
    )
    log_event(
        logger,
        "query_transformation_completed",
        request_id=context.request_id,
        transformations=",".join(transformations) or "none",
        entity_groups=len(entities),
        subqueries=len(subqueries),
    )
    return result

