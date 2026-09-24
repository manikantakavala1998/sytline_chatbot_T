# Fulfillment and Shipment Module

## What shipment means

Shipment is the fulfillment of a specific customer order line/release quantity from a shipping site. Order entry, reservation or supply, picking, shipment processing, and shipment confirmation are separate checkpoints. Infor supports more than one route: Available to Ship Report plus Shipping Processing Orders, order pick lists, and shipment-based confirmation. Choose the procedure your site uses. [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html) [Infor generate order pick list](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/uss1528996266009.html)

**Section Summary:** Explain the actual fulfillment route and shipped quantity, not just the order status.

### Keywords
shipment, fulfillment, order shipping, Shipping Processing Orders, Ship Confirmation

## Standard fulfillment checklist

1. Confirm the order/line is eligible to ship and identify shipping site, warehouse, item, U/M, and requested or due date.
2. Check customer and order Credit Hold, letter-of-credit rules where applicable, availability, and any lot/serial or reservation requirements.
3. Review Available to Ship Report or the site's pick workflow; generate a pick list or use Pick Workbench if enabled.
4. Record the actual picked and shipped quantities; check carrier/ship-via, packing slip, and delivery details as required by local setup.
5. Process the shipping transaction or confirm the shipment, then verify order line shipped quantity and shipment history.
6. Pass shipped-not-invoiced lines to the invoice process. [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html) [Infor generate order pick list](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/uss1528996266009.html)

**Section Summary:** Check holds and supply, record actual quantities, and verify the posted shipment.

### Keywords
pick list, available to ship, shipping transaction, packing slip, ship via

## Partial shipment and backorder

The Ship Partial option controls whether the Available to Ship Report lists an order with only some lines ready; Infor notes it does not by itself authorize a partial quantity of a line. Different shipping processes can handle quantities differently. Determine what actually shipped and what remains open from order and shipment data. Do not promise that a remainder will automatically create a new shipment. [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html)

**Section Summary:** Separate partial order readiness from partial line quantities and verify the actual remainder.

### Keywords
partial shipment, backorder, Ship Partial, remaining quantity

## Troubleshooting a shipment that cannot post

Check exact error, customer/order holds, line status, site/warehouse, inventory and reservation, serial/lot details, credit/letter-of-credit checks, ship-to, and required logistics fields. The Available to Ship Report excludes held orders and has its own allocation calculation. For a PO/job/transfer sourced line, Ready to Ship may remain zero until receipt or completion. Escalate with the order, line, site, and error message rather than altering credit or inventory settings blindly. [Infor shipping customer orders](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144032599.html) [Infor quantity ready](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/fields/r/ready_order_line_maintenance.html)

**Section Summary:** A shipping error can arise from credit, availability, status, or logistics configuration.

### Keywords
shipment won't confirm, cannot ship, Ready to Ship, inventory shortage
