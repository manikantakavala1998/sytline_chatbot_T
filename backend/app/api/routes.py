"""
API routes.

Every /chat request enters through the trusted Phase 2 boundary (session,
context, base permission), then Phase 3's LangGraph owns security, scope,
ambiguity, query transformation, hierarchical classification, routing,
and execution of the currently available Fast Q&A / Markdown RAG routes.
"""

import uuid

from fastapi import APIRouter, HTTPException, Path, Request

from backend.app.api.models import (
    SESSION_ID_PATTERN,
    ChatRequest,
    ChatResponse,
    EscalationInfo,
    RatingRequest,
    TicketRequest,
)
from backend.app.authorization.resolver import resolve_permission
from backend.app.classification.taxonomy import SecurityLabel
from backend.app.config import settings
from backend.app.context.manager import RecordContext, UIContext, build_request_context
from backend.app.escalation import store as escalation_store
from backend.app.escalation.notifier import notify_safely
from backend.app.escalation.policy import EscalationState
from backend.app.history import store as history_store
from backend.app.quality.answer_validator import LEAK_REASONS
from backend.app.integrations.syteline.session_context import get_configuration, get_current_site
from backend.app.orchestration.graph import get_chat_orchestrator
from backend.app.security.bootstrap import InvalidSessionError, bootstrap_security
from backend.app.utils.logger import get_logger, log_event

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/info")
async def info():
    return {
        "name": "SyteLine Prospect-to-Cash AI Chatbot",
        "phase": "Phase 3 - Security, classification, routing & LangGraph orchestration",
        "primary_llm": settings.primary_llm,
        "orchestrator_model": settings.orchestrator_model,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    log_event(
        logger,
        "chat_received",
        request_id=request_id,
        query_chars=len(request.query),
        simulated_group=request.simulated_group or "default_mock",
    )

    # Mock-only: a real session token always arrives with the request once
    # the frontend is actually embedded in SyteLine; until then, treat a
    # missing one as if the Context Simulator sent its default.
    session_token = request.session_token or "mock-session"

    try:
        log_event(logger, "security_bootstrap_started", request_id=request_id)
        user = bootstrap_security(session_token, simulated_group=request.simulated_group)
        log_event(
            logger,
            "security_bootstrap_completed",
            request_id=request_id,
            user_id=user.user_id,
            groups_count=len(user.groups),
        )
    except InvalidSessionError:
        log_event(logger, "security_bootstrap_blocked", request_id=request_id, reason="invalid_session")
        return ChatResponse(route="BLOCKED", answer=None, score=0.0, reason="invalid_session")

    ctx = request.context or None
    context = build_request_context(
        request_id=request_id,
        user=user,
        configuration=get_configuration(),
        site=(ctx.site if ctx else None) or get_current_site(),
        ui=UIContext(
            module=ctx.module if ctx else None,
            form=ctx.form if ctx else None,
            component=ctx.component if ctx else None,
            field=ctx.field if ctx else None,
        ),
        record=RecordContext(
            record_type=ctx.record_type if ctx else None,
            record_id=ctx.record_id if ctx else None,
        ),
    )
    context_payload = context.model_dump()
    log_event(
        logger,
        "request_context_built",
        request_id=request_id,
        site=context.site,
        module=context.ui.module or "none",
        form=context.ui.form or "none",
        has_record=bool(context.record.record_id),
    )

    # Base assistant permission stays outside all model prompts. Route-specific
    # Q&A/RAG permission checks happen again inside their graph nodes.
    permission = resolve_permission(user, "READ", "assistant", request_id=request_id)
    if not permission.allowed:
        log_event(
            logger,
            "chat_blocked",
            request_id=request_id,
            resource="assistant",
            reason=permission.reason,
        )
        return ChatResponse(
            route="BLOCKED", answer=None, score=0.0, reason=permission.reason, context=context_payload
        )

    history = _load_history(request.session_id, user.user_id, request_id)
    workflow_result = get_chat_orchestrator().run(request.query, context, user, history=history)
    log_event(
        logger,
        "chat_response_ready",
        request_id=request_id,
        route=workflow_result.route,
        source_count=len(workflow_result.sources or []),
    )
    _record_security_event(request, user.user_id, request_id, context, workflow_result)
    escalation = _apply_escalation_offer(request, user, request_id, workflow_result)
    message_id = _save_exchange(request, user.user_id, request_id, workflow_result)
    return ChatResponse(
        route=workflow_result.route,
        answer=workflow_result.answer,
        source=workflow_result.source,
        sources=workflow_result.sources,
        score=workflow_result.score,
        reason=workflow_result.reason,
        context=context_payload,
        decision_trace=workflow_result.decision_trace,
        message_id=message_id,
        resolved_query=workflow_result.resolved_query,
        grounding=workflow_result.grounding,
        escalation=escalation,
    )


# ── Escalation (Phase 5 step 3) ────────────────────────────────────────
# Support tickets (§55) and security events (§56) are separate flows. Both are fail-soft: if
# Postgres is down the chat still answers; the ticket offer then points to the support team.

TICKET_OFFER = (
    "If this doesn’t solve it, I can raise a support ticket with this conversation attached — "
    "press 🎫 Create support ticket below."
)
NO_TICKET_OFFER = (
    "If this doesn’t fix it, contact your SyteLine support team and tell them what you’ve already tried."
)
TICKETS_UNAVAILABLE = (
    "I can’t create support tickets right now. Please contact your SyteLine support team directly and "
    "tell them what you’ve already tried."
)


def _record_security_event(request: ChatRequest, user_id: str, request_id: str, context, result) -> None:
    """Every blocked attack and every blocked answer leak is stored; repeated attempts alert."""
    security_label = (result.decision_trace or {}).get("security")
    # A BLOCKED with a SAFE security label is a missing permission, not an attack.
    if result.route == "BLOCKED" and security_label and security_label != SecurityLabel.SAFE.value:
        event_type, label = "input_blocked", security_label
    elif result.grounding == "replaced" and result.reason in LEAK_REASONS:
        event_type, label = "response_leak", escalation_store.RESPONSE_LEAK_LABEL
    else:
        return
    if not escalation_store.is_available():
        log_event(logger, "security_event_not_stored", request_id=request_id, label=label, reason="store_down")
        return
    try:
        event = escalation_store.record_security_event(
            user_id=user_id, session_id=request.session_id, request_id=request_id, event_type=event_type,
            label=label, query=request.query, site=context.site, module=context.ui.module, form=context.ui.form,
        )
    except Exception:
        logger.exception("event=security_event_store_failed request_id=%s", request_id)
        return
    if event["alert_raised"]:
        notify_safely("security_alert", event)


def _apply_escalation_offer(request: ChatRequest, user, request_id: str, result) -> EscalationInfo:
    state = result.escalation
    trigger = (result.decision_trace or {}).get("escalation_trigger")
    if state == EscalationState.NONE.value:
        return EscalationInfo(state=state)
    available = (
        bool(request.session_id)
        and escalation_store.is_available()
        and resolve_permission(user, "INSERT", "support_ticket", request_id=request_id).allowed
    )
    if state == EscalationState.CREATE_AFTER_CONFIRMATION.value and not available:
        result.answer = TICKETS_UNAVAILABLE
    elif state == EscalationState.SUGGEST_TICKET.value and result.answer:
        result.answer = f"{result.answer}\n\n{TICKET_OFFER if available else NO_TICKET_OFFER}"
    log_event(logger, "escalation_offered", request_id=request_id, state=state, trigger=trigger or "none",
              ticket_available=available)
    return EscalationInfo(state=state, trigger=trigger, ticket_available=available)


def _ticket_user(simulated_group: str | None, session_token: str | None, request_id: str, resource: str,
                 operation: str):
    if not escalation_store.is_available():
        raise HTTPException(status_code=503, detail="Support tickets are not available (Postgres is down)")
    try:
        user = bootstrap_security(session_token or "mock-session", simulated_group=simulated_group)
    except InvalidSessionError:
        raise HTTPException(status_code=401, detail="invalid_session")
    if not resolve_permission(user, operation, resource, request_id=request_id).allowed:
        raise HTTPException(status_code=403, detail="not_permitted")
    return user


@router.post("/api/tickets")
def create_support_ticket(body: TicketRequest, http_request: Request):
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    user = _ticket_user(body.simulated_group, body.session_token, request_id, "support_ticket", "INSERT")
    ctx = body.context
    ticket_ctx = escalation_store.TicketContext(
        user_id=user.user_id,
        user_display_name=user.display_name,
        site=(ctx.site if ctx else None) or get_current_site(),
        module=ctx.module if ctx else None,
        form=ctx.form if ctx else None,
        record_type=ctx.record_type if ctx else None,
        record_id=ctx.record_id if ctx else None,
    )
    outcome = escalation_store.create_ticket(
        ctx=ticket_ctx, session_id=body.session_id, message_id=body.message_id, user_note=body.note,
        request_id=request_id,
    )
    if outcome is None:
        raise HTTPException(status_code=404, detail="conversation_not_found")
    ticket, created = outcome
    if created:
        notify_safely("ticket_created", ticket)
    return {"ticket_ref": ticket["ticket_ref"], "status": ticket["status"], "priority": ticket["priority"],
            "created": created}


@router.get("/api/tickets")
def list_my_tickets(http_request: Request, simulated_group: str | None = None, session_token: str | None = None):
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    user = _ticket_user(simulated_group, session_token, request_id, "support_ticket", "INSERT")
    return {"tickets": escalation_store.list_user_tickets(user.user_id)}


@router.get("/api/admin/tickets")
def list_all_tickets(http_request: Request, simulated_group: str | None = None, session_token: str | None = None):
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    _ticket_user(simulated_group, session_token, request_id, "admin_console", "READ")
    return {"tickets": escalation_store.list_all_tickets()}


@router.get("/api/admin/security-events")
def list_security_events(
    http_request: Request, simulated_group: str | None = None, session_token: str | None = None
):
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    _ticket_user(simulated_group, session_token, request_id, "admin_console", "READ")
    return {"events": escalation_store.list_security_events()}


# ── Conversation history (PostgreSQL) ──────────────────────────────────
# History never blocks an answer: if Postgres is down the bot answers without
# memory. The /api/history endpoints, whose whole job is history, return 503.


def _load_history(session_id: str | None, user_id: str, request_id: str) -> list[history_store.Turn]:
    if not session_id or not history_store.is_available():
        return []
    try:
        return history_store.recent_turns(session_id, user_id, settings.history_turns_for_context)
    except Exception:
        logger.exception("event=history_load_failed request_id=%s", request_id)
        return []


def _save_exchange(request: ChatRequest, user_id: str, request_id: str, result) -> int | None:
    if not request.session_id or not history_store.is_available():
        return None
    try:
        message_id = history_store.save_exchange(
            session_id=request.session_id,
            user_id=user_id,
            question=request.query,
            resolved_query=result.resolved_query,
            answer=result.answer or "",
            route=result.route,
            source=result.source,
            sources=result.sources,
            score=result.score,
            decision_trace=result.decision_trace,
            request_id=request_id,
        )
        log_event(logger, "history_saved", request_id=request_id, stored=message_id is not None)
        return message_id
    except Exception:
        logger.exception("event=history_save_failed request_id=%s", request_id)
        return None


def _history_user(simulated_group: str | None, session_token: str | None) -> str:
    """Same trusted identity as /chat — history is always scoped to this user."""
    if not history_store.is_available():
        raise HTTPException(status_code=503, detail="Conversation history is not available (Postgres is down)")
    try:
        return bootstrap_security(session_token or "mock-session", simulated_group=simulated_group).user_id
    except InvalidSessionError:
        raise HTTPException(status_code=401, detail="invalid_session")


@router.get("/api/history/sessions")
def list_history_sessions(
    simulated_group: str | None = None, session_token: str | None = None, include_messages: bool = False
):
    user_id = _history_user(simulated_group, session_token)
    return {"sessions": history_store.list_sessions(user_id, include_messages=include_messages)}


@router.get("/api/history/sessions/{session_id}")
def get_history_session(
    session_id: str = Path(pattern=SESSION_ID_PATTERN),
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    user_id = _history_user(simulated_group, session_token)
    messages = history_store.get_session_messages(session_id, user_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session_id": session_id, "messages": messages}


@router.delete("/api/history/sessions/{session_id}")
def delete_history_session(
    session_id: str = Path(pattern=SESSION_ID_PATTERN),
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    user_id = _history_user(simulated_group, session_token)
    return {"deleted": history_store.delete_session(session_id, user_id)}


@router.delete("/api/history/sessions")
def delete_all_history_sessions(simulated_group: str | None = None, session_token: str | None = None):
    user_id = _history_user(simulated_group, session_token)
    return {"deleted": history_store.delete_all_sessions(user_id)}


@router.put("/api/history/messages/{message_id}/rating")
def rate_history_message(
    message_id: int, body: RatingRequest, simulated_group: str | None = None, session_token: str | None = None
):
    user_id = _history_user(simulated_group, session_token)
    value = {"up": 1, "down": -1}.get(body.rating) if body.rating else None
    if not history_store.set_rating(message_id, user_id, value):
        raise HTTPException(status_code=404, detail="message_not_found")
    return {"message_id": message_id, "rating": body.rating}
