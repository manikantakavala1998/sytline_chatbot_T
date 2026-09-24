"""Central application logging.

Every application event is written to both the terminal and one active
log file: ``logs/chatbot.log``.  The same human-readable format is used in
both places, and request-scoped events include a request ID so a complete
chat turn can be followed from HTTP entry to the final response.

Never pass secrets, session tokens, raw user questions, generated answers,
or retrieved document text into :func:`log_event`.
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

_configured = False
_configuration_lock = threading.Lock()


def _configure_logging() -> None:
    global _configured
    if _configured:
        return

    with _configuration_lock:
        if _configured:
            return

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        terminal_handler = logging.StreamHandler(sys.stdout)
        terminal_handler.setLevel(logging.INFO)
        terminal_handler.setFormatter(formatter)
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
