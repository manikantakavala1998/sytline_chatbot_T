"""Clear, step-by-step trace of startup and of every question — terminal AND logs/chatbot.log.

Two kinds of log line exist:

  trace lines     written by this module for people: numbered steps, what went in, what came
                  out, why, and how long it took. Shown in the terminal and the log file.
  event lines     the technical `event=... key=value` lines from log_event(), for machines and
                  deep debugging. Always in the log file; in the terminal only with LOG_TERMINAL=all.

A request trace starts in the /chat route and is held in a context variable, so any module
(search, Excel matcher, answer check, answer generation) can add detail lines to the current
step without passing anything around. Outside a request these helpers do nothing.

Question / answer / document text is shown only if LOG_CONVERSATION_TEXT is on (default for
development — turn it off in production). Secrets are always masked and every value is kept on
one line, so a user can't forge extra log lines.
"""

import re
import time
from contextvars import ContextVar

from backend.app.utils.logger import TRACE_LOGGER_NAME, get_logger

_trace_logger = get_logger(TRACE_LOGGER_NAME)
_current: ContextVar["RequestTrace | None"] = ContextVar("request_trace", default=None)

_SECRETS = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}", re.IGNORECASE),
    re.compile(r"\b(password|passwd|api[_\s-]?key|secret|token)\s*[:=]\s*\S+", re.IGNORECASE),
]
RULE = "─" * 100
INDENT = " " * 13


def _content_on() -> bool:
    # Imported lazily: config imports nothing from here, but tests may swap settings.
    from backend.app.config import settings

    return settings.log_conversation_text


def clean(value, limit: int = 300) -> str:
    """One line, secrets masked, shortened."""
    text = " ".join(str(value).split())
    for pattern in _SECRETS:
        text = pattern.sub(lambda m: (m.group(1) + "=[masked]") if m.lastindex else "[masked]", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def text(value, limit: int = 300) -> str:
    """User/document/answer text — shown in quotes, or hidden when LOG_CONVERSATION_TEXT is off."""
    if value is None:
        return "—"
    if not _content_on():
        return f"[text hidden, {len(str(value))} chars]"
    return f"“{clean(value, limit)}”"


class RequestTrace:
    def __init__(self, request_id: str) -> None:
        self.tag = f"[{request_id[:8]}]"
        self.started = time.perf_counter()
        self.step_no = 0
        self._step_started: float | None = None

    def line(self, message: str) -> None:
        _trace_logger.info(f"{self.tag} {message}")

    def begin_step(self, title: str) -> None:
        self.step_no += 1
        self._step_started = time.perf_counter()
        self.line(f"STEP {self.step_no:>2}  {title}")

    def detail(self, message: str) -> None:
        self.line(f"{INDENT}{message}")

    def end_step(self, result: str) -> None:
        seconds = time.perf_counter() - self._step_started if self._step_started else 0.0
        self.line(f"{INDENT}→ {result}  ({seconds:.2f}s)")
        self._step_started = None

    def elapsed(self) -> float:
        return time.perf_counter() - self.started


def start_request(request_id: str) -> RequestTrace:
    trace = RequestTrace(request_id)
    _current.set(trace)
    _trace_logger.info(RULE)
    return trace


def current() -> RequestTrace | None:
    return _current.get()


def end_request() -> None:
    _current.set(None)


# ── Helpers that are safe to call from anywhere (no-op outside a request) ──


def detail(message: str) -> None:
    trace = _current.get()
    if trace:
        trace.detail(message)


def begin_step(title: str) -> None:
    trace = _current.get()
    if trace:
        trace.begin_step(title)


def end_step(result: str) -> None:
    trace = _current.get()
    if trace:
        trace.end_step(result)


def line(message: str) -> None:
    trace = _current.get()
    if trace:
        trace.line(message)


def note(message: str) -> None:
    """A clear line for things outside a chat question: tickets, emails, admin actions."""
    _trace_logger.info(f"NOTE     {message}")


# ── Startup ────────────────────────────────────────────────────────────


def startup(title: str, result: str = "") -> None:
    _trace_logger.info(f"STARTUP  {title:<30} {result}".rstrip())


def startup_detail(message: str) -> None:
    _trace_logger.info(f"STARTUP    {message}")


def banner(message: str) -> None:
    _trace_logger.info("═" * 100)
    _trace_logger.info(f"  {message}")
    _trace_logger.info("═" * 100)
