"""
API routes.

Every /chat request now goes through the real Phase 2 pipeline before any
search happens: Security Bootstrap (who is this user) -> Context Manager
(build one normalized RequestContext) -> Dynamic Permission Resolver
(are they allowed to READ this resource). Only then does it try Fast Q&A
(Source A), falling through to Markdown RAG (Source B) only if that's not
a confident match — the two stay separate routes per the master prompt
(section 8-9, section 26).
"""

import uuid

from fastapi import APIRouter

from backend.app.api.models import ChatRequest, ChatResponse
from backend.app.authorization.resolver import resolve_permission
from backend.app.config import settings
from backend.app.context.manager import RecordContext, UIContext, build_request_context
from backend.app.integrations.syteline.session_context import get_configuration, get_current_site
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.answer_service import generate_answer
from backend.app.rag.retriever import get_rag_index
from backend.app.security.bootstrap import InvalidSessionError, bootstrap_security

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/info")
async def info():
    return {
        "name": "SyteLine Prospect-to-Cash AI Chatbot",
        "phase": "Phase 2 - SyteLine identity, session & permissions (mocked)",
        "primary_llm": settings.primary_llm,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Mock-only: a real session token always arrives with the request once
    # the frontend is actually embedded in SyteLine; until then, treat a
    # missing one as if the Context Simulator sent its default.
    session_token = request.session_token or "mock-session"

    try:
        user = bootstrap_security(session_token, simulated_group=request.simulated_group)
    except InvalidSessionError:
        return ChatResponse(route="BLOCKED", answer=None, score=0.0, reason="invalid_session")

    ctx = request.context or None
    context = build_request_context(
        request_id=str(uuid.uuid4()),
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

    permission = resolve_permission(user, "READ", "qa")
    if not permission.allowed:
        return ChatResponse(
            route="BLOCKED", answer=None, score=0.0, reason=permission.reason, context=context_payload
        )

    match = get_qa_index().search(request.query)

    if match.route == "FAST_QA_RESPONSE" and match.record:
        return ChatResponse(
            route=match.route,
            answer=match.record.answer,
            source=match.record.qa_id,
            score=match.score,
            context=context_payload,
        )

    if match.route == "CLARIFY":
        options = "; ".join(record.canonical_question for record, _ in match.candidates)
        return ChatResponse(
            route=match.route,
            answer=f"I found a few possible matches — did you mean: {options}?",
            score=match.score,
            context=context_payload,
        )

    # MARKDOWN_RAG — Fast Q&A had nothing confident, try the deeper document search
    rag_permission = resolve_permission(user, "READ", "markdown_rag")
    if not rag_permission.allowed:
        return ChatResponse(
            route="BLOCKED", answer=None, score=match.score, reason=rag_permission.reason, context=context_payload
        )

    rag_result = get_rag_index().search(request.query)

    if not rag_result.has_evidence:
        return ChatResponse(
            route="NO_ANSWER",
            answer="I don't have information about that yet. Please contact the support team for help.",
            score=match.score,
            context=context_payload,
        )

    answer = generate_answer(request.query, rag_result.chunks)
    sources = [f"{c.source_file} — {c.full_context_path}" for c in rag_result.chunks]
    return ChatResponse(
        route="MARKDOWN_RAG_RESPONSE",
        answer=answer,
        sources=sources,
        score=rag_result.scores[0] if rag_result.scores else 0.0,
        context=context_payload,
    )
