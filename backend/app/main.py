"""
FastAPI app entry point. Both search indexes (Fast Q&A and Markdown RAG)
are built once at startup, not on the first request, so the first real
user isn't the one waiting for the embedding/reranker models to load and
the documents to be chunked and indexed into Milvus.
"""

from contextlib import asynccontextmanager
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.config import BASE_DIR
from backend.app.orchestration.graph import get_chat_orchestrator
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.retriever import get_rag_index
from backend.app.utils.logger import LOG_FILE, get_logger, log_event

FRONTEND_DIR = BASE_DIR / "frontend" / "chatbot"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_event(logger, "startup_begin", log_file=LOG_FILE)
    try:
        log_event(logger, "startup_ingestion_begin", sources="fast_qa,markdown_rag")
        get_qa_index()
        get_rag_index()
        get_chat_orchestrator()
        log_event(logger, "startup_orchestration_ready", engine="langgraph")
        log_event(logger, "startup_ready", status="accepting_requests")
        yield
    except Exception:
        logger.exception("event=startup_failed")
        raise
    finally:
        log_event(logger, "shutdown_complete")


app = FastAPI(
    title="SyteLine Prospect-to-Cash AI Chatbot",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_event_logging(request: Request, call_next):
    """Log every HTTP request and correlate downstream chat events."""

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    log_event(
        logger,
        "http_request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            "event=http_request_failed request_id=%s method=%s path=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    log_event(
        logger,
        "http_request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
    return response

app.include_router(router)

# Mounted last and at "/" so it only catches requests the API router above
# didn't already handle (StaticFiles(html=True) serves index.html at "/").
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
