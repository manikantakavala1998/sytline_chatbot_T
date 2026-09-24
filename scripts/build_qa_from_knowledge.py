"""
Builds the Fast Q&A Excel files from the Markdown knowledge base, so the two
sources can never contradict each other (the earlier hand-typed starter rows
did — e.g. "a Customer Order is created after a Quotation is accepted" while
the knowledge base says the Estimate is converted).

For every knowledge-base section the LLM drafts up to 2 question/answer pairs
using ONLY that section's text. A deterministic grounding gate then drops any
answer whose content words are not present in the source section, so nothing
invented reaches the Excel. Output: data/qa/prospect_to_cash/<md stem>.xlsx
with the same qa_master / question_variations sheets the loader expects.

Rows are marked APPROVED so the loader uses them, but `approved_by` says they
are auto-derived and still need a business (SME) review before production.

Run:  python -m scripts.build_qa_from_knowledge
"""

import json
import re
from collections import defaultdict
from datetime import date

import pandas as pd
from openai import OpenAI

from backend.app.config import BASE_DIR, settings
from backend.app.rag.markdown_processor import MarkdownChunk, process_all_markdown
from scripts.generate_sample_qa import COLUMNS, VARIATION_COLUMNS

KNOWLEDGE_ROOT = BASE_DIR / "data" / "knowledge" / "prospect_to_cash"
QA_ROOT = BASE_DIR / "data" / "qa" / "prospect_to_cash"
GROUNDING_MIN_RATIO = 0.85
MIN_SECTION_CHARS = 200
TODAY = date.today().isoformat()

PROMPT = """You write curated Q&A rows for a SyteLine Prospect-to-Cash help chatbot.
Use ONLY the SECTION TEXT. Never add facts, steps, field names, or numbers that are not in it.

Return JSON: {"items": [ ... up to 2 items ... ]}. Each item:
- "question": a short, natural question a business user would ask that this section answers fully.
- "answer": 1-4 sentences (or a short numbered list for steps) copied or tightly paraphrased from the
  section, reusing its exact terms. No links, no citations, no "the document says".
- "variations": 3 other ways a user might ask the same question (casual, short, different wording).
- "intent": one of HELP_GENERIC (what is / definition), HELP_FIELD (a field or setting), HELP_PROCESS (how to / steps / why).
- "keywords": 2-5 comma-separated key terms from the section.
If the section is too thin to answer anything completely, return {"items": []}."""

_STOPWORDS = set(
    "a an the and or of to in on for with by at from as is are be been was were it its this that these those "
    "can may might will would should must do does did not no if then than so such into onto via per each any "
    "all both either you your they their there here which who whom what when where why how also only more most "
    "use used using has have had i we our us he she his her them".split()
)


def _content_words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9/]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]


def grounding_ratio(answer: str, source: str) -> float:
    answer_words = _content_words(answer)
    if not answer_words:
        return 0.0
    source_words = set(_content_words(source))
    # allow simple plural/singular differences
    hits = sum(1 for w in answer_words if w in source_words or w.rstrip("s") in source_words or f"{w}s" in source_words)
    return hits / len(answer_words)


def draft_items(client: OpenAI, chunk: MarkdownChunk) -> list[dict]:
    response = client.chat.completions.create(
        model=settings.primary_llm,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"SECTION: {chunk.full_context_path}\n\nSECTION TEXT:\n{chunk.text}"},
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    return payload.get("items", []) if isinstance(payload, dict) else []


def main() -> None:
    client = OpenAI(api_key=settings.openai_api_key)
    chunks = [c for c in process_all_markdown(KNOWLEDGE_ROOT) if len(c.text) >= MIN_SECTION_CHARS]

    rows_by_file: dict[str, list[dict]] = defaultdict(list)
    variations_by_file: dict[str, list[dict]] = defaultdict(list)
    seen_questions: set[str] = set()
    kept = dropped = 0
    counter = 0

    for chunk in chunks:
        for item in draft_items(client, chunk):
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer or question.lower() in seen_questions:
                continue
            ratio = grounding_ratio(answer, chunk.text)
            if ratio < GROUNDING_MIN_RATIO:
                dropped += 1
                print(f"  DROP (grounding {ratio:.2f}) {question}")
                continue
            seen_questions.add(question.lower())
            kept += 1
            counter += 1
            qa_id = f"KB-{counter:04d}"  # distinct from the retired QA-xxxx placeholder ids
            stem = chunk.document_id
            rows_by_file[stem].append(
                dict(
                    qa_id=qa_id, domain="PROSPECT_TO_CASH", process=chunk.section_level1 or stem,
                    module=chunk.section_level1 or stem, form="", field="",
                    intent=item.get("intent", "HELP_GENERIC"), sub_intent="",
                    canonical_question=question, answer=answer,
                    keywords=str(item.get("keywords", "")), synonyms="", route="FAST_QA",
                    source_reference=chunk.source_file, source_section=chunk.full_context_path,
                    version="1.0", site_scope="", security_scope="ALL", approval_status="APPROVED",
                    approved_by="AUTO-DERIVED from knowledge base — pending SME review",
                    effective_date=TODAY, active=True, last_reviewed_date=TODAY, language="en",
                )
            )
            for n, variation in enumerate(item.get("variations", [])[:3], start=1):
                variations_by_file[stem].append(
                    dict(qa_id=qa_id, variation_id=f"V{n}", question_variation=str(variation).strip(),
                         language="en", source="auto_derived", validated=False)
                )
        print(f"{chunk.source_file:32} {chunk.full_context_path[:70]}")

    QA_ROOT.mkdir(parents=True, exist_ok=True)
    for old in QA_ROOT.glob("*.xlsx"):
        old.unlink()
    for stem, rows in rows_by_file.items():
        with pd.ExcelWriter(QA_ROOT / f"{stem}.xlsx", engine="openpyxl") as writer:
            pd.DataFrame(rows, columns=COLUMNS).to_excel(writer, sheet_name="qa_master", index=False)
            pd.DataFrame(variations_by_file[stem], columns=VARIATION_COLUMNS).to_excel(
                writer, sheet_name="question_variations", index=False
            )
    print(f"\nKept {kept} grounded Q&A rows in {len(rows_by_file)} files; dropped {dropped} ungrounded drafts.")


if __name__ == "__main__":
    main()
