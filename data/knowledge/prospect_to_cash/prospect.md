# Prospect Module

## Record meaning and forms

A prospect is a potential customer represented on the Prospects form. It can be associated with sales contacts, leads, opportunities, and estimates. The Prospects form displays related interactions, leads, opportunities, and estimates in separate read-only tabs; those related records are maintained in their own forms. A prospect can later be moved to a customer, at which time related records are reassigned and the old prospect record is removed.

**Section Summary:** Prospect is an organization before customer setup; linked sales activity lives in its own records.

### Keywords
prospect, Prospects form, potential customer, related tabs

## Create and qualify a prospect

1. Search Prospects and Customers for the organization first to avoid a duplicate account.
2. Create the company on Prospects and record the available organization, address, territory, and owner details shown by the site; exact required fields vary by configuration.
3. Create or select the person on Sales Contacts. Use Prospect Sales Contact Cross References to connect that person to the prospect.
4. Record calls and meetings in Sales Contact Interactions or Prospect Interactions. Include the business need, next action, responsible owner, and follow-up date according to local practice.
5. Create a lead when there is a specific interest to pursue; create an opportunity when the potential sale is qualified.

**Section Summary:** Avoid duplicates, attach contacts, log interactions, and carry a qualified need into a lead or opportunity.

### Keywords
create prospect, Sales Contacts, Prospect Sales Contact Cross References, interactions, qualify

## Move prospect to customer

When the organization is ready to trade, use the Prospects form's Move To Customer action, review the Move Prospect To Customer form, provide any required bank code, process, and verify the new Customers record. Because conversion changes record identity and relationships, confirm the correct prospect and review linked leads, opportunities, estimates, and contacts afterward. This is an operator action, not a chatbot action.

**Section Summary:** Prospect conversion creates a customer and reassigns linked activity; verify the result.

### Keywords
move prospect to customer, convert prospect, customer creation

## Common questions and checks

If a prospect cannot be found, check the site, search criteria, and whether it has already been converted. If a contact is missing, inspect the sales contact cross-reference. If a linked estimate or opportunity is missing from a read-only tab, open the owning form and verify its prospect/customer reference. Do not claim the user lacks permission without checking the site's actual security rules.

**Section Summary:** Look for conversion, references, and site context before assuming missing data.

### Keywords
missing prospect, missing contact, prospect converted, troubleshooting

## Prospect data to capture and why it matters

| Data group | What to record | Why the next stage needs it |
| --- | --- | --- |
| Identity | Prospect number, legal or trading name, address, region | Prevents duplicate organizations and identifies the party for a lead or estimate. |
| People | Sales contact name, role, phone/email, communication preference | Identifies whom to contact and which person expressed the need. |
| Ownership | Assigned salesperson or team, territory if used | Gives follow-up a responsible person; territory is a reporting classification, not a permission rule. |
| Interaction | Date, channel, summary, product interest, follow-up date | Explains why the prospect exists and what action is due next. |
| Qualification | Need, expected timing, interested product or service, next decision | Helps decide whether to open a lead or opportunity. |

Some labels are site-dependent. The Prospects form is the owner of the company record; Sales Contacts owns the person; cross-reference forms link them. Never infer that the person is linked merely because a matching name appears in an interaction note.

**Section Summary:** Separate company identity, person identity, ownership, and interaction history.

### Keywords
prospect fields, sales contact, prospect number, territory, qualification

## Conversion checks and exceptions

Before Move Prospect To Customer, check that the selected prospect is the correct organization, review linked contacts and open opportunities, and collect customer setup information needed by finance and order entry. After processing, search Customers for the new account and verify its bill-to, ship-to, terms, and linked activity. If the old prospect no longer appears, conversion may be the reason; do not recreate it as a duplicate. A failed conversion needs the exact form error and required setup values, not a guessed workaround.

**Section Summary:** Conversion is a record handoff that must be checked on both sides.

### Keywords
prospect conversion checklist, Move Prospect To Customer, missing converted prospect
