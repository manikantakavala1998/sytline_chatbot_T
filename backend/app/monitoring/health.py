"""Service health, the numbers behind the Health tab, and automatic health alerts (Phase 6).

Everything is computed from the audit trail (audit_events) plus live pings — nothing extra is
collected. `evaluate_alerts()` runs every MONITOR_INTERVAL_SECONDS in the background:

  rule                    breaks when (over the last ALERT_WINDOW_MINUTES, with ≥ ALERT_MIN_REQUESTS)
  error_rate              requests ending in ERROR  > ALERT_ERROR_RATE_PCT
  slow_answers            95th-percentile latency   > ALERT_P95_LATENCY_SECONDS
  llm_fallbacks           requests that fell back to rules / had a failed LLM call > ALERT_LLM_FALLBACK_RATE_PCT
  low_answered_rate       answered share of answerable questions < ALERT_ANSWERED_PCT_MIN
  daily_cost              today's OpenAI cost        > ALERT_DAILY_COST_USD   (no minimum)
  postgres / milvus / redis   the service doesn't answer a ping

An alert is raised ONCE when a rule breaks and resolved when it recovers (no alert storms); both
are written to the trace, the log, the monitoring_alerts table, and sent through the notifier
(email when Outlook is configured and OPS_ALERT_EMAIL is set).
"""

import os
import time
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.history import store as history_store
from backend.app.utils import trace
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)
STARTED_AT = time.time()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    alert_id     BIGSERIAL PRIMARY KEY,
    rule         TEXT NOT NULL,
    severity     TEXT NOT NULL,
    message      TEXT NOT NULL,
    value        DOUBLE PRECISION,
    threshold    DOUBLE PRECISION,
    raised_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_monitoring_alerts_open ON monitoring_alerts (rule) WHERE resolved_at IS NULL;
"""

# Chat outcomes that can't count as "answered or not" (attacks, small talk, off-topic, Phase 4 routes).
NOT_ANSWERABLE = ("BLOCKED", "DIRECT_RESPONSE", "OUT_OF_SCOPE", "CAPABILITY_PENDING")
FALLBACK_SQL = ("(details->>'conversation_source' = 'rules' OR details->>'classifier' = 'rules' "
                "OR llm_calls @> '[{\"ok\": false}]')")

_open_alerts: dict[str, dict] = {}  # rule -> alert, so each problem alerts once
_table_ready = False


def init_monitoring_store() -> bool:
    global _table_ready
    if not history_store.is_available():
        return False
    try:
        with history_store.shared_pool().connection() as conn:
            conn.execute(SCHEMA_SQL)
            for rule, alert_id, message, severity, raised in conn.execute(
                "SELECT rule, alert_id, message, severity, raised_at FROM monitoring_alerts WHERE resolved_at IS NULL"
            ).fetchall():
                _open_alerts[rule] = {"alert_id": alert_id, "rule": rule, "message": message, "severity": severity,
                                      "raised_at": raised.isoformat()}
        _table_ready = True
    except Exception as exc:
        log_event(logger, "monitoring_store_unavailable", error=type(exc).__name__)
        _table_ready = False
    return _table_ready


# ── Live service checks ─────────────────────────────────────────────────


def _timed(check) -> dict:
    started = time.perf_counter()
    try:
        check()
        return {"ok": True, "ms": round((time.perf_counter() - started) * 1000, 1)}
    except Exception as exc:
        return {"ok": False, "ms": round((time.perf_counter() - started) * 1000, 1), "error": type(exc).__name__}


def _postgres():
    if not history_store.is_available():
        raise ConnectionError("history store not connected")
    with history_store.shared_pool().connection(timeout=3) as conn:
        conn.execute("SELECT 1")


def _milvus():
    from backend.app.rag import milvus_store

    milvus_store.check_reachable(timeout_seconds=2)
    milvus_store.get_client().has_collection(milvus_store.COLLECTION_NAME)


def _redis():
    import redis

    redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db,
                socket_connect_timeout=1, socket_timeout=1).ping()


def service_checks() -> dict:
    services = {"postgres": _timed(_postgres), "milvus": _timed(_milvus), "redis": _timed(_redis)}
    process = {}
    try:
        import psutil

        me = psutil.Process(os.getpid())
        process = {"cpu_pct": me.cpu_percent(interval=0.1), "ram_mb": round(me.memory_info().rss / 2**20),
                   "system_cpu_pct": psutil.cpu_percent(interval=None),
                   "system_ram_pct": psutil.virtual_memory().percent}
    except Exception:
        pass
    return {"services": services, "process": process, "uptime_s": round(time.time() - STARTED_AT)}


# ── Numbers from the audit trail ────────────────────────────────────────


def window_stats(minutes: int) -> dict:
    """Request health over the last `minutes` (chat requests only)."""
    with history_store.shared_pool().connection() as conn:
        row = conn.execute(
            f"""
            SELECT count(*),
                   count(*) FILTER (WHERE status = 'ERROR'),
                   percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms),
                   percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms),
                   count(*) FILTER (WHERE {FALLBACK_SQL}),
                   count(*) FILTER (WHERE route NOT IN {NOT_ANSWERABLE} AND status <> 'ERROR'),
                   count(*) FILTER (WHERE route IN ('FAST_QA_RESPONSE', 'MARKDOWN_RAG_RESPONSE')),
                   coalesce(sum(cost_usd), 0)
            FROM audit_events
            WHERE event_type = 'chat' AND created_at > now() - make_interval(mins => %s)
            """,
            (minutes,),
        ).fetchone()
    total, errors, p95, p50, fallbacks, answerable, answered, cost = row
    pct = lambda part, whole: round(100 * part / whole, 1) if whole else None  # noqa: E731
    return {
        "minutes": minutes, "requests": total, "errors": errors, "error_rate_pct": pct(errors, total),
        "p95_latency_s": round(p95 / 1000, 1) if p95 is not None else None,
        "p50_latency_s": round(p50 / 1000, 1) if p50 is not None else None,
        "fallbacks": fallbacks, "fallback_rate_pct": pct(fallbacks, total),
        "answerable": answerable, "answered": answered, "answered_pct": pct(answered, answerable),
        "cost_usd": float(cost),
    }


def today_cost_usd() -> float:
    with history_store.shared_pool().connection() as conn:
        return float(conn.execute(
            "SELECT coalesce(sum(cost_usd), 0) FROM audit_events WHERE event_type = 'chat' "
            "AND created_at >= date_trunc('day', now())"
        ).fetchone()[0])


def daily_series(days: int = 14) -> list[dict]:
    """One row per day for the charts (days with no traffic included as zeros)."""
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            f"""
            WITH days AS (
                SELECT generate_series(date_trunc('day', now()) - make_interval(days => %s - 1),
                                       date_trunc('day', now()), interval '1 day') AS day)
            SELECT d.day,
                   count(a.audit_id),
                   count(a.audit_id) FILTER (WHERE a.status = 'ERROR'),
                   percentile_cont(0.95) WITHIN GROUP (ORDER BY a.latency_ms),
                   coalesce(sum(a.cost_usd), 0),
                   coalesce(sum(a.prompt_tokens + a.completion_tokens), 0),
                   count(a.audit_id) FILTER (WHERE a.grounding IN ('passed', 'approved')),
                   count(a.audit_id) FILTER (WHERE a.grounding = 'repaired'),
                   count(a.audit_id) FILTER (WHERE a.grounding IN ('replaced', 'not_found')),
                   count(a.audit_id) FILTER (WHERE a.route IN ('FAST_QA_RESPONSE', 'MARKDOWN_RAG_RESPONSE')),
                   count(a.audit_id) FILTER (WHERE a.route NOT IN {NOT_ANSWERABLE} AND a.status <> 'ERROR')
            FROM days d
            LEFT JOIN audit_events a ON a.event_type = 'chat' AND date_trunc('day', a.created_at) = d.day
            GROUP BY d.day ORDER BY d.day
            """,
            (days,),
        ).fetchall()
    return [
        {"day": day.date().isoformat(), "requests": n, "errors": errors,
         "p95_latency_s": round(p95 / 1000, 1) if p95 is not None else None, "cost_usd": round(float(cost), 4),
         "tokens": int(tokens), "checked_ok": ok, "repaired": repaired, "refused_or_not_found": refused,
         "answered": answered, "answerable": answerable}
        for day, n, errors, p95, cost, tokens, ok, repaired, refused, answered, answerable in rows
    ]


def llm_breakdown(days: int = 7) -> list[dict]:
    """Per purpose/model: calls, failures, average time, tokens and cost."""
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT c->>'purpose', c->>'model', count(*),
                   count(*) FILTER (WHERE (c->>'ok')::boolean IS FALSE),
                   avg((c->>'ms')::int), sum((c->>'prompt_tokens')::int), sum((c->>'completion_tokens')::int),
                   sum((c->>'cost_usd')::numeric)
            FROM audit_events a, jsonb_array_elements(a.llm_calls) c
            WHERE a.event_type = 'chat' AND a.created_at > now() - make_interval(days => %s)
            GROUP BY 1, 2 ORDER BY 8 DESC NULLS LAST
            """,
            (days,),
        ).fetchall()
    return [{"purpose": p, "model": m, "calls": n, "failures": f, "avg_ms": round(float(ms or 0)),
             "prompt_tokens": int(pt or 0), "completion_tokens": int(ct or 0), "cost_usd": round(float(cost or 0), 4)}
            for p, m, n, f, ms, pt, ct, cost in rows]


def stage_breakdown(days: int = 7) -> list[dict]:
    """Average time per workflow step (only requests that ran the step)."""
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT s.key, count(*), avg(s.value::int), max(s.value::int)
            FROM audit_events a, jsonb_each_text(a.stages_ms) s
            WHERE a.event_type = 'chat' AND a.created_at > now() - make_interval(days => %s)
            GROUP BY 1 ORDER BY 3 DESC
            """,
            (days,),
        ).fetchall()
    return [{"stage": k, "runs": n, "avg_ms": round(float(avg)), "max_ms": mx} for k, n, avg, mx in rows]


# ── Alerts ──────────────────────────────────────────────────────────────


def _rules(stats: dict, services: dict, cost_today: float) -> list[dict]:
    """Every rule with its current value — `breached` decides raise / resolve."""
    enough = stats["requests"] >= settings.alert_min_requests
    window = f"last {stats['minutes']} min"
    rules = [
        {"rule": "error_rate", "severity": "critical", "value": stats["error_rate_pct"],
         "threshold": settings.alert_error_rate_pct,
         "breached": enough and (stats["error_rate_pct"] or 0) > settings.alert_error_rate_pct,
         "message": f"{stats['error_rate_pct']}% of requests failed ({stats['errors']} of {stats['requests']}, {window})"},
        {"rule": "slow_answers", "severity": "warning", "value": stats["p95_latency_s"],
         "threshold": settings.alert_p95_latency_seconds,
         "breached": enough and (stats["p95_latency_s"] or 0) > settings.alert_p95_latency_seconds,
         "message": f"95% of answers took up to {stats['p95_latency_s']} s ({window})"},
        {"rule": "llm_fallbacks", "severity": "warning", "value": stats["fallback_rate_pct"],
         "threshold": settings.alert_llm_fallback_rate_pct,
         "breached": enough and (stats["fallback_rate_pct"] or 0) > settings.alert_llm_fallback_rate_pct,
         "message": f"{stats['fallback_rate_pct']}% of requests fell back to rules or had a failed OpenAI call ({window})"},
        {"rule": "low_answered_rate", "severity": "warning", "value": stats["answered_pct"],
         "threshold": settings.alert_answered_pct_min,
         "breached": stats["answerable"] >= settings.alert_min_requests
         and (stats["answered_pct"] if stats["answered_pct"] is not None else 100) < settings.alert_answered_pct_min,
         "message": f"only {stats['answered_pct']}% of questions got an answer ({window})"},
        {"rule": "daily_cost", "severity": "warning", "value": round(cost_today, 2),
         "threshold": settings.alert_daily_cost_usd, "breached": cost_today > settings.alert_daily_cost_usd,
         "message": f"today's OpenAI cost is ${cost_today:.2f} (limit ${settings.alert_daily_cost_usd:.2f})"},
    ]
    for name, result in services.items():
        rules.append({"rule": f"{name}_down", "severity": "critical", "value": None, "threshold": None,
                      "breached": not result["ok"],
                      "message": f"{name} is not answering ({result.get('error', 'no reply')})"})
    return rules


def _save_alert(alert: dict) -> None:
    if not _table_ready or not history_store.is_available():
        return
    try:
        with history_store.shared_pool().connection() as conn:
            if alert.get("resolved_at"):
                conn.execute("UPDATE monitoring_alerts SET resolved_at = now() WHERE alert_id = %s",
                             (alert["alert_id"],))
            else:
                alert["alert_id"] = conn.execute(
                    "INSERT INTO monitoring_alerts (rule, severity, message, value, threshold) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING alert_id",
                    (alert["rule"], alert["severity"], alert["message"], alert["value"], alert["threshold"]),
                ).fetchone()[0]
    except Exception:
        logger.exception("event=monitoring_alert_save_failed rule=%s", alert["rule"])


def evaluate_alerts() -> list[dict]:
    """Check every rule once; raise new alerts, resolve recovered ones. Returns what changed."""
    from backend.app.escalation.notifier import notify_safely

    services = service_checks()["services"]
    try:
        stats = window_stats(settings.alert_window_minutes) if services["postgres"]["ok"] else None
        cost_today = today_cost_usd() if services["postgres"]["ok"] else 0.0
    except Exception:
        logger.exception("event=monitoring_stats_failed")
        stats, cost_today = None, 0.0
    rules = _rules(stats, services, cost_today) if stats else _rules(
        {"requests": 0, "errors": 0, "error_rate_pct": None, "p95_latency_s": None, "fallback_rate_pct": None,
         "answerable": 0, "answered_pct": None, "minutes": settings.alert_window_minutes}, services, cost_today)

    changes = []
    for rule in rules:
        name = rule["rule"]
        if rule["breached"] and name not in _open_alerts:
            alert = {**rule, "raised_at": datetime.now(timezone.utc).isoformat()}
            _save_alert(alert)
            _open_alerts[name] = alert
            changes.append({**alert, "change": "raised"})
            logger.warning("event=health_alert_raised rule=%s severity=%s message=%s", name, rule["severity"],
                           rule["message"])
            trace.note(f"🚨 HEALTH ALERT ({rule['severity']}) {name}: {rule['message']}")
            notify_safely("health_alert", {**alert, "state": "raised"})
        elif not rule["breached"] and name in _open_alerts:
            alert = _open_alerts.pop(name)
            alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
            _save_alert(alert)
            changes.append({**alert, "change": "resolved"})
            log_event(logger, "health_alert_resolved", rule=name)
            trace.note(f"✅ HEALTH ALERT RESOLVED {name}")
            notify_safely("health_alert", {**alert, "state": "resolved", "message": f"{name} is back to normal"})
    log_event(logger, "health_check_completed", rules=len(rules), open_alerts=len(_open_alerts), changes=len(changes))
    return changes


def open_alerts() -> list[dict]:
    return list(_open_alerts.values())


def recent_alerts(limit: int = 50) -> list[dict]:
    if not _table_ready or not history_store.is_available():
        return []
    with history_store.shared_pool().connection() as conn:
        rows = conn.execute(
            "SELECT alert_id, rule, severity, message, value, threshold, raised_at, resolved_at "
            "FROM monitoring_alerts ORDER BY raised_at DESC LIMIT %s", (limit,),
        ).fetchall()
    return [{"alert_id": a, "rule": r, "severity": s, "message": m, "value": v, "threshold": t,
             "raised_at": ra.isoformat(), "resolved_at": rs.isoformat() if rs else None}
            for a, r, s, m, v, t, ra, rs in rows]


def thresholds() -> dict:
    return {"window_minutes": settings.alert_window_minutes, "min_requests": settings.alert_min_requests,
            "error_rate_pct": settings.alert_error_rate_pct, "p95_latency_s": settings.alert_p95_latency_seconds,
            "fallback_rate_pct": settings.alert_llm_fallback_rate_pct, "answered_pct_min": settings.alert_answered_pct_min,
            "daily_cost_usd": settings.alert_daily_cost_usd}
