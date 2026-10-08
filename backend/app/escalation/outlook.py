"""Outlook / Microsoft 365 mail for support tickets and security alerts.

Two ways to send, chosen by OUTLOOK_SEND_METHOD:

  graph (recommended)  Microsoft Graph `sendMail` with an Azure app registration
                       (client-credentials flow, application permission Mail.Send — ask IT to
                       limit it to the sender mailbox with an application access policy).
  smtp                 smtp.office365.com:587 with STARTTLS and the sender's login
                       (only if IT has SMTP AUTH enabled for that mailbox).

Secrets (client secret / SMTP password) come only from .env and are never logged. Every value
put into the HTML body is escaped, so text a user typed can't change the mail's markup.
"""

import html
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

import httpx

from backend.app.config import settings
from backend.app.escalation.policy import is_ticket_request, main_issue
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
SEND_URL = "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
SUBJECT_ISSUE_CHARS = 80



class OutlookNotConfigured(RuntimeError):
    """Required .env values are missing — the caller falls back to logging only."""


@dataclass
class Mail:
    to: list[str]
    subject: str
    html_body: str
    text_body: str


def recipients(value: str) -> list[str]:
    return [address.strip() for address in value.replace(";", ",").split(",") if address.strip()]


RECIPIENT_SETTING = {"security_alert": "SECURITY_ALERT_EMAIL", "health_alert": "OPS_ALERT_EMAIL"}


def missing_settings(for_security: bool = False, kind: str | None = None) -> list[str]:
    """Names of the .env values that still need filling in (never their contents)."""
    kind = kind or ("security_alert" if for_security else "ticket")
    needed = {"OUTLOOK_SENDER": settings.outlook_sender}
    recipient = RECIPIENT_SETTING.get(kind, "SUPPORT_TICKET_EMAIL")
    needed[recipient] = {"SECURITY_ALERT_EMAIL": settings.security_alert_email,
                         "OPS_ALERT_EMAIL": settings.ops_alert_email}.get(recipient, settings.support_ticket_email)
    method = settings.outlook_send_method.lower()
    if method == "graph":
        needed.update({
            "OUTLOOK_TENANT_ID": settings.outlook_tenant_id,
            "OUTLOOK_CLIENT_ID": settings.outlook_client_id,
            "OUTLOOK_CLIENT_SECRET": settings.outlook_client_secret,
        })
    elif method == "smtp":
        needed["OUTLOOK_SMTP_PASSWORD"] = settings.outlook_smtp_password
    else:
        return [f"OUTLOOK_SEND_METHOD (must be graph or smtp, got {settings.outlook_send_method!r})"]
    return [name for name, value in needed.items() if not str(value).strip()]


# ── Message content ────────────────────────────────────────────────────
#
# Email HTML is not web HTML: Outlook for Windows renders with Word, so the layout is nested tables,
# every style is inline, widths are fixed (640px, shrinking on phones), and nothing relies on flex,
# grid, web fonts or CSS classes. Colours come from the admin console's palette.

INK, SOFT, FAINT, BORDER, CANVAS, PANEL = "#1e2338", "#5b6088", "#7a7f9e", "#dde3f0", "#f4f7fc", "#f7f9fd"
BRAND = "#1c4fd6"
FONT = "'Segoe UI',Segoe,Arial,sans-serif"
BADGE = {  # (text colour, background) — soft tints, always with a word, never colour alone
    "critical": ("#b3261e", "#fdecea"),
    "warning": ("#8a5a00", "#fff4dc"),
    "good": ("#0f7a2e", "#e8f6ec"),
    "neutral": ("#555b78", "#f1f4f9"),
    "on_brand": ("#1f58cc", "#eaf1fe"),
}
OUTCOME_TEXT = {
    "FAST_QA_RESPONSE": ("Approved answer given", "good"),
    "MARKDOWN_RAG_RESPONSE": ("Answered from documents", "good"),
    "NO_ANSWER": ("Not found in documents", "critical"),
    "CLARIFY": ("Asked the user to clarify", "warning"),
    "CAPABILITY_PENDING": ("Needs live SyteLine data", "warning"),
    "OUT_OF_SCOPE": ("Outside Prospect-to-Cash", "neutral"),
    "DIRECT_RESPONSE": ("Small talk", "neutral"),
}


def _e(value) -> str:
    """Escape user text for HTML and keep its line breaks."""
    return html.escape(str(value)).replace("\n", "<br>")


def _when(value) -> str:
    """ISO time → '28 Sep 2026, 15:30 (UTC+05:30)' in the server's time zone."""
    if not value:
        return ""
    try:
        moment = datetime.fromisoformat(str(value)).astimezone()
    except ValueError:
        return str(value)
    offset = moment.strftime("%z")
    return f"{moment:%d %b %Y, %H:%M} (UTC{offset[:3]}:{offset[3:]})"


def _badge(text: str, kind: str = "neutral") -> str:
    colour, background = BADGE[kind]
    return (f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;background:{background};'
            f'color:{colour};font-size:12px;font-weight:bold;line-height:16px;mso-line-height-rule:exactly">'
            f"{_e(text)}</span>")


def _section(title: str, inner: str) -> str:
    return (f'<tr><td style="padding:20px 28px 0 28px">'
            f'<div style="font-size:13px;font-weight:bold;color:{SOFT};padding-bottom:8px">{_e(title)}</div>'
            f"{inner}</td></tr>")


def _facts(pairs: list[tuple[str, str | None]]) -> str:
    """Label / value rows; empty values are skipped. Values are already-safe HTML."""
    rows = "".join(
        f'<tr><td width="150" style="padding:7px 12px 7px 0;border-bottom:1px solid {BORDER};color:{SOFT};'
        f'vertical-align:top;font-size:13px">{_e(label)}</td>'
        f'<td style="padding:7px 0;border-bottom:1px solid {BORDER};color:{INK};vertical-align:top;font-size:14px">'
        f"{value}</td></tr>"
        for label, value in pairs if value
    )
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>'


def _button(label: str, url: str) -> str:
    """A 'bulletproof' button: a coloured table cell, which Outlook draws correctly."""
    return (f'<tr><td style="padding:24px 28px 0 28px"><table role="presentation" cellpadding="0" cellspacing="0" '
            f'border="0"><tr><td bgcolor="{BRAND}" style="border-radius:8px;background:{BRAND}">'
            f'<a href="{html.escape(url, quote=True)}" style="display:inline-block;padding:11px 20px;color:#ffffff;'
            f'font-family:{FONT};font-size:14px;font-weight:bold;text-decoration:none">{_e(label)}</a>'
            f"</td></tr></table></td></tr>")


def _layout(*, preheader: str, eyebrow: str, title: str, badges: str, body_rows: str, footer: str,
            band: str = BRAND) -> str:
    footer_html = _e(footer)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light">
<title>{_e(title)}</title></head>
<body style="margin:0;padding:0;background:{CANVAS}">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{CANVAS}">{_e(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CANVAS}" style="background:{CANVAS}">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff"
 style="width:100%;max-width:640px;background:#ffffff;border:1px solid {BORDER};border-radius:12px;font-family:{FONT};color:{INK}">
<tr><td bgcolor="{band}" height="4" style="background:{band};height:4px;line-height:4px;font-size:4px;border-radius:12px 12px 0 0">&nbsp;</td></tr>
<tr><td style="padding:20px 28px 16px 28px;border-bottom:1px solid {BORDER}">
<div style="font-size:12px;color:{FAINT}">{_e(eyebrow)}</div>
<div style="font-size:22px;font-weight:bold;color:{INK};padding:2px 0 8px">{_e(title)}</div>
<div>{badges}</div></td></tr>
{body_rows}
<tr><td style="padding:24px 28px 22px 28px">
<div style="border-top:1px solid {BORDER};padding-top:14px;font-size:12px;line-height:18px;color:{FAINT}">{footer_html}</div>
</td></tr></table></td></tr></table></body></html>"""


def _rows(pairs: list[tuple[str, str | None]]) -> tuple[str, str]:
    """Plain facts table (HTML) and the same facts as text lines, for the simple mails."""
    html_pairs = [(label, _e(value)) for label, value in pairs if value]
    return _facts(html_pairs), "\n".join(f"{label}: {value}" for label, value in pairs if value)


def _wrap(title: str, intro: str, table: str, footer: str, *, eyebrow: str = "SyteLine assistant",
          band: str = BRAND, badges: str = "") -> str:
    body = (f'<tr><td style="padding:22px 28px 0 28px;font-size:14px;line-height:21px;color:{SOFT}">{_e(intro)}</td></tr>'
            f'<tr><td style="padding:12px 28px 0 28px">{table}</td></tr>')
    if settings.admin_console_url:
        body += _button("Open the support console", settings.admin_console_url)
    return _layout(preheader=intro, eyebrow=eyebrow, title=title, badges=badges, body_rows=body, footer=footer,
                   band=band)


def _screen(item: dict) -> str:
    return " / ".join(p for p in (item.get("site"), item.get("module"), item.get("form")) if p)


# Why the ticket exists and how far the assistant got — one plain sentence each.
TRIGGER_SENTENCE = {
    "user_request": "The user asked to talk to the support team.",
    "user_confirmed": "The user asked for a support ticket.",
    "persistent": "The same problem came back after the assistant's answer.",
    "frustration": "The user was frustrated with the answers.",
    "unresolved": "The assistant couldn't answer two questions in a row.",
}
RESULT_SENTENCE = {
    "NO_ANSWER": "The assistant couldn't find this in the approved documents.",
    "CLARIFY": "The assistant needed more details and couldn't solve it.",
    "MARKDOWN_RAG_RESPONSE": "The assistant answered from the documents, but that didn't solve the problem.",
    "FAST_QA_RESPONSE": "The assistant gave the approved answer, but that didn't solve the problem.",
    "CAPABILITY_PENDING": "It needs live SyteLine data, which the assistant can't read yet.",
    "OUT_OF_SCOPE": "It is outside what the assistant covers.",
}
CHAT_OUTCOMES = {k: v for k, v in OUTCOME_TEXT.items() if k != "DIRECT_RESPONSE"}  # no tag on small talk


def _conversation(turns: list[dict]) -> tuple[str, str]:
    """The chat before the ticket, written as a chat: the user's message, then the assistant's
    reply with a small tag saying how it answered."""
    html_turns, text_turns = [], []
    for turn in turns:
        outcome = CHAT_OUTCOMES.get(turn.get("outcome"))
        answer = turn.get("answer") or ""
        tag = f" &nbsp;{_badge(outcome[0], outcome[1])}" if outcome else ""
        html_turns.append(
            f'<tr><td style="padding:12px 0;border-bottom:1px solid {BORDER}">'
            f'<div style="font-size:12px;font-weight:bold;color:{FAINT};padding-bottom:2px">User</div>'
            f'<div style="font-size:14px;line-height:21px;color:{INK};padding-bottom:10px">{_e(turn.get("question"))}</div>'
            f'<div style="font-size:12px;font-weight:bold;color:{FAINT};padding-bottom:2px">Assistant{tag}</div>'
            f'<div style="font-size:13px;line-height:20px;color:{SOFT}">{_e(answer) or "—"}</div>'
            "</td></tr>"
        )
        label = f" ({outcome[0]})" if outcome else ""
        text_turns.append(f"User: {turn.get('question')}\nAssistant{label}: {answer}")
    table = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(html_turns)}</table>'
    return table, "\n\n".join(text_turns)


def _panel(inner: str) -> str:
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td bgcolor="{PANEL}" style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;'
            f'padding:14px 16px">{inner}</td></tr></table>')


def ticket_mail(ticket: dict) -> Mail:
    ref = ticket["ticket_ref"]
    turns = ticket.get("conversation_summary") or []
    issue_turn = main_issue(turns)
    issue = ticket.get("issue_summary") or ""
    if not issue or is_ticket_request(issue):  # older tickets stored "can I talk to support?" as the issue
        issue = (issue_turn or {}).get("question") or issue or "Support request"
    short = issue if len(issue) <= SUBJECT_ISSUE_CHARS else issue[:SUBJECT_ISSUE_CHARS] + "…"
    high = ticket.get("priority") == "high"
    priority = "HIGH" if high else "Normal"
    subject = f"[{ref}] {priority} priority — {short}"
    who = ticket.get("user_display_name") or ticket["user_id"]
    user_id = ticket["user_id"]
    screen = _screen(ticket).replace(" / ", " › ")
    record = " ".join(p for p in (ticket.get("record_type"), ticket.get("record_id")) if p)
    created = _when(ticket.get("created_at"))
    why = " ".join(s for s in (TRIGGER_SENTENCE.get(ticket.get("trigger") or ""),
                               RESULT_SENTENCE.get((issue_turn or {}).get("outcome") or "")) if s)
    if high:
        why += " Marked high priority because the problem is repeating or the user is frustrated."

    badges = " ".join([
        _badge("▲ High priority" if high else "Normal priority", "critical" if high else "neutral"),
        _badge("Open", "on_brand"),
    ])
    who_html = f"{_e(who)}" + (f' <span style="color:{FAINT}">· {_e(user_id)}</span>' if who != user_id else "")
    body = _section("Summary", _panel(
        (f'<div style="font-size:14px;line-height:22px;color:{INK};padding-bottom:12px">{_e(why)}</div>' if why else "")
        + _facts([("Who", who_html), ("Where", _e(screen)), ("Record", _e(record)), ("When", _e(created))])
    ))
    if ticket.get("user_note"):
        body += _section("Note from the user",
                         f'<div style="border-left:3px solid {BRAND};padding:4px 0 4px 14px;font-size:15px;'
                         f'line-height:22px;color:{INK}">“{_e(ticket["user_note"])}”</div>')
    conversation_html, conversation_text = _conversation(turns)
    if turns:
        body += _section("The conversation", conversation_html)
    body += _section("What to do next",
                     f'<div style="font-size:14px;line-height:22px;color:{INK}">'
                     f"1. Contact {_e(who)} about this problem.<br>"
                     f"2. In the support console, open <b>Tickets</b>, press <b>Start working</b> on {_e(ref)}, "
                     f"and <b>Mark resolved</b> once it is fixed.</div>")
    if settings.admin_console_url:
        body += _button(f"Open {ref} in the support console", settings.admin_console_url)
    footer = ("Sent automatically by the SyteLine Prospect-to-Cash assistant after the user confirmed the ticket. "
              "Passwords and other secrets in the conversation are masked.")

    text = "\n".join(line for line in [
        f"New support ticket {ref} — {priority} priority",
        "",
        f"Problem: {issue}",
        why or None,
        "",
        f"Who: {who}" + (f" ({user_id})" if who != user_id else ""),
        f"Where: {screen}" if screen else None,
        f"Record: {record}" if record else None,
        f"When: {created}" if created else None,
        "",
        f"Note from the user: {ticket['user_note']}" if ticket.get("user_note") else None,
        "",
        "The conversation:" if turns else None,
        conversation_text if turns else None,
        "",
        f"Next: contact {who}, then in the support console press Start working on {ref} and Mark resolved once fixed.",
        settings.admin_console_url or None,
        "",
        footer,
    ] if line is not None)
    return Mail(
        to=recipients(settings.support_ticket_email),
        subject=subject,
        html_body=_layout(preheader=f"{who} · {screen or 'SyteLine'} · {short}",
                          eyebrow=f"New support ticket · {ref}", title=issue, badges=badges,
                          body_rows=body, footer=footer),
        text_body=text,
    )


def security_mail(event: dict) -> Mail:
    label = event["label"].removeprefix("SEC_").replace("_", " ").lower()
    subject = f"[SECURITY ALERT] {label} — {event['user_id']} ({event['attempts_in_window']} blocked attempts)"
    table, text = _rows([
        ("User", event["user_id"]),
        ("What was blocked", label),
        ("Severity", event["severity"]),
        ("Attempts", f"{event['attempts_in_window']} within {settings.security_alert_window_minutes} minutes"),
        ("SyteLine screen", _screen(event)),
        ("Request id", event.get("request_id")),
        ("Time", _when(event.get("created_at"))),
    ])
    footer = ("The messages were blocked and nothing was revealed. A redacted excerpt of each attempt is in the "
              "support console (Security).")
    high = event["severity"] == "high"
    return Mail(
        to=recipients(settings.security_alert_email),
        subject=subject,
        html_body=_wrap("Security alert", "One user was blocked repeatedly by the assistant's security gate.",
                        table, footer, eyebrow="SyteLine assistant · Security", band="#8f2424",
                        badges=_badge(f"{event['severity'].upper()} severity", "on_brand" if not high else "warning")),
        text_body=f"Security alert\n\n{text}\n\n{footer}",
    )


def health_mail(alert: dict) -> Mail:
    resolved = alert.get("state") == "resolved"
    state = "RESOLVED" if resolved else f"HEALTH ALERT ({alert.get('severity', 'warning')})"
    subject = f"[{state}] SyteLine assistant — {alert['rule'].replace('_', ' ')}"
    table, text = _rows([
        ("What", alert.get("message")),
        ("Rule", alert["rule"]),
        ("Value / limit", f"{alert.get('value')} / {alert.get('threshold')}" if alert.get("threshold") is not None
         else None),
        ("Raised", _when(alert.get("raised_at"))),
        ("Resolved", _when(alert.get("resolved_at"))),
    ])
    footer = "Open the support console → System health for the numbers behind this alert."
    return Mail(to=recipients(settings.ops_alert_email), subject=subject,
                html_body=_wrap(state.title(), "The assistant's automatic health check changed state.", table, footer,
                                eyebrow="SyteLine assistant · Health", band="#0c6b0c" if resolved else "#8a5a00"),
                text_body=f"{state}\n\n{text}\n\n{footer}")


def connection_test_mail() -> Mail:
    table, text = _rows([("Send method", settings.outlook_send_method), ("Sender", settings.outlook_sender)])
    return Mail(
        to=recipients(settings.support_ticket_email),
        subject="[TEST] SyteLine assistant — ticket mail is working",
        html_body=_wrap("Test email", "If you can read this, support-ticket mail is set up correctly.", table, "",
                        badges=_badge("✓ Working", "on_brand")),
        text_body=f"Test email — support-ticket mail is set up correctly.\n\n{text}",
    )


# ── Sending ────────────────────────────────────────────────────────────

_token: tuple[str, float] | None = None  # (access token, expiry time)


def _graph_token(client: httpx.Client) -> str:
    global _token
    if _token and _token[1] > time.time() + 60:
        return _token[0]
    response = client.post(
        TOKEN_URL.format(tenant=settings.outlook_tenant_id),
        data={
            "client_id": settings.outlook_client_id,
            "client_secret": settings.outlook_client_secret,
            "scope": GRAPH_SCOPE,
            "grant_type": "client_credentials",
        },
    )
    if response.status_code != 200:
        # The error body names the problem (wrong secret, missing consent) but never contains the secret.
        raise RuntimeError(f"Graph token request failed: HTTP {response.status_code} {response.text[:300]}")
    payload = response.json()
    _token = (payload["access_token"], time.time() + int(payload.get("expires_in", 3600)))
    return _token[0]


def _send_graph(mail: Mail, client: httpx.Client | None = None) -> None:
    own_client = client is None
    client = client or httpx.Client(timeout=settings.outlook_timeout_seconds)
    try:
        token = _graph_token(client)
        response = client.post(
            SEND_URL.format(sender=settings.outlook_sender),
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": {
                    "subject": mail.subject,
                    "body": {"contentType": "HTML", "content": mail.html_body},
                    "toRecipients": [{"emailAddress": {"address": a}} for a in mail.to],
                },
                "saveToSentItems": True,
            },
        )
        if response.status_code != 202:
            raise RuntimeError(f"Graph sendMail failed: HTTP {response.status_code} {response.text[:300]}")
    finally:
        if own_client:
            client.close()


def _send_smtp(mail: Mail) -> None:
    message = EmailMessage()
    # Graph always shows the mailbox's own display name; SMTP can set one.
    message["From"] = formataddr((settings.outlook_sender_name, settings.outlook_sender))
    message["To"] = ", ".join(mail.to)
    message["Subject"] = mail.subject
    message.set_content(mail.text_body)
    message.add_alternative(mail.html_body, subtype="html")
    with smtplib.SMTP(settings.outlook_smtp_host, settings.outlook_smtp_port,
                      timeout=settings.outlook_timeout_seconds) as smtp:
        smtp.starttls()
        smtp.login(settings.outlook_smtp_username or settings.outlook_sender, settings.outlook_smtp_password)
        smtp.send_message(message)


def send(mail: Mail, kind: str) -> None:
    """Send one mail. Raises OutlookNotConfigured if .env is incomplete, or the send error."""
    missing = missing_settings(kind=kind)
    if missing:
        raise OutlookNotConfigured("missing .env values: " + ", ".join(missing))
    if not mail.to:
        raise OutlookNotConfigured("no recipient address")
    started = time.perf_counter()
    if settings.outlook_send_method.lower() == "graph":
        _send_graph(mail)
    else:
        _send_smtp(mail)
    log_event(logger, "outlook_mail_sent", kind=kind, method=settings.outlook_send_method,
              recipients=len(mail.to), elapsed_ms=round((time.perf_counter() - started) * 1000))
