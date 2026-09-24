# Prospect-to-Cash Cross-Process Guide

## End-to-end map and alternate paths

A common path is contact/prospect → lead → opportunity → estimate/quote → customer → customer order and lines → fulfillment/shipment → invoice → A/R payment and follow-up. This is a navigation map, not a rule requiring every record. A lead can belong to an existing customer, an estimate can exist without a prior lead, and one order can have multiple lines, shipments, invoices, or payments. Returns and credit memos create additional branches.

**Section Summary:** Records form a linked commercial lifecycle with optional and repeated steps.

### Keywords
prospect to cash, end to end, CRM to cash, order to cash, lifecycle

## Trace one customer request through the forms

1. Find the party on Prospects or Customers; confirm contact and site.
2. Find the Lead and Opportunity, then inspect status, owner, tasks, and projected close date.
3. Find the linked Estimate and its lines; check quote version, validity, prices, and customer response.
4. If accepted, find the Customer and Customer Orders record; compare customer, ship-to, item, quantity, dates, and terms.
5. Inspect each Customer Order Line for line status, hold, availability, and shipped quantity.
6. Inspect shipment transactions and invoice history; reconcile ordered, shipped, and invoiced quantities.
7. Inspect A/R open items, payment applications, credit memos, and aging to determine the remaining balance.
8. Record the latest customer interaction and unresolved next action.

**Section Summary:** Follow identifiers and quantities from party to invoice and A/R rather than treating one status as the whole answer.

### Keywords
trace order, trace quote, trace invoice, related records, reconciliation

## How to answer common user questions

| Question | Knowledge answer versus live answer |
| --- | --- |
| “What is a prospect/lead/order line?” | Explain the record from this Markdown and cite its source. |
| “How do I create an order?” | Give general steps; ask for the current form or version if a control differs. |
| “What does Due Date mean on this line?” | Use the line and form context; distinguish requested, due, ship, and invoice dates. |
| “Where is order CO123?” | Requires an authorized live order and shipment lookup. |
| “What is this customer's balance?” | Requires an authorized live A/R lookup; do not infer it from a document. |
| “Why is the order held?” | Check the actual hold flags, reason, and credit configuration; general credit guidance alone cannot identify the cause. |
| “Release the order” | A future approved action with user confirmation and permission; static knowledge cannot execute it. |

**Section Summary:** Static knowledge explains process; transaction-specific answers require current, permitted ERP data.

### Keywords
static knowledge, live data, customer balance, order status, chatbot route

## What must be known before a precise answer

For an ambiguous request, ask for the entity and identifier (prospect, customer, opportunity, estimate, order, line/release, shipment, invoice, payment), site, and intended action. For field help, use form, tab, field, and any visible record context. For financial or security-sensitive questions, require a current authorized lookup. Do not quote an unconfirmed IDO/property or guess a customer's facts. The exact connector mappings are **[NEEDS SYTELINE CONFIRMATION]**.

**Section Summary:** Resolve the record and screen context before giving a specific workflow or factual status.

### Keywords
clarification, form context, record ID, site, permissions

## Record relationships and identifiers

A prospect or customer identifies an organization; a sales contact identifies a person. A lead records interest; an opportunity records a possible deal; an estimate records a proposed commercial offer. A customer order has a header and one or more lines/releases. A line may have several shipment and invoice events over time, and an invoice may have several payments or credits. Keep those identifiers distinct when tracing a case. A customer PO is the customer's external reference; the SyteLine order number is the internal transaction reference.

**Section Summary:** Link the correct organization, deal, order, line, shipment, invoice, and payment records.

### Keywords
prospect ID, opportunity number, estimate number, customer PO, order number, invoice number

## Questions that need different answers

“How do I create a Customer Order?” is a help/process question: explain the general Customer Orders and Customer Order Lines steps. “Has order CO123 shipped?” is a live-data question: check authorized shipment transactions. “Why can't this order ship?” needs actual hold, status, site, and availability data before deciding. “Show overdue invoices for this customer” needs an authorized A/R query with customer and as-of date. “Create a credit memo” or “release this order” is an action request and requires an explicitly approved future action workflow. The same nouns can appear in all five requests, so classify the intended operation as well as the module.

**Section Summary:** Definition, procedure, diagnosis, live lookup, and action are distinct intents.

### Keywords
help intent, live data intent, action intent, order status, overdue invoice
