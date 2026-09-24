# Shipment

## Overview

A Shipment records the physical delivery of ordered goods to a Customer. It is created from a
released Customer Order once the items are picked and packed, and it captures what was actually
shipped — which may differ from what was originally ordered if a line ships partially.

### Keywords
shipment, delivery, dispatch, ship confirm

---

## Partial Shipments

Not every order ships in one piece. If only part of a line's quantity is available, that line can
be shipped partially — the shipped quantity is recorded on the Shipment, and the remaining
quantity stays open on the Customer Order as a backorder. Backordered lines automatically appear
on a new shipment once inventory becomes available, unless the customer has requested the
remainder be cancelled instead.

**Section Summary:** Partial shipments split a line into what shipped now and what remains as a
backorder for later.

### Keywords
partial shipment, backorder, split shipment

---

## Troubleshooting: Shipment Won't Confirm

If a Shipment will not confirm, check the following:

1. **Inventory availability** — the on-hand quantity at the shipping site must cover the shipped
   quantity being entered.
2. **Credit Hold** — a Customer Order on Credit Hold cannot generate a confirmable shipment even
   if goods are physically ready.
3. **Missing carrier or ship-via information** — required on the Shipment header before
   confirmation.

**Section Summary:** Shipment confirmation failures are usually inventory shortages, an unresolved
Credit Hold, or missing carrier information.

### Keywords
shipment won't confirm, ship confirm error, troubleshooting
