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

from openai import OpenAI

from backend.app.config import settings
from backend.app.rag.markdown_processor import MarkdownChunk

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

Keep the answer concise and direct. Use a numbered list for step-by-step instructions. \
Do not mention "the context" or "the documents" out loud — just answer naturally, as if you \
already knew this.

Be polite and professional, like a helpful colleague — never curt or robotic. If the answer \
isn't in the context, say so courteously and suggest what the user could ask instead, rather \
than a flat refusal."""


def build_context(chunks: list[MarkdownChunk]) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {c.source_file} — {c.full_context_path}]\n{c.text}" for c in chunks
    )


def generate_answer(query: str, chunks: list[MarkdownChunk]) -> str:
    context = build_context(chunks)

    response = get_client().chat.completions.create(
        model=settings.primary_llm,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Retrieved Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    return (response.choices[0].message.content or "").strip()
