# Returns, Credits, and Corrections

## When a return is needed

Return Material Authorization (RMA) records an agreement to accept damaged, defective, or otherwise returned goods and define compensation such as credit, replacement, or repair. It is separate from editing an original shipped order line. A return may refer to an order and line, but the correct workflow depends on whether the original line was invoiced and what compensation was approved.

**Section Summary:** Use the return workflow for a post-shipment goods issue; preserve original transaction history.

### Keywords
RMA, return, damaged goods, replacement, credit memo

## General RMA flow

1. Identify customer, order, line, item, original shipment and invoice, returned quantity, reason, and requested outcome.
2. Create an RMA header and RMA line items with agreed compensation and disposition under local authority.
3. Receive the material through RMA Return Transaction when physical goods come back.
4. Record inspection, repair, rework, replacement, or credit as applicable.
5. Verify the resulting inventory, customer order, credit memo, and A/R effects.

**Section Summary:** Authorize, receive, inspect, compensate, and reconcile a return.

### Keywords
RMA header, RMA line, RMA Return Transaction, return disposition

## Correct a bill without a physical return

Use the appropriate order credit memo or A/R credit/debit memo process for a pricing or billing adjustment, with the original invoice and approved amount as references. Inventory-related transactions and noninventory charges follow different paths. A posted document should not be described as editable in place. For a return involving inventory, a material transaction may be needed before the credit memo adjusts customer balances.

**Section Summary:** Match the correction to the original transaction and document its financial effect.

### Keywords
invoice correction, credit memo, debit memo, price adjustment

## Troubleshooting and approvals

If an RMA or credit is blocked, collect the original order/line, invoice, shipped and returned quantities, current status, exact error, site, and permission context. The approval limit, return window, restocking rule, and credit authority are **[NEEDS SYTELINE CONFIRMATION]**; they are not universal SyteLine facts. The chatbot can explain the path and identify the likely form, but any actual posting or approval needs a future authorized tool flow.

**Section Summary:** Do not infer local return policy or post a credit from general documentation.

### Keywords
RMA blocked, credit approval, return policy, authorization

## Choose the correction path

| Situation | First record to inspect | Typical process to consider |
| --- | --- | --- |
| Goods damaged or returned after shipment | Order line, shipment, invoice | RMA authorization, physical return, disposition, credit or replacement. |
| Price or tax billed incorrectly | Posted invoice and original agreement | Authorized credit/debit memo or other approved billing correction. |
| Customer paid the wrong invoice | Payment and distributions | A/R reapplication or adjustment under finance controls. |
| Item has not shipped | Order line and supply status | Controlled order-line correction where status permits. |

Do not apply the same remedy to all four situations. A credit memo addresses a financial claim; an RMA addresses the physical return agreement and inventory path. A replacement order can create new demand rather than reversing the original invoice. Verify all resulting records and customer communication.

**Section Summary:** Choose a correction based on whether goods, billing, cash application, or unshipped demand is wrong.

### Keywords
return versus credit memo, billing correction, payment reapplication, replacement order
