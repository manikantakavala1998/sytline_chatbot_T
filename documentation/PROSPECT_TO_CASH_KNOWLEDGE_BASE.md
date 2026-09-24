# Prospect-to-Cash Knowledge Base — General SyteLine Guidance

## Purpose and status

This is the pre-Phase-4 knowledge expansion requested on 2026-09-24. It covers the CRM-to-cash business lifecycle with retrieval-ready Markdown, one module at a time. The 14 rollout-stage files from `data/qa/prospect_to_cash/` now have matching Markdown counterparts; four additional files cover CRM setup, field/form navigation, follow-up, and returns. The five original starter articles were replaced where they overstated configurable behavior.

The content is **general Infor CSI/SyteLine guidance**, based on public Infor help in the 9.01.x, 10.x, and 2026.x families. It has **not** been validated against the user's exact SyteLine release, site setup, custom forms, security rules, or approved IDOs. It is suitable as a version-aware draft reference and needs consultant/business approval before production use. It does not train or fine-tune an SLM/LLM: the Markdown is chunked and embedded into the RAG knowledge index at application startup. Phase 7 owns model training.

## Module inventory and process coverage

| Stage | File | Main coverage |
| --- | --- | --- |
| CRM setup | `crm_setup.md` | Status/source setup, form map, technical mapping boundary |
| Prospect | `prospect.md` | Company capture, contacts, interactions, conversion |
| Lead | `lead.md` | Interest, qualification, status, follow-up, opportunity link |
| Opportunity | `opportunity.md` | Pipeline fields, tasks, forecasting, win/loss |
| Estimate | `estimate.md` | Header, lines, status, pricing and order handoff |
| Quotation | `quotation.md` | Customer-facing proposal, issue, revision, acceptance |
| Customer | `customer.md` | Bill-to, ship-to, terms, credit and CRM data |
| Customer Order | `customer_order.md` | Header, order entry, status, exceptions |
| Customer Order Line | `customer_order_line.md` | Item/quantity, source, pricing, availability, line states |
| Pricing | `pricing.md` | Price sources, discounts, quote-to-order reconciliation |
| Credit | `credit.md` | Customer/order holds, parameters, diagnosis, multi-site |
| Shipment | `shipment.md` | Picking, shipping, partials, error diagnosis |
| Invoice | `invoice.md` | Shipped-not-invoiced, invoice process, credit memo |
| Payment | `payment.md` | A/R payments, distributions, aging, collection review |
| Follow-up | `customer_follow_up.md` | Quote, delivery, billing, and collection contacts |
| Returns | `returns_and_corrections.md` | RMA, credit, correction paths |
| Cross-process FAQ | `faq.md` | End-to-end trace, question-to-data mapping |
| Form/field guide | `form_field_catalog.md` | Owning forms, displayed field meaning, relationships |

Every module is stored directly under `data/knowledge/prospect_to_cash/` because `process_all_markdown()` currently reads only `*.md` in that folder. Each section uses headings, a concise Section Summary, and Keywords for the existing chunker. The frontend's source citation points to source filename and heading path.

## Source policy

- The Markdown paraphrases [Infor CRM overview](https://docs.infor.com/csi/10.x/en-us/csbiolh/sales_crm_user_cl_sl/mergedprojects/sl_custvend/other/overview/crm_overview.html), [recommended CRM setup](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144069328.html), and [CRM scenarios](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144070576.html) for front-office flow.
- It uses [customer creation](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/creating_a_customer.html), [order entry](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html), [credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html), [shipping](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html), and [order invoicing](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html) for fulfillment.
- It uses [A/R steps](https://docs.infor.com/csi/10.x/en-us/csbiolh/financials_user_cl_sl/lsm1454143881752.html), [quick payment application](https://docs.infor.com/csi/latest/en-us/csbiolh/financials_user_cl_sl/lsm1454143884482.html), and [A/R aging](https://docs.infor.com/csi/latest/en-us/csbiolh/financials_user_cl_sl/lsm1454143885762.html) for cash collection.
- Module sections link directly to their supporting Infor help. Version families are mixed because an exact deployment version was not supplied; release-specific differences must be checked before operational use.

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

The exact form identifiers, IDO collections, properties, methods, role permissions, field/row filters, and audit requirements remain **[NEEDS SYTELINE CONFIRMATION]**. The current Fast Q&A `.xlsx` files are still starter/sample content and require a separate business review. Their placeholder `PTC Training Guide` rows are excluded at load time even though the existing files mistakenly mark them APPROVED; future generated sample rows are DRAFT. Newly added Markdown becomes visible to the running RAG index only after an application restart or explicit reindex; the index is constructed at startup. Before production activation, apply the per-domain acceptance checklist in the master prompt §71, including version, citations, permissions, and business UAT.

## Verification for this content change

1. Confirm every expected Markdown file exists and links use reachable Infor pages.
2. Run `process_all_markdown()` and confirm each file yields nonempty chunks with unique IDs.
3. Restart the app to rebuild BM25/vector indexes and check `startup_ingestion_begin` and RAG index logs in `logs/chatbot.log`.
4. Query representative definitions and process questions for each module; inspect source filename/path and ensure no sample Q&A answer overrides a corrected article.
5. Validate the actual deployment version and local procedures with a SyteLine consultant before marking any area approved for production.
