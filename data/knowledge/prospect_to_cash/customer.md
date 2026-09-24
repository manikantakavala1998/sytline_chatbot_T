# Customer Module

## Meaning and forms

The Customers record is the trading account used for billing, shipping, orders, and receivables. A customer may be created directly or through Move Prospect To Customer. A customer can have one bill-to address and multiple ship-to locations. The Customer Ship Tos form maintains delivery locations; a specific ship-to can carry its own contact and codes. [Infor creating a customer](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/creating_a_customer.html) [Infor CRM scenario 5](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454144070919.html)

**Section Summary:** Customer setup controls the account and address defaults used downstream.

### Keywords
customer, Customers form, bill to, ship to, customer master

## Set up and validate a customer

1. Search existing Customers, Prospects, and corporate/subordinate relationships before adding a new account.
2. Enter or allow generation of the customer number; confirm legal name, bill-to address, contact, and site.
3. Set billing terms, currency, language, bank, tax, and credit details as required by the site's accounting policy.
4. Save the customer; add ship-to records through Customer Ship Tos and review each address and shipping contact.
5. Connect sales contacts and salesperson/territory data where CRM uses them.
6. Validate the first estimate or order defaults for customer, ship-to, terms, currency, and tax before processing. [Infor creating a customer](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/creating_a_customer.html) [Infor CRM overview](https://docs.infor.com/csi/10.x/en-us/csbiolh/sales_crm_user_cl_sl/mergedprojects/sl_custvend/other/overview/crm_overview.html)

**Section Summary:** Review account, bill-to, ship-to, financial codes, and sales links before order entry.

### Keywords
create customer, customer number, Customer Ship Tos, billing terms, currency

## Credit and balance are separate facts

Customers can carry a credit limit and a customer-level Credit Hold. A customer-level hold can prevent shipments without setting each order's Credit Hold checkbox. A balance is a live receivable figure and must come from an authorized SyteLine read; this article does not contain any customer's balance. Review corporate credit and multi-site settings before interpreting available credit. [Infor credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html)

**Section Summary:** Credit configuration and current balance need permission-aware, current ERP data.

### Keywords
customer balance, credit limit, customer credit hold, corporate credit

## Troubleshooting customer selection

If an order shows the wrong address, verify the selected customer and ship-to rather than assuming the customer master is wrong. If the customer cannot be selected, check site, account status, and permissions in the actual application. For converted prospects, verify the new customer number and reassigned contact/estimate links. Do not infer security settings from a missing result alone. [Infor creating a customer](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/creating_a_customer.html) [Infor Prospects form](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/crmtopics/prospects.htm)

**Section Summary:** Inspect party, ship-to, site, and conversion links when customer details look wrong.

### Keywords
wrong ship-to, customer not found, converted prospect, troubleshooting
