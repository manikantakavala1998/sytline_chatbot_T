# Credit Review and Credit Hold Module

This customer-to-cash article explains the credit decisions described in the original Infor SyteLine Customer Service User Guide, release 9.01.x. It is guidance for understanding the documented screens, not a source of live customer balances, permissions, or hold state. Local configuration and current user rights must be checked in SyteLine before taking action.

## Document Metadata
- **Document Title:** Credit Review and Credit Hold Module
- **Module:** credit
- **Tags:** customer credit, credit hold, customer orders, EDI, multi-site, order credit hold change utility
- **Document Owner:** Customer-to-Cash knowledge team
- **Reviewed / Approved By:** Pending local SyteLine SME review
- **Last Reviewed:** 2026-10-08
- **Version:** 0.2 draft
- **Source:** Infor SyteLine Customer Service User Guide 9.01.x, printed pages 33 and 96-101

## Credit form map
**Guide pages:** 96-101.

1. **Which documented screens participate in credit review?** Customers holds customer-level credit settings, Customer Orders holds order-level settings, Customer Order Lines handles line-entry warnings, Accounts Receivable Parameters controls an automatic hold reason, EDI Customer Profiles controls EDI validation, and Order Credit Hold Change Utility processes selected orders.
2. **Where do I inspect a customer-level hold?** Open the customer on Customers and inspect the Credit tab; the guide puts the customer Credit Hold selection and Credit Hold Reason there.
3. **Where do I inspect an order-level hold?** Open the order on Customer Orders and inspect the Amounts tab, which contains the order Credit Hold selection and reason.
4. **Which screen controls the over-limit order hold reason?** Accounts Receivable Parameters contains Limit Exceeded Credit Hold Reason, the setting the guide associates with automatic over-limit order holds.
5. **Which utility can hold or release a range of orders?** Order Credit Hold Change Utility offers Hold and Release processing for selected customer and order ranges.

**Section Summary:** Start with the level and screen involved: customer, order, line, parameter, EDI profile, or utility.
### Keywords
credit form map, Customers, Customer Orders, Accounts Receivable Parameters, EDI Customer Profiles

## Customer-level credit hold
**Guide pages:** 96, 99-100.

1. **What does a customer credit hold mean in the guide?** An authorized user can place the customer on Credit Hold from the Customers form, and shipments for that customer are prevented.
2. **Does holding a customer select Credit Hold on every order?** No. The guide explicitly distinguishes the customer hold from the Credit Hold field on individual orders.
3. **Can a customer hold be set manually?** Yes. The documented manual path is Customers, Credit tab, select Credit Hold, select a Credit Hold Reason, then save.
4. **What reason is entered when manually holding a customer?** The user selects a Credit Hold Reason on the Customers Credit tab as part of the documented procedure.
5. **What should I check if shipments are blocked but an order hold box is clear?** Inspect the customer Credit Hold state; a customer-level hold can block shipment without selecting that order's Credit Hold field.

**Section Summary:** A customer hold affects shipping and is not equivalent to marking each order held.
### Keywords
customer hold, Customers Credit tab, shipment prevention, credit reason

## Order-level credit hold
**Guide pages:** 96, 99-100.

1. **What is an order credit hold?** It is a hold associated with the order's Credit Hold field on Customer Orders, separate from the customer's own hold.
2. **Which tab contains the order Credit Hold field?** The guide places order Credit Hold on the Amounts tab of Customer Orders.
3. **Can an order be held directly by a user?** Yes. On Customer Orders, an authorized user can select Credit Hold and a reason on Amounts, then save.
4. **What other paths can select the order Credit Hold field?** The guide identifies automatic over-limit processing and Order Credit Hold Change Utility, in addition to a manual order hold.
5. **How do I distinguish an order hold from a customer hold?** Check the Customers Credit tab for customer state and Customer Orders Amounts tab for the specific order state; do not infer one checkbox from the other.

**Section Summary:** Order hold is an order-specific state with more than one possible origin.
### Keywords
order hold, Customer Orders Amounts tab, manual hold, automatic hold

## Red X hold indicator
**Guide pages:** 96.

1. **What does the red X indicate on a held customer?** The guide shows a red X for the customer on credit hold.
2. **Can orders show a red X when only the customer is held?** Yes. Orders for a held customer show the red X even if an individual order's Credit Hold field is not selected.
3. **Does a red X prove the order Credit Hold field is selected?** No. Inspect Customer Orders Amounts and the Customers Credit tab to identify the actual hold level.
4. **What is the first check after seeing a red X on an order?** Check whether the customer itself is held, then inspect the order's Credit Hold setting.
5. **Why is the hold indicator not enough for a release decision?** The same visible indicator may accompany a customer-level restriction; releasing only an order may leave the customer shipping block in place.

**Section Summary:** Use the indicator as a prompt to inspect both hold levels, not as the hold's full explanation.
### Keywords
red X, hold indicator, customer-level hold, order-level hold

## Automatic over-limit hold activation
**Guide pages:** 96, 98-99.

1. **Which parameter enables the guide's automatic over-limit order hold?** A value in Limit Exceeded Credit Hold Reason on Accounts Receivable Parameters is the documented activation point.
2. **What happens if Limit Exceeded Credit Hold Reason is blank?** The guide warns that an over-limit order may not be held and shipment may not be prevented by that automatic path.
3. **Where is the automatic hold reason maintained?** In the Limit Exceeded Credit Hold Reason field of Accounts Receivable Parameters.
4. **Is an exceeded limit alone proof of an automatic hold?** No. Confirm the A/R reason setting and the actual order Credit Hold state.
5. **How can the automatic over-limit hold behavior be disabled?** The guide's deactivation procedure clears the Limit Exceeded Credit Hold Reason in Accounts Receivable Parameters.

**Section Summary:** Automatic order holding depends on a configured reason; it cannot be assumed from exposure alone.
### Keywords
over credit limit, A/R parameter, Limit Exceeded Credit Hold Reason

## Missing automatic hold reason
**Guide pages:** 96, 98.

1. **Can an order exceed the limit without that setting placing it on hold?** Yes. The guide cautions that a blank Limit Exceeded Credit Hold Reason can leave an over-limit order unheld.
2. **Does an absent automatic reason prove the order is shippable?** No. A customer-level or manually applied order hold may still prevent progress; inspect current state.
3. **Which screen should be checked when expected automatic holding is absent?** Inspect Limit Exceeded Credit Hold Reason on Accounts Receivable Parameters, subject to access rights.
4. **Should the chatbot promise that all over-limit orders are blocked?** No. The documented behavior depends on the A/R setting and the way the order line was entered.
5. **What should an agent report if the over-limit reason is not known?** State that automatic hold behavior is configuration-dependent and ask an authorized user to verify the A/R setting and the order state.

**Section Summary:** A missing A/R reason is a meaningful configuration difference, not a generic error.
### Keywords
blank reason, no automatic hold, configuration-dependent credit

## New line credit evaluation
**Guide pages:** 33, 97.

1. **When does the guide evaluate a new order line against available credit?** The check occurs when the new line is saved.
2. **Which two credit measures are mentioned in the order-entry steps?** The guide refers to the customer's total available credit and then the order limit when saving a line.
3. **Where is Allow Over Credit Limit used?** It is an order-line entry option for a new line, affecting the outcome when the credit check fails.
4. **Can the Allow Over Credit Limit option be changed for an existing line?** The guide says it is editable only for new lines.
5. **What should be inspected after a credit warning on line save?** Check the new line's resulting status, its Allow Over Credit Limit choice, the order hold state, and the relevant reason configuration.

**Section Summary:** A save-time credit warning can lead to different line and order outcomes.
### Keywords
order line save, available credit, Allow Over Credit Limit, order limit

## Allow Over Credit Limit selected
**Guide pages:** 33, 97.

1. **What happens to a new over-limit line when Allow Over Credit Limit is selected?** The guide says the line is saved as entered in Ordered status and a warning appears.
2. **Does selecting Allow Over Credit Limit remove the credit warning?** No. The warning is still displayed.
3. **Can the order be placed on hold after that line is saved?** Yes. If a reason code is defined in the Reason field on the customer's Credit tab, the guide says the order is placed on hold.
4. **Is Ordered status evidence that credit was acceptable?** No. An over-limit line can remain Ordered when the option was selected.
5. **What should an agent explain for an Ordered line and held order?** Those states can coexist when Allow Over Credit Limit is selected and the customer's Credit-tab Reason is defined.

**Section Summary:** The selected option preserves Ordered line status but does not make the exposure acceptable.
### Keywords
allow over credit limit selected, Ordered line, warning, held order

## Allow Over Credit Limit cleared
**Guide pages:** 33, 97.

1. **What happens to a new over-limit line when Allow Over Credit Limit is cleared?** The guide says the line is saved in Planned status and a warning is displayed.
2. **Does a Planned over-limit line update On Order Balance?** No. The guide says that balance is not updated for this case.
3. **Is the order automatically put on credit hold by this Planned-line path?** No. The guide distinguishes it from the option-selected case and says the order is not placed on hold.
4. **What choice remains after the new line is saved Planned?** The user can later change it to Ordered or delete it, according to the guide.
5. **Why should a Planned line not be described as a released order?** Planned is a line status reached by a particular credit-entry choice; it does not by itself describe every other hold or shipping condition.

**Section Summary:** A new line can be saved Planned instead of producing an order hold.
### Keywords
Allow Over Credit Limit cleared, Planned line, On Order Balance

## Existing line changes
**Guide pages:** 97.

1. **What happens when an existing line is changed so the order exceeds credit?** The guide describes a warning and automatic order hold when a credit hold reason is configured.
2. **Is the new-line Allow Over Credit Limit choice editable during that change?** No. The guide limits editing that option to new lines.
3. **Why is an existing-line credit result not identical to adding a new line?** The guide documents a separate outcome for changing an existing line, including possible automatic order hold.
4. **What should be checked after increasing an existing line's value?** Inspect the warning, the order Credit Hold state, and the configured hold reason.
5. **Can an existing-line change be discussed without live order values?** The general rule can be explained, but the actual exposure and hold status require current SyteLine data.

**Section Summary:** Editing an existing line has its own documented hold behavior.
### Keywords
existing line, changed quantity, credit warning, automatic order hold

## Corporate customer exposure
**Guide pages:** 97.

1. **How does the guide treat a subordinate customer with a corporate credit limit?** It compares the current order plus corporate posted and on-order amounts against the corporate limit.
2. **Is the current order excluded from the corporate check?** No. The current order is part of the documented comparison.
3. **Are posted amounts relevant to a corporate credit check?** Yes. Corporate posted amounts are included.
4. **Are other on-order amounts relevant to corporate exposure?** Yes. The guide includes corporate on-order amounts in the comparison.
5. **Should a chatbot calculate the actual corporate headroom from this article alone?** No. The article states the rule, but current balances, relationships, and limits must come from authorized live data.

**Section Summary:** Corporate credit checks use a broader exposure than only the current line.
### Keywords
corporate customer, subordinate, posted amount, on-order amount

## Held-order cross-references
**Guide pages:** 97.

1. **Can a new line cross-reference be made while the order is on credit hold?** The guide says a held order cannot make a new line cross-reference.
2. **What happens to a cross-reference that already existed before the hold?** It remains in place.
3. **Does a credit hold automatically delete cross-references?** No. The guide distinguishes blocking new ones from retaining existing ones.
4. **What should an agent inspect before advising a new cross-reference?** Confirm whether the order is currently on hold and whether the reference is new or existing.
5. **Why does an existing cross-reference not prove the order is currently unheld?** The reference may have been created before the credit hold and is retained afterward.

**Section Summary:** Credit hold blocks new cross-references but does not erase prior ones.
### Keywords
cross-reference, held order, existing reference

## EDI credit validation
**Guide pages:** 97-99.

1. **Which EDI setting validates a customer's credit limit?** Validate Credit Limit on EDI Customer Profiles.
2. **What is the documented effect when EDI Validate Credit Limit is selected?** An EDI order that exceeds the limit is prevented from posting.
3. **Does the EDI validation setting live on Customer Orders?** No. The guide places it on EDI Customer Profiles.
4. **Is an EDI posting failure the same as a posted order on hold?** No. The validation path prevents posting, while another configuration permits posting and then holding.
5. **What should be checked when an over-limit EDI order did not post?** Inspect the customer's EDI Customer Profiles Validate Credit Limit setting, plus the actual processing result.

**Section Summary:** EDI validation can stop posting before an order exists as a posted held order.
### Keywords
EDI Customer Profiles, Validate Credit Limit, posting rejection

## EDI post-then-hold alternative
**Guide pages:** 97-99.

1. **Can an over-limit EDI order post and then be held?** Yes. The guide gives that as an alternative when automatic order holding is configured instead of blocking posting through EDI validation.
2. **Which parameter supports post-then-hold processing?** Limit Exceeded Credit Hold Reason on Accounts Receivable Parameters.
3. **What if EDI validation and the A/R automatic-hold reason are both absent?** The guide says the over-limit EDI order posts without being held by those two settings.
4. **Are all EDI over-limit cases handled by one rule?** No. Posting prevention, post-then-hold, and posting without those controls are distinct configurations.
5. **What should a support agent compare after an EDI credit incident?** Compare Validate Credit Limit, the A/R hold reason, whether the order posted, and its actual Credit Hold field.

**Section Summary:** EDI credit behavior is a configuration choice, not a universal rejection rule.
### Keywords
EDI order, post then hold, automatic credit hold

## Replicated credit limits
**Guide pages:** 97-98.

1. **What happens to a replicated customer's credit limit across participating sites?** The guide says a credit limit update is replicated to all sites configured for that replication.
2. **Does the guide say every installation automatically replicates credit limits?** No. Its multi-site behavior applies to sites configured to replicate the relevant credit information.
3. **Why might the same customer limit appear at several sites?** In the documented multi-site arrangement, the limit is shared by replication.
4. **Should a chatbot assume a single-site customer's limit is shared everywhere?** No. Confirm the site's replication configuration and customer setup.
5. **What should be verified when sites display inconsistent limits?** Check the relevant multi-site replication setup and the current customer records; the general guide alone cannot diagnose synchronization.

**Section Summary:** Shared limits require the documented replication arrangement.
### Keywords
multi-site, replicated credit limit, customer master

## Multi-site On Order Balance
**Guide pages:** 97-98.

1. **How is On Order Balance treated in the guide's multi-site example?** It is cumulative across the participating sites for the customer credit comparison.
2. **What is the guide's example credit limit?** The illustrative limit is 100 currency units, with orders from two sites contributing to exposure.
3. **What happens in the example when a 35-unit order follows 50 and 25 units of exposure?** The combined 110 exceeds the 100 limit, so the new line is saved Planned in that example.
4. **Why can a site-local order seem below the limit yet trigger a warning?** Exposure from another participating site contributes to the cumulative On Order Balance.
5. **Should the example's numbers be treated as a customer's live balance?** No. They are illustrative figures from the guide, not current business data.

**Section Summary:** Participating sites contribute to a cumulative credit comparison.
### Keywords
On Order Balance, multi-site credit, cumulative exposure

## Originating-site hold control
**Guide pages:** 98.

1. **Which site controls the order's credit hold status in the documented multi-site flow?** The originating site controls the credit hold status for shipping sites.
2. **Can a shipping site independently decide that the originating order is not held?** Do not assume so; the guide ties the hold state to the originating site.
3. **Why does the originating site matter when researching a hold?** A shipping site may show a warning or shipping effect while the actual order hold decision belongs to the origin.
4. **What site context should a support agent capture?** Record the order's originating site and the site from which shipping is attempted.
5. **Does a warning at another site always mean that site set the hold?** No. The documented origin-site control makes warning and hold placement different events.

**Section Summary:** In the guide's multi-site case, origin-site ownership determines where hold state is set.
### Keywords
originating site, shipping site, multi-site hold

## Utility across sites
**Guide pages:** 98.

1. **Does Order Credit Hold Change Utility run across sites in the guide's multi-site description?** Yes. The guide says it runs for all sites.
2. **What happens if a shipping site is also the originating site during utility processing?** That site can place the order on hold under the documented conditions.
3. **What happens at a non-originating shipping site in that utility case?** The guide describes a warning there, but not a hold set by that non-originating site.
4. **Why might a utility warning not correspond to a local order hold?** The site issuing the warning may not own the order's origin-site hold state.
5. **What should be checked before interpreting a multi-site utility result?** Verify the order origin, shipping site, utility selection, and current order Credit Hold state.

**Section Summary:** Utility processing spans sites, but an order hold remains origin-controlled.
### Keywords
Order Credit Hold Change Utility, all sites, warning, origin

## Manually placing a customer hold
**Guide pages:** 99-100.

1. **What is the first screen in the documented customer-hold procedure?** Open the customer in the Customers form.
2. **Which tab is used to place that hold?** Use the Credit tab.
3. **Which two fields are set for a manual customer hold?** Select Credit Hold and choose Credit Hold Reason.
4. **What completes the customer-hold procedure?** Save the Customers record after selecting the hold and reason.
5. **Should a chatbot apply a customer hold merely because the user asks?** No. The operation requires an authorized SyteLine user and current permission checks; this article only describes the documented form procedure.

**Section Summary:** The customer hold procedure is Customers > Credit > hold and reason > save.
### Keywords
manual customer hold, Credit tab, Credit Hold Reason

## Manually placing an order hold
**Guide pages:** 99.

1. **What is the first screen in the documented order-hold procedure?** Open the relevant order in Customer Orders.
2. **Which tab is used for a manual order hold?** Use the Amounts tab.
3. **Which order fields are set?** Select Credit Hold and choose a Credit Hold Reason.
4. **What final action records the manual order hold?** Save the Customer Orders record.
5. **Does manually holding one order necessarily hold the whole customer?** No. The documented order and customer hold controls are separate.

**Section Summary:** The order hold procedure is Customer Orders > Amounts > hold and reason > save.
### Keywords
manual order hold, Amounts tab, credit reason

## Releasing a customer hold
**Guide pages:** 100.

1. **Where is a manually applied customer credit hold removed?** On the Customers form's Credit tab.
2. **Which field is cleared to release the customer hold?** Clear Credit Hold on Customers.
3. **What action completes release of a customer hold?** Save the changed customer record.
4. **Does clearing a customer hold automatically prove every order is released?** No. Separate order Credit Hold fields may still be selected.
5. **What should be checked after releasing a customer?** Reinspect both the customer Credit Hold state and any relevant orders' individual Credit Hold states.

**Section Summary:** Clear and save the customer hold, then distinguish any remaining order holds.
### Keywords
release customer hold, clear Credit Hold, Customers Credit

## Releasing an order hold
**Guide pages:** 100.

1. **Where is a single order's credit hold removed?** On Customer Orders, Amounts tab.
2. **Which field is cleared when releasing that order?** Clear the order Credit Hold field.
3. **What completes the manual order release?** Save the Customer Orders record.
4. **Does releasing one order remove a customer-level hold?** No. The customer-level Credit Hold must be inspected separately.
5. **Why might shipping remain blocked after an order hold is cleared?** The customer may remain on Credit Hold or another current restriction may apply; check live SyteLine state.

**Section Summary:** Clear the specific order hold; do not assume customer-level restrictions have changed.
### Keywords
release order hold, Customer Orders Amounts, shipping blocked

## Credit-field authorization
**Guide pages:** 100.

1. **Which groups does the guide name for updating customer credit fields?** It names Order Entry and Credit Field Update groups for the user's authorization, with a Super User exception.
2. **Is Order Entry membership alone the complete documented rule?** No. The guide also names Credit Field Update unless the user is a Super User.
3. **What exception does the guide mention to the two-group requirement?** A Super User can be an exception.
4. **Does this article grant a chatbot permission to change limits or holds?** No. Actual access must be enforced through the live SyteLine security context.
5. **What should an agent do when a user cannot edit a credit field?** Verify the current user's effective permissions and the relevant groups with an administrator; do not infer authorization from the article.

**Section Summary:** Credit changes are permission-sensitive and require effective current authorization.
### Keywords
Order Entry group, Credit Field Update group, Super User, authorization

## Utility scope and aging inputs
**Guide pages:** 96, 100-101.

1. **What does Order Credit Hold Change Utility process?** It applies hold or release processing to selected orders, using customer and order ranges and aging-related inputs.
2. **Which customer selection does the utility allow?** A customer-number range can be entered.
3. **Which order selection does the utility allow?** An order-number range can be entered.
4. **Which customer credit-aging fields does the guide mention?** Days Over Invoice Date, Days Over Due Date, and Aged Posted Balance Limit.
5. **Why must utility input ranges be checked before processing?** They determine which orders are evaluated or changed; the guide's general procedure does not identify the business-approved range for a particular run.

**Section Summary:** The utility's action and selected ranges need explicit review before processing.
### Keywords
credit hold utility, customer range, order range, aged balance

## Utility Hold selection
**Guide pages:** 100-101.

1. **Which utility choice applies holds?** Select Hold in Order Credit Hold Change Utility.
2. **What ranges can limit a Hold run?** The utility accepts customer-number and order-number ranges.
3. **Which aging thresholds are relevant to the utility's hold evaluation?** The guide discusses Days Over Invoice Date or Due Date and Aged Posted Balance Limit on Customers.
4. **What starts the utility's selected action?** After reviewing selections and conditions, use Process.
5. **Should an assistant run Hold from a general question alone?** No. The utility changes order state and requires an authorized user, explicit scope, and current business approval.

**Section Summary:** Hold is a bulk-changing utility action with range and aging consequences.
### Keywords
utility Hold, Process, aging threshold, order range

## Utility Release selection
**Guide pages:** 100-101.

1. **Which utility choice releases selected orders?** Select Release in Order Credit Hold Change Utility.
2. **What Aging Basis choices are documented for Release?** Invoice Date or Due Date.
3. **Which additional Release inputs are named?** The guide names Reason and Aging Date.
4. **What action executes a configured Release run?** Use Process after selecting the Release parameters and intended ranges.
5. **Does utility Release necessarily remove a customer-level hold?** Do not assume that. The utility acts on orders; inspect the separate Customers Credit Hold field.

**Section Summary:** Release has its own Aging Basis, Reason, and Aging Date inputs.
### Keywords
utility Release, Aging Basis, Invoice Date, Due Date, Aging Date

## Blank customer aging thresholds
**Guide pages:** 100-101.

1. **What does the guide say about blank customer aging thresholds during utility processing?** If Days Over Invoice Date or Due Date and Aged Posted Balance Limit are blank on Customers, the selected orders are held.
2. **Why must blank thresholds not be treated as harmless?** In the documented utility case they can cause all selected orders to be held.
3. **Where are those aging settings maintained?** On the Customers record, according to the utility description.
4. **What should an operator review before running Hold over a broad range?** Check customer aging thresholds and selected customer and order ranges.
5. **How should the chatbot describe an unexpectedly broad hold result?** Note the guide's blank-threshold behavior as a possible explanation, then ask an authorized user to verify actual utility inputs and current records.

**Section Summary:** Blank aging fields can materially widen the utility's hold outcome.
### Keywords
blank aging threshold, all selected orders, Hold utility

## Shipping consequence and hold level
**Guide pages:** 96-97.

1. **Which hold level does the guide explicitly say prevents customer shipments?** A customer-level Credit Hold on Customers.
2. **Can an individual order hold also be relevant to order progression?** Yes. The guide separately identifies order Credit Hold and restrictions such as new cross-references on a held order.
3. **Why should a shipping answer identify the hold level?** The customer may be held without each order checkbox selected, so the remedy and explanation differ.
4. **Is a credit warning alone proof that shipment is blocked?** No. The warning may occur with a Planned line or with an unheld order when automatic holding is not configured.
5. **What live information is needed before stating an order can ship?** Current customer and order hold state, line status, originating site, and effective SyteLine permissions and shipping checks.

**Section Summary:** Explain the actual hold level and current state rather than equating every warning with a shipping block.
### Keywords
shipments, held customer, held order, warning

## Order-entry warning interpretation
**Guide pages:** 33, 97.

1. **Can a credit warning appear while a line stays Ordered?** Yes, for a new over-limit line with Allow Over Credit Limit selected.
2. **Can a credit warning appear while a line becomes Planned?** Yes, for a new over-limit line with the option cleared.
3. **Can a warning arise from changing an existing line?** Yes. The guide documents a warning and possible automatic order hold for an existing-line change.
4. **What must be known before explaining a warning's outcome?** Whether the line is new or existing, the Allow Over Credit Limit choice for a new line, the configured reason, and resulting status.
5. **Why is the wording 'credit warning equals hold' inaccurate?** The guide describes warning paths that save a line as Planned without putting the order on hold.

**Section Summary:** Credit warnings are signals; their state transitions depend on entry path and configuration.
### Keywords
credit warning, Ordered, Planned, existing line

## Credit diagnostic decision path
**Guide pages:** 96-101.

1. **What should be checked first for a reported credit hold?** Identify whether the current hold is on Customers, Customer Orders, or both.
2. **What should be checked second when the issue started on line save?** Determine whether the line was new or edited and inspect its status and Allow Over Credit Limit choice if new.
3. **What configuration explains an automatic over-limit order hold?** Check Limit Exceeded Credit Hold Reason in Accounts Receivable Parameters and, for the documented new-line path, the Reason field on the customer's Credit tab.
4. **What should be checked when an EDI order did not post?** Inspect EDI Customer Profiles Validate Credit Limit and the actual EDI processing result.
5. **What should be checked when different sites disagree about a hold?** Identify the originating site, participating replication setup, cumulative exposure, and current order state.

**Section Summary:** Diagnose by level, entry path, setting, channel, and site rather than guessing from one symptom.
### Keywords
credit troubleshooting, line status, EDI, multi-site

## Guide and live-data boundary
**Guide pages:** 96-101.

1. **Can this article tell a user their current credit limit?** No. It explains guide behavior; a current customer limit requires authorized live SyteLine data.
2. **Can this article tell whether a specific order is presently held?** No. The order and customer records must be inspected in the current site and session.
3. **Can this article decide whether a user may release a hold?** No. Effective permissions and organizational approval must be checked at execution time.
4. **Can this article guarantee that every SyteLine site has identical credit configuration?** No. The guide presents general 9.01.x behavior, while local configuration and later releases may differ.
5. **What should a chatbot say when asked for a live credit decision without data access?** Explain the documented screen and rule, state that the live status is unverified, and direct the user to the authorized SyteLine record or team.

**Section Summary:** Knowledge-base guidance never substitutes for live balances, current holds, and permission enforcement.
### Keywords
live credit data, permission, configuration, source boundary
