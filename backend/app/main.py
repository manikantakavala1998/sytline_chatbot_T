"""
FastAPI app entry point. Kept small on purpose — this is Phase 1's
foundation step. The RAG pipeline (Excel Q&A + Markdown search) gets
wired in as its own step next.
"""

from fastapi import FastAPI

from backend.app.api.routes import router

app = FastAPI(
    title="SyteLine Prospect-to-Cash AI Chatbot",
    version="0.1.0",
)

app.include_router(router)
