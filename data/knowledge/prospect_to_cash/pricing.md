# Pricing and Discount Module

## Where pricing is reviewed

Pricing is determined for Estimate Lines and Customer Order Lines, with inputs that can include customer contracts, item pricing, customer/item price codes, promotions, quantity breaks, currency, and discounts. Infor documents an ordered price-selection process; there is no safe universal statement that one price list always wins. Quoted price, current calculated price, and invoiced price may differ after revisions or timing changes. [Infor calculating unit price](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144030727.html)

**Section Summary:** Review the pricing source and effective date for the specific customer, item, and line.

### Keywords
unit price, price list, customer contract price, promotion, price code

## Price-check sequence for a line

1. Confirm customer, ship-to, site, item, U/M, currency, quantity, and due date.
2. Review any customer contract or customer-item agreement and its effective dates.
3. Review promotion pricing and item/customer price-code rules configured in the site.
4. Check line and order discounts, plus surcharges, freight, and tax; these are different components of the total.
5. Compare the calculated unit price with the approved quotation or customer purchase order.
6. If quantity or date changed, verify whether the system recalculated price or retained the original. Resolve a discrepancy with the pricing owner before shipping or invoicing. [Infor calculating unit price](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144030727.html) [Infor Customer Order Lines](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/ucm1528917030675.html)

**Section Summary:** Identify the exact price input and compare it with the customer's agreed terms.

### Keywords
price discrepancy, discount, quantity break, effective date, reprice

## Quote-to-order price handoff

Copy Orders and Estimates can move an accepted estimate into an order, but calculated amounts such as tax may be recalculated and some fields come from current customer or tax setup. Check every copied line, unit price, discount, freight, tax, currency, and total. A copied order should not be represented as an exact financial snapshot of the quote without verification. [Infor copying orders and estimates](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454144031054.html)

**Section Summary:** Reconcile quote and order pricing after copying.

### Keywords
estimate price, quote to order, copied order price, tax recalculation

## Pricing permissions and current amounts

This Markdown explains how to investigate pricing. It contains no customer's confidential contract price and no live unit-price result. For “What price does this customer get today?”, Phase 4 must query approved SyteLine data with customer, item, quantity, date, site, and user permissions. The approved pricing IDO/API and override roles are **[NEEDS SYTELINE CONFIRMATION]**.

**Section Summary:** Live customer-specific pricing needs an authorized, current ERP lookup.

### Keywords
live price, customer-specific price, IDO, pricing permission
