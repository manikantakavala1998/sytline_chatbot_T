# Credit Review and Credit Hold Module

## Customer credit, order hold, and parameters

SyteLine distinguishes customer credit limit, customer-level Credit Hold, and order-level Credit Hold. A customer hold can block shipments without setting every order's checkbox. Automatic over-limit order holds require the Limit Exceeded Credit Hold Reason parameter in Accounts Receivable Parameters; with that field blank, an over-limit order may not be placed on hold by that mechanism. Behavior also depends on Allow Over Credit Limit, customer hierarchy, and site setup. [Infor about credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html)

**Section Summary:** Exceeding a limit does not always produce an automatic hold; inspect configuration and actual order state.

### Keywords
credit limit, customer credit hold, order credit hold, Limit Exceeded Credit Hold Reason

## Diagnose a credit warning or blocked shipment

1. Identify customer, corporate customer if relevant, order, line, originating site, and shipping site.
2. Check the customer-level Credit Hold and the order-level Credit Hold separately, including reason and date where shown.
3. Review the customer's limit, posted balance, on-order balance, aging settings, and any order-specific limit using authorized current data.
4. Check Accounts Receivable Parameters for the configured over-limit hold reason; inspect Allow Over Credit Limit and the line's Planned or Ordered status.
5. If EDI or multi-site is involved, inspect its separate validation and originating-site behavior.
6. Give the user the observed reason and the responsible AR/credit team. Do not claim the hold is cleared until SyteLine confirms it. [Infor about credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html) [Infor order entry steps](https://docs.infor.com/csi/2026.x/en-us/csbiolh/customer_svc_user_cl_sl/mergedprojects/sl_custvend/other/process/order_entry_steps.html)

**Section Summary:** Investigate the actual hold flags, balances, parameters, and line status before explaining the block.

### Keywords
why on hold, available credit, on-order balance, aging, credit warning

## Place or release a hold

Authorized users can set a customer or order hold manually. Order Credit Hold Change Utility can place or release holds across selected customer/order ranges and can use aging parameters. Releasing an order hold does not override a separate customer-level hold. A local approval, reason-code, and audit process may be required, but the exact policy is **[NEEDS SYTELINE CONFIRMATION]**. The chatbot may explain the process; it must not perform a credit override without a future approved action workflow. [Infor about credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html) [Infor credit hold utility](https://docs.infor.com/csi/latest/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036812.html)

**Section Summary:** Credit release requires permission and may still leave a customer-level block.

### Keywords
release credit hold, credit override, Order Credit Hold Change Utility, AR authorization

## Multi-site and subordinate customers

Where a subordinate customer uses corporate credit, the parent credit position affects the order. Replicated multi-site balances and originating-site behavior can change the result of a credit check. Never derive available credit by adding a few visible invoices or orders; use the authorized ERP calculation for that customer and site. [Infor about credit hold](https://docs.infor.com/csi/10.x/en-us/csbiolh/customer_svc_user_cl_sl/lsm1454144036235.html)

**Section Summary:** Corporate and multi-site credit require the configured SyteLine calculation.

### Keywords
corporate credit, subordinate customer, multi-site credit, originating site
