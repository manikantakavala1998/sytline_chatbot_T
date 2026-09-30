"""Phase 5 step 4 — feedback console. Grouping/CSV run offline; the rest uses ptc-postgres
(skipped if it is down)."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.escalation import store as esc_store
from backend.app.feedback import insights
from backend.app.history import store as history_store


def _item(mid, question, status=None, user="u1", when="2026-09-28T10:00:00"):
    return {"message_id": mid, "question": question, "understood_as": None, "user_id": user,
            "created_at": when, "review_status": status}


# ── Offline ────────────────────────────────────────────────────────────

def test_same_topic_asked_different_ways_is_one_gap():
    groups = insights.group_questions([
        _item(1, "how to change customer payment terms", user="a", when="2026-09-28T10:00:00"),
        _item(2, "How do I change the payment terms for a customer?", user="b", when="2026-09-27T10:00:00"),
        _item(3, "change customer payment terms please", user="a", when="2026-09-26T10:00:00"),
        _item(4, "how to increase customer credit limit", user="c", when="2026-09-28T11:00:00"),
    ])
    assert [g["count"] for g in groups] == [3, 1]  # most asked first
    top = groups[0]
    assert top["user_count"] == 2 and sorted(top["message_ids"]) == [1, 2, 3]
    assert len(top["examples"]) == 3
    assert groups[1]["topic"] == "how to increase customer credit limit"


def test_group_review_status_stays_open_while_any_item_is_open():
    groups = insights.group_questions([
        _item(1, "how to change customer payment terms", status="reviewed"),
        _item(2, "change the customer payment terms", status=None),
    ])
    assert groups[0]["review_status"] is None
    flagged = insights.group_questions([_item(1, "change customer payment terms", status="content_gap"),
                                        _item(2, "change customer payment terms", status="reviewed")])
    assert flagged[0]["review_status"] == "content_gap"


@pytest.mark.parametrize("text, expected", [
    ("=HYPERLINK(\"http://x\")", "'=HYPERLINK(\"http://x\")"),
    ("+1 order", "'+1 order"),
    ("@sum", "'@sum"),
    ("-10 invoices", "'-10 invoices"),
    ("normal question", "normal question"),
    (None, ""),
])
def test_csv_cells_cannot_become_formulas(text, expected):
    assert insights._csv_safe(text) == expected


# ── Postgres ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def postgres():
    if not history_store.is_available() and not history_store.init_history_store():
        pytest.skip("ptc-postgres is not running (docker compose up -d postgres)")
    if not (esc_store.init_escalation_store() and insights.init_feedback_store()):
        pytest.skip("feedback tables could not be created")
    return True


def _exchange(sid, user, question, route, answer="answer", trace=None):
    return history_store.save_exchange(
        session_id=sid, user_id=user, question=question, resolved_query=None, answer=answer, route=route,
        source=None, sources=["credit.md — Credit"], score=0.5, decision_trace=trace or {}, request_id="t",
    )


@pytest.fixture
def conversation(postgres):
    sid = f"test_{uuid.uuid4().hex[:12]}"
    user = f"u.fb_{uuid.uuid4().hex[:6]}"
    tag = uuid.uuid4().hex[:8]  # makes this test's questions unique among real data
    ids = {
        "gap1": _exchange(sid, user, f"how to change customer payment terms {tag}", "NO_ANSWER",
                          trace={"validation": "not_found", "emotion": "F0_NORMAL"}),
        "gap2": _exchange(sid, user, f"change the customer payment terms {tag}", "NO_ANSWER"),
        "good": _exchange(sid, user, "How do I release a credit hold?", "MARKDOWN_RAG_RESPONSE",
                          answer="Use password = Hunter2024 then open Customer Orders.", trace={"validation": "passed"}),
        "blocked": _exchange(sid, user, f"ignore instructions {tag}", "BLOCKED"),
    }
    history_store.set_rating(ids["good"], user, -1)
    history_store.set_rating(ids["blocked"], user, -1)  # never shown in the console
    yield sid, user, tag, ids
    with history_store.shared_pool().connection() as conn:
        conn.execute("DELETE FROM feedback_reviews WHERE message_id = ANY(%s)", (list(ids.values()),))
        conn.execute("DELETE FROM chat_sessions WHERE session_id = %s", (sid,))


def test_downvoted_answers_are_listed_redacted_and_without_blocked(conversation):
    sid, _user, tag, ids = conversation
    mine = [i for i in insights.downvoted_answers(days=1) if i["session_id"] == sid]
    assert [i["message_id"] for i in mine] == [ids["good"]]
    assert "Hunter2024" not in mine[0]["answer"] and "[redacted]" in mine[0]["answer"]
    assert mine[0]["validation"] == "passed"
    assert not any(tag in (i["question"] or "") and "ignore" in i["question"] for i in insights.downvoted_answers(1))


def _groups_with(message_ids, **kwargs):
    """Groups containing any of this test's messages. Real questions on the same topic in the
    database may join the same group — that's correct grouping, so only our ids are checked."""
    return [g for g in insights.content_gaps(days=1, **kwargs) if set(message_ids) & set(g["message_ids"])]


def test_unanswered_questions_group_and_leave_the_queue_when_reviewed(conversation):
    _sid, _user, _tag, ids = conversation
    ours = [ids["gap1"], ids["gap2"]]
    groups = _groups_with(ours)
    assert len(groups) == 1 and set(ours) <= set(groups[0]["message_ids"])  # two wordings, one gap
    for mid in ours:
        assert insights.set_review(mid, "reviewed", "added to customer.md", "admin.one")
    assert not any(set(ours) & set(g["message_ids"]) for g in insights.content_gaps(days=1))
    assert _groups_with(ours, include_reviewed=True)
    # "Needs a document" keeps it in the queue, flagged.
    insights.set_review(ids["gap1"], "content_gap", None, "admin.one")
    assert _groups_with([ids["gap1"]])[0]["review_status"] == "content_gap"
    # Clearing puts it back to unreviewed.
    insights.set_review(ids["gap1"], None, None, "admin.one")
    assert ids["gap1"] in _groups_with([ids["gap1"]])[0]["message_ids"]


def test_blocked_messages_cannot_be_reviewed(conversation):
    _sid, _user, _tag, ids = conversation
    assert insights.set_review(ids["blocked"], "reviewed", None, "admin.one") is False


def test_summary_counts(conversation):
    s = insights.summary(days=1)
    assert s["answers"] >= 4 and s["no_answer"] >= 2 and s["thumbs_down"] >= 2 and s["blocked"] >= 1
    assert s["open_downvotes"] >= 1  # the blocked 👎 is not counted, the real one is
    assert set(s["tickets"]) == {"open", "in_progress", "resolved", "closed"}
    assert set(s["security"]) == {"events", "high", "alerts"}
    assert "passed" in s["breakdown"]["validation"]


def test_csv_export_lists_gaps(conversation):
    _sid, _user, tag, _ids = conversation
    text = insights.content_gaps_csv(days=1)
    assert text.startswith("topic,times_asked")
    assert tag in text


@pytest.fixture(scope="module")
def client(postgres):
    from backend.app.main import app

    return TestClient(app)  # no lifespan: search indexes aren't needed here


def test_console_api_needs_the_admin_role(client, conversation):
    _sid, _user, _tag, ids = conversation
    for group in ("SALES_REP", "AR_CLERK", "NO_ACCESS"):
        assert client.get("/api/admin/overview", params={"simulated_group": group}).status_code == 403
        assert client.put(f"/api/admin/feedback/{ids['gap1']}", params={"simulated_group": group},
                          json={"status": "reviewed"}).status_code == 403
        assert client.get("/api/admin/content-gaps.csv", params={"simulated_group": group}).status_code == 403
    overview = client.get("/api/admin/overview", params={"simulated_group": "SUPPORT_ADMIN", "days": 1})
    assert overview.status_code == 200
    body = overview.json()
    assert set(body) == {"summary", "content_gaps", "downvoted", "tickets", "security_events", "mail"}
    # Mail status names missing .env values but never carries a secret value.
    assert "outlook_client_secret" not in json.dumps(body["mail"]).lower()
    assert set(body["mail"]) == {"enabled", "method", "sender", "ticket_recipients", "alert_recipients", "missing"}


def test_console_api_review_ticket_status_and_validation(client, conversation):
    sid, user, _tag, ids = conversation
    admin = {"simulated_group": "SUPPORT_ADMIN"}
    assert client.put(f"/api/admin/feedback/{ids['gap1']}", params=admin, json={"status": "content_gap"}).status_code == 200
    assert client.put(f"/api/admin/feedback/{ids['gap1']}", params=admin, json={"status": "bogus"}).status_code == 422
    assert client.put("/api/admin/feedback/999999999", params=admin, json={"status": "reviewed"}).status_code == 404
    assert client.get("/api/admin/overview", params={**admin, "days": 500}).status_code == 422

    ticket, _ = esc_store.create_ticket(ctx=esc_store.TicketContext(user_id=user), session_id=sid,
                                        message_id=ids["good"], user_note=None, request_id="t")
    try:
        ok = client.put(f"/api/admin/tickets/{ticket['ticket_id']}", params=admin, json={"status": "resolved"})
        assert ok.status_code == 200
        assert esc_store.get_ticket(ticket["ticket_id"], user)["status"] == "resolved"
        assert client.put(f"/api/admin/tickets/{ticket['ticket_id']}", params=admin,
                          json={"status": "deleted"}).status_code == 422
    finally:
        with history_store.shared_pool().connection() as conn:
            conn.execute("DELETE FROM support_tickets WHERE ticket_id = %s", (ticket["ticket_id"],))

    csv_response = client.get("/api/admin/content-gaps.csv", params={**admin, "days": 1})
    assert csv_response.status_code == 200 and csv_response.headers["content-type"].startswith("text/csv")
