"""Where new tickets and security alerts are sent (Phase 5 step 3).

Only the "log" notifier exists today: every ticket and alert is written as a structured log
event (and is already stored in Postgres). Email or Microsoft Teams plug in here later — add
a class with the same two methods and select it with ESCALATION_NOTIFIER; nothing else changes.
A notifier failure never fails the user's request: the ticket/event is already saved.
"""

from backend.app.config import settings
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)


class LogNotifier:
    name = "log"

    def ticket_created(self, ticket: dict) -> None:
        log_event(logger, "notify_ticket_created", ticket=ticket["ticket_ref"], priority=ticket["priority"],
                  user_id=ticket["user_id"], trigger=ticket.get("trigger"))

    def security_alert(self, event: dict) -> None:
        logger.warning(
            "event=notify_security_alert user_id=%s label=%s severity=%s attempts_in_window=%s request_id=%s",
            event["user_id"], event["label"], event["severity"], event["attempts_in_window"], event["request_id"],
        )


_NOTIFIERS = {LogNotifier.name: LogNotifier}


def get_notifier():
    cls = _NOTIFIERS.get(settings.escalation_notifier)
    if cls is None:
        logger.warning("event=unknown_escalation_notifier name=%s action=use_log", settings.escalation_notifier)
        cls = LogNotifier
    return cls()


def notify_safely(method: str, payload: dict) -> None:
    try:
        getattr(get_notifier(), method)(payload)
    except Exception:
        logger.exception("event=escalation_notify_failed method=%s", method)
