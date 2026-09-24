# Estimate Module

## Meaning, status, and forms

An estimate holds the proposed items, quantities, price, terms, and dates used to quote a prospect or customer. Use Estimates for the header and Estimate Lines for item detail; Estimates Quick Entry is an alternate entry form. Infor describes header states Working, Quoted, Planned, and History. Quoted means the estimate has been used to quote a price; it does not mean customer acceptance.

**Section Summary:** An estimate is a proposal record; its status must not be confused with an order or payment.

### Keywords
estimate, Estimates form, Working, Quoted, Planned, History

## Prepare the header

1. Create an Estimates record and accept or enter its estimate number.
2. Review Quote Date, Expiration Date, and Status; defaults come from system parameters.
3. Link the relevant prospect or customer and contact where available; record the customer's quote reference if supplied.
4. Review terms, currency, tax information, and order discount shown by the site.
5. Save the header, then open Estimate Lines.

**Section Summary:** A valid header establishes quote identity, validity period, party, and commercial terms.

### Keywords
create estimate, quote date, expiration date, terms, tax code

## Prepare and review lines

For each Estimate Line, review line number, item, Qty Ordered, U/M, status, Sales Disc, Unit Price, expected delivery, and sourcing details where shown. Inventoried and non-inventoried items can be used. If the line quantity changes, SyteLine may ask whether to recalculate price; record the answer because the quoted price may otherwise stay as it was. A line can be cross-referenced to an estimate job or project when that workflow is enabled. Review totals, taxes, margins, and feasibility before issuing a quote.

**Section Summary:** Price and delivery must be reviewed at line level, especially after quantity changes.

### Keywords
Estimate Lines, item, quantity, U/M, Sales Disc, Unit Price, estimate job

## Handoff after acceptance

Use Copy Orders and Estimates to create an order from an accepted estimate where the site uses that path. Copying does not preserve every source value: historic values and calculated taxes may be recalculated, and some values come from current customer or tax configuration. Review the new order header and every line before treating it as booked demand.

**Section Summary:** Copying an estimate begins order entry; verify recalculated fields and new order status.

### Keywords
copy estimate to order, accepted estimate, conversion, recalculated tax

## Header and line data dictionary

| Location | Data | Why it is checked |
| --- | --- | --- |
| Estimates header | Estimate number, party, contact | Connects proposal to the right prospect or customer. |
| Estimates header | Quote Date, Expiration Date, Status | Shows when the proposal applies and whether it is Working, Quoted, Planned, or History. |
| Estimates header | Terms, tax, order discount, currency | Establishes commercial assumptions for the quote. |
| Estimate Lines | Item, description, Qty Ordered, U/M | Identifies each proposed good or service and quantity. |
| Estimate Lines | Unit Price, Sales Disc, extended amount | Explains the line's proposed price. |
| Estimate Lines | Source, estimate job/project reference | Shows optional supply or costing work used to prepare the proposal. |

An estimate total should be reconciled to its individual lines plus applicable charges and tax. The displayed quote may differ if the report suppresses price, if a line is omitted, or if the estimate was revised after the document was sent. Use the saved estimate and the actual customer-facing report when investigating a dispute.

**Section Summary:** Header terms and line detail together define the proposal.

### Keywords
estimate header fields, estimate line fields, quote total, status

## Estimate review before quotation

Confirm the correct party, contact, item descriptions, quantities, unit measures, due dates, and pricing. Check whether non-inventory items or configured items require additional descriptions or sourcing work. Review discount and tax treatment and ask the responsible estimator to validate any job/project cost assumptions. If a quantity was edited, inspect the saved Unit Price because the user may have chosen not to recalculate it. Set an expiration that reflects the approved offer and issue the report only after the commercial details are accepted internally.

**Section Summary:** Validate business, pricing, and fulfillment assumptions before sending a quote.

### Keywords
estimate review, configured item, quantity change, price recalculation
