<!--
═══════════════════════════════════════════════════════════════════════════════════════════════
SYTELINE PROSPECT-TO-CASH — MODULE KNOWLEDGE DOCUMENT TEMPLATE (version 1.0)

HOW TO USE THIS TEMPLATE
1. Copy this file once per module. Name it after the module in lower case with underscores, e.g.
   customer_order.md, credit.md, shipment.md (the file name is the module id — keep it the same
   as the Excel Q&A file for that module, e.g. credit.md + credit.xlsx).
2. Replace every <placeholder> in angle brackets. Delete sections that really do not apply.
3. Keep every "**Section Summary:**" and "**Keywords:**" line — the chatbot uses them to find the
   right section. Keywords = the words USERS type, including slang and abbreviations.
4. These grey notes (comment blocks) are for you. The chatbot ignores them, so you may leave them in.
5. Run the checker before sending:  python -m scripts.validate_knowledge_data <your file>

HOW THE CHATBOT READS THIS FILE (why the rules matter)
• Every "## " heading starts a new searchable section. The chatbot finds the best 6 sections for
  a question and writes its answer ONLY from them — anything not written here, it cannot say.
• Keep each "## " section to ONE topic and under ~1,000 characters (about 150 words, 5–15 lines).
  Longer sections are split automatically and can lose their heading context.
• "Document Metadata", "Table of Contents" and "Change History" are for people only — they are
  NOT searched. The **Tags:** in the metadata ARE added to every section's keywords.
• Write form, field, button and status names EXACTLY as SyteLine shows them on screen.
• Put exact system messages in quotes: "Credit limit exceeded for customer".
• Unknown or company-specific items: write [NEEDS CONFIRMATION] — never guess.
• Tables are fine — the chatbot turns every row into a sentence ("Field: Credit Limit · Form:
  Customers · Meaning: …") and searches each row on its own. For good results: a header row with
  clear column names; the FIRST column is the thing users ask about (field, status, term, form);
  one fact per row; short cells (no long paragraphs, no merged cells); and one or two plain
  sentences above the table saying what it is about.
• No customer names, real order numbers, prices, personal data, passwords or screenshots.
═══════════════════════════════════════════════════════════════════════════════════════════════
-->

# <Module Name> – SyteLine Prospect-to-Cash Knowledge Document

## Document Metadata
- **Document Title:** <Module Name> – Process and Form Reference
- **Document Type:** <Process Documentation | Form Reference | Troubleshooting Guide>
- **Module:** <module id, same as the file name, e.g. customer_order>
- **SyteLine Forms:** <exact form names, e.g. Customer Orders, Customer Order Lines>
- **Process Stage:** <Lead | Opportunity | Estimate | Quotation | Customer | Customer Order | Pricing | Credit | Shipment | Invoice | Payment | Returns>
- **Tags:** <5–10 words users use for this module, comma-separated, e.g. sales order, SO, customer order, order entry>
- **Access Level (SyteLine groups):** <e.g. Sales Rep, Customer Service, AR Clerk>
- **Site Scope:** <All sites | site codes>
- **SyteLine Version:** <e.g. CloudSuite Industrial 10>
- **Document Owner:** <name, team>
- **Reviewed / Approved By:** <business owner name, date>
- **Review Cycle:** <Quarterly>
- **Last Reviewed:** <YYYY-MM-DD>
- **Version:** <1.0>
- **Source:** <company SOP name / Infor documentation / SME session date>

---

## Table of Contents
1. Purpose / Overview
2. Scope
3. Roles and Permissions
4. Prerequisites and Setup
5. Forms and Navigation
6. Key Fields
7. <Task 1: How to …>
8. <Task 2: How to …>
9. Status Lifecycle
10. Business Rules and Validations
11. What Comes Before and After
12. Common Issues and Resolutions
13. Best Practices
14. Glossary

---

## 1. Purpose / Overview
<!-- 2–4 sentences: what this record means for the business and why users work with it. -->
<What the <record> is, what it is used for, and where it sits in the Prospect-to-Cash process.>

**Section Summary:** <One sentence: what question this section answers, e.g. "Explains what a customer order is and why it is used.">

**Keywords:** <what is a customer order, sales order, SO, order meaning>

---

## 2. Scope
<!-- What this document covers and what it does NOT cover (point to the other module file). -->
* <Covered: …>
* <Covered: …>
* <Not covered: … (see <other_module>.md)>

**Section Summary:** <Defines what is included in this module's process.>

**Keywords:** <scope, …>

---

## 3. Roles and Permissions
<!-- Who may do what. Use the SyteLine group names your company uses. The chatbot uses this to
     explain "why can't I …" questions; it never grants permission itself. -->

| Role / SyteLine group | View | Create | Change | Approve / Release | Notes |
|---|---|---|---|---|---|
| <Sales Rep> | <Yes> | <Yes> | <Own records> | <No> | <…> |
| <Credit Manager> | <Yes> | <No> | <No> | <Yes> | <…> |

**Section Summary:** <Who can view, create, change and approve <records>.>

**Keywords:** <permission, access denied, not allowed, who can approve>

---

## 4. Prerequisites and Setup
<!-- What must exist before a user can do the task: master data, parameters, codes. -->
* <e.g. The customer exists and is not on credit hold.>
* <e.g. Order types and terms codes are set up in <form>.>
* <Company-specific: [NEEDS CONFIRMATION]>

**Section Summary:** <What must be set up before working with <records>.>

**Keywords:** <setup, prerequisites, parameters, codes>

---

## 5. Forms and Navigation
<!-- Every form users open for this module, and how to get there. Exact names. -->

| Form | How to open it (path) | Used for |
|---|---|---|
| <Customer Orders> | <Customer → Customer Orders, or type "Customer Orders" in the form search> | <Order header: customer, dates, terms> |
| <Customer Order Lines> | <From Customer Orders → Lines button> | <Items, quantities, prices, due dates> |

**Section Summary:** <Which forms are used for <module> and how to open them.>

**Keywords:** <which form, where do I, open form, navigation, path>

---

## 6. Key Fields
<!-- The fields users ask about. One row per field. Allowed values exactly as in SyteLine. -->

| Field | Form | Meaning | Mandatory? | Allowed values / notes |
|---|---|---|---|---|
| <Status> | <Customer Orders> | <Where the order is in its life> | <Yes> | <Planned, Ordered, Stopped, Complete> |
| <Due Date> | <Customer Order Lines> | <Date the customer expects the goods> | <Yes> | <…> |

**Section Summary:** <Meaning and allowed values of the key <module> fields.>

**Keywords:** <field meaning, what does <field> mean, mandatory fields, allowed values>

---

## 7. <Task 1: How to <create / process / change> a <record>>
<!-- One "## " section per task users do. Copy this block for each task (7, 8, …).
     Title it the way users ask: "How to create a customer order", "Release a credit hold". -->

**Path:** <Menu → Form → Button>

**Preconditions:**
* <What must be true first>

**Steps:**
1. <Open the <form> form.>
2. <Enter / select …>
3. <Click <button>.>
4. <The system shows: "<exact message>".>

**Buttons and Their Use:**

| Button | What it does |
|---|---|
| <Save> | <Saves the record> |

**Result / What happens next:** <What the record looks like afterwards, and the next task or form (e.g. "The order is now Ordered; next, check credit and ship it — see Shipment.").>

**Section Summary:** <How to <task>, step by step.>

**Keywords:** <how to create order, enter sales order, punch SO, book order, new order>

---

## 8. <Task 2: How to …>
<!-- Same structure as section 7. Add as many task sections as needed; renumber the rest. -->

**Path:** <…>

**Steps:**
1. <…>

**Result / What happens next:** <…>

**Section Summary:** <…>

**Keywords:** <…>

---

## 9. Status Lifecycle
<!-- Every status the record can have, what it means, and what moves it on. -->

| Status | Meaning | Can move to | Who / what changes it |
|---|---|---|---|
| <Planned> | <Not yet firm; no allocation> | <Ordered> | <User changes Status> |
| <Ordered> | <Firm order> | <Complete, Stopped> | <Shipping and invoicing> |

**Section Summary:** <What each <record> status means and how it changes.>

**Keywords:** <status meaning, order status, why is it planned, stuck in status>

---

## 10. Business Rules and Validations
<!-- Rules the system enforces. Quote exact messages. Mark company-specific rules. -->
* <Rule, e.g. An order on credit hold cannot be shipped.>
* <Rule with message: If <condition> → Error: "<exact message>".>
* <Company rule: <…> [NEEDS CONFIRMATION]>

**Section Summary:** <Rules SyteLine enforces for <records>.>

**Keywords:** <validation, rule, error message, not allowed>

---

## 11. What Comes Before and After
<!-- Where this module sits in the chain. This is the most-asked and most-missing content. -->
* **Comes from:** <e.g. An accepted estimate / quotation (see quotation.md).>
* **Leads to:** <e.g. Shipment (see shipment.md), then Invoice (see invoice.md).>
* **How to move on:** <e.g. After the order is Ordered and released from credit, run shipping from <form>.>

**Section Summary:** <What happens before and after <module> in the Prospect-to-Cash flow.>

**Keywords:** <what next, next step, after this, before this, flow>

---

## 12. Common Issues and Resolutions (Troubleshooting)
<!-- The real problems users hit. Get them from the help desk and business users.
     One block per issue. Put the exact error message if there is one. -->

**Issue 1:** <What the user sees, e.g. "Order cannot be shipped.">
**Error message:** "<exact text, or 'none'>"
**Cause:** <Why it happens.>
**Solution:** <What to do, step by step.>
**Who can fix it:** <User / Credit team / IT>

**Issue 2:** <…>
**Error message:** "<…>"
**Cause:** <…>
**Solution:** <…>
**Who can fix it:** <…>

**Section Summary:** <Fixes for common <module> problems.>

**Keywords:** <why can't I, not working, error, stuck, blocked, fix>

---

## 13. Best Practices
* <e.g. Confirm the customer's credit status before promising a ship date.>
* <…>

**Section Summary:** <Recommended ways of working with <records>.>

**Keywords:** <best practice, tips, recommended>

---

## 14. Glossary
<!-- Terms of THIS module. Also add each term to the glossary sheet of the Excel template so the
     chatbot understands abbreviations and nicknames everywhere. -->

| Term | Meaning | Also called / abbreviation |
|---|---|---|
| <Customer Order> | <A confirmed request from a customer to buy goods> | <Sales order, SO, CO> |
| <Credit Hold> | <A block that stops shipping until released> | <On hold, credit block> |

**Section Summary:** <Definitions of key <module> terms.>

**Keywords:** <glossary, definition, meaning, abbreviation>

---

## Change History

| Version | Date | Changed by | Change |
|---|---|---|---|
| <1.0> | <YYYY-MM-DD> | <name> | <First version> |
