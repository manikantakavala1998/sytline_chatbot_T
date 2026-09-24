# Customer Order

## Overview

A Customer Order is the confirmed request from a Customer to purchase goods or services. It is
created after a Quotation has been accepted, and it drives everything downstream: pricing and
credit checks, shipment, invoicing, and payment.

### Keywords
customer order, sales order, order entry, confirmed order

---

## Creating a Customer Order

1. Open the Customer Orders form and select New.

2. Choose the Customer. The system pulls in the customer's default ship-to address, payment
   terms, and price list automatically.

3. Add one or more Order Lines, specifying the item, quantity, and requested Due Date for each
   line.

4. Review the calculated pricing on each line — see the Pricing section below for how this is
   determined.

5. Release the order once all lines are complete and any Credit Hold has been cleared.

**Section Summary:** Creating a Customer Order means selecting a customer, adding order lines,
confirming pricing, and releasing the order once credit checks pass.

### Keywords
create customer order, new order, release order

---

## Editing or Cancelling an Order

An order can be edited or cancelled only while it is still in an unreleased or unshipped state.
Once a line has shipped, that line can no longer be edited or cancelled — a return process is
required instead. Look for the Edit or Cancel option on the same Customer Orders form; if it is
greyed out, the order has likely already progressed past the point where changes are allowed.

**Section Summary:** Orders can be freely edited or cancelled before shipment; after shipment, use
the returns process instead.

### Keywords
edit customer order, cancel order, change order

---

## Troubleshooting: Order Won't Release

If a Customer Order will not release, check the following in order:

1. **Credit Hold** — the customer's outstanding balance may exceed their Credit Limit. The order
   stays on hold until the hold is released by an authorized user.
2. **Missing required fields** — every order line needs an item, quantity, and price before it can
   release.
3. **Site mismatch** — the order's site must match a site the current user has access to.

If none of these resolve it, contact the Accounts Receivable team with the order number and the
exact error message shown.

**Section Summary:** Most release failures come from a Credit Hold, a missing required field, or a
site mismatch — check those three before escalating.

### Keywords
order won't release, credit hold, troubleshooting
