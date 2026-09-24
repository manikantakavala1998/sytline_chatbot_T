# Fulfillment and Shipment Module

## What shipment means

Shipment is the fulfillment of a specific customer order line/release quantity from a shipping site. Order entry, reservation or supply, picking, shipment processing, and shipment confirmation are separate checkpoints. Infor supports more than one route: Available to Ship Report plus Shipping Processing Orders, order pick lists, and shipment-based confirmation. Choose the procedure your site uses.

**Section Summary:** Explain the actual fulfillment route and shipped quantity, not just the order status.

### Keywords
shipment, fulfillment, order shipping, Shipping Processing Orders, Ship Confirmation

## Standard fulfillment checklist

1. Confirm the order/line is eligible to ship and identify shipping site, warehouse, item, U/M, and requested or due date.
2. Check customer and order Credit Hold, letter-of-credit rules where applicable, availability, and any lot/serial or reservation requirements.
3. Review Available to Ship Report or the site's pick workflow; generate a pick list or use Pick Workbench if enabled.
4. Record the actual picked and shipped quantities; check carrier/ship-via, packing slip, and delivery details as required by local setup.
5. Process the shipping transaction or confirm the shipment, then verify order line shipped quantity and shipment history.
6. Pass shipped-not-invoiced lines to the invoice process.

**Section Summary:** Check holds and supply, record actual quantities, and verify the posted shipment.

### Keywords
pick list, available to ship, shipping transaction, packing slip, ship via

## Partial shipment and backorder

The Ship Partial option controls whether the Available to Ship Report lists an order with only some lines ready; Infor notes it does not by itself authorize a partial quantity of a line. Different shipping processes can handle quantities differently. Determine what actually shipped and what remains open from order and shipment data. Do not promise that a remainder will automatically create a new shipment.

**Section Summary:** Separate partial order readiness from partial line quantities and verify the actual remainder.

### Keywords
partial shipment, backorder, Ship Partial, remaining quantity

## Troubleshooting a shipment that cannot post

Check exact error, customer/order holds, line status, site/warehouse, inventory and reservation, serial/lot details, credit/letter-of-credit checks, ship-to, and required logistics fields. The Available to Ship Report excludes held orders and has its own allocation calculation. For a PO/job/transfer sourced line, Ready to Ship may remain zero until receipt or completion. Escalate with the order, line, site, and error message rather than altering credit or inventory settings blindly.

**Section Summary:** A shipping error can arise from credit, availability, status, or logistics configuration.

### Keywords
shipment won't confirm, cannot ship, Ready to Ship, inventory shortage

## Quantities, documents, and handoffs

| Record or quantity | What it tells the user |
| --- | --- |
| Ordered quantity | What the customer requested on the line. |
| Ready/available quantity | What supply appears available to fulfil now; report logic may differ from the line display. |
| Picked quantity | What warehouse staff selected; picking alone is not a posted shipment. |
| Shipped quantity and date | What the shipping transaction recorded. |
| Packing slip or shipment reference | Evidence for the physical delivery process. |
| Unshipped remainder | Difference to investigate for later fulfillment or cancellation. |

The selected shipping method may use Order Shipping, Shipping Processing Orders, an order pick list, Pick Workbench, or Ship Confirmation. Match the documentation to the actual workflow and selected order. A shipped quantity can be lower than ordered quantity; check whether the remainder remains open rather than assuming it will ship automatically.

**Section Summary:** Picking, posting shipment, and invoicing are separate events with different records.

### Keywords
picked quantity, shipped quantity, packing slip, order shipping, remainder

## Shipment-to-invoice handoff

After posting shipment, verify the correct customer, order, line/release, quantity, date, and site. Check whether a shipment approval requirement applies and whether the line is on Invoice Hold. The shipped but uninvoiced quantity becomes a candidate for the standard order invoicing process. A shipment event by itself is not proof of an invoice or A/R balance. If the customer reports nonreceipt, compare the posted shipment with the packing and carrier evidence under local procedure.

**Section Summary:** Verify the posted shipment and invoice eligibility independently.

### Keywords
shipment approval, shipped not invoiced, Invoice Hold, delivery dispute
