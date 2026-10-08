"""LangGraph workflow for Phase 3.

SyteLine session validation and normalized context construction remain at
the trusted API boundary. The graph owns every AI/query step after that
boundary: security -> scope -> ambiguity -> transformation -> hierarchical
classification -> code-enforced routing -> route execution.
"""

import re

from langgraph.graph import END, START, StateGraph

from backend.app.authorization.resolver import resolve_permission
from backend.app.classification.ambiguity import GENERAL_ANSWER_REASON, resolve_ambiguity
from backend.app.classification.conversation import MessageKind, analyze_message
from backend.app.classification.query_transformer import expand_for_retrieval, transform_query
from backend.app.classification.router import classifier_source, classify_and_route
from backend.app.classification.scope import classify_scope
from backend.app.classification.small_talk import greeting_key_from_label, parse_greeting
from backend.app.classification.taxonomy import EmotionLabel, IntentLabel, QueryClassification, RouteLabel
from backend.app.config import settings
from backend.app.history.store import Turn
from backend.app.orchestration.state import ChatWorkflowState, WorkflowResult
from backend.app.orchestration.step_trace import traced
from backend.app.utils import trace
from backend.app.qa.retriever import get_qa_index
from backend.app.quality import tone
from backend.app.quality.answer_validator import LEAK_REASONS, validate_answer
from backend.app.escalation.policy import decide_escalation
from backend.app.quality.tone import apply_tone, rules_mood, strongest, tone_instruction
from backend.app.rag.answer_service import generate_answer
from backend.app.rag.retriever import CONTEXT_CHAR_BUDGET, TOP_K_RERANKED, get_rag_index
from backend.app.security.input_gate import evaluate_security
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

SECURITY_BLOCK_MESSAGE = (
    "I can’t help with requests that attempt to bypass security, expose restricted data, "
    "or override system instructions."
)
OUT_OF_SCOPE_MESSAGE = "This question is outside the scope of the SyteLine assistant."

_GREETING_ECHO = {
    "good_morning": "Good morning!",
    "good_afternoon": "Good afternoon!",
    "good_evening": "Good evening!",
    "good_night": "Good night!",
    "hello": "Hello!",
}
_WELLBEING_REPLY = "I’m doing well, thank you for asking!"
MULTI_QUESTION_CONTEXT_CHARS = 9000

# Show a curated Excel answer verbatim only when BOTH signals agree:
#   question match (Fast Q&A hybrid of BM25 + embeddings over question + variations) >= 0.90
#   AND the cross-encoder ranks that same row #1 among 10 Excel + 10 Markdown candidates.
# Measured on the knowledge-derived rows: correct matches scored 0.95-1.00, near-miss wrong
# rows 0.88-0.89 ("What is a customer order?" -> order-LINE row). Starter value — re-check
# with the evaluation set before production (master prompt section 33).
EXCEL_VERBATIM_MATCH_SCORE = 0.90
# How much better the SyteLine-terms rewording must match an Excel row to beat the user's own words.
TERMINOLOGY_MATCH_MARGIN = 0.05
# An ERP abbreviation in the question (SO, CO, RMA, A/R, POs) — then the answer model also gets the
# SyteLine-terms wording, because it can't expand the abbreviation itself.
_ABBREVIATION = re.compile(r"\b(?:[A-Z]{2,5}s?|[A-Z]/[A-Z])\b")
# A simple definition question ("what is customer", "what does CO mean") gets a one-or-two-sentence
# answer. Questions about how, why, steps, differences or what happens are never cut short.
_DEFINITION = re.compile(
    r"^\s*(?:what\s+(?:is|are)|what'?s|whats|define|definition\s+of|meaning\s+of|what\s+does\s+.+\s+mean)\b",
    re.IGNORECASE,
)
_NEEDS_DETAIL = re.compile(
    r"\b(?:how|why|when|difference|differ|between|compare|vs|versus|steps?|process|lifecycle|flow|explain|"
    r"happens?|list|all|types?|examples?)\b",
    re.IGNORECASE,
)
BRIEF_MAX_WORDS = 10


def is_definition_question(question: str, operation: str | None = None) -> bool:
    if _NEEDS_DETAIL.search(question) or len(question.split()) > BRIEF_MAX_WORDS:
        return False
    return bool(_DEFINITION.match(question)) or (operation or "").strip().lower() == "definition"


def _greet_back(state: ChatWorkflowState, answer: str | None) -> str | None:
    """Prefix the answer with the greeting the user opened with ("Good morning! ...")."""
    conversation = state.get("conversation")
    transformed = state.get("transformed")
    if conversation and (conversation.greeting or conversation.asked_wellbeing):
        greeting = conversation.greeting.value if conversation.greeting else None
        # A pure "how are you" already gets a wellbeing template; only add it in front of real answers.
        asked_wellbeing = conversation.asked_wellbeing and conversation.kind == MessageKind.BUSINESS
    else:
        greeting = transformed.leading_greeting if transformed else None
        asked_wellbeing = bool(transformed and transformed.leading_wellbeing)
    if not answer:
        return answer
    if not greeting:
        # "hope you're doing well! how do I ..." — no greeting word, but still answer the kindness.
        return f"{_WELLBEING_REPLY} {answer}" if asked_wellbeing else answer
    wellbeing = f" {_WELLBEING_REPLY}" if asked_wellbeing else ""
    return f"{_GREETING_ECHO.get(greeting, 'Hello!')}{wellbeing} {answer}"


def _greeting_reply(state: ChatWorkflowState) -> str | None:
    """Reply to a pure greeting, echoing its time of day and answering "how are you".

    The conversation-understanding LLM decides the greeting; the offline rules and the
    classifier's label are fallbacks for when it is unavailable."""
    conversation = state.get("conversation")
    if conversation and conversation.is_small_talk:
        if conversation.kind != MessageKind.GREETING:
            return None
        key = conversation.greeting.value if conversation.greeting else "hello"
        return _format_greeting_reply(key, conversation.asked_wellbeing)

    greeting = parse_greeting(state.get("original_query") or state["query"]) or parse_greeting(state["query"])
    classification = state.get("classification")
    label = (classification.sub_intent or "") if classification else ""
    if greeting is None:
        if not classification or classification.intent != IntentLabel.GREETING:
            return None
        key = greeting_key_from_label(label) or "hello"
        wellbeing = any(word in label.lower() for word in ("wellbeing", "how_are", "how are"))
    else:
        key, wellbeing = greeting.key, greeting.wellbeing
    return _format_greeting_reply(key, wellbeing)


def _format_greeting_reply(key: str, wellbeing: bool) -> str:
    echo = _GREETING_ECHO.get(key, "Hello!")
    if key == "good_night":
        return f"{echo} I’ll be here whenever you need help with SyteLine."
    follow = "How can I help with your SyteLine Prospect-to-Cash work" + (" today?" if key != "hello" else "?")
    return f"{echo} {_WELLBEING_REPLY + ' ' if wellbeing else ''}{follow}"


_CHITCHAT_KEYWORDS = (
    ("farewell", "farewell"),  # before "well" — "farewell" contains it
    ("bye", "farewell"),
    ("well", "wellbeing"),
    ("how_are", "wellbeing"),
    ("thank", "thanks"),
    ("ident", "identity"),
    ("who", "identity"),
    ("capab", "capabilities"),
    ("meet", "introduction"),
    ("ack", "acknowledgement"),
)


def _normalize_chitchat_sub_intent(sub_intent: str | None) -> str | None:
    """Map the LLM classifier's free-form labels (e.g. CHECK_WELLBEING) onto our reply keys."""
    if not sub_intent:
        return sub_intent
    lowered = sub_intent.lower()
    for keyword, key in _CHITCHAT_KEYWORDS:
        if keyword in lowered:
            return key
    return lowered


def _best_qa_match(transformed):
    """Match the curated Excel questions with the user's own words AND the standard-terminology
    version, keeping the better one. The user's words must stay in play: an exact match on a
    question/variation ("What is an estimate?") is lost if only the LLM's rewording is used."""
    index = get_qa_index()
    match = index.search(transformed.expanded_query)
    if transformed.terminology_query and match.score < 1.0:
        alternative = index.search(transformed.terminology_query)
        # The user's own words win unless the SyteLine-terms version is clearly better. Found with
        # the step trace: "What is an estimate?" matched KB-0052 at 0.91, the rewording "estimate
        # (quotation)" matched KB-0117 at 0.92 — a 0.01 edge picked the wrong row and lost the
        # approved answer.
        if alternative.score > match.score + TERMINOLOGY_MATCH_MARGIN:
            trace.detail(f"  → using the SyteLine-terms match {alternative.candidates[0][0].qa_id} "
                         f"({alternative.score:.2f} vs {match.score:.2f})")
            match = alternative
        elif match.candidates:
            trace.detail(f"  → keeping the user's-words match {match.candidates[0][0].qa_id} ({match.score:.2f}; "
                         f"the SyteLine-terms version needs > +{TERMINOLOGY_MATCH_MARGIN} to win)")
    return match


def _search_each_question(state: ChatWorkflowState):
    """Search every sub-question separately and interleave the evidence.

    One combined search let the dominant topic crowd out the others: "What is a
    quotation and how is an invoice created?" retrieved only invoice chunks.
    Returns (chunks, scores, source types, per-sub-question results).
    """
    transformed = state["transformed"]
    # Multi-query retrieval: a single question is searched with BOTH the user's own words and the
    # LLM's standard-terminology version, and the results are merged. Either one alone misses
    # cases — "raise the quotation" needs the terminology; "change customer payment terms" was
    # steered to the payment module by the rewrite while the answer is in the customer module.
    if transformed.expanded_subqueries:
        queries = transformed.expanded_subqueries
    elif transformed.terminology_query and transformed.terminology_query != transformed.expanded_query:
        queries = [transformed.terminology_query, transformed.expanded_query]
    else:
        queries = [transformed.expanded_query]
    index = get_rag_index()
    per_query = []
    for n, query in enumerate(queries, 1):
        kind = "sub-question" if transformed.expanded_subqueries else ("SyteLine terms" if n == 1 and len(queries) > 1
                                                                        else "user's words")
        trace.detail(f"▸ search {n}/{len(queries)} ({kind}): {trace.text(query, 160)}")
        per_query.append(index.search(query))

    if transformed.expanded_subqueries:
        # Different sub-questions: interleave so every part gets evidence.
        candidates = []
        depth = max((len(result.chunks) for result in per_query), default=0)
        for rank in range(depth):
            for result in per_query:
                if rank < len(result.chunks):
                    candidates.append((result.chunks[rank], result.scores[rank]))
        budget = MULTI_QUESTION_CONTEXT_CHARS
    else:
        # One question searched two ways. Each wording keeps its top 2 (so the shipment section
        # found only by "ship a customer order (shipment)" isn't pushed out by six generic
        # "customer order" sections from the user's wording), then the rest by score.
        best: dict[str, tuple] = {}
        for result in per_query:
            for chunk, score in zip(result.chunks, result.scores):
                if chunk.chunk_id not in best or score > best[chunk.chunk_id][1]:
                    best[chunk.chunk_id] = (chunk, score)
        guaranteed = [cid for result in per_query for cid in (c.chunk_id for c in result.chunks[:2])]
        ordered = sorted(best.values(), key=lambda pair: pair[1], reverse=True)
        picked = list(dict.fromkeys(guaranteed))
        picked += [c.chunk_id for c, _ in ordered if c.chunk_id not in picked]
        candidates = sorted((best[cid] for cid in picked[:TOP_K_RERANKED]), key=lambda pair: pair[1], reverse=True)
        budget = CONTEXT_CHAR_BUDGET

    chunks, scores, sources, seen, running_chars = [], [], [], set(), 0
    for chunk, score in candidates:
        if chunk.chunk_id in seen:
            continue
        if chunks and running_chars + len(chunk.text) > budget:
            continue
        seen.add(chunk.chunk_id)
        chunks.append(chunk)
        scores.append(score)
        sources.append(index.source_type(chunk.chunk_id))
        running_chars += len(chunk.text)
    if chunks:
        trace.detail(f"▸ evidence kept for the answer: {len(chunks)} item(s), {running_chars} chars "
                     f"(budget {budget}):")
        for n, (chunk, score, source) in enumerate(zip(chunks, scores, sources), 1):
            trace.detail(f"    {n}. {score:>6.2f}  [{source}] {index.label(chunk)}")
    else:
        trace.detail("▸ evidence kept for the answer: none above the evidence bar")
    return chunks, scores, sources, per_query


def _user_mood(state: ChatWorkflowState, classifier_mood: EmotionLabel) -> EmotionLabel:
    """The user's mood from their RAW words and the conversation, strongest signal wins.

    The classifier only sees the cleaned-up question ("!!!", CAPS and "still not working" are
    gone), so its label is used only when the conversation LLM was unavailable.
    """
    raw = state.get("original_query") or state["query"]
    rules = rules_mood(raw, state.get("history") or [])
    conversation = state.get("conversation")
    if conversation and conversation.source in ("llm", "cache"):
        return strongest(conversation.mood, rules)
    return strongest(classifier_mood, rules)


def _mood(state: ChatWorkflowState) -> EmotionLabel:
    classification = state.get("classification")
    return classification.emotion if classification else EmotionLabel.NORMAL


def _verbatim_reason(transformed, chunks, sources, qa_candidate, verbatim: bool) -> str:
    """Why the approved Excel answer was (or wasn't) shown word for word — for the trace."""
    if verbatim:
        return (f"YES — the top evidence is Excel row {qa_candidate[0]}, the same row the question matched "
                f"({qa_candidate[1]:.2f} ≥ {EXCEL_VERBATIM_MATCH_SCORE}) → approved answer, no generation")
    if transformed.subqueries:
        return "NO — several questions in one message; one approved row can't answer them all"
    if not chunks:
        return "NO — no evidence at all"
    if not qa_candidate:
        return "NO — no Excel row matched the question"
    if sources[0] != "excel":
        return f"NO — the strongest evidence is a document section, not Excel row {qa_candidate[0]}"
    if qa_candidate[0] != chunks[0].chunk_id:
        return f"NO — the top evidence is Excel row {chunks[0].chunk_id}, but the question matched {qa_candidate[0]}"
    return (f"NO — question match {qa_candidate[1]:.2f} is below {EXCEL_VERBATIM_MATCH_SCORE} "
            "→ write an answer from the evidence instead")


def _decision_trace(state: ChatWorkflowState) -> dict[str, object]:
    security = state.get("security")
    scope = state.get("scope")
    ambiguity = state.get("ambiguity")
    transformed = state.get("transformed")
    classification = state.get("classification")
    selected_route = state.get("selected_route")
    conversation = state.get("conversation")
    return {
        "security": security.label.value if security else None,
        "scope": scope.label.value if scope else None,
        "ambiguity": ambiguity.label.value if ambiguity else None,
        "intent": classification.intent.value if classification else None,
        "sub_intent": classification.sub_intent if classification else None,
        "complexity": classification.complexity.value if classification else None,
        "emotion": classification.emotion.value if classification else None,
        # "llm" (separate call), "combined" (inside the understanding call) or "rules" (LLM
        # unavailable) — the Health tab's fallback rate counts "rules".
        "classifier": classifier_source(classification) if classification else None,
        "selected_route": selected_route.value if selected_route else None,
        "tool_candidate": classification.tool_candidate if classification else None,
        "transformations": transformed.transformations if transformed else [],
        "history_turns_used": len(state.get("history") or []),
        "followup_resolved": bool(state.get("followup_resolved")),
        "message_kind": conversation.kind.value if conversation else None,
        "conversation_source": conversation.source if conversation else None,
    }


class ChatOrchestrator:
    def __init__(self) -> None:
        builder = StateGraph(ChatWorkflowState)
        builder.add_node("security_gate", traced("security_gate", self._security_node))
        builder.add_node("blocked_response", traced("blocked_response", self._blocked_response_node))
        builder.add_node("conversation_understanding", traced("conversation_understanding", self._conversation_node))
        builder.add_node("scope_check", traced("scope_check", self._scope_node))
        builder.add_node("out_of_scope_response", traced("out_of_scope_response", self._out_of_scope_node))
        builder.add_node("ambiguity_resolution", traced("ambiguity_resolution", self._ambiguity_node))
        builder.add_node("clarify_response", traced("clarify_response", self._clarify_node))
        builder.add_node("query_transformation", traced("query_transformation", self._transform_node))
        builder.add_node("query_classification", traced("query_classification", self._classification_node))
        builder.add_node("route_selection", traced("route_selection", self._route_node))
        builder.add_node("direct_response", traced("direct_response", self._direct_response_node))
        builder.add_node("fast_qa", traced("fast_qa", self._fast_qa_node))
        builder.add_node("markdown_rag", traced("markdown_rag", self._rag_node))
        builder.add_node("capability_pending", traced("capability_pending", self._capability_pending_node))

        builder.add_edge(START, "security_gate")
        builder.add_conditional_edges(
            "security_gate",
            self._after_security,
            {"blocked": "blocked_response", "safe": "conversation_understanding"},
        )
        builder.add_edge("blocked_response", END)
        builder.add_conditional_edges(
            "conversation_understanding",
            self._after_conversation,
            {"small_talk": "direct_response", "business": "scope_check"},
        )
        builder.add_conditional_edges(
            "scope_check",
            self._after_scope,
            {"out_of_scope": "out_of_scope_response", "in_scope": "ambiguity_resolution"},
        )
        builder.add_edge("out_of_scope_response", END)
        builder.add_conditional_edges(
            "ambiguity_resolution",
            self._after_ambiguity,
            {"clarify": "clarify_response", "resolved": "query_transformation"},
        )
        builder.add_edge("clarify_response", END)
        builder.add_edge("query_transformation", "query_classification")
        builder.add_edge("query_classification", "route_selection")
        builder.add_conditional_edges(
            "route_selection",
            self._dispatch_route,
            {
                "blocked": "blocked_response",
                "clarify": "clarify_response",
                "direct": "direct_response",
                "fast_qa": "fast_qa",
                "rag": "markdown_rag",
                "pending": "capability_pending",
            },
        )
        builder.add_edge("direct_response", END)
        builder.add_conditional_edges(
            "fast_qa",
            self._after_fast_qa,
            {"rag": "markdown_rag", "done": END},
        )
        builder.add_edge("markdown_rag", END)
        builder.add_edge("capability_pending", END)
        self.graph = builder.compile()

    @staticmethod
    def _security_node(state: ChatWorkflowState) -> dict:
        return {"security": evaluate_security(state["query"], state["request_id"])}

    @staticmethod
    def _after_security(state: ChatWorkflowState) -> str:
        return "safe" if state["security"].allowed else "blocked"

    @staticmethod
    def _blocked_response_node(state: ChatWorkflowState) -> dict:
        security = state.get("security")
        reason = f"security:{security.label.value}" if security and not security.allowed else "blocked"
        result = WorkflowResult(
            route="BLOCKED",
            answer=SECURITY_BLOCK_MESSAGE,
            reason=reason,
            decision_trace=_decision_trace(state),
        )
        log_event(logger, "orchestration_blocked", request_id=state["request_id"], reason=reason)
        return {"result": result}

    @staticmethod
    def _conversation_node(state: ChatWorkflowState) -> dict:
        # Security already checked the raw message; the LLM here only labels it and
        # rewrites references with topics from earlier turns that passed the same gate.
        ctx = state["context"]
        screen = {"module": ctx.ui.module, "form": ctx.ui.form, "field": ctx.ui.field,
                  "record_type": ctx.record.record_type, "has_selected_record": bool(ctx.record.record_id)}
        analysis = analyze_message(state["query"], state.get("history") or [], state["request_id"], screen=screen)
        update: dict = {"conversation": analysis, "followup_resolved": analysis.followup_resolved}
        if analysis.is_small_talk:
            # Pure small talk needs no scope check, search or paid classifier call.
            update["classification"] = QueryClassification(
                intent=IntentLabel.GREETING if analysis.kind == MessageKind.GREETING else IntentLabel.CHITCHAT,
                sub_intent=analysis.kind.value,
                route=RouteLabel.DIRECT_RESPONSE,
                confidence=0.95,
                reasoning_summary=f"conversation_analysis:{analysis.source}",
            )
            update["selected_route"] = RouteLabel.DIRECT_RESPONSE
        elif analysis.question:
            update["query"] = analysis.question
        return update

    @staticmethod
    def _after_conversation(state: ChatWorkflowState) -> str:
        return "small_talk" if state["conversation"].is_small_talk else "business"

    @staticmethod
    def _scope_node(state: ChatWorkflowState) -> dict:
        return {"scope": classify_scope(state["query"], state["context"])}

    @staticmethod
    def _after_scope(state: ChatWorkflowState) -> str:
        return "in_scope" if state["scope"].in_scope else "out_of_scope"

    @staticmethod
    def _out_of_scope_node(state: ChatWorkflowState) -> dict:
        result = WorkflowResult(
            route="OUT_OF_SCOPE",
            answer=OUT_OF_SCOPE_MESSAGE,
            reason=state["scope"].label.value,
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_out_of_scope",
            request_id=state["request_id"],
            scope=state["scope"].label.value,
        )
        return {"result": result}

    @staticmethod
    def _ambiguity_node(state: ChatWorkflowState) -> dict:
        return {"ambiguity": resolve_ambiguity(state["query"], state["context"])}

    @staticmethod
    def _after_ambiguity(state: ChatWorkflowState) -> str:
        return "resolved" if state["ambiguity"].resolved else "clarify"

    @staticmethod
    def _clarify_node(state: ChatWorkflowState) -> dict:
        ambiguity = state.get("ambiguity")
        answer = (
            ambiguity.clarification_question
            if ambiguity and ambiguity.clarification_question
            else "Could you clarify the SyteLine topic or record you mean?"
        )
        result = WorkflowResult(
            route="CLARIFY",
            answer=answer,
            reason=ambiguity.label.value if ambiguity else "clarification_required",
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_clarification_requested",
            request_id=state["request_id"],
            ambiguity=result.reason,
        )
        return {"result": result}

    @staticmethod
    def _transform_node(state: ChatWorkflowState) -> dict:
        query = state["ambiguity"].resolved_query or state["query"]
        transformed = transform_query(query, state["context"])
        # Search with the LLM's standard-terminology version ("raise a quote" -> "create and issue a
        # quotation") — the manuals never say "raise", so the user's slang scored below the evidence
        # bar. Only for a single question whose text wasn't changed by screen-context substitution;
        # the answer is still written for the user's own wording (rewritten_query).
        conversation = state.get("conversation")
        if (
            conversation
            and conversation.search_query
            and not transformed.subqueries
            and query == state["query"]
        ):
            transformed.terminology_query = expand_for_retrieval(conversation.search_query)
            transformed.transformations.append("llm_search_terminology")
        return {"transformed": transformed}

    @staticmethod
    def _classification_node(state: ChatWorkflowState) -> dict:
        conversation = state.get("conversation")
        precomputed = conversation.classification if conversation and settings.combined_understanding else None
        classification = classify_and_route(state["transformed"], state["context"], precomputed=precomputed)
        mood = _user_mood(state, classification.emotion)
        if mood != classification.emotion:
            log_event(logger, "user_mood_adjusted", request_id=state["request_id"],
                      classifier=classification.emotion.value, mood=mood.value)
            trace.detail(f"mood from the user's own words: {mood.value} (the classifier alone said "
                         f"{classification.emotion.value} from the cleaned-up question)")
        classification.emotion = mood
        return {"classification": classification}

    @staticmethod
    def _route_node(state: ChatWorkflowState) -> dict:
        route = state["classification"].route
        log_event(
            logger,
            "orchestration_route_selected",
            request_id=state["request_id"],
            route=route.value,
            intent=state["classification"].intent.value,
        )
        return {"selected_route": route}

    @staticmethod
    def _dispatch_route(state: ChatWorkflowState) -> str:
        route = state["selected_route"]
        if route == RouteLabel.BLOCK:
            return "blocked"
        if route == RouteLabel.CLARIFY:
            return "clarify"
        if route == RouteLabel.DIRECT_RESPONSE:
            return "direct"
        if route == RouteLabel.FAST_QA:
            return "fast_qa"
        if route == RouteLabel.MARKDOWN_RAG:
            return "rag"
        return "pending"

    @staticmethod
    def _direct_response_node(state: ChatWorkflowState) -> dict:
        intent = state["classification"].intent
        sub_intent = _normalize_chitchat_sub_intent(state["classification"].sub_intent)
        # Time-of-day greetings get an answer that actually echoes the greeting back,
        # instead of every "hi"/"good morning"/"good evening" collapsing to one reply.
        greeting_answer = _greeting_reply(state)
        answers = {
            IntentLabel.GREETING: greeting_answer or "Hello! How can I help with your SyteLine Prospect-to-Cash work?",
            IntentLabel.FEEDBACK: "Thank you for the feedback. It has been noted for the improvement workflow.",
            IntentLabel.COMPLAINT: "I understand this is frustrating. Tell me the SyteLine screen or process involved, and I’ll help narrow it down.",
        }
        chitchat_answers = {
            "wellbeing": "I’m doing well, thank you for asking! How can I help you with SyteLine today?",
            "casual_checkin": "Not much—I’m here and ready to help with SyteLine. What are you working on?",
            "identity": (
                "I’m the SyteLine Prospect-to-Cash Assistant. I help with approved business concepts, "
                "screens, fields, processes, and safe request routing."
            ),
            "capabilities": (
                "I can explain approved Prospect-to-Cash concepts, screens, fields, and processes, "
                "and I can classify live-data, navigation, and action requests for the appropriate route."
            ),
            "thanks": "You’re welcome. Ask me anytime about the SyteLine Prospect-to-Cash process.",
            "introduction": "Nice to meet you too. I’m here to help with SyteLine Prospect-to-Cash.",
            "acknowledgement": "Got it. What would you like to work on in SyteLine?",
            "farewell": "Goodbye! I’ll be here when you need more SyteLine help.",
            "escalation_request": (
                "Sure — I can raise a support ticket with this conversation attached, so the support "
                "team can follow up with you. Press 🎫 Create support ticket below to confirm, and add a "
                "short note about what went wrong if you like."
            ),
        }
        result = WorkflowResult(
            route="DIRECT_RESPONSE",
            answer=(
                greeting_answer  # a greeting the classifier happened to label CHITCHAT is still a greeting
                or _greet_back(
                    state,
                    chitchat_answers.get(
                        sub_intent,
                        "I’m here to help with SyteLine Prospect-to-Cash. What would you like to discuss?",
                    ),
                )
                if intent == IntentLabel.CHITCHAT
                else answers.get(intent, "How can I help with SyteLine?")
            ),
            decision_trace=_decision_trace(state),
        )
        log_event(logger, "orchestration_response_ready", request_id=state["request_id"], route=result.route)
        return {"result": result}

    @staticmethod
    def _fast_qa_node(state: ChatWorkflowState) -> dict:
        permission = resolve_permission(state["user"], "READ", "qa", request_id=state["request_id"])
        if not permission.allowed:
            result = WorkflowResult(
                route="BLOCKED",
                answer=None,
                reason=permission.reason,
                decision_trace=_decision_trace(state),
            )
            return {"result": result}

        log_event(logger, "fast_qa_search_started", request_id=state["request_id"])
        match = _best_qa_match(state["transformed"])
        log_event(
            logger,
            "fast_qa_search_completed",
            request_id=state["request_id"],
            route=match.route,
            score=round(match.score, 4),
            candidates=len(match.candidates),
        )

        # Exact wording match (question or a listed variation): answer instantly, no search needed.
        if match.record and match.score >= 1.0 and not state["transformed"].subqueries:
            return {
                "result": WorkflowResult(
                    route="FAST_QA_RESPONSE", grounding="approved",
                    answer=_greet_back(state, apply_tone(match.record.answer, _mood(state), tone.APPROVED)),
                    source=match.record.qa_id,
                    score=match.score,
                    decision_trace={**_decision_trace(state), "answer_source": "excel_exact_match"},
                )
            }

        # Otherwise hand the best curated row to the unified Excel + Markdown search, which
        # shows it verbatim only if the reranker independently agrees it is the best answer.
        # (The old 0.80 hybrid threshold and hybrid-gap "did you mean" both mis-fired on the
        # knowledge-derived rows — e.g. "What is a customer order?" matched the order-LINE row.)
        update: dict = {"selected_route": RouteLabel.MARKDOWN_RAG}
        if match.candidates:
            best_record, best_score = match.candidates[0]
            update["qa_candidate"] = (best_record.qa_id, float(best_score))
        return update

    @staticmethod
    def _after_fast_qa(state: ChatWorkflowState) -> str:
        return "done" if state.get("result") else "rag"

    @staticmethod
    def _rag_node(state: ChatWorkflowState) -> dict:
        permission = resolve_permission(
            state["user"], "READ", "markdown_rag", request_id=state["request_id"]
        )
        if not permission.allowed:
            return {
                "result": WorkflowResult(
                    route="BLOCKED",
                    answer=None,
                    reason=permission.reason,
                    decision_trace=_decision_trace(state),
                )
            }

        transformed = state["transformed"]
        qa_candidate = state.get("qa_candidate")
        if qa_candidate is None and not transformed.subqueries:
            # Routes that skip the Fast Q&A node (e.g. troubleshooting) still get the question match.
            if resolve_permission(state["user"], "READ", "qa", request_id=state["request_id"]).allowed:
                trace.detail("▸ Excel curated answers — does the question match one?")
                match = _best_qa_match(transformed)
                if match.candidates:
                    qa_candidate = (match.candidates[0][0].qa_id, float(match.candidates[0][1]))

        # Exact wording match on a curated question or variation: approved answer, no search needed.
        if qa_candidate and qa_candidate[1] >= 1.0 and not transformed.subqueries:
            record = get_rag_index().qa_records.get(qa_candidate[0])
            if record:
                log_event(logger, "excel_answer_selected", request_id=state["request_id"], qa_id=record.qa_id)
                return {
                    "result": WorkflowResult(
                        route="FAST_QA_RESPONSE", grounding="approved",
                        answer=_greet_back(state, apply_tone(record.answer, _mood(state), tone.APPROVED)),
                        source=record.qa_id,
                        score=1.0,
                        decision_trace={**_decision_trace(state), "answer_source": "excel_exact_match"},
                    )
                }

        log_event(logger, "rag_search_started", request_id=state["request_id"])
        chunks, scores, sources, per_query = _search_each_question(state)
        best_by_source: dict[str, float] = {}
        for result in per_query:
            for source, score in result.best_score_by_source.items():
                best_by_source[source] = max(best_by_source.get(source, score), score)
        log_event(
            logger,
            "rag_search_completed",
            request_id=state["request_id"],
            has_evidence=bool(chunks),
            chunks=len(chunks),
            excel_chunks=sources.count("excel"),
            markdown_chunks=sources.count("markdown"),
            best_excel=round(best_by_source.get("excel", float("nan")), 2),
            best_markdown=round(best_by_source.get("markdown", float("nan")), 2),
            searches=len(per_query),
            subquestions_with_evidence=sum(1 for r in per_query if r.has_evidence),
        )
        confidence_trace = {
            "excel_best_score": round(best_by_source["excel"], 2) if "excel" in best_by_source else None,
            "markdown_best_score": round(best_by_source["markdown"], 2) if "markdown" in best_by_source else None,
        }

        # Single question whose top-ranked evidence (of 10 Excel + 10 Markdown) is the same curated
        # row the question itself strongly matched -> show the approved Excel answer verbatim.
        verbatim = (
            not transformed.subqueries
            and chunks
            and sources[0] == "excel"
            and qa_candidate
            and qa_candidate[0] == chunks[0].chunk_id
            and qa_candidate[1] >= EXCEL_VERBATIM_MATCH_SCORE
        )
        trace.detail("▸ cross-check: use an approved Excel answer word for word?")
        trace.detail(f"    {_verbatim_reason(transformed, chunks, sources, qa_candidate, bool(verbatim))}")
        if verbatim:
            record = get_rag_index().qa_records[chunks[0].chunk_id]
            log_event(logger, "excel_answer_selected", request_id=state["request_id"], qa_id=record.qa_id)
            return {
                "result": WorkflowResult(
                    route="FAST_QA_RESPONSE", grounding="approved",
                    answer=_greet_back(state, apply_tone(record.answer, _mood(state), tone.APPROVED)),
                    source=record.qa_id,
                    score=round(qa_candidate[1], 2),
                    decision_trace={
                        **_decision_trace(state),
                        **confidence_trace,
                        "answer_source": "excel_verbatim",
                    },
                )
            }

        if not chunks:
            trace.detail("▸ nothing to answer from → polite NO_ANSWER (listed as a content gap in the console)")
            return {
                "result": WorkflowResult(
                    route="NO_ANSWER",
                    answer=_greet_back(
                        state,
                        apply_tone(
                            "I don’t have enough approved information to answer that yet. "
                            "Try naming the specific form, field, or step you’re working on.",
                            _mood(state),
                            tone.NOT_FOUND,
                        ),
                    ),
                    decision_trace={**_decision_trace(state), **confidence_trace, "answer_source": "none"},
                )
            }

        log_event(
            logger,
            "answer_generation_started",
            request_id=state["request_id"],
            evidence_chunks=len(chunks),
        )
        question = state["transformed"].rewritten_query
        mood = _mood(state)
        style = tone_instruction(mood)
        # The SyteLine-terms hint only when the question has an abbreviation the answer model can't
        # read ("What is SO?"). For ordinary wording it just re-phrases the question and was
        # measured to pull the answer toward generic "process" evidence (TC-34 invoice lifecycle).
        terminology = (
            transformed.terminology_query
            if transformed.terminology_query and not transformed.subqueries and _ABBREVIATION.search(question)
            else None
        )
        classification = state.get("classification")
        brief = not transformed.subqueries and is_definition_question(
            question, getattr(classification, "operation", None))
        trace.detail(f"▸ write the answer from the {len(chunks)} evidence item(s) — tone for mood {mood.value}"
                     + (" · length: short (simple definition question)" if brief else "")
                     + (f" · SyteLine-terms hint {trace.text(terminology, 100)}" if terminology else ""))
        try:
            answer = generate_answer(question, chunks, tone=style, terminology=terminology, brief=brief)
        except Exception:
            logger.exception("event=answer_generation_failed request_id=%s", state["request_id"])
            raise

        # Hallucination guard: every claim must come from the evidence; repair once, else refuse.
        validation = validate_answer(
            f"{question} (in SyteLine terms: {terminology})" if terminology else question,
            answer,
            chunks,
            request_id=state["request_id"],
            regenerate=lambda claims: generate_answer(question, chunks, avoid_claims=claims, tone=style,
                                                      terminology=terminology, brief=brief),
        )
        source_labels = [f"{chunk.source_file} — {chunk.full_context_path}" for chunk in chunks]
        used = sorted(set(sources))
        route = "MARKDOWN_RAG_RESPONSE"
        if validation.action in ("not_found", "replaced"):
            route = "NO_ANSWER"  # counted as unanswered, never as a document answer
        return {
            "result": WorkflowResult(
                route=route,
                answer=_greet_back(
                    state,
                    apply_tone(
                        validation.answer,
                        mood,
                        tone.NOT_FOUND if route == "NO_ANSWER" else tone.GENERATED,
                    ),
                ),
                sources=None if validation.reason in LEAK_REASONS else source_labels,
                score=max(scores) if scores else 0.0,
                reason=validation.reason,
                grounding=validation.action,
                decision_trace={
                    **_decision_trace(state),
                    **confidence_trace,
                    "answer_source": "generated_from_" + "_and_".join(used),
                    **validation.trace(),
                },
            )
        }

    @staticmethod
    def _capability_pending_node(state: ChatWorkflowState) -> dict:
        route = state["selected_route"]
        messages = {
            RouteLabel.LIVE_DATA: (
                "I recognized this as a live SyteLine data request. Live IDO/API access is not connected yet, "
                "so I did not answer it from documents or model memory."
            ),
            RouteLabel.RAG_IDO: (
                "This request needs both approved documentation and live SyteLine data. The live-data part "
                "arrives in Phase 4, so no partial or potentially misleading answer was generated."
            ),
            RouteLabel.NAVIGATION: (
                "I recognized this as a SyteLine navigation request. Navigation execution is not connected "
                "yet; no form or record was opened."
            ),
            RouteLabel.ACTION: (
                "I recognized this as a transaction request. The current proof of concept is read-only, "
                "so no SyteLine change was made."
            ),
            RouteLabel.LLM_REASONING: (
                "I recognized this as an advanced analysis request. That controlled reasoning route is not "
                "enabled yet, so I did not generate an unsupported answer."
            ),
        }
        result = WorkflowResult(
            route="CAPABILITY_PENDING",
            answer=messages.get(route, "This route is not available yet."),
            reason=f"phase_4_or_later:{route.value}",
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_capability_pending",
            request_id=state["request_id"],
            route=route.value,
        )
        return {"result": result}

    def run(self, query: str, context, user, history: list[Turn] | None = None) -> WorkflowResult:
        state = self.graph.invoke(
            {
                "request_id": context.request_id,
                "query": query,
                "original_query": query,
                "history": history or [],
                "context": context,
                "user": user,
            }
        )
        result = state.get("result")
        if result is None:
            raise RuntimeError("Orchestration completed without a result")
        if state.get("followup_resolved"):
            result.resolved_query = state["query"]
        ambiguity = state.get("ambiguity")
        if (
            ambiguity
            and ambiguity.reason == GENERAL_ANSWER_REASON
            and result.answer
            and result.route in ("FAST_QA_RESPONSE", "MARKDOWN_RAG_RESPONSE")
        ):
            result.answer += (
                "\n\nThis is the general answer. To check a specific record, select it in SyteLine "
                "(or type its number) and ask again."
            )
        # Support-ticket offer (§55). The graph only DECIDES; the API adds the offer text
        # (it knows whether tickets can be stored right now) and the user must confirm.
        conversation = state.get("conversation")
        decision = decide_escalation(
            result.route,
            _mood(state),
            state.get("history") or [],
            user_requested=bool(conversation and conversation.kind == MessageKind.ESCALATION_REQUEST),
        )
        result.escalation = decision.state.value
        result.decision_trace["escalation"] = decision.state.value
        result.decision_trace["escalation_trigger"] = decision.trigger
        log_event(
            logger,
            "orchestration_completed",
            request_id=context.request_id,
            route=result.route,
            reason=result.reason or "none",
        )
        return result


_orchestrator: ChatOrchestrator | None = None


def get_chat_orchestrator() -> ChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator()
    return _orchestrator
