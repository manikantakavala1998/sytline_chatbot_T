"""
Follow-up resolution using conversation history (flowchart Level 1 "conversation
history" and Level 5 "coreference resolution").

  Q1: "What is a quotation?"
  Q2: "How do I convert it?"   ->  "How do I convert a quotation?"

Runs right after the security gate, before scope/ambiguity, so every later
step sees a standalone question (otherwise "how do I convert it?" looks
vague and gets a clarification request).

Cheap by design: the LLM is called only when there IS earlier history and
the message looks like a follow-up (a reference word like "it"/"that", or a
very short "and the invoice?"-style message). On any failure the original
message is used unchanged — history can only help, never break a reply.
"""

import json
import re

from openai import OpenAI

from backend.app.config import settings
from backend.app.history.store import Turn
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

ANSWER_CHARS_IN_PROMPT = 600
MAX_STANDALONE_CHARS = 1000
SHORT_MESSAGE_WORDS = 4

_REFERENCE = re.compile(
    r"\b(it|its|this|that|these|those|they|them|their|there|same|above|previous|former|latter|"
    r"next|then|after that|before that|one|ones)\b",
    re.IGNORECASE,
)
_CONTINUATION_START = re.compile(r"^\s*(and|also|so|but|what about|how about|why|why not|what else)\b", re.IGNORECASE)
# Small talk is answered without history; never spend an LLM call on it.
_SMALL_TALK = re.compile(
    r"^\s*(thanks?|thank you|thx|ok(ay)?|great|cool|nice|perfect|got it|bye|goodbye|see you|"
    r"hi|hello|hey|good (morning|afternoon|evening))\b[\s\w,!.]*$",
    re.IGNORECASE,
)

PROMPT = (
    "You rewrite the user's LATEST message of a SyteLine Prospect-to-Cash help chat into ONE "
    "standalone message that can be understood without the conversation. Replace references "
    "such as it/this/that/they/the next step with the exact thing they refer to from the earlier "
    "turns. Keep the user's own wording, language, greeting, and number of questions. Do not "
    "answer, do not add facts, do not add new questions. If the latest message is already "
    "standalone, or is small talk, return it unchanged. Return JSON only: {\"standalone\": \"...\"}"
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.orchestrator_timeout_seconds,
            max_retries=1,
        )
    return _client


def looks_like_followup(query: str) -> bool:
    if _SMALL_TALK.match(query):
        return False
    if _REFERENCE.search(query) or _CONTINUATION_START.match(query):
        return True
    return len(query.split()) <= SHORT_MESSAGE_WORDS


def _conversation_text(history: list[Turn]) -> str:
    lines = []
    for turn in history:
        answer = turn.answer if len(turn.answer) <= ANSWER_CHARS_IN_PROMPT else turn.answer[:ANSWER_CHARS_IN_PROMPT] + "…"
        lines.append(f"User: {turn.question}\nAssistant: {answer}")
    return "\n\n".join(lines)


def resolve_followup(query: str, history: list[Turn], request_id: str) -> tuple[str, bool]:
    """Returns (standalone query, whether it was rewritten)."""
    if not history or not settings.orchestrator_llm_enabled or not looks_like_followup(query):
        return query, False

    try:
        response = _get_client().chat.completions.create(
            model=settings.orchestrator_model,
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": f"CONVERSATION SO FAR:\n{_conversation_text(history)}\n\nLATEST MESSAGE:\n{query}",
                },
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        standalone = str(payload.get("standalone", "")).strip()
    except Exception:
        logger.exception("event=followup_resolution_failed request_id=%s", request_id)
        return query, False

    if not standalone or len(standalone) > MAX_STANDALONE_CHARS:
        return query, False
    rewritten = standalone.casefold() != query.strip().casefold()
    log_event(
        logger,
        "followup_resolution_completed",
        request_id=request_id,
        history_turns=len(history),
        rewritten=rewritten,
    )
    return (standalone if rewritten else query), rewritten
