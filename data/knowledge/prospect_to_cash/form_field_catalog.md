# Prospect-to-Cash Form and Field Guide

## How to use this guide

Form titles and labels are from general Infor CSI/SyteLine help. Field availability, requiredness, default, editable state, and internal property name depend on release, license, role, site, and customization. The entries below explain the business meaning and where to inspect a field; they are not a confirmed IDO schema. A field shown on a read-only related tab is maintained on its owning form. **[NEEDS SYTELINE CONFIRMATION]** applies to all IDO, property, method, API, and row-filter mappings. [Infor web forms](https://docs.infor.com/csi/2026.x/en-us/csbiolh/admin_cl_sl/xoy1567550426603.html)

**Section Summary:** Use displayed labels for help; inspect the deployed site before using a field in an API.

### Keywords
form field, field help, form map, IDO property, screen context

## Sales Contacts, Prospects, and Leads

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Sales Contacts | Contact identity and preferences | The person and preferred communication details; link to organization through cross-reference. |
| Prospects | Prospect identifier, name, address, territory | Potential organization; check for duplicates and whether converted to Customer. |
| Prospect Sales Contact Cross References | Prospect and sales contact | The relationship between company and person. |
| Prospect Interactions | Interaction date, status, follow-up date, notes | History and next contact action; not an order or invoice. |
| Leads | Prospect or Customer, source, quality, status | Interest record; select one party type and interpret status via configured Lead Statuses. |
| Leads | Related opportunities, estimates, orders | Read-only trace of downstream work; open owning form to change data. |

Lead Statuses are required configuration values; the labels and meaning are organization-defined. [Infor CRM recommended setup](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144069328.html) [Infor Leads](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/crmtopics/leads.htm) [Infor CRM scenario 1](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144070654.html)

**Section Summary:** A person, prospect company, lead, and interaction are separate records connected by references.

### Keywords
Sales Contacts, Prospects, Leads, lead status, Prospect Interactions

## Opportunities and tasks

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Opportunities | Opportunity number, Prospect or Customer | Pipeline identity and party. |
| Opportunities | Status, Stage, Source | Configured sales progress and origin; do not equate a stage with a booked order. |
| Opportunities | Estimated Value, win percentage, projected close date | Forecast assumptions; update when sales information changes. |
| Opportunities | Won/Lost reason, close date | Outcome and explanation; does not itself create a customer order. |
| Opportunity Tasks | Type, owner, priority, due date, mandatory, completion date | Actions agreed by the team. |
| Opportunities related tabs | Estimates, Orders, Competitors, Team Members | Links or read-only views maintained in the corresponding form. |

Opportunity Statuses are required setup; sources, stages, reasons, and task types are optional classifications. [Infor Opportunities](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/crmtopics/opportunities.htm) [Infor creating opportunities](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_managing_opportunities.htm)

**Section Summary:** Forecast fields, outcome fields, tasks, and later order links answer different questions.

### Keywords
Opportunities form, Opportunity Tasks, Estimated Value, Projected Close Date

## Estimate and quotation

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Estimates | Estimate number, Prospect/Customer, Contact | Proposal identity and intended party. |
| Estimates | Quote Date, Expiration Date, Status | Validity and workflow state; Quoted is not accepted. |
| Estimates | Terms Code, Order Discount, Tax Code, customer quote reference | Commercial terms and tax input. |
| Estimate Lines | Line, Item, Qty Ordered, U/M | Proposed item and amount. |
| Estimate Lines | Status, Unit Price, Sales Disc, Source | Line state, price, discount, and optional supply/job link. |
| Estimate Response Form Report | Print Price and output | Customer-facing proposal; inspect before sending. |

When quantity changes on an Estimate Line, SyteLine may offer price recalculation; check the saved value. [Infor creating estimate](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_an_estimate.htm) [Infor creating estimate lines](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_estimate_lines.htm) [Infor CRM scenario 3](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144070779.html)

**Section Summary:** Estimate header holds quote terms; lines hold item detail; the report is the customer document.

### Keywords
Estimates form, Estimate Lines, Quote Date, Expiration Date, Sales Disc

## Customer and ship-to

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Customers | Customer number, name, bill-to address | Trading account and billing identity. |
| Customers | Terms, currency, bank, language, tax | Invoice/payment defaults subject to local finance setup. |
| Customers | Credit Limit, Credit Hold, balances | Credit controls and live amounts; balance requires authorized current read. |
| Customer Ship Tos | Ship-to number, address, contact, codes | Delivery location selected by an order. |
| Customers CRM tab | Territory, sales contacts, classification | Relationship and reporting data. |

The customer can have one bill-to and multiple ship-tos; current terms may have restrictions with other invoicing options. [Infor creating a customer](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/creating_a_customer.html)

**Section Summary:** Customer master, bill-to, and selected ship-to must be checked independently.

### Keywords
Customers form, Customer Ship Tos, billing terms, Credit Limit

## Customer order header and line

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Customer Orders | Order number, customer, ship-to, type, status | Booked transaction identity and header state. |
| Customer Orders | Order/request dates, customer PO, terms, tax, freight | Commercial and delivery context. |
| Customer Orders | Credit Hold, hold reason, Ship Partial | Shipping restrictions and order-readiness behavior. |
| Customer Order Lines | Line/release, item, Qty Ordered, U/M, due date | Demand and schedule for a specific product. |
| Customer Order Lines | Unit Price, discount, source, site | Pricing and fulfillment source. |
| Customer Order Lines | Ready to Ship, shipped/invoiced quantity, Invoice Hold | Operational progress; verify in reports and transactions. |

For blanket orders, inspect blanket lines and releases separately. A saved line may remain Planned after a credit check. [Infor Customer Orders](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/cotopics/order_maintenance.htm) [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html) [Infor Customer Order Lines](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/ucm1528917030675.html)

**Section Summary:** Header status, line status, holds, shipped quantity, and invoice hold answer distinct questions.

### Keywords
Customer Orders, Customer Order Lines, Due Date, Ready to Ship, Invoice Hold

## Shipment, invoice, and A/R

| Owning form/report | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Available to Ship Report | Order, line, site, ready quantity | Candidate fulfillment; excludes some holds. |
| Order Shipping / Ship Confirmation | Order, line, quantity, ship date | Actual posted shipment; workflow varies by site. |
| To Be Invoiced Report | Shipped, uninvoiced lines | Billing work queue. |
| Order Invoicing/Credit Memo | Customer/order range, Invoice or Credit Memo, process result | Creates standard order invoice or credit memo. |
| A/R Posted Transactions | Invoice, memo, payment, amount, open balance | Posted financial history. |
| A/R Payments / A/R Payment Distributions | Payment number/type, customer, amount, applied invoice | Cash receipt and allocation. |
| A/R Aging Report | As-of date, buckets, customer, currency | Open balance view for collections. |

Never infer a live customer balance, invoice amount, shipment status, or payment status from this catalog. [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html) [Infor order invoicing](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html) [Infor A/R steps](https://docs.infor.com/csi/10.x/en-us/csbiolh/financials_user_cl_sl/lsm1454143881752.html)

**Section Summary:** Shipment, billing, and cash application live in separate transactions and reports.

### Keywords
Order Shipping, To Be Invoiced, A/R Payments, A/R Aging Report
