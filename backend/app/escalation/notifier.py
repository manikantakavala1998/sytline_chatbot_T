"""Where new tickets and security alerts are sent (Phase 5 step 3).

ESCALATION_NOTIFIER selects it:
  log      write a structured log event only (the data is already in Postgres)
  outlook  also email it through Outlook / Microsoft 365 (see escalation/outlook.py)

Mail is sent on a background thread, so a user confirming a ticket never waits for Outlook.
A failure never fails the user's request — the ticket/event is already saved — and each
ticket records whether its mail went out (sent / failed / not_configured), shown in the
feedback console. If the Outlook .env values are incomplete, it logs and falls back to "log".
"""

from concurrent.futures import ThreadPoolExecutor

from backend.app.config import settings
from backend.app.escalation import outlook
from backend.app.utils import trace
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="notify")
# Tests set this to run notifications inline.
RUN_INLINE = False


class LogNotifier:
    name = "log"

    def ticket_created(self, ticket: dict) -> str:
        log_event(logger, "notify_ticket_created", ticket=ticket["ticket_ref"], priority=ticket["priority"],
                  user_id=ticket["user_id"], trigger=ticket.get("trigger"))
        return "logged"

    def security_alert(self, event: dict) -> str:
        logger.warning(
            "event=notify_security_alert user_id=%s label=%s severity=%s attempts_in_window=%s request_id=%s",
            event["user_id"], event["label"], event["severity"], event["attempts_in_window"], event["request_id"],
        )
        return "logged"

    def health_alert(self, alert: dict) -> str:
        logger.warning("event=notify_health_alert state=%s rule=%s severity=%s message=%s", alert.get("state"),
                       alert["rule"], alert.get("severity"), alert.get("message"))
        return "logged"


class OutlookNotifier(LogNotifier):
    """Logs like LogNotifier, then emails the ticket / alert."""

    name = "outlook"

    def ticket_created(self, ticket: dict) -> str:
        super().ticket_created(ticket)
        return _deliver(outlook.ticket_mail(ticket), "ticket", ticket["ticket_ref"])

    def security_alert(self, event: dict) -> str:
        super().security_alert(event)
        if not settings.security_alert_email.strip():
            return "not_configured"  # alert mail is optional
        return _deliver(outlook.security_mail(event), "security_alert", str(event.get("event_id")))

    def health_alert(self, alert: dict) -> str:
        super().health_alert(alert)
        if not settings.ops_alert_email.strip():
            return "not_configured"  # health mail is optional
        return _deliver(outlook.health_mail(alert), "health_alert", alert["rule"])


def _deliver(mail: outlook.Mail, kind: str, reference: str) -> str:
    try:
        outlook.send(mail, kind)
        trace.note(f"📧 {kind} email for {reference} SENT via {settings.outlook_send_method} to "
                   f"{', '.join(mail.to)}")
        return "sent"
    except outlook.OutlookNotConfigured as exc:
        logger.warning("event=outlook_not_configured kind=%s ref=%s detail=%s", kind, reference, exc)
        trace.note(f"📧 {kind} email for {reference} NOT SENT — mail not set up ({exc})")
        return "not_configured"
    except Exception as exc:
        # Log the error type and message (they name the problem — never the secret).
        logger.error("event=outlook_mail_failed kind=%s ref=%s error=%s: %s", kind, reference,
                     type(exc).__name__, str(exc)[:300])
        trace.note(f"📧 {kind} email for {reference} FAILED — {type(exc).__name__}: {trace.clean(exc, 160)}")
        return "failed"


_NOTIFIERS = {LogNotifier.name: LogNotifier, OutlookNotifier.name: OutlookNotifier}


def get_notifier():
    cls = _NOTIFIERS.get(settings.escalation_notifier.lower())
    if cls is None:
        logger.warning("event=unknown_escalation_notifier name=%s action=use_log", settings.escalation_notifier)
        cls = LogNotifier
    return cls()


def _run(method: str, payload: dict) -> None:
    try:
        status = getattr(get_notifier(), method)(payload)
    except Exception:
        logger.exception("event=escalation_notify_failed method=%s", method)
        status = "failed"
    if method == "ticket_created" and payload.get("ticket_id"):
        # Imported here: the store imports nothing from this module, keep it that way.
        from backend.app.escalation import store

        try:
            store.set_notification_status(payload["ticket_id"], status)
        except Exception:
            logger.exception("event=ticket_notification_status_failed ticket=%s", payload.get("ticket_ref"))


def notify_safely(method: str, payload: dict) -> None:
    """Send in the background; never raises."""
    if RUN_INLINE:
        _run(method, payload)
    else:
        _executor.submit(_run, method, payload)


def startup_check() -> None:
    """Say at startup whether ticket mail will work, naming any missing .env values (not their contents)."""
    if settings.escalation_notifier.lower() != "outlook":
        log_event(logger, "escalation_notifier_ready", notifier=settings.escalation_notifier, mail="off")
        trace.startup("Ticket email", "off — tickets are saved and shown in the console only")
        return
    missing = outlook.missing_settings()
    if missing:
        logger.warning("event=outlook_not_configured missing=%s action=tickets_saved_without_mail",
                       ",".join(missing))
        trace.startup("Ticket email (Outlook)", f"NOT READY — missing .env value(s): {', '.join(missing)}")
    else:
        log_event(logger, "escalation_notifier_ready", notifier="outlook", method=settings.outlook_send_method,
                  security_alert_mail=bool(settings.security_alert_email.strip()))
        trace.startup("Ticket email (Outlook)", f"configured ({settings.outlook_send_method}) · tickets to "
                      f"{len(outlook.recipients(settings.support_ticket_email))} address(es) · security alerts "
                      + ("emailed" if settings.security_alert_email.strip() else "not emailed")
                      + " · use 'Send test email' in the console to confirm the login works")
