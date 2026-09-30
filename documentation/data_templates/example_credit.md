<!--
FILLED EXAMPLE of SyteLine_Module_Knowledge_Template.md for the Credit module.
The content is GENERIC (standard SyteLine behaviour) — it shows the expected level of detail and
style. Replace it with your company's real process, codes, roles and messages. A real file would
be named credit.md.
-->

# Credit Review and Credit Hold – SyteLine Prospect-to-Cash Knowledge Document

## Document Metadata
- **Document Title:** Credit Review and Credit Hold – Process and Form Reference
- **Document Type:** Process Documentation
- **Module:** example_credit
- **SyteLine Forms:** Customers, Customer Orders, Order Credit Hold Change Utility, Accounts Receivable Parameters
- **Process Stage:** Credit
- **Tags:** credit hold, credit limit, blocked order, on hold, credit check
- **Access Level (SyteLine groups):** AR Clerk, Credit Manager, Sales Rep (view only)
- **Site Scope:** All sites
- **SyteLine Version:** CloudSuite Industrial 10
- **Document Owner:** Chatbot team (example)
- **Reviewed / Approved By:** Example reviewer, Credit team, 2026-09-29
- **Review Cycle:** Quarterly
- **Last Reviewed:** 2026-09-29
- **Version:** 1.0
- **Source:** Infor SyteLine standard documentation (generic example)

---

## Table of Contents
1. Purpose / Overview
2. Roles and Permissions
3. Key Fields
4. How to release a credit hold
5. Common Issues and Resolutions
6. Glossary

---

## 1. Purpose / Overview
Credit review protects the company from shipping to customers who owe too much. SyteLine can hold a whole customer or a single customer order. A held order cannot be shipped until the hold is released by someone with credit authority.

**Section Summary:** Explains what credit holds are and why orders get blocked.

**Keywords:** credit hold, what is credit hold, blocked order, on hold, credit check

---

## 2. Roles and Permissions

| Role / SyteLine group | View | Create | Change | Approve / Release | Notes |
|---|---|---|---|---|---|
| Sales Rep | Yes | No | No | No | Can see that an order is on hold and why |
| AR Clerk | Yes | Yes | Yes | No | Maintains credit limits and hold reasons |
| Credit Manager | Yes | Yes | Yes | Yes | Only role that releases holds |

**Section Summary:** Who can view, change and release credit holds.

**Keywords:** who can release credit hold, permission, not allowed to release, credit authority

---

## 3. Key Fields

| Field | Form | Meaning | Mandatory? | Allowed values / notes |
|---|---|---|---|---|
| Credit Limit | Customers | Maximum the customer may owe, including open orders | No | Amount in the customer's currency |
| Credit Hold | Customers | Blocks all orders of this customer | No | Check box |
| Credit Hold | Customer Orders | Blocks this one order | No | Check box; a reason is recorded |
| Credit Hold Reason | Customer Orders | Why the order is held | When held | Codes set up by the credit team [NEEDS CONFIRMATION] |

**Section Summary:** Meaning of the credit limit and credit hold fields.

**Keywords:** credit limit meaning, credit hold field, hold reason, customer limit

---

## 4. How to release a credit hold

**Path:** Customer → Customer Orders

**Preconditions:**
* You belong to the Credit Manager group.
* The reason for the hold has been reviewed (payment received, limit raised, or approval given).

**Steps:**
1. Open the Customer Orders form and find the order.
2. Check the Credit Hold Reason and the customer's open balance.
3. Clear the Credit Hold check box.
4. Save the order.

**Result / What happens next:** The order can now be picked and shipped (see shipment). If the customer itself is on credit hold, the order stays blocked until the customer hold on the Customers form is released too.

**Section Summary:** Steps to release a credit hold on a customer order.

**Keywords:** release credit hold, remove hold, unblock order, knock off credit hold, take order off hold

---

## 5. Common Issues and Resolutions (Troubleshooting)

**Issue 1:** The order is still blocked after the order hold was released.
**Error message:** none
**Cause:** The customer is also on credit hold.
**Solution:** Release the customer hold on the Customers form, then check the order again.
**Who can fix it:** Credit Manager

**Issue 2:** The Credit Hold check box cannot be changed.
**Error message:** "You do not have permission to change this field"
**Cause:** The user is not in the Credit Manager group.
**Solution:** Ask the credit team to release the hold.
**Who can fix it:** Credit Manager

**Section Summary:** Fixes for orders that stay blocked by credit.

**Keywords:** order still on hold, can't release hold, why is my order blocked, credit error

---

## 6. Glossary

| Term | Meaning | Also called / abbreviation |
|---|---|---|
| Credit Hold | A block that stops shipping until released | On hold, credit block |
| Credit Limit | The maximum a customer may owe | Limit |
| Open Balance | Unpaid invoices plus open orders | Exposure |

**Section Summary:** Definitions of key credit terms.

**Keywords:** glossary, credit terms, definition, meaning

---

## Change History

| Version | Date | Changed by | Change |
|---|---|---|---|
| 1.0 | 2026-09-29 | Chatbot team | First example |
