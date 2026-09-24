"""
Heading-aware Markdown chunker (master prompt section 14 / replica pattern
section 6.2) — walks a document line by line, not by raw character offset.

Rules:
  - Any heading (ATX "# Foo" or lettered "A. Foo") is a hard chunk boundary,
    EXCEPT a heading whose text is exactly "Keywords" — that one gets
    absorbed into the current chunk instead, so a keyword block stays
    attached to the section it belongs to.
  - A flushed chunk is tagged with the heading hierarchy as it stood BEFORE
    the triggering heading, then the hierarchy updates, then a new chunk
    starts with just the heading line.
  - Long sections (over MARKDOWN_CHUNK_SIZE chars) also split on their own,
    seeding the new piece with the previous chunk's last 3 lines so pieces
    of the same section still read like a continuation.
  - Chunks under MIN_CHUNK_CHARS are dropped — a bare heading with nothing
    under it isn't worth keeping as its own chunk.
"""

import re
from dataclasses import dataclass
from pathlib import Path

MARKDOWN_CHUNK_SIZE = 1200
MIN_CHUNK_CHARS = 20
KEYWORD_LINES_MAX = 4

_ATX_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_LETTERED_HEADER_RE = re.compile(r"^([A-Z])\.\s+(.+)$")


def _match_header(line: str) -> tuple[int, str] | None:
    stripped = line.strip()
    m = _ATX_HEADER_RE.match(stripped)
    if m:
        return len(m.group(1)), m.group(2).strip()
    m = _LETTERED_HEADER_RE.match(stripped)
    if m:
        return 3, m.group(2).strip()
    return None


def _is_keywords_header(header_text: str) -> bool:
    return header_text.strip().lower() == "keywords"


def _full_context_path(level1: str, level2: str, level3: str) -> str:
    parts = [p for p in (level1, level2, level3) if p]
    return " > ".join(parts) if parts else "Content"


def _extract_keywords_after(lines: list[str], header_index: int) -> str:
    collected: list[str] = []
    for line in lines[header_index + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "---" or _match_header(stripped):
            break
        collected.append(stripped)
        if len(collected) >= KEYWORD_LINES_MAX:
            break
    return " ".join(collected)


def _extract_keywords_from_chunk(chunk_lines: list[str]) -> str:
    for idx, line in enumerate(chunk_lines):
        header = _match_header(line)
        if header and _is_keywords_header(header[1]):
            return _extract_keywords_after(chunk_lines, idx)
    return ""


@dataclass
class _RawChunk:
    content: str
    level1: str
    level2: str
    level3: str


def _chunk_raw_text(text: str) -> list[_RawChunk]:
    lines = text.splitlines()
    level1 = level2 = level3 = ""
    buffer: list[str] = []
    chunks: list[_RawChunk] = []

    def buffer_char_count() -> int:
        return sum(len(l) + 1 for l in buffer)

    def flush_if_big_enough():
        content = "\n".join(buffer).strip()
        if len(content) > MIN_CHUNK_CHARS:
            chunks.append(_RawChunk(content=content, level1=level1, level2=level2, level3=level3))

    for line in lines:
        header = _match_header(line)

        if header:
            level, header_text = header
            if _is_keywords_header(header_text):
                buffer.append(line)
                continue

            flush_if_big_enough()
            if level == 1:
                level1, level2, level3 = header_text, "", ""
            elif level == 2:
                level2, level3 = header_text, ""
            else:
                level3 = header_text
            buffer = [line]
            continue

        prospective_length = buffer_char_count() + len(line) + 1
        if buffer and prospective_length > MARKDOWN_CHUNK_SIZE:
            flush_if_big_enough()
            overlap = buffer[-3:] if len(buffer) >= 3 else buffer[:]
            buffer = overlap + [line]
        else:
            buffer.append(line)

    flush_if_big_enough()
    return chunks


@dataclass
class MarkdownChunk:
    chunk_id: str
    document_id: str  # level / filename stem
    text: str  # raw chunk content — this is the context shown to the LLM
    embed_text: str  # synthetic text used only for embedding/search
    level: str
    section_level1: str
    section_level2: str
    section_level3: str
    full_context_path: str
    source_file: str
    chunk_index: int
    total_chunks: int
    keywords: str


def build_chunks(text: str, level: str, source_file: str) -> list[MarkdownChunk]:
    raw_chunks = _chunk_raw_text(text)
    total = len(raw_chunks)

    records: list[MarkdownChunk] = []
    for i, raw in enumerate(raw_chunks):
        chunk_lines = raw.content.splitlines()
        keywords = _extract_keywords_from_chunk(chunk_lines)
        full_path = _full_context_path(raw.level1, raw.level2, raw.level3)

        embed_parts = [full_path]
        if keywords:
            embed_parts.append(keywords)
        embed_parts.append(raw.content[:300])
        embed_text = "\n".join(embed_parts)[:1000]

        records.append(
            MarkdownChunk(
                chunk_id=f"{level}-{i + 1}",
                document_id=level,
                text=raw.content[:5000],
                embed_text=embed_text,
                level=level,
                section_level1=raw.level1[:200],
                section_level2=raw.level2[:200],
                section_level3=raw.level3[:200],
                full_context_path=full_path[:500],
                source_file=source_file,
                chunk_index=i + 1,
                total_chunks=total,
                keywords=keywords,
            )
        )
    return records


def process_markdown_file(path: Path) -> list[MarkdownChunk]:
    text = path.read_text(encoding="utf-8")
    return build_chunks(text, level=path.stem, source_file=path.name)


def process_all_markdown(root: Path) -> list[MarkdownChunk]:
    if not root.exists():
        return []

    chunks: list[MarkdownChunk] = []
    for md_file in sorted(root.glob("*.md")):
        chunks.extend(process_markdown_file(md_file))
    return chunks
