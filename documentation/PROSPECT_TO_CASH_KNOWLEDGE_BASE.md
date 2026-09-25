# Prospect-to-Cash Knowledge Base — General SyteLine Guidance

## Purpose and status

This is the pre-Phase-4 knowledge expansion requested on 2026-09-24. It covers the CRM-to-cash business lifecycle with retrieval-ready Markdown, one module at a time. The 14 rollout-stage files from `data/qa/prospect_to_cash/` now have matching Markdown counterparts; four additional files cover CRM setup, field/form navigation, follow-up, and returns. A later gap review added two more articles for campaigns/forecasting and nonstandard order/billing paths. The five original starter articles were replaced where they overstated configurable behavior.

The content is **general Infor CSI/SyteLine guidance**, based on public Infor help in the 9.01.x, 10.x, and 2026.x families. It has **not** been validated against the user's exact SyteLine release, site setup, custom forms, security rules, or approved IDOs. It is suitable as a version-aware draft reference and needs consultant/business approval before production use. It does not train or fine-tune an SLM/LLM: the Markdown is chunked and embedded into the RAG knowledge index at application startup. Phase 7 owns model training.

## Module inventory and process coverage

| Stage | File | Main coverage |
| --- | --- | --- |
| CRM setup | `crm_setup.md` | Status/source setup, form map, technical mapping boundary |
| Campaign and forecast | `campaigns_and_forecasts.md` | Contact groups, campaigns, competitors, teams, sales periods and forecasts |
| Prospect | `prospect.md` | Company capture, contacts, interactions, conversion |
| Lead | `lead.md` | Interest, qualification, status, follow-up, opportunity link |
| Opportunity | `opportunity.md` | Pipeline fields, tasks, forecasting, win/loss |
| Estimate | `estimate.md` | Header, lines, status, pricing and order handoff |
| Quotation | `quotation.md` | Customer-facing proposal, issue, revision, acceptance |
| Customer | `customer.md` | Bill-to, ship-to, terms, credit and CRM data |
| Customer Order | `customer_order.md` | Header, order entry, status, exceptions |
| Customer Order Line | `customer_order_line.md` | Item/quantity, source, pricing, availability, line states |
| Order/billing variations | `order_and_billing_variations.md` | Blanket releases, drop ship, EDI, multi-site, consolidated billing |
| Pricing | `pricing.md` | Price sources, discounts, quote-to-order reconciliation |
| Credit | `credit.md` | Customer/order holds, parameters, diagnosis, multi-site |
| Shipment | `shipment.md` | Picking, shipping, partials, error diagnosis |
| Invoice | `invoice.md` | Shipped-not-invoiced, invoice process, credit memo |
| Payment | `payment.md` | A/R payments, distributions, aging, collection review |
| Follow-up | `customer_follow_up.md` | Quote, delivery, billing, and collection contacts |
| Returns | `returns_and_corrections.md` | RMA, credit, correction paths |
| Cross-process FAQ | `faq.md` | End-to-end trace, question-to-data mapping |
| Form/field guide | `form_field_catalog.md` | Owning forms, displayed field meaning, relationships |

Every module is stored directly under `data/knowledge/prospect_to_cash/` because `process_all_markdown()` currently reads only `*.md` in that folder. Each section uses headings, a concise Section Summary, and Keywords for the existing chunker. The files contain the explanations, fields, steps, and decision checks as plain text with no external links. The frontend's source citation points to the local source filename and heading path.

## Source policy

- The content was checked against Infor CSI/SyteLine CRM overview, recommended CRM setup, and CRM scenario topics for front-office flow.
- Customer creation, order entry, credit hold, shipping, order invoicing, A/R steps, payment application, and A/R aging topics informed the fulfillment and cash articles.
- The gap-fill articles were checked against Infor CRM scenarios for campaign and opportunity work, plus blanket-order creation and consolidated-invoicing topics.
- This document and the vectorized knowledge articles contain no external URLs or Markdown links. Version families are mixed because an exact deployment version was not supplied; release-specific differences must be checked before operational use.

## Corrections to the starter knowledge

1. A quote or opportunity does not automatically become an order; conversion and order entry are distinct.
2. The customer does not have to be created only after quote acceptance; an existing customer can have leads and opportunities.
3. “Release order” is not a universal standard next step; header/line status, holds, and site workflow need inspection.
4. An over-limit order is not automatically held in every configuration. The A/R hold reason parameter and line settings matter.
5. Shipment does not automatically create a standard invoice. The order invoicing process selects eligible shipped quantities.
6. `Ship Partial` on the report does not mean any fraction of a line can automatically ship.
7. Invoice or credit correction may require a credit memo, RMA, or noninventory A/R path depending on the transaction.

## Operational boundary and remaining work

Static Markdown can answer definitions, form orientation, generic steps, common causes, and what evidence to gather. Current balances, order status, shipment dates, invoice state, price for a specific customer, and payment application need a permission-checked SyteLine connector in Phase 4. The chatbot should ask for an entity, identifier, and site when those are missing. Any CREATE/UPDATE/RELEASE/APPROVE action is outside this read-only knowledge expansion.

The exact form identifiers, IDO collections, properties, methods, role permissions, field/row filters, and audit requirements remain **[NEEDS SYTELINE CONFIRMATION]**. Fast Q&A workbooks have been auto-derived from the earlier 18 Markdown articles and are marked APPROVED for loading, but their `approved_by` metadata explicitly says they are pending SME review. The two gap-fill articles are Markdown-only until Q&A is regenerated and reviewed. Treat all generated Q&A as unapproved for production regardless of its loader status. Newly added Markdown becomes visible to the running RAG index only after an application restart or explicit reindex; the index is constructed at startup. Before production activation, apply the per-domain acceptance checklist in the master prompt §71, including version, citations, permissions, and business UAT.

## Verification for this content change

1. Confirm every expected Markdown file exists, has substantive text, and contains no external URLs or Markdown links.
2. `process_all_markdown()` now produces 162 chunks from all 20 files, with 162 unique chunk IDs. A corpus check finds no URLs or Markdown links in the ingested files.
3. The local server was restarted after the final article edits. `logs/chatbot.log` records 162 Markdown chunks from 20 files, 690 vectors stored in `ptc_knowledge` (162 Markdown chunks plus 528 Fast Q&A search entries), and `startup_ready` on 2026-09-25.
4. Live `/chat` queries returned `MARKDOWN_RAG_RESPONSE` from the prospect, credit, invoice, payment, and new blanket-order articles. The blanket-line versus release query cited `order_and_billing_variations.md`. The invoice answer names the To Be Invoiced Report and Order Invoicing/Credit Memo instead of claiming shipment automatically creates an invoice. A customer-balance request without an identifier returned `CLARIFY`.
5. The focused and existing automated suite passed after the gap-fill articles: 78 tests. Validate the actual deployment version and local procedures with a SyteLine consultant before marking any area approved for production.
