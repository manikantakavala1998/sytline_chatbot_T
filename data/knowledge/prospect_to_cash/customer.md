# Customer Module — Customer-to-Cash Form and Screen Guide

## Document Metadata
- **Document Title:** Customer master, bill-to, ship-to, and first-order readiness
- **Document Type:** Process and form reference
- **Module:** customer
- **SyteLine Forms:** Customers, Customer Ship-Tos, Multi-Site Customers, Multi-Site Customer Ship-Tos, Customer Hub, Customer Orders
- **Process Stage:** Customer setup before order entry
- **Tags:** customer, customer master, bill-to, ship-to, customer account, credit, customer order, first order
- **Access Level (SyteLine groups):** Determined by the deployed SyteLine permissions
- **Site Scope:** General guidance; verify current site and multi-site configuration
- **SyteLine Version:** General CSI/SyteLine guidance; checked against Infor CSI 2026.10 Customer Service help
- **Document Owner:** Customer-to-Cash process owner
- **Reviewed / Approved By:** Pending local SyteLine business and security review
- **Last Reviewed:** Not yet locally reviewed
- **Version:** 0.2 draft
- **Source:** Infor CSI Customer Service help: Creating a Customer; Customers; Customer Ship-Tos; Customer Hub; customer field help. No external links are included in this retrieval article.

## Customer-to-Cash starting point

A Customer record identifies the trading account used for orders, billing, shipping, and receivables. A prospect may be converted to a customer, but a customer may also be created directly. Customer setup precedes the first customer order when the account does not already exist. The sales transaction starts when the Customer Orders header and its lines are saved; the customer master itself is not an order. Search for an existing account before adding another customer number.

**Section Summary:** Customer setup establishes the account; the order is the start of the sales transaction.

### Keywords
where customer to cash starts, create customer, first order, prospect conversion, customer master

## Customer screen map

Use the current site and the user's permitted forms. The exact layout can differ by CSI release and customization.

| Form or screen | Use at this stage |
| --- | --- |
| Customers | Create or review the customer account, bill-to data, defaults, credit, contacts, and related tabs. |
| Customer Ship-Tos | Create or review a delivery location and its address and codes. |
| Multi-Site Customers | Maintain customer information from a master site when the multi-site setup permits it. |
| Multi-Site Customer Ship-Tos | Maintain ship-to data across eligible sites; not a replacement for checking local site access. |
| Customer Hub | Search and navigate to customer, ship-to, pricing, order, and interaction views when this form is deployed. |
| Customer Orders | Verify the selected customer and ship-to defaults on the new transaction. |

**Section Summary:** These forms own account, delivery, multi-site, overview, and first-order checks.

### Keywords
Customers form, Customer Ship-Tos form, Multi-Site Customers, Customer Hub, screen navigation

## Before opening a new customer record

Search Customers by customer number and name; check possible duplicate legal names, trading names, and existing site records. Review the prospect or CRM record if the account originated there. Determine whether the user needs a new customer, a new ship-to for an existing customer, or an update to an existing bill-to. Confirm the intended site and the local approval procedure for customer creation. Do not assume a missing search result means no record exists; filters, inactive status, site context, and permissions can hide it.

**Section Summary:** Establish the correct account and site before creating a customer or ship-to.

### Keywords
duplicate customer, search customer, new account, existing account, wrong site

## Customers form — create and save the account

Open Customers, or Multi-Site Customers when working from an authorized master site. Leave Filter-in-Place mode, choose Actions > New, and enter a Customer identifier or leave it blank if the configured A/R Customer Prefix should generate one. Enter the bill-to name and address and required billing details shown by the site, then choose Actions > Save. After saving, confirm the generated or entered customer number. Do not copy a placeholder customer number into an order before the save succeeds.

**Section Summary:** Create the customer header, save it, and verify its actual identifier.

### Keywords
Actions New, Actions Save, customer number, customer prefix, Filter-in-Place

## Customers form — identity and bill-to fields

The Customer field is the account identifier. The name and bill-to address identify the account that receives invoices; address fields may include multiple lines and location codes. Confirm the legal or approved billing name, address, country and postal details required by the site. The bill-to record is distinct from ship-to destinations. One customer can have one bill-to address and multiple ship-to locations. Changes to a master address should be reviewed against existing open orders and billing documents instead of assuming that they all update automatically.

**Section Summary:** The customer identifier and bill-to details identify the billed party.

### Keywords
Customer field, bill-to address, billing name, customer number, invoice address

## Customers form — billing, currency, and terms

Review the billing fields displayed on Customers, including language, currency code, bank information, and payment Terms Code where used. These are customer defaults and may flow to new transactions; inspect the saved order to see what it actually uses. If the business uses more than one customer currency, review the Currency Codes tab or Customer Currency Codes form. A Terms code with multiple due dates is incompatible with certain features such as letter of credit, consolidated invoicing, or draft payment type in the vendor guidance; verify the site's enabled features before choosing it.

**Section Summary:** Billing and currency settings provide defaults, but the saved order is authoritative for a transaction.

### Keywords
terms code, currency code, language, bank, multiple currencies, invoice terms

## Customers form — Ship To tab and default destination

After the initial customer save, refresh or reopen Customers if the Ship To tab appears empty. The Ship To tab displays delivery-location information and provides the Ship Tos button to open Customer Ship-Tos. Select a Default Ship To number on Customers when the normal delivery location is known. On Customer Ship-Tos, the Default Ship To indicator is read-only and reflects that customer-level selection. The default is a convenience, not proof that it is correct for every order; confirm the actual ship-to on each order.

**Section Summary:** Save and refresh before maintaining ship-tos; verify the default on every order.

### Keywords
Ship To tab blank, Ship Tos button, Default Ship To, delivery address, refresh customer

## Customer Ship-Tos — create a destination

From Customers > Ship To > Ship Tos, open Customer Ship-Tos, choose Actions > New, and enter a Ship To number or accept the next available sequential number. On Address, enter the delivery name and address. On Codes, review the site-required shipping, tax, warehouse, or other defaults. Save with Actions > Save and verify the new ship-to appears under the correct customer. Add more locations only when they represent distinct delivery destinations. Infor documents up to 9999 ship-to addresses; local policies may be more restrictive.

**Section Summary:** Each ship-to is a numbered delivery location belonging to one customer.

### Keywords
Customer Ship-Tos, Ship To number, Address tab, Codes tab, create ship-to

## Customer Ship-Tos — address and contact checks

The ship-to name and address identify where goods go, not who is billed. Confirm street/address lines, city, region, postal code, country, and the shipping contact against the requested destination. The ship-to contact is separate from the Customers billing and order contacts. If an order uses the wrong destination, inspect its selected Ship To number and saved address/defaults; changing the master ship-to is not automatically the right correction for an already-open transaction.

**Section Summary:** The ship-to record owns delivery location and its shipping contact.

### Keywords
shipping address, ship-to contact, wrong destination, city, country, bill-to versus ship-to

## Customer Ship-Tos — warehouse, site, and salesperson

A Warehouse on Customer Ship-Tos can default to Customer Orders for that destination. Leave it blank when orders for the ship-to routinely originate from different warehouses; choose the correct warehouse on the order instead. In multi-site processing, check the Ship Site and whether it is valid for the item on each order line. A Salesperson assigned to the ship-to can default onto future order headers. These defaults may be overridden on a transaction where the user's permissions and business rules permit it.

**Section Summary:** Ship-to warehouse, ship site, and salesperson can influence new-order defaults.

### Keywords
ship-to warehouse, Ship Site, Salesperson, order default, multi-site shipment

## Customers form — Credit tab

On Credit, review the Credit Limit and customer-level Credit Hold with an authorized credit role. A credit-limit warning during order entry does not by itself prove that the customer or every order is held; order behavior depends on A/R and order-entry parameters. Customer-level Credit Hold blocks shipments for that customer but does not set the Credit Hold field on each individual customer order. Use Customer Orders to inspect an order-level hold. Never advise bypassing or clearing a hold without the site's approval procedure.

**Section Summary:** Customer credit limit, customer hold, and order hold are separate controls.

### Keywords
Credit tab, Credit Limit, Credit Hold, customer hold, order hold, cannot ship

## Customers form — Contacts tab

Use Contacts to maintain the people responsible for order and billing communication. Order Contact may default to a new order and can be changed on that order. Billing Contact identifies the person for invoices. The Customer Orders Bill To contact is derived from Customers, while its Ship To contact is derived from Customer Ship-Tos. Check contact ownership before changing it; updating an order contact is not necessarily a master-data change. Handle personal contact details under local privacy and access rules.

**Section Summary:** Order, billing, and shipping contacts have different owners and defaults.

### Keywords
Contacts tab, Order Contact, Billing Contact, Ship To Contact, invoice contact

## Customers form — Codes tab

Use Codes to review customer-level default codes that the site requires, such as sales, tax, shipping, or other configured classifications. The exact fields and permitted values depend on local setup. A code selected on the customer or ship-to can influence a new order, but the saved order fields must be checked independently. If a code is missing or rejected, capture the field label and error and ask the responsible master-data or configuration owner; do not invent a replacement value.

**Section Summary:** Codes establish defaults that require site-specific validation on the resulting order.

### Keywords
Codes tab, customer codes, tax code, shipping code, missing code, default fields

## Customers form — CRM and interactions

When CRM is enabled, use the CRM tab to review sales team and customer-contact associations. Customer Interactions is a related record of contact activity; its view on Customers is display-only, with the underlying activity maintained in Customer Interactions. Confirm converted prospect contacts and salesperson ownership after Move Prospect To Customer. A sales contact or interaction does not itself prove that a bill-to, ship-to, or active customer account is ready for an order.

**Section Summary:** CRM relationships support the account but do not replace customer and ship-to setup.

### Keywords
CRM tab, Customer Interactions, sales contacts, converted prospect, salesperson

## Customers form — Corporate Customer tab

Corporate Customer can define a two-tier relationship between separate customer accounts. A corporate customer may be linked to subordinate customers. The Corporate Cust field determines which account is corporate; Corp. Credit selects whether the corporate customer's credit values are used for credit-limit processing. This is not the same as a ship-to relationship. Confirm whether a corporate bill-to or consolidated payment arrangement applies before interpreting balances, exposure, or invoice ownership.

**Section Summary:** Corporate and subordinate customers affect credit and payment interpretation.

### Keywords
Corporate Customer tab, Corporate Cust, Corp. Credit, subordinate customer, corporate bill-to

## Customers form — payment and balance views

Payment History shows sales and payment history values, many maintained by normal posted transactions and utilities. Its monetary amounts are displayed in domestic currency. Posted Balance and On Order Balance are current ERP data, not facts stored in this article; in a multi-site setup, the globe symbol on certain credit and balance fields indicates global accumulated values. For a live balance question, obtain the user-authorized value from SyteLine with site, currency, and as-of context. Do not calculate available credit from an old screenshot.

**Section Summary:** Balance and history fields need a current, permission-aware ERP read.

### Keywords
Payment History, Posted Balance, On Order Balance, global balance, current balance

## Customers form — optional regional and billing tabs

The EU VAT tab is enabled only when EU reporting is activated; validate the required VAT and tax information under local policy. Revision/Pay supports invoice revision days and pay days when that process is used. Currency Codes supports multiple customer currencies where configured. These are conditional screens, not universal steps for every customer. A missing optional tab may reflect configuration, release, customization, or access; it is not proof that the customer is incomplete.

**Section Summary:** Regional and specialized billing tabs apply only when their features are enabled.

### Keywords
EU VAT, Revision/Pay, Currency Codes, optional tab, multi-currency customer

## Multi-site customer maintenance

Multi-Site Customers is intended for authorized work at a master site; Customers remains the local-site form. Multi-Site Customer Ship-Tos can maintain eligible ship-to details for sites in the same intranet when replication and shared-code prerequisites are met. Some identity and currency fields are shared across sites, while other details can vary by site. Confirm the current site, target site, replication status, and actual visibility before changing a shared customer. Do not infer access to another site's customer from a matching customer number alone.

**Section Summary:** Multi-site forms and shared fields require master-site and replication checks.

### Keywords
Multi-Site Customers, Multi-Site Customer Ship-Tos, master site, replication, customer site

## Customer Hub — search and navigate

Where Customer Hub is deployed, search by customer name or number. The hub summarizes account details, ship-tos, contacts, credit indicators, and related activity; its buttons can open Ship Tos, Pricing, and a new Customer Order. A hub tile is navigation or a summary, not authorization to view hidden records or perform a transaction. Confirm data in the owning Customers, Customer Ship-Tos, or Customer Orders form before acting. Some hub sections may be absent or customized in a particular installation.

**Section Summary:** Customer Hub helps navigation but does not replace owning forms or permissions.

### Keywords
Customer Hub, search customer, Ship Tos button, Create New Customer Order, customer overview

## First-order readiness checklist

Before Customer Orders entry, verify the selected customer number and site; bill-to identity and address; chosen ship-to number, address, and contact; Terms Code and currency; tax and shipping defaults; warehouse or ship site if applicable; and any customer credit hold. After saving the Customer Orders header, review the actual transaction values because defaults can be overridden or recalculated. Create lines only after the header is correct. Order pricing, availability, shipping, invoicing, and payment are covered by their owning modules.

**Section Summary:** Validate the customer and destination before booking the first order.

### Keywords
first order checklist, order readiness, customer defaults, customer order handoff, new customer

## Why an account may not appear in order entry

Check the current site, customer number/name, active or order-processing status, form filters, and the user's SyteLine permissions. For a newly created record, confirm it was saved and refreshed. For a multi-site account, confirm that the record exists in the order-entry site and that required replication completed. For converted prospects, verify the new customer number rather than continuing to search only by prospect number. Record the exact message and context before escalating; a missing lookup result has several possible causes.

**Section Summary:** Customer lookup failure needs site, status, save, filter, and access checks.

### Keywords
customer not found, cannot select customer, inactive customer, wrong site, customer lookup

## Why an order shows the wrong customer details

First identify the saved order number, customer number, Ship To number, and site. Compare the order's bill-to, ship-to, terms, tax, and contact values with the current customer and ship-to records. A customer-master change may not retroactively correct an existing order. If the order was copied from an estimate or created by an integration, inspect its saved fields rather than assuming defaulting followed manual order entry. Escalate a correction to the authorized owner when shipments or invoices already exist.

**Section Summary:** Compare saved transaction values with current master data before correcting a mismatch.

### Keywords
wrong address on order, wrong terms, copied estimate, default mismatch, correct customer order

## Security and data boundary for chatbot answers

This article can explain forms, field meanings, and generic workflow. A specific customer's balance, credit exposure, open orders, contacts, or invoices requires a current SyteLine read using the logged-in user's effective permissions and site context. The chatbot must not treat a visible hub summary or group name as proof of field- or row-level access. Creating or editing customers, changing credit, and changing orders require separate action permissions and audit. Do not include real customer data in this knowledge article or its Q&A workbook.

**Section Summary:** Static guidance is separate from live, permission-checked customer data and actions.

### Keywords
customer permissions, live balance, RBAC, site access, chatbot customer security
