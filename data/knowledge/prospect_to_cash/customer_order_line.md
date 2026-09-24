# Customer Order Line and Release Module

## Meaning and relationship to header

A Customer Order Line describes an item or service sold under a Customer Orders header. Lines and blanket releases carry their own item, quantity, unit, price, due date, source, site, and fulfillment state. The header's status does not replace the line status. A blanket line can have multiple releases, each with its own scheduled ship date. [Infor Customer Order Lines](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/forms/cotopics/order_line_maintenance.html) [Infor blanket lines](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/nol1528915094338.html)

**Section Summary:** Diagnose item, quantity, price, source, and status on the individual line or release.

### Keywords
customer order line, line release, blanket release, CO line

## Enter and validate a line

1. Open the correct Customer Orders header and select Lines.
2. Enter or select the line number and item; confirm description and the intended shipping site.
3. Enter Qty Ordered and verify U/M, unit price, line discount, tax treatment, and due date.
4. Review source or cross-reference where supply will come from (inventory, job, purchase order, transfer, or a site-specific path).
5. Review reservation, lot/serial, configuration, drop-ship, and invoice-hold options only if applicable.
6. Save and check the resulting line status, warnings, credit hold, totals, and available-to-ship information. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor Customer Order Lines](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/ucm1528917030675.html)

**Section Summary:** A saved line still needs review of credit, sourcing, availability, and pricing.

### Keywords
add order line, Qty Ordered, U/M, due date, item, source

## Planned, Ordered, and credit checks

Infor documentation describes an over-limit line remaining Planned when Allow Over Credit Limit is off; other settings can place an order on credit hold. Planned lines do not behave like booked, shippable demand. The Change CO Line/Release Status Utility can move selected lines/releases from Planned to Ordered and performs credit checks. Only an authorized operator should perform that change. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor line status utility](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/hyn1528903077630.html)

**Section Summary:** Review why a line is Planned before changing it to Ordered.

### Keywords
Planned line, Ordered line, Allow Over Credit Limit, Change CO Line/Release Status

## Availability, partials, and cross-references

Ready to Ship depends on supply reference and completion/receipt. The Available to Ship Report may differ from the line's Ready quantity because it considers competing order demand while processing. Check the shipping site's inventory, due date, reservations, source cross-reference, and shipped quantity before promising availability. A credit-held order cannot create a new cross-reference; an existing cross-reference remains. [Infor quantity ready](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/fields/r/ready_order_line_maintenance.html) [Infor Customer Order Lines](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/ucm1528917030675.html)

**Section Summary:** Available inventory and a line's ready quantity are related but can differ.

### Keywords
ready to ship, available to ship, partial shipment, cross-reference, supply

## Price changes and invoice hold

Changing line quantity does not always refresh Unit Price automatically. Confirm whether the current price should remain or be recalculated under the customer's agreement and the site's pricing rules. Invoice Hold can keep an otherwise shipped line from being invoiced. A shipped or invoiced line requires a controlled correction path; do not promise that it can be freely deleted or edited. [Infor Customer Order Lines](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/ucm1528917030675.html) [Infor order invoicing](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html)

**Section Summary:** Recheck price after quantity changes and invoice hold before billing.

### Keywords
line price changed, Invoice Hold, edit shipped line, line troubleshooting
