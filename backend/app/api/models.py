from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    route: str  # FAST_QA_RESPONSE | CLARIFY | MARKDOWN_RAG | BLOCKED
    answer: str | None
    source: str | None
    score: float
