# Customer Order Module

## Purpose and form ownership

Customer Orders holds the order header: customer, ship-to, order type and status, dates, terms, shipping and billing defaults, and credit hold information. Customer Order Lines holds the actual items and releases. The standard order-entry path is create header, save it, add lines, check credit and availability, ship, then invoice. A quote may be copied to an order, but a quote is not itself an order. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor Customer Orders](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/cotopics/order_maintenance.htm)

**Section Summary:** The order header controls the commercial transaction; lines specify demand.

### Keywords
customer order, Customer Orders form, order header, sales order, order entry

## Create and review an order

1. Search existing orders and customer purchase order references to avoid duplicates.
2. Create a record on Customer Orders, select customer and ship-to, and fill required header values shown by the site.
3. Review order type, status, order/requested dates, customer PO, bill-to, ship-to, terms, currency, tax, freight, and salesperson when present.
4. Save the header, then open Customer Order Lines and add line/releases.
5. Review unit price, due date, shipping site, available quantity, credit status, and order totals. Use Get ATP/CTP or availability tools if those features are enabled.
6. Print an Order Verification Report when an acknowledgement is needed; shipment and invoicing are later steps. Customer Orders Quick Entry is an alternate entry path. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html)

**Section Summary:** Save the header, add lines, then verify commercial, availability, and credit information.

### Keywords
create order, new Customer Order, customer PO, ship-to, order verification

## Status, holds, and changes

Order and line statuses are separate. Infor uses Planned and Ordered line states, and a credit check can leave a line Planned or put an order on hold depending on settings. A customer-level hold and order-level hold can both block shipping. Do not tell a user to simply “release the order” as a universal workflow: identify the current status, hold reason, error, line, and local authorization first. For a submitted change, recheck price, dates, tax, allocation, and downstream shipment or invoice history. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html)

**Section Summary:** Status and hold are different controls; explain the actual reason before proposing a change.

### Keywords
order status, Planned, Ordered, credit hold, release order, change order

## Order types and exceptions

Regular and blanket orders differ. Blanket orders use blanket lines and releases with separate ship dates. An order may also have multiple shipping sites, drop-ship lines, EDI origin, letter-of-credit requirements, or shipment approval. These are optional or configuration-dependent paths. Identify the order type and enabled features before giving specific steps. [Infor blanket order lines](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/nol1528915094338.html) [Infor Customer Orders](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/cotopics/order_maintenance.htm)

**Section Summary:** Order type and options determine the relevant line, credit, shipment, and invoice workflow.

### Keywords
blanket order, order release, EDI order, drop ship, multi-site

## Troubleshoot an order that cannot progress

Check the exact error and order number; current header/line status; customer and order credit hold; missing or invalid customer, ship-to, item, quantity, price, due date, site, tax, or terms; availability and cross-referenced supply; letter-of-credit and shipment approval settings; and whether the line already shipped or invoiced. The Order Entry Exception Report can help identify processing errors. Do not assume a credit hold is the cause merely because an order will not ship. [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html)

**Section Summary:** Diagnose the exact order and line state before changing it or escalating.

### Keywords
order won't process, order won't release, order exception, cannot ship
