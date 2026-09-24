# Customer Order Line and Release Module

## Meaning and relationship to header

A Customer Order Line describes an item or service sold under a Customer Orders header. Lines and blanket releases carry their own item, quantity, unit, price, due date, source, site, and fulfillment state. The header's status does not replace the line status. A blanket line can have multiple releases, each with its own scheduled ship date.

**Section Summary:** Diagnose item, quantity, price, source, and status on the individual line or release.

### Keywords
customer order line, line release, blanket release, CO line

## Enter and validate a line

1. Open the correct Customer Orders header and select Lines.
2. Enter or select the line number and item; confirm description and the intended shipping site.
3. Enter Qty Ordered and verify U/M, unit price, line discount, tax treatment, and due date.
4. Review source or cross-reference where supply will come from (inventory, job, purchase order, transfer, or a site-specific path).
5. Review reservation, lot/serial, configuration, drop-ship, and invoice-hold options only if applicable.
6. Save and check the resulting line status, warnings, credit hold, totals, and available-to-ship information.

**Section Summary:** A saved line still needs review of credit, sourcing, availability, and pricing.

### Keywords
add order line, Qty Ordered, U/M, due date, item, source

## Planned, Ordered, and credit checks

Infor documentation describes an over-limit line remaining Planned when Allow Over Credit Limit is off; other settings can place an order on credit hold. Planned lines do not behave like booked, shippable demand. The Change CO Line/Release Status Utility can move selected lines/releases from Planned to Ordered and performs credit checks. Only an authorized operator should perform that change.

**Section Summary:** Review why a line is Planned before changing it to Ordered.

### Keywords
Planned line, Ordered line, Allow Over Credit Limit, Change CO Line/Release Status

## Availability, partials, and cross-references

Ready to Ship depends on supply reference and completion/receipt. The Available to Ship Report may differ from the line's Ready quantity because it considers competing order demand while processing. Check the shipping site's inventory, due date, reservations, source cross-reference, and shipped quantity before promising availability. A credit-held order cannot create a new cross-reference; an existing cross-reference remains.

**Section Summary:** Available inventory and a line's ready quantity are related but can differ.

### Keywords
ready to ship, available to ship, partial shipment, cross-reference, supply

## Price changes and invoice hold

Changing line quantity does not always refresh Unit Price automatically. Confirm whether the current price should remain or be recalculated under the customer's agreement and the site's pricing rules. Invoice Hold can keep an otherwise shipped line from being invoiced. A shipped or invoiced line requires a controlled correction path; do not promise that it can be freely deleted or edited.

**Section Summary:** Recheck price after quantity changes and invoice hold before billing.

### Keywords
line price changed, Invoice Hold, edit shipped line, line troubleshooting

## Line quantities and dates

| Quantity/date | Meaning to verify |
| --- | --- |
| Qty Ordered | Customer demand entered for this line or release. |
| Ready to Ship | Supply presently indicated as ready on the line; it can differ from a report that allocates inventory across orders. |
| Shipped quantity | Quantity in posted shipment transactions. |
| Invoiced quantity | Quantity already billed; compare with shipped quantity. |
| Due date | Target for the line; do not confuse it with order date, ship date, or invoice due date. |

An order with several lines may have one line Planned, one Ordered, and one partially shipped. Always name the line/release in a precise answer. If quantities differ, check unit of measure, prior shipments, reservations, and any return or cancellation transaction.

**Section Summary:** The line/release is the right level for quantity and delivery questions.

### Keywords
Qty Ordered, Ready to Ship, shipped quantity, invoiced quantity, line due date

## Line-level investigation sequence

Read the header and selected line; confirm item, U/M, quantity, price, due date, shipping site, source, and status. Next inspect credit hold and invoice hold separately. Then compare available-to-ship, shipment, and invoice records. If the line was copied from an estimate or sourced to a job, purchase order, or transfer, inspect the cross-reference and its progress. Record the exact error before changing status or price.

**Section Summary:** Trace a line from demand through supply, shipment, and billing.

### Keywords
line troubleshooting, cross-reference, invoice hold, source
