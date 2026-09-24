# Estimate Module

## Meaning, status, and forms

An estimate holds the proposed items, quantities, price, terms, and dates used to quote a prospect or customer. Use Estimates for the header and Estimate Lines for item detail; Estimates Quick Entry is an alternate entry form. Infor describes header states Working, Quoted, Planned, and History. Quoted means the estimate has been used to quote a price; it does not mean customer acceptance. [Infor creating an estimate](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_an_estimate.htm) [Infor estimate status](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/fields/s/status_estimatesorder_maintenance.html)

**Section Summary:** An estimate is a proposal record; its status must not be confused with an order or payment.

### Keywords
estimate, Estimates form, Working, Quoted, Planned, History

## Prepare the header

1. Create an Estimates record and accept or enter its estimate number.
2. Review Quote Date, Expiration Date, and Status; defaults come from system parameters.
3. Link the relevant prospect or customer and contact where available; record the customer's quote reference if supplied.
4. Review terms, currency, tax information, and order discount shown by the site.
5. Save the header, then open Estimate Lines. [Infor creating an estimate](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_an_estimate.htm)

**Section Summary:** A valid header establishes quote identity, validity period, party, and commercial terms.

### Keywords
create estimate, quote date, expiration date, terms, tax code

## Prepare and review lines

For each Estimate Line, review line number, item, Qty Ordered, U/M, status, Sales Disc, Unit Price, expected delivery, and sourcing details where shown. Inventoried and non-inventoried items can be used. If the line quantity changes, SyteLine may ask whether to recalculate price; record the answer because the quoted price may otherwise stay as it was. A line can be cross-referenced to an estimate job or project when that workflow is enabled. Review totals, taxes, margins, and feasibility before issuing a quote. [Infor creating estimate lines](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/other/process/creating_estimate_lines.htm)

**Section Summary:** Price and delivery must be reviewed at line level, especially after quantity changes.

### Keywords
Estimate Lines, item, quantity, U/M, Sales Disc, Unit Price, estimate job

## Handoff after acceptance

Use Copy Orders and Estimates to create an order from an accepted estimate where the site uses that path. Copying does not preserve every source value: historic values and calculated taxes may be recalculated, and some values come from current customer or tax configuration. Review the new order header and every line before treating it as booked demand. [Infor copying orders and estimates](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454144031054.html)

**Section Summary:** Copying an estimate begins order entry; verify recalculated fields and new order status.

### Keywords
copy estimate to order, accepted estimate, conversion, recalculated tax
