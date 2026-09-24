# Invoice

## Overview

An Invoice is the billing document issued to a Customer after goods or services are delivered. It
states the amount owed, the due date for payment, and references the Shipment and Customer Order
it was generated from.

### Keywords
invoice, billing, amount owed

---

## When Invoices Are Generated

Invoices are generated automatically once a Shipment is confirmed — there is no manual invoice
creation step for standard orders. Service-only order lines (no physical shipment) invoice
immediately upon order release instead of waiting for a shipment event.

**Section Summary:** Shipped lines invoice on shipment confirmation; service lines invoice on
order release.

### Keywords
invoice generation, auto invoice, service line invoice

---

## Correcting an Invoice

Invoices cannot be edited directly once issued. To correct an error, a credit memo is issued
against the original invoice to reverse the incorrect amount, followed by a new, corrected invoice
if the customer still owes a balance. Contact Accounts Receivable to initiate a credit memo —
this is not a self-service action.

**Section Summary:** Invoice corrections go through a credit memo plus a new invoice, not a direct
edit.

### Keywords
correct invoice, credit memo, invoice error
