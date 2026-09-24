"""
API routes. /chat tries Fast Q&A first (Source A); only if that's not a
confident match does it fall through to Markdown RAG (Source B) — the two
stay separate routes per the master prompt (section 8-9, section 26), Fast
Q&A tried first for speed and lower hallucination risk.
"""

from fastapi import APIRouter

from backend.app.api.models import ChatRequest, ChatResponse
from backend.app.config import settings
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.answer_service import generate_answer
from backend.app.rag.retriever import get_rag_index
from backend.app.security.permission_seam import check_permission

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/info")
async def info():
    return {
        "name": "SyteLine Prospect-to-Cash AI Chatbot",
        "phase": "Phase 1 - foundation",
        "primary_llm": settings.primary_llm,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    permission = check_permission(user_id="anonymous", operation="READ", resource="qa")
    if not permission.allowed:
        return ChatResponse(route="BLOCKED", answer=None, source=None, score=0.0)

    match = get_qa_index().search(request.query)

    if match.route == "FAST_QA_RESPONSE" and match.record:
        return ChatResponse(
            route=match.route,
            answer=match.record.answer,
            source=match.record.qa_id,
            score=match.score,
        )

    if match.route == "CLARIFY":
        options = "; ".join(record.canonical_question for record, _ in match.candidates)
        return ChatResponse(
            route=match.route,
            answer=f"I found a few possible matches — did you mean: {options}?",
            source=None,
            score=match.score,
        )

    # MARKDOWN_RAG — Fast Q&A had nothing confident, try the deeper document search
    rag_result = get_rag_index().search(request.query)

    if not rag_result.has_evidence:
        return ChatResponse(
            route="NO_ANSWER",
            answer="I don't have information about that yet. Please contact the support team for help.",
            score=match.score,
        )

    answer = generate_answer(request.query, rag_result.chunks)
    sources = [f"{c.source_file} — {c.full_context_path}" for c in rag_result.chunks]
    return ChatResponse(
        route="MARKDOWN_RAG_RESPONSE",
        answer=answer,
        sources=sources,
        score=rag_result.scores[0] if rag_result.scores else 0.0,
    )
