"""
Builds one normalized RequestContext per turn (master prompt section 20)
— combines the bootstrapped SyteLine user, current configuration/site,
whatever screen/field/record context the frontend sent, and the business
domain. Nothing downstream should read raw session or UI data directly;
everything reads this one object instead.

Real SyteLine screens would supply the `ui`/`record` fields automatically
(master prompt section 3's Context Bridge — form/field/record detection
is still `[NEEDS SYTELINE CONFIRMATION]`, section 73 item 13-15). Until
that's wired up, the frontend's Context Simulator panel lets a person set
these manually so the rest of the pipeline can be built and tested now.
"""

from pydantic import BaseModel

from backend.app.integrations.syteline.session_context import SyteLineUser


class UIContext(BaseModel):
    module: str | None = None
    form: str | None = None
    component: str | None = None
    field: str | None = None


class RecordContext(BaseModel):
    record_type: str | None = None
    record_id: str | None = None


class RequestContext(BaseModel):
    request_id: str
    user_id: str
    user_display_name: str
    groups: list[str]
    configuration: str
    site: str
    ui: UIContext
    record: RecordContext
    domain: str = "PROSPECT_TO_CASH"


def build_request_context(
    request_id: str,
    user: SyteLineUser,
    configuration: str,
    site: str,
    ui: UIContext,
    record: RecordContext,
) -> RequestContext:
    return RequestContext(
        request_id=request_id,
        user_id=user.user_id,
        user_display_name=user.display_name,
        groups=user.groups,
        configuration=configuration,
        site=site,
        ui=ui,
        record=record,
    )
