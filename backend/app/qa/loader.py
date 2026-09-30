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

The generated starter workbooks used a placeholder "PTC Training Guide"
source and incorrectly marked their sample rows APPROVED. Exclude those
rows until a real source and business approval replace them.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from backend.app.config import BASE_DIR
from backend.app.utils import trace
from backend.app.utils.logger import get_logger, log_event

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


def _load_one_file(path: Path, level: str) -> tuple[list[QARecord], dict[str, int]]:
    """Returns the usable records and why the other rows were skipped (for the startup trace)."""
    qa_df = pd.read_excel(path, sheet_name="qa_master", engine="openpyxl")
    try:
        variations_df = pd.read_excel(path, sheet_name="question_variations", engine="openpyxl")
    except ValueError:
        variations_df = pd.DataFrame(columns=["qa_id", "question_variation"])

    approved = qa_df["approval_status"].astype(str).str.upper() == "APPROVED"
    active = qa_df["active"].astype(bool)
    real_source = qa_df["source_reference"].astype(str).str.strip() != "PTC Training Guide"
    skipped = {
        "not approved": int((~approved).sum()),
        "inactive": int((approved & ~active).sum()),
        "placeholder source": int((approved & active & ~real_source).sum()),
    }
    qa_df = qa_df[approved & active & real_source]

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
    return records, skipped


# Both indexes (Fast Q&A and the unified Excel + Markdown index) read the same workbooks at
# startup; read them once.
_cache: dict[Path, list[QARecord]] = {}


def load_qa_records(root: Path = QA_ROOT) -> list[QARecord]:
    if root in _cache:
        return _cache[root]
    if not root.exists():
        trace.startup("Excel Q&A", f"folder {root} not found — no curated answers")
        return []

    records: list[QARecord] = []
    files = sorted(root.glob("*.xlsx"))
    shown = root.relative_to(BASE_DIR) if root.is_relative_to(BASE_DIR) else root
    trace.startup("Excel Q&A (curated answers)", f"{len(files)} workbook(s) in {shown}")
    for qa_file in files:
        level_records, skipped = _load_one_file(qa_file, qa_file.stem)
        wordings = sum(len(r.match_texts) for r in level_records)
        reasons = ", ".join(f"{n} {why}" for why, n in skipped.items() if n)
        trace.startup_detail(
            f"{qa_file.name:<30} {len(level_records):>3} row(s) used · {wordings:>3} question wording(s)"
            + (f" · skipped: {reasons}" if reasons else "")
        )
        records.extend(level_records)
    trace.startup("Excel Q&A loaded", f"{len(records)} approved + active row(s)")
    log_event(logger, "qa_ingestion_complete", files=len(files), records=len(records))
    _cache[root] = records
    return records
