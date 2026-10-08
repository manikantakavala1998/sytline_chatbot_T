# Prospect-to-Cash Knowledge Base — General SyteLine Guidance

## Purpose and status

This is the pre-Phase-4 knowledge expansion requested on 2026-09-24. It covers the CRM-to-cash business lifecycle with retrieval-ready Markdown, one module at a time. The 14 rollout-stage files from `data/qa/prospect_to_cash/` now have matching Markdown counterparts; four additional files cover CRM setup, field/form navigation, follow-up, and returns. A later gap review added two more articles for campaigns/forecasting and nonstandard order/billing paths. The five original starter articles were replaced where they overstated configurable behavior.

Earlier articles are **general Infor CSI/SyteLine guidance** prepared from public help across the 9.01.x, 10.x, and 2026.x families; they are not yet manual-only. The corrected Customer Order Lines article and expanded Pricing, Credit, Shipment, and Invoice articles use the official 9.01.x Customer Service User Guide. The user additionally authorized the official 9.01.x Financials User Guide for Payment; its invoice-to-A/R handoff also uses the Customer Service guide. All eight planned Customer-to-Cash detailed modules (Customer, Customer Order, Customer Order Line, Pricing, Credit, Shipment, Invoice, Payment) have now been expanded, but the first two still need a manual-only source audit. None of this content has been validated against the user's exact SyteLine release, site setup, custom forms, security rules, or approved IDOs. It remains draft reference material needing consultant/business approval before production use. The Markdown is chunked and embedded into the RAG knowledge index; it does not fine-tune an SLM/LLM. Phase 7 owns model training.

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
| Customer | `customer.md` | Expanded screen-level Customers, Customer Ship-Tos, multi-site, credit, contacts, billing defaults and first-order readiness |
| Customer Order | `customer_order.md` | Expanded Customer Orders header, lookup, order type/status, shipping and billing defaults, credit, Quick Entry, and line handoff |
| Customer Order Line | `customer_order_line.md` | Expanded Customer Order Lines form, 32 line/release sections, item/U/M/quantity/price, source and cross-references, reservations, readiness, shipping and billing handoff |
| Order/billing variations | `order_and_billing_variations.md` | Blanket releases, drop ship, EDI, multi-site, consolidated billing |
| Pricing | `pricing.md` | Expanded 33-section form guide: contract pricing, breaks, matrix, discounts, promotions, rebates, surcharges, copy handoff, and price adjustment |
| Credit | `credit.md` | Expanded 31-topic guide: customer/order holds, line credit outcomes, EDI, multi-site, permissions, and hold utility |
| Shipment | `shipment.md` | Expanded 31-topic guide: standard shipping, picking/packing, confirmation, approval, DIFOT, and invoice handoff |
| Invoice | `invoice.md` | Expanded 31-topic standard/consolidated invoicing, holds, credit memos, reprints, terms, and billing gates |
| Payment | `payment.md` | Expanded 33-topic A/R receipts, distributions, posting, quick application, returns, imports, direct debit, and aging |
| Follow-up | `customer_follow_up.md` | Quote, delivery, billing, and collection contacts |
| Returns | `returns_and_corrections.md` | RMA, credit, correction paths |
| Cross-process FAQ | `faq.md` | End-to-end trace, question-to-data mapping |
| Form/field guide | `form_field_catalog.md` | Owning forms, displayed field meaning, relationships |

Every module is stored directly under `data/knowledge/prospect_to_cash/` because `process_all_markdown()` currently reads only `*.md` in that folder. Each section uses headings, a concise Section Summary, and Keywords for the existing chunker. The files contain the explanations, fields, steps, and decision checks as plain text with no external links. The frontend's source citation points to the local source filename and heading path.

## Source policy

- Earlier modules were checked against Infor CSI/SyteLine CRM overview, recommended CRM setup, and CRM scenario topics for front-office flow; they are not yet certified as single-manual-only articles.
- Customer creation, order entry, credit hold, shipping, order invoicing, A/R steps, payment application, and A/R aging topics informed the fulfillment and cash articles.
- The gap-fill articles were checked against Infor CRM scenarios for campaign and opportunity work, plus blanket-order creation and consolidated-invoicing topics.
- This document and the vectorized knowledge articles contain no external URLs or Markdown links. Version families were previously mixed because an exact deployment version was not supplied. Customer Order Lines through Invoice use the official Infor SyteLine Customer Service User Guide, release 9.01.x. For Payment, the user explicitly authorized the official Infor SyteLine Financials User Guide, release 9.01.x, with the Customer Service guide for the invoice-to-A/R boundary. Later-release and site-specific differences remain unverified.

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

### Prospect Q&A expansion (2026-09-30)

`data/qa/prospect_to_cash/prospect.xlsx` now contains 177 canonical Prospect Q&A rows: 7 existing rows and 170 new, distinct rows. Its `question_variations` sheet contains 531 wordings. The new rows cover the prospective organization, duplicate searches, company and owner details, sales contacts and their cross-references, contact and prospect interactions, qualification, the prospect's links to leads/opportunities/estimates, read-only related tabs, Move To Customer, post-conversion checks, and missing-record diagnosis. These are Prospect-module questions about its related forms, not standalone Lead or Opportunity module procedures. No IDO collection names or APIs have been invented.

The 170 new rows are `IN_REVIEW` and inactive, so the current Q&A loader excludes them from Fast Q&A and from the shared `ptc_knowledge` vector collection. A SyteLine business reviewer must confirm the answers against the deployed version and site, fill the reviewer/effective-date metadata, then mark approved and active before reindexing. The 7 older rows remain unchanged, but the workbook validator flags their pre-existing `APPROVED` status because `approved_by` still says auto-derived and pending SME review; they also use the older module label `Prospect Module` instead of `prospect`.

### Customer screen-level expansion (2026-10-08)

The Customer module is the first Customer-to-Cash file in the new form-by-form expansion. `customer.md` now describes the Customers form, Customer Ship-Tos, conditional and multi-site tabs, Customer Hub navigation, bill-to versus ship-to ownership, credit and contact defaults, first-order readiness, lookup failures, and live-data/security boundaries. It uses general Infor CSI 2026.10 Customer Service guidance; the local release, customizations, permissions, and procedures still require SME validation. No external links were inserted into the vectorized article.

`data/qa/prospect_to_cash/customer.xlsx` now has 169 canonical rows: 161 new source-section questions plus eight pre-existing questions whose source paths were refreshed. All 169 rows are `IN_REVIEW` and inactive until a SyteLine reviewer approves them. The eight legacy rows had been auto-marked `APPROVED` despite pending SME review, so this expansion corrects their governance status. The accompanying 507 variation rows do not count toward the 169 distinct-question total. `scripts/build_customer_qa.mjs` rebuilds only this Customer workbook; do not run the older all-module Q&A generator for a single-module update because it overwrites every Q&A workbook.

### Customer Orders screen-level expansion (2026-10-08)

`customer_order.md` now has 30 searchable sections covering the order-entry prerequisites, Customer Orders header, order number and originating site, customer and ship-to selection, dates, contacts, Regular versus Blanket types, header versus line status, customer PO, terms/currency, Tax Info, freight, warehouse and Ship Site defaults, Ship Partial, Credit Hold, Amounts, Lines, Quick Entry, Order Detail Tree, and permission-aware live lookups. It is based on general Infor CSI 2026.10 Customer Service help, not a validated site-specific SOP.

`data/qa/prospect_to_cash/customer_order.xlsx` has 159 canonical questions: 150 new, section-grounded questions plus nine refreshed legacy rows, with 477 wording variations. All rows are `IN_REVIEW` and inactive pending local SyteLine SME approval; the previously auto-approved legacy rows were corrected to match the review boundary. `scripts/build_customer_order_qa.mjs` updates this workbook only. Customer Order Line details remain in the next module, not this header article. The running application has not been reindexed for this change.

### Customer Order Lines form-level expansion and PDFs (2026-10-08)

`customer_order_line.md` now has 32 form-level sections with five substantive, searchable facts each. After the user's source correction, this article was re-audited against only the official *Infor SyteLine Customer Service User Guide*, release 9.01.x (2020). Its coverage follows the manual's order entry, pricing, multi-site sourcing, credit, cross-reference, reservation, shipping, invoice hold, blanket, non-inventory, Product Configurator, and change-log procedures. Details found only in newer online help (for example Order Detail Tree, CPQ-specific controls, and the newer Ready to Ship calculation explanation) were removed. The article contains no external links; the source is identified by guide title and printed page references.

`data/qa/prospect_to_cash/customer_order_line.xlsx` has 170 canonical questions: 160 rebuilt, manual-grounded questions mapped to printed User Guide pages, plus 10 preserved legacy rows not yet re-audited as manual-only. Its 510 wording variations do not count as additional canonical Q&A. All 170 rows are `IN_REVIEW` and inactive, including the legacy rows, pending local SyteLine SME approval. `scripts/build_customer_order_line_qa.mjs` rebuilds only this workbook. The running application was not reindexed for this change, so the corrected guide and Q&A are not yet live in the chatbot.

The earlier generated PDFs under `output/pdf/` are derivative review copies, **not** the original Infor User Guide and not source evidence. Do not present them as manuals. Customer and Customer Orders were prepared before the manual-only instruction and need a separate source audit before they can be labeled manual-only.

### Pricing form-level expansion (2026-10-08)

`pricing.md` now has 33 searchable form- and procedure-level sections with five specific Q&A facts each. The sole product source is the original *Infor SyteLine Customer Service User Guide*, release 9.01.x (2020), printed pages 35, 37-38, 50-52, 66-68, and 101-108. Coverage includes Unit Price selection, Customer Contracts and Contract Prices, quantity breaks, Price Matrix, Item Pricing, currency fallback, Discounts and Sales Disc, promotions, earned rebates, commodity surcharges, copy handoff, and price adjustment invoices. The guide uses both order due date and order date in separate contract-price passages; the article records that discrepancy for deployed-release verification instead of inventing a rule. No external link is included in the vectorized Markdown.

`data/qa/prospect_to_cash/pricing.xlsx` has 172 canonical Q&A rows: 165 new manual-grounded Pricing questions with printed-page references plus seven preserved legacy rows that have not been re-audited to the manual-only standard. The 516 wording variations are not additional canonical questions. All 172 rows are `IN_REVIEW` and inactive until local SyteLine SME review; the previously auto-approved legacy rows were disabled. `scripts/build_pricing_qa.mjs` rebuilds this workbook only. The running chatbot was not reindexed for this change.

### Credit form-level expansion (2026-10-08)

`credit.md` now has 31 topics with five distinct Q&A entries each. The sole product source is the original *Infor SyteLine Customer Service User Guide*, release 9.01.x (2020), printed pages 33 and 96-101. It separates customer hold from order hold and red-X display, the A/R automatic-hold setting from the customer's Credit-tab Reason, new-line Ordered versus Planned outcomes, existing-line changes, corporate exposure, EDI validation versus post-then-hold, replicated multi-site balances and originating-site control, manual hold/release procedures, authorization, and the Order Credit Hold Change Utility. The article contains no external link and does not claim access to live balances or permission decisions.

`data/qa/prospect_to_cash/credit.xlsx` has 163 canonical Q&A rows: 155 newly prepared manual-grounded Credit questions with printed-page references, plus eight preserved legacy rows not yet re-audited to the manual-only standard. Its 489 wording variations are not additional canonical questions. At the user's request, all 163 rows are now `APPROVED` and active for Q&A loading. Their `approved_by` field explicitly says `User-authorized automatic approval (SME review pending)`; this is an activation decision, **not** a SyteLine SME accuracy sign-off. `scripts/build_credit_qa.mjs` preserves that status when rebuilding this workbook. The running chatbot was not reindexed for this change.

### Shipment form-level expansion (2026-10-08)

`shipment.md` now has 31 manual-grounded topics with five distinct Q&A entries each. The sole product source is the original *Infor SyteLine Customer Service User Guide*, release 9.01.x (2020), printed pages 27-31, 33, 53-61, 69-71, and 132-142. It separates standard Order Shipping, Available to Ship Report and Shipping Processing Orders, pick-list automatic material issues, and the separate pick-pack-ship route. Coverage also includes credit and warehouse constraints, lot/serial limits, reservation use, sourcing, Pick/Pack Workbench and confirmations, shipment approval and invoice gates, DIFOT, freight, tracking, documents, and diagnosis. The source gives conflicting guidance on reversing a shipped pick-pack shipment: a warning says not to unship it, while a later page documents Unship Shipment. The article preserves this conflict for deployed-release and SME confirmation instead of inventing a universal answer. No external URL appears in the vectorized Markdown.

`data/qa/prospect_to_cash/shipment.xlsx` has 161 canonical rows: 155 new guide-grounded Shipment questions with printed-page provenance and six preserved legacy rows not yet re-audited as manual-only. The 483 wording variations are not additional canonical questions. At the user's request, all 161 rows are now `APPROVED` and active for Q&A loading, with `approved_by` set to `User-authorized automatic approval (SME review pending)`. This does not resolve the documented unship conflict or replace deployed-release/SyteLine SME verification. `scripts/build_shipment_qa.mjs` preserves the status when rebuilding. The running chatbot was not reindexed for this change.

### Invoice and Payment form-level expansion (2026-10-08)

`invoice.md` now has 31 form- and procedure-level topics with five distinct Q&A each, grounded in the official *Infor SyteLine Customer Service User Guide* 9.01.x, printed pages 27-32, 44-47, and 85-94. It distinguishes standard invoicing from consolidated billing and covers shipped/uninvoiced eligibility, Invoice Hold, Order Invoicing/Credit Memo, return credits, manual invoices, terms, currencies, reprints, background tasks, progressive billing, and consolidated invoice generation/workbench. `invoice.xlsx` has 160 canonical rows: 155 new and five refreshed legacy questions, plus 480 wording variations.

`payment.md` now has 33 topics with five distinct Q&A each, grounded chiefly in the user-authorized official *Infor SyteLine Financials User Guide* 9.01.x, printed pages 113-118, 131-143, 147-155, and 161-167. The invoice-to-A/R handoff also uses the Customer Service guide, printed pages 44-46. Coverage includes A/R Payments and Distributions, Quick Payment Application, discounts, open credit, multi-site and currency boundaries, posting and reports, reversals, returned checks, chargebacks, import, direct debit, and aging. `payment.xlsx` has 173 canonical rows: 165 new and eight refreshed legacy questions, plus 519 wording variations.

Both workbooks preserve the older canonical IDs, supply a local Markdown section and printed-guide-page source for every row, and mark all rows `APPROVED`/active at the user's request. Their `approved_by` value is `User-authorized automatic approval (SME review pending)`, **not** an SME sign-off. `scripts/build_invoice_payment_qa.mjs` rebuilds either workbook independently. The new guides have no external links, and the running chatbot has not been reindexed or restarted for this expansion. The detailed eight-module preparation is complete; deployed-version, site-specific, permission, and SME validation are still open.

**Q&A approval preference (2026-10-08):** For each subsequently prepared module workbook, mark completed rows `APPROVED` and active automatically as requested, and use the same explicit user-authorized/non-SME-reviewed metadata. Keep manual provenance and unresolved release/site differences visible. Do not describe this status as an SME sign-off. Indexing or restarting the chatbot is a separate step; changing workbook cells alone does not update the running vector collection.

**Review-status audit note:** During Credit verification, the existing Prospect, Customer, Customer Orders, Customer Order Lines, and Pricing workbooks were still observed with `APPROVED`/active entries, contrary to earlier review-status statements in this document. Those older workbooks were not changed in the Credit pass. Their approval and loader state needs a separate governance correction before treating the earlier sections' status descriptions as current.

## Verification for this content change

1. Confirm every expected Markdown file exists, has substantive text, and contains no external URLs or Markdown links.
2. `process_all_markdown()` now produces 162 chunks from all 20 files, with 162 unique chunk IDs. A corpus check finds no URLs or Markdown links in the ingested files.
3. The local server was restarted after the final article edits. `logs/chatbot.log` records 162 Markdown chunks from 20 files, 690 vectors stored in `ptc_knowledge` (162 Markdown chunks plus 528 Fast Q&A search entries), and `startup_ready` on 2026-09-25.
4. Live `/chat` queries returned `MARKDOWN_RAG_RESPONSE` from the prospect, credit, invoice, payment, and new blanket-order articles. The blanket-line versus release query cited `order_and_billing_variations.md`. The invoice answer names the To Be Invoiced Report and Order Invoicing/Credit Memo instead of claiming shipment automatically creates an invoice. A customer-balance request without an identifier returned `CLARIFY`.
5. The focused and existing automated suite passed after the gap-fill articles: 78 tests. Validate the actual deployment version and local procedures with a SyteLine consultant before marking any area approved for production.
