"""Guard the pre-Phase-4 knowledge corpus and sample Q&A boundary."""

from pathlib import Path

from backend.app.rag.markdown_processor import process_all_markdown


ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge" / "prospect_to_cash"
CORE_MODULES = {
    "prospect.md", "lead.md", "opportunity.md", "estimate.md", "quotation.md",
    "customer.md", "customer_order.md", "customer_order_line.md", "pricing.md",
    "credit.md", "shipment.md", "invoice.md", "payment.md", "faq.md",
    "campaigns_and_forecasts.md", "order_and_billing_variations.md",
}


def test_every_prospect_to_cash_article_is_chunked_with_unique_ids():
    files = {path.name for path in ROOT.glob("*.md")}
    chunks = process_all_markdown(ROOT)

    assert CORE_MODULES <= files
    assert {chunk.source_file for chunk in chunks} == files
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert all(chunk.full_context_path and chunk.text for chunk in chunks)


def test_knowledge_articles_contain_complete_text_without_external_links():
    texts = [path.read_text(encoding="utf-8") for path in ROOT.glob("*.md")]

    assert all("http://" not in text and "https://" not in text and "](" not in text for text in texts)
    assert all("## " in text and "**Section Summary:**" in text for text in texts)
