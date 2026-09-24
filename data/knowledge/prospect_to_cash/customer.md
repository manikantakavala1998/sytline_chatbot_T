# Customer Module

## Meaning and forms

The Customers record is the trading account used for billing, shipping, orders, and receivables. A customer may be created directly or through Move Prospect To Customer. A customer can have one bill-to address and multiple ship-to locations. The Customer Ship Tos form maintains delivery locations; a specific ship-to can carry its own contact and codes.

**Section Summary:** Customer setup controls the account and address defaults used downstream.

### Keywords
customer, Customers form, bill to, ship to, customer master

## Set up and validate a customer

1. Search existing Customers, Prospects, and corporate/subordinate relationships before adding a new account.
2. Enter or allow generation of the customer number; confirm legal name, bill-to address, contact, and site.
3. Set billing terms, currency, language, bank, tax, and credit details as required by the site's accounting policy.
4. Save the customer; add ship-to records through Customer Ship Tos and review each address and shipping contact.
5. Connect sales contacts and salesperson/territory data where CRM uses them.
6. Validate the first estimate or order defaults for customer, ship-to, terms, currency, and tax before processing.

**Section Summary:** Review account, bill-to, ship-to, financial codes, and sales links before order entry.

### Keywords
create customer, customer number, Customer Ship Tos, billing terms, currency

## Credit and balance are separate facts

Customers can carry a credit limit and a customer-level Credit Hold. A customer-level hold can prevent shipments without setting each order's Credit Hold checkbox. A balance is a live receivable figure and must come from an authorized SyteLine read; this article does not contain any customer's balance. Review corporate credit and multi-site settings before interpreting available credit.

**Section Summary:** Credit configuration and current balance need permission-aware, current ERP data.

### Keywords
customer balance, credit limit, customer credit hold, corporate credit

## Troubleshooting customer selection

If an order shows the wrong address, verify the selected customer and ship-to rather than assuming the customer master is wrong. If the customer cannot be selected, check site, account status, and permissions in the actual application. For converted prospects, verify the new customer number and reassigned contact/estimate links. Do not infer security settings from a missing result alone.

**Section Summary:** Inspect party, ship-to, site, and conversion links when customer details look wrong.

### Keywords
wrong ship-to, customer not found, converted prospect, troubleshooting

## Customer master field groups

| Group | Meaning for Prospect-to-Cash |
| --- | --- |
| Customer number and bill-to | The account and address receiving the financial obligation. |
| Ship-to number and address | The delivery location selected on an order; one customer can have multiple ship-tos. |
| Order and billing contacts | People for order communication and invoice delivery. |
| Terms and currency | Defaults used in invoicing, due dates, and payment processing. |
| Tax and freight codes | Inputs to calculation and fulfillment; check against the order. |
| Credit limit and Credit Hold | Controls that may restrict shipping, subject to A/R parameters. |
| Salesperson, territory, CRM contacts | Relationship ownership and reporting. |

Some values default onto an estimate or order but can be changed for that transaction. Therefore, the current customer master and the saved order should both be inspected when a user asks why a particular order has different terms or addresses.

**Section Summary:** Customer setup provides defaults; the saved transaction records the values actually used.

### Keywords
customer master fields, bill-to, ship-to, terms, currency, salesperson

## Conversion and first-order checks

After moving a Prospect to Customer, verify the new customer number, contact links, bill-to and ship-to setup, currency and terms, tax status, and credit configuration. Then test the intended order or estimate selection. A missing required finance code or ship-to can block the first transaction. A current balance or credit exposure must be obtained from authorized live A/R data; no static article can state it.

**Section Summary:** Validate customer setup before the first order, particularly after prospect conversion.

### Keywords
first order customer setup, converted customer, missing terms, ship-to
