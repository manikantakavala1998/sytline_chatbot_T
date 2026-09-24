from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    route: str  # FAST_QA_RESPONSE | CLARIFY | MARKDOWN_RAG_RESPONSE | NO_ANSWER | BLOCKED
    answer: str | None
    source: str | None = None  # single source, e.g. a Q&A id
    sources: list[str] | None = None  # multiple sources, e.g. Markdown RAG citations
    score: float
