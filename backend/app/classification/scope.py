"""Five-label scope classifier with a binary downstream gate."""

import json
import re
from functools import lru_cache

from openai import OpenAI

from backend.app.classification.taxonomy import ScopeLabel, ScopeResult
from backend.app.config import settings
from backend.app.context.manager import RequestContext
from backend.app.qa.glossary import load_glossary
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)
_client: OpenAI | None = None

_SYTELINE_TERMS = {
    "syteline",
    "infor csi",
    "cloudsuite industrial",
    "ido",
    "prospect",
    "lead",
    "opportunity",
    "estimate",
    "quotation",
    "quote",
    "customer",
    "customer order",
    "order line",
    "credit limit",
    "shipment",
    "invoice",
    "payment",
    "receivable",
    "form",
    "field",
    "site",
    "configuration",
    "permission",
}
_COMPETITORS = re.compile(r"\b(?:sap|oracle ebs|oracle erp|netsuite|dynamics 365|epicor|odoo)\b", re.IGNORECASE)
_GENERAL = re.compile(
    r"\b(?:weather|temperature|capital of|president of|stock price|recipe|cook|movie|sports score|"
    r"football|cricket|joke|poem|write a story|translate this|quantum physics)\b",
    re.IGNORECASE,
)
_CHITCHAT = re.compile(
    r"^(?:hi|hello|hey|good (?:morning|afternoon|evening)|how are you|how(?:'s| is) it going|"
    r"what(?:'s| is) up|who are you|what can you do|nice to meet you|ok(?:ay)?|cool|"
    r"thanks?|thank you|bye|goodbye)[?!. ]*$",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _business_terms() -> set[str]:
    terms = set(_SYTELINE_TERMS)
    for entry in load_glossary():
        terms.add(entry.canonical_term.lower())
        terms.update(value.lower() for value in entry.synonyms)
        if entry.abbreviation:
            terms.add(entry.abbreviation.lower())
    return terms


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.orchestrator_timeout_seconds,
            max_retries=1,
        )
    return _client


def _llm_scope(query: str, context: RequestContext) -> ScopeResult:
    if not settings.orchestrator_llm_enabled:
        raise RuntimeError("orchestrator LLM is disabled")

    labels = ", ".join(label.value for label in ScopeLabel)
    response = _get_client().chat.completions.create(
        model=settings.orchestrator_model,
        temperature=0,
        max_tokens=140,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify whether a user message belongs to a SyteLine/Infor CSI "
                    "Prospect-to-Cash assistant. Return JSON only with label, confidence, reason. "
                    f"Labels: {labels}. Greetings and conversational thanks are SYTELINE_RELATED "
                    "because they are part of an assistant conversation. Do not answer the question."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "message": query,
                        "current_module": context.ui.module,
                        "current_form": context.ui.form,
                        "current_field": context.ui.field,
                    }
                ),
            },
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    label = ScopeLabel(payload.get("label", ScopeLabel.IRRELEVANT.value))
    return ScopeResult(
        label=label,
        in_scope=label == ScopeLabel.SYTELINE_RELATED,
        confidence=float(payload.get("confidence", 0.65)),
        reason=str(payload.get("reason", "semantic_scope_classification"))[:160],
    )


def classify_scope(query: str, context: RequestContext) -> ScopeResult:
    normalized = re.sub(r"\s+", " ", query.lower()).strip()

    if _CHITCHAT.match(normalized):
        result = ScopeResult(
            label=ScopeLabel.SYTELINE_RELATED,
            in_scope=True,
            confidence=1.0,
            reason="assistant_conversation",
        )
    elif _COMPETITORS.search(normalized):
        result = ScopeResult(
            label=ScopeLabel.COMPETITOR_OTHER_ERP,
            in_scope=False,
            confidence=0.98,
            reason="other_erp_detected",
        )
    elif _GENERAL.search(normalized):
        result = ScopeResult(
            label=ScopeLabel.GENERAL_KNOWLEDGE,
            in_scope=False,
            confidence=0.98,
            reason="general_knowledge_topic",
        )
    elif any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in _business_terms()):
        result = ScopeResult(
            label=ScopeLabel.SYTELINE_RELATED,
            in_scope=True,
            confidence=0.96,
            reason="syteline_business_term",
        )
    elif (context.ui.module or context.ui.form or context.ui.field or context.record.record_id) and re.search(
        r"\b(?:this|that|screen|record|field|what|why|how|show|open|help|error|status)\b", normalized
    ):
        result = ScopeResult(
            label=ScopeLabel.SYTELINE_RELATED,
            in_scope=True,
            confidence=0.86,
            reason="current_syteline_ui_context",
        )
    elif not re.search(r"[a-zA-Z]{2,}", normalized):
        result = ScopeResult(
            label=ScopeLabel.IRRELEVANT,
            in_scope=False,
            confidence=0.95,
            reason="no_meaningful_language",
        )
    else:
        if not settings.orchestrator_llm_enabled:
            result = ScopeResult(
                label=ScopeLabel.SYTELINE_RELATED if (context.ui.module or context.ui.form) else ScopeLabel.OFF_TOPIC,
                in_scope=bool(context.ui.module or context.ui.form),
                confidence=0.55,
                reason="context_fallback_classifier_disabled",
            )
        else:
            try:
                result = _llm_scope(query, context)
            except Exception:
                logger.exception("event=scope_classifier_failed request_id=%s", context.request_id)
                result = ScopeResult(
                    label=ScopeLabel.OFF_TOPIC,
                    in_scope=False,
                    confidence=0.55,
                    reason="scope_classifier_unavailable",
                )

    log_event(
        logger,
        "scope_classification_completed",
        request_id=context.request_id,
        label=result.label.value,
        in_scope=result.in_scope,
        confidence=round(result.confidence, 3),
    )
    return result
