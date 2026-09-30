"""Convert a module document written in Word (from SyteLine_Module_Knowledge_Template.docx) into
the Markdown file the chatbot loads.

    python -m scripts.convert_docx_to_md <file.docx> [<output.md>]

Word → Markdown:
  Title / Heading 1 / 2 / 3       →  # / ## / ###   (each ## becomes one searchable section)
  "List Number" / "List Bullet"   →  1. 2. 3. / *   (numbering restarts after any other paragraph)
  a paragraph starting with a bold "Label:"  →  **Label:** text   (Section Summary, Keywords, Path…)
  tables                          →  Markdown tables (first row = header)
  grey italic "Note: …" / "HOW TO USE" paragraphs (writer guidance)  →  left out
  a horizontal rule is added before every ## section, like the Markdown template

The output is named after the module (lower case, underscores) unless an output path is given.
Run the checker afterwards: python -m scripts.validate_knowledge_data <output.md>
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

WRITER_NOTE = re.compile(r"^\s*(Note:|HOW TO USE:)", re.IGNORECASE)


def _iter_blocks(document):
    """Paragraphs and tables in document order."""
    body = document.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _table_md(table: Table) -> list[str]:
    rows = [[_cell(c.text) for c in row.cells] for row in table.rows]
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return lines


def _paragraph_md(paragraph: Paragraph) -> str:
    """Inline text with a leading bold 'Label:' kept as **Label:**; other bold kept too."""
    parts = []
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
        parts.append(f"**{text.strip()}** " if run.bold and text.strip() else text)
    line = "".join(parts).strip()
    line = re.sub(r"\*\*\s*\*\*", "", line)  # adjoining bold runs
    line = re.sub(r"\s{2,}", " ", line)
    # "**Label:** value" — make sure the colon sits inside the bold, as the loader expects.
    line = re.sub(r"^\*\*(.+?)\*\*\s*:\s*", r"**\1:** ", line)
    return line


TYPED_NUMBER = re.compile(r"^(\d+)[.)]\s+(.*)$", re.DOTALL)


def _numbering_formats(document) -> dict[str, str]:
    """numId -> 'decimal' / 'bullet' / … for lists made with Word's Numbering / Bullets buttons."""
    try:
        numbering = document.part.numbering_part.element
    except Exception:  # document without any list
        return {}
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    abstract = {}
    for node in numbering.findall("w:abstractNum", ns):
        fmt = node.find("w:lvl/w:numFmt", ns)
        abstract[node.get(f"{{{ns['w']}}}abstractNumId")] = fmt.get(f"{{{ns['w']}}}val") if fmt is not None else ""
    formats = {}
    for node in numbering.findall("w:num", ns):
        ref = node.find("w:abstractNumId", ns)
        if ref is not None:
            formats[node.get(f"{{{ns['w']}}}numId")] = abstract.get(ref.get(f"{{{ns['w']}}}val"), "")
    return formats


def _list_kind(paragraph: Paragraph, formats: dict[str, str]) -> str | None:
    """'number', 'bullet' or None — from the list style or Word's own list buttons."""
    style = (paragraph.style.name if paragraph.style is not None else "").lower()
    if "list number" in style:
        return "number"
    if "list bullet" in style:
        return "bullet"
    num_pr = paragraph._p.pPr.numPr if paragraph._p.pPr is not None else None
    if num_pr is not None and num_pr.numId is not None:
        fmt = formats.get(str(num_pr.numId.val), "")
        return "bullet" if fmt in ("bullet", "none", "") else "number"
    return None


def _is_writer_note(paragraph: Paragraph) -> bool:
    text = paragraph.text.strip()
    if not text:
        return False
    if WRITER_NOTE.match(text):
        return True
    runs = [r for r in paragraph.runs if r.text.strip()]
    return bool(runs) and all(r.italic for r in runs) and text.lower().startswith("note")


def convert(docx_path: Path) -> str:
    document = Document(str(docx_path))
    formats = _numbering_formats(document)
    out: list[str] = []
    number = 0

    def blank():
        if out and out[-1] != "":
            out.append("")

    for block in _iter_blocks(document):
        if isinstance(block, Table):
            number = 0
            blank()
            out.extend(_table_md(block))
            out.append("")
            continue
        paragraph = block
        if _is_writer_note(paragraph):
            continue
        text = paragraph.text.strip()
        style = (paragraph.style.name if paragraph.style is not None else "").lower()
        if not text:
            continue
        heading = re.match(r"heading (\d)", style)
        if style == "title" or heading:
            number = 0
            level = 1 if style == "title" else min(int(heading.group(1)), 3)
            blank()
            if level == 2 and out:
                out += ["---", ""]
            out += [f"{'#' * level} {text}", ""]
            continue
        kind = _list_kind(paragraph, formats)
        typed = TYPED_NUMBER.match(text)
        if kind == "number" or (kind is None and typed):
            number += 1
            body = _paragraph_md(paragraph)
            if typed:  # "3.<tab>Click Save" typed by hand — drop the typed number, keep ours
                body = TYPED_NUMBER.sub(r"\2", body).strip()
            out.append(f"{number}. {body}")
            continue
        number = 0
        if kind == "bullet" or "list paragraph" in style:
            out.append(f"* {_paragraph_md(paragraph)}")
            continue
        blank()
        out += [_paragraph_md(paragraph), ""]

    markdown = "\n".join(out).strip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", markdown)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    source = Path(argv[0])
    if not source.exists() or source.suffix.lower() != ".docx":
        print(f"❌ not a .docx file: {source}")
        return 2
    target = Path(argv[1]) if len(argv) > 1 else source.with_name(
        re.sub(r"[^a-z0-9]+", "_", source.stem.lower()).strip("_") + ".md")
    target.write_text(convert(source), encoding="utf-8")
    print(f"✅ {source.name} → {target}")
    print(f"   next: python -m scripts.validate_knowledge_data {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
