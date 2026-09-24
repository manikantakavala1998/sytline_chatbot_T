"""
Loads data/metadata/business_glossary.csv and uses it to bridge everyday
phrasing ("credit ceiling", "CO") to the formal terms used in the Q&A data
("Credit Limit", "Customer Order") — the "Synonym / Terminology Mapping"
and "Acronym Expansion" steps in the Fast Q&A pipeline (master prompt §9).
"""

import csv
import re
from dataclasses import dataclass

from backend.app.config import BASE_DIR

GLOSSARY_FILE = BASE_DIR / "data" / "metadata" / "business_glossary.csv"


@dataclass
class GlossaryEntry:
    canonical_term: str
    synonyms: list[str]
    abbreviation: str


def load_glossary(path=GLOSSARY_FILE) -> list[GlossaryEntry]:
    if not path.exists():
        return []

    entries: list[GlossaryEntry] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            synonyms = [s.strip() for s in (row.get("synonyms") or "").split("|") if s.strip()]
            entries.append(
                GlossaryEntry(
                    canonical_term=row["canonical_term"].strip(),
                    synonyms=synonyms,
                    abbreviation=(row.get("abbreviation") or "").strip(),
                )
            )
    return entries


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
