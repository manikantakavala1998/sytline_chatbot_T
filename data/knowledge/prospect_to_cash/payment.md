# Payment and Accounts Receivable Module

## What A/R tracks

Accounts Receivable tracks posted customer invoices, credit and debit memos, payments, open items, and aging. A shipment, an invoice, and a payment are separate events. The customer balance and invoice paid status are live financial facts and must be read from authorized current SyteLine records. A/R normally receives sales invoices from Customer Service's invoicing process.

**Section Summary:** Payment settles A/R items; order or shipment status alone does not prove settlement.

### Keywords
payment, accounts receivable, open item, customer balance, invoice paid

## Record and apply a customer payment

1. Identify the customer, payment type/number, amount, currency, receipt date, and bank or cash context under local controls.
2. Enter the payment on A/R Payments or use A/R Quick Payment Application if available.
3. Select the open invoice(s), credit(s), or finance charge(s) the customer intended to settle; a payment may be full, partial, or open/unapplied.
4. Review distributions and discounts, deductions, and currency differences where relevant.
5. Save and post with authorized A/R processing, then verify the posted payment and remaining open balance.
6. For an unapplied payment, investigate remittance details and apply it later through the approved A/R process.

**Section Summary:** Enter, distribute, post, and verify payment against the intended open item.

### Keywords
A/R Payments, A/R Quick Payment Application, partial payment, open payment, payment distribution

## Aging and collections review

A/R Aging Report groups open balances into configurable aging buckets and can show detailed open items or customer summaries. Run it with the right as-of date, customer, currency, and site context; a past-due label depends on these options and billing terms. Customer statements and collection follow-up may use the results, but the report is not a substitute for checking the specific invoice and payment applications.

**Section Summary:** Aging is a report view of open receivables as of selected criteria.

### Keywords
overdue invoice, A/R Aging Report, aging buckets, collections, statement

## Troubleshoot unpaid or unmatched items

If a customer says they paid, look for the payment in A/R, confirm its posting status and customer, inspect distributions against the invoice, and check whether it remains open or was applied to another item. If a payment amount differs, inspect partial application, credits, discounts, currency, and bank reference. Do not disclose or infer a balance from static knowledge. Reversals and adjustments require the site's A/R controls.

**Section Summary:** Check payment posting and invoice distribution before concluding an invoice is unpaid.

### Keywords
payment not applied, unpaid invoice, missing payment, A/R discrepancy

## Payment lifecycle and key fields

| Data | What it means |
| --- | --- |
| Payment number/type | Identifies the remittance, such as check or wire under the site's supported types. |
| Customer and currency | Party and monetary unit to which the receipt belongs. |
| Receipt date and amount | When and how much cash was recorded. |
| Distribution or apply-to invoice | Which open item receives the payment. |
| Open/unapplied amount | Receipt not yet allocated to an invoice or charge. |
| Posted status | Whether the transaction has entered the A/R ledger process. |

One payment can be distributed across several invoices; one invoice can receive partial payments and remain open. Credits or adjustments may also reduce the open amount without a new cash receipt. To answer “Is invoice X paid?”, inspect posted invoice detail, applications, and remaining open amount in the authorized site and currency.

**Section Summary:** Payment entry, application, posting, and final invoice balance are different checkpoints.

### Keywords
payment number, payment distribution, apply to invoice, unapplied payment

## Aging and dispute decisions

Start with the selected A/R Aging Report's as-of date and bucket basis, then drill into the exact invoice. If the customer disputes a charge, separate a billing error from a missing payment application or unresolved return. Check credits and finance charges as well as receipts. A reminder should reference a verified open item under local policy; do not send or recommend collection action from a stale report alone.

**Section Summary:** A/R follow-up requires invoice-level verification, not only an aging total.

### Keywords
aging bucket, invoice dispute, missing payment application, collection follow-up
