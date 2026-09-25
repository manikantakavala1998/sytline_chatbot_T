"""Initial LLM-based hierarchical classifier and three-source router.

The LLM may select only taxonomy values and approved tool candidates. A
deterministic classifier is both a fallback and the path for trivial
conversation. Final route policy is enforced in code, never by a prompt.
"""

import json
import re

from openai import OpenAI

from backend.app.classification.small_talk import chitchat_kind, parse_greeting
from backend.app.classification.taxonomy import (
    ComplexityLabel,
    EmotionLabel,
    IntentLabel,
    QueryClassification,
    QueryTransformResult,
    RouteLabel,
)
from backend.app.config import settings
from backend.app.context.manager import RequestContext
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)
_client: OpenAI | None = None

# Candidate names only. Phase 4 owns the actual registry and execution.
APPROVED_TOOL_CANDIDATES = {
    "get_customer_balance",
    "get_order_status",
    "list_open_orders",
    "list_overdue_invoices",
    "open_form",
    "open_record",
}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.orchestrator_timeout_seconds,
            max_retries=1,
        )
    return _client


def _complexity(query: str, subqueries: list[str]) -> ComplexityLabel:
    text = query.lower()
    if subqueries:
        return ComplexityLabel.MULTI_PART
    if re.search(r"\b(?:compare|difference|versus|vs\.?|better than)\b", text):
        return ComplexityLabel.COMPARISON
    if re.search(r"\b(?:why|root cause|keeps failing|not working|won't|cannot)\b", text):
        return ComplexityLabel.ROOT_CAUSE
    if re.search(r"\b(?:calculate|total|sum|percentage|how much)\b", text):
        return ComplexityLabel.CALCULATION
    if re.search(r"\b(?:what if|suppose|hypothetical|scenario)\b", text):
        return ComplexityLabel.HYPOTHETICAL
    if re.search(r"\b(?:except|unless|negative|exclude|not when)\b", text):
        return ComplexityLabel.NEGATIVE_EXCEPTION
    if re.search(r"\b(?:steps?|process|workflow|how (?:do|can|to))\b", text):
        return ComplexityLabel.PROCESS_WORKFLOW
    return ComplexityLabel.DIRECT


def _emotion(query: str) -> EmotionLabel:
    text = query.lower()
    if re.search(r"\b(?:again|still|already told|third time|keeps happening)\b", text):
        return EmotionLabel.PERSISTENT
    if re.search(r"\b(?:angry|furious|ridiculous|useless|terrible|damn)\b", text):
        return EmotionLabel.FRUSTRATED
    if re.search(r"\b(?:complaint|unacceptable|not satisfied)\b", text):
        return EmotionLabel.COMPLAINT
    if re.search(r"\b(?:confused|don't understand|unclear|not sure)\b", text):
        return EmotionLabel.CONFUSED
    return EmotionLabel.NORMAL


def _heuristic_classification(
    transformed: QueryTransformResult,
    context: RequestContext,
) -> QueryClassification:
    query = transformed.rewritten_query
    text = query.lower().strip(" !?.")
    complexity = _complexity(query, transformed.subqueries)
    emotion = _emotion(query)

    intent = IntentLabel.UNKNOWN
    route = RouteLabel.MARKDOWN_RAG
    sub_intent: str | None = None
    tool_candidate: str | None = None
    operation = "READ"

    greeting = parse_greeting(query)
    small_talk = chitchat_kind(query)
    if greeting:
        intent, route = IntentLabel.GREETING, RouteLabel.DIRECT_RESPONSE
        sub_intent = greeting.key + ("+wellbeing" if greeting.wellbeing else "")
    elif small_talk:
        intent, route, sub_intent = IntentLabel.CHITCHAT, RouteLabel.DIRECT_RESPONSE, small_talk
    elif re.search(r"\b(?:create|add|update|change|delete|release|approve|post)\b", text):
        intent, route = IntentLabel.ACTION, RouteLabel.ACTION
        operation_match = re.search(r"\b(create|add|update|change|delete|release|approve|post)\b", text)
        operation = (operation_match.group(1).upper() if operation_match else "EXECUTE")
        operation = {"ADD": "INSERT", "CREATE": "INSERT", "CHANGE": "UPDATE"}.get(operation, operation)
    elif re.search(r"\b(?:open|navigate|go to|take me to)\b", text):
        intent, route = IntentLabel.NAVIGATION, RouteLabel.NAVIGATION
        tool_candidate = "open_record" if transformed.entities.get("identifier") else "open_form"
        operation = "EXECUTE"
    elif re.search(r"\b(?:show|list|get|display|check)\b", text) and re.search(
        r"\b(?:balance|current|status|open orders?|overdue invoices?|inventory|production)\b", text
    ):
        intent, route = IntentLabel.LIVE_DATA, RouteLabel.LIVE_DATA
        if "balance" in text:
            tool_candidate = "get_customer_balance"
        elif "order" in text and "status" in text:
            tool_candidate = "get_order_status"
        elif "open order" in text:
            tool_candidate = "list_open_orders"
        elif "overdue invoice" in text:
            tool_candidate = "list_overdue_invoices"
    elif re.search(r"\b(?:why|error|issue|problem|not working|won't|cannot|failed|troubleshoot)\b", text):
        intent, route = IntentLabel.TROUBLESHOOTING, RouteLabel.MARKDOWN_RAG
    elif re.search(r"\b(?:compare|analy[sz]e|trend|summary across)\b", text):
        intent, route = IntentLabel.ANALYSIS, RouteLabel.LLM_REASONING
    elif re.search(r"\b(?:permission|role access|authorization|security setting)\b", text):
        intent, route = IntentLabel.SECURITY_HELP, RouteLabel.MARKDOWN_RAG
    elif re.search(r"\b(?:field|property|column)\b", text):
        intent, route = IntentLabel.HELP_FIELD, RouteLabel.MARKDOWN_RAG
    elif re.search(r"\b(?:screen|form)\b", text):
        intent, route = IntentLabel.HELP_SCREEN, RouteLabel.MARKDOWN_RAG
    elif complexity == ComplexityLabel.PROCESS_WORKFLOW:
        intent, route = IntentLabel.HELP_PROCESS, RouteLabel.MARKDOWN_RAG
    elif re.search(r"\b(?:feedback|suggestion)\b", text):
        intent, route = IntentLabel.FEEDBACK, RouteLabel.DIRECT_RESPONSE
    elif emotion in {EmotionLabel.COMPLAINT, EmotionLabel.FRUSTRATED, EmotionLabel.PERSISTENT}:
        intent, route = IntentLabel.COMPLAINT, RouteLabel.DIRECT_RESPONSE
    elif re.search(r"\b(?:what is|what are|define|explain|meaning of|help with)\b", text):
        intent = IntentLabel.HELP_GENERIC
        route = RouteLabel.FAST_QA if complexity == ComplexityLabel.DIRECT else RouteLabel.MARKDOWN_RAG

    entity_names = transformed.entities.get("business_entity", [])
    return QueryClassification(
        intent=intent,
        sub_intent=sub_intent,
        module=context.ui.module,
        form=context.ui.form,
        field=context.ui.field,
        entity=entity_names[0] if entity_names else context.record.record_type,
        operation=operation,
        complexity=complexity,
        emotion=emotion,
        route=route,
        tool_candidate=tool_candidate,
        confidence=0.78 if intent != IntentLabel.UNKNOWN else 0.5,
        reasoning_summary="deterministic_fallback",
    )


def _enum_values(enum_type: type) -> str:
    return ", ".join(item.value for item in enum_type)


def _llm_classification(
    transformed: QueryTransformResult,
    context: RequestContext,
) -> QueryClassification:
    response = _get_client().chat.completions.create(
        model=settings.orchestrator_model,
        temperature=0,
        max_tokens=420,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You classify and route safe, in-scope SyteLine/Infor CSI requests. Do not answer them. "
                    "Return one JSON object with: intent, sub_intent, module, form, field, entity, operation, "
                    "complexity, emotion, route, tool_candidate, confidence, reasoning_summary. "
                    f"Intent values: {_enum_values(IntentLabel)}. "
                    f"Complexity values: {_enum_values(ComplexityLabel)}. "
                    f"Emotion values: {_enum_values(EmotionLabel)}. "
                    f"Route values: {_enum_values(RouteLabel)}. "
                    f"tool_candidate must be null or one of: {', '.join(sorted(APPROVED_TOOL_CANDIDATES))}. "
                    "Use FAST_QA only for simple definitions. Use MARKDOWN_RAG for screens, fields, processes, "
                    "and troubleshooting. Current balances/status/open records are LIVE_DATA. Open/go-to is "
                    "NAVIGATION. A request for the assistant to perform a write/release/approve/post is ACTION; "
                    "a question about HOW to do it (\"how do I / how to / steps to create a quote\") is "
                    "HELP_PROCESS, and a problem the user wants help fixing (\"order blocked by credit, "
                    "fix?\", \"why can't I ...\") is TROUBLESHOOTING. Never invent a tool name. Keep "
                    "reasoning_summary under 12 words."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        # The user's own (cleaned) question decides the intent. The expanded /
                        # terminology search text can read like a command ("Create and issue a
                        # quotation") and was misread as an ACTION request.
                        "query": transformed.rewritten_query,
                        "subqueries": transformed.subqueries,
                        "entities": transformed.entities,
                        "context": {
                            "module": context.ui.module,
                            "form": context.ui.form,
                            "field": context.ui.field,
                            "record_type": context.record.record_type,
                            "has_selected_record": bool(context.record.record_id),
                        },
                    }
                ),
            },
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    classification = QueryClassification.model_validate(payload)
    if classification.tool_candidate not in APPROVED_TOOL_CANDIDATES:
        classification.tool_candidate = None
    return classification


# Analysis that needs real ERP figures ("sales trend this quarter", "how many overdue invoices")
# waits for the Phase 4 live-data connector. Analysis of concepts ("difference between an estimate
# and a quotation", "compare lead and opportunity") is answered from the knowledge base — the LLM
# classifier labels those ANALYSIS too, and sending them to an unbuilt route answered nothing.
_LIVE_FIGURES = re.compile(
    r"\b(?:trend|total|totals|how many|how much|count|sum|average|revenue|sales figures?|top \d+|"
    r"this (?:week|month|quarter|year)|last (?:week|month|quarter|year)|ytd|mtd|kpi|dashboard|report on)\b",
    re.IGNORECASE,
)


def _enforce_route_policy(classification: QueryClassification, query: str = "") -> QueryClassification:
    intent = classification.intent
    if intent in {IntentLabel.GREETING, IntentLabel.CHITCHAT, IntentLabel.FEEDBACK, IntentLabel.COMPLAINT}:
        classification.route = RouteLabel.DIRECT_RESPONSE
    elif intent == IntentLabel.ACTION:
        classification.route = RouteLabel.ACTION
        classification.tool_candidate = None  # Phase 3 never executes writes.
    elif intent == IntentLabel.NAVIGATION:
        classification.route = RouteLabel.NAVIGATION
    elif intent == IntentLabel.LIVE_DATA:
        classification.route = RouteLabel.LIVE_DATA
    elif intent in {
        IntentLabel.HELP_SCREEN,
        IntentLabel.HELP_FIELD,
        IntentLabel.HELP_PROCESS,
        IntentLabel.TROUBLESHOOTING,
        IntentLabel.SECURITY_HELP,
    }:
        classification.route = RouteLabel.MARKDOWN_RAG
    elif intent == IntentLabel.HELP_GENERIC and classification.complexity == ComplexityLabel.DIRECT:
        classification.route = RouteLabel.FAST_QA
    elif intent == IntentLabel.ANALYSIS:
        classification.route = RouteLabel.LLM_REASONING if _LIVE_FIGURES.search(query) else RouteLabel.MARKDOWN_RAG
    elif intent == IntentLabel.MIXED:
        classification.route = RouteLabel.RAG_IDO
    elif intent == IntentLabel.UNKNOWN:
        classification.route = RouteLabel.MARKDOWN_RAG
    return classification


def classify_and_route(
    transformed: QueryTransformResult,
    context: RequestContext,
) -> QueryClassification:
    fallback = _heuristic_classification(transformed, context)

    # Trivial conversation does not need a paid classifier call.
    if fallback.intent in {IntentLabel.GREETING, IntentLabel.CHITCHAT}:
        result = fallback
    elif settings.orchestrator_llm_enabled:
        try:
            result = _llm_classification(transformed, context)
        except Exception:
            logger.exception("event=router_llm_failed request_id=%s", context.request_id)
            result = fallback
    else:
        result = fallback

    result = _enforce_route_policy(result, transformed.rewritten_query)
    log_event(
        logger,
        "query_classification_completed",
        request_id=context.request_id,
        intent=result.intent.value,
        complexity=result.complexity.value,
        emotion=result.emotion.value,
        route=result.route.value,
        confidence=round(result.confidence, 3),
        classifier="llm" if result.reasoning_summary != "deterministic_fallback" else "fallback",
    )
    return result
