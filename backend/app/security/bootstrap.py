"""
Security Bootstrap (master prompt section 2.1 / section 18) — establishes
who the current user is from their SyteLine session, before anything
else runs. There is no separate chatbot login: a missing or invalid
session is rejected outright, never silently treated as "guest".

Session validation and user lookup are mocked for now — see
backend/app/integrations/syteline/session_context.py for why, and what
swapping in the real thing later will involve.
"""

from backend.app.integrations.syteline.session_context import (
    SyteLineUser,
    get_logged_in_user,
    validate_session,
)


class InvalidSessionError(Exception):
    pass


def bootstrap_security(session_token: str | None, simulated_group: str | None = None) -> SyteLineUser:
    if not validate_session(session_token):
        raise InvalidSessionError("Missing or invalid SyteLine session")
    return get_logged_in_user(simulated_group=simulated_group)
