"""When to offer a support ticket (Phase 5 step 3, master prompt §55).

States:
  ESC_NONE                              nothing to offer
  ESC_SUGGEST_TICKET                    offer a ticket ("I can raise a ticket for you")
  ESC_CREATE_TICKET_AFTER_CONFIRMATION  the user asked for one; create it once they confirm

A ticket is NEVER created by this module. The user always confirms (the 🎫 button in the chat
calls POST /api/tickets) — §55 requires confirmation unless a future business policy allows
automatic creation.

Triggers for a suggestion:
  frustration     the user is frustrated (F3)
  persistent      the same problem again (F4 — repeated question, "still not working")
  unresolved      this answer and an earlier one in the last few turns were NO_ANSWER / CLARIFY
  user_request    the user asked for a ticket / a human (-> confirmation state)

Security attacks never get a ticket offer — they go to the separate security-event flow (§56).
"""

import re
from dataclasses import dataclass
from enum import Enum

from backend.app.classification.taxonomy import EmotionLabel
from backend.app.history.store import Turn


class EscalationState(str, Enum):
    NONE = "ESC_NONE"
    SUGGEST_TICKET = "ESC_SUGGEST_TICKET"
    CREATE_AFTER_CONFIRMATION = "ESC_CREATE_TICKET_AFTER_CONFIRMATION"


FAILED_ROUTES = {"NO_ANSWER", "CLARIFY"}
# Attacks, off-topic questions, missing permissions and small talk are not support problems.
NO_TICKET_ROUTES = {"BLOCKED", "OUT_OF_SCOPE"}
FAILED_TURNS_LOOKBACK = 3

# Offline fallback for "raise a ticket / let me talk to a person" (the conversation LLM is the
# primary detector). Questions ABOUT tickets or SyteLine records are not requests.
_TICKET_REQUEST = re.compile(
    r"\b(?:raise|create|open|log|file|submit|make)\s+(?:a\s+|an\s+|me\s+a\s+)?(?:support\s+|help\s*desk\s+|it\s+)?"
    r"(?:ticket|case|incident)\b"
    r"|\b(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+|some\s*one\s*(?:from\s+)?|the\s+)?"
    r"(?:human|person|real person|agent|someone|support|support team|admin|consultant|helpdesk|help desk)\b"
    r"|\bescalate\b|\bconnect me (?:to|with)\b|\bneed (?:a\s+)?human\b",
    re.IGNORECASE,
)
# "can I speak to someone" is a polite request, so "can I" is not treated as a how-to question.
_HOW_TO = re.compile(r"^\s*(?:how|what|where|why|when|which|do i|is there)\b", re.IGNORECASE)


def is_ticket_request(text: str) -> bool:
    return bool(_TICKET_REQUEST.search(text)) and not _HOW_TO.match(text)


@dataclass
class EscalationDecision:
    state: EscalationState = EscalationState.NONE
    trigger: str | None = None


def decide_escalation(
    route: str,
    mood: EmotionLabel,
    history: list[Turn],
    user_requested: bool = False,
) -> EscalationDecision:
    if route in NO_TICKET_ROUTES:
        return EscalationDecision()
    if user_requested:
        return EscalationDecision(EscalationState.CREATE_AFTER_CONFIRMATION, "user_request")
    if mood == EmotionLabel.PERSISTENT:
        return EscalationDecision(EscalationState.SUGGEST_TICKET, "persistent")
    if mood == EmotionLabel.FRUSTRATED:
        return EscalationDecision(EscalationState.SUGGEST_TICKET, "frustration")
    if route in FAILED_ROUTES and any(
        turn.route in FAILED_ROUTES for turn in history[-FAILED_TURNS_LOOKBACK:]
    ):
        return EscalationDecision(EscalationState.SUGGEST_TICKET, "unresolved")
    return EscalationDecision()
