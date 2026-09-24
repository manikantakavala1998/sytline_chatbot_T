# Invoice and Credit Memo Module

## What creates an invoice

For a standard customer order, shipped but uninvoiced line/release quantities are selected by Order Invoicing/Credit Memo. Running that process calculates amounts, records invoice history, creates A/R invoice transactions, and produces the invoice. Shipping alone does not mean the invoice has already been generated. Invoice Hold can prevent a line from being invoiced. Consolidated invoicing and delivery orders have separate paths.

**Section Summary:** A standard order invoice follows a shipping transaction and an invoicing process.

### Keywords
invoice, Order Invoicing/Credit Memo, shipped not invoiced, Invoice Hold

## Standard order invoicing steps

1. Confirm that the intended order line/release quantity has a posted shipping transaction.
2. Run To Be Invoiced Report to identify eligible lines and check invoice holds.
3. Open Order Invoicing/Credit Memo, select Invoice, and set the intended customer/order/date ranges and print options.
4. Preview or review totals, tax, freight, terms, ship-to, and currency as the site permits.
5. Process with appropriate authorization; verify the invoice number and posted A/R transaction.
6. Confirm document delivery using the site's document profile or communication process.

**Section Summary:** Verify shipped quantity and eligibility, process the invoice, then confirm A/R posting.

### Keywords
create invoice, To Be Invoiced Report, invoice number, A/R transaction

## Due date, amount, and corrections

Terms and invoice dates determine due scheduling according to the configured billing rules; some terms permit multiple due dates. A posted invoice is a financial transaction, so a correction uses an approved credit/debit memo or return process rather than casual editing. For inventory returns, RMA and material return processing may be required before a credit memo. For noninventory charges, A/R's Invoices, Debit and Credit Memos form has a different use.

**Section Summary:** Use the transaction-specific correction path and preserve posted financial history.

### Keywords
invoice due date, credit memo, debit memo, invoice correction, RMA

## Why an expected invoice is missing

Check whether the order line was shipped, whether shipping posted, whether Invoice Hold is selected, whether a different consolidated/delivery-order billing route applies, and whether the invoicing process completed or stopped on an error. Order Invoicing/Credit Memo can leave earlier invoices posted when a later selected invoice fails. Compare shipment and invoice history before reporting that nothing was billed.

**Section Summary:** Separate missing shipment, invoice hold, different billing route, and process error.

### Keywords
invoice not generated, shipped not invoiced, billing error, invoice hold

## Invoice data and reconciliation

| Data on or around the invoice | What to verify |
| --- | --- |
| Invoice number and date | Identity and posting period of the billing document. |
| Customer and bill-to | Party responsible for payment. |
| Order and shipment references | Source of the billed goods or services. |
| Line/release and billed quantity | The portion of the order being billed now. |
| Unit price, discount, freight, tax, total | Components of the amount charged. |
| Terms and due date(s) | Payment schedule calculated under customer/order terms. |
| A/R transaction and open amount | Posted receivable and any remaining balance after credits or payments. |

Compare ordered, shipped, and invoiced quantities at line level. A partial shipment or invoice hold can explain why the invoice does not equal the original order total. A/R payment status must be checked separately from invoice posting.

**Section Summary:** Reconcile the billed quantity and amount with shipment, order, and A/R.

### Keywords
invoice fields, invoice total, billed quantity, due date, A/R open amount

## Exceptions and correction path

If the To Be Invoiced Report omits a line, verify the ship transaction, invoice hold, line/order type, shipment approval, and whether the line already invoiced. If Order Invoicing/Credit Memo stops on an error, examine which earlier invoices posted and correct only the failed item. If an invoice amount is disputed, compare order and invoice price, discount, freight, tax, and quantity; then use an authorized credit/debit memo or RMA path as appropriate. Do not overwrite a posted invoice as if it were a draft estimate.

**Section Summary:** Diagnose billing eligibility and preserve the posted transaction trail.

### Keywords
To Be Invoiced missing, invoice process error, disputed invoice, credit memo
