"""Check the data team's knowledge files before they are loaded into the chatbot.

    python -m scripts.validate_knowledge_data <file or folder> [<file or folder> ...]

Checks module Markdown files (*.md) and Excel Q&A workbooks (*.xlsx) against the templates in
documentation/data_templates/. Prints ✅ / ⚠ / ❌ per file and a preview of how each Markdown file
will be split into searchable sections. Exit code 1 if any ❌ error was found, so it can also run in
a pipeline. Nothing is changed and nothing is loaded — it only reads the files.

Errors (❌) would break loading, leak data, or give users wrong answers. Warnings (⚠) are quality
problems worth fixing before go-live.
"""

import re
import sys
from pathlib import Path

import pandas as pd

from backend.app.classification.taxonomy import IntentLabel
from backend.app.rag.markdown_processor import (
    MARKDOWN_CHUNK_SIZE,
    SKIPPED_SECTIONS,
    _match_header,
    _section_name,
    build_chunks,
)

FILE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
PLACEHOLDER = re.compile(r"<(?!!--)[^<>\n]{2,80}>")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
NEEDS_CONFIRMATION = re.compile(r"\[NEEDS[ A-Z]*CONFIRMATION\]", re.IGNORECASE)
class _PhoneNumber:
    """10+ digits written as a phone number — but never a date like 2026-09-29."""

    _candidate = re.compile(r"(?<![\w-])\+?\d[\d\s().-]{8,}\d(?![\w-])")
    _date = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

    def search(self, line: str):
        for match in self._candidate.finditer(self._date.sub(" ", line)):
            if sum(ch.isdigit() for ch in match.group(0)) >= 10:
                return match
        return None


PERSONAL_OR_SECRET = {
    "e-mail address": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "phone number": _PhoneNumber(),
    "password / key": re.compile(r"\b(?:password|passwd|api[_\s-]?key|secret|token)\s*[:=]\s*\S+", re.IGNORECASE),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
}
REQUIRED_METADATA = ["Module", "Tags", "Document Owner", "Reviewed / Approved By", "Last Reviewed", "Version", "Source"]
SECTION_TARGET_CHARS = 1000

QA_COLUMNS = [
    "qa_id", "domain", "process", "module", "form", "field", "intent", "sub_intent", "canonical_question",
    "answer", "keywords", "synonyms", "route", "source_reference", "source_section", "version", "site_scope",
    "security_scope", "approval_status", "approved_by", "effective_date", "active", "last_reviewed_date",
    "language",
]
QA_REQUIRED = ["qa_id", "module", "canonical_question", "answer", "keywords", "intent", "route",
               "source_reference", "approval_status", "active", "language"]
VARIATION_COLUMNS = ["qa_id", "variation_id", "question_variation", "language", "source", "validated"]
GLOSSARY_COLUMNS = ["canonical_term", "synonyms", "abbreviation", "module", "process"]
APPROVAL = {"DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"}
USER_AUTHORIZED_APPROVAL = "User-authorized automatic approval (SME review pending)"
ROUTES = {"FAST_QA", "MARKDOWN_RAG"}
QA_INTENTS = {i.value for i in IntentLabel}
QA_ID = re.compile(r"^[A-Z]{2,5}-\d{3,6}$")
ANSWER_WARN_CHARS = 700
MIN_VARIATIONS = 3
ROW_LABEL = re.compile(r"row (\d+ \([^)]*\)|\d+)")
KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge" / "prospect_to_cash"


class Report:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @staticmethod
    def _grouped(messages: list[str]) -> list[str]:
        """Same problem on many rows -> one line: '8 row(s) (2, 3, 4 …): <problem>'."""
        groups: dict[str, list[str]] = {}
        for message in messages:
            match = ROW_LABEL.search(message)
            key = ROW_LABEL.sub("row …", message) if match else message
            groups.setdefault(key, []).append(match.group(1) if match else "")
        lines = []
        for key, rows in groups.items():
            if len(rows) > 1 and rows[0]:
                shown = ", ".join(rows[:6]) + (" …" if len(rows) > 6 else "")
                lines.append(f"{len(rows)} rows ({shown}): {re.sub(r' ?row …', '', key)}")
            else:
                lines.append(ROW_LABEL.sub(lambda m: f"row {m.group(1)}", key) if not rows[0] else
                             key.replace("row …", f"row {rows[0]}"))
        return lines

    def print(self) -> None:
        status = "❌" if self.errors else ("⚠ " if self.warnings else "✅")
        print(f"\n{status} {self.path}")
        for message in self._grouped(self.errors):
            print(f"   ❌ {message}")
        for message in self._grouped(self.warnings):
            print(f"   ⚠  {message}")
        for message in self.info:
            print(f"   {message}")


def _lines_without_comments(text: str) -> list[tuple[int, str]]:
    """(line number, line) with <!-- comments --> blanked out but line numbers kept."""
    cleaned = COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return list(enumerate(cleaned.splitlines(), 1))


def _check_personal_data(report: Report, numbered_lines, where: str = "") -> None:
    for number, line in numbered_lines:
        for label, pattern in PERSONAL_OR_SECRET.items():
            if pattern.search(line):
                report.error(f"{where}line {number}: looks like a {label} — remove personal data and secrets")


# ── Markdown ───────────────────────────────────────────────────────────


def check_markdown(path: Path) -> Report:
    report = Report(path)
    if not FILE_NAME.match(path.stem):
        report.error(f"file name '{path.name}' — use lower case and underscores, e.g. customer_order.md")
    text = path.read_text(encoding="utf-8")
    lines = _lines_without_comments(text)

    headings = [(n, _match_header(line)) for n, line in lines if _match_header(line)]
    if not any(level == 1 for _, (level, _t) in headings):
        report.error("no '# Title' line at the top")
    if not any(level == 2 for _, (level, _t) in headings):
        report.error("no '## ' sections — the chatbot searches section by section")

    # Metadata
    metadata = {}
    for _, line in lines:
        m = re.match(r"^\s*(?:[-*]\s*)?\*\*(.+?):?\*\*:?\s*(.*)$", line)  # "- **Module:** x" or "**Module:** x"
        if m:
            metadata.setdefault(m.group(1).strip().rstrip(":"), m.group(2).strip())
    for field in REQUIRED_METADATA:
        value = next((v for k, v in metadata.items() if k.lower().startswith(field.lower())), None)
        if not value:
            report.error(f"Document Metadata: '{field}' is missing or empty")
    module = next((v for k, v in metadata.items() if k.lower() == "module"), "")
    if module and module.strip() != path.stem:
        report.warn(f"metadata Module '{module}' differs from the file name '{path.stem}' — keep them the same")

    # Leftovers, markers, personal data
    placeholders = [(n, PLACEHOLDER.search(line).group(0)) for n, line in lines if PLACEHOLDER.search(line)]
    if placeholders:
        first = ", ".join(f"line {n} {p}" for n, p in placeholders[:5])
        report.error(f"{len(placeholders)} template <placeholder>(s) not filled in — e.g. {first}"
                     f"{' …' if len(placeholders) > 5 else ''}")
    for number, line in lines:
        if re.search(r"\bTODO\b|\bTBD\b|lorem ipsum", line, re.IGNORECASE):
            report.error(f"line {number}: unfinished text (TODO / TBD)")
        if "![" in line:
            report.warn(f"line {number}: image — the chatbot reads text only; describe what the screen shows")
    confirmations = [n for n, line in lines if NEEDS_CONFIRMATION.search(line)]
    if confirmations:
        report.warn(f"{len(confirmations)} [NEEDS CONFIRMATION] item(s) still open (lines "
                    f"{', '.join(map(str, confirmations[:10]))}{'…' if len(confirmations) > 10 else ''})")
    _check_personal_data(report, lines)

    # Sections: one topic, summary, keywords, size
    seen: dict[str, int] = {}
    sections: list[tuple[int, str, list[str]]] = []
    current = None
    for number, line in lines:
        header = _match_header(line)
        if header and header[0] <= 2:
            current = (number, header[1], [])
            sections.append(current)
        elif current:
            current[2].append(line)
    for number, title, body in sections:
        if any(n == number and level == 1 for n, (level, _t) in headings):
            continue  # the "# Title" line isn't a searchable section
        name = _section_name(title)
        if name in SKIPPED_SECTIONS or name == "keywords":
            continue
        key = name.lower()
        if key in seen:
            report.warn(f"line {number}: section '{title}' appears twice (also line {seen[key]}) — merge them")
        seen[key] = number
        body_text = "\n".join(body)
        if not re.search(r"\*\*Section Summary:?\*\*", body_text):
            report.warn(f"line {number}: section '{title}' has no **Section Summary:**")
        if not re.search(r"\*\*Keywords:?\*\*|^#{1,6}\s+Keywords\s*$", body_text, re.MULTILINE | re.IGNORECASE):
            report.warn(f"line {number}: section '{title}' has no **Keywords:** — users' words help find it")
        size = len(body_text.strip())
        if size > MARKDOWN_CHUNK_SIZE:
            report.warn(f"line {number}: section '{title}' is {size} characters — it will be split; aim for "
                        f"under {SECTION_TARGET_CHARS} (one topic per section)")
        if 0 < size < 60:
            report.warn(f"line {number}: section '{title}' is almost empty ({size} characters)")

    # Preview: exactly what the chatbot will index
    chunks = build_chunks(text, level=path.stem, source_file=path.name)
    report.info.append(f"→ will be indexed as {len(chunks)} searchable section(s):")
    for chunk in chunks:
        label = chunk.full_context_path.split(" > ", 1)[-1]
        report.info.append(f"     {chunk.chunk_index:>2}. {label[:70]:<70} {len(chunk.text):>5} chars · "
                           f"keywords: {'yes' if chunk.keywords else 'NO'}")
    return report


# ── Excel ──────────────────────────────────────────────────────────────


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or not str(value).strip()


def check_excel(path: Path) -> Report:
    report = Report(path)
    if not FILE_NAME.match(path.stem):
        report.error(f"file name '{path.name}' — use lower case and underscores, e.g. customer_order.xlsx")
    try:
        book = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:
        report.error(f"can't open the workbook: {exc}")
        return report
    for sheet in ("qa_master", "question_variations"):
        if sheet not in book.sheet_names:
            report.error(f"sheet '{sheet}' is missing (exact name, lower case)")
    if report.errors:
        return report

    qa = book.parse("qa_master")
    missing = [c for c in QA_COLUMNS if c not in qa.columns]
    if missing:
        report.error(f"qa_master: missing column(s) {', '.join(missing)} — don't rename or delete columns")
        return report
    qa = qa.dropna(how="all")
    ids = qa["qa_id"].astype(str).str.strip()
    for dup in sorted(set(ids[ids.duplicated()])):
        report.error(f"qa_master: qa_id {dup} is used more than once")

    usable = 0
    user_authorized = 0
    for index, row in qa.iterrows():
        where = f"qa_master row {index + 2} ({row['qa_id']})"
        for column in QA_REQUIRED:
            if _blank(row[column]):
                report.error(f"{where}: '{column}' is empty")
        qa_id = str(row["qa_id"]).strip()
        if qa_id and not QA_ID.match(qa_id):
            report.warn(f"{where}: qa_id should look like KB-0001 (prefix, dash, number)")
        status = str(row["approval_status"]).strip().upper()
        if status not in APPROVAL:
            report.error(f"{where}: approval_status '{row['approval_status']}' — use {', '.join(sorted(APPROVAL))}")
        if str(row["route"]).strip() not in ROUTES:
            report.error(f"{where}: route '{row['route']}' — use FAST_QA or MARKDOWN_RAG")
        if str(row["intent"]).strip() not in QA_INTENTS:
            report.error(f"{where}: intent '{row['intent']}' is not a known value (see allowed_values sheet)")
        if str(row["active"]).strip().upper() not in {"TRUE", "FALSE", "1", "0"}:
            report.error(f"{where}: active must be TRUE or FALSE")
        if str(row["module"]).strip() != path.stem:
            report.warn(f"{where}: module '{row['module']}' differs from the file name '{path.stem}'")
        if status == "APPROVED":
            reviewer = str(row["approved_by"]) if not _blank(row["approved_by"]) else ""
            if reviewer == USER_AUTHORIZED_APPROVAL:
                user_authorized += 1
            elif not reviewer or "pending" in reviewer.lower() or "auto" in reviewer.lower():
                report.error(f"{where}: APPROVED but approved_by is '{reviewer or 'empty'}' — a real reviewer "
                             "name is required")
            if _blank(row["effective_date"]):
                report.warn(f"{where}: APPROVED without an effective_date")
            if str(row["active"]).strip().upper() in {"TRUE", "1"}:
                usable += 1
        answer = "" if _blank(row["answer"]) else str(row["answer"])
        if len(answer) > ANSWER_WARN_CHARS:
            report.warn(f"{where}: answer is {len(answer)} characters — keep approved answers short (1–4 sentences "
                        "or a few steps); put long procedures in the Markdown file")
        question = "" if _blank(row["canonical_question"]) else str(row["canonical_question"]).strip()
        if question and not question.endswith("?"):
            report.warn(f"{where}: canonical_question should be a question ending with '?'")
        source = "" if _blank(row["source_reference"]) else str(row["source_reference"]).strip()
        if source == "PTC Training Guide":
            report.error(f"{where}: source_reference 'PTC Training Guide' is a placeholder and is ignored by the chatbot")
        elif source.endswith(".md") and not ((path.parent / source).exists() or (KNOWLEDGE_ROOT / source).exists()):
            report.warn(f"{where}: source_reference '{source}' not found (next to this workbook or in "
                        "data/knowledge/prospect_to_cash) — check the file name")
        _check_personal_data(report, [(index + 2, answer)], where="qa_master answer ")

    # Variations
    variations = book.parse("question_variations").dropna(how="all")
    missing = [c for c in VARIATION_COLUMNS if c not in variations.columns]
    if missing:
        report.error(f"question_variations: missing column(s) {', '.join(missing)}")
    else:
        known = set(ids)
        counts = variations["qa_id"].astype(str).str.strip().value_counts()
        for index, row in variations.iterrows():
            if str(row["qa_id"]).strip() not in known:
                report.error(f"question_variations row {index + 2}: qa_id {row['qa_id']} is not in qa_master")
            if _blank(row["question_variation"]):
                report.error(f"question_variations row {index + 2}: question_variation is empty")
        for qa_id in ids:
            if counts.get(qa_id, 0) < MIN_VARIATIONS:
                report.warn(f"{qa_id}: only {counts.get(qa_id, 0)} variation(s) — add at least {MIN_VARIATIONS} "
                            "in users' own words")
        pairs = variations.assign(v=variations["question_variation"].astype(str).str.strip().str.lower())
        for (qa_id, text), group in pairs.groupby(["qa_id", "v"]):
            if len(group) > 1:
                report.warn(f"{qa_id}: variation '{text}' is listed {len(group)} times")

    # Glossary (optional sheet in the template)
    if "glossary" in book.sheet_names:
        glossary = book.parse("glossary").dropna(how="all")
        missing = [c for c in GLOSSARY_COLUMNS if c not in glossary.columns]
        if missing:
            report.error(f"glossary: missing column(s) {', '.join(missing)}")
        else:
            for index, row in glossary.iterrows():
                if _blank(row["canonical_term"]):
                    report.error(f"glossary row {index + 2}: canonical_term is empty")
                synonyms = "" if _blank(row["synonyms"]) else str(row["synonyms"])
                if "," in synonyms and "|" not in synonyms:
                    report.warn(f"glossary row {index + 2}: separate synonyms with | not commas")
            report.info.append(f"→ glossary: {len(glossary)} term(s)")

    if user_authorized:
        report.warn(f"{user_authorized} APPROVED row(s) were activated by user request, not SyteLine SME review; "
                    "verify against the deployed version and site before production reliance")
    report.info.append(f"→ {len(qa)} Q&A row(s): {usable} will be used (APPROVED + active); "
                       f"{len(variations)} variation(s)")
    return report


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    files: list[Path] = []
    for arg in argv:
        path = Path(arg)
        if path.is_dir():
            files += sorted(p for p in path.iterdir() if p.suffix.lower() in {".md", ".xlsx"}
                            and not p.name.startswith("~$"))
        elif path.exists():
            files.append(path)
        else:
            print(f"❌ not found: {arg}")
            return 2
    reports = [check_markdown(p) if p.suffix.lower() == ".md" else check_excel(p) for p in files]
    for report in reports:
        report.print()
    errors = sum(len(r.errors) for r in reports)
    warnings = sum(len(r.warnings) for r in reports)
    print(f"\n{len(reports)} file(s) checked · {errors} error(s) · {warnings} warning(s) — "
          + ("fix the ❌ errors before sending." if errors else "ready to send (review the ⚠ warnings)."))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
