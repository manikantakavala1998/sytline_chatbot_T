"""Shared test setup."""

import pytest

from backend.app.config import settings
from backend.app.escalation import notifier


@pytest.fixture(autouse=True)
def no_real_mail(monkeypatch):
    """.env may turn Outlook ticket mail on (ENABLE_TICKET_RAISING / ESCALATION_NOTIFIER=outlook).
    Tests must never send real email, so every test starts with the log-only notifier, run
    inline. tests/test_outlook.py switches Outlook back on with faked Graph/SMTP."""
    monkeypatch.setattr(settings, "escalation_notifier", "log")
    monkeypatch.setattr(notifier, "RUN_INLINE", True)
