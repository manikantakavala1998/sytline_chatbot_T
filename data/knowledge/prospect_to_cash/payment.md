# Payment and Accounts Receivable Module

## What A/R tracks

Accounts Receivable tracks posted customer invoices, credit and debit memos, payments, open items, and aging. A shipment, an invoice, and a payment are separate events. The customer balance and invoice paid status are live financial facts and must be read from authorized current SyteLine records. A/R normally receives sales invoices from Customer Service's invoicing process. [Infor accounts receivable steps](https://docs.infor.com/csi/10.x/en-us/csbiolh/financials_user_cl_sl/lsm1454143881752.html)

**Section Summary:** Payment settles A/R items; order or shipment status alone does not prove settlement.

### Keywords
payment, accounts receivable, open item, customer balance, invoice paid

## Record and apply a customer payment

1. Identify the customer, payment type/number, amount, currency, receipt date, and bank or cash context under local controls.
2. Enter the payment on A/R Payments or use A/R Quick Payment Application if available.
3. Select the open invoice(s), credit(s), or finance charge(s) the customer intended to settle; a payment may be full, partial, or open/unapplied.
4. Review distributions and discounts, deductions, and currency differences where relevant.
5. Save and post with authorized A/R processing, then verify the posted payment and remaining open balance.
6. For an unapplied payment, investigate remittance details and apply it later through the approved A/R process. [Infor quick payment application](https://docs.infor.com/csi/latest/en-us/csbiolh/financials_user_cl_sl/lsm1454143884482.html) [Infor accounts receivable steps](https://docs.infor.com/csi/10.x/en-us/csbiolh/financials_user_cl_sl/lsm1454143881752.html)

**Section Summary:** Enter, distribute, post, and verify payment against the intended open item.

### Keywords
A/R Payments, A/R Quick Payment Application, partial payment, open payment, payment distribution

## Aging and collections review

A/R Aging Report groups open balances into configurable aging buckets and can show detailed open items or customer summaries. Run it with the right as-of date, customer, currency, and site context; a past-due label depends on these options and billing terms. Customer statements and collection follow-up may use the results, but the report is not a substitute for checking the specific invoice and payment applications. [Infor A/R Aging Report](https://docs.infor.com/csi/latest/en-us/csbiolh/financials_user_cl_sl/lsm1454143885762.html)

**Section Summary:** Aging is a report view of open receivables as of selected criteria.

### Keywords
overdue invoice, A/R Aging Report, aging buckets, collections, statement

## Troubleshoot unpaid or unmatched items

If a customer says they paid, look for the payment in A/R, confirm its posting status and customer, inspect distributions against the invoice, and check whether it remains open or was applied to another item. If a payment amount differs, inspect partial application, credits, discounts, currency, and bank reference. Do not disclose or infer a balance from static knowledge. Reversals and adjustments require the site's A/R controls. [Infor quick payment application](https://docs.infor.com/csi/latest/en-us/csbiolh/financials_user_cl_sl/lsm1454143884482.html) [Infor A/R distribution journal](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454143885138.html)

**Section Summary:** Check payment posting and invoice distribution before concluding an invoice is unpaid.

### Keywords
payment not applied, unpaid invoice, missing payment, A/R discrepancy
