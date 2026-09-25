# CRM Campaigns, Competitors, Teams, and Sales Forecasts

## Scope and record boundaries

SyteLine CRM can organize marketing contacts and campaign activity before a lead exists, and can summarize opportunities in a sales forecast before a customer order exists. These are related but different records. A campaign contact is not automatically a lead; a lead is not automatically an opportunity; an opportunity or forecast is not booked revenue. The deployed release and site may expose different optional fields or use a different marketing process. Confirm local statuses, ownership, communication rules, and permissions before telling a user to change records.

**Section Summary:** Campaigns generate or organize interest; opportunities and forecasts track potential sales; orders represent booked transactions.

### Keywords
campaign, Sales Contacts, lead, opportunity, sales forecast, booked order

## Sales contacts and contact groups

Sales Contacts identifies people who may be associated with a prospect or customer. A contact group is a reusable selection of people for a marketing or sales activity. The Add Sales Contacts form can take contacts from Customers, Prospects, Campaigns, Sales Contact Groups, or Sales Contacts, filter the source, then select people to add to a group or campaign. Check the contact's current organization relationship and approved communication preferences before including them. If a person appears twice, compare the underlying contact records and cross-references; do not assume a duplicate campaign row means two different people.

| Data to inspect | Why it matters |
| --- | --- |
| Contact identity and organization reference | Distinguishes a person from the prospect or customer company. |
| Contact group and campaign membership | Explains why the person is in an audience. |
| Preferred communication information | Helps select a permitted channel; it is not itself proof of consent. |
| Interaction or communication history | Shows prior outreach and follow-up, subject to access rights. |

**Section Summary:** Contact groups select an audience; organization links and communication rules must be checked separately.

### Keywords
Sales Contacts, Sales Contact Groups, Add Sales Contacts, campaign audience, duplicate contact

## Create and work a campaign

The Campaigns form holds the campaign record. Campaign Items holds items associated with the campaign; these are marketing context, not an order line. A general sequence is: create a contact group or select contacts, create the campaign, add the intended contacts using Add Sales Contacts, add relevant Campaign Items, then record authorized communications and responses. A Communication Wizard may be available for an email promotion; its use depends on the site's communication setup and privacy policy. A response indicating sales interest can be recorded as a lead and associated with the campaign. Do not say that sending a communication automatically creates a lead or customer order.

To answer “Which leads came from this campaign?”, identify the campaign, inspect its Leads relationship and lead-source information, then verify each lead's party, date, status, and ownership. To answer “Was the campaign successful?”, define the site's measure first: responses, qualified leads, opportunities, won value, orders, or cash are different measures. Avoid adding those values together as if they were the same stage. Any cost, attribution, or conversion-rate calculation requires approved local definitions and current records.

**Section Summary:** Campaign-to-lead conversion is an explicit business handoff, not an automatic order transaction.

### Keywords
Campaigns form, Campaign Items, Communication Wizard, campaign leads, conversion, attribution

## Competitors and sales teams on opportunities

Competitors stores basic competitor information. An opportunity's competitor association is maintained through Opportunity Competitor Cross References; the related Competitors tab is a view of that association. Salespeople working an opportunity can be added or removed through Opportunity Member Cross References, with the Team Members tab reflecting those relationships. The opportunity's salesperson, team, or territory helps route ownership and reporting, but a territory is not by itself a security filter. Use actual SyteLine permissions to decide whether a user may see or modify the opportunity.

When a user asks why a competitor or team member is missing, check the opportunity identifier, cross-reference record, active status, and site access. Do not invent a competitor ranking, deal strategy, or salesperson assignment from the opportunity narrative alone. A won/lost reason is recorded on the opportunity and should be reviewed for accuracy before using it in pipeline reporting.

**Section Summary:** Competitor and team relationships are separate records; their display tabs do not own all edits.

### Keywords
Competitors, Opportunity Competitor Cross References, Opportunity Member Cross References, Team Members, territory

## Sales forecast preparation and submission

Sales Forecasts groups pipeline expectations for a sales period and salesperson. Select the correct Sales Period and salesperson, inspect the opportunities and forecast values included, reconcile outdated estimated values or projected close dates on the owning Opportunities records, and review any manual forecast adjustments according to the site's approval process. In documented CRM behavior, changes to a related opportunity can update its forecast opportunity value while the forecast is Draft. A Submitted forecast is a reporting or approval state; it is not an invoice, payment, or actual sale. Do not assume the forecast continues to auto-update after submission.

For a forecast question, separate four measures: opportunity estimated value, win probability, forecast amount, and actual booked or invoiced value. Ask for sales period, salesperson/team, site, and currency if missing. A future sales estimate cannot answer “How much did we invoice?”; that requires authorized invoice or A/R records. A weighted estimate such as value times probability is a business formula only if the local forecast process uses it; never present it as a universal SyteLine calculation.

**Section Summary:** Forecasts summarize expected business for a period; actual orders, invoices, and cash remain separate records.

### Keywords
Sales Forecasts, Sales Periods, Draft forecast, Submitted forecast, probability, actual revenue

## Troubleshooting and answer boundaries

| Question or symptom | First checks | Safe answer boundary |
| --- | --- | --- |
| Contact missing from campaign | Source group, filter, contact selection, duplicate record | Explain selection path; do not add the person without authorization. |
| Campaign has no leads | Whether leads were explicitly created and associated | Do not infer no interest from an empty Leads tab alone. |
| Competitor missing on opportunity | Opportunity number and competitor cross-reference | Do not edit the display-only tab as if it were the source. |
| Team member missing | Opportunity member cross-reference and access | Verify assignment and security separately. |
| Forecast differs from opportunity | Forecast period, salesperson, Draft/Submitted state, update timing | Explain the snapshot or manual adjustment possibility; verify live records. |
| User asks for current forecast total | Period, owner, site, currency, authorization | Use a permission-checked live query; Markdown contains no current totals. |

**Section Summary:** Resolve discrepancies at the owning record and require live, authorized data for current totals.

### Keywords
campaign troubleshooting, forecast mismatch, opportunity ownership, live forecast, permission
