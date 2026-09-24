"""
Conversation history in PostgreSQL (ptc-postgres from docker-compose.yml).

Two tables, created on startup if missing:

  chat_sessions   one row per conversation, owned by one SyteLine user
  chat_messages   every user question and assistant answer, in order

Every read, write and delete is filtered by the trusted user_id from the
session bootstrap, so one user can never read or delete another user's
conversations — even if they guess a session id.

History is fail-soft: if Postgres is down, the chatbot still answers (it
just can't remember earlier turns), and a clear event is logged.
"""

from dataclasses import dataclass

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from backend.app.config import settings
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

TITLE_MAX_CHARS = 60
MAX_SESSIONS_LISTED = 50

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_updated
    ON chat_sessions (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id      BIGSERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES chat_sessions (session_id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    resolved_query  TEXT,
    route           TEXT,
    source          TEXT,
    sources         JSONB,
    score           REAL,
    decision_trace  JSONB,
    rating          SMALLINT CHECK (rating IN (-1, 1)),
    request_id      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_chat_messages_session
    ON chat_messages (session_id, message_id);
"""

_pool: ConnectionPool | None = None
_available = False


class HistoryUnavailableError(RuntimeError):
    pass


@dataclass
class Turn:
    """One earlier exchange, as the follow-up resolver needs it."""

    question: str
    answer: str


def _conninfo() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} dbname={settings.postgres_db} "
        f"user={settings.postgres_user} password={settings.postgres_password} connect_timeout=3"
    )


def init_history_store() -> bool:
    """Open the pool and create the tables. Returns False (and logs) if Postgres is unreachable."""
    global _pool, _available
    try:
        _pool = ConnectionPool(_conninfo(), min_size=1, max_size=5, open=True, timeout=5)
        with _pool.connection() as conn:
            conn.execute(SCHEMA_SQL)
        _available = True
        log_event(
            logger, "history_store_ready",
            host=settings.postgres_host, port=settings.postgres_port, db=settings.postgres_db,
        )
    except Exception as exc:  # any connection/auth failure — keep the chatbot running
        _available = False
        if _pool is not None:
            _pool.close()
            _pool = None
        log_event(logger, "history_store_unavailable", error=type(exc).__name__)
        logger.warning(
            "Conversation history disabled: can't reach Postgres at %s:%s. "
            "Start it with `docker compose up -d postgres`.",
            settings.postgres_host, settings.postgres_port,
        )
    return _available


def is_available() -> bool:
    return _available


def _require_pool() -> ConnectionPool:
    if not _available or _pool is None:
        raise HistoryUnavailableError("Conversation history store is not available")
    return _pool


def _owns(conn, session_id: str, user_id: str) -> bool:
    row = conn.execute("SELECT user_id FROM chat_sessions WHERE session_id = %s", (session_id,)).fetchone()
    return row is not None and row[0] == user_id


def recent_turns(session_id: str, user_id: str, limit: int) -> list[Turn]:
    """Last `limit` answered question/answer pairs, oldest first. Blocked turns are skipped
    so text the security gate rejected is never fed back into a model."""
    with _require_pool().connection() as conn:
        if not _owns(conn, session_id, user_id):
            return []
        rows = conn.execute(
            """
            SELECT role, content, route FROM chat_messages
            WHERE session_id = %s ORDER BY message_id DESC LIMIT %s
            """,
            (session_id, limit * 2 + 2),
        ).fetchall()

    turns: list[Turn] = []
    pending_answer: tuple[str, str | None] | None = None
    for role, content, route in rows:  # newest first
        if role == "assistant":
            pending_answer = (content, route)
        elif pending_answer is not None:
            answer, route = pending_answer
            if route not in ("BLOCKED", "ERROR"):
                turns.append(Turn(question=content, answer=answer))
            pending_answer = None
        if len(turns) >= limit:
            break
    return list(reversed(turns))


def save_exchange(
    *,
    session_id: str,
    user_id: str,
    question: str,
    resolved_query: str | None,
    answer: str,
    route: str,
    source: str | None,
    sources: list[str] | None,
    score: float,
    decision_trace: dict | None,
    request_id: str,
) -> int | None:
    """Store one question + answer. Returns the answer's message_id (used for ratings),
    or None if the session id already belongs to a different user."""
    with _require_pool().connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_sessions (session_id, user_id, title) VALUES (%s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
            """,
            (session_id, user_id, question[:TITLE_MAX_CHARS]),
        )
        if not _owns(conn, session_id, user_id):
            log_event(logger, "history_session_owner_mismatch", request_id=request_id)
            return None
        conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, resolved_query, request_id)
            VALUES (%s, 'user', %s, %s, %s)
            """,
            (session_id, question, resolved_query, request_id),
        )
        row = conn.execute(
            """
            INSERT INTO chat_messages
                (session_id, role, content, route, source, sources, score, decision_trace, request_id)
            VALUES (%s, 'assistant', %s, %s, %s, %s, %s, %s, %s)
            RETURNING message_id
            """,
            (
                session_id, answer, route, source,
                Jsonb(sources) if sources is not None else None, score,
                Jsonb(decision_trace) if decision_trace is not None else None, request_id,
            ),
        ).fetchone()
        conn.execute("UPDATE chat_sessions SET updated_at = now() WHERE session_id = %s", (session_id,))
    return int(row[0])


def list_sessions(user_id: str, include_messages: bool = False) -> list[dict]:
    with _require_pool().connection() as conn:
        sessions = conn.execute(
            """
            SELECT session_id, title, created_at, updated_at FROM chat_sessions
            WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s
            """,
            (user_id, MAX_SESSIONS_LISTED),
        ).fetchall()
        result = [
            {"session_id": sid, "title": title, "created_at": created.isoformat(), "updated_at": updated.isoformat()}
            for sid, title, created, updated in sessions
        ]
        if include_messages:
            for session in result:
                session["messages"] = _messages(conn, session["session_id"])
    return result


def _messages(conn, session_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT message_id, role, content, resolved_query, route, source, sources, score, decision_trace,
               rating, created_at
        FROM chat_messages WHERE session_id = %s ORDER BY message_id
        """,
        (session_id,),
    ).fetchall()
    return [
        {
            "message_id": message_id, "role": role, "content": content, "resolved_query": resolved,
            "route": route, "source": source, "sources": sources, "score": score, "decision_trace": trace,
            "rating": rating, "created_at": created.isoformat(),
        }
        for message_id, role, content, resolved, route, source, sources, score, trace, rating, created in rows
    ]


def get_session_messages(session_id: str, user_id: str) -> list[dict] | None:
    with _require_pool().connection() as conn:
        if not _owns(conn, session_id, user_id):
            return None
        return _messages(conn, session_id)


def delete_session(session_id: str, user_id: str) -> bool:
    with _require_pool().connection() as conn:
        deleted = conn.execute(
            "DELETE FROM chat_sessions WHERE session_id = %s AND user_id = %s", (session_id, user_id)
        ).rowcount
    return deleted > 0


def delete_all_sessions(user_id: str) -> int:
    with _require_pool().connection() as conn:
        return conn.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,)).rowcount


def set_rating(message_id: int, user_id: str, rating: int | None) -> bool:
    """Thumbs up (1) / down (-1) / cleared (None) on an assistant message the user owns."""
    with _require_pool().connection() as conn:
        updated = conn.execute(
            """
            UPDATE chat_messages m SET rating = %s
            FROM chat_sessions s
            WHERE m.message_id = %s AND m.role = 'assistant'
              AND m.session_id = s.session_id AND s.user_id = %s
            """,
            (rating, message_id, user_id),
        ).rowcount
    return updated > 0


def close_history_store() -> None:
    global _pool, _available
    if _pool is not None:
        _pool.close()
    _pool = None
    _available = False
