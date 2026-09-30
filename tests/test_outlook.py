"""Outlook ticket mail — Graph and SMTP are faked; no real mail is ever sent by these tests."""

import json

import httpx
import pytest

from backend.app.config import settings
from backend.app.escalation import notifier, outlook
from backend.app.escalation import store  # noqa: F401 — imported (with openai) before tests patch httpx.Client

TICKET = {
    "ticket_id": 7, "ticket_ref": "PTC-000007", "priority": "high", "user_id": "demo.sales_rep",
    "user_display_name": "Demo User", "trigger": "persistent", "site": "MAIN", "module": "CRM",
    "form": "Customer Orders", "record_type": "CustomerOrder", "record_id": "CO1001",
    "issue_summary": "order is still on credit hold <script>alert(1)</script>",
    "steps_attempted": ["How do I release a credit hold? → MARKDOWN_RAG_RESPONSE"],
    "user_note": "CO1001 & CO1002 blocked", "conversation_summary": [
        {"question": "How do I release a credit hold?", "outcome": "MARKDOWN_RAG_RESPONSE"}],
    "created_at": "2026-09-28T10:00:00+00:00",
}
EVENT = {"event_id": 3, "user_id": "demo.sales_rep", "label": "SEC_PROMPT_INJECTION", "severity": "medium",
         "attempts_in_window": 3, "request_id": "r1", "site": "MAIN", "module": None, "form": None,
         "created_at": "2026-09-28T10:00:00+00:00"}


@pytest.fixture(autouse=True)
def outlook_settings(monkeypatch):
    values = {
        "escalation_notifier": "outlook", "outlook_send_method": "graph", "outlook_sender": "bot@example.com",
        "support_ticket_email": "support@example.com; helpdesk@example.com",
        "security_alert_email": "security@example.com", "outlook_tenant_id": "tenant-1",
        "outlook_client_id": "client-1", "outlook_client_secret": "not-a-real-secret",
        "outlook_smtp_password": "", "outlook_smtp_username": "",
    }
    for key, value in values.items():
        monkeypatch.setattr(settings, key, value)
    monkeypatch.setattr(outlook, "_token", None)
    monkeypatch.setattr(notifier, "RUN_INLINE", True)


# ── Content ────────────────────────────────────────────────────────────

def test_ticket_mail_subject_recipients_and_escaping():
    mail = outlook.ticket_mail(TICKET)
    assert mail.subject.startswith("[PTC-000007] HIGH priority — order is still on credit hold")
    assert mail.to == ["support@example.com", "helpdesk@example.com"]
    assert "<script>" not in mail.html_body and "&lt;script&gt;" in mail.html_body  # user text can't inject HTML
    assert "CO1001 &amp; CO1002" in mail.html_body
    assert "Same problem came back" in mail.html_body and "Customer Orders" in mail.html_body
    assert "CO1001 & CO1002 blocked" in mail.text_body


def test_long_issue_is_shortened_in_the_subject():
    mail = outlook.ticket_mail({**TICKET, "issue_summary": "x" * 200})
    assert mail.subject.endswith("…") and len(mail.subject) < 130


def test_ticket_mail_uses_plain_words_and_outlook_safe_layout(monkeypatch):
    ticket = {**TICKET, "mood": "F4_PERSISTENT", "conversation_summary": [
        {"question": "How do I release a credit hold?", "outcome": "MARKDOWN_RAG_RESPONSE", "answer": "Open <b>it</b>"},
        {"question": "it is still on hold", "outcome": "NO_ANSWER", "answer": ""}]}
    mail = outlook.ticket_mail(ticket)
    body = mail.html_body
    # support staff see plain words, never internal route or mood codes
    assert "Answered from documents" in body and "Not found in documents" in body
    assert "MARKDOWN_RAG_RESPONSE" not in body and "Persistent (asked again)" in body and "F4_" not in body
    assert "Open &lt;b&gt;it&lt;/b&gt;" in body  # the assistant's answer is escaped too
    # table layout, no web-only CSS that Outlook for Windows drops
    assert body.count("<table") >= 3 and "display:flex" not in body and "display:grid" not in body
    assert "Conversation before the ticket (2 questions)" in body
    assert "2. it is still on hold — Not found in documents" in mail.text_body
    assert "feedback console" in body and "href=" not in body  # no button without ADMIN_CONSOLE_URL

    monkeypatch.setattr(settings, "admin_console_url", 'https://bot.example.com/admin.html?x="1"')
    body = outlook.ticket_mail(ticket).html_body
    assert 'href="https://bot.example.com/admin.html?x=&quot;1&quot;"' in body


def test_security_mail():
    mail = outlook.security_mail(EVENT)
    assert mail.subject == "[SECURITY ALERT] prompt injection — demo.sales_rep (3 blocked attempts)"
    assert mail.to == ["security@example.com"]


# ── Configuration ──────────────────────────────────────────────────────

def test_complete_graph_settings_have_nothing_missing():
    assert outlook.missing_settings() == []


def test_missing_values_are_named_not_shown(monkeypatch):
    monkeypatch.setattr(settings, "outlook_client_secret", "")
    monkeypatch.setattr(settings, "support_ticket_email", "")
    assert outlook.missing_settings() == ["SUPPORT_TICKET_EMAIL", "OUTLOOK_CLIENT_SECRET"]


def test_smtp_needs_a_password(monkeypatch):
    monkeypatch.setattr(settings, "outlook_send_method", "smtp")
    assert outlook.missing_settings() == ["OUTLOOK_SMTP_PASSWORD"]


def test_unknown_method_is_reported(monkeypatch):
    monkeypatch.setattr(settings, "outlook_send_method", "carrier_pigeon")
    assert "OUTLOOK_SEND_METHOD" in outlook.missing_settings()[0]


# ── Graph ──────────────────────────────────────────────────────────────

def _fake_graph(monkeypatch, token_status=200, send_status=202):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if "oauth2" in str(request.url):
            if token_status != 200:
                return httpx.Response(token_status, json={"error": "invalid_client"})
            return httpx.Response(200, json={"access_token": "tok-123", "expires_in": 3600})
        return httpx.Response(send_status, text="" if send_status == 202 else '{"error":"ErrorAccessDenied"}')

    real_client = httpx.Client
    monkeypatch.setattr(outlook.httpx, "Client",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    return calls


def test_graph_send_uses_token_and_sendmail(monkeypatch):
    calls = _fake_graph(monkeypatch)
    outlook.send(outlook.ticket_mail(TICKET), "ticket")
    token_call, send_call = calls
    assert "login.microsoftonline.com/tenant-1/oauth2/v2.0/token" in str(token_call.url)
    assert b"grant_type=client_credentials" in token_call.content
    assert str(send_call.url) == "https://graph.microsoft.com/v1.0/users/bot@example.com/sendMail"
    assert send_call.headers["Authorization"] == "Bearer tok-123"
    body = json.loads(send_call.content)
    assert [r["emailAddress"]["address"] for r in body["message"]["toRecipients"]] == \
        ["support@example.com", "helpdesk@example.com"]
    assert body["message"]["body"]["contentType"] == "HTML"


def test_graph_token_is_reused(monkeypatch):
    calls = _fake_graph(monkeypatch)
    outlook.send(outlook.ticket_mail(TICKET), "ticket")
    outlook.send(outlook.ticket_mail(TICKET), "ticket")
    assert sum("oauth2" in str(c.url) for c in calls) == 1


def test_graph_errors_raise_without_the_secret(monkeypatch):
    _fake_graph(monkeypatch, token_status=401)
    with pytest.raises(RuntimeError) as err:
        outlook.send(outlook.ticket_mail(TICKET), "ticket")
    assert "401" in str(err.value) and "not-a-real-secret" not in str(err.value)


# ── SMTP ───────────────────────────────────────────────────────────────

class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout):
        self.host, self.port = host, port
        self.steps = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.steps.append("starttls")

    def login(self, user, password):
        self.steps.append(("login", user))

    def send_message(self, message):
        FakeSMTP.sent.append((self.host, self.port, self.steps, message))


def test_smtp_send_uses_starttls_and_login(monkeypatch):
    monkeypatch.setattr(settings, "outlook_send_method", "smtp")
    monkeypatch.setattr(settings, "outlook_smtp_password", "pw")
    monkeypatch.setattr(outlook.smtplib, "SMTP", FakeSMTP)
    FakeSMTP.sent.clear()
    outlook.send(outlook.ticket_mail(TICKET), "ticket")
    host, port, steps, message = FakeSMTP.sent[0]
    assert (host, port) == ("smtp.office365.com", 587)
    assert steps == ["starttls", ("login", "bot@example.com")]
    assert message["To"] == "support@example.com, helpdesk@example.com"
    assert message["Subject"].startswith("[PTC-000007]")


# ── Notifier ───────────────────────────────────────────────────────────

def test_notifier_records_sent_status(monkeypatch):
    _fake_graph(monkeypatch)
    recorded = []
    from backend.app.escalation import store

    monkeypatch.setattr(store, "set_notification_status", lambda tid, status: recorded.append((tid, status)))
    notifier.notify_safely("ticket_created", TICKET)
    assert recorded == [(7, "sent")]


def test_notifier_records_failure_and_never_raises(monkeypatch):
    _fake_graph(monkeypatch, send_status=403)
    recorded = []
    from backend.app.escalation import store

    monkeypatch.setattr(store, "set_notification_status", lambda tid, status: recorded.append((tid, status)))
    notifier.notify_safely("ticket_created", TICKET)  # must not raise
    assert recorded == [(7, "failed")]


def test_notifier_without_settings_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "outlook_client_secret", "")
    recorded = []
    from backend.app.escalation import store

    monkeypatch.setattr(store, "set_notification_status", lambda tid, status: recorded.append((tid, status)))
    notifier.notify_safely("ticket_created", TICKET)
    assert recorded == [(7, "not_configured")]


def test_log_notifier_marks_tickets_logged(monkeypatch):
    monkeypatch.setattr(settings, "escalation_notifier", "log")
    recorded = []
    from backend.app.escalation import store

    monkeypatch.setattr(store, "set_notification_status", lambda tid, status: recorded.append((tid, status)))
    notifier.notify_safely("ticket_created", TICKET)
    assert recorded == [(7, "logged")]


def test_security_alert_mail_is_optional(monkeypatch):
    monkeypatch.setattr(settings, "security_alert_email", "")
    assert notifier.OutlookNotifier().security_alert(EVENT) == "not_configured"


def test_security_alert_is_mailed(monkeypatch):
    calls = _fake_graph(monkeypatch)
    assert notifier.OutlookNotifier().security_alert(EVENT) == "sent"
    body = json.loads(calls[-1].content)
    assert body["message"]["toRecipients"][0]["emailAddress"]["address"] == "security@example.com"
