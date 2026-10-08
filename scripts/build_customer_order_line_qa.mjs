// Expand only Customer Order Lines Q&A from the five grounded facts in each article section.
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const articlePath = path.join(root, "data/knowledge/prospect_to_cash/customer_order_line.md");
const workbookPath = path.join(root, "data/qa/prospect_to_cash/customer_order_line.xlsx");
const previewPath = path.join(root, "tmp/pdfs");
await fs.mkdir(previewPath, {recursive:true});
const source = await fs.readFile(articlePath, "utf8");
const sections = new Map();
for (const block of source.split(/^## /m).slice(1)) {
  const index = block.indexOf("\n");
  const heading = block.slice(0, index).trim();
  if (heading === "Document Metadata") continue;
  const facts = block.slice(index + 1).split("**Section Summary:**")[0]
    .split("\n").filter(line => /^\d+\. /.test(line))
    .map(line => line.replace(/^\d+\. /, "").trim());
  if (facts.length !== 5) throw new Error(`${heading}: expected five grounded facts, got ${facts.length}`);
  sections.set(heading, facts);
}

// These are distinct canonical questions, one per source fact in heading order.
const questions = new Map([
  ["Form role and hierarchy", [
    "Which form owns a regular order's item-level demand?", "Can one customer order have several lines?", "What values belong to an individual order line?", "Which forms hold scheduled blanket-order demand?", "What identifiers do I need for a specific line answer?",
  ]],
  ["Header handoff and navigation", [
    "Must the order header be saved before adding lines?", "Where does the Lines action on a regular order lead?", "How do I reach scheduled blanket releases?", "What detail can the Order Detail Tree show?", "Why might the tree omit a multi-site shipment?",
  ]],
  ["Find the intended line", [
    "What should I confirm after searching for an order number?", "How should I choose the correct visible line?", "What does a line number identify?", "Which values should I compare before answering about a line?", "Why is release number needed for blanket demand?",
  ]],
  ["Create and save a regular line", [
    "How do I start a new regular order line?", "What identifier and item do I enter on a new line?", "Which commercial and fulfillment fields should I verify before saving?", "What should I inspect immediately after saving a line?", "Is an AI-recommended line automatically saved?",
  ]],
  ["Item selection and setup", [
    "What must the Item field match?", "Should I trust item defaults without checking the saved line?", "Which item tracking and stock controls matter?", "What should I check when the expected item is missing?", "When do configuration features apply to a line?",
  ]],
  ["Description and unit of measure", [
    "Is description or item number the stronger identifier?", "What does line U/M define?", "What U/M check comes before a quantity change?", "Why can numeric quantities appear inconsistent?", "Where might an Ordered-line U/M change be recorded?",
  ]],
  ["Qty Ordered and other quantities", [
    "Does Qty Ordered mean the whole order's quantity?", "Which quantities must be kept separate from Qty Ordered?", "What item allocation can change when Qty Ordered changes?", "What downstream effects should I consider before editing quantity?", "How should I investigate a line quantity mismatch?",
  ]],
  ["Unit Price and repricing", [
    "What does Unit Price represent on a line?", "Will a Qty Ordered edit automatically pick up a new Items price?", "What should be verified before repricing?", "Which rules can influence an order line's price?", "What should a saved line price be compared against?",
  ]],
  ["Discount and line amount", [
    "Should line discount be reviewed separately from Unit Price?", "What header charges can change the final billed amount?", "Which values explain a line amount discrepancy?", "Does an estimated line amount prove payment?", "Who may change price or discount?",
  ]],
  ["Due, request, and projected dates", [
    "Is line Due Date the same as Order Date or invoice due date?", "How can a new line's Due Date default?", "What does Request Date preserve in APS?", "Is Projected Date always the agreed date?", "When can time-of-day matter on an order line?",
  ]],
  ["Warehouse and Ship Site", [
    "Where can a line warehouse default from?", "Can a user always override the line warehouse?", "What does Ship Site identify?", "Does a default warehouse reserve stock?", "What must be checked before promising delivery from a site?",
  ]],
  ["Line status and progression", [
    "Which status categories appear in line or release reporting?", "Does an Ordered header guarantee an Ordered line?", "Can a Planned line ship as normal demand?", "Does Complete status by itself prove an invoice?", "What evidence is needed for a stopped line?",
  ]],
  ["Credit hold and blocked lines", [
    "Where may the customer credit-hold warning appear?", "Which credit holds can block shipping?", "Can a credit-held order create a new cross-reference?", "Does exceeding the credit limit always cause an automatic hold?", "May the chatbot remove a hold or advance a Planned line?",
  ]],
  ["Source area overview", [
    "What source types can supply a customer order line?", "Which fields are in the Source area header?", "What can Source sub-areas reveal about linked supply?", "What does Inventory source imply about hard-pegging?", "Does a Source reference prove goods were received?",
  ]],
  ["Inventory source", [
    "How does Inventory source normally fulfill a stocked item?", "Which stock details can the Source area display?", "When can inventory-referenced Ready to Ship increase?", "Why is on-hand quantity not the same as available stock?", "What report helps when multiple orders compete for stock?",
  ]],
  ["Job source", [
    "What does Job source link to the order line?", "When may a non-stocked manufactured item default to Job?", "Which identifiers can be in a job cross-reference?", "What manufacturing progress can the Source area show?", "When can job-referenced Ready to Ship increase?",
  ]],
  ["Purchase Order source", [
    "What does Purchase Order source mean?", "Which PO identifiers can the source reference contain?", "What PO progress can the Source area show?", "When can a PO-referenced line become ready?", "Is a vendor's promise proof of customer shipment?",
  ]],
  ["Requisition source", [
    "What stage of purchasing is Requisition source?", "Which requisition identifiers can the line hold?", "What requisition details can the Source area show?", "Is an open requisition received stock?", "What should I inspect for a requisition sourcing delay?",
  ]],
  ["Transfer source", [
    "What movement does Transfer source represent?", "What transfer information can Source show?", "When does transfer-referenced readiness increase?", "Is source-site shipment the same as fulfillment-site receipt?", "Which details help diagnose a transfer delay?",
  ]],
  ["Project and SRO source", [
    "When can Project be a line source?", "What can SRO identify?", "Why might Project or SRO be unavailable?", "Does a linked SRO prove an invoice?", "Who should review an inaccessible project or service reference?",
  ]],
  ["Cross-reference rules", [
    "What is a demand-to-supply hard peg?", "Can one supply cross-reference normally serve multiple demands?", "Which supply types can be linked to a line?", "What happens when linked supply misses quantity or date?", "What checks precede creation of a cross-reference?",
  ]],
  ["Reservations and traceability", [
    "What conditions are needed for an ordinary inventory reservation?", "Which forms show reserved warehouse, location, or lot?", "Can serial numbers be reserved specifically?", "Is a reservation a posted shipment?", "How should I verify an order-line reservation?",
  ]],
  ["Ready to Ship versus Available to Ship", [
    "What is the line's Ready to Ship value based on?", "Which supply completions can increase line readiness?", "How does the Available to Ship Report handle competing orders?", "Why can Ready to Ship differ from that report?", "What evidence is needed before saying a line can ship?",
  ]],
  ["Partial shipment and balances", [
    "Can lines on one order be at different fulfillment stages?", "Is header Ship Partial the only eligibility check?", "Which quantities define a line's remaining balance?", "Does a partial shipment complete the entire line?", "Which local controls should be checked for a partial?",
  ]],
  ["Pick and shipping handoff", [
    "Does saving an order line perform picking or shipping?", "Which line statuses can Order Shipping filter?", "What must be checked before a line is shipped?", "What updates the shipped fields of a line?", "Which shipment fields appear in Order Detail Tree?",
  ]],
  ["Invoice hold and billing handoff", [
    "What does Invoice Hold do to a shipped line?", "Are shipping and invoicing one event?", "Which checks explain a shipped-not-invoiced line?", "Does consolidated invoicing need extra setup?", "What evidence confirms that a customer was billed?",
  ]],
  ["Blanket line and release branch", [
    "Which Order Type identifies a blanket order?", "What do Customer Order Blanket Lines describe?", "What do Customer Order Blanket Releases hold?", "Which blanket quantities should be reconciled?", "Can a release Unit Price differ from its blanket line?",
  ]],
  ["Non-inventory item branch", [
    "Must a non-inventory item's price sometimes be entered manually?", "Should non-inventory items be treated as ordinary stocked inventory?", "Can a non-inventory line be job-sourced in the documented procedure?", "What non-inventory behavior needs local version confirmation?", "How should help distinguish stocked and non-inventory demand?",
  ]],
  ["Configured item branch", [
    "When are CPQ or Product Configurator controls present?", "How can a planning item be configured?", "Why might Configure/Create Item be disabled?", "How should a configuration hold be handled?", "What determines whether a configured item is created?",
  ]],
  ["Change log and corrections", [
    "Which creation or status events can appear in the line change log?", "Which field edits can the change log record?", "Can Ordered-line deletion appear in the change log?", "Can a shipped or invoiced line always be deleted directly?", "What context should be captured before a line correction?",
  ]],
  ["Troubleshooting sequence", [
    "What identifiers and error should be gathered first?", "Which line fields should be checked in a diagnosis?", "Which hold and readiness checks should be kept separate?", "Which linked supply records might need investigation?", "What records should be compared before recommending a correction?",
  ]],
  ["Permissions and live-data boundary", [
    "Can this guide report a named customer's current line price?", "Which permissions must secure a live line lookup?", "Does read permission allow line changes?", "Should a chatbot invent local IDO mappings?", "What if site or authorization is uncertain?",
  ]],
]);

// Manual-only revision: replace prompts whose source facts changed during the
// 9.01.x User Guide audit. Retain stable prompts for the unchanged sections.
questions.delete("Due, request, and projected dates");
questions.delete("Permissions and live-data boundary");
const guideQuestions = new Map([
  ["Header handoff and navigation", ["Must the order header be saved before adding lines?", "Where does the Lines action on a regular order lead?", "How do I reach scheduled blanket releases?", "What alternative does the manual give for creating an entire order?", "Do shipping and invoicing happen during line entry?"]],
  ["Find the intended line", ["How do I navigate from the saved header to a regular or blanket detail?", "Does the change log distinguish an order line from its header?", "Which regular and blanket detail forms does the manual distinguish?", "Which values identify the line being discussed?", "Why identify the relevant blanket release?"]],
  ["Create and save a regular line", ["How do I start a new regular order line?", "What identifier and item do I enter on a new line?", "Which commercial and fulfillment fields should I verify before saving?", "What should I inspect immediately after saving a line?", "How does the manual suggest checking availability before saving?"]],
  ["Item selection and setup", ["What must the Item field match?", "Should I trust item defaults without checking the saved line?", "Which item types have different manual procedures?", "Which item condition can trigger an order-entry warning?", "Which planning items can use the manual's configuration procedure?"]],
  ["Description and unit of measure", ["Is description or item number the stronger identifier?", "What does line U/M define?", "Where does a blanket line's U/M default from?", "Where is a line or release U/M update logged?", "Can a blanket-line U/M change appear in the log?"]],
  ["Unit Price and repricing", ["What does Unit Price represent on a line?", "How does the pricing sequence handle a promotion?", "Can Customer Contracts provide unit price?", "When do quantity breaks or a Price Matrix determine price?", "What happens when no applicable Item Pricing record exists?"]],
  ["Discount and line amount", ["Should line discount be reviewed separately from Unit Price?", "When are product-code and customer-type discounts applied?", "What happens to Unit Price when a promotion code applies?", "What happens to an existing Sales Discount after a promotion?", "Can a promotion code apply to an entire order or blanket line?"]],
  ["Order entry and planning dates", ["Which parameter defines the standard due period?", "Which order-entry actions check availability?", "When should availability results be reviewed?", "What APS exception can arise when supply is due after demand?", "Where are a blanket release's date and quantity entered?"]],
  ["Warehouse and Ship Site", ["Which form compares sites and warehouses for an order line?", "What quantities can be compared across warehouses?", "What factors help choose a warehouse?", "How are selected site and warehouse values returned to the line?", "Where can copied multi-site lines be placed?"]],
  ["Line status and progression", ["Which line statuses matter in the manual's credit checks?", "What status can a failed credit check assign?", "What allocation changes when a blanket release becomes Ordered?", "When can a fully shipped and invoiced line become Complete?", "Which status changes does the line change log record?"]],
  ["Source area overview", ["Which supply types does the Source-tab overview mention?", "What does a hard-peg cross-reference connect?", "Why can Source sub-tabs help a user without supply-form access?", "Does Inventory Source have a supply-order cross-reference?", "Can a customer order line be cross-referenced to a project task?"]],
  ["Inventory source", ["When does Inventory become the default Source reference?", "Does Inventory Source create a one-to-one supply link?", "How does reserving stock affect other demand?", "When can an Inventory-referenced blanket release gain Ready Quantity?", "How does the Available to Ship Report decide order inclusion?"]],
  ["Job source", ["What does Job source link to the order line?", "When may a non-stocked manufactured item default to Job?", "Which identifiers can be in a job cross-reference?", "What steps create or confirm a job cross-reference?", "What job activity updates a blanket release's Ready Quantity?"]],
  ["Purchase Order source", ["What does Purchase Order source mean?", "Which PO identifiers can the source reference contain?", "How is a PO cross-reference created or confirmed?", "What PO event updates the line's Ready Quantity?", "Is a vendor's promise proof of customer shipment?"]],
  ["Requisition source", ["What stage of purchasing is Requisition source?", "Which requisition identifiers can the line hold?", "Where is a customer-order requisition source set?", "How does Source create or display a requisition link?", "Which workbench supports a range of requisition cross-references?"]],
  ["Transfer source", ["What movement does Transfer source represent?", "At which site does a CO-to-transfer cross-reference start?", "Which records are linked at the To site?", "Can linked transfer supply serve another demand?", "Which workbench supports a range of transfer cross-references?"]],
  ["Project and SRO source", ["Can a blanket release be cross-referenced to a project task?", "What setup precedes creation of a linked project?", "Can the Project Source procedure create a new project task?", "Can non-inventory items be sourced to projects?", "Does this manual give a detailed SRO line procedure?"]],
  ["Cross-reference rules", ["What is a demand-to-supply hard peg?", "Can one supply cross-reference normally serve multiple demands?", "Which supply types have detailed CO cross-reference procedures?", "What happens when linked supply misses quantity or date?", "What checks precede creation of a cross-reference?"]],
  ["Ready to Ship versus Available to Ship", ["Where does the manual use Ready Quantity?", "Which job activity can update blanket-release readiness?", "How does PO receiving affect line readiness?", "How can Available to Ship Report output be narrowed?", "How does Ship Partial affect report inclusion?"]],
  ["Partial shipment and balances", ["When does a non-partial order appear in Available to Ship?", "When can a Ship Partial order appear in that report?", "Does Ship Partial permit partial quantities of one line?", "Which quantities enter the manual's reservation calculation?", "How does shipping a blanket release affect Alloc Order?"]],
  ["Pick and shipping handoff", ["When does shipping happen in the manual's order-entry sequence?", "Which report starts the standard shipping check?", "Which utility follows the Available to Ship Report?", "Are Picking/Packing/Shipping and standard Order Shipping one routine?", "Which credit conditions prevent shipping?"]],
  ["Invoice hold and billing handoff", ["What does Invoice Hold prevent on a line or release?", "Why might a customer request Invoice Hold until receipt?", "What happens to shipped quantity after Invoice Hold is removed?", "Where is Consolidated Invoice selected for a line or release?", "What happens in A/R when an order invoice is printed?"]],
  ["Blanket line and release branch", ["Which Order Type identifies a blanket order?", "What do Customer Order Blanket Lines describe?", "What do Customer Order Blanket Releases hold?", "Which blanket quantities should be reconciled?", "Can the blanket line U/M be changed before releases are added?"]],
  ["Non-inventory item branch", ["Must a non-inventory item's Unit Price be entered manually?", "Can a non-inventory line be job-sourced in this manual?", "Can a non-inventory line be project-sourced in this manual?", "Where does a non-inventory line's material cost come from?", "Which COGS account does the manual debit for non-inventory items?"]],
  ["Configured item branch", ["Which configurator does this manual's order-entry procedure cover?", "What kind of item is selected for configuration?", "Where are feature-group selections made?", "What enables Config String on the line?", "Which parameter affects Create Item behavior?"]],
  ["Change log and corrections", ["Which creation or status events can appear in the line change log?", "Which field edits can the change log record?", "Can Ordered-line deletion appear in the change log?", "When does an order marked for deletion actually delete?", "Which manual procedure adjusts an invoiced line's price, discount, or quantity?"]],
  ["Troubleshooting sequence", ["What guide checks help explain an order-entry warning?", "Which manual pricing steps help explain a price question?", "Which records help explain missing supply?", "What manual checks precede a shipping answer?", "What evidence helps explain a billing question?"]],
  ["Source visibility and guide boundary", ["Can Customer Order Lines users always open related supply forms?", "What can Source sub-tabs show without direct supply-form access?", "Does the manual include today's value for a named order line?", "Does this article define local IDO names or permission grants?", "What must be confirmed before acting in a different SyteLine release?"]],
]);
for (const [heading, prompts] of guideQuestions) questions.set(heading, prompts);
if (sections.size !== 32 || questions.size !== 32) throw new Error("Expected 32 grounded sections");
const manualPages = new Map([
  ["Form role and hierarchy","11-12, 39"], ["Header handoff and navigation","33, 39"],
  ["Find the intended line","33, 39, 43"], ["Create and save a regular line","33"],
  ["Item selection and setup","33-34"], ["Description and unit of measure","39, 43"],
  ["Qty Ordered and other quantities","12, 43, 69"], ["Unit Price and repricing","35"],
  ["Discount and line amount","35, 106"], ["Order entry and planning dates","32-33, 39, 74"],
  ["Warehouse and Ship Site","38, 53-54"], ["Line status and progression","33, 36, 43, 96"],
  ["Credit hold and blocked lines","39, 96"], ["Source area overview","12, 74-75"],
  ["Inventory source","43, 69, 74"], ["Job source","75-76"],
  ["Purchase Order source","75, 79-80"], ["Requisition source","76-77"],
  ["Transfer source","78-79"], ["Project and SRO source","12, 78"],
  ["Cross-reference rules","74-75"], ["Reservations and traceability","69-70"],
  ["Ready to Ship versus Available to Ship","43, 56, 75"], ["Partial shipment and balances","43, 56, 69"],
  ["Pick and shipping handoff","33, 55-56"], ["Invoice hold and billing handoff","33, 46, 88-89"],
  ["Blanket line and release branch","39"], ["Non-inventory item branch","30, 35, 76, 78"],
  ["Configured item branch","34"], ["Change log and corrections","43, 68"],
  ["Troubleshooting sequence","33, 35, 56, 74, 96"], ["Source visibility and guide boundary","75"],
]);
if (manualPages.size !== sections.size) throw new Error("Missing manual page mapping");
const book = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const master = book.worksheets.getItem("qa_master");
const variations = book.worksheets.getItem("question_variations");
console.log((await book.inspect({kind:"workbook,sheet,table",maxChars:900,tableMaxRows:2,tableMaxCols:3})).ndjson);
const before = await book.render({sheetName:"qa_master",range:"A1:D4",scale:1,format:"png"});
await fs.writeFile(path.join(previewPath,"customer_order_line_qa_before.png"),new Uint8Array(await before.arrayBuffer()));
const oldRows = master.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("COLN-"));
const oldVariations = variations.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("COLN-"));
const seen = new Set(oldRows.map(row => String(row[8]).trim().toLowerCase()));
const newRows = [];
const newVariations = [];
let number = 0;
for (const [heading, facts] of sections) {
  const prompts = questions.get(heading);
  if (!prompts || prompts.length !== facts.length) throw new Error(`Question mismatch: ${heading}`);
  for (let i=0; i<5; i++) {
    const question = prompts[i];
    if (seen.has(question.toLowerCase())) throw new Error(`Duplicate question: ${question}`);
    seen.add(question.toLowerCase());
    const id = `COLN-${String(++number).padStart(4,"0")}`;
    const answer = facts[i];
    const intent = /which|where|field|form|date|number|status|what is/i.test(question) ? "HELP_FIELD" : "HELP_PROCESS";
    newRows.push([id,"PROSPECT_TO_CASH","Customer-to-Cash","customer_order_line","Customer Order Lines","",intent,"",question,answer,heading.toLowerCase(),"","FAST_QA","customer_order_line.md",`Customer Order Line Module > ${heading}`,`Infor SyteLine Customer Service User Guide 9.01.x, printed pp. ${manualPages.get(heading)}`,"Verify current site","Effective SyteLine permissions","IN_REVIEW","Pending local SyteLine SME approval","2026-10-08",false,"","en"]);
    const lower = question[0].toLowerCase()+question.slice(1);
    newVariations.push([id,"V1",`In SyteLine, ${lower}`,"en","editorial_variation",false]);
    newVariations.push([id,"V2",`Could you help me answer this: ${question}`,"en","editorial_variation",false]);
    newVariations.push([id,"V3",`For a customer order line, ${lower}`,"en","editorial_variation",false]);
  }
}
if (newRows.length !== 160) throw new Error(`Expected 160, got ${newRows.length}`);
for (const row of oldRows) {
  row[3] = "customer_order_line";
  row[18] = "IN_REVIEW";
  row[19] = "Pending local SyteLine SME approval";
  row[21] = false;
}
const rows = [...oldRows,...newRows];
const vars = [...oldVariations,...newVariations];
master.getRange(`A2:X${rows.length+1}`).values = rows;
variations.getRange(`A2:F${vars.length+1}`).values = vars;
master.getRange(`A1:A${rows.length+1}`).format.columnWidth = 16;
master.getRange(`B1:B${rows.length+1}`).format.columnWidth = 23;
master.getRange(`C1:C${rows.length+1}`).format.columnWidth = 24;
master.getRange(`D1:D${rows.length+1}`).format.columnWidth = 21;
master.getRange(`I1:I${rows.length+1}`).format.columnWidth = 50;
master.getRange(`J1:J${rows.length+1}`).format.columnWidth = 82;
variations.getRange(`A1:A${vars.length+1}`).format.columnWidth = 16;
variations.getRange(`B1:B${vars.length+1}`).format.columnWidth = 10;
variations.getRange(`C1:C${vars.length+1}`).format.columnWidth = 70;
book.recalculate();
console.log(`Rows=${rows.length}; new=${newRows.length}; variations=${vars.length}`);
console.log((await book.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const after = await book.render({sheetName:"qa_master",range:`A${oldRows.length+1}:D${oldRows.length+4}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewPath,"customer_order_line_qa_after.png"),new Uint8Array(await after.arrayBuffer()));
const answerAfter = await book.render({sheetName:"qa_master",range:`I${oldRows.length+1}:J${oldRows.length+4}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewPath,"customer_order_line_answers_after.png"),new Uint8Array(await answerAfter.arrayBuffer()));
const variationsAfter = await book.render({sheetName:"question_variations",range:`A${oldVariations.length+1}:D${oldVariations.length+4}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewPath,"customer_order_line_variations_after.png"),new Uint8Array(await variationsAfter.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(workbookPath);
console.log(`Saved ${workbookPath}`);
