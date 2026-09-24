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


# Retrieval-only rewrites (the answer model still sees the user's own words).
# The knowledge base says "process", never "lifecycle": "Explain the invoice
# lifecycle" found no evidence while "Explain the invoice process" scored 2.0.
_PROCESS_SYNONYMS = re.compile(r"\blife[\s-]?cycle\b|\bjourney\b", flags=re.IGNORECASE)

# Polite openers carry no search meaning but pushed the reranker score below the
# evidence cutoff ("Can you explain the invoice lifecycle?" -> no answer).
_POLITE_OPENER = re.compile(
    r"^(?:(?:can|could|would|will) you(?: please)?|please|kindly|"
    r"i (?:want|would like|need) to know|(?:can|could|may) i (?:know|ask)|tell me)\b[\s,]*",
    flags=re.IGNORECASE,
)

# A greeting in front of a real question ("good morning, how do I ...") dragged
# the retrieval score from 2.9 to -1.0, so it is removed before search and
# classification, and remembered so the answer can greet back.
_LEADING_GREETING = re.compile(
    r"^(hi|hello|hey|good morning|good afternoon|good evening)"
    r"(?:\s+(?:there|team|everyone|all))?[\s,!.:;-]+(?=\S)",
    flags=re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _glossary() -> tuple[GlossaryEntry, ...]:
    return tuple(load_glossary())


def _strip_leading_greeting(query: str) -> tuple[str, str | None]:
    match = _LEADING_GREETING.match(query)
    if not match:
        return query, None
    remainder = query[match.end():].strip()
    if len(remainder.split()) < 2:
        return query, None
    return remainder, match.group(1).lower().replace(" ", "_")


def _expand_for_retrieval(query: str) -> str:
    text = query
    while True:
        stripped = _POLITE_OPENER.sub("", text, count=1)
        if stripped == text or len(stripped.split()) < 2:
            break
        text = stripped
    text = _PROCESS_SYNONYMS.sub("process", text)
    return expand_query(text, list(_glossary()))


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

    without_greeting, leading_greeting = _strip_leading_greeting(normalized)
    if leading_greeting:
        transformations.append("leading_greeting_removed")

    rewritten, spelling_changed = _fix_spelling(without_greeting)
    if spelling_changed:
        transformations.append("spell_normalization")

    expanded = _expand_for_retrieval(rewritten)
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
        expanded_subqueries=[_expand_for_retrieval(part) for part in subqueries],
        leading_greeting=leading_greeting,
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

