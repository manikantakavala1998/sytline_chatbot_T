"""Per-request measurements (Phase 6): LLM calls, tokens, cost, step timings, database time.

A RequestUsage is started with each /chat request and held in a context variable, so every
module can add to it without passing anything around (the same pattern as utils/trace.py).
At the end of the request it is written into the audit record (audit/store.py), which is what
the Health dashboard and the health alerts read.

Cost = tokens × the price per million tokens in settings.model_prices (USD). The defaults are
the public list prices at the time of writing — check them against your OpenAI invoice and set
MODEL_PRICES in .env if they differ. Local models (embeddings, reranker) cost nothing and are
only timed.
"""

import time
from contextvars import ContextVar
from dataclasses import dataclass, field

from backend.app.config import settings

_current: ContextVar["RequestUsage | None"] = ContextVar("request_usage", default=None)


@dataclass
class LLMCall:
    purpose: str  # understanding | classifier | scope | security | answer | answer_repair | grounding_check
    model: str
    seconds: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    ok: bool = True
    error: str | None = None

    @property
    def cost_usd(self) -> float:
        price = settings.model_prices.get(self.model) or {}
        return (self.prompt_tokens * price.get("input", 0.0) + self.completion_tokens * price.get("output", 0.0)) / 1e6

    def as_dict(self) -> dict:
        return {"purpose": self.purpose, "model": self.model, "ms": round(self.seconds * 1000),
                "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
                "cost_usd": round(self.cost_usd, 6), "ok": self.ok, **({"error": self.error} if self.error else {})}


@dataclass
class RequestUsage:
    started: float = field(default_factory=time.perf_counter)
    llm_calls: list[LLMCall] = field(default_factory=list)
    stages_ms: dict[str, int] = field(default_factory=dict)
    db_ms: dict[str, int] = field(default_factory=dict)

    @property
    def prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.llm_calls)

    @property
    def completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.llm_calls)

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.llm_calls)

    def elapsed_ms(self) -> int:
        return round((time.perf_counter() - self.started) * 1000)


def start() -> RequestUsage:
    usage = RequestUsage()
    _current.set(usage)
    return usage


def current() -> RequestUsage | None:
    return _current.get()


def end() -> None:
    _current.set(None)


def record_llm(purpose: str, model: str, started: float, response=None, error: Exception | None = None) -> None:
    """Call right after an OpenAI chat completion (or when it failed)."""
    usage = _current.get()
    if usage is None:
        return
    tokens = getattr(response, "usage", None) if response is not None else None
    usage.llm_calls.append(LLMCall(
        purpose=purpose,
        model=model,
        seconds=time.perf_counter() - started,
        prompt_tokens=int(getattr(tokens, "prompt_tokens", 0) or 0),
        completion_tokens=int(getattr(tokens, "completion_tokens", 0) or 0),
        ok=error is None,
        error=f"{type(error).__name__}" if error else None,
    ))


def record_stage(name: str, seconds: float) -> None:
    usage = _current.get()
    if usage is not None:
        usage.stages_ms[name] = usage.stages_ms.get(name, 0) + round(seconds * 1000)


def record_db(operation: str, seconds: float) -> None:
    usage = _current.get()
    if usage is not None:
        usage.db_ms[operation] = usage.db_ms.get(operation, 0) + round(seconds * 1000)


def metered_create(purpose: str, client, **kwargs):
    """client.chat.completions.create(**kwargs), measured. Errors are recorded and re-raised."""
    started = time.perf_counter()
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        record_llm(purpose, kwargs.get("model", "?"), started, error=exc)
        raise
    record_llm(purpose, kwargs.get("model", "?"), started, response)
    return response
