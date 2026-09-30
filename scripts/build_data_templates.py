"""Build the data team's Excel Q&A template and Word module template.

    python -m scripts.build_data_templates

Writes to documentation/data_templates/:
  SyteLine_QA_Template.xlsx            one workbook per module (sheets the loader reads + help)
  SyteLine_Module_Knowledge_Template.docx   Word version of the Markdown module template

The column list, allowed values and heading structure come from the same code the chatbot uses
to load data (qa/loader.py, taxonomy, markdown template), so the templates can't drift from it.
"""

import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from backend.app.classification.taxonomy import IntentLabel
from scripts.validate_knowledge_data import GLOSSARY_COLUMNS, QA_COLUMNS, VARIATION_COLUMNS

OUT = Path(__file__).resolve().parents[1] / "documentation" / "data_templates"
MD_TEMPLATE = OUT / "SyteLine_Module_Knowledge_Template.md"

HEADER_FILL = PatternFill("solid", fgColor="1C4FD6")
REQUIRED_FILL = PatternFill("solid", fgColor="C0392B")
EXAMPLE_FILL = PatternFill("solid", fgColor="EEF3FC")
HEADER_FONT = Font(bold=True, color="FFFFFF")
THIN = Side(style="thin", color="D5DCEA")

MODULES = ["prospect", "lead", "opportunity", "estimate", "quotation", "customer", "customer_order",
           "customer_order_line", "pricing", "credit", "shipment", "invoice", "payment", "returns_and_corrections",
           "customer_follow_up", "crm_setup", "form_field_catalog", "faq"]

# column -> (required, help text shown as the header's note)
QA_HELP = {
    "qa_id": (True, "Unique id, never reused. Format PREFIX-NUMBER, e.g. KB-0133. Ask the chatbot team for the next free number range."),
    "domain": (False, "Always PROSPECT_TO_CASH."),
    "process": (False, "Business process name, e.g. Credit Review."),
    "module": (True, "Module id = the file name without .xlsx, e.g. credit. Must match the Markdown file name."),
    "form": (False, "SyteLine form the question is about, exactly as on screen, e.g. Customer Orders."),
    "field": (False, "Field name if the question is about one field, e.g. Credit Hold."),
    "intent": (True, "HELP_GENERIC = what is…; HELP_PROCESS = how do I / why; HELP_FIELD = what does field X mean; HELP_SCREEN = what is this form for; TROUBLESHOOTING = why can't I / error."),
    "sub_intent": (False, "Optional short label, e.g. RELEASE_CREDIT_HOLD."),
    "canonical_question": (True, "The clearest way to ask it, ending with '?'."),
    "answer": (True, "The APPROVED answer, shown to users word for word when their question matches. 1–4 sentences or a few short steps (under ~600 characters). Long procedures go in the Markdown file."),
    "keywords": (True, "3–6 words users type, comma-separated, e.g. credit hold, release, unblock order."),
    "synonyms": (False, "Other names for the main term, separated with |, e.g. SO|sales order."),
    "route": (True, "FAST_QA (normal). MARKDOWN_RAG only if the row should never be shown word for word."),
    "source_reference": (True, "Where the answer comes from: the module Markdown file (credit.md) or the company SOP name."),
    "source_section": (False, "Section in that source, e.g. 3. Release a credit hold."),
    "version": (False, "1 for new rows; add 1 when the answer changes."),
    "site_scope": (False, "Empty or ALL = every site; otherwise site codes, e.g. MAIN|EAST."),
    "security_scope": (False, "ALL = every user may see it; otherwise SyteLine groups, e.g. AR_CLERK|CREDIT_MANAGER. Stored now, enforced when SyteLine roles are connected."),
    "approval_status": (True, "DRAFT → IN_REVIEW → APPROVED (or REJECTED). ONLY APPROVED rows are used by the chatbot."),
    "approved_by": (False, "REQUIRED when APPROVED: business reviewer's name and team, e.g. A. Kumar (Credit team)."),
    "effective_date": (False, "Date the answer becomes valid (YYYY-MM-DD). Required when APPROVED."),
    "active": (True, "TRUE to use; FALSE to switch a row off without deleting it."),
    "last_reviewed_date": (False, "Date the row was last checked (YYYY-MM-DD)."),
    "language": (True, "en"),
}
VARIATION_HELP = {
    "qa_id": "The qa_id this wording belongs to (must exist in qa_master).",
    "variation_id": "V1, V2, V3 … per qa_id.",
    "question_variation": "Another way USERS ask the same question — casual words, slang, abbreviations, typos. At least 3 per row.",
    "language": "en",
    "source": "Where the wording came from: user_interview, helpdesk_ticket, chatbot_log, sme.",
    "validated": "TRUE once a business user confirmed it means the same question.",
}
GLOSSARY_HELP = {
    "canonical_term": "The official SyteLine / business term, e.g. Customer Order.",
    "synonyms": "Other names users say, separated with |, e.g. sales order|SO|order.",
    "abbreviation": "Short form, e.g. CO.",
    "module": "Module id, e.g. customer_order.",
    "process": "Process name, e.g. Order Entry.",
}

EXAMPLES = [
    {"qa_id": "KB-9001", "domain": "PROSPECT_TO_CASH", "process": "Credit Review", "module": "credit",
     "form": "Customer Orders", "field": "Credit Hold", "intent": "HELP_PROCESS", "sub_intent": "RELEASE_CREDIT_HOLD",
     "canonical_question": "How do I release a credit hold on a customer order?",
     "answer": "Only users with credit authority can release a hold. Open the Customer Orders form, check the hold "
               "reason, clear the Credit Hold check box and save. If the customer itself is on hold, the order stays "
               "blocked until the customer hold is released.",
     "keywords": "credit hold, release hold, unblock order", "synonyms": "credit block|on hold", "route": "FAST_QA",
     "source_reference": "credit.md", "source_section": "Release a credit hold", "version": 1, "site_scope": "ALL",
     "security_scope": "AR_CLERK|CREDIT_MANAGER", "approval_status": "DRAFT", "approved_by": "",
     "effective_date": "", "active": True, "last_reviewed_date": "", "language": "en"},
    {"qa_id": "KB-9002", "domain": "PROSPECT_TO_CASH", "process": "Credit Review", "module": "credit",
     "form": "Customers", "field": "Credit Limit", "intent": "HELP_FIELD", "sub_intent": "",
     "canonical_question": "What does the Credit Limit field mean?",
     "answer": "Credit Limit is the maximum amount the customer may owe, including open orders, before new orders "
               "are held for credit review.",
     "keywords": "credit limit, customer limit, how much credit", "synonyms": "limit", "route": "FAST_QA",
     "source_reference": "credit.md", "source_section": "Key Fields", "version": 1, "site_scope": "ALL",
     "security_scope": "ALL", "approval_status": "DRAFT", "approved_by": "", "effective_date": "", "active": True,
     "last_reviewed_date": "", "language": "en"},
]
VARIATION_EXAMPLES = [
    ("KB-9001", "V1", "how to release credit hold", "en", "user_interview", False),
    ("KB-9001", "V2", "order is blocked by credit, how to unblock", "en", "helpdesk_ticket", False),
    ("KB-9001", "V3", "knock off the credit hold pls", "en", "chatbot_log", False),
    ("KB-9002", "V1", "what is credit limit", "en", "sme", False),
    ("KB-9002", "V2", "how much credit does the customer have", "en", "user_interview", False),
    ("KB-9002", "V3", "meaning of credit limit field", "en", "sme", False),
]
GLOSSARY_EXAMPLES = [
    ("Customer Order", "sales order|SO|order", "CO", "customer_order", "Order Entry"),
    ("Credit Hold", "credit block|on hold|blocked order", "", "credit", "Credit Review"),
    ("Return Material Authorization", "customer return|return", "RMA", "returns_and_corrections", "Returns"),
]

README = [
    ("SyteLine Prospect-to-Cash — Q&A template (one workbook per module)", "title"),
    ("", ""),
    ("WHAT THIS FILE IS", "h"),
    ("Curated question-and-answer pairs. When a user's question matches a row closely, the chatbot shows the "
     "APPROVED answer word for word. Everything else is answered from the module's Markdown document.", ""),
    ("", ""),
    ("HOW TO FILL IT", "h"),
    ("1. Save a copy per module and name it after the module id: credit.xlsx, customer_order.xlsx … "
     "(same name as the Markdown file: credit.md).", ""),
    ("2. qa_master — one row per question. Red headers are required. Point at a header to see its note.", ""),
    ("3. question_variations — at least 3 other ways users ask each question (their words, slang, typos).", ""),
    ("4. glossary — every term, nickname and abbreviation users use in this module (SO = Customer Order).", ""),
    ("5. New rows start as DRAFT. A business reviewer checks them and sets APPROVED + approved_by + effective_date.", ""),
    ("6. Delete the blue EXAMPLE rows (KB-9001, KB-9002) before sending.", ""),
    ("7. Check the file:  python -m scripts.validate_knowledge_data credit.xlsx", ""),
    ("", ""),
    ("RULES", "h"),
    ("• Do not rename, reorder or delete columns or sheets — the chatbot reads them by name.", ""),
    ("• Only APPROVED + active rows are used. The answer must agree with the module's Markdown document.", ""),
    ("• Keep answers short (1–4 sentences). Long procedures belong in the Markdown document.", ""),
    ("• Use SyteLine form, field and status names exactly as on screen.", ""),
    ("• Never put customer names, real order numbers, prices, personal data or passwords in any cell.", ""),
    ("• A question already answered here should not be answered differently in another workbook.", ""),
]


def _style_header(sheet, columns, helps, required=frozenset()):
    for index, column in enumerate(columns, 1):
        cell = sheet.cell(row=1, column=index, value=column)
        cell.font = HEADER_FONT
        cell.fill = REQUIRED_FILL if column in required else HEADER_FILL
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.comment = Comment(("REQUIRED. " if column in required else "") + helps.get(column, ""), "Chatbot team",
                               width=320, height=140)
    sheet.freeze_panes = "B2"
    sheet.row_dimensions[1].height = 30


def _widths(sheet, widths: dict[str, int]):
    for index in range(1, sheet.max_column + 1):
        name = sheet.cell(row=1, column=index).value
        sheet.column_dimensions[get_column_letter(index)].width = widths.get(name, 16)


def _dropdown(sheet, column_name, values, rows=500):
    columns = [sheet.cell(row=1, column=i).value for i in range(1, sheet.max_column + 1)]
    letter = get_column_letter(columns.index(column_name) + 1)
    rule = DataValidation(type="list", formula1=f'"{",".join(values)}"', allow_blank=True,
                          showErrorMessage=True, errorTitle="Not allowed",
                          error=f"Choose one of: {', '.join(values)}")
    sheet.add_data_validation(rule)
    rule.add(f"{letter}2:{letter}{rows}")


def _example_rows(sheet, rows):
    for row in rows:
        sheet.append(list(row))
        for cell in sheet[sheet.max_row]:
            cell.fill = EXAMPLE_FILL
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=THIN)


def build_excel() -> Path:
    wb = Workbook()
    readme = wb.active
    readme.title = "README"
    for text, kind in README:
        readme.append([text])
        cell = readme.cell(row=readme.max_row, column=1)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if kind == "title":
            cell.font = Font(bold=True, size=14, color="1C4FD6")
        elif kind == "h":
            cell.font = Font(bold=True, color="1C4FD6")
    readme.column_dimensions["A"].width = 130

    qa = wb.create_sheet("qa_master")
    required = {c for c, (req, _h) in QA_HELP.items() if req}
    _style_header(qa, QA_COLUMNS, {c: h for c, (_r, h) in QA_HELP.items()}, required)
    _example_rows(qa, [[e[c] for c in QA_COLUMNS] for e in EXAMPLES])
    _widths(qa, {"qa_id": 11, "canonical_question": 42, "answer": 70, "keywords": 30, "synonyms": 22,
                 "intent": 17, "approval_status": 16, "approved_by": 24, "source_reference": 20,
                 "security_scope": 24, "module": 16, "form": 20})
    _dropdown(qa, "intent", ["HELP_GENERIC", "HELP_PROCESS", "HELP_FIELD", "HELP_SCREEN", "TROUBLESHOOTING"])
    _dropdown(qa, "route", ["FAST_QA", "MARKDOWN_RAG"])
    _dropdown(qa, "approval_status", ["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"])
    _dropdown(qa, "active", ["TRUE", "FALSE"])
    _dropdown(qa, "language", ["en"])
    _dropdown(qa, "domain", ["PROSPECT_TO_CASH"])
    _dropdown(qa, "module", MODULES)

    variations = wb.create_sheet("question_variations")
    _style_header(variations, VARIATION_COLUMNS, VARIATION_HELP, {"qa_id", "variation_id", "question_variation"})
    _example_rows(variations, VARIATION_EXAMPLES)
    _widths(variations, {"question_variation": 60, "source": 18})
    _dropdown(variations, "source", ["user_interview", "helpdesk_ticket", "chatbot_log", "sme"])
    _dropdown(variations, "validated", ["TRUE", "FALSE"])

    glossary = wb.create_sheet("glossary")
    _style_header(glossary, GLOSSARY_COLUMNS, GLOSSARY_HELP, {"canonical_term"})
    _example_rows(glossary, GLOSSARY_EXAMPLES)
    _widths(glossary, {"canonical_term": 30, "synonyms": 45, "abbreviation": 14, "module": 24, "process": 20})
    _dropdown(glossary, "module", MODULES)

    allowed = wb.create_sheet("allowed_values")
    lists = {
        "intent": ["HELP_GENERIC", "HELP_PROCESS", "HELP_FIELD", "HELP_SCREEN", "TROUBLESHOOTING"],
        "route": ["FAST_QA", "MARKDOWN_RAG"],
        "approval_status": ["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"],
        "active": ["TRUE", "FALSE"],
        "module (file name)": MODULES,
        "variation source": ["user_interview", "helpdesk_ticket", "chatbot_log", "sme"],
    }
    for index, (name, values) in enumerate(lists.items(), 1):
        cell = allowed.cell(row=1, column=index, value=name)
        cell.font, cell.fill = HEADER_FONT, HEADER_FILL
        for row, value in enumerate(values, 2):
            allowed.cell(row=row, column=index, value=value)
        allowed.column_dimensions[get_column_letter(index)].width = 26
    # Every intent the chatbot knows, for reference (only the five above are used for Q&A rows).
    assert set(lists["intent"]) <= {i.value for i in IntentLabel}

    wb.active = 1
    path = OUT / "SyteLine_QA_Template.xlsx"
    wb.save(path)
    return path


# ── Word template (same structure as the Markdown template) ─────────────


def _shade(cell, hex_color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _note(doc, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x87, 0x8C, 0xA8)
    return p


def _label_line(doc, label: str, value: str):
    p = doc.add_paragraph()
    p.add_run(f"{label}: ").bold = True
    p.add_run(value)


def build_word() -> Path:
    """Word version of the Markdown template. Heading 1/2/3 = # / ## / ###; a grey note becomes a
    comment when converted. The converter (scripts/convert_docx_to_md.py) turns a filled copy
    into the Markdown file the chatbot loads."""
    text = MD_TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"^<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)  # the long how-to note
    doc = Document()
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(10.5)

    intro = doc.add_paragraph()
    run = intro.add_run("HOW TO USE: fill in every <placeholder>. Keep the headings (Heading 1 / Heading 2 styles), "
                        "every 'Section Summary:' and 'Keywords:' line. Grey italic notes are for you and are "
                        "removed when the file is converted. Then run: python -m scripts.convert_docx_to_md "
                        "<file>.docx and python -m scripts.validate_knowledge_data <file>.md")
    run.italic, run.font.size = True, Pt(9)
    run.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)

    table_rows: list[list[str]] = []

    def flush_table():
        if not table_rows:
            return
        header, *body = [r for r in table_rows if not re.match(r"^\|?\s*-{3}", "|".join(r))]
        table = doc.add_table(rows=1 + len(body), cols=len(header))
        table.style = "Table Grid"
        for i, value in enumerate(header):
            cell = table.rows[0].cells[i]
            cell.text = value
            cell.paragraphs[0].runs[0].bold = True
            _shade(cell, "DCE6FA")
        for r, row in enumerate(body, 1):
            for i, value in enumerate(row[: len(header)]):
                table.rows[r].cells[i].text = value
        table_rows.clear()
        doc.add_paragraph().paragraph_format.space_after = Pt(2)  # space before the next line

    note_lines: list[str] | None = None  # inside a multi-line <!-- note -->
    for line in text.splitlines():
        stripped = line.strip()
        if note_lines is not None:
            note_lines.append(stripped.removesuffix("-->").strip())
            if "-->" in stripped:
                _note(doc, "Note: " + " ".join(p for p in note_lines if p))
                note_lines = None
            continue
        if stripped.startswith("<!--"):
            note = stripped.removeprefix("<!--").removesuffix("-->").strip()
            if "-->" in stripped:
                if note:
                    _note(doc, "Note: " + note)
            else:
                note_lines = [note]  # the note continues on the next lines — keep all of it
            continue
        if stripped.startswith("|"):
            table_rows.append([c.strip() for c in stripped.strip("|").split("|")])
            continue
        flush_table()
        if not stripped or stripped == "---":
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            doc.add_heading(heading.group(2), level=len(heading.group(1)))
            continue
        label = re.match(r"^[-*]?\s*\*\*(.+?):\*\*\s*(.*)$", stripped)
        if label:
            _label_line(doc, label.group(1), label.group(2))
            continue
        number = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if number:
            # Typed numbers, not Word's "List Number" style: Word continues one list through the
            # whole file, so the task steps showed 15, 16, 17 after the 14-line contents list.
            p = doc.add_paragraph(f"{number.group(1)}.\t{number.group(2)}")
            p.paragraph_format.left_indent = Cm(0.9)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
            p.paragraph_format.space_after = Pt(2)
            continue
        if re.match(r"^[*-]\s", stripped):
            doc.add_paragraph(stripped[2:], style="List Bullet")
            continue
        doc.add_paragraph(stripped.replace("**", ""))
    flush_table()
    path = OUT / "SyteLine_Module_Knowledge_Template.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("saved", build_excel())
    print("saved", build_word())
