# Customer Order Line and Release Module

This article is derived only from the official Infor SyteLine Customer Service User Guide, release 9.01.x (2020). It paraphrases the manual; no newer online-help topic is used as a source. Confirm differences against the deployed SyteLine release and local configuration before operational use. The guide does not provide current values for a named order.

## Document Metadata
- **Document Title:** Customer Order Lines and blanket releases form guide
- **Document Type:** Process and form reference
- **Module:** customer_order_line
- **SyteLine Forms:** Customer Order Lines, Customer Order Blanket Lines, Customer Order Blanket Releases, Order Detail Tree, Order Shipping, Reservations for Order
- **Process Stage:** Customer order item entry through supply, shipment, and billing handoff
- **Tags:** order line, CO line, line release, item, U/M, quantity, price, Source, Ready to Ship, Invoice Hold
- **Access Level (SyteLine groups):** Effective permissions in the deployed SyteLine site
- **Site Scope:** General guidance; verify originating and shipping sites
- **SyteLine Version:** Source manual release 9.01.x; later-release behavior is unverified
- **Document Owner:** Customer-to-Cash process owner
- **Reviewed / Approved By:** Pending local SyteLine business and security review
- **Last Reviewed:** Not yet locally reviewed
- **Version:** 0.2 draft
- **Source:** Infor SyteLine Customer Service User Guide, release 9.01.x (2020), especially printed pages 11-12, 30-35, 39, 43-46, 53-56, 69-70, 74-80, 88-89, and 96. No external links in this retrieval article.

## Form role and hierarchy

1. Customer Orders owns the header; Customer Order Lines owns item-level demand for a regular order.
2. One header can contain multiple lines for separately sold items or services.
3. Each line carries its own item, quantity, unit price, due date, source, and fulfillment state.
4. Blanket orders use Customer Order Blanket Lines and Customer Order Blanket Releases for scheduled deliveries.
5. Identify order, line, release if applicable, and site before discussing a specific transaction.

**Section Summary:** The line or release is the unit for item-level answers.

### Keywords
Customer Order Lines, regular order, blanket order, hierarchy

## Header handoff and navigation

1. Create or locate the correct Customer Orders header and save it before adding lines.
2. The Lines action on a regular order opens Customer Order Lines.
3. The Releases path on a blanket order leads to blanket lines and scheduled releases.
4. Customer Orders Quick Entry is an alternative way to create an entire customer order.
5. After saving lines, the manual places shipping and invoicing in later, separate steps.

**Section Summary:** Navigate from a saved header to its correct detail form.

### Keywords
Lines button, Releases, Customer Orders Quick Entry, order entry

## Find the intended line

1. Open the saved Customer Orders header and use Lines for a regular order; use the blanket release path for a blanket order.
2. The manual's change-log procedure identifies a line or release separately from its order header.
3. The manual distinguishes Customer Order Lines from Customer Order Blanket Releases.
4. Before interpreting a line, identify its item, quantity, price, due date, and status from the actual record.
5. Blanket lines can have multiple releases, so identify the relevant release before discussing its scheduled quantity.

**Section Summary:** Precise order-line-release keys prevent wrong-record answers.

### Keywords
find line, line number, release number, lookup

## Create and save a regular line

1. From the saved regular order header, choose Lines and create a new line record.
2. Enter or accept the next line number and select the requested item.
3. Verify quantity, U/M, price, discount, due date, warehouse, Ship Site, and Source.
4. Save the line, then inspect status, warnings, holds, and calculated quantities.
5. Before saving, use Get ATP or Get CTP when item availability needs checking.

**Section Summary:** A visible line is not necessarily saved or shippable.

### Keywords
add line, save line, unsaved record, line validation

## Item selection and setup

1. Item identifies the sold product or service and must match the customer's request.
2. The Items record may supply defaults, but verify the values saved on the order line.
3. The manual treats stocked, non-inventory, and Product Configurator planning items through different procedures.
4. SyteLine can warn when an order line uses an item flagged obsolete or slow-moving.
5. A configured-item procedure applies only to Product Configurator planning items.

**Section Summary:** Validate the exact item and applicable controls.

### Keywords
Item, Items form, stocked, configured, item not found

## Description and unit of measure

1. Description helps recognition, but item number is the stronger record identifier.
2. U/M defines the unit used to interpret line quantity and unit price.
3. For a blanket line, U/M defaults from the Items form and can be changed.
4. Customer Order Lines Change Log records U/M updates to an order line or release.
5. The same change log can record a change to a customer order blanket line's U/M.

**Section Summary:** Interpret quantity and price with the same U/M.

### Keywords
description, U/M, unit conversion, sales unit

## Qty Ordered and other quantities

1. Qty Ordered is demand for this line or release, not the entire order.
2. Shipped, returned, reserved, and invoiced quantities are separate measures.
3. Changing Qty Ordered can adjust Allocated to Customer Orders on the Items form.
4. Quantity edits can affect availability, reservations, pricing decisions, and linked supply.
5. Investigate discrepancies using U/M, site, prior shipments, returns, reservations, and release selection.

**Section Summary:** Name the exact line and quantity measure.

### Keywords
Qty Ordered, shipped, returned, allocation

## Unit Price and repricing

1. Unit Price on Customer Order Lines is the price per line U/M.
2. The manual checks promotion pricing before applying its adjustment to the line's net unit price.
3. A valid Customer Contracts price can supply the line's unit price.
4. Customer/item quantity breaks or a Price Matrix formula may determine a default price.
5. If no applicable Item Pricing record exists, SyteLine requires manual price entry.

**Section Summary:** The manual's pricing sequence checks promotions, contracts, quantity breaks, matrix rules, and item pricing.

### Keywords
Unit Price, reprice, contract price, item price

## Discount and line amount

1. Review line discount separately from Unit Price.
2. Discounts or premiums configured by product code and customer type are applied after base pricing.
3. A promotion code on a customer order line can replace Unit Price with an adjusted price.
4. Applying that promotion overrides the existing Sales Discount and sets it to zero.
5. The manual does not allow a promotion code on an entire customer order or a blanket line.

**Section Summary:** Promotion pricing and sales discount have specific precedence in the manual.

### Keywords
discount, line amount, tax, currency

## Order entry and planning dates

1. Order Entry Parameters includes the Standard Due Period used in customer order setup.
2. The order-entry sequence checks availability with Get ATP or Get CTP when needed.
3. The availability result is reviewed before completing the order entry process.
4. Cross-referenced supply with a later due date than demand can produce an APS Move In Receipt exception.
5. A blanket release has its own release date and quantity entered on Customer Order Blanket Releases.

**Section Summary:** Separate setup defaults, availability planning, and blanket release scheduling.

### Keywords
Std Due Period, Due Date, Get ATP, Get CTP, release date

## Warehouse and Ship Site

1. The manual's Multi-Site Item Sourcing form compares candidate sites and warehouses for an order line.
2. That form can compare requested order quantity with quantity available at each warehouse.
3. A user can weigh item availability and distance to the ship-to address when choosing a warehouse.
4. Select returns the chosen site and warehouse to Customer Order Lines.
5. In a multi-site copied order, each line can be placed at its shipping site by the copy process.

**Section Summary:** The manual provides a site/warehouse selection workflow rather than a blanket stock promise.

### Keywords
Warehouse, Ship Site, inventory site, fulfillment

## Line status and progression

1. The manual distinguishes Planned and Ordered customer order line status during credit checks.
2. A line that fails the documented credit checks can be saved as Planned with a warning.
3. Changing a blanket release from Planned to Ordered increases Alloc Order in Inventory.
4. A fully shipped and invoiced line can become Complete when its order is changed to Complete.
5. Customer Order Lines Change Log records status changes, including Planned to Ordered.

**Section Summary:** Credit, allocation, completion, and change logging depend on line status.

### Keywords
Planned, Ordered, Filled, Complete, History

## Credit hold and blocked lines

1. A customer credit-hold problem indicator can appear on Customer Order Lines.
2. Customer-level or order-level Credit Hold can prevent shipping.
3. A credit-held order cannot create a new line cross-reference; an existing one remains.
4. A blank Limit Exceeded Credit Hold Reason means over-limit entry may not automatically hold the order.
5. Removing a hold or advancing a Planned line is an authorized business action.

**Section Summary:** Diagnose the specific hold before discussing line release.

### Keywords
Credit Hold, credit limit, blocked shipping, Planned

## Source area overview

1. The manual says the Customer Order Lines Source tab can show inventory, PO, job, requisition, transfer, and service-order sourcing.
2. Cross-referencing can hard-peg customer order line demand to specific supply.
3. Source sub-tabs can show expected availability even when the user cannot open the underlying supply form.
4. Source set to Inventory means there is no supply-order cross-reference.
5. A line can be cross-referenced to a project task through the Project source procedure.

**Section Summary:** Follow the selected supply path to its actual progress.

### Keywords
Source tab, cross-reference, inventory, PO, job

## Inventory source

1. Inventory is the default Source reference when an item's Stocked field is selected.
2. Inventory Source indicates no one-to-one supply-order cross-reference.
3. Reserving stocked material for an Ordered line reduces the amount still available for other demand.
4. When a blanket line/release changes from Planned to Ordered, its Ready Quantity can update from zero for Inventory reference.
5. The Available to Ship Report uses Ship Partial and line readiness to decide which orders appear.

**Section Summary:** Stocked-item sourcing, reservations, and shipping readiness are separate checks.

### Keywords
Inventory source, on hand, non-nettable, Available to Ship

## Job source

1. Job source links line demand to manufacturing supply.
2. A non-stocked manufactured item can default to Job source under matching item setup.
3. A job reference can include job number, suffix, and operation; routing/BOM may need further work.
4. The manual instructs the user to save the line, click Source, confirm the cross-reference, and complete or copy the job routing.
5. For a job-cross-referenced blanket release, quantity moved from the completed job updates Ready Quantity in Order Shipping.

**Section Summary:** A linked job is not finished stock.

### Keywords
Job source, manufacturing, job number, routing, BOM

## Purchase Order source

1. Purchase Order source links demand to material bought from a vendor.
2. The reference identifies a PO number and line or release according to PO type.
3. The manual directs the user to save the line and click Source to create or confirm the PO cross-reference.
4. Receiving a cross-referenced PO updates the customer order line/release Ready Quantity.
5. A vendor promise is not a customer shipment; inspect receipt, readiness, shipping, and invoice evidence.

**Section Summary:** Trace purchased supply through receipt.

### Keywords
Purchase Order source, PO receipt, vendor promise

## Requisition source

1. Requisition source represents a request to buy, which can later lead to a PO.
2. Its reference can contain requisition number and line number.
3. The customer order-to-requisition procedure uses the line's Source tab.
4. After saving, Source can create or display the cross-referenced requisition line.
5. The manual also permits a range of PO requisition cross-references through Material Planner Workbench.

**Section Summary:** A purchase request is distinct from available material.

### Keywords
Requisition, PO requisition, buyer, source delay

## Transfer source

1. Transfer source links demand to movement between sites or warehouses.
2. The customer order-to-transfer cross-reference starts at the To site where demand originates.
3. It links the customer order line to a transfer order line at that To site.
4. The transfer supply is reserved for that customer order and cannot serve another demand order.
5. Material Planner Workbench can cross-reference a range of transfer order lines.

**Section Summary:** Trace both sides of a transfer before promising delivery.

### Keywords
Transfer, From site, To site, receipt

## Project and SRO source

1. A customer order line or blanket release can be cross-referenced to a project task.
2. Before creating a linked project, define the cost accounts for the item's product code.
3. The Project Source procedure can use an existing project and task or create new ones.
4. Non-inventory items cannot be sourced to projects under this manual's procedure.
5. The guide mentions service orders in the Source-tab overview but gives no detailed SRO line procedure here.

**Section Summary:** The manual describes project cross-reference steps but only mentions SRO in overview.

### Keywords
Project, SRO, service order, optional module

## Cross-reference rules

1. Demand-to-supply cross-reference hard-pegs specific supply to specific demand.
2. General Infor guidance treats a cross-reference as one-to-one.
3. The manual's detailed CO cross-reference procedures cover job, PO, requisition, transfer, and project supply.
4. Planning can raise shortage or move-in messages when supply quantity or date misses demand.
5. Check credit hold, Source, planning mode, and permission before creating a reference.

**Section Summary:** Dedicated supply still needs quantity and timing checks.

### Keywords
hard peg, cross-reference, shortage, planning exception

## Reservations and traceability

1. Normal reservation needs an item marked Reservable and a line in Ordered status.
2. Reservations for Order or Item can show line, warehouse, location, and lot.
3. Serial-tracked items can use specific serials in the reservation process.
4. Reservation reduces unsatisfied planning demand but is not a posted shipment.
5. Verify a reservation with its reservation record or the Reserved Inventory by Order Report.

**Section Summary:** Reservation, readiness, and shipment are distinct.

### Keywords
reservation, lot, serial, Reservable

## Ready to Ship versus Available to Ship

1. The manual refers to Ready Quantity in Order Shipping for cross-referenced line/releases.
2. Job quantity moved to inventory can update Ready Quantity for a job-cross-referenced blanket release.
3. Receipt of a cross-referenced PO updates the customer order line/release Ready Quantity.
4. Available to Ship Report can be narrowed by its writable selection fields.
5. The report includes an order according to Ship Partial and whether all or at least one line is ready.

**Section Summary:** Ready Quantity and report inclusion depend on documented source and Ship Partial rules.

### Keywords
Ready to Ship, Available to Ship Report, competing demand

## Partial shipment and balances

1. With Ship Partial cleared, the Available to Ship Report shows an order only if all lines are ready.
2. With Ship Partial selected, the report can show an order if at least one line is ready.
3. The Ship Partial check box does not allow partial quantities of an individual line to be shipped.
4. The manual calculates reservation demand from ordered, shipped, returned, and already-reserved quantities.
5. A shipment reduces Alloc Order quantity for the shipped item on a blanket line/release.

**Section Summary:** Ship Partial affects order inclusion, not permission to split a line quantity.

### Keywords
partial shipment, Ship Partial, remaining quantity

## Pick and shipping handoff

1. The manual puts order shipping after order header and line entry.
2. For standard shipping, run Available to Ship Report with useful selection filters.
3. Then run Shipping Processing Orders for the desired order.
4. The manual treats Picking/Packing/Shipping and standard Order Shipping as different paths, not one combined routine.
5. Customer or order Credit Hold prevents shipping under the documented process.

**Section Summary:** Follow the shipping path used by the site after order entry.

### Keywords
pick, Order Shipping, shipment detail

## Invoice hold and billing handoff

1. Invoice Hold on Customer Order Lines or Customer Order Blanket Releases prevents automatic invoicing.
2. The manual gives an example of waiting for the customer's receipt confirmation before invoicing.
3. After removing Invoice Hold, already-shipped quantity is available on the next invoicing run.
4. Consolidated Invoice can be selected on the line/release Amounts tab when its eligibility conditions are met.
5. Printing an invoice posts the transaction to Accounts Receivable under ordinary order invoicing.

**Section Summary:** Follow shipped demand through actual billing.

### Keywords
Invoice Hold, shipped not invoiced, consolidated invoice

## Blanket line and release branch

1. A blanket order has Order Type Blanket on Customer Orders.
2. Customer Order Blanket Lines describe agreed items and blanket quantities.
3. Customer Order Blanket Releases carry scheduled dates and quantities.
4. Reconcile Quantity Released with Blanket Quantity rather than treating the line as one shipment.
5. The blanket line U/M defaults from the Items form and can be changed before adding its releases.

**Section Summary:** Delivery questions must identify the specific release.

### Keywords
blanket line, blanket release, Quantity Released

## Non-inventory item branch

1. The manual requires manual Unit Price for non-inventory items.
2. Non-inventory items cannot be sourced to jobs under the documented CO-to-job procedure.
3. Non-inventory items cannot be sourced to projects under the documented CO-to-project procedure.
4. For a non-inventory line, the material cost is the cost entered on that customer order line.
5. The manual says only the COGS material account is debited for non-inventory items.

**Section Summary:** Non-inventory demand needs different price and supply checks.

### Keywords
non-inventory, manual price, non-stocked

## Configured item branch

1. The manual's configured-item order-entry procedure applies only to Product Configurator.
2. Select a configurable planning item on Customer Order Lines.
3. On the Features tab, select an item for each feature group.
4. Completing feature choices enables Config String on the line.
5. Create Item can add the configured item to inventory, subject to Inventory Parameters Create Feature.

**Section Summary:** Configuration behavior is conditional.

### Keywords
Product Configurator, Features, Config String, Create Item

## Change log and corrections

1. Customer Order Lines Change Log can record Ordered-line creation and Planned-to-Ordered changes.
2. It can record changes to Qty Ordered, price, discount, Due Date, and U/M.
3. It can record Ordered-line deletion and other status changes.
4. The manual describes order deletion as a separate Customer Orders procedure; selecting Delete flags the order until the form is saved.
5. For an invoiced line's price, discount, or quantity adjustment, the manual provides the Price Adjustment Invoice procedure.

**Section Summary:** Preserve downstream integrity and an audit trail.

### Keywords
Customer Order Lines Change Log, correction, shipped line

## Troubleshooting sequence

1. For an order-entry warning, check the line's item status and credit result described in the guide.
2. For a price question, follow the manual's promotion, contract, quantity-break, matrix, and item-pricing sequence.
3. For missing supply, inspect Source cross-reference, APS exception, and reservation details.
4. For a shipping question, use Ship Partial and Available to Ship Report before the site's shipping process.
5. For a billing question, check Invoice Hold and the actual invoice/A/R transaction.

**Section Summary:** Trace demand through supply, shipment, and billing.

### Keywords
line troubleshooting, diagnostic sequence, order line error

## Source visibility and guide boundary

1. The guide warns that Customer Order Lines users may lack authorization to open related supply forms.
2. Source tab sub-tabs can still show source transaction details and expected material availability.
3. A static manual does not contain the current values of a named customer order line.
4. This article does not specify local IDO names or permissions because the source guide does not define them.
5. Confirm release-specific and site-specific behavior with the SyteLine team before acting on a line.

**Section Summary:** Use the guide for procedure, and obtain current transaction facts through authorized SyteLine access.

### Keywords
Source tab, authorization, live order, version, site

