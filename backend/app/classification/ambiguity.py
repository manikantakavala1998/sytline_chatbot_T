"""Intent-agnostic ambiguity resolution.

Per the architecture decision, this runs before intent classification. It
may use trusted UI/record context, but it never uses context to grant access.
"""

import re

from backend.app.classification.taxonomy import AmbiguityLabel, AmbiguityResult
from backend.app.context.manager import RequestContext
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

_REFERENCES = re.compile(
    r"\b(?:this|that|the previous|the selected)\s+(?:customer|order|record|field|screen|form|one)\b",
    re.IGNORECASE,
)


def _replace_context_references(query: str, context: RequestContext) -> tuple[str, list[str]]:
    resolved = query
    replacements: list[str] = []

    if context.record.record_id:
        record_type = context.record.record_type or "record"
        record_value = f"{record_type} {context.record.record_id}"
        updated = re.sub(
            r"\b(?:this|that|the previous|the selected)\s+(?:customer|order|record|one)\b",
            record_value,
            resolved,
            flags=re.IGNORECASE,
        )
        if updated != resolved:
            replacements.append("record_reference")
            resolved = updated

    if context.ui.field:
        updated = re.sub(
            r"\b(?:this|that|the selected)\s+field\b",
            f"field {context.ui.field}",
            resolved,
            flags=re.IGNORECASE,
        )
        if updated != resolved:
            replacements.append("field_reference")
            resolved = updated

    if context.ui.form:
        updated = re.sub(
            r"\b(?:this|that|the selected)\s+(?:screen|form)\b",
            f"form {context.ui.form}",
            resolved,
            flags=re.IGNORECASE,
        )
        if updated != resolved:
            replacements.append("form_reference")
            resolved = updated

    return resolved, replacements


def resolve_ambiguity(query: str, context: RequestContext) -> AmbiguityResult:
    normalized = re.sub(r"\s+", " ", query).strip()
    resolved_query, replacements = _replace_context_references(normalized, context)
    identifiers = re.findall(r"\b[A-Z]{1,6}[-_]?[0-9]{2,}\b", query)

    if _REFERENCES.search(resolved_query):
        result = AmbiguityResult(
            label=AmbiguityLabel.REFERENTIAL,
            resolved=False,
            resolved_query=None,
            clarification_question=(
                "Which customer, order, record, field, or screen do you mean? "
                "Please select it in SyteLine or provide its identifier."
            ),
            reason="reference_missing_from_context",
        )
    elif len(set(identifiers)) > 1 and re.search(r"\bor\b", normalized, re.IGNORECASE) and not re.search(
        r"\bcompare\b", normalized, re.IGNORECASE
    ):
        result = AmbiguityResult(
            label=AmbiguityLabel.MULTIPLE_ENTITY,
            resolved=False,
            clarification_question="I found multiple record identifiers. Which single record should I use?",
            reason="multiple_entity_candidates",
        )
    elif re.search(
        r"\b(?:i do not know|i don't know|without)\b.{0,35}\b(?:which|customer id|order id|record id)\b",
        normalized,
        re.IGNORECASE,
    ):
        result = AmbiguityResult(
            label=AmbiguityLabel.UNANSWERABLE,
            resolved=False,
            clarification_question=(
                "I can’t identify the required record safely. Please select the record in SyteLine "
                "or provide its identifier."
            ),
            reason="required_identifier_unavailable",
        )
    elif re.fullmatch(r"(?:what|why|how|where|help|show me|open it|do it)[?!. ]*", normalized, re.IGNORECASE):
        result = AmbiguityResult(
            label=AmbiguityLabel.MISSING_TOPIC,
            resolved=False,
            clarification_question="What SyteLine topic, screen, record, or process do you need help with?",
            reason="topic_missing",
        )
    elif re.search(r"\b(?:create|add|release|approve|delete)\b", normalized, re.IGNORECASE) and re.search(
        r"\b(?:delete|cancel|undo|reject)\b", normalized, re.IGNORECASE
    ):
        result = AmbiguityResult(
            label=AmbiguityLabel.CONTRADICTORY,
            resolved=False,
            clarification_question="Your request contains conflicting actions. Which single action should be considered?",
            reason="conflicting_operations",
        )
    elif re.search(r"\b(?:latest|newest|current)\s+(?:version|release|documentation|manual)\b", normalized, re.IGNORECASE):
        result = AmbiguityResult(
            label=AmbiguityLabel.VERSION_RECENCY,
            resolved=False,
            clarification_question="Which SyteLine version or documentation release should I use?",
            reason="version_not_specified",
        )
    elif re.search(r"\b(?:balance|credit status|overdue invoices?)\b", normalized, re.IGNORECASE) and not (
        context.record.record_id
        or re.search(r"\b[A-Z]{1,5}[0-9]{2,}\b", query)
        or re.search(r"\b(?:for|customer)\s+[A-Za-z0-9_-]{3,}\b", query, re.IGNORECASE)
    ):
        result = AmbiguityResult(
            label=AmbiguityLabel.MISSING_DETAIL,
            resolved=False,
            clarification_question="Which customer should I use? Select a customer record or provide the customer ID.",
            reason="customer_identifier_missing",
        )
    else:
        result = AmbiguityResult(
            label=AmbiguityLabel.CLEAR,
            resolved=True,
            resolved_query=resolved_query,
            reason="resolved_from_context" if replacements else "clear",
        )

    log_event(
        logger,
        "ambiguity_resolution_completed",
        request_id=context.request_id,
        label=result.label.value,
        resolved=result.resolved,
        context_references=len(replacements),
    )
    return result
