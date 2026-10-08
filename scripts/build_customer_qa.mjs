// Rebuild only the Customer Q&A workbook from source-grounded question anchors.
// Each answer is an exact sentence from the cited customer.md section.
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const sourcePath = path.join(root, "data/knowledge/prospect_to_cash/customer.md");
const outputPath = path.join(root, "data/qa/prospect_to_cash/customer.xlsx");
const source = await fs.readFile(sourcePath, "utf8");
const sections = new Map();
for (const block of source.split(/^## /m).slice(1)) {
  const newline = block.indexOf("\n");
  const heading = block.slice(0, newline).trim();
  if (heading === "Document Metadata") continue;
  const body = block.slice(newline + 1).split("**Section Summary:**")[0].trim();
  sections.set(heading, body);
}

// The second item is an exact substring that identifies the answer sentence.
const groups = [
  ["Customer-to-Cash starting point", [
    ["What does a Customer record identify?", "identifies the trading account"],
    ["Can an account be created without converting a prospect?", "created directly"],
    ["When must customer setup precede order entry?", "when the account does not already exist"],
    ["Which saved records start the sales transaction?", "Customer Orders header and its lines"],
    ["Is a customer master record already a sales order?", "customer master itself is not an order"],
    ["What should I search before adding a customer number?", "Search for an existing account"],
    ["What business functions use the Customer account?", "orders, billing, shipping, and receivables"],
  ]],
  ["Before opening a new customer record", [
    ["Which identifiers should I use for a duplicate-customer search?", "customer number and name"],
    ["Should I check for a different trading name before creating a customer?", "trading names"],
    ["What should I review when the account originated in CRM?", "prospect or CRM record"],
    ["How do I decide between a new customer and a new ship-to?", "new customer, a new ship-to"],
    ["Why confirm the site before customer creation?", "intended site"],
    ["Can a failed search prove that no customer exists?", "missing search result"],
    ["What may hide an existing customer in a search?", "filters, inactive status"],
  ]],
  ["Customers form — create and save the account", [
    ["Which form opens for a normal customer account?", "Open Customers"],
    ["Which form may be used from an authorized master site?", "Multi-Site Customers"],
    ["Which mode should I leave before creating a customer?", "Filter-in-Place mode"],
    ["How do I start a new customer record?", "Actions > New"],
    ["When can the Customer identifier be left blank?", "Customer Prefix should generate one"],
    ["What must be entered before saving the initial customer?", "bill-to name and address"],
    ["What identifier should I confirm after Actions > Save?", "generated or entered customer number"],
  ]],
  ["Customers form — identity and bill-to fields", [
    ["What is the purpose of the Customer field?", "account identifier"],
    ["Which address identifies the party receiving invoices?", "receives invoices"],
    ["What billing-name detail should be confirmed?", "legal or approved billing name"],
    ["Are bill-to and ship-to the same destination?", "distinct from ship-to destinations"],
    ["How many bill-to addresses can one customer have?", "one bill-to address"],
    ["Can one customer have several delivery locations?", "multiple ship-to locations"],
    ["Will changing a master address certainly update open orders?", "instead of assuming that they all update automatically"],
  ]],
  ["Customers form — billing, currency, and terms", [
    ["Which billing fields should I review on Customers?", "language, currency code, bank information"],
    ["Do customer billing settings always match the saved order?", "inspect the saved order"],
    ["Where is multi-currency customer setup reviewed?", "Currency Codes tab"],
    ["What is the role of the customer Terms Code?", "payment Terms Code"],
    ["Can a multi-due-date terms code be used with letter of credit?", "incompatible with certain features"],
    ["Can a multi-due-date terms code be used with consolidated invoicing?", "consolidated invoicing"],
    ["What should be checked before choosing specialized terms?", "site's enabled features"],
  ]],
  ["Customers form — Ship To tab and default destination", [
    ["Why might the Ship To tab be empty immediately after creating a customer?", "refresh or reopen Customers"],
    ["Which button opens Customer Ship-Tos?", "Ship Tos button"],
    ["Where is the Default Ship To number selected?", "on Customers"],
    ["Can I edit the Default Ship To indicator on Customer Ship-Tos?", "read-only"],
    ["What does the Customer Ship-Tos default indicator reflect?", "customer-level selection"],
    ["Does the default ship-to prove the destination is correct for every order?", "not proof that it is correct"],
    ["What delivery number should be checked on each order?", "actual ship-to on each order"],
  ]],
  ["Customer Ship-Tos — create a destination", [
    ["How do I open the ship-to maintenance form from Customers?", "Customers > Ship To > Ship Tos"],
    ["Which action starts a new ship-to record?", "Actions > New"],
    ["May SyteLine assign the next Ship To number?", "next available sequential number"],
    ["Which tab holds the delivery name and address?", "On Address"],
    ["Which tab holds ship-to defaults and codes?", "On Codes"],
    ["What should be verified after saving a new ship-to?", "under the correct customer"],
    ["When should another ship-to location be added?", "distinct delivery destinations"],
  ]],
  ["Customer Ship-Tos — address and contact checks", [
    ["Does a ship-to identify the invoiced party?", "not who is billed"],
    ["Which location parts should be checked on a ship-to?", "street/address lines"],
    ["Which contact belongs to the delivery location?", "shipping contact"],
    ["Is the shipping contact the same field as the billing contact?", "separate from the Customers billing"],
    ["What should I inspect if an order has the wrong destination?", "selected Ship To number"],
    ["Should I always change the ship-to master to fix an open order?", "not automatically the right correction"],
    ["Where do I confirm the requested delivery destination?", "against the requested destination"],
  ]],
  ["Customer Ship-Tos — warehouse, site, and salesperson", [
    ["What order field can the ship-to Warehouse default?", "default to Customer Orders"],
    ["When should the ship-to Warehouse be left blank?", "different warehouses"],
    ["Where is the correct warehouse chosen when no ship-to default applies?", "on the order instead"],
    ["What site must be checked for each order line in multi-site processing?", "Ship Site"],
    ["Must the Ship Site be valid for the line's item?", "valid for the item"],
    ["What order field may the ship-to Salesperson default?", "future order headers"],
    ["Can a ship-to default be overridden on a transaction?", "may be overridden"],
  ]],
  ["Customers form — Credit tab", [
    ["Where do I inspect customer Credit Limit?", "On Credit"],
    ["Does a credit-limit warning prove that the customer is held?", "does not by itself prove"],
    ["What controls order behavior when credit is exceeded?", "A/R and order-entry parameters"],
    ["What does customer-level Credit Hold block?", "blocks shipments"],
    ["Does customer Credit Hold tick the hold field on every order?", "does not set the Credit Hold field"],
    ["Where is an individual order-level hold inspected?", "Use Customer Orders"],
    ["Can a user clear a credit hold without approval?", "Never advise bypassing"],
  ]],
  ["Customers form — Contacts tab", [
    ["Which tab holds order and billing communication contacts?", "Use Contacts"],
    ["Can Order Contact default to a new order?", "Order Contact may default"],
    ["May the order contact be changed on a particular order?", "can be changed on that order"],
    ["Who is identified by Billing Contact?", "person for invoices"],
    ["Where does Customer Orders get its Bill To contact?", "derived from Customers"],
    ["Where does Customer Orders get its Ship To contact?", "derived from Customer Ship-Tos"],
    ["Does changing an order contact necessarily change customer master data?", "not necessarily a master-data change"],
  ]],
  ["Customers form — Codes tab", [
    ["Which tab holds customer-level default codes?", "Use Codes"],
    ["Are every site's Codes fields identical?", "depend on local setup"],
    ["Can a ship-to code affect a new order?", "customer or ship-to can influence"],
    ["Should a customer code be checked on the saved order?", "checked independently"],
    ["What information should I capture when a code is rejected?", "field label and error"],
    ["Who should resolve a missing required master-data code?", "master-data or configuration owner"],
    ["Should the chatbot invent a replacement code?", "do not invent a replacement value"],
  ]],
  ["Customers form — CRM and interactions", [
    ["When is the customer CRM tab relevant?", "When CRM is enabled"],
    ["What relationships does the CRM tab show?", "sales team and customer-contact associations"],
    ["Can Customer Interactions be edited in its Customers view?", "display-only"],
    ["Where is the underlying contact activity maintained?", "maintained in Customer Interactions"],
    ["What should be confirmed after Move Prospect To Customer?", "converted prospect contacts"],
    ["Does a sales contact prove that bill-to setup is ready?", "does not itself prove"],
    ["Does an interaction prove the customer is active for orders?", "active customer account is ready"],
  ]],
  ["Customers form — Corporate Customer tab", [
    ["What relationship can Corporate Customer define?", "two-tier relationship"],
    ["What may be linked to a corporate customer?", "subordinate customers"],
    ["What does Corporate Cust identify?", "determines which account is corporate"],
    ["What does Corp. Credit control?", "corporate customer's credit values"],
    ["Is a corporate customer relationship the same as a ship-to?", "not the same as a ship-to"],
    ["What should be confirmed before interpreting corporate balances?", "corporate bill-to or consolidated payment"],
    ["Why does corporate setup matter to invoice ownership?", "before interpreting balances, exposure, or invoice ownership"],
  ]],
  ["Customers form — payment and balance views", [
    ["What information appears on Payment History?", "sales and payment history values"],
    ["Which processes maintain many payment-history amounts?", "normal posted transactions and utilities"],
    ["In which currency are Payment History amounts displayed?", "domestic currency"],
    ["Can this article tell me a customer's Posted Balance?", "current ERP data, not facts stored"],
    ["What does the globe symbol on certain balance fields mean?", "global accumulated values"],
    ["How must a live customer balance be obtained?", "user-authorized value from SyteLine"],
    ["Should available credit be calculated from an old screenshot?", "Do not calculate available credit"],
  ]],
  ["Customers form — optional regional and billing tabs", [
    ["When is EU VAT enabled?", "only when EU reporting is activated"],
    ["What must be validated on EU VAT?", "required VAT and tax information"],
    ["What is the Revision/Pay tab for?", "invoice revision days and pay days"],
    ["Which tab supports multiple customer currencies?", "Currency Codes supports"],
    ["Must every customer use every optional tab?", "not universal steps"],
    ["Does a missing optional tab prove customer setup is incomplete?", "not proof that the customer is incomplete"],
    ["What can explain a missing optional tab?", "configuration, release, customization, or access"],
  ]],
  ["Multi-site customer maintenance", [
    ["From which site is Multi-Site Customers normally maintained?", "at a master site"],
    ["Which form remains the local-site customer form?", "Customers remains"],
    ["Which form can maintain eligible ship-to details across sites?", "Multi-Site Customer Ship-Tos can maintain"],
    ["What prerequisites matter for cross-site ship-to maintenance?", "replication and shared-code prerequisites"],
    ["Are all customer fields identical across sites?", "other details can vary by site"],
    ["What site information should be confirmed before a shared change?", "current site, target site"],
    ["Does a matching customer number grant access to another site?", "Do not infer access"],
  ]],
  ["Customer Hub — search and navigate", [
    ["How can a customer be found in Customer Hub?", "customer name or number"],
    ["Which information does Customer Hub summarize?", "account details, ship-tos"],
    ["Can Customer Hub open a new Customer Order?", "new Customer Order"],
    ["Can Customer Hub open Pricing?", "Pricing"],
    ["Does a Customer Hub tile authorize access to hidden data?", "not authorization"],
    ["Where should hub data be confirmed before acting?", "owning Customers"],
    ["Can Customer Hub differ between installations?", "absent or customized"],
  ]],
  ["First-order readiness checklist", [
    ["Which customer identifiers must be checked before the first order?", "customer number and site"],
    ["Which billed-party details must be checked before order entry?", "bill-to identity and address"],
    ["Which destination details must be checked before order entry?", "ship-to number, address, and contact"],
    ["Which finance defaults must be checked before an order?", "Terms Code and currency"],
    ["Should a customer credit hold be checked before the first order?", "any customer credit hold"],
    ["Why review the saved Customer Orders header?", "defaults can be overridden or recalculated"],
    ["When should order lines be created?", "only after the header is correct"],
  ]],
  ["Why an account may not appear in order entry", [
    ["Which context should I check when a customer is missing in order entry?", "current site"],
    ["Can order-processing status explain a missing customer?", "order-processing status"],
    ["Can form filters hide a customer?", "form filters"],
    ["Can SyteLine permissions affect customer lookup?", "user's SyteLine permissions"],
    ["What should I confirm for a newly created customer?", "saved and refreshed"],
    ["What should I confirm for a multi-site customer lookup?", "required replication completed"],
    ["Which identifier should be used after prospect conversion?", "new customer number"],
  ]],
  ["Why an order shows the wrong customer details", [
    ["What order identifiers should I gather for a default mismatch?", "saved order number"],
    ["Which order fields should be compared with customer master data?", "bill-to, ship-to, terms, tax, and contact"],
    ["Will a customer-master update necessarily correct an old order?", "may not retroactively correct"],
    ["What should I inspect if an order was copied from an estimate?", "inspect its saved fields"],
    ["What should I inspect if an order came from an integration?", "created by an integration"],
    ["Can I assume manual-entry defaults were used for an integrated order?", "rather than assuming defaulting"],
    ["When should an order correction be escalated?", "shipments or invoices already exist"],
  ]],
  ["Security and data boundary for chatbot answers", [
    ["What can the Customer article answer without live ERP access?", "forms, field meanings, and generic workflow"],
    ["Can static Customer guidance supply a specific customer's balance?", "requires a current SyteLine read"],
    ["Which permissions apply to a named customer's invoices?", "logged-in user's effective permissions"],
    ["Does a visible hub summary prove field-level access?", "must not treat a visible hub summary"],
    ["Are customer create and edit permissions separate from reading?", "separate action permissions"],
    ["Do credit changes require authorization and audit?", "changing credit"],
    ["May real customer data be copied into the knowledge article?", "Do not include real customer data"],
  ]],
];

// The 21 substantive groups above produce 147 questions. Add focused screen-map
// questions that cite the overview rather than padding any other section.
groups.push(["Customer screen map", [
  ["Which form owns the customer account and bill-to defaults?", "| Customers |"],
  ["Which form owns delivery-location records?", "| Customer Ship-Tos |"],
  ["Which form gives a customer overview and navigation?", "| Customer Hub |"],
  ["Which form checks the saved first-order customer and ship-to?", "| Customer Orders |"],
  ["Which form supports customer maintenance at a master site?", "| Multi-Site Customers |"],
  ["Which form supports eligible multi-site ship-to maintenance?", "| Multi-Site Customer Ship-Tos |"],
  ["Can the exact Customer screen layout vary?", "exact layout can differ"],
]]);

const existing = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const before = await existing.inspect({ kind: "workbook,sheet,table", maxChars: 1200, tableMaxRows: 2, tableMaxCols: 3 });
console.log("Existing workbook:", before.ndjson);
const oldPreview = await existing.render({ sheetName: "qa_master", range: "A1:D4", scale: 1, format: "png" });
await fs.writeFile(path.join(os.tmpdir(), "customer_before_preview.png"), new Uint8Array(await oldPreview.arrayBuffer()));

const workbook = Workbook.create();
const master = workbook.worksheets.add("qa_master");
const variations = workbook.worksheets.add("question_variations");
const headers = ["qa_id", "domain", "process", "module", "form", "field", "intent", "sub_intent", "canonical_question", "answer", "keywords", "synonyms", "route", "source_reference", "source_section", "version", "site_scope", "security_scope", "approval_status", "approved_by", "effective_date", "active", "last_reviewed_date", "language"];
const variationHeaders = ["qa_id", "variation_id", "question_variation", "language", "source", "validated"];
const rows = [];
const variationRows = [];
const seen = new Set();
const today = "2026-10-08";
let number = 0;
function addVariations(id, question) {
  const lower = question.charAt(0).toLowerCase() + question.slice(1);
  variationRows.push([id, "V1", `In SyteLine, ${lower}`, "en", "editorial_variation", false]);
  variationRows.push([id, "V2", `Could you help me answer this: ${question}`, "en", "editorial_variation", false]);
  variationRows.push([id, "V3", `For this customer process, ${lower}`, "en", "editorial_variation", false]);
}
for (const [heading, items] of groups) {
  const body = sections.get(heading);
  if (!body) throw new Error(`Missing source heading: ${heading}`);
  for (const [question, anchor] of items) {
    const key = question.toLowerCase();
    if (seen.has(key)) throw new Error(`Duplicate question: ${question}`);
    seen.add(key);
    let answer;
    if (anchor.startsWith("| ")) {
      answer = body.split("\n").find(line => line.startsWith(anchor));
      if (answer) answer = answer.split("|").slice(2, 3)[0].trim();
    } else {
      answer = body.replace(/\n/g, " ").split(/(?<=[.!?])\s+/).find(sentence => sentence.includes(anchor));
    }
    if (!answer) throw new Error(`Answer anchor not found: ${heading} / ${anchor}`);
    number += 1;
    const id = `CUST-${String(number).padStart(4, "0")}`;
    const form = heading.includes("Ship-Tos") ? "Customer Ship-Tos" : heading.includes("Hub") ? "Customer Hub" : heading.includes("Multi-site") ? "Multi-Site Customers" : "Customers";
    const intent = /where|which form|which tab|field|indicator|number|code/i.test(question) ? "HELP_FIELD" : /how|when|should|can|why|before|after/i.test(question) ? "HELP_PROCESS" : "HELP_GENERIC";
    rows.push([id, "PROSPECT_TO_CASH", "Customer-to-Cash", "customer", form, "", intent, "", question, answer, heading.toLowerCase().replace(/[—–]/g, ","), "", "FAST_QA", "customer.md", `Customer Module — Customer-to-Cash Form and Screen Guide > ${heading}`, "General CSI/SyteLine; Infor 2026.10 reference", "Verify current site", "Effective SyteLine permissions", "IN_REVIEW", "Pending local SyteLine SME approval", today, false, "", "en"]);
    addVariations(id, question);
  }
}
// Keep the eight pre-existing questions while their answers and section paths
// move to the expanded source. Their old auto-approval was not SME approval.
const legacy = [
  ["KB-0018", "What is a customer record and what forms does it use?", "A Customer record identifies the trading account used for orders, billing, shipping, and receivables. Customers owns the account and Customer Ship-Tos owns delivery locations.", "Customer screen map"],
  ["KB-0019", "How are ship-to locations managed for a customer?", "Customer Ship-Tos creates or reviews a delivery location and its address and codes. A customer can have multiple ship-to locations.", "Customer Ship-Tos — create a destination"],
  ["KB-0020", "How do I set up and validate a new customer?", "Search for an existing account, create and save the Customers record, confirm its number and bill-to details, add required ship-tos, then check the saved first order's defaults.", "Customers form — create and save the account"],
  ["KB-0021", "What should I review before entering a customer order?", "Verify the customer number and site, bill-to, ship-to, Terms Code, currency, tax and shipping defaults, warehouse or ship site if applicable, and any customer credit hold.", "First-order readiness checklist"],
  ["KB-0022", "What is the difference between a customer's credit and balance?", "Credit Limit and Credit Hold are customer controls. Posted Balance and On Order Balance are current ERP data that require an authorized SyteLine read.", "Customers form — payment and balance views"],
  ["KB-0023", "How does a customer-level Credit Hold work?", "Customer-level Credit Hold blocks shipments for that customer but does not set the Credit Hold field on each individual customer order.", "Customers form — Credit tab"],
  ["KB-0024", "What should I check if an order shows the wrong address for a customer?", "Identify the saved order number, customer number, Ship To number, and site. Compare the order's bill-to and ship-to with current customer and ship-to records.", "Why an order shows the wrong customer details"],
  ["KB-0025", "What should I do if I can't select a customer in the system?", "Check the current site, customer identifier, order-processing status, filters, and SyteLine permissions. Confirm a new record was saved and refreshed.", "Why an account may not appear in order entry"],
];
for (const [id, question, answer, heading] of legacy.reverse()) {
  rows.unshift([id, "PROSPECT_TO_CASH", "Customer-to-Cash", "customer", "", "", "HELP_PROCESS", "", question, answer, heading.toLowerCase(), "", "FAST_QA", "customer.md", `Customer Module — Customer-to-Cash Form and Screen Guide > ${heading}`, "General CSI/SyteLine; Infor 2026.10 reference", "Verify current site", "Effective SyteLine permissions", "IN_REVIEW", "Pending local SyteLine SME approval", today, false, "", "en"]);
  const lower = question.charAt(0).toLowerCase() + question.slice(1);
  variationRows.unshift([id, "V3", `For this customer process, ${lower}`, "en", "editorial_variation", false]);
  variationRows.unshift([id, "V2", `Could you help me answer this: ${question}`, "en", "editorial_variation", false]);
  variationRows.unshift([id, "V1", `In SyteLine, ${lower}`, "en", "editorial_variation", false]);
}
if (rows.length < 150) throw new Error(`Only ${rows.length} Q&A rows generated`);
master.getRange(`A1:X${rows.length + 1}`).values = [headers, ...rows];
variations.getRange(`A1:F${variationRows.length + 1}`).values = [variationHeaders, ...variationRows];
for (const sheet of [master, variations]) {
  sheet.getUsedRange().format.font = { name: "Arial", size: 10 };
  sheet.getRange(sheet === master ? "A1:X1" : "A1:F1").format = { fill: "#1F4E78", font: { name: "Arial", bold: true, color: "#FFFFFF", size: 10 } };
  sheet.freezePanes.freezeRows(1);
}
master.getRange(`I1:I${rows.length + 1}`).format.columnWidth = 52;
master.getRange(`J1:J${rows.length + 1}`).format.columnWidth = 80;
variations.getRange(`C1:C${variationRows.length + 1}`).format.columnWidth = 70;
workbook.recalculate();
console.log(`Generated ${rows.length} canonical Q&As and ${variationRows.length} variation rows.`);
console.log((await workbook.inspect({ kind: "region", sheetId: "qa_master", range: "A1:J3", maxChars: 1800 })).ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 20 }, maxChars: 1000 });
console.log("Formula-error scan:", errors.ndjson);
const preview = await workbook.render({ sheetName: "qa_master", range: "A1:D5", scale: 1, format: "png" });
await fs.writeFile(path.join(os.tmpdir(), "customer_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Saved ${outputPath}`);
process.exitCode = 0;
