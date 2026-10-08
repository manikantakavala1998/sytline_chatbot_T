"""
Generates a grounded answer from the Markdown RAG chunks (master prompt
section 34) — the retrieved context is the only source of truth, no
outside knowledge, no guessing at steps or numbers that aren't there.

This is a deliberately simplified version of the full answer-generation
prompt for Phase 1. Role-aware tone, RBAC scope enforcement, and the full
rule set (the replica pattern's section 9.3-equivalent) land in Phase 5
per the build roadmap — this only needs to prove grounded, cited answers
work end to end.
"""

import time

from openai import OpenAI

from backend.app.config import settings
from backend.app.monitoring.usage import metered_create
from backend.app.rag.markdown_processor import MarkdownChunk
from backend.app.utils import trace

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


SYSTEM_PROMPT = """You are a SyteLine Prospect-to-Cash assistant. Answer ONLY using the \
Retrieved Context below. Never use outside knowledge, never guess or invent steps, field \
names, or numbers that are not stated in the context.

If the context does not contain the answer, say so plainly rather than guessing.

Keep the answer concise and direct. Answer only what was asked: do not add related topics, \
other modules or extra background the user did not ask about. Use a numbered list for \
step-by-step instructions. Do not mention "the context" or "the documents" out loud — just \
answer naturally, as if you already knew this.

Be polite and professional, like a helpful colleague — never curt or robotic. If the answer \
isn't in the context, say so courteously and suggest what the user could ask instead, rather \
than a flat refusal."""

# Added for simple "what is X?" questions: users want the definition, not everything around it.
BRIEF_INSTRUCTION = (
    "This is a simple definition question. Reply in one or two short sentences (about 40 words at "
    "most): say what it is in SyteLine and, if the context names it, the form where it is kept. No "
    "steps, no lists, no related processes. If the context has no clear definition, say so in one "
    "sentence and name the closest topic you can explain instead."
)


def build_context(chunks: list[MarkdownChunk]) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c.source_file} — {c.full_context_path}]\n{c.text}" for c in chunks
    )


def generate_answer(
    query: str,
    chunks: list[MarkdownChunk],
    avoid_claims: list[str] | None = None,
    tone: str | None = None,
    terminology: str | None = None,
    brief: bool = False,
) -> str:
    """`avoid_claims`: statements the answer validator found unsupported in an earlier draft.
    `tone`: style guidance for the user's mood (quality/tone.py) — never changes the facts.
    `terminology`: the same question in SyteLine terms ("What is SO?" -> "What is a sales order
    (SO)? Customer Order"), so abbreviations and slang are understood; the reply still answers
    the user's own wording.
    `brief`: a simple definition question ("What is a customer?") — answer in one or two sentences."""
    context = build_context(chunks)
    system = SYSTEM_PROMPT
    if brief:
        system += f"\n\nAnswer length: {BRIEF_INSTRUCTION}"
    if tone:
        system += f"\n\nTone for this reply (style only — the rules above still come first): {tone}"
    question = f"Question: {query}"
    if terminology and terminology.strip().casefold() != query.strip().casefold():
        question += f"\n(The same question in SyteLine terms: {terminology})"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Retrieved Context:\n{context}\n\n{question}"},
    ]
    if avoid_claims:
        listed = "\n".join(f"- {claim}" for claim in avoid_claims)
        messages.append({
            "role": "user",
            "content": (
                "A previous draft of this answer included statements that the Retrieved Context does "
                f"not support:\n{listed}\n\nWrite the answer again. Keep everything the context does "
                "support, in the same helpful step-by-step style; only leave out or correct those "
                "statements. You are read-only: never say you changed anything in SyteLine. Say the "
                "context does not cover something only if nothing in it answers the question."
            ),
        })

    started = time.perf_counter()
    response = metered_create("answer_repair" if avoid_claims else "answer", get_client(),
        model=settings.primary_llm,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        messages=messages,
    )
    answer = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    tokens = f" · tokens in {usage.prompt_tokens} / out {usage.completion_tokens}" if usage else ""
    trace.detail(f"    {'re-written without the flagged statements' if avoid_claims else 'written'} by "
                 f"{settings.primary_llm} in {time.perf_counter() - started:.1f}s{tokens} · {len(answer)} chars "
                 f"from {len(context)} chars of evidence")
    trace.detail(f"    draft: {trace.text(answer, 220)}")
    return answer
