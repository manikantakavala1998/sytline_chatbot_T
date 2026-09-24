"""
FastAPI app entry point. Both search indexes (Fast Q&A and Markdown RAG)
are built once at startup, not on the first request, so the first real
user isn't the one waiting for the embedding/reranker models to load and
the documents to be chunked and indexed into Milvus.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.config import BASE_DIR
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.retriever import get_rag_index
from backend.app.utils.logger import get_logger

FRONTEND_DIR = BASE_DIR / "frontend" / "chatbot"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Startup: ingesting Fast Q&A + Markdown RAG data ===")
    get_qa_index()
    get_rag_index()
    logger.info("=== Startup complete: both indexes ready, server accepting requests ===")
    yield


app = FastAPI(
    title="SyteLine Prospect-to-Cash AI Chatbot",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)

# Mounted last and at "/" so it only catches requests the API router above
# didn't already handle (StaticFiles(html=True) serves index.html at "/").
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
