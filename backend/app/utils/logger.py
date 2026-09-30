"""Central application logging.

Two streams share the terminal and one active log file, ``logs/chatbot.log``:

* **Trace lines** (logger ``trace``, written by ``utils/trace.py``): the clear, numbered,
  human-readable story of startup and of every question — always in the terminal and the file.
* **Event lines** (``log_event``): technical ``event=... key=value`` lines with the full request
  ID. Always in the file; in the terminal only when ``LOG_TERMINAL=all`` (default ``trace``
  shows trace lines plus every warning and error).

Never pass secrets, session tokens, raw user questions, generated answers,
or retrieved document text into :func:`log_event` — question/answer text belongs only in the
trace, which masks secrets and can be switched off with ``LOG_CONVERSATION_TEXT=false``.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "chatbot.log"
TRACE_LOGGER_NAME = "trace"
# Chatty libraries: their INFO lines (every OpenAI HTTP call, model downloads) drown the trace.
QUIET_LIBRARIES = ("httpx", "httpcore", "openai", "sentence_transformers", "urllib3", "pymilvus", "huggingface_hub")

_configured = False
_configuration_lock = threading.Lock()


class _Formatter(logging.Formatter):
    """Trace lines: `time  message`. Everything else: `time  LEVEL  module  message`."""

    def __init__(self) -> None:
        super().__init__(fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        self._trace = logging.Formatter(fmt="%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        return self._trace.format(record) if record.name == TRACE_LOGGER_NAME else super().format(record)


class _TerminalFilter(logging.Filter):
    """LOG_TERMINAL=trace (default): trace lines + warnings/errors. LOG_TERMINAL=all: everything."""

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.show_all = mode.lower() == "all"

    def filter(self, record: logging.LogRecord) -> bool:
        return self.show_all or record.name == TRACE_LOGGER_NAME or record.levelno >= logging.WARNING


def _terminal_mode() -> str:
    try:
        from backend.app.config import settings  # lazy: config must never depend on logging

        return settings.log_terminal
    except Exception:
        return "trace"


def _configure_logging() -> None:
    global _configured
    if _configured:
        return

    with _configuration_lock:
        if _configured:
            return

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        formatter = _Formatter()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        for library in QUIET_LIBRARIES:
            logging.getLogger(library).setLevel(logging.WARNING)

        terminal_handler = logging.StreamHandler(sys.stdout)
        terminal_handler.setLevel(logging.INFO)
        terminal_handler.setFormatter(formatter)
        terminal_handler.addFilter(_TerminalFilter(_terminal_mode()))
        terminal_handler._syteline_handler = True  # type: ignore[attr-defined]

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        file_handler._syteline_handler = True  # type: ignore[attr-defined]

        # Uvicorn reloads modules in-process during development. Remove only
        # handlers installed by this module so reloads never duplicate lines.
        for handler in list(root_logger.handlers):
            if getattr(handler, "_syteline_handler", False):
                root_logger.removeHandler(handler)
                handler.close()

        root_logger.addHandler(terminal_handler)
        root_logger.addHandler(file_handler)
        _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)


def _safe_value(value: Any) -> str:
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    return text[:300]


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Write a structured, single-line lifecycle event.

    Field order is preserved, which keeps a request's terminal/file trace
    easy to read without requiring a separate log viewer.
    """

    details = " ".join(
        f"{key}={_safe_value(value)}" for key, value in fields.items() if value is not None
    )
    message = f"event={event}"
    if details:
        message = f"{message} {details}"
    logger.info(message)
