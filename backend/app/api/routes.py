"""
Basic routes to prove the server is alive. The real /chat endpoint gets
added in the next Phase 1 step, once the Q&A + Markdown search engine exists.
"""

from fastapi import APIRouter

from backend.app.api.models import ChatRequest, ChatResponse
from backend.app.config import settings
from backend.app.qa.retriever import get_qa_index
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

    # MARKDOWN_RAG — document search isn't built yet, that's the next step
    return ChatResponse(
        route=match.route,
        answer="I don't have a quick answer for that yet. Deeper document search isn't built yet in this project — that's the next step.",
        source=None,
        score=match.score,
    )
