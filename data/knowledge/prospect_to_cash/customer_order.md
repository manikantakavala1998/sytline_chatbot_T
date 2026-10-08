# Customer Order Module

## Document Metadata
- **Document Title:** Customer Orders header and order-entry screen guide
- **Document Type:** Process and form reference
- **Module:** customer_order
- **SyteLine Forms:** Customer Orders, Customer Order Lines, Customer Orders Quick Entry, Customer Order Blanket Lines, Customer Order Blanket Releases, Order Verification Report
- **Process Stage:** Customer order entry before fulfillment
- **Tags:** customer order, CO, sales order, order header, customer PO, ship-to, credit hold, order status
- **Access Level (SyteLine groups):** Determined by effective permissions in the deployed SyteLine site
- **Site Scope:** General guidance; verify originating and shipping sites
- **SyteLine Version:** General CSI/SyteLine guidance checked against Infor CSI 2026.10 Customer Service help
- **Document Owner:** Customer-to-Cash process owner
- **Reviewed / Approved By:** Pending local SyteLine business and security review
- **Last Reviewed:** Not yet locally reviewed
- **Version:** 0.2 draft
- **Source:** Infor CSI Customer Service help: Customer Orders Overview; Order Entry Steps; Customer Orders Quick Entry; Customer Purchase Order; Ship To; Status; About Credit Hold; Ship Partial; Order Detail Tree. No external links in this retrieval article.

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

## Before order entry

Confirm that a permitted Customer record exists in the order-entry site and is active for order processing. Check the intended bill-to, ship-to, currency, terms, item master, and any customer-level Credit Hold. Determine whether the request is a new order, a change to an existing order, or a conversion/copy from an estimate. Search for a previous order or customer PO before creating another transaction. The customer master provides defaults, but the new saved order must be checked independently.

**Section Summary:** Validate the customer, site, request type, and duplicate risk before order entry.

### Keywords
before customer order, order prerequisites, active customer, duplicate order, first order

## Find an existing order

Search Customer Orders using the order number when known, or filter by customer, order date, status, and Customer Purchase Order where available. The Customer Orders Lookup widget, if deployed, can show order number, customer, contact, order date, and customer PO; its filters can narrow the results to one customer. An absent search result can reflect site, filters, history status, or permissions. Verify the chosen order before changing it; a customer PO is a reference and may not uniquely identify one transaction under local practices.

**Section Summary:** Find and verify the existing order before creating or editing a transaction.

### Keywords
find customer order, order lookup, search customer PO, duplicate order, order number

## Create the Customer Orders header

Open Customer Orders and choose Actions > New. Enter or accept the Order number, choose the Order Type, select the Customer, and enter the required fields shown by the site. Review defaults from Customers and Customer Ship-Tos before choosing Actions > Save. Infor's standard sequence saves the header first, then opens Customer Order Lines through the Lines button. Saving a header alone does not mean that items, quantities, pricing, or fulfillment are complete.

**Section Summary:** Create and save the order header before entering lines.

### Keywords
Actions New, Actions Save, create sales order, order header, Lines button

## Order number and originating site

The Order number identifies the Customer Orders header and connects related lines, shipping, invoicing, and correspondence. Enter a permitted number or accept the configured default rather than inventing a numbering rule. Record the originating site when an order can be shipped from multiple sites. In multi-site processing, certain header status decisions are controlled at the originating site. Do not treat the same visible order number in a different site as permission to view or change that site's data.

**Section Summary:** Order number and originating site identify the transaction and its control point.

### Keywords
Order number, customer order prefix, originating site, multi-site order, order identifier

## Order Date and planning dates

Order Date on Customer Orders is the date the order was taken; a new order can default to today's date, subject to authorized correction. Line due dates represent item-level commitments and can differ from the header date. Keep the requested date, promised or projected date, and actual ship date distinct when explaining delivery. A date shown in a lookup or report must be tied to its owning field and record; do not infer that Order Date is the delivery date.

**Section Summary:** Order Date records when the order was taken, not when its lines ship.

### Keywords
Order Date, due date, requested date, promised date, ship date

## Select a valid Customer

The Customer field selects the account placing the order. Confirm the customer number and display name rather than relying only on a similar name. If the account is missing from the selection list, check the current site, customer status, list filters, and the user's access. A Customer Status code can control whether an account is active for order processing. Do not switch to another account merely to pass a validation error; correct the underlying customer or site issue through the proper owner.

**Section Summary:** Select the intended, order-eligible customer in the correct site.

### Keywords
Customer field, customer not selectable, active for order processing, order customer, site

## Select Ship To and verify addresses

Customer Orders displays the selected Ship To customer's name and address and allows a different valid Ship To address to be selected. Compare the destination with the customer's request and check the bill-to separately. A ship-to can be absent from the drop-down when Show in Drop-Down Lists is cleared on Customer Ship-Tos; a valid sequence may still be entered manually where permitted. Do not interpret a blank drop-down as proof that no ship-to exists. Verify the saved order's selected ship-to number after defaulting.

**Section Summary:** Confirm the order's actual ship-to rather than relying on a default or drop-down list.

### Keywords
Ship To, delivery address, ship-to dropdown, wrong address, bill-to

## Order and billing contacts

The order contact may default from the Customers Order Contact and may be changed on an individual order. The Bill To contact is derived from the Customers Billing Contact. The Ship To contact is derived from Customer Ship-Tos. Review these separately when the customer asks who receives confirmations, goods, or invoices. Editing an order contact need not change the customer master. Contact visibility and changes must follow local privacy and field permissions.

**Section Summary:** Order, bill-to, and ship-to contacts have different source records.

### Keywords
order contact, Bill To contact, Ship To contact, confirmation contact, billing contact

## Order Type on the header

Order Type distinguishes a Regular order from a Blanket order. A Regular order uses Customer Order Lines for item demand. A Blanket order can use blanket lines and multiple releases with separate quantities and dates. Confirm the type before selecting a line-entry procedure or interpreting the Order Detail Tree. Do not treat a blanket release as a regular line or assume a special type applies merely because a customer makes repeat purchases.

**Section Summary:** Order Type determines regular versus blanket line and release workflow.

### Keywords
Order Type, Regular, Blanket, blanket release, customer order type

## Header Status and line status

Customer Orders Status describes the header; each line or release has its own status. Infor lists Ordered, Planned, Stopped, Complete, and History for a customer-order header. New headers normally default to Ordered. Planned is limited by line and reservation conditions; Complete and History have separate criteria. A header marked Ordered does not prove every line can ship, and a line marked Planned is not available for shipment. Inspect both levels before answering whether an order is booked or ready.

**Section Summary:** Header status and line/release status must be interpreted separately.

### Keywords
header Status, Ordered, Planned, Stopped, Complete, History, line status

## Customer Purchase Order reference

Customer Purchase Order is the customer's own purchase-order number, if known. It is a reference field on Customer Orders and can help filter for an order or select order reports. It is not the SyteLine Order number. Check its spelling and revision against the customer's document, especially when multiple orders are raised against one customer PO. If absent, do not invent a number; follow the site's rule for whether the field is required.

**Section Summary:** Customer Purchase Order links the customer's paperwork to the SyteLine order.

### Keywords
Customer Purchase Order, customer PO, PO reference, search PO, order number

## Terms, currency, and commercial defaults

The Customers record can supply billing Terms Code and currency defaults to a new order, but the saved Customer Orders transaction is the source for the values actually used. Compare the order with the customer's accepted quote or PO, especially after a copy or conversion. A mismatch can affect invoice due dates, pricing conversion, and customer expectations. The exact editable fields and restrictions depend on the deployed setup and the user's permissions.

**Section Summary:** Verify the saved order's terms and currency instead of assuming master defaults persisted.

### Keywords
Terms Code, currency, billing defaults, quote to order, order terms

## Tax Info on Customer Orders

Use the Tax Info area to review the tax codes and related tax settings on the order. Tax behavior depends on configured tax systems, ship-to location, item taxation, and exemption rules. Infor's tax setup guidance tests the order tax result and the Order Verification Report before proceeding. Do not prescribe a universal tax code or infer that blank freight tax means the same thing in every tax mode. Escalate discrepancies to the site's tax owner with the order, site, customer, ship-to, and exact field values.

**Section Summary:** Tax Info must be checked against the site's tax configuration and saved order.

### Keywords
Tax Info, tax code, tax exempt, freight tax, order tax

## Freight and miscellaneous charges

Review freight, miscellaneous charges, and any related tax fields when they appear on the order header. Freight Tax Code behavior differs between area-based and item-based tax systems. Pricing and tax can change the amount invoiced even when item quantities are correct. Confirm who owns the charge and whether it belongs on the header, line, or later shipment process under the site's procedure. Do not use an estimated order amount as proof of the final invoice total.

**Section Summary:** Freight and miscellaneous amounts need transaction and tax review.

### Keywords
freight, miscellaneous charge, Freight Tax Code, order amount, invoice total

## Warehouse and shipping site defaults

The order header Warehouse can default from the selected Customer Ship-To; a line may inherit that warehouse and sometimes be changed when the form allows it. In multi-site processing, Ship Site identifies the site intended to ship a line and must be valid for the item. Check the saved line when an order appears in the wrong fulfillment site. A default warehouse or site is not an allocation or proof of available inventory.

**Section Summary:** Header warehouse and line ship site guide fulfillment but do not prove stock availability.

### Keywords
Warehouse, Ship Site, shipping site, multi-site order, fulfillment warehouse

## Ship Partial and shipment expectations

Ship Partial records whether the customer accepts partial shipments. On the Available to Ship Report, a cleared flag normally requires all lines to be ready for the order to appear; a selected flag can show the order when at least one line is ready. The flag is informational for shipment processing and does not by itself permit partial quantities of a line. Confirm actual shipment eligibility, holds, line status, and available stock separately. Do not describe Ship Partial as an unconditional shipping authorization.

**Section Summary:** Ship Partial affects readiness reporting but is not a blanket shipment permission.

### Keywords
Ship Partial, partial shipment, Available to Ship Report, partial line quantity

## Credit Hold on the order

The Credit Hold field on Customer Orders is an order-level control; Customers has a separate customer-level hold. Either hold can prevent shipping. A red problem indicator on an order can reflect a customer hold even when that order's Credit Hold field is not selected. The automatic hold outcome also depends on the Limit Exceeded Credit Hold Reason on Accounts Receivable Parameters and line-level Allow Over Credit Limit behavior. Record the actual reason and seek authorized credit review before changing a hold.

**Section Summary:** Inspect both customer and order holds and the configured credit reason.

### Keywords
Credit Hold, order hold, customer hold, red X, credit reason

## Amounts and estimated totals

The Customer Orders Amounts area can show order-level amounts and tax information as processing progresses. A displayed estimated total is not proof of an invoice or payment. Infor tax guidance notes that certain tax amounts appear on Amounts when shipping occurs, so a pre-shipment display can differ from a later one. Compare the saved line prices, discounts, freight, tax, shipped quantity, and invoice history when investigating a value difference. Use authorized live data for any named order amount.

**Section Summary:** Amounts on an order are stage-dependent and differ from final invoiced cash.

### Keywords
Amounts tab, estimated total, order total, tax amount, invoice amount

## Lines button and item handoff

After saving the Customer Orders header, click Lines to open Customer Order Lines. Enter each item, quantity, due date, price, and sourcing information on the line form as applicable; a header does not hold the full item demand. Multiple lines can belong to one header. A line may remain new and unsaved until Actions > Save. The separate Customer Order Line guide owns detailed item, allocation, ATP/CTP, cross-reference, and line-status procedures.

**Section Summary:** The Lines button moves from saved header to item-level demand.

### Keywords
Lines button, Customer Order Lines, add item, order line, save line

## Customer Orders Quick Entry alternative

Where deployed, Customer Orders Quick Entry can create an order with lines: choose New Order, complete and save the header, then choose New Line and save line details. A customer or order filter from related lookup widgets may preselect a record, so verify the intended account. For an existing record, Refresh returns to its last saved state; Cancel can discard a new entry. The application form supports functions that may not be available in a widget, such as blanket-order entry, notes, or detailed field help.

**Section Summary:** Quick Entry is an alternate screen with its own save and filter behavior.

### Keywords
Customer Orders Quick Entry, New Order, New Line, Refresh, Cancel

## Order Detail Tree navigation

The Order Detail Tree on Customer Orders displays line and shipment information. For a regular order, the first level shows line, item, ordered quantity, and due date; the next level shows shipments. A blanket order adds a release level between the blanket line and shipment. Expand the relevant row before concluding that an item shipped or was returned. In multi-site orders, shipping detail in the tree can be limited to the current site, so check the correct site for a full picture.

**Section Summary:** Expand the correct tree level and site to inspect lines, releases, and shipments.

### Keywords
Order Detail Tree, order line tree, blanket release, shipment detail, multi-site tree

## Blanket-order branch

For a Blanket Order Type, save the Customer Orders header, then use the Releases path to Customer Order Blanket Lines and Customer Order Blanket Releases as supported by the deployed form. Blanket lines describe the agreement; releases specify dates and quantities to fulfill. Compare Quantity Released with Blanket Quantity and check each release status. A blanket order should not be answered with only the regular Customer Order Lines procedure; the detailed exception workflow belongs in the order/billing variations article.

**Section Summary:** Blanket orders add a release workflow beyond the regular order header.

### Keywords
blanket order, blanket line, release date, Quantity Released, Blanket Quantity

## Permissions and live-order boundary

This article can explain standard order forms and checks, but a named order's current status, credit exposure, line availability, shipment, invoice, or payment requires an authorized live SyteLine lookup. Use the logged-in user's effective site, form, field, and row permissions. Read permission does not grant create, change, hold-release, shipping, or invoicing authority. Record audit context for any approved action. No static article can confirm that a particular customer order is ready to ship today.

**Section Summary:** Order-specific facts and changes require live data and effective permissions.

### Keywords
customer order permission, live status, RBAC, order security, audit
