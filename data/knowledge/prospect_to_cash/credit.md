# Credit

## Credit Limit

Every Customer has a Credit Limit — the maximum outstanding balance (open invoices plus
unshipped, unpaid orders) they are allowed to carry. Credit Limit is set on the Customer record by
the Accounts Receivable team and is reviewed periodically based on payment history.

### Keywords
credit limit, outstanding balance, customer credit

---

## Credit Hold

A Credit Hold is applied automatically to a Customer Order when releasing it would push the
customer's outstanding balance above their Credit Limit. A held order cannot ship until the hold
is cleared.

**Exception:** orders for existing, already-invoiced backorder lines are not re-checked against
Credit Limit a second time — only new order value is checked. This prevents a customer from being
blocked from receiving goods they have already been invoiced for.

**Section Summary:** Credit Hold blocks new orders that would exceed the credit limit, but does
not re-block already-invoiced backorder shipments.

### Keywords
credit hold, order hold, credit block

---

## Releasing a Credit Hold

Only a user with Accounts Receivable authorization can release a Credit Hold. Releasing requires
either (a) the customer's balance dropping back under the limit through a payment, or (b) a
manual, documented override approved by an AR supervisor. Every manual override must include a
reason code — undocumented overrides are flagged in the weekly credit exceptions report.

**Section Summary:** Credit holds clear automatically once balance drops under the limit, or via a
documented manual override from an authorized AR user.

### Keywords
release credit hold, credit override, AR authorization
