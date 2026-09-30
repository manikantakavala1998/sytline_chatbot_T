"""Numbered, timed trace step for every LangGraph node (see utils/trace.py).

Each node is wrapped once in ChatOrchestrator: the wrapper opens "STEP n  <title>", runs the
node (search / matcher / answer check add their own detail lines while it runs), then writes
what the node decided and how long it took. Keeping every description here means the node
code stays about behaviour, and the trace can't drift out of step with the graph.
"""

import time
from typing import Callable

from backend.app.monitoring import usage
from backend.app.utils import trace

TITLES = {
    "security_gate": "Security gate — attacks, prompt tricks, secret requests",
    "blocked_response": "Blocked reply",
    "conversation_understanding": "Understand the message (LLM) — kind, mood, clean question, follow-up",
    "scope_check": "Scope check — is it about SyteLine Prospect-to-Cash?",
    "out_of_scope_response": "Out-of-scope reply",
    "ambiguity_resolution": "Ambiguity check — is a specific record or customer needed?",
    "clarify_response": "Ask the user to clarify",
    "query_transformation": "Prepare the search — typos, abbreviations, glossary, split questions",
    "query_classification": "Classify — intent, complexity, mood, route",
    "route_selection": "Choose where the answer comes from",
    "direct_response": "Direct reply (approved template, no search)",
    "fast_qa": "Excel curated answers — exact wording match?",
    "markdown_rag": "Search the knowledge base, write the answer, cross-check it",
    "capability_pending": "Route not available yet (needs live SyteLine / Phase 4+)",
}


def _v(label) -> str:
    return getattr(label, "value", label) if label is not None else "—"


def _answer_result(update: dict) -> str:
    result = update.get("result")
    if not result:
        return "continue"
    parts = [result.route]
    if result.grounding:
        parts.append(f"answer check: {result.grounding}")
    if result.reason:
        parts.append(f"reason: {result.reason}")
    return " · ".join(parts)


def _security(state, update):
    s = update["security"]
    if s.allowed:
        return f"✅ safe ({_v(s.label)}, confidence {s.confidence:.2f})"
    trace.detail(f"signals: {', '.join(s.signals) or s.reason}")
    return f"⛔ BLOCKED as {_v(s.label)} (confidence {s.confidence:.2f}) — the question goes no further"


def _conversation(state, update):
    a = update["conversation"]
    trace.detail(f"kind: {a.kind.value} · greeting: {_v(a.greeting)} · asked how we are: {a.asked_wellbeing} · "
                 f"mood: {a.mood.value} · understood by: {a.source}")
    if a.question:
        trace.detail(f"clean question : {trace.text(a.question)}")
    if a.search_query and a.search_query != a.question:
        trace.detail(f"search wording : {trace.text(a.search_query)}  (SyteLine terms, used for search only)")
    if a.followup_resolved:
        trace.detail("follow-up: “it / this / that” replaced using the earlier conversation")
    return "small talk → template reply" if a.is_small_talk else "business question → continue"


def _scope(state, update):
    s = update["scope"]
    return (f"✅ {_v(s.label)} (confidence {s.confidence:.2f})" if s.in_scope
            else f"✗ {_v(s.label)} — {s.reason}")


def _ambiguity(state, update):
    a = update["ambiguity"]
    if a.resolved_query and a.resolved_query != state.get("query"):
        trace.detail(f"resolved to : {trace.text(a.resolved_query)}")
    if not a.resolved:
        trace.detail(f"ask the user: {trace.text(a.clarification_question)}")
        return f"✗ {_v(a.label)} — needs clarification ({a.reason})"
    return f"✅ {_v(a.label)} ({a.reason})"


def _transform(state, update):
    t = update["transformed"]
    trace.detail(f"answer wording : {trace.text(t.rewritten_query)}")
    trace.detail(f"search wording : {trace.text(t.expanded_query)}")
    if t.terminology_query:
        trace.detail(f"SyteLine terms : {trace.text(t.terminology_query)}")
    for n, sub in enumerate(t.subqueries, 1):
        trace.detail(f"sub-question {n} : {trace.text(sub)}")
    entities = {k: v for k, v in t.entities.items() if v}
    if entities:
        trace.detail(f"entities       : {trace.clean(entities, 200)}")
    return ", ".join(t.transformations) or "no changes needed"


def _classification(state, update):
    c = update["classification"]
    source = "rules (LLM unavailable)" if c.reasoning_summary == "deterministic_fallback" else "LLM"
    trace.detail(f"intent {c.intent.value}{' / ' + c.sub_intent if c.sub_intent else ''} · complexity "
                 f"{c.complexity.value} · mood {c.emotion.value} · operation {c.operation} · by {source} "
                 f"(confidence {c.confidence:.2f})")
    if c.tool_candidate:
        trace.detail(f"live-data tool that would be used: {c.tool_candidate}")
    return f"route {c.route.value}"


def _route(state, update):
    return {
        "FAST_QA": "Excel curated answers first, then documents if needed",
        "MARKDOWN_RAG": "search Excel + documents together and write an answer",
        "DIRECT_RESPONSE": "template reply",
        "CLARIFY": "ask the user a question",
        "BLOCK": "block",
    }.get(_v(update["selected_route"]), f"{_v(update['selected_route'])} (not connected yet)")


def _reply(state, update):
    result = update.get("result")
    if result and result.answer:
        trace.detail(f"reply: {trace.text(result.answer, 200)}")
    return _answer_result(update)


def _fast_qa(state, update):
    if update.get("result"):
        return f"✅ exact match {update['result'].source} → approved Excel answer, word for word"
    candidate = update.get("qa_candidate")
    if candidate:
        return f"no exact match — best Excel row {candidate[0]} ({candidate[1]:.2f}) goes into the combined search"
    return "no Excel candidate — combined search"


DESCRIBERS: dict[str, Callable] = {
    "security_gate": _security,
    "blocked_response": _reply,
    "conversation_understanding": _conversation,
    "scope_check": _scope,
    "out_of_scope_response": _reply,
    "ambiguity_resolution": _ambiguity,
    "clarify_response": _reply,
    "query_transformation": _transform,
    "query_classification": _classification,
    "route_selection": _route,
    "direct_response": _reply,
    "fast_qa": _fast_qa,
    "markdown_rag": lambda state, update: _answer_result(update),
    "capability_pending": _reply,
}


def traced(name: str, node: Callable) -> Callable:
    """Wrap a graph node so it becomes one numbered, timed step in the request trace."""
    describe = DESCRIBERS[name]

    def run(state):
        trace.begin_step(TITLES[name])  # the trace times the step from here
        started = time.perf_counter()
        try:
            update = node(state)
        except Exception as exc:
            usage.record_stage(name, time.perf_counter() - started)
            trace.end_step(f"⛔ FAILED: {type(exc).__name__}: {trace.clean(exc, 200)}")
            raise
        usage.record_stage(name, time.perf_counter() - started)  # for the audit record / Health tab
        try:
            result = describe(state, update)
        except Exception as exc:  # a trace bug must never break a chat answer
            result = f"(trace description failed: {type(exc).__name__})"
        trace.end_step(result)
        return update

    run.__name__ = f"traced_{name}"
    return run
