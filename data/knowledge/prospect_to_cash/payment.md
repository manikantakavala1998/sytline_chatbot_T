# Payment and Accounts Receivable Module

This Customer-to-Cash article paraphrases the official Infor SyteLine Financials User Guide, release 9.01.x, with the Customer Service User Guide for the invoice-to-A/R handoff. Printed guide pages are shown per topic. The article cannot report a named customer's balance or grant payment-posting permission; those require current, authorized SyteLine data and local controls.

## Document Metadata

- **Module:** payment
- **Tags:** prospect-to-cash, customer-to-cash, accounts-receivable, payment, application, aging
- **Document Owner:** Accounts Receivable
- **Reviewed / Approved By:** User-authorized knowledge activation; SyteLine SME review pending
- **Last Reviewed:** 2026-10-08
- **Version:** Infor SyteLine Financials User Guide 9.01.x and Customer Service User Guide 9.01.x
- **Source:** Infor SyteLine Financials User Guide 9.01.x, printed pages 113-118, 131-143, 147-155, 161-167; Infor SyteLine Customer Service User Guide 9.01.x, printed pages 44-46

## Invoice-to-A/R handoff

Customer Service invoicing creates an A/R invoice transaction; receiving cash and applying it are later financial steps. A shipped order, posted invoice, entered receipt, and fully settled invoice are not interchangeable statuses.

**Section Summary:** Invoice posting starts receivables; payment distribution settles selected items.
**Guide pages:** Customer Service 45; Financials 113, 132
### Keywords
invoice, A/R, receipt, application, open balance

1. **Does a shipped order prove the customer paid?** No; shipment precedes invoice and payment processing.
2. **What does standard order invoicing create in A/R?** An A/R invoice transaction.
3. **Does an entered payment alone prove an invoice is settled?** No; review distribution and posting.
4. **Which financial area records customer receipts?** Accounts Receivable.
5. **What is needed to answer whether a named invoice is paid?** Authorized posted invoice, payment application, and remaining-balance data.

## A/R Payments purpose

The A/R Payments form processes customer payments for invoices, finance charges, and other amounts owed. Non-customer payments can instead be posted as non-A/R cash to the G/L.

**Section Summary:** A/R Payments is the main customer-receipt entry form.
**Guide pages:** Financials 132, 135
### Keywords
A/R Payments, customer receipt, finance charge, non-A/R cash

1. **Which form enters ordinary customer payments?** A/R Payments.
2. **Can it record payments for invoiced amounts?** Yes.
3. **Can it record payment of finance charges?** Yes.
4. **Can non-customer cash use A/R distribution logic?** The guide allows non-A/R cash posting to the G/L.
5. **What should be determined before using non-A/R cash?** Whether the receipt actually belongs to a customer open item.

## Customer and payment identity

On A/R Payments, Actions > New starts a receipt. Customer identifies whose account is affected; Type defaults from the customer but may be changed; Number identifies the check or draft. Verify remittance before selecting the customer and number.

**Section Summary:** Customer, method, and check/draft number establish payment identity.
**Guide pages:** Financials 135
### Keywords
Customer, Type, Number, check, draft

1. **Which action begins a new A/R payment?** Actions > New.
2. **What does Customer identify?** The customer whose payment is entered.
3. **What is the default for Type?** The customer's default payment method.
4. **Can Type be changed?** Yes, to another supported method.
5. **What is entered in Number?** The check or draft number.

## Receipt, due, and deposit dates

Receipt Date is when the payment was received. Payment Due Date appears for Draft. Deposit Date is available for post-dated checks only when Type is Check and no credit memo is associated. These dates are different business events.

**Section Summary:** Date fields distinguish receipt, draft maturity, and check deposit.
**Guide pages:** Financials 135
### Keywords
Receipt Date, Payment Due Date, Deposit Date, post-dated check

1. **What does Receipt Date record?** The date the payment was received.
2. **What is its default?** The current date.
3. **When is Payment Due Date available?** For Draft payment type.
4. **When is Deposit Date enabled?** For Check type without an associated credit memo.
5. **What use does Deposit Date support?** Entry of post-dated checks.

## Reference, description, bank, and amount

G/L Reference and Description appear in the distribution journal; the reference defaults to ARP plus the check/draft number. Bank Code defaults from the customer but can be changed. Customer Amount is the receipt amount to distribute.

**Section Summary:** Enter the journal reference, receiving bank, and customer amount accurately.
**Guide pages:** Financials 135
### Keywords
G/L Reference, Description, Bank Code, Customer Amount

1. **Where does G/L Reference appear?** In the distribution journal.
2. **What is its default pattern?** ARP followed by the check or draft number.
3. **What does Bank Code identify?** The bank into which the payment will be deposited.
4. **Can the default bank code be changed?** Yes.
5. **Which field holds the receipt value?** Customer Amount.

## Save, distribute, then post

The guide saves the A/R Payments record before distribution. Distributions specify the invoices, charges, open payment, or non-A/R cash destinations; a posting step then commits balanced transactions. The three stages must be verified separately.

**Section Summary:** Entry, application, and posting are distinct actions.
**Guide pages:** Financials 132, 135-137, 161-162
### Keywords
save payment, distribution, posting, A/R workflow

1. **What action saves the entered payment?** Actions > Save.
2. **What must happen before posting?** Apply or distribute the payment amount.
3. **Which button opens the distribution form?** Distributions.
4. **Does Save alone post the receipt?** No; A/R Payment Posting is a later step.
5. **What should be checked after posting?** Posted transactions and remaining invoice/open-item balances.

## Automatically generated distributions

Actions > Generate Distribution on A/R Payments or A/R Payment Distributions creates distributions automatically. The operator can inspect them through Distributions. The documented default G/L account comes from Accounts Receivable Parameters.

**Section Summary:** Automatic distribution still requires review before posting.
**Guide pages:** Financials 136
### Keywords
Generate Distribution, A/R Payment Distributions, G/L default

1. **Which action generates distributions automatically?** Actions > Generate Distribution.
2. **Which forms offer that action?** A/R Payments or A/R Payment Distributions.
3. **How can generated distributions be reviewed from A/R Payments?** Click Distributions.
4. **Where does the automatic G/L default come from?** Accounts Receivable Parameters.
5. **Does automatic generation remove the balance requirement?** No; the distributions must balance to the payment.

## Manual distribution entry

A/R Payment Distributions allows manual selection of customer, payment type, number, bank code, and distribution type. The selected type determines additional fields. A payment's applied total must equal its check amount or posting is canceled.

**Section Summary:** Manual distributions direct the receipt and must balance.
**Guide pages:** Financials 136-139
### Keywords
manual distribution, distribution Type, balanced payment

1. **Which form holds manual distributions?** A/R Payment Distributions.
2. **Which action adds a distribution?** Actions > New.
3. **What identifies the receipt being distributed?** Customer, payment type, check/draft Number, and Bank Code.
4. **What decides which additional fields are shown?** Distribution Type.
5. **What happens if distributed amount differs from check amount?** Posting detects the imbalance and cancels.

## Invoice distribution fields

For an Invoice distribution, select the customer's invoice, inspect Site and Order, enter Dist Amount, and review Disc/Credit 1 and Allowance/Credit 2. The site displayed is the invoice-owning site but can be changed according to the guide and permitted configuration.

**Section Summary:** Invoice distributions name a specific invoice and applied amount.
**Guide pages:** Financials 137-138
### Keywords
Invoice distribution, Dist Amount, Site, Disc/Credit 1

1. **What transaction is selected for Invoice Type?** The customer's invoice number.
2. **What does Site initially show?** The site owning the invoice.
3. **What does Dist Amount specify?** The amount applied through that distribution.
4. **What can Disc/Credit 1 show before the discount date?** The invoice discount amount.
5. **What is Allowance/Credit 2 used for?** An allowance or second credit distribution amount.

## Open payment and Open Credit

A payment can be distributed as Open Credit instead of to a specific invoice. For an open-item customer, the credit/payment can later be reapplied to an invoice or finance charge. Balance-forward customers use the account-balance approach identified by the guide.

**Section Summary:** An open receipt remains available for later application.
**Guide pages:** Financials 132, 135, 165-166
### Keywords
Open Credit, open payment, balance forward, reapplication

1. **Which distribution type creates an open payment?** Open Credit.
2. **Does an open payment name a settled invoice immediately?** No.
3. **What can happen later for an open-item customer?** Reapply it to an invoice or finance charge.
4. **What customer method uses account-balance payment?** Balance forward.
5. **What should be checked when a receipt exists but an invoice remains open?** Whether the receipt is still an open payment.

## Finance-charge and non-A/R destinations

The guide permits distributions to finance charges and non-A/R cash. Non-A/R distributions are entered on A/R Payment Distributions, not in the Quick Payment grid. Use the destination that matches the remittance and local accounting policy.

**Section Summary:** A receipt need not apply only to standard invoices.
**Guide pages:** Financials 132, 137-139, 152
### Keywords
finance charge, non-A/R cash, distribution type

1. **Can a customer payment pay a finance charge?** Yes.
2. **Where is a non-A/R cash distribution entered?** A/R Payment Distributions.
3. **Does Quick Payment directly enter non-A/R distributions?** No.
4. **What should be checked before choosing non-A/R cash?** Whether the amount is outside customer receivables.
5. **Why does distribution Type matter?** It changes the target item and account fields.

## Discounts and allowances

Invoice distributions can carry Disc/Credit 1 and Allowance/Credit 2. Discount defaults depend on receipt date relative to discount date, and account fields may default from A/R Parameters. Verify the applicable terms and tax settings before changing the amounts.

**Section Summary:** Discounts and allowances are explicit distribution components.
**Guide pages:** Financials 137-139
### Keywords
discount date, Disc/Credit 1, Allowance/Credit 2

1. **When can Disc/Credit 1 display a default invoice discount?** When receipt date precedes the invoice discount date.
2. **Can that displayed amount be changed?** Yes, within authorized accounting controls.
3. **What is the second allowance field named?** Allowance/Credit 2.
4. **Where can discount account defaults come from?** Accounts Receivable Parameters.
5. **What should be checked before claiming a discount is valid?** Terms, discount date, amounts, and tax configuration.

## Multiple-due-date payment

When a payment is applied toward one due date of a multi-due-date invoice, the system creates a partial payment record. Multiple payments for the same invoice are still represented by one record for that invoice under the documented distribution behavior.

**Section Summary:** Payment can target a due installment rather than the entire invoice.
**Guide pages:** Financials 132
### Keywords
multiple due dates, installment, partial payment

1. **Can a payment target one due date on an invoice?** Yes.
2. **What record is created for that case?** A partial payment record.
3. **Does paying one due installment prove the whole invoice is paid?** No.
4. **How many records are described if several payments apply to the same invoice?** One record for that invoice.
5. **What must a paid-status answer inspect?** All due amounts and remaining posted balance.

## A/R Quick Payment Application purpose

Quick Payment Application supports full/partial payment, open payment, finance-charge payment, and reapplication of open payments or credits. The Quick button from A/R Payments or A/R Payment Distributions opens it.

**Section Summary:** Quick Payment combines entry and selection of common open items.
**Guide pages:** Financials 152
### Keywords
A/R Quick Payment Application, full payment, partial payment

1. **Which form supports full and partial customer payments?** A/R Quick Payment Application.
2. **Can it create an open payment?** Yes.
3. **Can it pay a finance charge?** Yes.
4. **Can it reapply open payments and credits?** Yes.
5. **How can it be opened from A/R Payments?** Click Quick.

## Quick Payment grid

After payment details are saved, the grid shows the customer's open invoices, credit memos, finance charges, and open payments. Select items individually or Select All, then Apply. Debit memos and non-A/R distribution entry follow other paths.

**Section Summary:** Save first, select matching open items, then Apply.
**Guide pages:** Financials 152-154
### Keywords
Quick Payment grid, Selected, Select All, Apply

1. **When do open items appear in the Quick Payment grid?** After the payment is saved.
2. **What items can appear there?** Open invoices, credit memos, finance charges, and open payments.
3. **How is one item chosen?** Select its Selected check box.
4. **How are all displayed items chosen?** Select All.
5. **What applies the chosen items?** Apply.

## Quick Payment open remainder

Quick Payment can create an open payment for the whole receipt or leave a remainder open after selected invoices or finance charges are applied. When multiple invoices and open credits/payments are selected, the guide says oldest open transaction is applied to oldest invoice; it does not allow entering a specific invoice number for that open portion.

**Section Summary:** Unallocated receipt value remains open for later use.
**Guide pages:** Financials 153
### Keywords
open remainder, Quick Payment, oldest open transaction

1. **How is the whole Quick Payment left open?** Save the payment without selecting transactions, then Apply.
2. **How can only part be left open?** Select the intended invoices or charges; the remaining amount becomes open.
3. **What ordering applies with multiple open items?** Oldest open transaction to oldest invoice.
4. **Can the operator enter a specific invoice number for an open portion in that case?** No.
5. **What should be checked after partial application?** The applied amount and remaining open payment.

## Reapply open payment in Quick Payment

For an already posted open payment, enter its customer and matching check number or select it in the grid, save, choose target transactions, then Apply. The guide documents ARPR journal references and recommends verifying posted transaction detail.

**Section Summary:** Reapplication moves a posted open receipt to selected open items.
**Guide pages:** Financials 154-155
### Keywords
reapply, open payment, open credit, ARPR

1. **Which check number is used when entering an open payment to reapply?** The number matching the posted open payment.
2. **When can target invoices be selected?** After saving the reapplication entry.
3. **Which action completes Quick reapplication?** Apply.
4. **What journal reference identifies this reapplication?** ARPR.
5. **Where is the result verified?** A/R Posted Transactions Detail.

## Quick Payment limitations

The guide excludes debit memos from Quick Payment because an invoice number cannot be entered for them there; use A/R Posted Transactions instead. Non-A/R distributions must be entered in A/R Payment Distributions. Quick Payment also restricts movement of subordinate-customer credits across sibling accounts.

**Section Summary:** Quick Payment does not replace every A/R application form.
**Guide pages:** Financials 152
### Keywords
debit memo, non-A/R, corporate customer, subordinate

1. **Why are debit memos absent from Quick Payment?** The form cannot enter the required invoice number for them.
2. **Where are debit memos applied instead?** A/R Posted Transactions.
3. **Where are non-A/R payment distributions entered?** A/R Payment Distributions.
4. **Can one subordinate's open credit be applied to a sibling subordinate?** No.
5. **Whose open credits can a corporate customer apply according to the guide?** Its own and subordinate customers' eligible items.

## Multi-site application boundary

Payment distributions identify the invoice-owning site; centralized collection may create inter-site entries. In Quick Payment, drafts show only invoices from the current site, and applying a payment to an invoice at a site with a different domestic currency is unsupported.

**Section Summary:** Site ownership and domestic currency constrain cross-site payment use.
**Guide pages:** Financials 137, 152, 161-162
### Keywords
multi-site payment, invoice site, domestic currency, centralized collection

1. **What does Site show on an invoice distribution?** The site owning that invoice.
2. **Can centralized collection distribute one receipt across sites?** The guide gives such an example with inter-site accounting.
3. **What invoice scope does Quick Payment show for Draft in multi-site?** Current-site invoices only.
4. **Can Quick Payment apply across sites with different domestic currencies?** No.
5. **What must be checked before cross-site application?** Invoice site, site currency, and authorized accounting route.

## Payment currency conversion

A/R Payments supports invoices in multiple transaction currencies. Payment currency need not equal Bank Code currency: the payment is converted to bank amount and then domestic amount. Foreign-exchange differences may create A/R journal gains or losses.

**Section Summary:** Customer, bank, invoice, and domestic currencies can differ.
**Guide pages:** Financials 113, 132
### Keywords
payment currency, bank currency, domestic amount, exchange gain loss

1. **Can one A/R payment cover invoices with different transactional currencies?** Yes.
2. **Must payment currency equal the bank code currency?** No.
3. **What is the first conversion described?** Payment amount to bank amount.
4. **What follows that conversion?** Bank amount to domestic amount.
5. **Where can applicable multi-currency gains/losses appear?** In the A/R journal.

## Credit-card payment controls

Credit-card A/R payment handling depends on the Credit Card Interface being installed. In that case the guide prevents changing the payment amount and other components so they reconcile with the card charge, though the payment may be applied to multiple invoices.

**Section Summary:** Card reconciliation constrains edits but permits multiple applications.
**Guide pages:** Financials 132
### Keywords
credit card, Credit Card Interface, reconciliation

1. **When are the guide's credit-card payment controls available?** Only when the Credit Card Interface is used.
2. **Can the card payment amount be freely edited?** No.
3. **Why are card components protected?** To reconcile the A/R payment with the card charge.
4. **Can one card payment apply to several invoices?** Yes.
5. **What should be checked before explaining a missing card option?** Whether the Credit Card Interface is configured.

## A/R Payment Transaction Report

Before committing payment posting, the A/R Payment Posting form produces an A/R Payment Transaction Report as an edit report. Review the selected customer/bank/date/check range and distributions. A printed report is a review step, not proof of final posting.

**Section Summary:** Preview and verify the edit report before Commit.
**Guide pages:** Financials 132, 162
### Keywords
Payment Transaction Report, edit report, posting preview

1. **Which report is printed before posting?** A/R Payment Transaction Report.
2. **What is the report's role?** An edit report for review and verification.
3. **Can posting be narrowed to one receipt?** Yes, a single payment can be selected.
4. **Does printing the report itself post the payment?** No.
5. **What should be reviewed on the report?** Selected payment scope, amounts, and distributions.

## A/R Payment Posting Commit

A/R Payment Posting defaults to all customers unless ranges or a single payment are selected. First Process the required report, then enable Commit and Process again. Correct transaction errors before retrying; errored transactions are not posted.

**Section Summary:** Report review precedes the Commit posting action.
**Guide pages:** Financials 161-162
### Keywords
A/R Payment Posting, Commit, Process, posting error

1. **Which form posts ordinary A/R payments?** A/R Payment Posting.
2. **What is the default customer scope?** All customers.
3. **Which criteria can narrow it?** Customer, bank code, receipt date, check number, or one payment.
4. **What enables Commit?** Processing and reviewing the required report first.
5. **What happens to a transaction with errors?** It is not posted until corrected.

## A/R posting account prerequisite

The Accounts Receivable account must be assigned on the Accounts tab of Accounts Receivable Parameters. Otherwise posting displays an error and stops. This configuration prerequisite is not an invitation for a chatbot to alter accounts.

**Section Summary:** Missing A/R account setup blocks payment posting.
**Guide pages:** Financials 161
### Keywords
Accounts Receivable Parameters, A/R account, posting stop

1. **Which parameter account is required for payment posting?** The Accounts Receivable account.
2. **Where is it assigned?** Accounts tab of Accounts Receivable Parameters.
3. **What happens if it is absent?** An error displays and posting stops.
4. **Can a knowledge answer repair this live configuration?** No; an authorized financial administrator must review it.
5. **What should be checked first for this posting error?** The configured A/R account on the parameter form.

## Open payment tied to an order

When posting an A/R open payment tied to a customer order, SyteLine asks whether to apply it as a prepaid order amount. Yes posts and updates the order, No posts without updating it, and Cancel stops the action. This choice must be made by an authorized operator.

**Section Summary:** The order-prepayment prompt changes the posting outcome.
**Guide pages:** Financials 162
### Keywords
open payment, prepaid customer order, Yes No Cancel

1. **When does the prepaid-order prompt appear?** When posting an open A/R payment tied to a customer order.
2. **What does Yes do?** Posts the payment and updates the order.
3. **What does No do?** Posts without updating the order.
4. **What does Cancel do?** Cancels posting and the order update.
5. **Can the chatbot choose this outcome from a manual?** No; it requires live context and operator authority.

## A/R Distribution Journal

The A/R Distribution Journal records invoices, credit/debit memos, finance charges, and payments before eventual G/L posting. Posted journal transactions cannot be directly updated, although text can be added. Posted Transactions Detail and Summary show transaction evidence.

**Section Summary:** The distribution journal and posted views provide the audit trail.
**Guide pages:** Financials 163
### Keywords
AR DIST, journal, Posted Transactions Detail, Summary

1. **Which journal records A/R payment transactions?** The A/R Distribution Journal.
2. **What other transaction types appear there?** Invoices, credit/debit memos, and finance charges.
3. **Can posted journal transactions be directly edited?** No.
4. **Where can posted transaction details be viewed?** A/R Posted Transactions Detail.
5. **Which view gives a transaction summary?** A/R Posted Transactions Summary.

## Reversing a posted payment

The 9.01.x guide's reversal procedure enters a negative A/R payment for the same customer and distributes it against the originally paid invoices or as the original open payment was distributed. It changes the duplicate check-number entry and then posts the reversal. This is a controlled financial action.

**Section Summary:** A posted receipt is reversed by a new negative transaction, not erased.
**Guide pages:** Financials 163
### Keywords
payment reversal, negative payment, original distribution

1. **What amount sign starts a posted-payment reversal?** A negative A/R payment.
2. **Which customer is used?** The customer on the original posted payment.
3. **How is its check number differentiated?** The guide adds a one or zero to the original number.
4. **Where is the negative amount distributed?** To the originally paid invoices or original open-payment destination.
5. **Should a posted payment simply be deleted?** No; use the documented reversal under financial authorization.

## Returned checks

The Returned Checks utility follows Accounts Receivable Parameters choices. It may generate debit memos per invoice or negative payment adjustments, with optional returned-check fees. The resulting invoice or adjustment posting steps differ by chosen configuration.

**Section Summary:** Returned-check correction depends on configured posting method.
**Guide pages:** Financials 140-143
### Keywords
Returned Checks, debit memo, payment adjustment, fee

1. **Which utility processes a returned check?** Returned Checks.
2. **Which parameters affect its result?** Generate Debit Memo per Invoice or Generate Payment Adjustment for Returned Checks.
3. **Can it generate a fee?** Yes, when returned-check fee settings are enabled.
4. **What posts generated debit memos?** Invoice Posting.
5. **What posts generated negative payment adjustments?** A/R Adjustment Posting.

## Chargebacks

A chargeback is a customer deduction, such as for damage or lateness. Chargebacks and deposit accounts are configured on A/R Parameters; types describe reasons. Chargebacks form captures amount, type, invoice/credit reference and approval status, and payment posting handles the approved result.

**Section Summary:** A customer deduction has its own review and posting path.
**Guide pages:** Financials 120-121
### Keywords
chargeback, deduction, Chargebacks, approved pending denied

1. **What is a chargeback?** An amount a customer deducts from payment for a stated reason.
2. **Where are chargeback reasons defined?** Chargeback Types.
3. **Where is a chargeback amount and status entered?** Chargebacks.
4. **Which statuses does the guide list?** Approved, Pending, or Denied.
5. **What does posting do for an approved chargeback?** It creates/posts a credit memo tied to the invoice under the documented route.

## Electronic A/R Payment Import

Electronic receipt files require mapping between bank file fields and SyteLine A/R payment/distribution fields. The guide uses A/R Customer Bank Account, Import Conversions, Field Mappings, and Import Mappings, with authorized logical-folder access. Imported data requires Workbench validation before posting.

**Section Summary:** Bank-file import is a mapped and reviewed A/R workflow.
**Guide pages:** Financials 147-151
### Keywords
A/R Payment Import, bank file, mapping, logical folder

1. **What links customers to routing/account data for import?** A/R Customer Bank Account.
2. **Which form maps incoming values to acceptable SyteLine values?** A/R Payment Import Conversions.
3. **Which form maps file fields?** A/R Payment Import Field Mappings.
4. **What defines a bank format and logical folder?** A/R Payment Import Mappings.
5. **Are bank reconciliation records imported with payment records?** No; posting creates them later.

## Import Workbench validation

A/R Payment Import Workbench lists imported batches, permits review/changes, and validates payment/distribution records. Processed means every payment in the batch was processed; Unprocessed can contain unprocessed, error, or held records. Imported discounts are supplied by the file or must be updated manually.

**Section Summary:** Imported batches must be validated and corrected before posting.
**Guide pages:** Financials 151
### Keywords
Import Workbench, Validate, Processed, Error, Hold

1. **Which form reviews imported receipt batches?** A/R Payment Import Workbench.
2. **What does Processed batch status mean?** Every payment record in that batch was processed.
3. **What can Unprocessed include?** Unprocessed, Error, or Hold records.
4. **Which action validates unprocessed/error payments?** Validate.
5. **Are distribution discounts automatically calculated on import?** No; they come from the file or manual update.

## A/R direct debit

Direct Debit requires customer banking and mandate setup plus configured receivable accounts. A/R Direct Debit Posting reports eligible ranges, lets the operator select Process rows, then Commits. Posting debits Direct Debit Receivable, credits A/R, marks status Generated, and triggers a DebitTransfer BOD.

**Section Summary:** Direct debit is a configured, mandate-backed payment route.
**Guide pages:** Financials 116-118, 164
### Keywords
direct debit, mandate, Direct Debit Receivable, DebitTransfer

1. **Which customer field identifies direct-debit payment method?** Payment Type set to Direct Debit.
2. **What identifies the customer's authorization agreement?** Mandate Reference.
3. **Which form posts direct-debit payments?** A/R Direct Debit Posting.
4. **What receivable account is debited on posting?** Direct Debit Receivable.
5. **What BOD is triggered?** DebitTransfer.

## Accounts Receivable Aging Report

The Accounts Receivable Aging Report shows current customer-balance status and helps find past-due invoices. The guide normally runs it at period end before statements. Choose report parameters, optionally Preview, then Print; the default selection covers all customers.

**Section Summary:** Aging is a parameterized report, not a static balance stored in this article.
**Guide pages:** Financials 167
### Keywords
Accounts Receivable Aging Report, past due, statement, Preview

1. **Which report displays customer-balance status?** Accounts Receivable Aging Report.
2. **When is it normally printed?** At period end before statements.
3. **What issue does it help identify?** Customers with past-due invoices.
4. **What do default selections include?** All customers.
5. **Which actions review and produce it?** Preview optionally, then Print.
