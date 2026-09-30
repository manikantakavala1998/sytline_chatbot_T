"""Phase 6 — health checks, alert rules and the Health tab numbers."""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.api.models import ChatResponse
from backend.app.audit import store as audit_store
from backend.app.config import settings
from backend.app.history import store as history_store
from backend.app.monitoring import health, usage

OK = {"ok": True, "ms": 1.0}


def _stats(**overrides):
    base = {"minutes": 15, "requests": 50, "errors": 0, "error_rate_pct": 0.0, "p95_latency_s": 8.0,
            "fallback_rate_pct": 0.0, "answerable": 40, "answered_pct": 90.0}
    base.update(overrides)
    return base


def _breached(stats, services=None, cost=0.0):
    services = services or {"postgres": OK, "milvus": OK, "redis": OK}
    return {r["rule"] for r in health._rules(stats, services, cost) if r["breached"]}


# ── Rules (no database) ────────────────────────────────────────────────

def test_healthy_system_breaks_no_rule():
    assert _breached(_stats()) == set()


@pytest.mark.parametrize("overrides, rule", [
    ({"errors": 5, "error_rate_pct": 10.0}, "error_rate"),
    ({"p95_latency_s": 40.0}, "slow_answers"),
    ({"fallback_rate_pct": 35.0}, "llm_fallbacks"),
    ({"answered_pct": 40.0}, "low_answered_rate"),
])
def test_each_rule_breaks_on_its_threshold(overrides, rule):
    assert _breached(_stats(**overrides)) == {rule}


def test_rates_are_not_judged_on_too_little_traffic():
    few = _stats(requests=3, answerable=3, error_rate_pct=66.0, p95_latency_s=90.0, answered_pct=0.0)
    assert _breached(few) == set()


def test_cost_and_services_alert_without_a_minimum():
    down = {"postgres": OK, "milvus": {"ok": False, "ms": 2000, "error": "ConnectionError"}, "redis": OK}
    assert _breached(_stats(requests=0), services=down, cost=settings.alert_daily_cost_usd + 1) == \
        {"daily_cost", "milvus_down"}


# ── Raise once, resolve once ───────────────────────────────────────────

def test_alert_is_raised_once_and_resolved_when_it_recovers(monkeypatch):
    monkeypatch.setattr(health, "_open_alerts", {})
    monkeypatch.setattr(health, "_table_ready", False)  # don't write to the database here
    sent = []
    from backend.app.escalation import notifier

    monkeypatch.setattr(notifier, "notify_safely", lambda method, payload: sent.append((method, payload["state"])))
    services = {"services": {"postgres": OK, "milvus": OK, "redis": OK}}
    monkeypatch.setattr(health, "service_checks", lambda: services)
    monkeypatch.setattr(health, "today_cost_usd", lambda: 0.0)

    monkeypatch.setattr(health, "window_stats", lambda m: _stats(errors=9, error_rate_pct=18.0))
    assert [c["change"] for c in health.evaluate_alerts()] == ["raised"]
    assert health.evaluate_alerts() == []  # still broken: no second alert
    assert [a["rule"] for a in health.open_alerts()] == ["error_rate"]

    monkeypatch.setattr(health, "window_stats", lambda m: _stats())
    assert [c["change"] for c in health.evaluate_alerts()] == ["resolved"]
    assert health.open_alerts() == []
    assert sent == [("health_alert", "raised"), ("health_alert", "resolved")]


# ── Numbers from the audit trail (Postgres) ────────────────────────────

@pytest.fixture(scope="module")
def db():
    if not history_store.is_available() and not history_store.init_history_store():
        pytest.skip("ptc-postgres is not running")
    from backend.app.escalation import store as esc_store
    from backend.app.feedback import insights

    esc_store.init_escalation_store()
    insights.init_feedback_store()  # the admin endpoints check the console store first
    if not (audit_store.init_audit_store() and health.init_monitoring_store()):
        pytest.skip("audit / monitoring tables could not be created")
    yield True
    with history_store.shared_pool().connection() as conn:
        with conn.transaction():
            conn.execute("SET LOCAL audit.retention_purge = 'on'")
            conn.execute("DELETE FROM audit_events WHERE request_id LIKE 'test-health-%' OR user_id = 'u.health'")
        conn.execute("DELETE FROM monitoring_alerts WHERE rule LIKE 'test_%'")
    audit_store._available = False


def _audited(route="MARKDOWN_RAG_RESPONSE", grounding="passed", latency_stage=1.0, error=None):
    measured = usage.start()

    class Client:
        chat = type("C", (), {"completions": type("X", (), {"create": staticmethod(
            lambda **kw: type("R", (), {"usage": type("U", (), {"prompt_tokens": 500, "completion_tokens": 50})()})()
        )})()})()

    usage.metered_create("answer", Client(), model="gpt-4.1", messages=[])
    usage.record_stage("markdown_rag", latency_stage)
    usage.end()
    response = None if error else ChatResponse(
        route=route, answer="a", score=0.5, grounding=grounding,
        context={"user_id": "u.health", "groups": [], "site": "MAIN", "ui": {}, "record": {}},
        decision_trace={"security": "SEC_SAFE", "classifier": "llm"})
    return audit_store.record_chat(request_id=f"test-health-{uuid.uuid4().hex[:8]}", question="q", session_id=None,
                                   response=response, usage=measured, error=error)


def test_window_daily_and_breakdowns_read_the_audit_trail(db):
    before = health.window_stats(5)
    _audited()
    _audited(route="NO_ANSWER", grounding="not_found")
    _audited(error=RuntimeError("boom"))
    after = health.window_stats(5)
    assert after["requests"] == before["requests"] + 3
    assert after["errors"] == before["errors"] + 1
    assert after["answerable"] >= 2 and after["cost_usd"] > before["cost_usd"]

    today = health.daily_series(3)[-1]
    assert len(health.daily_series(3)) == 3 and today["requests"] >= 3 and today["tokens"] >= 1650
    assert any(r["purpose"] == "answer" and r["model"] == "gpt-4.1" for r in health.llm_breakdown(1))
    assert any(r["stage"] == "markdown_rag" and r["runs"] >= 3 for r in health.stage_breakdown(1))
    assert health.today_cost_usd() >= 3 * 0.0014


def test_service_checks_report_each_service(db):
    result = health.service_checks()
    assert set(result["services"]) == {"postgres", "milvus", "redis"}
    assert result["services"]["postgres"]["ok"] is True
    assert "ram_mb" in result["process"]


def test_alerts_are_stored_with_their_resolution(db):
    alert = {"rule": "test_rule", "severity": "warning", "message": "m", "value": 1.0, "threshold": 0.5}
    health._save_alert(alert)
    health._save_alert({**alert, "resolved_at": "now"})
    stored = [a for a in health.recent_alerts(200) if a["alert_id"] == alert["alert_id"]][0]
    assert stored["resolved_at"] is not None


def test_health_api_needs_the_admin_role(db):
    from backend.app.main import app

    client = TestClient(app)
    assert client.get("/api/admin/health", params={"simulated_group": "SALES_REP"}).status_code == 403
    response = client.get("/api/admin/health", params={"simulated_group": "SUPPORT_ADMIN", "days": 3})
    assert response.status_code == 200
    body = response.json()
    assert {"services", "window", "last_24h", "cost_today_usd", "daily", "llm", "stages", "open_alerts",
            "thresholds"} <= set(body)
    assert client.post("/api/admin/health/check", params={"simulated_group": "SALES_REP"}).status_code == 403
