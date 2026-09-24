from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    """What the frontend currently knows about the SyteLine screen the
    user is on. Real screens would supply this automatically (master
    prompt's Context Bridge); until that's wired up, the frontend's
    Context Simulator panel lets a person set it by hand."""

    site: str | None = None
    module: str | None = None
    form: str | None = None
    component: str | None = None
    field: str | None = None
    record_type: str | None = None
    record_id: str | None = None


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    session_token: str | None = None
    simulated_group: str | None = None  # mock-only: which test user/group to act as
    context: ChatContext | None = None


class ChatResponse(BaseModel):
    route: str  # FAST_QA_RESPONSE | CLARIFY | MARKDOWN_RAG_RESPONSE | NO_ANSWER | BLOCKED
    answer: str | None
    source: str | None = None  # single source, e.g. a Q&A id
    sources: list[str] | None = None  # multiple sources, e.g. Markdown RAG citations
    score: float
    reason: str | None = None  # why BLOCKED, if it was
    context: dict | None = None  # echoes user/site/module back for transparency
