"""Markdown chunking for the data team's template (HRMS-style documents) — no services needed."""

from backend.app.rag.markdown_processor import build_chunks, document_tags

DOC = """# Credit Hold – Process Document

## Document Metadata
- **Document Title:** Credit Hold
- **Module:** Credit
- **Tags:** credit hold, blocked order
- **Access Level:** AR Clerk, Credit Manager

---

## Table of Contents
1. Purpose
2. Release a credit hold

---

## 1. Purpose
Explains how a credit hold stops shipping and who can release it.

**Section Summary:** Why credit holds exist.

**Keywords:** purpose, credit hold

---

## 2. Release a credit hold
1. Open the Customer Orders form.
2. Clear the Credit Hold check box and save.

**Section Summary:** Steps to release an order credit hold.

### Keywords
release hold, unblock order

## Change History
| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-29 | First version |
"""


def _chunks():
    return build_chunks(DOC, level="credit", source_file="credit.md")


def test_people_only_sections_are_not_indexed():
    texts = " ".join(c.text for c in _chunks())
    assert "Document Title" not in texts
    assert "Table of Contents" not in texts
    assert "First version" not in texts


def test_title_only_chunk_is_dropped():
    assert all(not c.text.startswith("# Credit Hold – Process Document\n") or "\n" in c.text.strip()
               for c in _chunks())
    assert [c.section_level2 for c in _chunks()] == ["1. Purpose", "2. Release a credit hold"]


def test_inline_and_heading_keywords_both_work_and_tags_are_added():
    purpose, release = _chunks()
    assert purpose.keywords.startswith("purpose, credit hold")
    assert release.keywords.startswith("release hold, unblock order")
    assert "blocked order" in purpose.keywords and "blocked order" in release.keywords


def test_tags_are_read_from_metadata():
    assert document_tags(DOC) == "credit hold, blocked order"


def test_writer_guidance_comments_are_not_indexed():
    doc = DOC.replace("Explains how", "<!-- WRITER NOTE: keep this short -->\nExplains how")
    doc = doc.replace("## 2. Release", "<!--\nmulti-line\nnote\n-->\n## 2. Release")
    texts = " ".join(c.text for c in build_chunks(doc, level="credit", source_file="credit.md"))
    assert "WRITER NOTE" not in texts and "multi-line" not in texts


TABLE_DOC = """# Credit

## Key Fields

| Field | Form | Meaning |
|---|---|---|
| Credit Limit | Customers | Maximum the customer may owe |
| Credit Hold Reason | Customer Orders | Why the order is held |
| Allow Over Credit Limit | Customer Order Lines | Lets a line stay Ordered over the limit |

**Section Summary:** Meaning of credit fields.

**Keywords:** credit fields
"""


def test_table_rows_become_labelled_sentences():
    chunk = build_chunks(TABLE_DOC, level="credit", source_file="credit.md")[0]
    assert chunk.row_texts == [
        "Field: Credit Limit · Form: Customers · Meaning: Maximum the customer may owe",
        "Field: Credit Hold Reason · Form: Customer Orders · Meaning: Why the order is held",
        "Field: Allow Over Credit Limit · Form: Customer Order Lines · Meaning: Lets a line stay Ordered over the limit",
    ]
    assert "|" not in chunk.search_text  # search reads sentences, not pipes
    assert "|" in chunk.text  # the answer model still gets the real table


def test_every_row_is_visible_to_search_even_after_300_characters():
    """Rows past the first 300 characters used to be invisible to search. Now every row has its
    own vector (row_texts) and the section vector reads up to 1,500 characters."""
    long_doc = TABLE_DOC.replace("| Allow Over", "| Filler A | X | " + "y" * 300 + " |\n| Allow Over")
    chunk = build_chunks(long_doc, level="credit", source_file="credit.md")[0]
    assert any("Allow Over Credit Limit" in row for row in chunk.row_texts)
    assert "Allow Over Credit Limit" in chunk.embed_text


def test_keyword_text_stays_short():
    """Indexing whole sections for keyword search was measured to hurt ranking (see search_text)."""
    long_doc = TABLE_DOC.replace("| Allow Over", "| Filler A | X | " + "y" * 900 + " |\n| Allow Over")
    chunk = build_chunks(long_doc, level="credit", source_file="credit.md")[0]
    assert len(chunk.search_text) < 500


def test_header_and_separator_rows_are_not_facts():
    chunk = build_chunks(TABLE_DOC, level="credit", source_file="credit.md")[0]
    assert not any(r.startswith("Field: Field") or "---" in r for r in chunk.row_texts)


def test_section_path_keeps_the_title():
    assert _chunks()[1].full_context_path == "Credit Hold – Process Document > 2. Release a credit hold"
