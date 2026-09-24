# CRM Setup and Navigation

## Purpose and boundary

Infor CSI/SyteLine CRM connects sales contacts, prospects, leads, opportunities, estimates, customers, and orders. These are related records, not a mandatory one-way status chain: an opportunity may belong to an existing customer, and an estimate may be prepared before a prospect becomes a customer. Form names below follow Infor documentation; a site's version, web forms, personalization, and license can change what a user sees. This library explains product workflows. It does not hold customer transactions or grant permission to perform them.

**Section Summary:** CRM records connect the sales cycle but are not forced into a single conversion path.

### Keywords
CRM, SyteLine sales, CSI, prospect to cash, sales cycle, navigation

## Prepare reference values before entering CRM records

1. Define Lead Statuses and Opportunity Statuses; Infor identifies these as required setup values.
2. Decide whether the organization needs Opportunity Sources, Stages, Won Reasons, Lost Reasons, and Task Types.
3. Set up Territories if they will be used for reporting and assignment. A territory does not itself restrict data access.
4. Set up Sales Teams and sales contacts; connect contacts to prospects and existing customers.
5. Enter existing leads, opportunities, tasks, and estimates only after values and ownership are agreed.
6. Test the workflow in a nonproduction site and document local definitions of each status/stage before bulk import.

**Section Summary:** Configure status and classification values before entering or importing records.

### Keywords
Lead Statuses, Opportunity Statuses, Opportunity Sources, Opportunity Stages, Territories, Sales Teams

## Form map and ownership

| Business need | Infor form or report | Main record or result |
| --- | --- | --- |
| Contact identity and preferences | Sales Contacts | Person and communication details |
| Company before customer creation | Prospects | Prospective organization |
| Interest to qualify | Leads, Lead Statuses | Lead tied to prospect or customer |
| Pursue a deal | Opportunities, Opportunity Tasks | Potential sale and next activities |
| Make a proposal | Estimates, Estimate Lines, Estimate Response Form Report | Quote details and customer document |
| Establish trading account | Move Prospect To Customer, Customers, Customer Ship Tos | Customer and delivery locations |
| Book demand | Customer Orders, Customer Order Lines | Order header and line/release |
| Fulfil and bill | Order Shipping, Order Invoicing/Credit Memo | Shipment and invoice transactions |
| Collect | A/R Payments, A/R Quick Payment Application, A/R Aging Report | Receivable settlement |

Use the form displayed in the user's own session. Some current CSI web forms use a `web.` prefix; older forms can coexist during transition. Do not infer the exact form ID, IDO, property, or API method from a display label.

**Section Summary:** Match the business question to its owning form; confirm technical mappings in the deployed site.

### Keywords
form map, form ID, web forms, IDO, prospect, lead, opportunity, estimate, customer

## Local facts to capture for Phase 4

For each enabled form, record the SyteLine version, site, displayed form name, underlying form name, field label, internal property, IDO collection, read or write permission, filter and row rules, API method, and a sanitized sample response. Mark all unverified mappings **[NEEDS SYTELINE CONFIRMATION]**. Never invent these from a screenshot or a generic help page.

**Section Summary:** General knowledge can explain a form; live connector mappings need site validation.

### Keywords
metadata catalogue, IDO, permissions, API, site, version

## Setup dependency order and validation

Lead and opportunity status values should be agreed before users enter records. Optional sources, stages, won/lost reasons, territories, and task types should have written meanings so different salespeople classify the same situation consistently. After setup, create one test prospect, contact, lead, opportunity, task, estimate, and customer handoff in a nonproduction environment. Confirm the links on read-only related tabs and test search by the actual record identifiers. Review each user role's form access in SyteLine; a territory classification alone does not enforce visibility.

**Section Summary:** Configure controlled values, test linked records, and verify access before importing volume.

### Keywords
CRM setup order, status values, opportunity stage, test workflow, form access
