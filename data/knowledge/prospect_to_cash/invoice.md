# Invoice and Credit Memo Module

## What creates an invoice

For a standard customer order, shipped but uninvoiced line/release quantities are selected by Order Invoicing/Credit Memo. Running that process calculates amounts, records invoice history, creates A/R invoice transactions, and produces the invoice. Shipping alone does not mean the invoice has already been generated. Invoice Hold can prevent a line from being invoiced. Consolidated invoicing and delivery orders have separate paths. [Infor order invoicing and credit memos](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html)

**Section Summary:** A standard order invoice follows a shipping transaction and an invoicing process.

### Keywords
invoice, Order Invoicing/Credit Memo, shipped not invoiced, Invoice Hold

## Standard order invoicing steps

1. Confirm that the intended order line/release quantity has a posted shipping transaction.
2. Run To Be Invoiced Report to identify eligible lines and check invoice holds.
3. Open Order Invoicing/Credit Memo, select Invoice, and set the intended customer/order/date ranges and print options.
4. Preview or review totals, tax, freight, terms, ship-to, and currency as the site permits.
5. Process with appropriate authorization; verify the invoice number and posted A/R transaction.
6. Confirm document delivery using the site's document profile or communication process. [Infor invoicing a customer order](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/invoicing_a_customer_order.htm) [Infor order invoicing and credit memos](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html)

**Section Summary:** Verify shipped quantity and eligibility, process the invoice, then confirm A/R posting.

### Keywords
create invoice, To Be Invoiced Report, invoice number, A/R transaction

## Due date, amount, and corrections

Terms and invoice dates determine due scheduling according to the configured billing rules; some terms permit multiple due dates. A posted invoice is a financial transaction, so a correction uses an approved credit/debit memo or return process rather than casual editing. For inventory returns, RMA and material return processing may be required before a credit memo. For noninventory charges, A/R's Invoices, Debit and Credit Memos form has a different use. [Infor accounts receivable steps](https://docs.infor.com/csi/10.x/en-us/csbiolh/financials_user_cl_sl/lsm1454143881752.html) [Infor RMA steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144038357.html)

**Section Summary:** Use the transaction-specific correction path and preserve posted financial history.

### Keywords
invoice due date, credit memo, debit memo, invoice correction, RMA

## Why an expected invoice is missing

Check whether the order line was shipped, whether shipping posted, whether Invoice Hold is selected, whether a different consolidated/delivery-order billing route applies, and whether the invoicing process completed or stopped on an error. Order Invoicing/Credit Memo can leave earlier invoices posted when a later selected invoice fails. Compare shipment and invoice history before reporting that nothing was billed. [Infor order invoicing and credit memos](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144031725.html)

**Section Summary:** Separate missing shipment, invoice hold, different billing route, and process error.

### Keywords
invoice not generated, shipped not invoiced, billing error, invoice hold
