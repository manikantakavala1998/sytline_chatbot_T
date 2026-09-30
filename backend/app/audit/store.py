"""Permanent audit trail (Phase 6, master prompt §62) in PostgreSQL.

One row per chat request and per admin / ticket / rating action, in `audit_events`:
who (user, groups), when, where (site, module, form, safe record reference), what was asked
(secret-masked text + SHA-256), how it was understood (intent, route, tool, mood), whether it was
allowed (authorization, security label), what came back (status, answer-check result, sources,
a short answer preview + SHA-256), which models answered, and the measurements (latency, time per
step, database time, every LLM call with tokens and cost).

Guarantees:
  • append-only — a database trigger rejects UPDATE and DELETE, so nothing in the app can change
    or erase history; only the retention purge (AUDIT_RETENTION_DAYS) may delete old rows
  • independent of chat history — deleting a conversation doesn't touch its audit rows
  • never stores passwords, tokens, keys or session secrets (all text is secret-masked)
  • fail-soft — if Postgres is down the chat still answers and a warning is logged

The Health dashboard and the health alerts (monitoring/) read their numbers from this table.
"""

import hashlib
import time

from psycopg.types.json import Jsonb

from backend.app.config import settings
from backend.app.escalation.store import redact
from backend.app.history import store as history_store
from backend.app.monitoring.usage import RequestUsage
from backend.app.rag.reranker import RERANKER_MODEL
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

QUESTION_MAX_CHARS = 1000
ANSWER_PREVIEW_CHARS = 500

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS audit_events (
    audit_id          BIGSERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type        TEXT NOT NULL,
    request_id        TEXT,
    trace_id          TEXT,
    user_id           TEXT,
    user_groups       TEXT,
    session_id        TEXT,
    message_id        BIGINT,
    site              TEXT,
    module            TEXT,
    form              TEXT,
    record_type       TEXT,
    record_id         TEXT,
    question_sha256   TEXT,
    question_text     TEXT,
    intent            TEXT,
    route             TEXT,
    tool              TEXT,
    authorization_result TEXT,
    security_label    TEXT,
    status            TEXT,
    grounding         TEXT,
    mood              TEXT,
    escalation        TEXT,
    sources           JSONB,
    answer_sha256     TEXT,
    answer_preview    TEXT,
    answer_chars      INT,
    models            JSONB,
    latency_ms        INT,
    stages_ms         JSONB,
    db_ms             JSONB,
    llm_calls         JSONB,
    prompt_tokens     INT,
    completion_tokens INT,
    cost_usd          NUMERIC(12, 6),
    error             TEXT,
    details           JSONB
);
CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_events (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_type_created ON audit_events (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_user_created ON audit_events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_message ON audit_events (message_id) WHERE message_id IS NOT NULL;

-- Append-only: the app may INSERT, never UPDATE; DELETE only inside the retention purge.
CREATE OR REPLACE FUNCTION audit_events_append_only() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' AND current_setting('audit.retention_purge', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'audit_events is append-only (% blocked)', TG_OP;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS audit_events_no_change ON audit_events;
CREATE TRIGGER audit_events_no_change BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION audit_events_append_only();
"""

_available = False


def init_audit_store() -> bool:
    global _available
    if not history_store.is_available():
        _available = False
        return False
    try:
        with history_store.shared_pool().connection() as conn:
            conn.execute(SCHEMA_SQL)
        _available = True
        log_event(logger, "audit_store_ready")
    except Exception as exc:
        _available = False
        log_event(logger, "audit_store_unavailable", error=type(exc).__name__)
    return _available


def is_available() -> bool:
    return _available and history_store.is_available()


def _sha(text: str | None) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


def model_versions() -> dict:
    """Which models produced the answer (§62 slm_version / llm_version)."""
    return {
        "answer": settings.primary_llm,
        "understanding_classifier_scope_security": settings.orchestrator_model,
        "answer_check": settings.answer_validation_model,
        "embedding": settings.embedding_model,
        "reranker": RERANKER_MODEL,
        "slm": None,  # Phase 7
    }


STATUS_BY_ROUTE = {
    "FAST_QA_RESPONSE": "SUCCESS",
    "MARKDOWN_RAG_RESPONSE": "SUCCESS",
    "DIRECT_RESPONSE": "SUCCESS",
    "NO_ANSWER": "NO_ANSWER",
    "CLARIFY": "CLARIFY",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    "CAPABILITY_PENDING": "NOT_AVAILABLE",
    "BLOCKED": "BLOCKED",
}


def _insert(conn, row: dict) -> int:
    columns = ", ".join(row)
    placeholders = ", ".join(["%s"] * len(row))
    values = [Jsonb(v) if isinstance(v, (dict, list)) else v for v in row.values()]
    return conn.execute(f"INSERT INTO audit_events ({columns}) VALUES ({placeholders}) RETURNING audit_id",
                        values).fetchone()[0]


def record_chat(
    *,
    request_id: str,
    question: str,
    session_id: str | None,
    response,  # api.models.ChatResponse
    usage: RequestUsage | None,
    error: Exception | None = None,
) -> int | None:
    """Write the audit row for one /chat request. Never raises."""
    if not is_available():
        return None
    started = time.perf_counter()
    try:
        context = (response.context if response is not None else None) or {}
        trace = (response.decision_trace if response is not None else None) or {}
        ui = context.get("ui") or {}
        record = context.get("record") or {}
        route = response.route if response is not None else "ERROR"
        denied = route == "BLOCKED" and (trace.get("security") in (None, "SEC_SAFE"))
        answer = (response.answer or "") if response is not None else ""
        row = {
            "event_type": "chat",
            "request_id": request_id,
            "trace_id": request_id,
            "user_id": context.get("user_id"),
            "user_groups": ",".join(context.get("groups") or []) or None,
            "session_id": session_id,
            "message_id": response.message_id if response is not None else None,
            "site": context.get("site"),
            "module": ui.get("module"),
            "form": ui.get("form"),
            "record_type": record.get("record_type"),
            "record_id": record.get("record_id"),
            "question_sha256": _sha(question),
            "question_text": redact(question[:QUESTION_MAX_CHARS]) if settings.audit_store_question_text else None,
            "intent": trace.get("intent"),
            "route": route,
            "tool": trace.get("tool_candidate"),
            "authorization_result": "DENY" if denied else "ALLOW",
            "security_label": trace.get("security"),
            "status": "ERROR" if error else STATUS_BY_ROUTE.get(route, route),
            "grounding": response.grounding if response is not None else None,
            "mood": trace.get("emotion"),
            "escalation": trace.get("escalation"),
            "sources": (response.sources or ([response.source] if response.source else [])) if response else [],
            "answer_sha256": _sha(answer),
            "answer_preview": (redact(answer[:ANSWER_PREVIEW_CHARS]) if settings.audit_store_answer_preview
                               else None),
            "answer_chars": len(answer),
            "models": model_versions(),
            "latency_ms": usage.elapsed_ms() if usage else None,
            "stages_ms": usage.stages_ms if usage else {},
            "db_ms": usage.db_ms if usage else {},
            "llm_calls": [c.as_dict() for c in usage.llm_calls] if usage else [],
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "cost_usd": round(usage.cost_usd, 6) if usage else 0,
            "error": f"{type(error).__name__}: {redact(str(error))[:300]}" if error else None,
            "details": {k: trace.get(k) for k in ("answer_source", "validation", "validation_llm_checked",
                                                   "conversation_source", "classifier", "escalation_trigger",
                                                   "followup_resolved") if trace.get(k) is not None},
        }
        with history_store.shared_pool().connection() as conn:
            audit_id = _insert(conn, row)
        log_event(logger, "audit_recorded", request_id=request_id, audit_id=audit_id, status=row["status"],
                  ms=round((time.perf_counter() - started) * 1000, 1))
        return audit_id
    except Exception:
        logger.exception("event=audit_record_failed request_id=%s", request_id)
        return None


def record_action(event_type: str, *, user_id: str | None, request_id: str | None = None,
                  message_id: int | None = None, session_id: str | None = None, details: dict | None = None) -> None:
    """Admin / ticket / rating actions: who did what, when. Never raises."""
    if not is_available():
        return
    try:
        with history_store.shared_pool().connection() as conn:
            _insert(conn, {"event_type": event_type, "request_id": request_id, "trace_id": request_id,
                           "user_id": user_id, "message_id": message_id, "session_id": session_id,
                           "status": "SUCCESS", "details": details or {}})
    except Exception:
        logger.exception("event=audit_action_failed type=%s", event_type)


def purge_expired() -> int:
    """Delete audit rows older than AUDIT_RETENTION_DAYS (the only delete the trigger allows)."""
    if not is_available():
        return 0
    with history_store.shared_pool().connection() as conn:
        with conn.transaction():
            conn.execute("SET LOCAL audit.retention_purge = 'on'")
            deleted = conn.execute(
                "DELETE FROM audit_events WHERE created_at < now() - make_interval(days => %s)",
                (settings.audit_retention_days,),
            ).rowcount
    if deleted:
        record_action("retention_purge", user_id="system",
                      details={"deleted": deleted, "retention_days": settings.audit_retention_days})
    log_event(logger, "audit_retention_purge", deleted=deleted, retention_days=settings.audit_retention_days)
    return deleted


AUDIT_COLUMNS = ["audit_id", "created_at", "event_type", "request_id", "user_id", "user_groups", "session_id",
                 "message_id", "site", "module", "form", "record_type", "record_id", "question_text", "intent",
                 "route", "tool", "authorization_result", "security_label", "status", "grounding", "mood", "escalation",
                 "sources", "answer_preview", "answer_chars", "latency_ms", "prompt_tokens", "completion_tokens",
                 "cost_usd", "error", "details"]


def search(*, days: int = 7, user_id: str | None = None, event_type: str | None = None,
           status: str | None = None, request_id: str | None = None, limit: int = 200) -> list[dict]:
    """Admin console: find audit rows. Filters are parameterised (never string-built)."""
    conditions = ["created_at > now() - make_interval(days => %s)"]
    params: list = [max(1, min(int(days), 3650))]
    for column, value in (("user_id", user_id), ("event_type", event_type), ("status", status),
                          ("request_id", request_id)):
        if value:
            conditions.append(f"{column} = %s")
            params.append(value)
    params.append(max(1, min(int(limit), 1000)))
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(AUDIT_COLUMNS)} FROM audit_events WHERE {' AND '.join(conditions)} "
            "ORDER BY created_at DESC LIMIT %s",
            params,
        ).fetchall()
    result = []
    for row in rows:
        item = dict(zip(AUDIT_COLUMNS, row))
        item["created_at"] = item["created_at"].isoformat()
        item["cost_usd"] = float(item["cost_usd"]) if item["cost_usd"] is not None else None
        result.append(item)
    return result
