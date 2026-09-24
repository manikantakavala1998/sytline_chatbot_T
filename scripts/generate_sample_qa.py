"""
Makes starter Q&A Excel files, one per Prospect-to-Cash level/stage, directly
under data/qa/prospect_to_cash/<level>.xlsx — using the same level names the
Markdown knowledge base will use later (master prompt section 13), so both
sources are organized the same way and each level can be reviewed/approved
independently. One flat file per level, no extra subfolders.

Run again any time to regenerate all files (overwrites them). To add real
questions long-term, edit the Excel files directly, or add rows below and
re-run this script.
"""

from pathlib import Path

import pandas as pd

COLUMNS = [
    "qa_id", "domain", "process", "module", "form", "field",
    "intent", "sub_intent", "canonical_question", "answer",
    "keywords", "synonyms", "route", "source_reference", "source_section",
    "version", "site_scope", "security_scope", "approval_status",
    "approved_by", "effective_date", "active", "last_reviewed_date", "language",
]

VARIATION_COLUMNS = ["qa_id", "variation_id", "question_variation", "language", "source", "validated"]


def _row(qa_id, process, module, form, field, intent, sub_intent,
         canonical_question, answer, keywords, synonyms, source_section):
    return dict(
        qa_id=qa_id, domain="PROSPECT_TO_CASH", process=process, module=module,
        form=form, field=field, intent=intent, sub_intent=sub_intent,
        canonical_question=canonical_question, answer=answer,
        keywords=keywords, synonyms=synonyms, route="FAST_QA",
        source_reference="PTC Training Guide", source_section=source_section,
        version="1.0", site_scope="", security_scope="ALL", approval_status="DRAFT",
        approved_by="", effective_date="2026-01-01", active=True,
        last_reviewed_date="2026-01-01", language="en",
    )


# One key per level folder under data/qa/prospect_to_cash/ — same names §13
# uses for the Markdown knowledge base folders.
LEVELS: dict[str, list[dict]] = {
    "prospect": [
        _row("QA-0001", "Prospect", "CRM", "Prospects", "", "HELP_GENERIC", "definition",
             "What is a Prospect?",
             "A Prospect is a potential customer who has not yet been qualified as a Lead or Opportunity. It is the earliest stage in the Prospect-to-Cash process.",
             "prospect,potential customer", "potential customer,lead contact", "1.1"),
    ],
    "lead": [
        _row("QA-0009", "Lead", "CRM", "Leads", "", "HELP_GENERIC", "definition",
             "What is a Lead?",
             "A Lead is a Prospect who has been qualified as genuinely interested and is being actively followed up on — one step further than a raw Prospect, but before a formal Opportunity is created.",
             "lead,inquiry", "inquiry,interested party", "1.1b"),
    ],
    "opportunity": [
        _row("QA-0002", "Opportunity", "CRM", "Opportunities", "", "HELP_GENERIC", "definition",
             "What is an Opportunity?",
             "An Opportunity is a qualified potential sale being actively pursued, created once a Prospect or Lead shows real buying interest.",
             "opportunity,deal", "deal,potential sale", "1.2"),
    ],
    "estimate": [
        _row("QA-0003", "Estimate", "CRM", "Estimates", "", "HELP_GENERIC", "definition",
             "What is an Estimate?",
             "An Estimate is a preliminary price and terms calculation prepared for a customer before a formal Quotation is issued.",
             "estimate,quote draft", "quote draft", "1.3"),
    ],
    "quotation": [
        _row("QA-0010", "Quotation", "CRM", "Quotations", "", "HELP_GENERIC", "definition",
             "What is a Quotation?",
             "A Quotation (or Quote) is a formal, customer-facing price and terms document sent after an Estimate is finalized. The customer accepting it is what creates a Customer Order.",
             "quotation,quote", "quote,proposal", "1.4"),
        _row("QA-0011", "Quotation", "CRM", "Quotations", "", "HELP_PROCESS", "how_to",
             "How do I print a quotation?",
             "Open the Quotation record, select Print or Print Preview from the toolbar, choose the output format, then print or save it.",
             "print quotation", "", "1.5"),
    ],
    "customer": [
        _row("QA-0012", "Customer", "CRM", "Customers", "", "HELP_GENERIC", "definition",
             "What is a Customer?",
             "A Customer is an organization or person with an approved account who can place Customer Orders — created once a Quotation is accepted.",
             "customer,client", "client,account", "2.1"),
    ],
    "customer_order": [
        _row("QA-0013", "Customer Order", "Order Entry", "Customer Orders", "", "HELP_GENERIC", "definition",
             "What is a Customer Order?",
             "A Customer Order is the confirmed request from a Customer to purchase goods or services, created after a Quotation is accepted. It drives fulfillment, invoicing, and payment.",
             "customer order,sales order", "sales order,order", "4.0"),
        _row("QA-0004", "Customer Order", "Order Entry", "Customer Orders", "Due Date", "HELP_FIELD", "field_definition",
             "What is Due Date on a Customer Order?",
             "Due Date is the date the customer expects to receive the ordered goods or services. It drives scheduling and shipment planning.",
             "due date,customer order", "delivery date,expected date", "4.2"),
        _row("QA-0006", "Customer Order", "Order Entry", "Customer Orders", "", "HELP_PROCESS", "how_to",
             "How do I create a Customer Order?",
             "Open the Customer Orders form, select New, choose the customer, add order lines with item and quantity, then release the order once complete.",
             "create customer order,new order", "", "4.1"),
    ],
    "customer_order_line": [
        _row("QA-0014", "Customer Order", "Order Entry", "Customer Orders", "Order Line", "HELP_FIELD", "definition",
             "What is an Order Line?",
             "An Order Line is a single item or service entry within a Customer Order, specifying the item, quantity, price, and due date for that particular line.",
             "order line,line item", "line item,order item", "4.3"),
    ],
    "pricing": [
        _row("QA-0015", "Pricing", "Order Entry", "Customer Orders", "", "HELP_PROCESS", "how_to",
             "How is pricing determined on a Customer Order?",
             "Pricing comes from the item's price list, any customer-specific pricing agreements, and applicable discounts — applied automatically when the item is added to an order line.",
             "pricing,price list", "", "5.1"),
    ],
    "credit": [
        _row("QA-0005", "Credit", "Accounts Receivable", "Customers", "Credit Limit", "HELP_FIELD", "field_definition",
             "What is Credit Limit?",
             "Credit Limit is the maximum outstanding balance a customer is allowed to carry before new orders are held for credit review.",
             "credit limit", "credit ceiling,spending limit", "7.1"),
        _row("QA-0016", "Credit", "Accounts Receivable", "Customer Orders", "", "HELP_GENERIC", "definition",
             "What is a Credit Hold?",
             "A Credit Hold is a status placed on a Customer Order when the customer's outstanding balance would exceed their Credit Limit. The order cannot ship until the hold is released.",
             "credit hold,order hold", "credit block,order hold", "7.2"),
    ],
    "shipment": [
        _row("QA-0017", "Shipment", "Shipping", "Shipments", "", "HELP_GENERIC", "definition",
             "What is a Shipment?",
             "A Shipment is the physical delivery of ordered goods to the customer, created from a released Customer Order and used to record what was actually shipped.",
             "shipment,delivery", "delivery,dispatch", "8.1"),
    ],
    "invoice": [
        _row("QA-0007", "Invoice", "Accounts Receivable", "Invoices", "", "HELP_GENERIC", "definition",
             "What is an Invoice?",
             "An Invoice is the billing document issued to a customer after goods or services are delivered, stating the amount owed.",
             "invoice,bill", "bill", "9.1"),
    ],
    "payment": [
        _row("QA-0018", "Payment", "Accounts Receivable", "Payments", "", "HELP_GENERIC", "definition",
             "What is a Payment?",
             "A Payment is the amount a customer remits against one or more Invoices, recorded to reduce their outstanding Receivable balance.",
             "payment,remittance", "remittance,receipt", "10.2"),
        _row("QA-0008", "Payment", "Accounts Receivable", "Receivables", "", "HELP_GENERIC", "definition",
             "What is a Receivable?",
             "A Receivable is the amount a customer still owes for goods or services already invoiced but not yet paid.",
             "receivable,outstanding balance", "amount owed,outstanding balance", "10.1"),
    ],
    "faq": [
        _row("QA-0019", "Prospect-to-Cash", "CRM", "", "", "HELP_GENERIC", "overview",
             "What is the Prospect-to-Cash process?",
             "Prospect-to-Cash is the end-to-end flow from an initial Prospect through Lead, Opportunity, Estimate, Quotation, Customer, Customer Order, Pricing and Credit checks, Shipment, Invoice, and finally Payment.",
             "prospect to cash,end to end process", "", "0.1"),
    ],
}

VARIATIONS_BY_QA_ID: dict[str, list[str]] = {
    "QA-0001": ["define prospect"],
    "QA-0002": ["define opportunity"],
    "QA-0004": ["what does due date mean"],
    "QA-0005": ["explain credit limit"],
    "QA-0006": ["steps to create a customer order"],
    "QA-0009": ["define lead"],
    "QA-0010": ["define quotation"],
    "QA-0013": ["define customer order"],
    "QA-0016": ["explain credit hold"],
    "QA-0019": ["explain the prospect to cash process", "prospect to cash overview"],
}


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "data" / "qa" / "prospect_to_cash"
    total_rows = 0
    total_variations = 0

    base.mkdir(parents=True, exist_ok=True)

    for level, rows in LEVELS.items():
        variation_rows = []
        for row in rows:
            for i, variation in enumerate(VARIATIONS_BY_QA_ID.get(row["qa_id"], []), start=1):
                variation_rows.append(dict(
                    qa_id=row["qa_id"], variation_id=f"V{i}", question_variation=variation,
                    language="en", source="manual", validated=True,
                ))

        qa_df = pd.DataFrame(rows, columns=COLUMNS)
        variations_df = pd.DataFrame(variation_rows, columns=VARIATION_COLUMNS)

        out_path = base / f"{level}.xlsx"
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            qa_df.to_excel(writer, sheet_name="qa_master", index=False)
            variations_df.to_excel(writer, sheet_name="question_variations", index=False)

        total_rows += len(qa_df)
        total_variations += len(variations_df)
        print(f"  {level}: {len(qa_df)} rows -> {out_path}")

    print(f"Wrote {total_rows} Q&A rows and {total_variations} variations across {len(LEVELS)} levels.")


if __name__ == "__main__":
    main()
