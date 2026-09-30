"""Support tickets and security events in PostgreSQL (Phase 5 step 3).

Two separate tables on the conversation-history pool, because they are two separate flows
(master prompt §55 vs §56):

  support_tickets   created only after the user confirms; owned by that user
  security_events   one row per blocked attack or blocked answer leak; never shown to users,
                    only to the admin console; repeated attempts raise an alert

Tickets are built from the STORED conversation (not from text the browser sends), so a user
can't put words into a ticket that the chatbot never saw. Blocked turns are left out of the
ticket summary, and secrets are redacted from every stored text.
"""

import hashlib
from dataclasses import dataclass

from psycopg.types.json import Jsonb

from backend.app.classification.taxonomy import SecurityLabel
from backend.app.config import settings
from backend.app.history import store as history_store
from backend.app.quality.answer_validator import SECRET_PATTERNS
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

SUMMARY_TURNS = 6
ANSWER_CHARS_IN_SUMMARY = 300
EXCERPT_CHARS = 300
NOTE_MAX_CHARS = 1000

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id            BIGSERIAL PRIMARY KEY,
    user_id              TEXT NOT NULL,
    user_display_name    TEXT,
    session_id           TEXT,
    message_id           BIGINT,
    site                 TEXT,
    module               TEXT,
    form                 TEXT,
    record_type          TEXT,
    record_id            TEXT,
    issue_summary        TEXT NOT NULL,
    steps_attempted      JSONB NOT NULL DEFAULT '[]',
    user_note            TEXT,
    conversation_summary JSONB NOT NULL DEFAULT '[]',
    mood                 TEXT,
    trigger              TEXT,
    priority             TEXT NOT NULL DEFAULT 'normal',
    status               TEXT NOT NULL DEFAULT 'open',
    request_id           TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Whether the ticket mail went out: pending | sent | failed | not_configured | logged.
ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS notification_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS notified_at TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS ux_support_tickets_message
    ON support_tickets (session_id, message_id) WHERE message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_support_tickets_user ON support_tickets (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS security_events (
    event_id        BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    session_id      TEXT,
    request_id      TEXT,
    event_type      TEXT NOT NULL,
    label           TEXT NOT NULL,
    severity        TEXT NOT NULL,
    site            TEXT,
    module          TEXT,
    form            TEXT,
    query_sha256    TEXT,
    query_excerpt   TEXT,
    alert_raised    BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_security_events_user ON security_events (user_id, created_at DESC);
"""

_available = False

# Security gate labels -> severity. Anything not listed is "medium".
RESPONSE_LEAK_LABEL = "RESPONSE_LEAK_BLOCKED"
HIGH_SEVERITY = {
    SecurityLabel.CREDENTIAL_REQUEST.value,
    SecurityLabel.DATA_EXFILTRATION.value,
    SecurityLabel.PERMISSION_BYPASS.value,
    SecurityLabel.TOOL_ABUSE.value,
    RESPONSE_LEAK_LABEL,
}


def init_escalation_store() -> bool:
    """Create the tables on the history pool. Fail-soft like history: False if Postgres is down."""
    global _available
    if not history_store.is_available():
        _available = False
        log_event(logger, "escalation_store_unavailable", reason="history_store_down")
        return False
    try:
        with history_store.shared_pool().connection() as conn:
            conn.execute(SCHEMA_SQL)
        _available = True
        log_event(logger, "escalation_store_ready")
    except Exception as exc:
        _available = False
        log_event(logger, "escalation_store_unavailable", error=type(exc).__name__)
    return _available


def is_available() -> bool:
    return _available and history_store.is_available()


def redact(text: str | None) -> str | None:
    if not text:
        return text
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


# ── Support tickets ────────────────────────────────────────────────────


@dataclass
class TicketContext:
    """Trusted identity + the screen the user was on (same trust level as /chat context)."""

    user_id: str
    user_display_name: str | None = None
    site: str | None = None
    module: str | None = None
    form: str | None = None
    record_type: str | None = None
    record_id: str | None = None


def build_ticket_content(messages: list[dict], message_id: int | None) -> dict:
    """Issue summary, steps attempted and a safe summary from the stored conversation.

    `messages` are the session's stored messages (oldest first). The conversation is cut at the
    answer the ticket was raised from; BLOCKED exchanges are left out entirely.
    """
    if message_id is not None:
        cut = next((i for i, m in enumerate(messages) if m["message_id"] == message_id), None)
        if cut is not None:
            messages = messages[: cut + 1]

    exchanges = []
    pending = None
    for message in messages:
        if message["role"] == "user":
            pending = message
        elif pending is not None:
            if message.get("route") not in ("BLOCKED", "ERROR"):
                exchanges.append((pending, message))
            pending = None

    summary = []
    for question, answer in exchanges[-SUMMARY_TURNS:]:
        text = answer.get("content") or ""
        summary.append({
            "question": redact(question.get("resolved_query") or question.get("content")),
            "outcome": answer.get("route"),
            "answer": redact(text[:ANSWER_CHARS_IN_SUMMARY] + ("…" if len(text) > ANSWER_CHARS_IN_SUMMARY else "")),
        })

    last = exchanges[-1] if exchanges else None
    trace = (last[1].get("decision_trace") or {}) if last else {}
    return {
        "issue_summary": summary[-1]["question"] if summary else "User asked for help from the support team.",
        "steps_attempted": [f"{s['question']} → {s['outcome']}" for s in summary[:-1]],
        "conversation_summary": summary,
        "mood": trace.get("emotion"),
        "trigger": trace.get("escalation_trigger"),
    }


def _ticket_ref(ticket_id: int) -> str:
    return f"PTC-{ticket_id:06d}"


def create_ticket(
    *,
    ctx: TicketContext,
    session_id: str | None,
    message_id: int | None,
    user_note: str | None,
    request_id: str,
) -> tuple[dict, bool] | None:
    """Create a ticket from the user's own conversation. Returns (ticket, created) — created is
    False when this answer already has a ticket (double click). None if the session isn't theirs."""
    pool = history_store.shared_pool()
    with pool.connection() as conn:
        messages: list[dict] = []
        if session_id:
            if not history_store.owns_session(conn, session_id, ctx.user_id):
                return None
            messages = history_store.get_session_messages(session_id, ctx.user_id) or []
            if message_id is not None and not any(
                m["message_id"] == message_id and m["role"] == "assistant" for m in messages
            ):
                return None
            existing = conn.execute(
                "SELECT ticket_id FROM support_tickets WHERE session_id = %s AND message_id = %s",
                (session_id, message_id),
            ).fetchone() if message_id is not None else None
            if existing:
                return get_ticket(int(existing[0]), ctx.user_id), False

        content = build_ticket_content(messages, message_id)
        priority = "high" if content["mood"] in ("F3_FRUSTRATED", "F4_PERSISTENT") else "normal"
        note = redact((user_note or "").strip()[:NOTE_MAX_CHARS]) or None
        row = conn.execute(
            """
            INSERT INTO support_tickets
                (user_id, user_display_name, session_id, message_id, site, module, form, record_type,
                 record_id, issue_summary, steps_attempted, user_note, conversation_summary, mood,
                 trigger, priority, request_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ticket_id
            """,
            (
                ctx.user_id, ctx.user_display_name, session_id, message_id, ctx.site, ctx.module, ctx.form,
                ctx.record_type, ctx.record_id, content["issue_summary"], Jsonb(content["steps_attempted"]),
                note, Jsonb(content["conversation_summary"]), content["mood"],
                content["trigger"] or "user_confirmed", priority, request_id,
            ),
        ).fetchone()
    ticket = get_ticket(int(row[0]), ctx.user_id)
    log_event(logger, "support_ticket_created", request_id=request_id, ticket=ticket["ticket_ref"],
              priority=priority, trigger=ticket["trigger"])
    return ticket, True


_TICKET_COLUMNS = (
    "ticket_id, user_id, user_display_name, session_id, message_id, site, module, form, record_type, "
    "record_id, issue_summary, steps_attempted, user_note, conversation_summary, mood, trigger, priority, "
    "status, notification_status, created_at"
)


def _ticket_row(row) -> dict:
    keys = [c.strip() for c in _TICKET_COLUMNS.split(",")]
    ticket = dict(zip(keys, row))
    ticket["ticket_ref"] = _ticket_ref(ticket["ticket_id"])
    ticket["created_at"] = ticket["created_at"].isoformat()
    return ticket


def set_notification_status(ticket_id: int, status: str) -> None:
    with history_store.shared_pool().connection() as conn:
        conn.execute(
            "UPDATE support_tickets SET notification_status = %s, notified_at = now() WHERE ticket_id = %s",
            (status, ticket_id),
        )


def get_ticket(ticket_id: int, user_id: str) -> dict | None:
    with history_store.shared_pool().connection() as conn:
        row = conn.execute(
            f"SELECT {_TICKET_COLUMNS} FROM support_tickets WHERE ticket_id = %s AND user_id = %s",
            (ticket_id, user_id),
        ).fetchone()
    return _ticket_row(row) if row else None


def list_user_tickets(user_id: str, limit: int = 50) -> list[dict]:
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            f"SELECT {_TICKET_COLUMNS} FROM support_tickets WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        ).fetchall()
    return [_ticket_row(r) for r in rows]


def list_all_tickets(limit: int = 100) -> list[dict]:
    """Admin console only — the route checks the admin permission first."""
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            f"SELECT {_TICKET_COLUMNS} FROM support_tickets ORDER BY created_at DESC LIMIT %s", (limit,)
        ).fetchall()
    return [_ticket_row(r) for r in rows]


# ── Security events ────────────────────────────────────────────────────


def record_security_event(
    *,
    user_id: str,
    session_id: str | None,
    request_id: str,
    event_type: str,
    label: str,
    query: str,
    site: str | None = None,
    module: str | None = None,
    form: str | None = None,
) -> dict:
    """Store one blocked attack / blocked leak. Returns the event, with alert_raised set when this
    user has now been blocked `security_alert_threshold` times inside the alert window."""
    severity = "high" if label in HIGH_SEVERITY else "medium"
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    excerpt = redact(query[:EXCERPT_CHARS])
    with history_store.shared_pool().connection() as conn:
        recent = conn.execute(
            """
            SELECT count(*) FROM security_events
            WHERE user_id = %s AND created_at > now() - make_interval(mins => %s)
            """,
            (user_id, settings.security_alert_window_minutes),
        ).fetchone()[0]
        already_alerted = conn.execute(
            """
            SELECT 1 FROM security_events
            WHERE user_id = %s AND alert_raised AND created_at > now() - make_interval(mins => %s)
            """,
            (user_id, settings.security_alert_window_minutes),
        ).fetchone()
        # One alert per burst: raise it when the threshold is reached, not on every later attempt.
        alert = recent + 1 >= settings.security_alert_threshold and not already_alerted
        row = conn.execute(
            """
            INSERT INTO security_events
                (user_id, session_id, request_id, event_type, label, severity, site, module, form,
                 query_sha256, query_excerpt, alert_raised)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING event_id, created_at
            """,
            (user_id, session_id, request_id, event_type, label, severity, site, module, form, digest,
             excerpt, alert),
        ).fetchone()
    event = {
        "event_id": int(row[0]), "user_id": user_id, "session_id": session_id, "request_id": request_id,
        "event_type": event_type, "label": label, "severity": severity, "site": site, "module": module,
        "form": form, "attempts_in_window": recent + 1, "alert_raised": alert, "created_at": row[1].isoformat(),
    }
    log_event(logger, "security_event_recorded", request_id=request_id, label=label, severity=severity,
              attempts_in_window=recent + 1, alert=alert)
    return event


def list_security_events(limit: int = 200) -> list[dict]:
    """Admin console only. Only a redacted 300-character excerpt and a SHA-256 of the message are
    stored — enough to investigate and to spot the same attack repeated, without keeping secrets."""
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT event_id, user_id, session_id, request_id, event_type, label, severity, site, module, form,
                   query_excerpt, alert_raised, created_at
            FROM security_events ORDER BY created_at DESC LIMIT %s
            """,
            (limit,),
        ).fetchall()
    keys = ["event_id", "user_id", "session_id", "request_id", "event_type", "label", "severity", "site",
            "module", "form", "query_excerpt", "alert_raised", "created_at"]
    events = [dict(zip(keys, r)) for r in rows]
    for event in events:
        event["created_at"] = event["created_at"].isoformat()
    return events
