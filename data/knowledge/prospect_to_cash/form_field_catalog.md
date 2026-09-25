# Prospect-to-Cash Form and Field Guide

## How to use this guide

Form titles and labels are from general Infor CSI/SyteLine help. Field availability, requiredness, default, editable state, and internal property name depend on release, license, role, site, and customization. The entries below explain the business meaning and where to inspect a field; they are not a confirmed IDO schema. A field shown on a read-only related tab is maintained on its owning form. **[NEEDS SYTELINE CONFIRMATION]** applies to all IDO, property, method, API, and row-filter mappings.

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

Lead Statuses are required configuration values; the labels and meaning are organization-defined.

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

Opportunity Statuses are required setup; sources, stages, reasons, and task types are optional classifications.

**Section Summary:** Forecast fields, outcome fields, tasks, and later order links answer different questions.

### Keywords
Opportunities form, Opportunity Tasks, Estimated Value, Projected Close Date

## Campaigns, contacts, and forecasts

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Sales Contacts | Contact identity, organization link, communication details | Person-level record; verify current prospect/customer cross-reference and outreach rules. |
| Sales Contact Groups | Group and members | Reusable audience; membership does not create a lead. |
| Campaigns | Campaign identity, selected contacts, communications, related leads | Marketing activity and response trace; verify an explicit lead association. |
| Campaign Items | Item and campaign association | Product or item context for the campaign, not an order line. |
| Competitors / Opportunity Competitor Cross References | Competitor identity and opportunity association | Competitive context for a potential sale. |
| Opportunity Member Cross References | Opportunity and salesperson/team member | Ownership and collaboration; the related opportunity tab may be display-only. |
| Sales Forecasts | Sales Period, salesperson, Draft/Submitted status, included opportunity values | Expected sales view; not an invoice or actual booked amount. |

For a current campaign response count or forecast total, request the campaign or sales period, owner, site, and permission-checked live records. Do not infer a number from this field catalog.

**Section Summary:** Campaign membership, lead creation, opportunity ownership, and forecast submission are separate data relationships.

### Keywords
Campaigns form, Campaign Items, Sales Contact Groups, Sales Forecasts, Sales Periods

## Estimate and quotation

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Estimates | Estimate number, Prospect/Customer, Contact | Proposal identity and intended party. |
| Estimates | Quote Date, Expiration Date, Status | Validity and workflow state; Quoted is not accepted. |
| Estimates | Terms Code, Order Discount, Tax Code, customer quote reference | Commercial terms and tax input. |
| Estimate Lines | Line, Item, Qty Ordered, U/M | Proposed item and amount. |
| Estimate Lines | Status, Unit Price, Sales Disc, Source | Line state, price, discount, and optional supply/job link. |
| Estimate Response Form Report | Print Price and output | Customer-facing proposal; inspect before sending. |

When quantity changes on an Estimate Line, SyteLine may offer price recalculation; check the saved value.

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

The customer can have one bill-to and multiple ship-tos; current terms may have restrictions with other invoicing options.

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

For blanket orders, inspect blanket lines and releases separately. A saved line may remain Planned after a credit check.

**Section Summary:** Header status, line status, holds, shipped quantity, and invoice hold answer distinct questions.

### Keywords
Customer Orders, Customer Order Lines, Due Date, Ready to Ship, Invoice Hold

## Blanket, drop-ship, and consolidated-billing fields

| Owning form | Field or data group to inspect | Business meaning and next check |
| --- | --- | --- |
| Customer Orders | Type, originating site, ship-to, credit hold | Determines regular versus blanket flow and header-level restrictions. |
| Customer Order Blanket Lines | Item, Blanket Quantity, Quantity Released, Line Status | Agreement quantity and how much is scheduled in releases. |
| Customer Order Blanket Releases | Release number, date, quantity, status, Ready Quantity | Individual fulfillment obligation; check its shipping and invoicing history. |
| Customer Order Lines / Blanket Releases | Drop Ship/Drop Ship To and ship-to sequence | Line-level destination that may differ from header ship-to. |
| Customer Order Lines / Blanket Releases | Consolidated Invoice, Invoice Freq, Summarize Lines | Determines a nonstandard billing route and invoice presentation where eligible. |
| Consolidated Invoices Workbench | Pending invoice header, lines, modified state | Review shipped lines selected for consolidated billing before posting. |
| Consolidated Invoicing | Process range, print/post result, invoice number | Confirms whether a consolidated invoice was created and posted. |

An EDI-origin order may be controlled by an integration workflow. Its partner-specific field mapping is **[NEEDS SYTELINE CONFIRMATION]**. A pending consolidated invoice is not the same as a posted A/R invoice.

**Section Summary:** A blanket release and a consolidated invoice record require their own form-level checks.

### Keywords
Blanket Quantity, Quantity Released, Drop Ship To, Consolidated Invoice, Invoice Freq

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

Never infer a live customer balance, invoice amount, shipment status, or payment status from this catalog.

**Section Summary:** Shipment, billing, and cash application live in separate transactions and reports.

### Keywords
Order Shipping, To Be Invoiced, A/R Payments, A/R Aging Report

## Frequently asked field meanings

| Field | Form context | Plain-language meaning |
| --- | --- | --- |
| Lead Status | Leads | The configured state of a sales interest. The organization's status list gives the precise meaning. |
| Opportunity Stage | Opportunities | The configured step in pursuing a potential sale; separate from a won/lost outcome. |
| Projected Close Date | Opportunities | Expected sales decision timing, not a promised ship date. |
| Expiration Date | Estimates | Date after which the offer should be revalidated before use. |
| Qty Ordered | Estimate Lines or Customer Order Lines | Requested amount of the line item, with its unit of measure. |
| Due Date | Customer Order Lines | The line's scheduled need or delivery target; inspect site-specific semantics and related dates. |
| Unit Price | Estimate Lines or Customer Order Lines | Proposed or booked price per unit before the complete transaction total is built. |
| Credit Hold | Customers or Customer Orders | Account-level or order-level shipping restriction; check both forms. |
| Ship Partial | Customer Orders | Influences whether an order with some ready lines appears in availability reporting; does not itself authorize a fraction of one line. |
| Invoice Hold | Customer Order Lines | Prevents eligible shipped line quantity from normal invoice processing while selected. |
| Terms Code | Customer, estimate, or order | Billing/payment terms used in due-date scheduling under configuration. |
| Apply To | A/R payment/distribution | The open invoice or other item to which a receipt is allocated. |

For any field-help answer, state the form and record level. A Due Date on an order line, an invoice due date, and an opportunity projected close date serve different purposes. If the user asks for the current field's actual value, read the authorized live record rather than inferring a value from this guide.

**Section Summary:** Field names require form context and sometimes live values.

### Keywords
Due Date, Projected Close Date, Terms Code, Unit Price, Credit Hold, Invoice Hold
