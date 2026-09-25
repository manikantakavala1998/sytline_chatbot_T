# Customer Order and Billing Variations

## Choose the actual transaction path

The standard Prospect-to-Cash explanation is customer order header, line, shipment, invoice, A/R, and payment. Several supported paths change what record or process owns the next step. Before explaining a missing shipment or invoice, identify the order type, the exact line or release, the shipping site, the invoice method, and any EDI, drop-ship, delivery-order, or credit-control settings. These features are optional or version-dependent. Do not treat a general flow as a command to execute a transaction.

**Section Summary:** Order type and billing method determine the correct line, shipment, and invoice checks.

### Keywords
regular order, blanket order, EDI, drop ship, consolidated invoice, delivery order

## Blanket orders and releases

A blanket order represents demand that is fulfilled in staggered releases. On Customer Orders, select the Blanket order type; Customer Order Blanket Lines holds the item and blanket quantity; Customer Order Blanket Releases holds individual release quantities and dates. One blanket line can have multiple releases. Compare Quantity Released with Blanket Quantity to find an incomplete schedule, while allowing for an intentionally open agreement. For availability or shipment, identify the particular order number, line, and release; the blanket header total alone does not identify what should ship today.

An Ordered release can affect allocated-order inventory and customer balance. A Planned release does not perform the same credit check or customer-balance update; changing it to Ordered can trigger those checks. A customer or order Credit Hold prevents shipping, and site-specific controls may add more restrictions. If a release was completed and must be reopened, the order header and blanket line may have to be reopened before the release. This is a controlled transaction requiring an authorized operator, not a chatbot action.

| Record or field | Diagnostic use |
| --- | --- |
| Customer Orders Type | Distinguishes Blanket from Regular order path. |
| Blanket line Item, Blanket Quantity, Line Status | Defines the scheduled item and agreement amount. |
| Release number, date, quantity, status | Identifies each planned shipment obligation. |
| Quantity Released | Reconciles the schedule with the blanket quantity. |
| Ready Quantity and shipment history | Separates available, shipped, and remaining quantities. |

**Section Summary:** A blanket release, not only the blanket header, is the operational unit for timing and shipment.

### Keywords
Customer Order Blanket Lines, Customer Order Blanket Releases, release date, Quantity Released, Ready Quantity

## Drop-ship destination and multi-site fulfillment

The Drop Ship/Drop Ship To value on a Customer Order Line or release identifies a customer and ship-to destination that may differ from the ordering customer's header ship-to. The destination must be an established customer record for invoicing. Check the line/release destination, ship-to sequence, and tax information before giving a delivery or invoice-address explanation. Once a line/release reaches Filled, Complete, or History, changing its drop-ship customer can be restricted. Do not advise changing a historical line to repair an address without the site's correction procedure.

In a multi-site order, the originating site and shipping site can differ. A single order may have lines sourced from more than one shipping site. Check site-specific availability, shipping transactions, and inter-site status before concluding a line is missing. The Order Verification Report for such an order may need to be produced from the originating site to include all lines. Current inventory and ship status require an authorized live read at the correct site.

**Section Summary:** Header ship-to, line drop-ship destination, originating site, and shipping site are separate facts.

### Keywords
Drop Ship To, ship-to sequence, multi-site, originating site, shipping site, Order Verification Report

## EDI-origin orders and customer acknowledgements

An EDI-origin customer order may have a different entry, validation, and change-control path from a manually entered order. Identify the source and customer purchase-order reference, then compare the accepted order header, lines/releases, quantities, dates, and ship-to with the inbound message or approved record. Site EDI mappings and partner rules are not specified by this article. Never tell a user to overwrite an EDI field or resend a transaction without checking the partner integration and local procedure. A changed drop-ship destination on an EDI line may also require tax-code review.

For a non-EDI or mixed workflow, the Order Verification Report can provide an order acknowledgement for Planned or Ordered orders, including line/release quantities and due dates. It is an acknowledgement, not proof of shipment or invoice posting. If an acknowledgement differs from the saved order, verify report parameters, line/release status, language, site, and whether the order changed after printing.

**Section Summary:** EDI orders require partner-specific validation; order acknowledgement does not prove fulfillment.

### Keywords
EDI customer order, customer PO, order acknowledgement, Order Verification Report, tax code

## Standard versus consolidated invoicing

The standard Order Invoicing/Credit Memo path processes eligible shipped-and-uninvoiced order lines or releases. A customer, order, or line/release may instead be designated for consolidated invoicing. A consolidated invoice can group multiple shipped orders over a period, so one shipment may not immediately produce its own invoice. At the line/release level, the Consolidated Invoice indicator and invoice frequency help determine when it enters that path. A blanket release is marked on Customer Order Blanket Releases rather than on the blanket header alone.

The Consolidated Invoices Workbench can assemble eligible shipped lines; Consolidated Invoice Generation and Consolidated Invoicing handle generation and posting according to the site's process. Some delivery orders are invoiced through this system, with invoice type and customer purchase-order grouping affecting whether lines join one invoice or create separate headers. Do not use the ordinary To Be Invoiced queue alone to declare a consolidated line unbilled. Check the pending consolidated invoice record, processing status, errors or modified-record state, posted invoice, and A/R transaction.

Summarize Lines can group similar line detail on a consolidated invoice when the option is eligible. It changes presentation, not the underlying shipment or order history. Eligibility can depend on line state, notes, item configuration, EDI source, tax settings, and other site controls. If the option is unavailable, inspect these conditions instead of telling the user to force it.

**Section Summary:** Consolidated billing has its own selection, workbench, print/post, and exception checks.

### Keywords
Consolidated Invoice, Consolidated Invoices Workbench, Invoice Freq, delivery order, Summarize Lines

## Exception diagnosis by missing outcome

| Missing outcome | Check in sequence | Avoid this assumption |
| --- | --- | --- |
| Blanket release does not ship | Release status and date, Ready Quantity, customer/order hold, site | Blanket header status alone makes it ready. |
| Drop-ship delivery is unclear | Line/release Drop Ship To and ship-to sequence, shipping record | Header ship-to always determines destination. |
| EDI order differs from request | Partner reference, inbound message, accepted order, mapping errors | Manual overwrite is safe. |
| Shipped line is not on standard invoice queue | Invoice Hold, already-invoiced quantity, consolidated flag, delivery-order route | Shipment automatically generated an invoice. |
| Consolidated invoice will not post | Workbench record, modified-state warning, invoice frequency, print/post result | A pending invoice is a posted invoice. |
| Customer says an invoice lacks an item | Shipment, order line, consolidated summarization, posted invoice detail | The printed invoice line count equals shipment line count. |

For every case, preserve the order number, line/release, customer, site, dates, and document number. Current status and amounts require permission-checked SyteLine data. An invoice correction or credit requires the approved finance workflow, not a silent change to a shipped order.

**Section Summary:** Trace exact records through shipment, billing selection, posting, and A/R before explaining an exception.

### Keywords
blanket release not shipping, missing consolidated invoice, pending invoice, invoice posting, order exception
