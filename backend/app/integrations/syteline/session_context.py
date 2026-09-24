"""
Stands in for a real connection to SyteLine's session/security APIs.

The real implementation is blocked on master prompt section 73's open
questions — how the chatbot actually receives the trusted, logged-in
SyteLine session, how groups/site/configuration are actually queried,
against the real WebClient environment (confirmed target:
https://syteline.myhumanet.com/WSWebClient/... ConfigGroup=AIDEMO, but
that only tells us WHICH system, not the technical session-bridging
mechanism). Until those are confirmed, every function here returns
realistic-shaped mock data so the rest of the app can be built and tested
against the real interface shape.

Swap only this file (and MOCK_GROUP_PERMISSIONS in
backend/app/authorization/resolver.py) once real SyteLine integration
lands — nothing that calls these functions needs to change.

For testing without a real SyteLine session, the frontend's Context
Simulator panel lets you pick which mock user/group to act as; that
choice arrives here as `simulated_group`. A real integration would
ignore that entirely and read the actual logged-in user instead.
"""

from dataclasses import dataclass

MOCK_GROUPS = ["SALES_REP", "AR_CLERK", "NO_ACCESS"]
DEFAULT_MOCK_GROUP = "SALES_REP"


@dataclass
class SyteLineUser:
    user_id: str
    display_name: str
    groups: list[str]
    sites: list[str]


def get_logged_in_user(simulated_group: str | None = None) -> SyteLineUser:
    group = simulated_group if simulated_group in MOCK_GROUPS else DEFAULT_MOCK_GROUP
    return SyteLineUser(
        user_id=f"demo.{group.lower()}",
        display_name=f"Demo User ({group})",
        groups=[group],
        sites=["MAIN"],
    )


def validate_session(session_token: str | None) -> bool:
    # Mock: any non-empty token counts as valid. The real check validates
    # the actual SyteLine session/token once section 73's questions are
    # answered — this is intentionally permissive so Phase 2's other
    # pieces (permissions, context) can be built and tested now.
    return bool(session_token)


def get_configuration() -> str:
    return "AIDEMO"


def get_current_site() -> str:
    return "MAIN"
