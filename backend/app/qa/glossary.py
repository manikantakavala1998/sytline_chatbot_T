"""
Loads data/metadata/business_glossary.csv and uses it to bridge everyday
phrasing ("credit ceiling", "CO") to the formal terms used in the Q&A data
("Credit Limit", "Customer Order") — the "Synonym / Terminology Mapping"
and "Acronym Expansion" steps in the Fast Q&A pipeline (master prompt §9).

(2026-09-29) Also reads the optional "glossary" sheet of every Q&A workbook in
data/qa/prospect_to_cash/ (the data team's template has one per module) and merges
it with the CSV: the same term from several places becomes one entry with all its
synonyms.
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from backend.app.config import BASE_DIR

GLOSSARY_FILE = BASE_DIR / "data" / "metadata" / "business_glossary.csv"
WORKBOOK_ROOT = BASE_DIR / "data" / "qa" / "prospect_to_cash"


@dataclass
class GlossaryEntry:
    canonical_term: str
    synonyms: list[str]
    abbreviation: str


def _entry(row: dict) -> GlossaryEntry | None:
    term = str(row.get("canonical_term") or "").strip()
    if not term or term.lower() == "nan":
        return None
    raw_synonyms = str(row.get("synonyms") or "")
    abbreviation = str(row.get("abbreviation") or "").strip()
    return GlossaryEntry(
        canonical_term=term,
        synonyms=[s.strip() for s in raw_synonyms.split("|") if s.strip() and s.strip().lower() != "nan"],
        abbreviation="" if abbreviation.lower() == "nan" else abbreviation,
    )


def _workbook_rows(root: Path) -> list[dict]:
    if not root.exists():
        return []
    import pandas as pd  # only needed when workbooks exist

    rows: list[dict] = []
    for workbook in sorted(root.glob("*.xlsx")):
        if workbook.name.startswith("~$"):
            continue
        try:
            sheet = pd.read_excel(workbook, sheet_name="glossary", engine="openpyxl", dtype=str)
        except ValueError:
            continue  # no glossary sheet in this workbook
        rows += sheet.fillna("").to_dict("records")
    return rows


def load_glossary(path=GLOSSARY_FILE, workbook_root: Path | None = WORKBOOK_ROOT) -> list[GlossaryEntry]:
    rows: list[dict] = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows += list(csv.DictReader(f))
    if workbook_root is not None:
        rows += _workbook_rows(workbook_root)

    merged: dict[str, GlossaryEntry] = {}
    for row in rows:
        entry = _entry(row)
        if entry is None:
            continue
        existing = merged.get(entry.canonical_term.lower())
        if existing is None:
            merged[entry.canonical_term.lower()] = entry
            continue
        existing.synonyms += [s for s in entry.synonyms if s.lower() not in {x.lower() for x in existing.synonyms}]
        existing.abbreviation = existing.abbreviation or entry.abbreviation
    return list(merged.values())


def _whole_word_present(term: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(term.lower())}\b", text) is not None


def expand_query(query: str, glossary: list[GlossaryEntry]) -> str:
    """
    Returns the query with any recognized synonym/abbreviation's canonical
    term appended, so downstream matching sees the formal vocabulary too.
    The original wording is never removed.
    """
    normalized = query.lower()
    additions: list[str] = []

    for entry in glossary:
        if entry.canonical_term.lower() in normalized:
            continue  # already using the formal term

        candidates = entry.synonyms + ([entry.abbreviation] if entry.abbreviation else [])
        if any(_whole_word_present(c, normalized) for c in candidates if c):
            additions.append(entry.canonical_term)

    if not additions:
        return query
    return f"{query} {' '.join(additions)}"
