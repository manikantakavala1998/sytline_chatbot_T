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
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
SEND_URL = "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
SUBJECT_ISSUE_CHARS = 80

TRIGGER_TEXT = {
    "frustration": "User was frustrated",
    "persistent": "Same problem came back",
    "unresolved": "Two answers in a row could not resolve it",
    "user_request": "User asked for a person / a ticket",
    "user_confirmed": "User raised it",
}


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
BADGE = {  # (text colour, background) — always shown with a word, never colour alone
    "critical": ("#ffffff", "#b52e2e"),
    "warning": ("#5c3b00", "#fde3a7"),
    "good": ("#ffffff", "#0c7d0c"),
    "neutral": (INK, "#e3e8f5"),
    "on_brand": (BRAND, "#ffffff"),
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
MOOD_TEXT = {
    "F0_NORMAL": "Calm", "F1_CONFUSED": "Confused", "F2_COMPLAINT": "Complaining",
    "F3_FRUSTRATED": "Frustrated", "F4_PERSISTENT": "Persistent (asked again)",
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
            f'<div style="font-size:12px;font-weight:bold;letter-spacing:.06em;text-transform:uppercase;'
            f'color:{FAINT};padding-bottom:8px">{_e(title)}</div>{inner}</td></tr>')


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
<tr><td bgcolor="{band}" style="background:{band};padding:22px 28px;border-radius:12px 12px 0 0">
<div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#dbe5ff">{_e(eyebrow)}</div>
<div style="font-size:24px;font-weight:bold;color:#ffffff;padding:4px 0 10px">{_e(title)}</div>
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
        body += _button("Open the feedback console", settings.admin_console_url)
    return _layout(preheader=intro, eyebrow=eyebrow, title=title, badges=badges, body_rows=body, footer=footer,
                   band=band)


def _screen(item: dict) -> str:
    return " / ".join(p for p in (item.get("site"), item.get("module"), item.get("form")) if p)


def _conversation(turns: list[dict]) -> tuple[str, str]:
    """The turns before the ticket: question, what the assistant did, and the start of its answer."""
    html_turns, text_turns = [], []
    for number, turn in enumerate(turns, 1):
        outcome, kind = OUTCOME_TEXT.get(turn.get("outcome"), (turn.get("outcome") or "", "neutral"))
        answer = turn.get("answer")
        html_turns.append(
            f'<tr><td width="28" style="vertical-align:top;padding:10px 0;color:{FAINT};font-size:13px;'
            f'font-weight:bold">{number}.</td><td style="vertical-align:top;padding:10px 0;'
            f'border-bottom:1px solid {BORDER}">'
            f'<div style="font-size:14px;font-weight:bold;color:{INK};padding-bottom:6px">{_e(turn.get("question"))}</div>'
            f'<div style="padding-bottom:{6 if answer else 0}px">{_badge(outcome, kind)}</div>'
            + (f'<div style="font-size:13px;line-height:19px;color:{SOFT}">{_e(answer)}</div>' if answer else "")
            + "</td></tr>"
        )
        text_turns.append(f"{number}. {turn.get('question')} — {outcome}" + (f"\n   {answer}" if answer else ""))
    table = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(html_turns)}</table>'
    return table, "\n".join(text_turns)


def ticket_mail(ticket: dict) -> Mail:
    ref = ticket["ticket_ref"]
    issue = ticket.get("issue_summary") or "Support request"
    short = issue if len(issue) <= SUBJECT_ISSUE_CHARS else issue[:SUBJECT_ISSUE_CHARS] + "…"
    high = ticket.get("priority") == "high"
    priority = "HIGH" if high else "Normal"
    subject = f"[{ref}] {priority} priority — {short}"
    who = ticket.get("user_display_name") or ticket["user_id"]
    user = f"{who} ({ticket['user_id']})" if who != ticket["user_id"] else who
    reason = TRIGGER_TEXT.get(ticket.get("trigger"), ticket.get("trigger"))
    mood = MOOD_TEXT.get(ticket.get("mood") or "", ticket.get("mood"))
    record = " ".join(p for p in (ticket.get("record_type"), ticket.get("record_id")) if p)
    created = _when(ticket.get("created_at"))
    turns = ticket.get("conversation_summary") or []

    badges = " ".join([
        _badge("▲ HIGH priority" if high else "Normal priority", "critical" if high else "on_brand"),
        _badge("● Open", "on_brand"),
    ])
    body = _section("What the user needs help with",
                    f'<div style="font-size:18px;line-height:26px;font-weight:bold;color:{INK}">{_e(issue)}</div>')
    if ticket.get("user_note"):
        body += _section("User’s note",
                         f'<div style="background:{PANEL};border-left:3px solid {BRAND};padding:10px 14px;'
                         f'font-size:14px;line-height:21px;color:{INK}">“{_e(ticket["user_note"])}”</div>')
    body += _section("Details", _facts([
        ("Raised by", _e(user)),
        ("Raised on", _e(created)),
        ("SyteLine screen", _e(_screen(ticket))),
        ("Record", _e(record)),
        ("Why it was raised", _e(reason) if reason else None),
        ("User’s mood", _e(mood) if mood else None),
    ]))
    conversation_html, conversation_text = _conversation(turns)
    if turns:
        body += _section(f"Conversation before the ticket ({len(turns)} question{'s' if len(turns) != 1 else ''})",
                         conversation_html)
    body += _section("What to do next",
                     f'<div style="font-size:14px;line-height:22px;color:{INK}">'
                     f"1. Contact {_e(who)} about this issue.<br>"
                     f"2. In the feedback console → <b>Tickets</b>, set {_e(ref)} to <b>In progress</b>, "
                     f"then <b>Resolved</b> when it is fixed.</div>")
    if settings.admin_console_url:
        body += _button(f"Open {ref} in the feedback console", settings.admin_console_url)
    footer = ("Sent automatically by the SyteLine Prospect-to-Cash assistant when the user confirmed the ticket. "
              "Passwords and other secrets in the conversation are masked.")

    text = "\n".join(line for line in [
        f"New support ticket {ref} — {priority} priority",
        "",
        f"What the user needs help with: {issue}",
        f"User's note: {ticket['user_note']}" if ticket.get("user_note") else None,
        "",
        f"Raised by: {user}",
        f"Raised on: {created}" if created else None,
        f"SyteLine screen: {_screen(ticket)}" if _screen(ticket) else None,
        f"Record: {record}" if record else None,
        f"Why it was raised: {reason}" if reason else None,
        f"User's mood: {mood}" if mood else None,
        "",
        "Conversation before the ticket:" if turns else None,
        conversation_text if turns else None,
        "",
        f"Next: contact {who}, then set {ref} to In progress / Resolved in the feedback console (Tickets tab).",
        settings.admin_console_url or None,
        "",
        footer,
    ] if line is not None)
    return Mail(
        to=recipients(settings.support_ticket_email),
        subject=subject,
        html_body=_layout(preheader=f"{who} · {_screen(ticket) or 'SyteLine'} · {short}",
                          eyebrow="SyteLine assistant · New support ticket", title=ref, badges=badges,
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
              "feedback console (Security tab).")
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
    footer = "Open the feedback console → Health tab for the numbers behind this alert."
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
