# Invoice and Credit Memo Module

This Customer-to-Cash article paraphrases only the official Infor SyteLine Customer Service User Guide, release 9.01.x. Printed guide pages are listed for every topic. It explains documented forms, not live invoice status, tax calculation, site settings, or permissions. Standard order invoices and consolidated invoices have different processing routes.

## Document Metadata

- **Module:** invoice
- **Tags:** prospect-to-cash, customer-to-cash, invoice, credit-memo, consolidated-invoice
- **Document Owner:** Customer Service and Accounts Receivable
- **Reviewed / Approved By:** User-authorized knowledge activation; SyteLine SME review pending
- **Last Reviewed:** 2026-10-08
- **Version:** Infor SyteLine Customer Service User Guide 9.01.x
- **Source:** Infor SyteLine Customer Service User Guide 9.01.x, printed pages 27-32, 44-47, and 85-94

## Invoice process boundary

Shipment creates billable quantity, while Order Invoicing/Credit Memo creates a standard invoice and A/R transaction. A line on Invoice Hold is excluded. Delivery-order and consolidated-invoice items follow a separate billing route.

**Section Summary:** Shipment, invoicing, and payment are separate checkpoints.
**Guide pages:** 44-46, 85-87
### Keywords
shipment, standard invoice, A/R, consolidated billing

1. **Does shipping automatically create a standard order invoice?** No. The order invoicing process must run.
2. **What supplies quantity to a standard invoice?** A shipped line or release that is not fully invoiced.
3. **Which process creates the standard customer-order invoice?** Order Invoicing/Credit Memo.
4. **Does an invoice prove the customer has paid?** No. Payment application is a separate A/R step.
5. **When should a different billing route be checked?** Check consolidated and delivery-order settings before using standard invoicing.

## Order Invoicing/Credit Memo screen

Open Order Invoicing/Credit Memo, select Invoice in the Invoices or Credit Memos field, specify the remaining form values, and Process. One run processes invoices or credit memos, not both.

**Section Summary:** Mode and selection criteria determine what the run processes.
**Guide pages:** 44-45
### Keywords
Order Invoicing/Credit Memo, Invoice mode, Process

1. **Which form invoices customer-order items?** Order Invoicing/Credit Memo.
2. **Which field selects standard invoicing?** Choose Invoice in Invoices or Credit Memos.
3. **What is done after selecting Invoice?** Specify the appropriate remaining values and click Process.
4. **Can a single run create invoices and credit memos together?** No; select one type per run.
5. **Why review the run criteria before processing?** The selected mode and scope control which eligible orders are searched.

## Shipped and uninvoiced eligibility

The standard process searches selected orders for line/release quantities shipped but not fully invoiced. The line must not be on Invoice Hold. Compare the line's shipment and invoice state if it is unexpectedly omitted.

**Section Summary:** Eligible quantity is shipped, not yet fully invoiced, and not held.
**Guide pages:** 44-46
### Keywords
shipped quantity, uninvoiced quantity, Invoice Hold

1. **What line quantity does standard invoicing seek?** Quantity shipped but not fully invoiced.
2. **Can an unshipped line print through this standard procedure?** No; prior shipment is required.
3. **Which field can block an otherwise shipped line?** Invoice Hold.
4. **What should be compared if only part of an order was billed?** Shipped, invoiced, and held quantities by line/release.
5. **Why does a second run skip an already billed shipment?** That shipped quantity is no longer uninvoiced.

## Standard invoicing effects

The completed process computes invoice amounts, updates customer sales and invoicing fields, calculates commission due, posts invoice history, creates A/R invoice transactions, and prints the invoice.

**Section Summary:** Completed standard billing updates commercial, history, and A/R records.
**Guide pages:** 45
### Keywords
invoice amount, invoice history, commission, A/R transaction

1. **What amount is computed during order invoicing?** Invoice amounts for eligible selected quantities.
2. **Which customer data is updated?** Customer sales and invoicing fields.
3. **Is commission considered?** Yes, the process calculates a commission due amount.
4. **Where is a completed invoice recorded?** Invoice history and A/R invoice transactions.
5. **What document does the process print?** The invoice.

## Posting or printing error

If posting or printing fails, the process stops and the invoice in error is not generated. Earlier invoices in the same run remain posted. Inspect history before retrying.

**Section Summary:** One failed invoice does not undo earlier successful invoices.
**Guide pages:** 45-46
### Keywords
invoice error, partial batch, retry, Background Task History

1. **What happens to the invoice at the error?** It is not generated.
2. **Does the process continue past the failing invoice?** No; processing stops.
3. **Are prior posted invoices rolled back?** No; they remain posted.
4. **What must be checked before retrying the range?** Invoice history and the precise failure point.
5. **Where can submitted background-task results be checked?** Background Task History.

## Credit Memo mode

Credit Memo mode generates credit memos for orders entered through Customer Orders, including credits and returned items. It is processed separately from Invoice mode.

**Section Summary:** Customer-order credits use a separate credit-memo run.
**Guide pages:** 45
### Keywords
credit memo, Customer Orders, return

1. **Which mode creates a customer-order credit memo?** Credit Memo on Order Invoicing/Credit Memo.
2. **Can this mode be mixed with Invoice in one run?** No.
3. **What can the memo represent?** A customer credit or a return of items.
4. **How does the guide compare its processing with invoicing?** It is very similar, but selected separately.
5. **Which orders are named for this option?** Orders entered through Customer Orders.

## Apply To Invoice reference

If an Apply To Invoice number was entered on the customer order, a line referencing that invoice prints on the first credit-memo page. Actual application and balance must still be inspected in live A/R.

**Section Summary:** Apply To Invoice adds a visible reference, not a live balance assertion.
**Guide pages:** 45
### Keywords
Apply To Invoice, original invoice, credit memo

1. **When does a credit memo print the original invoice reference?** When the order has an Apply To Invoice number.
2. **Where is that reference printed?** On the first page of the credit memo.
3. **What does the line connect?** The credit memo and the named invoice.
4. **Does the printed line prove the open balance is zero?** No; inspect posted A/R applications.
5. **What should be checked if the reference is absent?** Check Apply To Invoice on the source customer order.

## Returned-item credit sequence

For a credit with returned items, first post returned quantity with a material transaction through a ship transaction. That adjusts inventory. The credit memo is still required to adjust domestic-currency sales and the customer balance.

**Section Summary:** Inventory return and financial credit are distinct effects.
**Guide pages:** 45
### Keywords
returned quantity, ship transaction, inventory, customer balance

1. **What occurs before crediting returned items?** Post the returned quantity through a material/ship transaction.
2. **What does that transaction adjust?** Inventory quantity fields.
3. **Does it alone adjust the customer balance?** No.
4. **What adjusts domestic-currency sales and customer balance?** Printing the credit memo.
5. **Why distinguish a return from a price-only credit?** A physical return also requires inventory quantity processing.

## Manual invoice boundary

Invoices unrelated to a sale or return of inventory items use Invoices, Debit and Credit Memos, not the standard order run. The guide notes that manual invoices are unsupported when Print Draft is selected on Customers.

**Section Summary:** Non-order/manual A/R invoices have a different form and limitation.
**Guide pages:** 44-45
### Keywords
manual invoice, Invoices Debit and Credit Memos, Print Draft

1. **Which form handles invoices unrelated to inventory sales or returns?** Invoices, Debit and Credit Memos.
2. **Should every A/R invoice use Order Invoicing/Credit Memo?** No.
3. **Which customer setting blocks manual invoices?** Print Draft selected on Customers.
4. **What should be classified before choosing the form?** Whether the charge is an order-shipment invoice or a separate A/R invoice.
5. **Does a manual invoice substitute for a missing shipment?** No; it is a different transaction path.

## Regular and blanket header amounts

For regular and blanket invoices, prepaid amount, miscellaneous charges, sales tax, and freight from the order header are zeroed out. This documented behavior is specific to that route.

**Section Summary:** The regular/blanket run clears named order-header amounts.
**Guide pages:** 45
### Keywords
prepaid, miscellaneous charges, sales tax, freight

1. **What happens to the order-header prepaid amount?** It is zeroed for regular and blanket invoices.
2. **What happens to order-header miscellaneous charges?** They are zeroed in the described run.
3. **What happens to order-header sales tax?** It is zeroed in the described run.
4. **What happens to order-header freight?** It is zeroed in the described run.
5. **Should this be assumed for every invoice route?** No; confirm the applicable route and its rules.

## Advanced Terms

When Advanced Terms is used, the Advanced Term Algorithm calculates the due-date bucket for customer orders. A named invoice's actual due schedule requires current terms and invoice data.

**Section Summary:** Advanced Terms may govern due-bucket calculation.
**Guide pages:** 45
### Keywords
Advanced Terms, due-date bucket, billing terms

1. **What calculates the bucket under Advanced Terms?** The Advanced Term Algorithm.
2. **Is Advanced Terms necessarily active everywhere?** No; the guide states this conditionally.
3. **Can static knowledge determine a specific invoice due date?** No.
4. **What should be checked for an unexpected bucket?** Terms and installed Advanced Terms configuration.
5. **Does selecting the invoice run itself define the bucket?** No; the applicable terms algorithm does.

## Multiple due-date terms

A billing terms code can create several due dates for one invoice. SyteLine makes associated due records; dates, percentages, and amounts due appear on the invoice.

**Section Summary:** Some terms divide an invoice into several due amounts.
**Guide pages:** 45
### Keywords
multiple due dates, percentage due, amount due

1. **What causes multiple invoice due dates?** A terms code configured for multiple due dates.
2. **What associated records are created?** Payment due-date records.
3. **What due information prints?** Due dates, percentages, and amounts.
4. **Why can one invoice have several scheduled payments?** Its terms split the obligation.
5. **What should be checked before calling it overdue?** The individual due records and outstanding amounts.

## Foreign-language printing

Multi-Lingual Order Invoice is the guide's form for printing order invoices or credit memos in a foreign language. Language choice is separate from transaction currency.

**Section Summary:** Multilingual print presentation uses a dedicated form.
**Guide pages:** 45
### Keywords
Multi-Lingual Order Invoice, language, print

1. **Which form is named for foreign-language order invoices?** Multi-Lingual Order Invoice.
2. **Can it print credit memos too?** Yes.
3. **Is invoice language the same decision as debt currency?** No.
4. **What should be checked for an unexpected print language?** The multilingual form fields and selected output settings.
5. **Does language selection itself prove a different A/R amount?** No; check the posted transaction.

## Foreign-currency debt

A foreign-currency customer owes the foreign-currency amount even if the document is printed in domestic currency. Exchange-rate changes may create gains/losses, and over/underpayments may leave balances needing separate adjustment.

**Section Summary:** Printed currency need not be the currency owed.
**Guide pages:** 45
### Keywords
foreign currency, domestic print, exchange gain loss

1. **Which currency does a foreign-currency customer owe?** The foreign-currency amount.
2. **Can the document print in domestic currency for customs purposes?** Yes, without changing the debt currency.
3. **What can rate changes create?** Exchange gains or losses.
4. **What can over/underpayment leave?** A debit or credit customer-account balance.
5. **How is a rate-related balancing difference handled?** The guide requires a separate posted adjustment.

## Invoice Hold field

Invoice Hold on Customer Order Lines and Customer Order Blanket Releases prevents automatic invoicing. Once removed, shipped quantity becomes available at the next invoicing run.

**Section Summary:** Invoice Hold delays billing without undoing shipment.
**Guide pages:** 46
### Keywords
Invoice Hold, Customer Order Lines, Blanket Releases

1. **Which forms expose Invoice Hold?** Customer Order Lines and Customer Order Blanket Releases.
2. **What does the hold prevent?** Automatic invoicing of that line/release.
3. **Does a held item necessarily lack a shipment?** No.
4. **What happens after hold removal?** Shipped quantity can be invoiced on the next run.
5. **What example does the guide give for a hold?** An FOB customer waits until shipment receipt before billing.

## Packing-slip invoice option

To create invoices from packing slips, select Print Packing Slip on Invoice on Customers Codes and Create from Packing Slip on the invoice form. Both conditions matter.

**Section Summary:** Packing-slip invoicing requires customer and run settings.
**Guide pages:** 46
### Keywords
packing slip, Print Packing Slip on Invoice, Create from Packing Slip

1. **Which Customers option is needed?** Print Packing Slip on Invoice on Codes.
2. **Which invoice-form option is needed?** Create from Packing Slip.
3. **Is a packing slip alone sufficient?** No.
4. **Where is the customer option?** On the Codes tab of Customers.
5. **What should be checked when this route fails?** Both the customer option and invoice-form selection.

## Reprint Options

Reprint Options retrieves invoice history by invoice number, date, customer, or order range. The reprint uses current display options rather than the original print options. Preprinted-number forms cannot simply be reprinted; the guide directs voiding and regenerating in that case.

**Section Summary:** A reprint is history-based and subject to current print settings.
**Guide pages:** 46
### Keywords
Reprint Options, invoice history, preprinted forms

1. **Which ranges can Reprint Options use?** Invoice numbers, invoice dates, customers, or orders.
2. **Does reprinting reuse original display options?** No; it uses currently specified options.
3. **What setting affects whether reprinting is allowed?** Use Preprinted Forms on Accounts Receivable Parameters.
4. **Why are preprinted-number forms not simply reprinted?** A new preprinted number would not match the original invoice number.
5. **What does the guide direct for that preprinted-number case?** Void and regenerate the invoice.

## Reprint data sources

Core invoice amounts and line facts come from invoice history. Some descriptive information comes from the customer order, which must still exist in the database. A missing order may therefore affect secondary reprint details.

**Section Summary:** Reprints combine retained invoice history with still-available order context.
**Guide pages:** 46
### Keywords
invoice history, order text, reprint detail

1. **Where does reprint line-item number come from?** Invoice history.
2. **Where do reprint shipped quantity and price come from?** Invoice history.
3. **Where do reprint freight and sales tax come from?** Invoice history.
4. **Where does reprint order or line text come from?** The customer order still in the database.
5. **Why might a reprint lack secondary order details?** The customer order supplying them may no longer be available.

## Background Task History

Only one invoicing background task instance runs at a time; requests are queued synchronously. When two users invoice the same order, the first processed request succeeds and the second does not create another invoice. Report submitted means a task was submitted, not that an invoice was created.

**Section Summary:** Verify actual invoice output in Background Task History.
**Guide pages:** 46-47
### Keywords
Background Task History, Report submitted, concurrent invoicing

1. **How many invoicing background task instances can run at once?** One.
2. **Where do simultaneous invoice requests go?** The background queue.
3. **What happens to the second request for the same order?** It creates no second invoice after the first succeeds.
4. **Does Report submitted prove invoice creation?** No.
5. **Where can the created invoice range be verified?** Background Task History.

## Progressive billing invoice selection

The guide describes a progressive bill with Invoice Flag Yes printing in the next regular invoice run. For Invoice Flag Automatic, it gives an individual print path: select Invoice, choose Progressive Bill in Invoice Type, optionally print progressive notes, then Process.

**Section Summary:** Progressive bills have a documented invoice-type selection.
**Guide pages:** 47
### Keywords
progressive bill, Invoice Flag, Invoice Type

1. **When does a progressive bill flagged Yes print?** In the next regular invoice run.
2. **What mode is chosen for an individually printed Automatic progressive bill?** Invoice.
3. **Which Invoice Type is selected?** Progressive Bill.
4. **What optional text can be included?** Progressive billing notes.
5. **What final action starts that individual print run?** Process.

## Shipment approval and invoice gate

For a customer configured to require shipment approval, approved shipped value is tracked separately. The guide says an approved quantity may be adjusted while invoiced quantity is lower than shipped quantity; further changes are blocked when invoiced catches up. Required in-process accounts must be configured or approval is prevented.

**Section Summary:** Shipment approval can be a prerequisite to the invoice path.
**Guide pages:** 28-32
### Keywords
Shipment Approval Required, Quantity Approved, invoiced quantity

1. **Where is shipment approval required for a customer selected?** On Customers.
2. **What may prevent approval when it is required?** Missing required in-process accounts.
3. **When can approved quantity still be adjusted?** While invoiced quantity is less than shipped quantity.
4. **When are further approved-quantity changes barred?** Once invoiced quantity matches shipped quantity.
5. **Where are changes to approved quantity logged?** Order Shipment Approval Log.

## Consolidated invoice overview

A consolidated invoice combines multiple shipped orders for one customer over a period, for example weekly. Delivery-order items must use this system. The setup can be made at customer, order, or line/release level; the default can be overridden lower down.

**Section Summary:** Consolidated invoicing groups shipped items through a separate route.
**Guide pages:** 85-87
### Keywords
consolidated invoice, delivery order, weekly billing

1. **What does a consolidated invoice combine?** Multiple orders shipped to a customer over a period.
2. **Can items from several customer purchase orders appear together?** Yes.
3. **How must delivery-order items be invoiced?** Through consolidated invoicing.
4. **At which levels can consolidated invoicing be specified?** Customer, customer order, and line/release.
5. **Does a shipment necessarily produce its own invoice immediately?** No; the configured consolidation period and process matter.

## Consolidated-route restrictions

The 9.01.x guide excludes EDI orders, progressive billing invoices, project invoices, and RMAs from consolidated invoicing. It also excludes a customer order with a fixed exchange rate, and invoiced items must ship from the same site. These are guide-specific restrictions to verify in the deployed release.

**Section Summary:** Some order types, currency settings, and site combinations cannot consolidate.
**Guide pages:** 85-86
### Keywords
consolidated restrictions, EDI, fixed exchange rate, same site

1. **Can EDI orders use the guide's consolidated route?** No.
2. **Can progressive billing invoices be processed by Consolidated Invoicing?** No.
3. **Can RMAs be processed by Consolidated Invoicing?** No.
4. **Can a fixed-exchange-rate order be consolidated?** No, according to the guide.
5. **What site condition applies to the invoiced items?** They must have shipped from the same site.

## Customer consolidated defaults

On Customers, select Consolidated Invoice, optionally Summarize, set Invoice Freq, and choose DO Invoice type when delivery orders are planned. New orders and lines inherit the customer designation but can be overridden at lower levels.

**Section Summary:** Customer settings establish defaults for later consolidated invoices.
**Guide pages:** 87-88
### Keywords
Customers, Consolidated Invoice, Summarize, Invoice Freq, DO Invoice

1. **Which Customers option enables the default?** Consolidated Invoice.
2. **When is Summarize enabled on Customers?** Only when Consolidated Invoice is selected.
3. **Which field selects billing cadence?** Invoice Freq.
4. **Which setting addresses delivery-order invoice type?** DO Invoice.
5. **Can an inherited customer setting be overridden?** Yes, at order or line/release level.

## Customer Orders consolidated settings

On Customer Orders General, select Consolidated Invoice, optionally Summarize Lines, and set Invoice Freq. The option is enabled only for Planned or Ordered non-EDI orders whose excise-exchange setting matches the customer.

**Section Summary:** The order header can override the customer's consolidation default.
**Guide pages:** 87-88
### Keywords
Customer Orders General, Summarize Lines, Excs Exch

1. **Where is Consolidated Invoice selected on an order?** Customer Orders, General tab.
2. **Which order statuses allow the option?** Planned or Ordered.
3. **Does an EDI order meet this option's condition?** No.
4. **What excise-exchange condition must match?** Order Excs Exch and customer Excs Exch.
5. **Which order-level field groups similar items?** Summarize Lines.

## Line and blanket-release consolidation

Use Customer Order Lines or Customer Order Blanket Releases, Amounts tab, to set Consolidated Invoice, Summarize Lines, and Invoice Freq. The option requires Planned/Ordered status, non-EDI order, and matching excise exchange; summarization also requires limited notes and a nonconfigurable item.

**Section Summary:** Line/release settings determine which shipped items enter consolidation.
**Guide pages:** 88
### Keywords
Customer Order Lines, Blanket Releases, Amounts, Summarize Lines

1. **Where is line-level Consolidated Invoice selected?** Amounts tab on Customer Order Lines.
2. **Which form handles a blanket release?** Customer Order Blanket Releases.
3. **What status condition enables the line/release option?** Planned or Ordered.
4. **When is Summarize Lines enabled?** With Consolidated Invoice selected, no more than one notes line, and a nonconfigurable item.
5. **Which field sets line/release frequency?** Invoice Freq.

## Consolidated Invoice Generation

Consolidated Invoice Generation builds pending invoice records from selected shipped orders or delivery orders. Its criteria include invoice frequency, order and delivery-order processing, and shipping date. Pending records are not the same as printed and posted invoices.

**Section Summary:** Generation prepares pending records for review and later posting.
**Guide pages:** 87-89
### Keywords
Consolidated Invoice Generation, frequency, ship date, pending

1. **Which activity generates pending consolidated records?** Consolidated Invoice Generation.
2. **Can generation filter by invoicing frequency?** Yes.
3. **Can it separately select customer and delivery orders?** Yes, with processing criteria.
4. **Can shipping date be part of generation criteria?** Yes.
5. **Does generating a pending record equal final posting?** No; review and Consolidated Invoicing follow.

## Consolidated Invoices Workbench

The Workbench reviews and changes pending invoice records before printing. Its Lines tab can add eligible shipped, not-yet-included order lines. Single By PO delivery-order additions create a new header, while other allowed additions join the current invoice; Single delivery-order invoices do not allow manual line addition.

**Section Summary:** Workbench manages the pending invoice composition.
**Guide pages:** 89-90
### Keywords
Consolidated Invoices Workbench, Add Consolidated Line, Single By PO

1. **What is reviewed in Consolidated Invoices Workbench?** Pending consolidated invoice records.
2. **Which tab begins adding a line?** Lines, then Add.
3. **What lines appear on Add Consolidated Line?** Shipped, marked-for-consolidation lines not yet included in a pending record.
4. **What happens when adding a Single By PO delivery-order line?** A new invoice header is created.
5. **Can a Single delivery-order invoice have lines added here?** No; the add function is unavailable.

## Invalid pending consolidated records

Changes after generation can mark pending records modified. Consolidated Invoicing reports these as invalid until regenerated. The guide lists order/customer/ship-to/price/discount/quantity and related delivery-order changes as examples. Do not force-post a stale pending record.

**Section Summary:** Regenerate stale consolidated records before print/post.
**Guide pages:** 90-92
### Keywords
invalid consolidated invoice, modified record, regenerate

1. **What can make a pending consolidated record invalid?** Relevant source changes after it was generated.
2. **How does the guide describe affected records?** They are marked modified.
3. **What does Consolidated Invoicing report for them?** Invalid.
4. **Which group activity can update them?** Consolidated Invoice Generation.
5. **Which Workbench action can fix an individual line?** Regenerate the line marked Regen.

## Consolidated tax and charge review

The Workbench shows tax codes for freight and miscellaneous charges on unprinted invoices, and calculated sales tax can be previewed. The source warns that changed order charges require regeneration and that tax defaults differ between area-based and item-based systems. Confirm local tax configuration rather than inventing a universal code.

**Section Summary:** Review pending freight, miscellaneous, and tax values before posting.
**Guide pages:** 86, 92-93
### Keywords
freight tax, miscellaneous tax, Tax Systems, tax preview

1. **Where are pending freight and miscellaneous tax codes visible?** Consolidated Invoices Workbench.
2. **Can calculated sales tax be previewed there?** Yes.
3. **What if order charges change after generation?** Regenerate the pending invoice.
4. **Are area-based and item-based tax defaults identical?** No; the guide describes different defaults.
5. **Should a chatbot assert a particular tax amount from this article?** No; inspect live tax configuration and the pending invoice.

## Updating pending consolidated invoices

Workbench edits individual pending invoices and selected header fields. Consolidated Invoice Generation can delete/regenerate groups selected by customer, frequency, order, delivery order, or ship date. Delete Records First By offers Range, All, or None; these choices have materially different effects and require authorized review.

**Section Summary:** Workbench edits individual pending records; Generation refreshes groups.
**Guide pages:** 93-94
### Keywords
pending invoice update, Delete Records First By, Range, All, None

1. **Which form edits individual pending consolidated invoices?** Consolidated Invoices Workbench.
2. **Which activity updates groups of pending invoices?** Consolidated Invoice Generation.
3. **What does Delete Records First By Range target?** A selected range, such as customer, order, frequency, delivery order, or ship date.
4. **What does All with both Process check boxes cleared do?** It deletes all pending records without adding new ones.
5. **What does None permit?** Generation of new records without first deleting existing records.
