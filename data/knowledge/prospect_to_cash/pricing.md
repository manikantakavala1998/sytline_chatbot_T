# Pricing and Discount Module

This Customer-to-Cash article uses only the *Infor SyteLine Customer Service User Guide*, release 9.01.x (2020). References below are printed guide pages. The installed release, site configuration, and permissions require local verification. This article does not contain live customer prices or external links.

## Document Metadata
- **Document Title:** Pricing and discounts form guide
- **Document Type:** Process and form reference
- **Module:** pricing
- **SyteLine Forms:** Customer Order Lines, Customer Contracts, Customer Contract Prices, Discounts, Price Promotions and Rebates, Earned Rebates, Item Content References, Price Adjustment Invoice
- **Process Stage:** Customer order pricing through post-invoice price adjustment
- **Tags:** pricing, Unit Price, contract, quantity break, discount, promotion, rebate, surcharge, price adjustment
- **Access Level (SyteLine groups):** Effective permissions in the deployed SyteLine site
- **Site Scope:** General guidance; verify customer, item, site, and currency
- **SyteLine Version:** Source manual release 9.01.x; later-release behavior is unverified
- **Document Owner:** Customer-to-Cash process owner
- **Reviewed / Approved By:** Pending local SyteLine business and security review
- **Last Reviewed:** Not yet locally reviewed
- **Version:** 0.2 draft
- **Source:** Infor SyteLine Customer Service User Guide, release 9.01.x (2020), printed pages 35, 37-38, 50-52, 66-68, and 101-108. No external links in this retrieval article.

## Pricing form map

**Guide pages:** 35, 50, 66-68, 101-107.

1. **Where is Unit Price determined during order entry?** The guide covers price determination on Customer Orders, EDI Customer Orders, Customer Order Lines, and Estimate Lines.
2. **Which form links a customer to an item for pricing?** Customer Contracts stores the customer-item relationship.
3. **Which form holds a guaranteed customer-item price?** Customer Contract Prices stores the effective-dated contract price and quantity breaks.
4. **Which form sets a customer-type/product-code discount?** Discounts stores Customer Type, Product Code, Discount Percent, and Description.
5. **Which form starts a post-invoice price correction?** Price Adjustment Invoice selects a previously invoiced order line for an eligible adjustment.

**Section Summary:** Identify the screen that owns the price rule or transaction before explaining a line amount.

### Keywords
Pricing, Customer Contracts, Customer Contract Prices, Discounts, Price Adjustment Invoice

## Unit Price decision sequence

**Guide pages:** 35.

1. **Does the guide specify one price list for every order?** No. It gives a sequence involving promotions, contracts, breaks, matrix pricing, and item pricing.
2. **What is tested first in that sequence?** SyteLine checks whether a promotion pricing code was specified for the selected line.
3. **Does the promotion skip the base-price search?** No. The base unit price is determined before the promotional value produces a net unit price.
4. **Which relationship is checked after the promotion test?** SyteLine searches for an applicable Customer Contracts record.
5. **What if no applicable Item Pricing record exists?** SyteLine displays a missing-price message and requires manual price entry.

**Section Summary:** Follow the documented order of decisions rather than assuming a single price source.

### Keywords
Unit Price, price sequence, promotion, contract, manual price

## Promotion in base-price calculation

**Guide pages:** 35, 106.

1. **When is a Promotion Code considered?** The price calculation first tests for a code on the selected customer line.
2. **When is the promotion value applied?** It is applied after the underlying unit price is established.
3. **Which line field receives the adjusted price?** Unit Price is replaced by the promotion-adjusted item price.
4. **What happens to an existing Sales Discount?** Applying the promotion overrides it and sets Sales Discount to zero.
5. **Can a separate Sales Discount remain with a line promotion?** No. The guide excludes a sales discount when that line has a promotion.

**Section Summary:** Promotion changes the line's price after base pricing and clears Sales Discount.

### Keywords
Promotion Code, Unit Price, Sales Discount, net price

## Customer contract matching order

**Guide pages:** 35, 102.

1. **Which Customer Contracts key is searched first?** The customer, item, and customer-item combination is searched first.
2. **What key is searched when that full combination is absent?** SyteLine tries the same customer and item with a blank customer-item value.
3. **Is a contract relationship alone sufficient to set price?** No. An eligible effective-dated pricing record is also checked.
4. **What does a valid nonzero contract price do?** It supplies the default Unit Price under the guide's sequence.
5. **What does a zero contract price do?** It sends pricing to the quantity-break step rather than finalizing a zero price.

**Section Summary:** Match the contract key and then its valid price record.

### Keywords
Customer Contracts, Cust Item, contract match, price record

## Contract effective-date wording

**Guide pages:** 35, 102-103.

1. **Which date does the main Unit Price section use for contract eligibility?** It compares order due date with the contract-price effective date.
2. **Which date does the Customer Contracts chapter use?** That chapter compares customer order date with effective date.
3. **Does this article resolve the guide's date-label difference?** No. The installed release must be checked before relying on one interpretation.
4. **Where is a contract price's Effective Date entered?** It is entered on Customer Contract Prices.
5. **What should be checked for a date-sensitive price question?** Compare the actual saved order and line dates with the contract price's Effective Date in the installed system.

**Section Summary:** The guide uses both due-date and order-date wording; verify behavior locally.

### Keywords
effective date, due date, order date, contract eligibility

## Guaranteed Contract Price

**Guide pages:** 102-103.

1. **Where is the guaranteed customer-item amount entered?** Enter it in Contract Price on Customer Contract Prices.
2. **What does an eligible nonzero Contract Price override?** The guide says it overrides other pricing formulas.
3. **Does zero Contract Price mean free goods in this procedure?** No. The selection sequence continues to quantity-break pricing.
4. **Which identifiers belong on the contract-price record?** Customer, Item, and Customer Item where applicable identify the price entry.
5. **Can the price screen be opened from Customer Contracts?** Yes. Select customer and item and choose Pricing.

**Section Summary:** A valid guaranteed price overrides formulas; a zero value follows the break path.

### Keywords
Contract Price, guaranteed price, Customer Contract Prices

## Customer contract quantity breaks

**Guide pages:** 35, 102-103.

1. **When are customer-item quantity breaks used?** Valid breaks from Customer Contract Prices can supply Unit Price when a fixed contract price does not.
2. **Where is each break quantity specified?** Enter it on Customer Contract Prices.
3. **Which base-code choices does the guide list?** Unit price, cost, or none may be selected.
4. **Can a break use amount or percent?** Yes. The setup chooses amount or percentage and a positive or negative value.
5. **Which U/M basis applies to the break value?** It uses the item's base U/M, not the customer's U/M.

**Section Summary:** Evaluate threshold, base code, amount or percent, and base U/M together.

### Keywords
contract break, quantity threshold, base code, U/M

## Price Matrix matching

**Guide pages:** 35.

1. **Which codes are required for matrix pricing?** Both a customer price code and an item price code are required.
2. **What if either code is missing?** The sequence advances to Item Pricing.
3. **Which table is searched when both codes exist?** The Price Matrix Table is searched for their combination.
4. **What can a matching matrix row provide?** Its Price Formula can calculate the item's Unit Price.
5. **What wins if the matrix cross-check finds valid breaks?** Valid quantity breaks calculate Unit Price; otherwise the Price Formula does.

**Section Summary:** Matrix pricing needs both price codes, a matching row, and a break-price check.

### Keywords
Price Matrix Table, customer price code, item price code, Price Formula

## Item Pricing fallback

**Guide pages:** 35.

1. **When does the sequence search Item Pricing?** It does so after earlier pricing paths do not supply an applicable price.
2. **Which criteria select a current Item Pricing record?** The item's price effective date and customer's currency are considered.
3. **Can item-level quantity breaks provide a default?** Yes, when they exist and apply.
4. **Which field supplies the final listed item default?** Unit Price 1 on Item Pricing supplies it when no other item price applies.
5. **What if there is no Item Pricing record?** The guide requires manual price entry after a message.

**Section Summary:** Check applicable item breaks and Unit Price 1 before concluding that manual entry is needed.

### Keywords
Item Pricing, Unit Price 1, item break, effective date

## Customer currency pricing

**Guide pages:** 35.

1. **Which currency is searched first for Price Formulas?** The customer's currency is searched first.
2. **Which currency is searched first for Item Pricing?** The customer's currency is searched first.
3. **What if customer-currency records are absent?** The system searches domestic-currency records and converts the result.
4. **Can the domestic-currency number be reported unchanged as customer price?** No. The documented fallback includes conversion to the customer's currency.
5. **What should be examined for a cross-currency price difference?** Check which currency record supplied the formula or item price and whether conversion occurred.

**Section Summary:** Customer-currency lookup precedes domestic-currency fallback and conversion.

### Keywords
multi-currency, domestic currency, customer currency, conversion

## Non-inventory price entry

**Guide pages:** 35.

1. **How is a non-inventory item's Unit Price entered?** The guide requires manual Unit Price entry.
2. **Where is the resulting selling price held?** The applicable customer order or estimate line holds its Unit Price.
3. **Is a missing Item Pricing message always a system fault?** No. The guide explicitly permits manual entry if no price record exists.
4. **Can this article state a particular non-inventory customer's price?** No. The actual transaction line must be read for that value.
5. **What should be verified on a non-inventory line?** Verify that its required Unit Price was entered on the line.

**Section Summary:** Non-inventory selling prices are entered manually in this guide.

### Keywords
non-inventory, manual Unit Price, missing price

## Discounts form setup

**Guide pages:** 50.

1. **Which combination identifies a documented Discounts rule?** Customer Type and Product Code identify the rule.
2. **How is a Discounts record started?** Select Actions > New on the Discounts form.
3. **Which values are entered?** Enter Customer Type, Product Code, Discount Percent, and a short Description.
4. **Which transactions use these discounts?** The guide names regular orders and estimates.
5. **When are product-code/customer-type discounts applied?** They are applied after the item's base price has been determined.

**Section Summary:** The Discounts rule matches customer type and product code after base pricing.

### Keywords
Discounts, Customer Type, Product Code, Discount Percent

## Sales Disc line override

**Guide pages:** 35, 50, 106.

1. **Can the configured discount be changed on one line?** Yes. The guide allows an override through that line's Sales Disc field.
2. **Does a Sales Disc line edit rewrite the Discounts setup record?** The described override is on the individual line, not the rule record.
3. **Can Sales Disc remain after applying a promotion?** No. A line promotion resets Sales Discount to zero.
4. **What explains an unexpected zero Sales Discount?** Check whether a Promotion Code was applied to the line.
5. **Why examine base price and discount separately?** The guide establishes item price before applying configured discounts or premiums.

**Section Summary:** Sales Disc can override a line rule, but promotion pricing clears it.

### Keywords
Sales Disc, line override, premium, Promotion Code

## Customer Contracts creation

**Guide pages:** 101-102.

1. **How is a Customer Contracts record started?** Open Customer Contracts and select Actions > New.
2. **Which primary identifiers are selected?** Select Customer and a valid Item.
3. **Which optional fields refine the relationship?** The guide lists U/M, Std Due Period, Cust Item, End User, and Rank.
4. **What do End User and Rank support?** They support different end-user price structures in contract manufacturing.
5. **How is the new relationship completed?** Save the Customer Contracts record.

**Section Summary:** Establish the customer-item relationship before detailed pricing.

### Keywords
Customer Contracts, Cust Item, End User, Rank

## Customer Contract Prices entry

**Guide pages:** 102-103.

1. **How can Customer Contract Prices be opened from a contract?** Select customer and item on Customer Contracts and choose Pricing.
2. **Which identifiers are entered for a new contract price?** Select Customer, Item, and Customer Item where applicable.
3. **Which date is entered on the pricing record?** Enter Effective Date.
4. **Where is the guaranteed customer amount entered?** Enter Contract Price.
5. **Which action calculates a configured break Unit Price?** Choose Unit Price after entering break parameters.

**Section Summary:** Customer Contract Prices owns effective-dated price and break details.

### Keywords
Customer Contract Prices, Effective Date, Contract Price, Unit Price action

## Contract manufacturing end users

**Guide pages:** 101, 103-104.

1. **Why may one customer-item pair need several prices?** A contract manufacturer may buy for ultimate end users with different negotiated prices.
2. **What identifies an end-user-specific arrangement?** A unique customer-item number can distinguish that customer-item-end-user combination.
3. **Which fields capture the ultimate end user and priority?** End User identifies the end user; Rank records priority.
4. **Which form stores its end-user-specific price?** Customer Contract Prices stores pricing for that arrangement.
5. **Where can the unique customer-item number be used?** The guide names customer orders, estimates, and RMAs for that end user.

**Section Summary:** Contract manufacturing can require distinct customer-item/end-user pricing records.

### Keywords
contract manufacturing, ultimate end user, Rank, customer item

## Price Promotions and Rebates setup

**Guide pages:** 104-105.

1. **Which form defines promotion and rebate programs?** Price Promotions and Rebates defines the programs.
2. **Which dimensions can restrict a program?** The guide names salesperson, customer, item, and product code among possible limits.
3. **Which immediate price changes can a promotion offer?** It can use a discount percent, discount amount, or new fixed price.
4. **Can a promotion offer a free item?** Yes. The guide describes free items as a promotion possibility.
5. **Which optional promotion limits are mentioned?** Minimum net price, minimum order quantity, maximum discount, and maximum discounted quantity are listed.

**Section Summary:** Program setup controls eligible customers/items and the kind and size of the benefit.

### Keywords
Price Promotions and Rebates, fixed price, free item, minimum net price

## Promotion eligibility on an order line

**Guide pages:** 104, 106.

1. **Where may a promotion be applied during entry?** Customer Order Lines and Customer Orders Quick Entry are the documented screens.
2. **Where is the eligible code selected?** Select it in the line's Promotion Code field.
3. **Why may a code be absent from the selection list?** The program's setup criteria may not match that line.
4. **How do dates affect code eligibility?** An order date outside the promotion's effective-to-expiration period excludes it.
5. **How does an item restriction affect code eligibility?** An item-specific promotion is absent if that item is not ordered.

**Section Summary:** Promotion Code choices depend on the configured eligibility criteria.

### Keywords
Promotion Code, eligibility, effective date, expiration date, item restriction

## Promotion application on Customer Order Lines

**Guide pages:** 106.

1. **What must be selected before applying a promotion?** Select the intended order and line on Customer Order Lines or Customer Orders Quick Entry.
2. **Which action applies the promotion?** Choose an eligible Promotion Code for that line.
3. **Which price field changes after selection?** Unit Price is replaced with the adjusted item price.
4. **What happens to the line's old Sales Discount?** It is overridden and set to zero.
5. **Is the code applied to an entire order header?** No. The documented procedure applies it to a selected line.

**Section Summary:** Recheck Unit Price and Sales Discount after a line promotion.

### Keywords
Customer Order Lines, Quick Entry, Promotion Code, Unit Price, Sales Discount

## Promotion exclusions and copying

**Guide pages:** 38, 106.

1. **Can promotion pricing apply to Estimate Lines?** No. The guide excludes estimates.
2. **Can a customer order blanket line receive a promotion?** No. Blanket lines are excluded.
3. **Can a configurable item use promotion pricing?** No. Configurable items are excluded.
4. **Does Copy Orders and Estimates copy Promotion Code to a new order?** No. The guide expressly excludes that field.
5. **Can a promotion be defined for a price adjustment invoice?** No. Price adjustment invoices and progressive billing are excluded.

**Section Summary:** Promotion pricing has explicit form, item, and copy-process limits.

### Keywords
promotion exclusion, estimate, blanket line, configurable item, copy

## Rebate program prerequisites

**Guide pages:** 104-105.

1. **What benefit does a rebate program provide?** It provides future payment credits rather than an immediate Unit Price change.
2. **Which account is needed before program creation?** Set a deferred revenue account on Accounts Receivable Parameters.
3. **What accompanies that account?** The guide also requires related unit codes.
4. **Which valuation inputs belong to the rebate program?** Fair value and estimated redemption rate are specified.
5. **Which time or threshold controls can be set?** Define the credit-use period and optional amount or quantity thresholds.

**Section Summary:** Rebate setup requires A/R accounting and program valuation.

### Keywords
rebate, deferred revenue, fair value, redemption rate, credit-use period

## Rebates at invoice generation

**Guide pages:** 105.

1. **When are rebate programs evaluated?** SyteLine reviews defined rebate programs during invoice generation.
2. **Which order record must qualify?** An existing customer order line must meet the rebate criteria.
3. **What invoice accounting can eligibility create?** It creates deferred revenue invoice distributions for eligible rebate codes.
4. **Which rebate work records are added?** Earned Rebates and Earned Rebate Credit Workbench receive entries.
5. **What is the new earned rebate's status?** The guide calls it Pending.

**Section Summary:** Qualifying invoices generate rebate accounting and Pending earned-rebate records.

### Keywords
invoice generation, deferred revenue, Earned Rebates, Pending

## Earned rebate valuation

**Guide pages:** 105.

1. **Which input determines a potential earned credit?** Rebate fair value determines the amount described by the guide.
2. **Which inputs determine deferred revenue?** Invoiced line amount, rebate fair value, and redemption rate are used.
3. **What is the guide's deferred-revenue example?** A $250 line at 30% fair value and 80% redemption yields $60 deferred revenue.
4. **Does that $60 equal the example's earned customer credit?** No. The same example describes a $75 earned credit.
5. **Where should a real customer's rebate amount be checked?** Read the actual Earned Rebates entry; the guide example is not live data.

**Section Summary:** Earned credit and deferred revenue differ because the redemption estimate affects accounting.

### Keywords
rebate fair value, deferred revenue, redemption rate, earned credit

## Earned Rebates inquiry and hold

**Guide pages:** 106-107.

1. **Which form supports a customer rebate inquiry?** Use Earned Rebates and filter its fields.
2. **Which status may be put on hold?** Pending earned rebates can be put on hold.
3. **What does a rebate hold prevent?** It prevents processing on Earned Rebate Credit Workbench.
4. **Can a held rebate be returned to processing?** Yes. Clear its hold in Earned Rebates to restore Pending status.
5. **Which form expires unused earned rebates?** Earned Rebates is used to find and process them.

**Section Summary:** Earned Rebates is the inquiry, hold, release, and expiry screen.

### Keywords
Earned Rebates, Pending, Hold, expire

## Earned Rebate Credit Workbench

**Guide pages:** 107.

1. **Which form turns qualified rebates into credit memos?** Earned Rebate Credit Workbench performs that processing.
2. **Which field identifies the rebate program there?** Specify its Promotion Code.
3. **Can the workbench be limited to one customer?** Yes. Customer is an optional filter.
4. **Which date is entered for new open credit memos?** Enter Application Date.
5. **Which Pending-tab entries are selectable?** Only entries marked Qualified may be selected.

**Section Summary:** Process qualified Pending rebates with the desired program, customer, and application date.

### Keywords
Earned Rebate Credit Workbench, Promotion Code, Application Date, Qualified

## Rebate application and expiry

**Guide pages:** 105, 107-108.

1. **What does rebate workbench processing create?** It creates open credit memos and marks the processed rebates Applied.
2. **How can those credits be used?** They can be combined with payments or other credits against open A/R invoices.
3. **How are expired unused rebates found?** Filter Earned Rebates for Pending status and a passed Expiration Date.
4. **What does expiring a rebate do?** It transfers unused value from deferred to current revenue through an A/R distribution journal entry.
5. **What if estimated redemption differs from actual redemption at closing?** The guide requires a manual adjustment to settle the difference.

**Section Summary:** Applied credits and expired unused rebates follow different accounting paths.

### Keywords
rebate Applied, open credit memo, Expired, AR Dist, redemption adjustment

## Surcharge purpose and formula

**Guide pages:** 51.

1. **Why does the guide use item surcharges?** They reflect changing commodity prices for content within an item.
2. **What does Base Price represent in this calculation?** It represents estimated commodity cost already built into the item cost.
3. **What is the documented per-unit formula?** Unit surcharge equals (Actual Price minus Base Price) times Content Factor times Surcharge Factor.
4. **Which transaction types can carry surcharges?** The guide lists purchase orders, vouchers, customer orders, and invoices.
5. **Which customer-facing reports show surcharge information?** Order Verification Report and Order Invoicing/Credit Memo are among those listed.

**Section Summary:** Commodity movement contributes a separate per-unit surcharge.

### Keywords
surcharge, Base Price, Actual Price, Content Factor, Surcharge Factor

## Surcharge accounts and tax setup

**Guide pages:** 51.

1. **Which accounts are created before using surcharges?** Create Surcharge and, if needed, Surcharge in Process accounts on Chart of Accounts.
2. **Where is the surcharge factor set?** Accounts Payable Parameters and Accounts Receivable Parameters offer a default of 1.00 or a new value.
3. **Where are surcharge accounts assigned?** The guide names A/P Parameters, A/R Parameters, Distribution Accounts, and End User Types.
4. **Which form labels the surcharge tax code?** Tax Systems holds its label and description.
5. **Which field decides whether tax basis includes a surcharge?** Include Surcharge on Tax Codes controls that inclusion.

**Section Summary:** Accounting and tax setup precede a surcharge calculation.

### Keywords
Chart of Accounts, Surcharge in Process, A/R Parameters, Include Surcharge

## Item content and exchange setup

**Guide pages:** 51-52.

1. **Which form defines commodities for surcharges?** Item Contents holds the commodity records.
2. **Which form identifies commodity exchange services?** Item Content Exchanges stores exchange services.
3. **Which form tracks changing commodity prices?** Item Content Prices stores prices by content and exchange.
4. **Which Items field marks an item with commodity content?** Includes Item Content on the Sales tab marks it.
5. **Which action opens item-level references?** Item Content on Items opens Item Content References.

**Section Summary:** Commodity, exchange, price, and item-content records supply surcharge inputs.

### Keywords
Item Contents, Item Content Exchanges, Item Content Prices, Includes Item Content

## Surcharge references and customer rules

**Guide pages:** 52.

1. **What values define an item-content reference?** Effective Date, Base Price, and Content Factor are specified for each content.
2. **Can a customer or order-line reference supersede the general item reference?** Yes. More specific customer, contract, or order-line references take precedence.
3. **Which form defines customer/exchange rules?** Customer Surcharge Rules holds those combinations.
4. **Which rule fields are identified?** Price method, applicable offset intervals, and start/end date-times are defined.
5. **Which form is the vendor-side counterpart?** Vendor Surcharge Rules holds vendor/exchange combinations.

**Section Summary:** Specific content references can override item defaults; customer rules select price timing.

### Keywords
Item Content References, Customer Surcharge Rules, price method, offset interval

## Copy Orders and Estimates pricing handoff

**Guide pages:** 37-38.

1. **Which form copies an estimate into an order?** Copy Orders and Estimates performs the copy.
2. **Can the user copy a selected range of lines?** Yes. Starting and Ending Line Number define that range.
3. **Are calculated sales taxes copied unchanged?** No. Values such as sales tax are recalculated for copied lines.
4. **Are order-level discounts copied?** Yes. The guide says those discounts are copied with orders and estimates.
5. **Is Promotion Code copied to a new order?** No. The guide excludes it from the copy.

**Section Summary:** A copy can retain discounts while recalculating tax and omitting promotion codes.

### Keywords
Copy Orders and Estimates, line range, sales tax, order discount, Promotion Code

## Price Adjustment Invoice eligibility

**Guide pages:** 66-67.

1. **What does a price adjustment invoice correct?** It reflects a change to discount or Unit Price on a previously invoiced line.
2. **Can an unshipped or uninvoiced line use this procedure?** No. The guide excludes those lines.
3. **Can a line with an uncredited return be adjusted?** No. Generate the return's credit memo before a price change.
4. **Which adjusted lines print on the adjustment invoice?** Only lines with a nonzero Net Adjust amount appear.
5. **Can an adjustment invoice have no adjusted line?** Yes, if Misc Charges or Freight are adjusted.

**Section Summary:** Eligibility depends on invoice/shipment status and completion of any return credit.

### Keywords
Price Adjustment Invoice, Unit Price, return, Net Adjust

## Price Adjustment Invoice steps and evidence

**Guide pages:** 67-68.

1. **How is the target order found on Price Adjustment Invoice?** Filter by order, customer, or other header criteria and select its displayed line.
2. **Which amounts can be changed on the form header?** Freight and Misc Charges can be adjusted there.
3. **Which line values can be adjusted on its tabs?** The guide allows quantity, discount amount, and price adjustments.
4. **Which net values update after an edited field is left?** Old Net, New Net, and Net Adjust recalculate.
5. **Which action opens the print/post screen?** Print/Post Invoice opens Print Price Adjustment Invoice for formatting, printing, and posting.

**Section Summary:** Select the invoiced line, review recalculated net values, and print/post the adjustment.

### Keywords
Price Adjustment Invoice, Freight, Misc Charges, Old Net, New Net, Print/Post Invoice
