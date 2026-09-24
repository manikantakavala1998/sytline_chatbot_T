"""
Phase 1 placeholder for permission checking.

Every place in the code that will eventually need a real SyteLine
permission check calls check_permission() from here, even though right
now it always says "allowed". This way, when Phase 2 builds the real
SyteLine permission resolver, we swap what's inside this function only —
nothing else in the app has to change.
"""

from dataclasses import dataclass


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str = "mocked-allow"


def check_permission(user_id: str, operation: str, resource: str) -> PermissionDecision:
    return PermissionDecision(allowed=True, reason="Phase 1 mock: always allowed")
