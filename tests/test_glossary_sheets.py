"""The glossary sheet in each Q&A workbook is merged with business_glossary.csv."""

import shutil
from pathlib import Path

import openpyxl

from backend.app.qa.glossary import expand_query, load_glossary

TEMPLATE = Path(__file__).resolve().parents[1] / "documentation" / "data_templates" / "SyteLine_QA_Template.xlsx"


def _csv(tmp_path, text):
    path = tmp_path / "business_glossary.csv"
    path.write_text("canonical_term,synonyms,abbreviation,module,process\n" + text, encoding="utf-8")
    return path


def test_workbook_glossary_sheets_are_loaded_and_merged(tmp_path):
    books = tmp_path / "qa"
    books.mkdir()
    shutil.copy(TEMPLATE, books / "credit.xlsx")  # glossary sheet: Customer Order, Credit Hold, RMA
    csv_path = _csv(tmp_path, "Customer Order,order|purchase order,CO,CRM,Order\n")
    entries = {e.canonical_term: e for e in load_glossary(csv_path, workbook_root=books)}
    assert set(entries) == {"Customer Order", "Credit Hold", "Return Material Authorization"}
    order = entries["Customer Order"]
    assert order.abbreviation == "CO"
    assert {"order", "purchase order", "sales order", "SO"} <= set(order.synonyms)  # both sources, no duplicates
    assert len(order.synonyms) == len({s.lower() for s in order.synonyms})


def test_workbook_terms_expand_questions(tmp_path):
    books = tmp_path / "qa"
    books.mkdir()
    shutil.copy(TEMPLATE, books / "returns.xlsx")
    glossary = load_glossary(_csv(tmp_path, ""), workbook_root=books)
    assert "Return Material Authorization" in expand_query("how do I process an RMA", glossary)


def test_workbooks_without_a_glossary_sheet_are_fine(tmp_path):
    books = tmp_path / "qa"
    books.mkdir()
    book = openpyxl.Workbook()
    book.active.title = "qa_master"
    book.save(books / "lead.xlsx")
    assert [e.canonical_term for e in load_glossary(_csv(tmp_path, "Lead,inquiry,,CRM,Lead\n"), books)] == ["Lead"]


def test_empty_rows_are_ignored(tmp_path):
    assert load_glossary(_csv(tmp_path, ",,,,\nLead,,,,\n"), workbook_root=None)[0].canonical_term == "Lead"
