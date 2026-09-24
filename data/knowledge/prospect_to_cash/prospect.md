# Prospect Module

## Record meaning and forms

A prospect is a potential customer represented on the Prospects form. It can be associated with sales contacts, leads, opportunities, and estimates. The Prospects form displays related interactions, leads, opportunities, and estimates in separate read-only tabs; those related records are maintained in their own forms. A prospect can later be moved to a customer, at which time related records are reassigned and the old prospect record is removed. [Infor Prospects form](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/crmtopics/prospects.htm)

**Section Summary:** Prospect is an organization before customer setup; linked sales activity lives in its own records.

### Keywords
prospect, Prospects form, potential customer, related tabs

## Create and qualify a prospect

1. Search Prospects and Customers for the organization first to avoid a duplicate account.
2. Create the company on Prospects and record the available organization, address, territory, and owner details shown by the site; exact required fields vary by configuration.
3. Create or select the person on Sales Contacts. Use Prospect Sales Contact Cross References to connect that person to the prospect.
4. Record calls and meetings in Sales Contact Interactions or Prospect Interactions. Include the business need, next action, responsible owner, and follow-up date according to local practice.
5. Create a lead when there is a specific interest to pursue; create an opportunity when the potential sale is qualified. [Infor CRM scenario 1](https://docs.infor.com/csi/2026.x/en-us/csbiolh/sales_crm_user_cl_sl/lsm1454144070654.html) [Infor CRM scenario 2](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454144070717.html)

**Section Summary:** Avoid duplicates, attach contacts, log interactions, and carry a qualified need into a lead or opportunity.

### Keywords
create prospect, Sales Contacts, Prospect Sales Contact Cross References, interactions, qualify

## Move prospect to customer

When the organization is ready to trade, use the Prospects form's Move To Customer action, review the Move Prospect To Customer form, provide any required bank code, process, and verify the new Customers record. Because conversion changes record identity and relationships, confirm the correct prospect and review linked leads, opportunities, estimates, and contacts afterward. This is an operator action, not a chatbot action. [Infor CRM scenario 5](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/lsm1454144070919.html) [Infor Prospects form](https://docs.infor.com/csi/9.01.x/en-us/csbiolh/mergedprojects/sl_custvend/forms/crmtopics/prospects.htm)

**Section Summary:** Prospect conversion creates a customer and reassigns linked activity; verify the result.

### Keywords
move prospect to customer, convert prospect, customer creation

## Common questions and checks

If a prospect cannot be found, check the site, search criteria, and whether it has already been converted. If a contact is missing, inspect the sales contact cross-reference. If a linked estimate or opportunity is missing from a read-only tab, open the owning form and verify its prospect/customer reference. Do not claim the user lacks permission without checking the site's actual security rules.

**Section Summary:** Look for conversion, references, and site context before assuming missing data.

### Keywords
missing prospect, missing contact, prospect converted, troubleshooting
