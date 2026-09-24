"""
API routes.

Every /chat request enters through the trusted Phase 2 boundary (session,
context, base permission), then Phase 3's LangGraph owns security, scope,
ambiguity, query transformation, hierarchical classification, routing,
and execution of the currently available Fast Q&A / Markdown RAG routes.
"""

import uuid

from fastapi import APIRouter, Request

from backend.app.api.models import ChatRequest, ChatResponse
from backend.app.authorization.resolver import resolve_permission
from backend.app.config import settings
from backend.app.context.manager import RecordContext, UIContext, build_request_context
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

    workflow_result = get_chat_orchestrator().run(request.query, context, user)
    log_event(
        logger,
        "chat_response_ready",
        request_id=request_id,
        route=workflow_result.route,
        source_count=len(workflow_result.sources or []),
    )
    return ChatResponse(
        route=workflow_result.route,
        answer=workflow_result.answer,
        source=workflow_result.source,
        sources=workflow_result.sources,
        score=workflow_result.score,
        reason=workflow_result.reason,
        context=context_payload,
        decision_trace=workflow_result.decision_trace,
    )
