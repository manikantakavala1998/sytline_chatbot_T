# Fulfillment and Shipment Module

This article covers the documented customer-order shipment paths in the original Infor SyteLine Customer Service User Guide, release 9.01.x. It describes standard Order Shipping, report/utility shipping, order-pick-list posting, and the separate pick-pack-ship workflow. Actual order state, stock, site configuration, approvals, and permissions require a live SyteLine check. The guide's shipment-reversal passages conflict; that boundary is identified rather than resolved by assumption.

## Document Metadata
- **Document Title:** Fulfillment and Shipment Module
- **Module:** shipment
- **Tags:** order shipping, available to ship, pick list, packing, shipment confirmation, reservations, shipment approval, DIFOT
- **Document Owner:** Customer-to-Cash knowledge team
- **Reviewed / Approved By:** Pending local SyteLine SME review
- **Last Reviewed:** 2026-10-08
- **Version:** 0.2 draft
- **Source:** Infor SyteLine Customer Service User Guide 9.01.x, printed pages 27-31, 33, 53-61, 69-71, and 132-142

## Shipment workflow map
**Guide pages:** 33, 55-59, 132-140.

1. **Which shipment routes does the guide describe?** It describes standard Order Shipping, Available to Ship Report followed by Shipping Processing Orders, order-pick-list posting, and a separate Pick Workbench through Ship Confirmation flow.
2. **Where is a single order shipped manually?** The standard manual path starts on the Order Shipping form.
3. **Which forms start the pick-pack-ship route?** Pick Workbench starts picking; Pack Workbench or Pack Confirmation handles optional packing; Shipment Master and Ship Confirmation handle shipment.
4. **Are standard Order Shipping and pick-pack-ship intended as one combined process?** No. The guide recommends choosing one route; they exchange some quantity awareness but were not designed to be used together.
5. **Does creating an order itself record shipment?** No. The guide places order entry, shipping, and invoicing at separate steps.

**Section Summary:** Identify the site's route before interpreting forms, quantities, or shipment status.
### Keywords
shipment routes, Order Shipping, Shipping Processing Orders, Pick Workbench, Ship Confirmation

## Standard Order Shipping selection
**Guide pages:** 55.

1. **How does manual shipping begin?** Open Order Shipping, then select the customer order to ship.
2. **What does Select All do on Order Shipping?** It selects the order lines shown on the form for the whole-order shipping choice.
3. **How can only one line be selected?** Select the line's Select check box instead of choosing the entire order.
4. **Can a user choose between whole-order and one-line shipping on this form?** Yes. The manual procedure presents both options after the order is selected.
5. **What should be confirmed before selecting a line to ship?** Confirm the intended order, line, quantity, location or lot, and warehouse in the live form.

**Section Summary:** Order Shipping selection can target the displayed order or an individual line.
### Keywords
Order Shipping, Select All, Select line, manual shipment

## Credit-hold shipping block
**Guide pages:** 55, 59, 96.

1. **Which credit-hold fields can stop Order Shipping?** A selected Credit Hold field on Customers or Customer Orders prevents the documented shipment.
2. **Can a customer hold block an order whose own hold box is clear?** Yes. The customer-level hold independently prevents shipment.
3. **Does the order pick-list posting path ignore credit holds?** No. The guide repeats the customer or order Credit Hold block for that path.
4. **What extra credit check is mentioned for multi-site manual shipping?** The system checks whether the customer's credit limit is exceeded.
5. **What should be inspected after a credit-related shipping failure?** Check both hold levels, the current site and customer credit state, without treating a warning as permission to bypass the block.

**Section Summary:** Shipment routes must respect both customer and order credit holds.
### Keywords
shipping blocked, customer Credit Hold, order Credit Hold, multi-site credit

## Order Shipping editable fields
**Guide pages:** 55.

1. **Which shipping details may be changed on Order Shipping?** The guide lists CR Return, Location, Lot, Quantity, and U/M.
2. **Can the Location be reviewed before shipment?** Yes. Location is among the details the form permits the operator to change.
3. **Can the Lot be changed in the manual shipping flow?** Yes. Lot is one of the listed Order Shipping details.
4. **Where is the actual Quantity entered or revised for manual shipping?** On the Order Shipping form before shipping the selected order or line.
5. **Should a chatbot infer a specific lot or quantity from this article?** No. Those are transaction values that require live authorized SyteLine data.

**Section Summary:** Review transactional fields on Order Shipping before posting.
### Keywords
CR Return, Location, Lot, Quantity, U/M, Order Shipping

## Order Shipping status and flags
**Guide pages:** 55.

1. **What Ship Status change follows a successful manual shipment?** The guide says Ship Status changes from Ordered to Filled.
2. **Does the Ship Partial check box on Order Shipping itself prevent a partial shipment?** No. In the manual-shipping procedure it is informational and does not restrict shipment.
3. **Does the Ship Early check box itself block an early shipment?** No. The guide calls it informational in this procedure.
4. **Can the same Ship Partial field affect a different screen?** Yes. Available to Ship Report uses the order setting to decide which orders appear, even though the manual-shipping note says the flag is informational for that form.
5. **Is a Filled Ship Status proof of an invoice?** No. Shipping and invoicing are separate steps in the guide.

**Section Summary:** Form context matters: flags and shipment status do not replace invoice verification.
### Keywords
Ship Status, Ordered, Filled, Ship Partial, Ship Early

## Warehouse and inventory exceptions
**Guide pages:** 55-56.

1. **Can Order Shipping process more than one warehouse at once?** No. The guide states shipping is performed for one warehouse at a time.
2. **What happens when a selected line belongs to another warehouse?** The form displays an error that it cannot be shipped from the current warehouse.
3. **Why might one order line appear as several shipping lines?** Stock in different locations or lots can supply the same order line when the primary location is insufficient.
4. **When can On Hand Negative be selected?** The check box is enabled when the On Hand Neg Flag is selected on Inventory Parameters.
5. **What should be checked after a warehouse mismatch message?** Compare the selected shipping warehouse with the line's allocated warehouse and inspect the relevant location or lot choices.

**Section Summary:** Warehouse scope and stock locations can change what is selectable for shipment.
### Keywords
warehouse mismatch, multiple locations, negative on hand, Inventory Parameters

## Available to Ship Report
**Guide pages:** 56.

1. **What is the report's role in the documented standard batch route?** Available to Ship Report narrows and displays candidate orders before Shipping Processing Orders is run.
2. **Are all writable report filters required?** No. The guide says they are optional but useful for narrowing the scope.
3. **When does an order with Ship Partial cleared appear?** The report displays it only when all its line items are ready to ship.
4. **When does an order with Ship Partial selected appear?** The report displays it when at least one line item is ready to ship.
5. **Does this report's Ship Partial logic authorize a partial quantity of one line?** No. The guide explicitly separates order visibility from partial quantities on a line.

**Section Summary:** Report filtering and Ship Partial affect candidate order visibility, not line-quantity permission.
### Keywords
Available to Ship Report, Ship Partial, report filters, ready lines

## Shipping Processing Orders
**Guide pages:** 56.

1. **Which utility follows the Available to Ship Report in the documented route?** Shipping Processing Orders.
2. **Is generating Available to Ship Report itself the shipping transaction?** No. The next documented step runs Shipping Processing Orders for the desired order.
3. **Why should report scope be reviewed before utility processing?** The filters determine the set examined, and the utility should be run for the intended order only.
4. **Does this utility belong to the separate pick-pack-ship shipment path?** No. The guide presents it with standard customer-order shipping, and the pick-pack-ship overview excludes shipping processing orders from that workflow.
5. **What live evidence confirms that this route completed?** Verify the utility's result and current shipped quantity or status in SyteLine; the article cannot provide the transaction outcome.

**Section Summary:** Reporting candidates and processing their shipment are distinct steps.
### Keywords
Shipping Processing Orders, standard shipping, order filter

## Generate Order Pick List posting
**Guide pages:** 59.

1. **Which form can create shipping transactions while generating a pick list?** Generate Order Pick List when Post Material Issues is selected before Process.
2. **What does Post Material Issues change?** It causes the selected pick-list orders to receive shipping transactions automatically, subject to the guide's constraints.
3. **Which selection examples determine orders included?** The guide names order-number and due-date ranges as examples.
4. **Must eligible line or release stock be positive?** Yes. The guide requires quantity on hand greater than zero for this posting route.
5. **Can customer or order Credit Hold block pick-list posting?** Yes. The same documented hold restriction applies.

**Section Summary:** Generating a pick list can post shipment only when Post Material Issues and eligibility permit it.
### Keywords
Generate Order Pick List, Post Material Issues, due-date range, on hand

## Lot and serial pick-list boundary
**Guide pages:** 59.

1. **Can Generate Order Pick List post lot-tracked items with Post Material Issues selected?** No. The guide directs these items to Order Shipping for the shipping transaction.
2. **Can that form post serial-tracked items when Post Material Issues is selected?** No. Serial-tracked items have the same restriction.
3. **Can a pick list still be generated for tracked items without posting issues?** Yes. Set Post Material Issues to No to generate the list without that shipment transaction.
4. **Which form does the guide name for shipping lot- or serial-tracked items in this route?** Order Shipping.
5. **Why should a printed pick list not be taken as proof of shipment?** The list can be generated with Post Material Issues off, and tracked items are not shipped by the automatic-post option.

**Section Summary:** Tracked items can be listed without being shipped by pick-list posting.
### Keywords
lot tracked, serial tracked, Post Material Issues, Order Shipping

## Reservation prerequisites
**Guide pages:** 69-70.

1. **Which item control is required before inventory is reserved for an order?** Reservable must be selected on the Items form's Controls tab.
2. **Which order-line status is required for reservation?** Ordered.
3. **Where can a reservation be verified by order?** Reservations for Order shows reservation records associated with order lines.
4. **Where can a reservation be verified by item?** Reservations for Item shows the order and line against the selected item.
5. **Which report can check reserved stock by order or item?** Reserved Inventory by Order Report.

**Section Summary:** Reservation requires a reservable item and Ordered line and has separate verification screens.
### Keywords
Reservable, Ordered, Reservations for Order, Reservations for Item

## Reserved inventory during shipment
**Guide pages:** 69-71.

1. **Which stock is used first when an order has reserved inventory?** The reserved quantity is used before non-reserved inventory.
2. **What happens to a reserved serial number in the shipping grid?** It defaults into the Serial Numbers grid for the reserved item.
3. **Can other in-inventory serial numbers be added to fulfill shipment?** Yes. Generate can add serial numbers with In Inventory status for selection with reserved serials.
4. **What happens to reservation balances as reserved stock ships?** The guide lists reductions to reserved inventory and associated order, location, warehouse, and applicable lot reservation quantities.
5. **Does deleting or reducing a reservation automatically update a pick-pack shipment?** No. The guide says to update the shipment through Unpack Inventory before changing that reservation.

**Section Summary:** Reserved stock has priority; reservation and shipment quantities must remain aligned.
### Keywords
reserved inventory, serial numbers, Unpack Inventory, reservation balance

## Multi-Site Item Sourcing
**Guide pages:** 53-54.

1. **Which form helps compare fulfillment site and warehouse choices?** Multi-Site Item Sourcing, opened from a Customer Order Lines line with Multi-Site Source.
2. **Which line statuses allow the documented sourcing action?** Ordered or Planned.
3. **What information is passed from the order line?** The item, ship-to address, and ordered quantity.
4. **What factors does the guide suggest comparing?** Driving distance, warehouse available quantity, and, where APS is enabled, projected production time.
5. **How is the selected source returned to the order line?** Choose a site/warehouse row and click Select.

**Section Summary:** Source selection is a comparison tool and depends on enabled integrations and current stock.
### Keywords
Multi-Site Item Sourcing, site, warehouse, available quantity, APS

## Standard versus pick-pack-ship
**Guide pages:** 55, 136-138.

1. **Does the guide recommend mixing Order Shipping with pick-pack-ship for the same process?** No. It recommends choosing one route because the two were not designed to run together.
2. **Is packing mandatory in pick-pack-ship?** No. The guide allows picking followed directly by shipping.
3. **Can standard Order Shipping see quantities already in pick-pack-ship?** Yes. The guide says the routes have some quantity awareness of one another.
4. **Does that quantity awareness make the workflows interchangeable?** No. Their forms and invoicing paths still differ.
5. **What should be confirmed before giving a user step-by-step shipping instructions?** Identify which fulfillment route the site uses for the order.

**Section Summary:** Similar quantities do not make the two fulfillment routes one workflow.
### Keywords
standard shipping, pick pack ship, workflow separation

## Pick Workbench
**Guide pages:** 132-133.

1. **Which orders can Pick Workbench use to create pick lists?** The guide specifies customer orders with Ordered status.
2. **Where is a picker assigned?** On Pick Workbench while creating the pick list.
3. **Must selected lines have the same due date?** No. The guide permits different due dates on one selected pick list.
4. **Where can Qty To Pick be changed before generation?** In the optional Inventory tab's lower-left grid for the selected line.
5. **Which action generates the selected pick list?** Click Generate after reviewing the picker, lines, grouping, and optional inventory choices.

**Section Summary:** Pick Workbench forms lists from selected Ordered order lines and assigns the picker.
### Keywords
Pick Workbench, picker, Qty To Pick, Generate

## Pick Confirmation and maintenance
**Guide pages:** 132-133.

1. **Where is the quantity actually picked recorded?** Pick Confirmation, in Qty Picked for the selected pick list.
2. **What is the confirmation action?** Verify or change Qty Picked, click Complete, then confirm the message.
3. **What status does a new pick list initially have?** Open in Pick Maintenance.
4. **When does confirming a full pick make the list Picked?** When all ordered quantity on all lines is confirmed.
5. **What extra step is needed when any pick-list quantity is partial?** Change the pick list status to Picked manually on Pick Maintenance, per the guide.

**Section Summary:** Picked quantity and Picked status need deliberate confirmation, especially for partial picks.
### Keywords
Pick Confirmation, Qty Picked, Pick Maintenance, partial pick

## Pick-list grouping and splitting
**Guide pages:** 133, 140.

1. **How do selected lines go onto the same pick list in Pick Workbench?** Give the selected lines the same group number.
2. **Can orders with different currencies be grouped this way?** No. The guide excludes different-currency orders from the same grouping.
3. **What extra rule applies to grouped credit-card orders?** They can group only with credit-card orders for the same customer and Ship To.
4. **What does Generate Bulk Pick List allow?** It combines pick lists from different groups for one warehouse picking trip.
5. **Where is an existing pick list split?** Select it and the items to move on Pick List Splitting, then Process to create the new list.

**Section Summary:** Grouping and splitting are controlled pick-list operations with currency and payment restrictions.
### Keywords
group number, bulk pick list, Pick List Splitting, credit card grouping

## Pack Workbench
**Guide pages:** 132, 135.

1. **Is Pack Workbench required for a shipment from one pick list?** No. The guide calls grouping pick lists with this form optional.
2. **What role is assigned on Pack Workbench?** A packer for the shipment.
3. **What records are selected there?** Pick lists to group into a shipment.
4. **What action creates the grouped shipment?** Click Generate after selecting the packer and pick lists.
5. **Which form normally follows Pack Workbench for packaging detail?** Pack Confirmation.

**Section Summary:** Pack Workbench optionally groups pick lists and assigns a packer before confirmation.
### Keywords
Pack Workbench, packer, pick lists, Generate

## Pack Confirmation and packages
**Guide pages:** 133-135, 137.

1. **Which form records how shipment items are packaged?** Pack Confirmation.
2. **Where is a package created?** Insert a new package in Pack Confirmation's package grid.
3. **Which package attributes does the guide list?** Weight, Rate Code, NMFC Code, Marks and Exceptions, Hazardous when needed, Package Type, and Package Description.
4. **Where does a saved package appear?** In the Package Tree.
5. **Can packing assign lot or serial numbers to a package?** Yes. The pick-pack-ship overview lists that as a packing capability.

**Section Summary:** Packages are explicit records with shipment and handling attributes.
### Keywords
Pack Confirmation, package grid, package tree, lot, serial

## Shipment Master and Ship Confirmation
**Guide pages:** 132, 140.

1. **Which form maintains a pick-pack shipment before posting?** Shipment Master.
2. **Which status begins the documented shipment procedure?** Open.
3. **What status is set when the shipment is ready?** Ready To Ship.
4. **How is Ship Confirmation opened?** From Shipment Master, click Ship Confirmation after preparing the shipment.
5. **What posts the selected shipment?** On Ship Confirmation, select the intended shipment or shipments and click Ship.

**Section Summary:** Shipment Master preparation precedes the irreversible-looking confirmation step.
### Keywords
Shipment Master, Open, Ready To Ship, Ship Confirmation

## Shipment merging and splitting
**Guide pages:** 132, 135-136, 141.

1. **Which form combines shipments?** Shipment Merging selects a base shipment and the shipments to add, then processes the merge.
2. **Can different-currency shipments be merged?** No. The guide disallows merging shipments with different currencies.
3. **What credit-card rule applies to shipment merging?** Credit-card shipments can merge only with credit-card shipments for the same customer and Ship To.
4. **Which form divides a shipment?** Shipment Splitting.
5. **What is selected on Shipment Splitting?** Select packages if they exist; otherwise select order lines or releases to move into the new shipment.

**Section Summary:** Merging and splitting alter shipment composition before final processing.
### Keywords
Shipment Merging, Shipment Splitting, packages, currency

## Shipment correction and reversal boundary
**Guide pages:** 140-142.

1. **What does the Shipment Master procedure say about undoing a shipped shipment?** Its note says a shipped shipment cannot be unshipped or returned and directs item returns to RMA or Order Shipping.
2. **Does the guide also describe an Unship Shipment form?** Yes. A later page gives that procedure, so the deployed release needs confirmation.
3. **Which fields does the Unship Shipment procedure require?** Shipment, selected lines, Quantity at most the shipped quantity, and Reason Code.
4. **What options are mentioned for unshipping?** Return-to-stock, status, cycle-count warning, and LCR warning choices.
5. **Can a chatbot promise a specific shipment can be unshipped?** No. Flag the guide conflict and check the deployed form and transaction state with an authorized user.

**Section Summary:** Do not collapse contradictory guide passages into an unconditional reversal rule.
### Keywords
Unship Shipment, RMA, Order Shipping, reversal, guide conflict

## Shipment Approval setup
**Guide pages:** 27-28, 31.

1. **Which customer setting starts the approval-required path?** Shipment Approval Required on Customers.
2. **Can an order override that customer default?** Yes. Customer Orders allows that field to be selected or cleared for a new order.
3. **Which process accounts does the guide associate with shipment approval?** It names inventory, cost-of-goods-sold, receivable, sales, discount, and tax in-process accounts across setup forms as applicable.
4. **What happens when required shipping in-process accounts are missing?** The guide says the line cannot be shipped when approval is required and the applicable COGS or Inventory In Process accounts are absent.
5. **Should an assistant turn on Shipment Approval Required from an explanation request?** No. It is a configured transaction control needing authorized setup and accounting review.

**Section Summary:** Approval-required shipping depends on customer/order choice and complete in-process accounting setup.
### Keywords
Shipment Approval Required, Customers, Customer Orders, in-process accounts

## Order Shipments approval
**Guide pages:** 28, 31.

1. **Where is customer approval of shipped quantity recorded?** On Order Shipments.
2. **Which two approval values are entered?** Quantity to approve and approval date.
3. **When is that approval step required?** For customer orders with Shipment Approval Required selected; otherwise the step is optional.
4. **What audit record is created for approval entries?** Order Shipment Approval Log records each quantity-approved entry.
5. **What bounds does the guide give for changing an approved quantity?** It may vary between the quantity already invoiced and the quantity shipped, until invoiced quantity equals shipped quantity.

**Section Summary:** Customer approval is recorded against shipments and becomes constrained by invoicing.
### Keywords
Order Shipments, approval quantity, approval date, approval log

## Approval and invoice gate
**Guide pages:** 29, 31, 138.

1. **What is invoice eligibility when Shipment Approval Required is selected?** Only shipment quantity approved beyond quantity already invoiced is eligible, and the invoice date must be on or after the approval date.
2. **What changes if approval is not required?** The guide includes uninvoiced order shipments in the standard invoicing path without that approval gate.
3. **Does shipping itself create an A/R invoice?** No. Order entry steps place invoicing after shipping.
4. **How are pick-pack-ship shipments invoiced in the guide?** Through Consolidated Invoice Generation, Consolidated Invoices Workbench, and Consolidated Invoicing, rather than Order Invoicing/Credit Memo.
5. **Why must the invoicing route be identified before answering a shipment billing question?** Standard order shipping and pick-pack-ship use different documented invoice paths.

**Section Summary:** Shipment, approval, and invoice are distinct events with route-specific invoice processing.
### Keywords
shipped not invoiced, shipment approval, consolidated invoicing

## DIFOT measurement
**Guide pages:** 59-60.

1. **What does DIFOT stand for?** Delivered In Full and On Time.
2. **Which two dimensions does the guide evaluate?** Delivered quantity against tolerance and shipping date against early or late tolerance.
3. **Does a DIFOT policy change how shipment is processed?** No. The guide says it evaluates performance rather than changing delivery or shipping steps.
4. **Where do line-level DIFOT indicators appear?** Customer Order Lines and Customer Order Blanket Releases show On Time, In Full, and overall indicators.
5. **When is the overall DIFOT evaluation successful?** When both the In Full and On Time checks pass under the applicable criteria.

**Section Summary:** DIFOT measures delivery performance after applying a policy; it is not a shipping authorization.
### Keywords
DIFOT, In Full, On Time, delivery performance

## DIFOT policy settings
**Guide pages:** 60-61.

1. **Where are system-default DIFOT criteria set?** Order Entry Parameters.
2. **At which levels may DIFOT defaults be overridden?** The guide names customer ship-to, customer order, line or blanket line, and blanket release levels.
3. **Which fields set under- and over-delivery tolerance?** Ordered Qty Tolerance Under and Ordered Qty Tolerance Over.
4. **Which fields set early- and late-shipping tolerance?** Shipped Before Due Date Tolerance and Shipped After Due Date Tolerance.
5. **Which report evaluates the policy for analysis?** Delivered In Full And On Time Report.

**Section Summary:** DIFOT uses a default-and-override hierarchy plus quantity and date tolerances.
### Keywords
DIFOT policy, Order Entry Parameters, quantity tolerance, date tolerance

## Credit-card shipping freight
**Guide pages:** 56-58.

1. **Why are shipping charges calculated before a credit-card order is submitted?** The guide says the customer needs the total charge before submission.
2. **Which forms define freight rules and selectable ship methods?** Freight Charge Methods, Ship Methods, and Ship Method Groups.
3. **Where can a customer-specific Ship Method Group be assigned?** Customers or Multi-Site Customers.
4. **Where does calculated shipping freight appear on the order?** In the Freight field of Customer Orders.
5. **What happens when no Ship Method is entered for that credit-card calculation?** No automatic shipping freight is calculated by that feature; the standard freight-entry process is used.

**Section Summary:** Credit-card ship methods calculate estimated freight before order submission.
### Keywords
credit card, Ship Method, Freight Charge Methods, Freight field

## Tracking and package labels
**Guide pages:** 134, 138-140.

1. **Which form records shipment carrier and tracking details in the guide?** Shipment Master has ship-via, tracking number, and tracking URL fields.
2. **Which query can show shipment tracking numbers?** Shipment Tracking.
3. **Which forms define carrier and service information?** Carriers and Ship Via Codes.
4. **Which form initiates printing package labels?** Print Package Labels using configured Package Label Templates and the external BarTender workflow.
5. **Can a tracking number be assumed from a shipped order alone?** No. Check the current Shipment Master or tracking records and carrier integration result.

**Section Summary:** Shipment tracking and label production use specific forms and configured external software.
### Keywords
Shipment Tracking, tracking number, Ship Via Codes, Print Package Labels

## Shipment documents and inquiries
**Guide pages:** 138-139.

1. **Which guide report provides shipment packing-slip output?** Shipment Packing Slip Report.
2. **Which guide report provides bill-of-lading output?** Shipment Bill of Lading Report.
3. **Which other shipment document reports are named?** Shipment Pro Forma Invoice, Certificate Of Origin, and Canada Customs Invoice reports.
4. **Which query form locates shipment records?** Shipment Master Query.
5. **Which query form locates pick-list records?** Pick Maintenance Query.

**Section Summary:** Shipment documents and query forms provide evidence separate from posting itself.
### Keywords
packing slip, bill of lading, Shipment Master Query, Pick Maintenance Query

## Shipment diagnosis and live-data boundary
**Guide pages:** 27-31, 55-59, 69-71, 132-142.

1. **What should be checked first when a shipment cannot post?** Identify route, order and line, site or warehouse, exact message, and both credit-hold levels.
2. **What should be checked when pick-list posting skips a line?** Check on-hand quantity, lot or serial tracking, Post Material Issues, and credit holds.
3. **What should be checked when a Picked list stalls?** Review Qty Picked, Pick Maintenance status, shipment assignment, and the site's route.
4. **What should be checked when a shipped order is not invoiced?** Check approval state and whether standard or consolidated invoicing applies.
5. **Can this article report current shipped quantity or delivery proof?** No. Retrieve those from permission-checked live SyteLine and carrier records.

**Section Summary:** Diagnose by route and current transaction evidence; the article cannot certify live shipment state.
### Keywords
shipment troubleshooting, credit hold, picked status, invoice eligibility, live data
