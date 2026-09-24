"""Typed state and final result contracts for the chat workflow."""

from typing import TypedDict

from pydantic import BaseModel, Field

from backend.app.classification.taxonomy import (
    AmbiguityResult,
    QueryClassification,
    QueryTransformResult,
    RouteLabel,
    ScopeResult,
    SecurityResult,
)
from backend.app.context.manager import RequestContext
from backend.app.integrations.syteline.session_context import SyteLineUser


class WorkflowResult(BaseModel):
    route: str
    answer: str | None = None
    source: str | None = None
    sources: list[str] | None = None
    score: float = 0.0
    reason: str | None = None
    decision_trace: dict[str, object] = Field(default_factory=dict)


class ChatWorkflowState(TypedDict, total=False):
    request_id: str
    query: str
    context: RequestContext
    user: SyteLineUser
    security: SecurityResult
    scope: ScopeResult
    ambiguity: AmbiguityResult
    transformed: QueryTransformResult
    classification: QueryClassification
    selected_route: RouteLabel
    result: WorkflowResult

