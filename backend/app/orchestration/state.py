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
from backend.app.classification.conversation import ConversationAnalysis
from backend.app.context.manager import RequestContext
from backend.app.history.store import Turn
from backend.app.integrations.syteline.session_context import SyteLineUser


class WorkflowResult(BaseModel):
    route: str
    answer: str | None = None
    source: str | None = None
    sources: list[str] | None = None
    score: float = 0.0
    reason: str | None = None
    resolved_query: str | None = None  # standalone rewrite of a follow-up, if one was made
    decision_trace: dict[str, object] = Field(default_factory=dict)


class ChatWorkflowState(TypedDict, total=False):
    request_id: str
    # `query` is what every step after follow-up resolution works on; for a follow-up
    # like "how do I convert it?" it is the standalone rewrite, and `original_query`
    # keeps what the user actually typed.
    query: str
    original_query: str
    history: list[Turn]
    followup_resolved: bool
    # LLM reading of the message: small-talk kind, greeting, "how are you", clean question.
    conversation: ConversationAnalysis
    context: RequestContext
    user: SyteLineUser
    security: SecurityResult
    scope: ScopeResult
    ambiguity: AmbiguityResult
    transformed: QueryTransformResult
    classification: QueryClassification
    selected_route: RouteLabel
    # Best curated Excel row for the question (qa_id, question-match score), handed from the
    # Fast Q&A node to the unified search, which decides whether to show it verbatim.
    qa_candidate: tuple[str, float]
    result: WorkflowResult

