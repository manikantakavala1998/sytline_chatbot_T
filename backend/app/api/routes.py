"""
API routes.

Every /chat request enters through the trusted Phase 2 boundary (session,
context, base permission), then Phase 3's LangGraph owns security, scope,
ambiguity, query transformation, hierarchical classification, routing,
and execution of the currently available Fast Q&A / Markdown RAG routes.
"""

import time
import uuid

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response

from backend.app.api.models import (
    SESSION_ID_PATTERN,
    ChatRequest,
    ChatResponse,
    EscalationInfo,
    RatingRequest,
    ReviewRequest,
    TicketRequest,
    TicketStatusRequest,
)
from backend.app.authorization.resolver import resolve_permission
from backend.app.classification.taxonomy import SecurityLabel
from backend.app.config import settings
from backend.app.context.manager import RecordContext, UIContext, build_request_context
from backend.app.escalation import outlook as outlook_mail
from backend.app.escalation import store as escalation_store
from backend.app.escalation.notifier import notify_safely
from backend.app.escalation.policy import EscalationState
from backend.app.feedback import insights as feedback_insights
from backend.app.history import store as history_store
from backend.app.quality.answer_validator import LEAK_REASONS
from backend.app.audit import store as audit_store
from backend.app.monitoring import health as health_monitor  # health is the /health endpoint below
from backend.app.monitoring import usage
from backend.app.utils import trace
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
    run = trace.start_request(request_id)
    run.line(f"❓ NEW QUESTION  {trace.text(request.query, 400)}")
    run.line(f"   request {request_id} · test group {request.simulated_group or 'SALES_REP (default)'} · "
             f"chat session {request.session_id or '— (not saved)'}")
    measured = usage.start()
    try:
        response = await _answer_chat(request, request_id)
    except Exception as exc:
        run.line(f"⛔ FAILED after {run.elapsed():.1f}s — {type(exc).__name__}: {trace.clean(exc, 200)} "
                 "(full error in the log below)")
        audit_store.record_chat(request_id=request_id, question=request.query, session_id=request.session_id,
                                response=None, usage=measured, error=exc)
        raise
    finally:
        trace.end_request()
        usage.end()
    audit_id = audit_store.record_chat(request_id=request_id, question=request.query,
                                       session_id=request.session_id, response=response, usage=measured)
    run.line(f"🧾 audit #{audit_id} · {measured.elapsed_ms()} ms · {len(measured.llm_calls)} LLM call(s) · "
             f"tokens {measured.prompt_tokens} in / {measured.completion_tokens} out · "
             f"cost ${measured.cost_usd:.4f}" if audit_id else
             "🧾 audit NOT stored (database unavailable) — see the warning above")
    return response


def _trace_final(run, result, escalation, message_id) -> None:
    run.line(f"💬 ANSWER ({len(result.answer or '')} chars): {trace.text(result.answer, 600)}")
    if result.source:
        run.line(f"   source: {result.source}")
    for n, source in enumerate(result.sources or [], 1):
        run.line(f"   source {n}: {trace.clean(source, 160)}")
    extras = [f"route {result.route}"]
    if result.grounding:
        extras.append(f"answer check {result.grounding}")
    if escalation and escalation.state != EscalationState.NONE.value:
        extras.append(f"ticket offer {escalation.state} ({escalation.trigger})")
    extras.append(f"saved as message {message_id}" if message_id else "not saved (no session / history down)")
    run.line(f"✔ DONE in {run.elapsed():.1f}s · " + " · ".join(extras))


async def _answer_chat(request: ChatRequest, request_id: str) -> ChatResponse:
    run = trace.current()
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
        run.line("⛔ SIGN-IN FAILED — invalid SyteLine session; nothing else runs")
        return ChatResponse(route="BLOCKED", answer=None, score=0.0, reason="invalid_session")
    run.line(f"👤 signed in as {user.user_id} ({user.display_name}) · groups {', '.join(user.groups)} · "
             f"sites {', '.join(user.sites) or '—'}")

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
    screen = " / ".join(p for p in (context.site, context.ui.module, context.ui.form, context.ui.field) if p)
    record = f" · selected record {context.record.record_type} {context.record.record_id}" if context.record.record_id else ""
    run.line(f"🖥  screen: {screen or '—'}{record}")
    permission = resolve_permission(user, "READ", "assistant", request_id=request_id)
    if not permission.allowed:
        log_event(
            logger,
            "chat_blocked",
            request_id=request_id,
            resource="assistant",
            reason=permission.reason,
        )
        run.line(f"⛔ NO PERMISSION to use the assistant ({permission.reason}) · done in {run.elapsed():.1f}s")
        return ChatResponse(
            route="BLOCKED", answer=None, score=0.0, reason=permission.reason, context=context_payload
        )
    run.line("🔑 permission: READ assistant ✅")

    history = _load_history(request.session_id, user.user_id, request_id)
    run.line(f"🕘 history: {len(history)} earlier question(s) from this chat used to understand follow-ups"
             if history else "🕘 history: none (new chat) — the question is read on its own")
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
    _trace_final(run, workflow_result, escalation, message_id)
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
        trace.line(f"🛡  security event {label} NOT stored — database unavailable")
        return
    try:
        event = escalation_store.record_security_event(
            user_id=user_id, session_id=request.session_id, request_id=request_id, event_type=event_type,
            label=label, query=request.query, site=context.site, module=context.ui.module, form=context.ui.form,
        )
    except Exception:
        logger.exception("event=security_event_store_failed request_id=%s", request_id)
        return
    trace.line(f"🛡  security event #{event.get('event_id', '?')} stored: {label} · severity "
               f"{event.get('severity', '?')} · {event.get('attempts_in_window', '?')} block(s) by this user in "
               f"{settings.security_alert_window_minutes} min" + (" · 🚨 ALERT RAISED" if event.get("alert_raised") else ""))
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
    trace.line(f"🎫 support ticket: {state} (why: {trigger}) · "
               + ("the 🎫 button is shown — created only if the user confirms" if available
                  else "tickets unavailable (no session, database down or no permission) — told to contact support"))
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
    trace.note(f"🎫 TICKET {ticket['ticket_ref']} {'created' if created else 'already existed (double click)'} by "
               f"{user.user_id} · priority {ticket['priority']} · why {ticket['trigger']} · issue "
               f"{trace.text(ticket['issue_summary'], 120)}")
    if created:
        audit_store.record_action("ticket_created", user_id=user.user_id, request_id=request_id,
                                  session_id=body.session_id, message_id=body.message_id,
                                  details={"ticket": ticket["ticket_ref"], "priority": ticket["priority"],
                                           "trigger": ticket["trigger"]})
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


# ── Feedback console (Phase 5 step 4) ──────────────────────────────────
# Everything here needs the admin-console permission (SUPPORT_ADMIN in the mock groups).


def _admin(http_request: Request, simulated_group: str | None, session_token: str | None, operation: str):
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    if not feedback_insights.is_available():
        raise HTTPException(status_code=503, detail="The feedback console is not available (Postgres is down)")
    user = _ticket_user(simulated_group, session_token, request_id, "admin_console", operation)
    log_event(logger, "admin_console_access", request_id=request_id, user_id=user.user_id, operation=operation,
              path=http_request.url.path)
    # Who looked at or changed admin data, and when (security events, tickets, feedback, audit).
    audit_store.record_action("admin_access", user_id=user.user_id, request_id=request_id,
                              details={"operation": operation, "path": http_request.url.path})
    return user


@router.get("/api/admin/overview")
def admin_overview(
    http_request: Request,
    days: int = Query(default=7, ge=1, le=feedback_insights.MAX_DAYS),
    include_reviewed: bool = False,
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    """One call for the console: summary tiles, content gaps, 👎 answers, tickets, security events."""
    _admin(http_request, simulated_group, session_token, "READ")
    return {
        "summary": feedback_insights.summary(days),
        "content_gaps": feedback_insights.content_gaps(days, include_reviewed=include_reviewed),
        "downvoted": feedback_insights.downvoted_answers(days, include_reviewed=include_reviewed),
        "tickets": escalation_store.list_all_tickets(),
        "security_events": escalation_store.list_security_events(),
        "mail": _mail_status(),
    }


def _mail_status() -> dict:
    """Ticket-mail setup for the console. Names missing .env values, never shows secret values."""
    enabled = settings.escalation_notifier.lower() == "outlook"
    return {
        "enabled": enabled,
        "method": settings.outlook_send_method if enabled else None,
        "sender": settings.outlook_sender or None,
        "ticket_recipients": outlook_mail.recipients(settings.support_ticket_email),
        "alert_recipients": outlook_mail.recipients(settings.security_alert_email),
        "missing": outlook_mail.missing_settings() if enabled else ["ESCALATION_NOTIFIER=outlook"],
    }


@router.post("/api/admin/notifier/test")
def send_test_mail(http_request: Request, simulated_group: str | None = None, session_token: str | None = None):
    """Send one test email to the ticket mailbox, right now, and report the result."""
    _admin(http_request, simulated_group, session_token, "UPDATE")
    status = _mail_status()
    if not status["enabled"] or status["missing"]:
        return {"sent": False, "reason": "not_configured", "missing": status["missing"]}
    try:
        outlook_mail.send(outlook_mail.connection_test_mail(), "test")
    except Exception as exc:
        logger.error("event=outlook_test_mail_failed error=%s: %s", type(exc).__name__, str(exc)[:300])
        return {"sent": False, "reason": "failed", "error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    return {"sent": True, "to": status["ticket_recipients"]}


@router.put("/api/admin/feedback/{message_id}")
def review_feedback_item(
    message_id: int,
    body: ReviewRequest,
    http_request: Request,
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    user = _admin(http_request, simulated_group, session_token, "UPDATE")
    if not feedback_insights.set_review(message_id, body.status, body.note, user.user_id):
        raise HTTPException(status_code=404, detail="message_not_found")
    audit_store.record_action("feedback_review", user_id=user.user_id, message_id=message_id,
                              details={"status": body.status})
    return {"message_id": message_id, "status": body.status}


@router.put("/api/admin/tickets/{ticket_id}")
def update_ticket_status(
    ticket_id: int,
    body: TicketStatusRequest,
    http_request: Request,
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    user = _admin(http_request, simulated_group, session_token, "UPDATE")
    if not feedback_insights.set_ticket_status(ticket_id, body.status, user.user_id):
        raise HTTPException(status_code=404, detail="ticket_not_found")
    audit_store.record_action("ticket_status", user_id=user.user_id, details={"ticket_id": ticket_id,
                                                                              "status": body.status})
    return {"ticket_id": ticket_id, "status": body.status}


@router.get("/api/admin/audit")
def search_audit(
    http_request: Request,
    days: int = Query(default=7, ge=1, le=3650),
    user_id: str | None = Query(default=None, max_length=120),
    event_type: str | None = Query(default=None, max_length=40),
    status: str | None = Query(default=None, max_length=40),
    request_id: str | None = Query(default=None, max_length=80),
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    """Find audit records (who asked what, what was allowed, what was answered, what it cost)."""
    _admin(http_request, simulated_group, session_token, "READ")
    if not audit_store.is_available():
        raise HTTPException(status_code=503, detail="The audit store is not available")
    return {"events": audit_store.search(days=days, user_id=user_id, event_type=event_type, status=status,
                                         request_id=request_id)}


@router.get("/api/admin/health")
def admin_health(
    http_request: Request,
    days: int = Query(default=14, ge=1, le=90),
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    """Health tab: live service checks, the alert window, today, daily series, LLM and step breakdowns."""
    _admin(http_request, simulated_group, session_token, "READ")
    if not audit_store.is_available():
        raise HTTPException(status_code=503, detail="Health numbers need the audit store (Postgres)")
    return {
        **health_monitor.service_checks(),
        "window": health_monitor.window_stats(settings.alert_window_minutes),
        "last_24h": health_monitor.window_stats(24 * 60),
        "cost_today_usd": round(health_monitor.today_cost_usd(), 4),
        "daily": health_monitor.daily_series(days),
        "llm": health_monitor.llm_breakdown(days),
        "stages": health_monitor.stage_breakdown(days),
        "open_alerts": health_monitor.open_alerts(),
        "recent_alerts": health_monitor.recent_alerts(),
        "thresholds": health_monitor.thresholds(),
    }


@router.post("/api/admin/health/check")
def run_health_check(http_request: Request, simulated_group: str | None = None, session_token: str | None = None):
    """Run the alert rules now instead of waiting for the next scheduled check."""
    _admin(http_request, simulated_group, session_token, "UPDATE")
    return {"changes": health_monitor.evaluate_alerts(), "open_alerts": health_monitor.open_alerts()}


@router.get("/api/admin/content-gaps.csv")
def export_content_gaps(
    http_request: Request,
    days: int = Query(default=30, ge=1, le=feedback_insights.MAX_DAYS),
    simulated_group: str | None = None,
    session_token: str | None = None,
):
    _admin(http_request, simulated_group, session_token, "READ")
    return Response(
        content=feedback_insights.content_gaps_csv(days),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="content_gaps.csv"'},
    )


# ── Conversation history (PostgreSQL) ──────────────────────────────────
# History never blocks an answer: if Postgres is down the bot answers without
# memory. The /api/history endpoints, whose whole job is history, return 503.


def _load_history(session_id: str | None, user_id: str, request_id: str) -> list[history_store.Turn]:
    if not session_id or not history_store.is_available():
        return []
    started = time.perf_counter()
    try:
        return history_store.recent_turns(session_id, user_id, settings.history_turns_for_context)
    except Exception:
        logger.exception("event=history_load_failed request_id=%s", request_id)
        return []
    finally:
        usage.record_db("history_load", time.perf_counter() - started)


def _save_exchange(request: ChatRequest, user_id: str, request_id: str, result) -> int | None:
    if not request.session_id or not history_store.is_available():
        return None
    started = time.perf_counter()
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
    finally:
        usage.record_db("history_save", time.perf_counter() - started)


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
    deleted = history_store.delete_session(session_id, user_id)
    if deleted:  # the chat goes; its audit rows stay (append-only)
        audit_store.record_action("chat_deleted", user_id=user_id, session_id=session_id)
    return {"deleted": deleted}


@router.delete("/api/history/sessions")
def delete_all_history_sessions(simulated_group: str | None = None, session_token: str | None = None):
    user_id = _history_user(simulated_group, session_token)
    deleted = history_store.delete_all_sessions(user_id)
    if deleted:
        audit_store.record_action("chat_deleted_all", user_id=user_id, details={"sessions": deleted})
    return {"deleted": deleted}


@router.put("/api/history/messages/{message_id}/rating")
def rate_history_message(
    message_id: int, body: RatingRequest, simulated_group: str | None = None, session_token: str | None = None
):
    user_id = _history_user(simulated_group, session_token)
    value = {"up": 1, "down": -1}.get(body.rating) if body.rating else None
    if not history_store.set_rating(message_id, user_id, value):
        raise HTTPException(status_code=404, detail="message_not_found")
    # Kept in the audit trail too, so a 👎 survives the user deleting the chat.
    audit_store.record_action("rating", user_id=user_id, message_id=message_id, details={"rating": value})
    return {"message_id": message_id, "rating": body.rating}
