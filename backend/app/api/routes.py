"""
Basic routes to prove the server is alive. The real /chat endpoint gets
added in the next Phase 1 step, once the Q&A + Markdown search engine exists.
"""

from fastapi import APIRouter

from backend.app.config import settings

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
