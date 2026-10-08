// Expand only Customer Orders Q&A. Answers are exact source sentences or rows.
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const articlePath = path.join(root, "data/knowledge/prospect_to_cash/customer_order.md");
const workbookPath = path.join(root, "data/qa/prospect_to_cash/customer_order.xlsx");
const source = await fs.readFile(articlePath, "utf8");
const sections = new Map();
for (const block of source.split(/^## /m).slice(1)) {
  const newline = block.indexOf("\n");
  const heading = block.slice(0, newline).trim();
  if (heading === "Document Metadata") continue;
  sections.set(heading, block.slice(newline + 1).split("**Section Summary:**")[0].trim());
}

// Every group maps to one article heading and contributes five distinct
// canonical questions. The anchor must exist verbatim in the cited section.
const groups = [
  ["Purpose and form ownership", [
    ["Which form holds the order header?", "Customer Orders holds the order header"],
    ["Which form holds the ordered items?", "Customer Order Lines holds the actual items"],
    ["What is the normal sequence after saving a header?", "create header, save it, add lines"],
    ["Does an accepted quote itself count as an order?", "a quote is not itself an order"],
    ["Which header values identify delivery and billing defaults?", "customer, ship-to, order type and status"],
  ]],
  ["Create and review an order", [
    ["What should be searched to avoid duplicate orders?", "line:Search existing orders"],
    ["Which parties should be selected on a new order header?", "line:select customer and ship-to"],
    ["Which commercial header values should be reviewed?", "line:Review order type"],
    ["What happens immediately after the header is saved?", "line:Save the header"],
    ["When is the Order Verification Report useful?", "line:Print an Order Verification Report"],
  ]],
  ["Status, holds, and changes", [
    ["Are header status and line status the same?", "Order and line statuses are separate"],
    ["How can a credit check affect a line?", "leave a line Planned"],
    ["Can either a customer hold or order hold block shipping?", "both block shipping"],
    ["Is release order always the correct next step?", "not tell a user to simply"],
    ["What must be rechecked after an order change?", "recheck price, dates, tax"],
  ]],
  ["Order types and exceptions", [
    ["Do Regular and Blanket customer orders follow the same line process?", "Regular and blanket orders differ"],
    ["What additional records do blanket orders use?", "blanket lines and releases"],
    ["Can an order involve several shipping sites?", "multiple shipping sites"],
    ["Which special order paths depend on configuration?", "drop-ship lines, EDI origin"],
    ["What should be known before giving an exception procedure?", "Identify the order type"],
  ]],
  ["Troubleshoot an order that cannot progress", [
    ["What first evidence is needed when an order cannot progress?", "exact error and order number"],
    ["Which statuses should be checked on a blocked order?", "current header/line status"],
    ["Which holds should be checked before shipping?", "customer and order credit hold"],
    ["Which report can help with order-processing exceptions?", "Order Entry Exception Report"],
    ["Should credit hold be assumed whenever shipping fails?", "Do not assume a credit hold"],
  ]],
  ["Header fields and downstream consequences", [
    ["Why check Customer and bill-to on the header?", "table:Customer and bill-to"],
    ["Why check ship-to and shipping site on the header?", "table:Ship-to and shipping site"],
    ["What links correspondence with order history?", "table:Order number and customer PO"],
    ["Why review order type and Status together?", "table:Order type and Status"],
    ["Why review Terms, freight, tax, and discount?", "table:Terms, freight, tax, discount"],
  ]],
  ["Order state questions and what to inspect", [
    ["How do I check whether an order is booked?", "For “Is the order booked?”"],
    ["How do I check whether an order can ship?", "For “Can it ship?”"],
    ["What proves an order has shipped?", "For “Has it shipped?”"],
    ["What proves an order has been invoiced?", "For “Has it been invoiced?”"],
    ["What should be checked before cancelling an order?", "For “Can I cancel it?”"],
  ]],
  ["Before order entry", [
    ["What customer status is needed for order entry?", "active for order processing"],
    ["Which destination and finance defaults should be checked first?", "intended bill-to, ship-to, currency, terms"],
    ["Should I distinguish a new order from an existing-order change?", "new order, a change to an existing order"],
    ["Why search the customer's PO before creating an order?", "Search for a previous order or customer PO"],
    ["Can I assume customer-master defaults persisted to the order?", "saved order must be checked independently"],
  ]],
  ["Find an existing order", [
    ["Which number is best for finding a known order?", "order number when known"],
    ["Which fields can narrow a Customer Orders search?", "customer, order date, status"],
    ["What details can the Customer Orders Lookup widget show?", "order number, customer, contact"],
    ["Why might an existing order be absent from search?", "site, filters, history status"],
    ["Is customer PO always a unique order identifier?", "may not uniquely identify"],
  ]],
  ["Create the Customer Orders header", [
    ["Which action starts a new Customer Orders header?", "Actions > New"],
    ["Which header fields are selected before saving?", "Order number, choose the Order Type"],
    ["What defaults should be reviewed before saving an order?", "Customers and Customer Ship-Tos"],
    ["Which action saves the order header?", "Actions > Save"],
    ["Does saving the header complete the ordered items?", "does not mean that items"],
  ]],
  ["Order number and originating site", [
    ["What does the Order number connect?", "connects related lines"],
    ["Should I invent a customer order numbering rule?", "rather than inventing"],
    ["Which site should be recorded for a multi-site order?", "originating site"],
    ["Where are some multi-site header status decisions controlled?", "at the originating site"],
    ["Does seeing an order number in another site grant access?", "not treat the same visible order number"],
  ]],
  ["Order Date and planning dates", [
    ["What does Order Date mean?", "date the order was taken"],
    ["What date can a new order default to?", "today's date"],
    ["Are line due dates the same as the header date?", "can differ from the header date"],
    ["Which delivery dates must be kept distinct?", "requested date, promised or projected date"],
    ["Does Order Date tell us when goods will be delivered?", "do not infer that Order Date"],
  ]],
  ["Select a valid Customer", [
    ["What does the Customer field select?", "account placing the order"],
    ["Why check the customer number as well as the display name?", "rather than relying only"],
    ["What should I check if the customer is missing from selection?", "current site, customer status"],
    ["Can a Customer Status block order processing?", "active for order processing"],
    ["Should I switch accounts just to pass validation?", "Do not switch to another account"],
  ]],
  ["Select Ship To and verify addresses", [
    ["Which address does Customer Orders display for Ship To?", "selected Ship To customer's name and address"],
    ["Can another valid Ship To be selected?", "allows a different valid Ship To"],
    ["Why check bill-to separately from ship-to?", "check the bill-to separately"],
    ["Can a valid ship-to be hidden from the drop-down?", "Show in Drop-Down Lists"],
    ["What ship-to value should be checked after defaulting?", "saved order's selected ship-to number"],
  ]],
  ["Order and billing contacts", [
    ["Where can the order contact default from?", "Customers Order Contact"],
    ["Can an individual order use a different order contact?", "changed on an individual order"],
    ["Where does the Bill To contact come from?", "Customers Billing Contact"],
    ["Where does the Ship To contact come from?", "Customer Ship-Tos"],
    ["Does editing the order contact edit the customer master?", "need not change the customer master"],
  ]],
  ["Order Type on the header", [
    ["What does Order Type distinguish?", "Regular order from a Blanket order"],
    ["Which form is used for regular item demand?", "Customer Order Lines"],
    ["What extra structure can blanket orders use?", "blanket lines and multiple releases"],
    ["Why confirm Order Type before reviewing the Detail Tree?", "Confirm the type before"],
    ["Do repeat customer purchases automatically mean Blanket orders?", "assume a special type"],
  ]],
  ["Header Status and line status", [
    ["Which record does Customer Orders Status describe?", "describes the header"],
    ["Which header statuses does Infor list?", "Ordered, Planned, Stopped, Complete, and History"],
    ["What status do new headers normally default to?", "default to Ordered"],
    ["Does an Ordered header prove every line can ship?", "does not prove every line can ship"],
    ["Can a Planned line be shipped?", "not available for shipment"],
  ]],
  ["Customer Purchase Order reference", [
    ["What is the Customer Purchase Order field?", "customer's own purchase-order number"],
    ["How does customer PO help find an order?", "help filter for an order"],
    ["Is Customer Purchase Order the SyteLine Order number?", "not the SyteLine Order number"],
    ["Why compare customer PO with the customer's document?", "spelling and revision"],
    ["Should the chatbot invent a missing customer PO?", "do not invent a number"],
  ]],
  ["Terms, currency, and commercial defaults", [
    ["Which record can supply Terms Code and currency defaults?", "Customers record can supply"],
    ["Which record shows the terms actually used?", "saved Customer Orders transaction"],
    ["When should order terms be compared with a quote?", "after a copy or conversion"],
    ["What can a commercial-default mismatch affect?", "invoice due dates, pricing conversion"],
    ["Are all header commercial fields editable for every user?", "user's permissions"],
  ]],
  ["Tax Info on Customer Orders", [
    ["Where are order tax codes reviewed?", "Tax Info area"],
    ["Which setup factors can change order tax?", "configured tax systems"],
    ["Which report can be used to verify order tax?", "Order Verification Report"],
    ["Is there one universal freight tax code for every tax mode?", "Do not prescribe a universal tax code"],
    ["What context should accompany a tax discrepancy?", "order, site, customer, ship-to"],
  ]],
  ["Freight and miscellaneous charges", [
    ["Which non-item charges should be reviewed on an order?", "freight, miscellaneous charges"],
    ["Does Freight Tax Code behave the same in all tax systems?", "differs between area-based and item-based"],
    ["Can tax change the invoice even with correct quantities?", "even when item quantities are correct"],
    ["What ownership should be confirmed for a charge?", "whether it belongs on the header"],
    ["Does estimated order amount prove the invoice total?", "not use an estimated order amount"],
  ]],
  ["Warehouse and shipping site defaults", [
    ["Where can the order header Warehouse default from?", "selected Customer Ship-To"],
    ["Can a line inherit the header warehouse?", "a line may inherit"],
    ["What does Ship Site identify?", "site intended to ship a line"],
    ["Must Ship Site be valid for the item?", "valid for the item"],
    ["Does a default warehouse prove stock is available?", "not an allocation or proof"],
  ]],
  ["Ship Partial and shipment expectations", [
    ["What customer preference does Ship Partial record?", "accepts partial shipments"],
    ["When can an order with Ship Partial cleared appear on the readiness report?", "cleared flag normally requires all lines"],
    ["When can an order with Ship Partial selected appear?", "at least one line is ready"],
    ["Does Ship Partial permit partial quantities of one line by itself?", "does not by itself permit partial quantities"],
    ["What else must be checked for actual shipment eligibility?", "holds, line status, and available stock"],
  ]],
  ["Credit Hold on the order", [
    ["Which form owns order-level Credit Hold?", "Customer Orders is an order-level control"],
    ["Can either order or customer hold prevent shipment?", "Either hold can prevent shipping"],
    ["Can an order show a red indicator without its hold field selected?", "red problem indicator"],
    ["Which parameter affects automatic credit hold outcome?", "Limit Exceeded Credit Hold Reason"],
    ["What should happen before changing a hold?", "authorized credit review"],
  ]],
  ["Amounts and estimated totals", [
    ["Where can order-level amounts appear?", "Customer Orders Amounts area"],
    ["Does estimated total prove invoice or payment?", "not proof of an invoice or payment"],
    ["When may certain tax amounts appear in Amounts?", "when shipping occurs"],
    ["Which values should be compared for an amount difference?", "saved line prices, discounts, freight"],
    ["What access is required for a named order amount?", "authorized live data"],
  ]],
  ["Lines button and item handoff", [
    ["When should the Lines button be clicked?", "After saving the Customer Orders header"],
    ["Which form opens from the Lines button?", "Customer Order Lines"],
    ["Which item details belong on order lines?", "item, quantity, due date, price"],
    ["Can several lines belong to one order header?", "Multiple lines can belong"],
    ["Can a newly entered line remain unsaved?", "new and unsaved"],
  ]],
  ["Customer Orders Quick Entry alternative", [
    ["Which action starts an order in Quick Entry?", "New Order"],
    ["Which action adds a line in Quick Entry?", "New Line"],
    ["Why check the customer selected by a lookup widget?", "preselect a record"],
    ["What does Refresh do for an existing Quick Entry record?", "returns to its last saved state"],
    ["Which functions may require the full application form?", "blanket-order entry, notes"],
  ]],
  ["Order Detail Tree navigation", [
    ["What does the Order Detail Tree display?", "line and shipment information"],
    ["What appears at the first tree level for a regular order?", "first level shows line"],
    ["What extra tree level does a blanket order add?", "release level"],
    ["Why expand a tree row before claiming an item shipped?", "Expand the relevant row"],
    ["Why might multi-site shipment detail appear incomplete in the tree?", "limited to the current site"],
  ]],
  ["Blanket-order branch", [
    ["What should be saved before blanket lines and releases?", "save the Customer Orders header"],
    ["Which forms own blanket lines and releases?", "Customer Order Blanket Lines and Customer Order Blanket Releases"],
    ["What do blanket lines describe?", "describe the agreement"],
    ["What do blanket releases specify?", "dates and quantities to fulfill"],
    ["Which blanket quantities should be compared?", "Quantity Released with Blanket Quantity"],
  ]],
  ["Permissions and live-order boundary", [
    ["Can this article tell me a named order's current status?", "requires an authorized live SyteLine lookup"],
    ["Which permissions govern a live order answer?", "effective site, form, field, and row permissions"],
    ["Does read permission authorize changing an order?", "Read permission does not grant"],
    ["What context should be recorded for an approved action?", "Record audit context"],
    ["Can static guidance confirm an order is ready to ship today?", "No static article can confirm"],
  ]],
];

function groundedAnswer(heading, anchor) {
  const body = sections.get(heading);
  if (!body) throw new Error(`Missing section: ${heading}`);
  if (anchor.startsWith("table:")) {
    const row = body.split("\n").find(line => line.startsWith(`| ${anchor.slice(6)} |`));
    if (!row) throw new Error(`Missing table row: ${heading} / ${anchor}`);
    return row.split("|").slice(1, 3).map(s => s.trim()).join(": ").replace(/\.$/, ".");
  }
  if (anchor.startsWith("line:")) {
    const line = body.split("\n").find(line => line.includes(anchor.slice(5)));
    if (!line) throw new Error(`Missing list line: ${heading} / ${anchor}`);
    return line.replace(/^\d+\.\s*/, "").trim();
  }
  const answer = body.replace(/\n/g, " ").split(/(?<=[.!?])\s+/).find(sentence => sentence.toLowerCase().includes(anchor.toLowerCase()));
  if (!answer) throw new Error(`Missing answer anchor: ${heading} / ${anchor}`);
  return answer.trim();
}

if (groups.length !== 30 || groups.some(([, items]) => items.length !== 5)) throw new Error("Expected 30 groups of five questions");
const book = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const master = book.worksheets.getItem("qa_master");
const variations = book.worksheets.getItem("question_variations");
console.log((await book.inspect({kind:"workbook,sheet,table",maxChars:1000,tableMaxRows:2,tableMaxCols:3})).ndjson);
const oldPreview = await book.render({sheetName:"qa_master",range:"A1:D4",scale:1,format:"png"});
await fs.writeFile(path.join(os.tmpdir(),"customer_order_qa_before.png"),new Uint8Array(await oldPreview.arrayBuffer()));
const masterValues = master.getUsedRange().values;
const oldRows = masterValues.slice(1).filter(row => !String(row[0]).startsWith("CORD-"));
const variationValues = variations.getUsedRange().values;
const oldVariations = variationValues.slice(1).filter(row => !String(row[0]).startsWith("CORD-"));
const newRows = [];
const newVariations = [];
const seen = new Set(oldRows.map(row => String(row[8]).trim().toLowerCase()));
let index = 0;
for (const [heading, items] of groups) {
  for (const [question, anchor] of items) {
    const normalized = question.trim().toLowerCase();
    if (seen.has(normalized)) throw new Error(`Duplicate canonical question: ${question}`);
    seen.add(normalized);
    index += 1;
    const id = `CORD-${String(index).padStart(4,"0")}`;
    const answer = groundedAnswer(heading, anchor);
    const intent = /which|where|field|form|date|number|type|status/i.test(question) ? "HELP_FIELD" : /how|when|why|should|can|before|after/i.test(question) ? "HELP_PROCESS" : "HELP_GENERIC";
    newRows.push([id,"PROSPECT_TO_CASH","Customer-to-Cash","customer_order","Customer Orders","",intent,"",question,answer,heading.toLowerCase(),"","FAST_QA","customer_order.md",`Customer Order Module > ${heading}`,"General CSI/SyteLine; Infor 2026.10 reference","Verify current site","Effective SyteLine permissions","IN_REVIEW","Pending local SyteLine SME approval","2026-10-08",false,"","en"]);
    const lower = question.charAt(0).toLowerCase() + question.slice(1);
    newVariations.push([id,"V1",`In SyteLine, ${lower}`,"en","editorial_variation",false]);
    newVariations.push([id,"V2",`Could you help me answer this: ${question}`,"en","editorial_variation",false]);
    newVariations.push([id,"V3",`For customer orders, ${lower}`,"en","editorial_variation",false]);
  }
}
if (newRows.length !== 150) throw new Error(`Generated ${newRows.length} instead of 150 questions`);
// Old auto-derived approval was not local business approval. Keep the rows but
// require review under the same rule as the new material.
for (const row of oldRows) {
  row[3] = "customer_order";
  row[18] = "IN_REVIEW";
  row[19] = "Pending local SyteLine SME approval";
  row[21] = false;
}
const allRows = [...oldRows, ...newRows];
const allVariations = [...oldVariations, ...newVariations];
master.getRange(`A2:X${allRows.length+1}`).values = allRows;
variations.getRange(`A2:F${allVariations.length+1}`).values = allVariations;
master.getRange(`I1:I${allRows.length+1}`).format.columnWidth = 50;
master.getRange(`J1:J${allRows.length+1}`).format.columnWidth = 82;
variations.getRange(`C1:C${allVariations.length+1}`).format.columnWidth = 70;
book.recalculate();
console.log(`Rows: ${allRows.length}; new: ${newRows.length}; variations: ${allVariations.length}`);
console.log((await book.inspect({kind:"region",sheetId:"qa_master",range:`A${oldRows.length+1}:J${oldRows.length+3}`,maxChars:1000})).ndjson);
console.log((await book.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const preview = await book.render({sheetName:"qa_master",range:`A${oldRows.length+1}:D${oldRows.length+4}`,scale:1,format:"png"});
await fs.writeFile(path.join(os.tmpdir(),"customer_order_qa_after.png"),new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(workbookPath);
console.log(`Saved ${workbookPath}`);
