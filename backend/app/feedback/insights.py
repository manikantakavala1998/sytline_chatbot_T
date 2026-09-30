"""Feedback loop for the admin console (Phase 5 step 4).

Turns what users did in the chat into work for the support and content teams:

  summary        answers, answered %, 👍/👎, answer-check outcomes, moods, ticket offers,
                 tickets by status, security events and alerts — for the last N days
  downvoted      every 👎 answer with its question, route, check result and sources
  content gaps   unanswered questions (route NO_ANSWER) grouped by topic, most asked
                 first — the list of documents that need writing
  reviews        an admin marks an item "content_gap" (needs a document), "reviewed"
                 (handled) or "dismissed"; reviewed/dismissed items leave the queue

Reads the conversation-history tables (admin permission is checked by the API). Blocked
exchanges are never listed here — attacks belong to the security-event view — and every text
is secret-redacted before it leaves this module.

Limitation (until Phase 6 audit storage): a user deleting a chat also deletes its messages,
so its 👎 and unanswered questions disappear from these lists.
"""

import csv
import io

from backend.app.escalation import store as escalation_store
from backend.app.history import store as history_store
from backend.app.quality.tone import topic_tokens
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

MAX_DAYS = 90
LIST_LIMIT = 200
ANSWER_PREVIEW_CHARS = 400
GROUP_SIMILARITY = 0.6
REVIEW_STATUSES = ("content_gap", "reviewed", "dismissed")
OPEN_STATUSES = (None, "content_gap")  # still in the queue
TICKET_STATUSES = ("open", "in_progress", "resolved", "closed")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS feedback_reviews (
    message_id   BIGINT PRIMARY KEY,
    status       TEXT NOT NULL CHECK (status IN ('content_gap', 'reviewed', 'dismissed')),
    note         TEXT,
    reviewer_id  TEXT NOT NULL,
    reviewed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_available = False


def init_feedback_store() -> bool:
    global _available
    if not history_store.is_available():
        _available = False
        return False
    try:
        with history_store.shared_pool().connection() as conn:
            conn.execute(SCHEMA_SQL)
        _available = True
        log_event(logger, "feedback_store_ready")
    except Exception as exc:
        _available = False
        log_event(logger, "feedback_store_unavailable", error=type(exc).__name__)
    return _available


def is_available() -> bool:
    return _available and history_store.is_available()


def _days(days: int) -> int:
    return max(1, min(int(days), MAX_DAYS))


# Every assistant answer with the question that produced it (the latest user message before it).
_ANSWERS_SQL = """
SELECT a.message_id, s.user_id, a.session_id, q.content, q.resolved_query, a.content, a.route,
       a.sources, a.rating, a.decision_trace, a.created_at, r.status, r.note, r.reviewer_id
FROM chat_messages a
JOIN chat_sessions s ON s.session_id = a.session_id
JOIN LATERAL (
    SELECT u.content, u.resolved_query FROM chat_messages u
    WHERE u.session_id = a.session_id AND u.role = 'user' AND u.message_id < a.message_id
    ORDER BY u.message_id DESC LIMIT 1
) q ON true
LEFT JOIN feedback_reviews r ON r.message_id = a.message_id
WHERE a.role = 'assistant' AND a.route <> 'BLOCKED'
  AND a.created_at > now() - make_interval(days => %s)
  AND {condition}
ORDER BY a.created_at DESC
LIMIT %s
"""


# (Phase 6) The same lists read from the permanent audit trail, so a 👎 or an unanswered question
# survives the user deleting the chat. The latest rating action per message wins.
_AUDIT_ANSWERS_SQL = """
WITH latest_rating AS (
    SELECT DISTINCT ON (message_id) message_id, NULLIF(details->>'rating', '')::int AS rating
    FROM audit_events WHERE event_type = 'rating' AND message_id IS NOT NULL
    ORDER BY message_id, audit_id DESC
)
SELECT a.message_id, a.user_id, a.session_id, a.question_text, a.answer_preview, a.route, a.sources,
       lr.rating, a.grounding, a.mood, a.intent, a.created_at, r.status, r.note, r.reviewer_id
FROM audit_events a
LEFT JOIN latest_rating lr ON lr.message_id = a.message_id
LEFT JOIN feedback_reviews r ON r.message_id = a.message_id
WHERE a.event_type = 'chat' AND a.message_id IS NOT NULL AND a.route <> 'BLOCKED'
  AND a.created_at > now() - make_interval(days => %s)
  AND {condition}
ORDER BY a.created_at DESC
LIMIT %s
"""
AUDIT_CONDITIONS = {"downvoted": "lr.rating = -1", "unanswered": "a.route = 'NO_ANSWER'"}
CHAT_CONDITIONS = {"downvoted": "a.rating = -1", "unanswered": "a.route = 'NO_ANSWER'"}


def _audit_on() -> bool:
    from backend.app.audit import store as audit_store  # imported late: audit imports this package's deps

    return audit_store.is_available()


def _audit_answer_rows(kind: str, days: int) -> list[dict]:
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(_AUDIT_ANSWERS_SQL.format(condition=AUDIT_CONDITIONS[kind]),
                            (_days(days), LIST_LIMIT)).fetchall()
    return [
        {"message_id": message_id, "user_id": user_id, "session_id": session_id,
         "question": escalation_store.redact(question), "understood_as": None,
         "answer": escalation_store.redact(answer or ""), "route": route, "sources": sources or [],
         "rating": rating, "validation": grounding, "mood": mood, "intent": intent,
         "created_at": created.isoformat(), "review_status": status, "review_note": note, "reviewer_id": reviewer}
        for (message_id, user_id, session_id, question, answer, route, sources, rating, grounding, mood, intent,
             created, status, note, reviewer) in rows
    ]


def _rows(kind: str, days: int) -> list[dict]:
    return _audit_answer_rows(kind, days) if _audit_on() else _answer_rows(CHAT_CONDITIONS[kind], days)


def _answer_rows(condition: str, days: int) -> list[dict]:
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(_ANSWERS_SQL.format(condition=condition), (_days(days), LIST_LIMIT)).fetchall()
    items = []
    for (message_id, user_id, session_id, question, resolved, answer, route, sources, rating, trace, created,
         status, note, reviewer) in rows:
        trace = trace or {}
        answer = answer or ""
        items.append({
            "message_id": message_id,
            "user_id": user_id,
            "session_id": session_id,
            "question": escalation_store.redact(question),
            "understood_as": escalation_store.redact(resolved),
            "answer": escalation_store.redact(
                answer[:ANSWER_PREVIEW_CHARS] + ("…" if len(answer) > ANSWER_PREVIEW_CHARS else "")
            ),
            "route": route,
            "sources": sources or [],
            "rating": rating,
            "validation": trace.get("validation"),
            "mood": trace.get("emotion"),
            "intent": trace.get("intent"),
            "created_at": created.isoformat(),
            "review_status": status,
            "review_note": note,
            "reviewer_id": reviewer,
        })
    return items


def downvoted_answers(days: int = 30, include_reviewed: bool = False) -> list[dict]:
    items = _rows("downvoted", days)
    return items if include_reviewed else [i for i in items if i["review_status"] in OPEN_STATUSES]


def group_questions(items: list[dict]) -> list[dict]:
    """Group unanswered questions by topic words, so "change payment terms" asked five ways is
    one content gap with count 5. Greedy: each question joins the first group it overlaps
    enough with (Jaccard of topic words ≥ GROUP_SIMILARITY)."""
    groups: list[dict] = []
    for item in items:  # newest first
        text = item["understood_as"] or item["question"] or ""
        tokens = topic_tokens(text)
        target = None
        for group in groups:
            union = tokens | group["_tokens"]
            if union and len(tokens & group["_tokens"]) / len(union) >= GROUP_SIMILARITY:
                target = group
                break
        if target is None:
            target = {"_tokens": set(tokens), "topic": text, "count": 0, "examples": [], "message_ids": [],
                      "users": set(), "last_asked": item["created_at"], "statuses": set()}
            groups.append(target)
        target["count"] += 1
        target["message_ids"].append(item["message_id"])
        target["users"].add(item["user_id"])
        target["statuses"].add(item["review_status"])
        if text not in target["examples"] and len(target["examples"]) < 5:
            target["examples"].append(text)
    result = []
    for group in groups:
        statuses = group.pop("statuses")
        group.pop("_tokens")
        group["user_count"] = len(group.pop("users"))
        group["review_status"] = "content_gap" if "content_gap" in statuses else (
            None if None in statuses else sorted(s for s in statuses if s)[0])
        result.append(group)
    result.sort(key=lambda g: (g["count"], g["last_asked"]), reverse=True)  # most asked, then most recent
    return result


def content_gaps(days: int = 30, include_reviewed: bool = False) -> list[dict]:
    items = _rows("unanswered", days)
    if not include_reviewed:
        items = [i for i in items if i["review_status"] in OPEN_STATUSES]
    return group_questions(items)


# Where the summary reads from: the audit trail (Phase 6, survives chat deletion, includes chats
# without a saved session) or, if it's unavailable, the chat history tables.
_SUMMARY_SOURCES = {
    "audit": {
        "rows": """
            WITH latest_rating AS (
                SELECT DISTINCT ON (message_id) message_id, NULLIF(details->>'rating', '')::int AS rating
                FROM audit_events WHERE event_type = 'rating' AND message_id IS NOT NULL
                ORDER BY message_id, audit_id DESC)
            SELECT a.*, lr.rating AS latest_rating FROM audit_events a
            LEFT JOIN latest_rating lr ON lr.message_id = a.message_id
            WHERE a.event_type = 'chat' AND a.created_at > now() - make_interval(days => %s)""",
        "rating": "latest_rating",
        "validation": "CASE WHEN grounding = 'approved' THEN NULL ELSE grounding END",
        "mood": "mood",
        "escalation": "escalation",
    },
    "chat": {
        "rows": """
            SELECT * FROM chat_messages
            WHERE role = 'assistant' AND created_at > now() - make_interval(days => %s)""",
        "rating": "rating",
        "validation": "decision_trace->>'validation'",
        "mood": "decision_trace->>'emotion'",
        "escalation": "decision_trace->>'escalation'",
    },
}


def summary(days: int = 7) -> dict:
    days = _days(days)
    source = _SUMMARY_SOURCES["audit" if _audit_on() else "chat"]
    with history_store.shared_pool().connection() as conn:
        row = conn.execute(
            f"""
            SELECT count(*),
                   count(*) FILTER (WHERE route IN ('FAST_QA_RESPONSE', 'MARKDOWN_RAG_RESPONSE')),
                   count(*) FILTER (WHERE route = 'NO_ANSWER'),
                   count(*) FILTER (WHERE route = 'CLARIFY'),
                   count(*) FILTER (WHERE route = 'BLOCKED'),
                   count(*) FILTER (WHERE {source['rating']} = 1),
                   count(*) FILTER (WHERE {source['rating']} = -1),
                   count(DISTINCT session_id)
            FROM ({source['rows']}) t
            """,
            (days,),
        ).fetchone()
        breakdown = {}
        for key in ("validation", "mood", "escalation", "route"):
            expression = source.get(key, key)
            breakdown[key] = {
                (label or "none"): count for label, count in conn.execute(
                    f"SELECT {expression}, count(*) FROM ({source['rows']}) t GROUP BY 1 ORDER BY 2 DESC",
                    (days,),
                ).fetchall()
            }
        tickets = dict(conn.execute(
            "SELECT status, count(*) FROM support_tickets WHERE created_at > now() - make_interval(days => %s) "
            "GROUP BY 1", (days,),
        ).fetchall()) if escalation_store.is_available() else {}
        security = conn.execute(
            """
            SELECT count(*), count(*) FILTER (WHERE severity = 'high'), count(*) FILTER (WHERE alert_raised)
            FROM security_events WHERE created_at > now() - make_interval(days => %s)
            """,
            (days,),
        ).fetchone() if escalation_store.is_available() else (0, 0, 0)
        open_downvotes = conn.execute(
            f"""
            SELECT count(*) FROM ({source['rows']}) a LEFT JOIN feedback_reviews r ON r.message_id = a.message_id
            WHERE a.{source['rating']} = -1 AND a.route <> 'BLOCKED'
              AND (r.status IS NULL OR r.status = 'content_gap')
            """,
            (days,),
        ).fetchone()[0]

    total, answered, no_answer, clarify, blocked, up, down, conversations = row
    answerable = total - blocked
    rated = up + down
    return {
        "days": days,
        "answers": total,
        "conversations": conversations,
        "answered": answered,
        "no_answer": no_answer,
        "clarify": clarify,
        "blocked": blocked,
        # Share of non-blocked questions that got a real answer (Excel or documents).
        "answered_pct": round(100 * answered / answerable, 1) if answerable else None,
        "thumbs_up": up,
        "thumbs_down": down,
        "satisfaction_pct": round(100 * up / rated, 1) if rated else None,
        "open_downvotes": open_downvotes,
        "breakdown": breakdown,
        "tickets": {status: tickets.get(status, 0) for status in TICKET_STATUSES},
        "security": {"events": security[0], "high": security[1], "alerts": security[2]},
    }


def set_review(message_id: int, status: str | None, note: str | None, reviewer_id: str) -> bool:
    """Mark a 👎 answer / unanswered question. status None clears the review (back in the queue)."""
    with history_store.shared_pool().connection() as conn:
        # The answer may still be in the chat, or — after the user deleted the chat — only in the
        # audit trail; either way it must exist and must not be a blocked attack.
        exists = conn.execute(
            """
            SELECT 1 FROM chat_messages WHERE message_id = %s AND role = 'assistant' AND route <> 'BLOCKED'
            UNION ALL
            SELECT 1 FROM audit_events WHERE to_regclass('audit_events') IS NOT NULL AND message_id = %s
                AND event_type = 'chat' AND route <> 'BLOCKED'
            LIMIT 1
            """,
            (message_id, message_id),
        ).fetchone() if _audit_on() else conn.execute(
            "SELECT 1 FROM chat_messages WHERE message_id = %s AND role = 'assistant' AND route <> 'BLOCKED'",
            (message_id,),
        ).fetchone()
        if not exists:
            return False
        if status is None:
            conn.execute("DELETE FROM feedback_reviews WHERE message_id = %s", (message_id,))
        else:
            conn.execute(
                """
                INSERT INTO feedback_reviews (message_id, status, note, reviewer_id) VALUES (%s, %s, %s, %s)
                ON CONFLICT (message_id) DO UPDATE
                    SET status = EXCLUDED.status, note = EXCLUDED.note, reviewer_id = EXCLUDED.reviewer_id,
                        reviewed_at = now()
                """,
                (message_id, status, escalation_store.redact(note), reviewer_id),
            )
    log_event(logger, "feedback_reviewed", message_id=message_id, status=status or "cleared", reviewer=reviewer_id)
    return True


def set_ticket_status(ticket_id: int, status: str, reviewer_id: str) -> bool:
    with history_store.shared_pool().connection() as conn:
        updated = conn.execute(
            "UPDATE support_tickets SET status = %s WHERE ticket_id = %s", (status, ticket_id)
        ).rowcount
    if updated:
        log_event(logger, "ticket_status_changed", ticket_id=ticket_id, status=status, reviewer=reviewer_id)
    return updated > 0


def content_gaps_csv(days: int = 30) -> str:
    """For the SME / content team: one row per topic with the wordings users actually typed."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["topic", "times_asked", "users", "last_asked", "review_status", "example_wordings"])
    for gap in content_gaps(days, include_reviewed=True):
        writer.writerow([
            _csv_safe(gap["topic"]), gap["count"], gap["user_count"], gap["last_asked"], gap["review_status"] or "",
            _csv_safe(" | ".join(gap["examples"])),
        ])
    return buffer.getvalue()


def _csv_safe(text: str | None) -> str:
    """Stop spreadsheet formula injection: a cell starting with = + - @ is shown as text."""
    text = text or ""
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text
