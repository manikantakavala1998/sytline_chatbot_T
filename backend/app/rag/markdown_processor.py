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
  - (2026-09-29, data-team template) Keywords may also be written inline as
    "**Keywords:** a, b, c" (the HRMS document style), not only under a "### Keywords"
    heading. "Document Metadata", "Table of Contents" and "Change History" sections are for
    people and are NOT indexed (they only add noise to search); the metadata's **Tags:** are
    added to every chunk's keywords instead.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.utils import trace
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

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


# "**Keywords:** a, b" / "**Keywords**: a, b" / "Keywords: a, b"
_INLINE_KEYWORDS_RE = re.compile(r"^\s*(?:\*\*)?keywords\s*(?::\s*\*\*|\*\*\s*:|:)\s*(.+)$", re.IGNORECASE)
# Metadata line "- **Tags:** a, b" — tags go into every chunk's keywords.
_TAGS_RE = re.compile(r"^\s*[-*]?\s*\*\*tags:?\*\*:?\s*(.+)$", re.IGNORECASE)
# Sections written for people, not for search.
SKIPPED_SECTIONS = {"document metadata", "metadata", "table of contents", "contents", "change history",
                    "revision history", "document history", "version history"}
_NUMBERING_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")


def _section_name(header_text: str) -> str:
    """'5. Mark Attendance' -> 'mark attendance' (for the skip list)."""
    return _NUMBERING_RE.sub("", header_text).strip().strip("*").strip().lower()


def _extract_keywords_from_chunk(chunk_lines: list[str]) -> str:
    for idx, line in enumerate(chunk_lines):
        header = _match_header(line)
        if header and _is_keywords_header(header[1]):
            return _extract_keywords_after(chunk_lines, idx)
        inline = _INLINE_KEYWORDS_RE.match(line)
        if inline:
            return inline.group(1).strip().rstrip(".")
    return ""


def document_tags(text: str) -> str:
    """The **Tags:** line of the Document Metadata section, if the file has one."""
    for line in text.splitlines():
        match = _TAGS_RE.match(line)
        if match:
            return match.group(1).strip().rstrip(".")
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
    skipping_level: int | None = None  # inside a people-only section (metadata, contents, history)

    def buffer_char_count() -> int:
        return sum(len(l) + 1 for l in buffer)

    def flush_if_big_enough():
        content = "\n".join(buffer).strip()
        # A heading with no body (e.g. the "# Module title" line right before the first "##")
        # has nothing to answer from; 14 such chunks were taking search-candidate slots.
        headings_only = all(_match_header(l) for l in buffer if l.strip() and l.strip() != "---")
        if len(content) > MIN_CHUNK_CHARS and not headings_only:
            chunks.append(_RawChunk(content=content, level1=level1, level2=level2, level3=level3))

    for line in lines:
        header = _match_header(line)

        if header:
            level, header_text = header
            if _is_keywords_header(header_text):
                if skipping_level is None:
                    buffer.append(line)
                continue

            if skipping_level is not None and level > skipping_level:
                continue  # a sub-heading inside a skipped section
            skipping_level = None
            flush_if_big_enough()
            buffer = []
            if level >= 2 and _section_name(header_text) in SKIPPED_SECTIONS:
                skipping_level = level
                continue
            if level == 1:
                level1, level2, level3 = header_text, "", ""
            elif level == 2:
                level2, level3 = header_text, ""
            else:
                level3 = header_text
            buffer = [line]
            continue

        if skipping_level is not None:
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
    # (2026-09-29) Text for keyword (BM25) search: heading path + keywords + the section's opening,
    # as before. Table rows are found by their own row vectors instead. Both "index the whole
    # section" and "add every row label" were measured to HURT keyword ranking: sections that
    # repeat "customer order" / "Ship Date" pushed shipment.md from rank 5 to 51 (whole section)
    # or 12 (row labels) for "how to ship an order".
    search_text: str = ""
    # One sentence per table row ("Field: Credit Limit · Form: Customers · Meaning: …"); each gets
    # its own vector pointing back to this chunk, so a question about one row finds the section.
    row_texts: list[str] = field(default_factory=list)


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")
EMBED_TEXT_CHARS = 1500  # bge-base reads up to 512 tokens ≈ 2,000 characters
SEARCH_EXCERPT_CHARS = 300  # keyword search reads the section's opening; rows have their own vectors


def _cells(line: str) -> list[str]:
    return [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]


def linearize_tables(text: str) -> tuple[str, list[str]]:
    """Markdown tables → one sentence per row, labelled with the column headers.

    | Field | Meaning |            Field: Credit Limit · Meaning: Maximum the customer may owe
    |---|---|             →
    | Credit Limit | Maximum… |

    Returns the text with every table replaced by its sentences, and the list of row sentences.
    Embedding models read "Field: X · Meaning: Y" far better than a row of | pipes.
    """
    out: list[str] = []
    rows: list[str] = []
    header: list[str] | None = None
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        is_row = stripped.startswith("|") and stripped.count("|") >= 2
        if not is_row:
            header = None
            out.append(line)
            continue
        if _TABLE_SEPARATOR_RE.match(stripped):
            continue
        cells = _cells(stripped)
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if header is None and _TABLE_SEPARATOR_RE.match(next_line):
            header = cells  # the header row itself isn't a fact
            continue
        if header:
            pairs = [f"{h}: {v}" for h, v in zip(header, cells) if v and v not in {"-", "—"}]
            sentence = " · ".join(pairs)
        else:
            sentence = " · ".join(c for c in cells if c)
        if sentence:
            rows.append(sentence)
            out.append(sentence)
    return "\n".join(out), rows


def build_chunks(text: str, level: str, source_file: str) -> list[MarkdownChunk]:
    # <!-- guidance notes --> in the data-team template are for writers, never for search.
    text = _HTML_COMMENT_RE.sub("", text)
    raw_chunks = _chunk_raw_text(text)
    total = len(raw_chunks)
    tags = document_tags(text)

    records: list[MarkdownChunk] = []
    for i, raw in enumerate(raw_chunks):
        chunk_lines = raw.content.splitlines()
        keywords = ", ".join(k for k in (_extract_keywords_from_chunk(chunk_lines), tags) if k)
        full_path = _full_context_path(raw.level1, raw.level2, raw.level3)

        readable, row_texts = linearize_tables(raw.content)
        embed_parts = [full_path]
        if keywords:
            embed_parts.append(keywords)
        embed_parts.append(readable)
        embed_text = "\n".join(embed_parts)[:EMBED_TEXT_CHARS]

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
                search_text="\n".join(p for p in (full_path, keywords, readable[:SEARCH_EXCERPT_CHARS]) if p),
                row_texts=row_texts,
            )
        )
    return records


def process_markdown_file(path: Path) -> list[MarkdownChunk]:
    text = path.read_text(encoding="utf-8")
    return build_chunks(text, level=path.stem, source_file=path.name)


def process_all_markdown(root: Path) -> list[MarkdownChunk]:
    if not root.exists():
        trace.startup("Markdown documents", f"folder {root} not found — no documents")
        return []

    files = sorted(root.glob("*.md"))
    trace.startup("Markdown documents", f"{len(files)} file(s) in {root.name}/ — split into sections (chunks)")

    chunks: list[MarkdownChunk] = []
    for md_file in files:
        file_chunks = process_markdown_file(md_file)
        largest = max((len(c.text) for c in file_chunks), default=0)
        trace.startup_detail(f"{md_file.name:<34} {len(file_chunks):>3} chunk(s) · largest {largest:>5} chars")
        chunks.extend(file_chunks)

    trace.startup("Markdown chunked", f"{len(chunks)} chunk(s) from {len(files)} file(s)")
    log_event(logger, "markdown_ingestion_complete", files=len(files), chunks=len(chunks))
    return chunks
