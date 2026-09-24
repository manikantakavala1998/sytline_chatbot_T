"""
Reads the Q&A Excel files from data/qa/prospect_to_cash/<level>.xlsx — one
flat file per Prospect-to-Cash stage (prospect.xlsx, lead.xlsx,
opportunity.xlsx, ...), named to match the level folders the Markdown
knowledge base uses later (master prompt section 13).

Only rows marked approval_status == "APPROVED" and active == True are kept
— per the master prompt: "Only APPROVED + ACTIVE records may be used in
production." Question variations get attached to their parent row so the
retriever can match against all the different ways someone might ask the
same thing.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from backend.app.config import BASE_DIR
from backend.app.utils.logger import get_logger

QA_ROOT = BASE_DIR / "data" / "qa" / "prospect_to_cash"

logger = get_logger(__name__)


@dataclass
class QARecord:
    qa_id: str
    canonical_question: str
    answer: str
    module: str
    form: str
    process: str
    keywords: str
    route: str
    level: str  # which data/qa/prospect_to_cash/<level>/ folder this came from
    match_texts: list[str] = field(default_factory=list)  # canonical question + all variations


def _load_one_file(path: Path, level: str) -> list[QARecord]:
    qa_df = pd.read_excel(path, sheet_name="qa_master", engine="openpyxl")
    try:
        variations_df = pd.read_excel(path, sheet_name="question_variations", engine="openpyxl")
    except ValueError:
        variations_df = pd.DataFrame(columns=["qa_id", "question_variation"])

    qa_df = qa_df[
        (qa_df["approval_status"].astype(str).str.upper() == "APPROVED")
        & (qa_df["active"].astype(bool))
    ]

    variations_by_qa_id: dict[str, list[str]] = {}
    for _, row in variations_df.iterrows():
        variations_by_qa_id.setdefault(str(row["qa_id"]), []).append(str(row["question_variation"]))

    records: list[QARecord] = []
    for _, row in qa_df.iterrows():
        qa_id = str(row["qa_id"])
        canonical_question = str(row["canonical_question"]).strip()
        match_texts = [canonical_question] + variations_by_qa_id.get(qa_id, [])
        records.append(
            QARecord(
                qa_id=qa_id,
                canonical_question=canonical_question,
                answer=str(row["answer"]).strip(),
                module=str(row.get("module", "")),
                form=str(row.get("form", "")),
                process=str(row.get("process", "")),
                keywords=str(row.get("keywords", "")),
                route=str(row.get("route", "FAST_QA")),
                level=level,
                match_texts=match_texts,
            )
        )
    return records


def load_qa_records(root: Path = QA_ROOT) -> list[QARecord]:
    if not root.exists():
        logger.info("Q&A folder %s does not exist yet — skipping Fast Q&A ingestion", root)
        return []

    records: list[QARecord] = []
    files = sorted(root.glob("*.xlsx"))
    logger.info("Ingesting Fast Q&A: found %d level file(s) in %s", len(files), root)
    for qa_file in files:
        level = qa_file.stem
        level_records = _load_one_file(qa_file, level)
        logger.info("  %-24s -> %d approved+active row(s)", qa_file.name, len(level_records))
        records.extend(level_records)
    logger.info("Fast Q&A ingestion complete: %d total records", len(records))
    return records
