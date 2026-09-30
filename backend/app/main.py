"""
FastAPI app entry point. Both search indexes (Fast Q&A and Markdown RAG)
are built once at startup, not on the first request, so the first real
user isn't the one waiting for the embedding/reranker models to load and
the documents to be chunked and indexed into Milvus.
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.config import BASE_DIR, settings
from backend.app.audit.store import init_audit_store, purge_expired
from backend.app.escalation.notifier import startup_check as notifier_startup_check
from backend.app.escalation.store import init_escalation_store
from backend.app.feedback.insights import init_feedback_store
from backend.app.history.store import close_history_store, init_history_store
from backend.app.monitoring.health import evaluate_alerts, init_monitoring_store
from backend.app.orchestration.graph import get_chat_orchestrator
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.retriever import get_rag_index
from backend.app.utils import trace
from backend.app.utils.logger import LOG_FILE, get_logger, log_event

FRONTEND_DIR = BASE_DIR / "frontend" / "chatbot"

logger = get_logger(__name__)


def _ok(flag: bool, ok: str, down: str) -> str:
    return f"✅ {ok}" if flag else f"⚠ {down}"


async def _monitor_loop() -> None:
    """Health alerts every MONITOR_INTERVAL_SECONDS; audit retention purge once a day."""
    last_purge = time.monotonic()
    while True:
        await asyncio.sleep(settings.monitor_interval_seconds)
        try:
            await asyncio.to_thread(evaluate_alerts)
            if time.monotonic() - last_purge > 24 * 3600:
                await asyncio.to_thread(purge_expired)
                last_purge = time.monotonic()
        except Exception:  # the monitor must never take the server down
            logger.exception("event=monitor_loop_failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    started = time.perf_counter()
    trace.banner("STARTING SyteLine Prospect-to-Cash assistant — loading knowledge and services")
    trace.startup("Log file", str(LOG_FILE))
    trace.startup("Models", f"answers {settings.primary_llm} · understanding/classifier {settings.orchestrator_model} "
                  f"· answer check {settings.answer_validation_model} · embeddings {settings.embedding_model}")
    trace.startup("Question/answer text in logs", "shown (LOG_CONVERSATION_TEXT=true, secrets masked)"
                  if settings.log_conversation_text else "hidden (LOG_CONVERSATION_TEXT=false)")
    log_event(logger, "startup_begin", log_file=LOG_FILE)
    monitor: asyncio.Task | None = None
    try:
        log_event(logger, "startup_ingestion_begin", sources="fast_qa,markdown_rag")
        get_qa_index()
        get_rag_index()
        get_chat_orchestrator()
        trace.startup("Question workflow (LangGraph)", "14 steps compiled")
        log_event(logger, "startup_orchestration_ready", engine="langgraph")
        history_ok = init_history_store()  # fail-soft: chat still works without Postgres, just without memory
        trace.startup("Chat history (Postgres)", _ok(
            history_ok, f"{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}",
            "UNAVAILABLE — answers still work, but without memory, tickets or the console"))
        tickets_ok = init_escalation_store()  # tickets + security events on the same Postgres; fail-soft too
        trace.startup("Tickets + security events", _ok(tickets_ok, "ready", "unavailable"))
        notifier_startup_check()  # says whether ticket mail (Outlook) is configured
        audit_ok = init_audit_store()  # permanent, append-only audit trail (Phase 6)
        purged = purge_expired() if audit_ok else 0
        trace.startup("Audit trail", _ok(audit_ok, f"append-only · kept {settings.audit_retention_days} days"
                                         f"{f' · {purged} expired row(s) purged' if purged else ''}",
                                         "UNAVAILABLE — requests are NOT audited"))
        monitoring_ok = init_monitoring_store()
        monitor = asyncio.create_task(_monitor_loop())
        trace.startup("Health monitor", _ok(monitoring_ok, f"checks every {settings.monitor_interval_seconds // 60} "
                                            f"min over the last {settings.alert_window_minutes} min · alerts to "
                                            + ("OPS_ALERT_EMAIL + log" if settings.ops_alert_email else "the log"),
                                            "running without alert history (database unavailable)"))
        feedback_ok = init_feedback_store()  # admin reviews of 👎 answers / unanswered questions
        trace.startup("Feedback console", _ok(feedback_ok, f"http://127.0.0.1:{settings.api_port}/admin.html",
                                              "unavailable"))
        log_event(logger, "startup_ready", status="accepting_requests")
        trace.banner(f"READY in {time.perf_counter() - started:.0f}s — chat at http://127.0.0.1:{settings.api_port}/ "
                     "· every question is traced below, step by step")
        yield
    except Exception as exc:
        logger.exception("event=startup_failed")
        trace.banner(f"STARTUP FAILED — {type(exc).__name__}: {trace.clean(exc, 200)} (details above)")
        raise
    finally:
        if monitor is not None:
            monitor.cancel()
            with suppress(asyncio.CancelledError):
                await monitor
        close_history_store()
        log_event(logger, "shutdown_complete")
        trace.note("server stopped")


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
