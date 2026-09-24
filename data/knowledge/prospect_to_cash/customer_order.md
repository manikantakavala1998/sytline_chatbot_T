# Customer Order Module

## Purpose and form ownership

Customer Orders holds the order header: customer, ship-to, order type and status, dates, terms, shipping and billing defaults, and credit hold information. Customer Order Lines holds the actual items and releases. The standard order-entry path is create header, save it, add lines, check credit and availability, ship, then invoice. A quote may be copied to an order, but a quote is not itself an order.

**Section Summary:** The order header controls the commercial transaction; lines specify demand.

### Keywords
customer order, Customer Orders form, order header, sales order, order entry

## Create and review an order

1. Search existing orders and customer purchase order references to avoid duplicates.
2. Create a record on Customer Orders, select customer and ship-to, and fill required header values shown by the site.
3. Review order type, status, order/requested dates, customer PO, bill-to, ship-to, terms, currency, tax, freight, and salesperson when present.
4. Save the header, then open Customer Order Lines and add line/releases.
5. Review unit price, due date, shipping site, available quantity, credit status, and order totals. Use Get ATP/CTP or availability tools if those features are enabled.
6. Print an Order Verification Report when an acknowledgement is needed; shipment and invoicing are later steps. Customer Orders Quick Entry is an alternate entry path.

**Section Summary:** Save the header, add lines, then verify commercial, availability, and credit information.

### Keywords
create order, new Customer Order, customer PO, ship-to, order verification

## Status, holds, and changes

Order and line statuses are separate. Infor uses Planned and Ordered line states, and a credit check can leave a line Planned or put an order on hold depending on settings. A customer-level hold and order-level hold can both block shipping. Do not tell a user to simply “release the order” as a universal workflow: identify the current status, hold reason, error, line, and local authorization first. For a submitted change, recheck price, dates, tax, allocation, and downstream shipment or invoice history.

**Section Summary:** Status and hold are different controls; explain the actual reason before proposing a change.

### Keywords
order status, Planned, Ordered, credit hold, release order, change order

## Order types and exceptions

Regular and blanket orders differ. Blanket orders use blanket lines and releases with separate ship dates. An order may also have multiple shipping sites, drop-ship lines, EDI origin, letter-of-credit requirements, or shipment approval. These are optional or configuration-dependent paths. Identify the order type and enabled features before giving specific steps.

**Section Summary:** Order type and options determine the relevant line, credit, shipment, and invoice workflow.

### Keywords
blanket order, order release, EDI order, drop ship, multi-site

## Troubleshoot an order that cannot progress

Check the exact error and order number; current header/line status; customer and order credit hold; missing or invalid customer, ship-to, item, quantity, price, due date, site, tax, or terms; availability and cross-referenced supply; letter-of-credit and shipment approval settings; and whether the line already shipped or invoiced. The Order Entry Exception Report can help identify processing errors. Do not assume a credit hold is the cause merely because an order will not ship.

**Section Summary:** Diagnose the exact order and line state before changing it or escalating.

### Keywords
order won't process, order won't release, order exception, cannot ship

## Header fields and downstream consequences

| Header data | Downstream effect to review |
| --- | --- |
| Customer and bill-to | Determines the party charged and defaults for terms, currency, and tax. |
| Ship-to and shipping site | Determines delivery location and which site must fulfill the order. |
| Order number and customer PO | Connects customer correspondence to order and invoice history. |
| Order type and Status | Determines whether regular or blanket line/release processing applies. |
| Dates | Used for customer request, planning, promised delivery, and reporting. |
| Terms, freight, tax, discount | Affect price and billing; verify on the saved order. |
| Credit Hold and Ship Partial | Affect whether shipping can proceed or the order appears ready. |

If the order was copied from an estimate, check current customer and tax defaults. A matching item list is not sufficient evidence that the new order retained every quote term.

**Section Summary:** Header fields direct fulfillment and billing even when the lines are correct.

### Keywords
Customer Orders fields, customer PO, order type, ship-to, Ship Partial

## Order state questions and what to inspect

For “Is the order booked?”, check the header and line/release statuses. For “Can it ship?”, inspect customer and order holds, line status, available quantity, shipping site, and any letter-of-credit condition. For “Has it shipped?”, use shipment transactions and shipped quantity, not the existence of an order. For “Has it been invoiced?”, use invoice history or A/R transaction. For “Can I cancel it?”, inspect whether the quantity has shipped or invoiced and follow the site's correction process. Every answer about a named order requires an authorized live lookup.

**Section Summary:** Booking, shipping, invoicing, and payment are separate evidence checkpoints.

### Keywords
order booked, can ship, order shipped, order invoiced, cancel order
