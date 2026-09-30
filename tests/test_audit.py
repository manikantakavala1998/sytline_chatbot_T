"""Phase 6 — audit trail and per-request measurements. Store tests need ptc-postgres (skipped if down)."""

import time
import uuid
from types import SimpleNamespace

import pytest
from psycopg.errors import RaiseException

from backend.app.api.models import ChatResponse
from backend.app.audit import store as audit_store
from backend.app.config import settings
from backend.app.escalation import store as esc_store
from backend.app.feedback import insights
from backend.app.history import store as history_store
from backend.app.monitoring import usage
from backend.app.orchestration.step_trace import traced


# ── Measurements (no database) ─────────────────────────────────────────

class _FakeClient:
    def __init__(self, fail=False):
        self.fail = fail
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        if self.fail:
            raise TimeoutError("slow")
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1000, completion_tokens=200))


def test_llm_calls_are_measured_with_tokens_and_cost():
    measured = usage.start()
    try:
        usage.metered_create("answer", _FakeClient(), model="gpt-4.1", messages=[])
        usage.metered_create("understanding", _FakeClient(), model="gpt-4.1-mini", messages=[])
    finally:
        usage.end()
    assert [c.purpose for c in measured.llm_calls] == ["answer", "understanding"]
    assert measured.prompt_tokens == 2000 and measured.completion_tokens == 400
    # gpt-4.1: 1000×$2 + 200×$8 per 1M = $0.0036; mini: 1000×$0.40 + 200×$1.60 = $0.00072
    assert measured.cost_usd == pytest.approx(0.0036 + 0.00072)


def test_failed_llm_call_is_recorded_and_still_raises():
    measured = usage.start()
    try:
        with pytest.raises(TimeoutError):
            usage.metered_create("classifier", _FakeClient(fail=True), model="gpt-4.1-mini", messages=[])
    finally:
        usage.end()
    call = measured.llm_calls[0]
    assert (call.ok, call.error, call.prompt_tokens) == (False, "TimeoutError", 0)


def test_unknown_model_costs_nothing_rather_than_crashing():
    call = usage.LLMCall(purpose="x", model="some-new-model", seconds=0.1, prompt_tokens=10, completion_tokens=10)
    assert call.cost_usd == 0.0


def test_nothing_is_recorded_outside_a_request():
    usage.end()
    usage.record_stage("x", 1.0)
    usage.record_db("x", 1.0)
    usage.metered_create("answer", _FakeClient(), model="gpt-4.1", messages=[])  # no error


def test_graph_steps_are_timed():
    measured = usage.start()
    try:
        traced("scope_check", lambda state: (time.sleep(0.01), {"scope": None})[1])({})
    finally:
        usage.end()
    assert measured.stages_ms["scope_check"] >= 10


# ── Audit store (Postgres) ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def audit(request):
    if not history_store.is_available() and not history_store.init_history_store():
        pytest.skip("ptc-postgres is not running (docker compose up -d postgres)")
    esc_store.init_escalation_store()
    insights.init_feedback_store()
    if not audit_store.init_audit_store():
        pytest.skip("audit table could not be created")
    yield True
    # Test rows are removed the only way the trigger allows, then the store is switched off again so
    # later test modules keep testing the chat-history fallback.
    with history_store.shared_pool().connection() as conn:
        with conn.transaction():
            conn.execute("SET LOCAL audit.retention_purge = 'on'")
            conn.execute("DELETE FROM audit_events WHERE request_id LIKE 'test-audit-%' "
                         "OR user_id LIKE 'u.audit_%'")
    audit_store._available = False


def _response(**overrides) -> ChatResponse:
    values = dict(
        route="MARKDOWN_RAG_RESPONSE", answer="Open Customer Orders and clear Credit Hold. password=Hunter2024",
        sources=["credit.md — Release a hold"], score=0.9, grounding="passed", message_id=None,
        context={"user_id": "u.audit_1", "groups": ["SALES_REP"], "site": "MAIN",
                 "ui": {"module": "CRM", "form": "Customer Orders"}, "record": {"record_type": None, "record_id": None}},
        decision_trace={"intent": "HELP_PROCESS", "security": "SEC_SAFE", "emotion": "F0_NORMAL",
                        "escalation": "ESC_NONE", "validation": "passed", "classifier": "llm"},
    )
    values.update(overrides)
    return ChatResponse(**values)


def _row(audit_id):
    return [e for e in audit_store.search(days=1, limit=1000) if e["audit_id"] == audit_id][0]


def test_chat_request_is_audited_with_measurements(audit):
    measured = usage.start()
    usage.metered_create("answer", _FakeClient(), model="gpt-4.1", messages=[])
    usage.record_stage("markdown_rag", 1.25)
    usage.end()
    rid = f"test-audit-{uuid.uuid4().hex[:8]}"
    audit_id = audit_store.record_chat(request_id=rid, question="how do I release a hold? my api_key=sk-abcdefghijklmnopqrstuv",
                                       session_id=None, response=_response(), usage=measured)
    row = _row(audit_id)
    assert (row["status"], row["authorization_result"], row["user_id"], row["form"]) == \
        ("SUCCESS", "ALLOW", "u.audit_1", "Customer Orders")
    assert "sk-abcdefghijklmnopqrstuv" not in row["question_text"]  # secrets masked
    assert "Hunter2024" not in row["answer_preview"]
    assert row["prompt_tokens"] == 1000 and row["cost_usd"] == pytest.approx(0.0036)
    with history_store.shared_pool().connection() as conn:
        stages, calls, models, sha = conn.execute(
            "SELECT stages_ms, llm_calls, models, question_sha256 FROM audit_events WHERE audit_id = %s", (audit_id,)
        ).fetchone()
    assert stages["markdown_rag"] == 1250 and calls[0]["purpose"] == "answer"
    assert models["answer"] == settings.primary_llm and len(sha) == 64


def test_permission_denied_and_errors_are_audited(audit):
    denied = audit_store.record_chat(
        request_id=f"test-audit-{uuid.uuid4().hex[:8]}", question="What is a lead?", session_id=None,
        response=_response(route="BLOCKED", answer=None, grounding=None, reason="denied",
                           decision_trace={"security": "SEC_SAFE"}), usage=None)
    assert (_row(denied)["status"], _row(denied)["authorization_result"]) == ("BLOCKED", "DENY")
    failed = audit_store.record_chat(request_id=f"test-audit-{uuid.uuid4().hex[:8]}", question="x", session_id=None,
                                     response=None, usage=None, error=RuntimeError("Milvus down"))
    assert _row(failed)["status"] == "ERROR" and "Milvus down" in _row(failed)["error"]


def test_audit_rows_cannot_be_changed_or_deleted(audit):
    audit_id = audit_store.record_chat(request_id=f"test-audit-{uuid.uuid4().hex[:8]}", question="q",
                                       session_id=None, response=_response(), usage=None)
    with history_store.shared_pool().connection() as conn:
        with pytest.raises(RaiseException, match="append-only"):
            conn.execute("UPDATE audit_events SET user_id = 'someone.else' WHERE audit_id = %s", (audit_id,))
    with history_store.shared_pool().connection() as conn:
        with pytest.raises(RaiseException, match="append-only"):
            conn.execute("DELETE FROM audit_events WHERE audit_id = %s", (audit_id,))
    assert _row(audit_id)["user_id"] == "u.audit_1"


def test_retention_purge_deletes_only_expired_rows(audit, monkeypatch):
    monkeypatch.setattr(settings, "audit_retention_days", 30)
    with history_store.shared_pool().connection() as conn:
        old_id = conn.execute("INSERT INTO audit_events (event_type, user_id, request_id, created_at) VALUES "
                              "('chat', 'u.audit_old', 'test-audit-old', now() - interval '40 days') "
                              "RETURNING audit_id").fetchone()[0]
    fresh = audit_store.record_chat(request_id=f"test-audit-{uuid.uuid4().hex[:8]}", question="q",
                                    session_id=None, response=_response(), usage=None)
    assert audit_store.purge_expired() >= 1
    with history_store.shared_pool().connection() as conn:
        assert conn.execute("SELECT 1 FROM audit_events WHERE audit_id = %s", (old_id,)).fetchone() is None
    assert _row(fresh)
    assert audit_store.search(days=1, event_type="retention_purge")  # the purge itself is audited


def test_feedback_survives_chat_deletion(audit):
    user = f"u.audit_{uuid.uuid4().hex[:6]}"
    sid = f"test_{uuid.uuid4().hex[:10]}"
    tag = uuid.uuid4().hex[:8]
    mid = history_store.save_exchange(session_id=sid, user_id=user, question=f"change payment terms {tag}",
                                      resolved_query=None, answer="not available", route="NO_ANSWER", source=None,
                                      sources=None, score=0.1, decision_trace={}, request_id="t")
    audit_store.record_chat(request_id=f"test-audit-{uuid.uuid4().hex[:8]}", question=f"change payment terms {tag}",
                            session_id=sid, usage=None,
                            response=_response(route="NO_ANSWER", message_id=mid, grounding="not_found",
                                               context={"user_id": user, "groups": [], "site": "MAIN",
                                                        "ui": {}, "record": {}}))
    history_store.set_rating(mid, user, -1)
    audit_store.record_action("rating", user_id=user, message_id=mid, details={"rating": -1})
    history_store.delete_session(sid, user)  # the user deletes the chat

    gaps = [g for g in insights.content_gaps(days=1) if mid in g["message_ids"]]
    assert gaps, "unanswered question lost after chat deletion"
    assert [d for d in insights.downvoted_answers(days=1) if d["message_id"] == mid]
    assert insights.set_review(mid, "reviewed", None, "admin")  # still reviewable
    with history_store.shared_pool().connection() as conn:
        conn.execute("DELETE FROM feedback_reviews WHERE message_id = %s", (mid,))


def test_audit_never_breaks_a_chat_when_the_store_is_down(monkeypatch):
    monkeypatch.setattr(audit_store, "_available", False)
    assert audit_store.record_chat(request_id="x", question="q", session_id=None, response=None, usage=None) is None
    audit_store.record_action("rating", user_id="u")  # no error


def test_audit_search_filters(audit):
    rid = f"test-audit-{uuid.uuid4().hex[:8]}"
    audit_store.record_chat(request_id=rid, question="q", session_id=None, response=_response(), usage=None)
    assert [e["request_id"] for e in audit_store.search(days=1, request_id=rid)] == [rid]
    assert all(e["status"] == "SUCCESS" for e in audit_store.search(days=1, status="SUCCESS", limit=20))
