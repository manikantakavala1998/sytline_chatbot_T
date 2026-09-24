# Pricing and Discount Module

## Where pricing is reviewed

Pricing is determined for Estimate Lines and Customer Order Lines, with inputs that can include customer contracts, item pricing, customer/item price codes, promotions, quantity breaks, currency, and discounts. Infor documents an ordered price-selection process; there is no safe universal statement that one price list always wins. Quoted price, current calculated price, and invoiced price may differ after revisions or timing changes.

**Section Summary:** Review the pricing source and effective date for the specific customer, item, and line.

### Keywords
unit price, price list, customer contract price, promotion, price code

## Price-check sequence for a line

1. Confirm customer, ship-to, site, item, U/M, currency, quantity, and due date.
2. Review any customer contract or customer-item agreement and its effective dates.
3. Review promotion pricing and item/customer price-code rules configured in the site.
4. Check line and order discounts, plus surcharges, freight, and tax; these are different components of the total.
5. Compare the calculated unit price with the approved quotation or customer purchase order.
6. If quantity or date changed, verify whether the system recalculated price or retained the original. Resolve a discrepancy with the pricing owner before shipping or invoicing.

**Section Summary:** Identify the exact price input and compare it with the customer's agreed terms.

### Keywords
price discrepancy, discount, quantity break, effective date, reprice

## Quote-to-order price handoff

Copy Orders and Estimates can move an accepted estimate into an order, but calculated amounts such as tax may be recalculated and some fields come from current customer or tax setup. Check every copied line, unit price, discount, freight, tax, currency, and total. A copied order should not be represented as an exact financial snapshot of the quote without verification.

**Section Summary:** Reconcile quote and order pricing after copying.

### Keywords
estimate price, quote to order, copied order price, tax recalculation

## Pricing permissions and current amounts

This Markdown explains how to investigate pricing. It contains no customer's confidential contract price and no live unit-price result. For “What price does this customer get today?”, Phase 4 must query approved SyteLine data with customer, item, quantity, date, site, and user permissions. The approved pricing IDO/API and override roles are **[NEEDS SYTELINE CONFIRMATION]**.

**Section Summary:** Live customer-specific pricing needs an authorized, current ERP lookup.

### Keywords
live price, customer-specific price, IDO, pricing permission

## Explain a price difference without guessing

Compare the same customer, item, site, currency, unit of measure, quantity, and effective/due date across the estimate, order line, and invoice. Check a customer contract or promotion, the applicable item/customer price-code rule, line discount, order discount, freight, surcharge, and tax separately. If the unit price changed after a quantity update, inspect whether the price was recalculated or intentionally retained. Keep the agreed quote or customer PO beside the calculation so the discrepancy has a reference.

| Amount | What it represents |
| --- | --- |
| Unit Price | Price per unit before some downstream charges or discounts. |
| Extended line amount | Quantity multiplied by the applicable line price, subject to discount rules. |
| Order discount | Commercial adjustment at header level where configured. |
| Tax, freight, surcharge | Additional components with their own setup and timing. |
| Invoice total | Final billed amount after the invoicing process; check the posted document. |

The precise calculation order is configuration-dependent; do not assert a numeric price from this article. A customer-specific price is a live, potentially restricted fact.

**Section Summary:** Match all pricing inputs and separate base price, discounts, and charges.

### Keywords
price variance, Unit Price, extended price, order discount, tax, invoice total
