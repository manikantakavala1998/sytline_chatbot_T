// Rebuild one manual-grounded Invoice or Payment workbook without touching other modules.
import fs from "node:fs/promises";
import path from "node:path";
import {FileBlob, SpreadsheetFile} from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const moduleName = process.argv[2];
const previewOnly = process.argv.includes("--preview");
const approvalNote = "User-authorized automatic approval (SME review pending)";
const configs = {
  invoice: {
    prefix: "INV",
    expected: 31,
    title: "Invoice and Credit Memo Module",
    source: "Infor SyteLine Customer Service User Guide 9.01.x",
    formGroups: [
      ["Multiple Invoice Forms", ["Invoice process boundary"]],
      ["Order Invoicing/Credit Memo", ["Order Invoicing/Credit Memo screen","Shipped and uninvoiced eligibility","Standard invoicing effects","Posting or printing error","Credit Memo mode","Apply To Invoice reference","Returned-item credit sequence","Regular and blanket header amounts","Foreign-currency debt","Packing-slip invoice option","Reprint Options","Reprint data sources","Progressive billing invoice selection"]],
      ["Invoices, Debit and Credit Memos", ["Manual invoice boundary"]],
      ["Billing Terms", ["Advanced Terms","Multiple due-date terms"]],
      ["Multi-Lingual Order Invoice", ["Foreign-language printing"]],
      ["Customer Order Lines / Customer Order Blanket Releases", ["Invoice Hold field"]],
      ["Background Task History", ["Background Task History"]],
      ["Order Shipments", ["Shipment approval and invoice gate"]],
      ["Customers", ["Customer consolidated defaults"]],
      ["Customer Orders", ["Customer Orders consolidated settings"]],
      ["Customer Order Lines / Customer Order Blanket Releases", ["Line and blanket-release consolidation"]],
      ["Consolidated Invoice Generation", ["Consolidated Invoice Generation","Updating pending consolidated invoices"]],
      ["Consolidated Invoices Workbench", ["Consolidated Invoices Workbench","Invalid pending consolidated records","Consolidated tax and charge review"]],
      ["Multiple Consolidated Invoice Forms", ["Consolidated invoice overview","Consolidated-route restrictions"]],
    ],
    legacy: {
      "KB-0079": ["Order Invoicing/Credit Memo screen", "Open Order Invoicing/Credit Memo, select Invoice, enter the intended criteria, and Process eligible shipped, unheld quantity."],
      "KB-0080": ["Order Invoicing/Credit Memo screen", "On Order Invoicing/Credit Memo, select Invoice, specify appropriate values, and Process after verifying shipment and Invoice Hold."],
      "KB-0081": ["Multiple due-date terms", "A multiple-due-date terms code creates due-date records and printed due amounts; customer-order credits use the separate Credit Memo run."],
      "KB-0082": ["Returned-item credit sequence", "For returned items, post the return quantity through a material/ship transaction and then process the credit memo; separate non-order invoices use Invoices, Debit and Credit Memos."],
      "KB-0083": ["Shipped and uninvoiced eligibility", "Check shipped versus invoiced quantity, Invoice Hold, the billing route, and the invoicing task result before deciding why no invoice was created."],
    },
  },
  payment: {
    prefix: "PAY",
    expected: 33,
    title: "Payment and Accounts Receivable Module",
    source: "Infor SyteLine Financials User Guide 9.01.x",
    formGroups: [
      ["Multiple A/R Forms", ["Invoice-to-A/R handoff"]],
      ["A/R Payments", ["A/R Payments purpose","Customer and payment identity","Receipt, due, and deposit dates","Reference, description, bank, and amount","Save, distribute, then post","Open payment and Open Credit","Payment currency conversion","Credit-card payment controls","Open payment tied to an order","Reversing a posted payment"]],
      ["A/R Payment Distributions", ["Automatically generated distributions","Manual distribution entry","Invoice distribution fields","Finance-charge and non-A/R destinations","Discounts and allowances","Multiple-due-date payment","Multi-site application boundary"]],
      ["A/R Quick Payment Application", ["A/R Quick Payment Application purpose","Quick Payment grid","Quick Payment open remainder","Reapply open payment in Quick Payment","Quick Payment limitations"]],
      ["A/R Payment Posting", ["A/R Payment Transaction Report","A/R Payment Posting Commit","A/R posting account prerequisite"]],
      ["A/R Posted Transactions Detail / AR DIST", ["A/R Distribution Journal"]],
      ["Returned Checks", ["Returned checks"]],
      ["Chargebacks", ["Chargebacks"]],
      ["A/R Payment Import Mappings", ["Electronic A/R Payment Import"]],
      ["A/R Payment Import Workbench", ["Import Workbench validation"]],
      ["A/R Direct Debit Posting", ["A/R direct debit"]],
      ["Accounts Receivable Aging Report", ["Accounts Receivable Aging Report"]],
    ],
    legacy: {
      "KB-0095": ["Invoice-to-A/R handoff", "A/R records the posted invoice, customer receipt, application, and remaining open amount as separate financial events."],
      "KB-0096": ["Invoice-to-A/R handoff", "No. Shipment and order status do not establish whether an invoice was posted, a payment applied, or a balance settled."],
      "KB-0097": ["Save, distribute, then post", "Enter the receipt on A/R Payments, save it, distribute to the intended open items, review the transaction report, and post with authorization."],
      "KB-0098": ["Open payment and Open Credit", "Check whether it was posted as Open Credit; reapply the open receipt to the intended invoice or finance charge through the documented A/R process."],
      "KB-0099": ["Accounts Receivable Aging Report", "The report shows customer-balance status and helps identify past-due invoices using selected report parameters."],
      "KB-0100": ["Accounts Receivable Aging Report", "Choose the intended report parameters, Preview if needed, then Print; the default selection covers all customers."],
      "KB-0101": ["A/R Distribution Journal", "Verify the posted receipt in A/R Posted Transactions Detail and check its distributions and the invoice's remaining open amount."],
      "KB-0102": ["Invoice distribution fields", "Compare the invoice's remaining balance with Dist Amount, discounts, allowances, and any open payment before concluding there is a mismatch."],
    },
  },
};
const config = configs[moduleName];
if (!config) throw new Error("Usage: node build_invoice_payment_qa.mjs invoice|payment [--preview]");

const articlePath = path.join(root, "data/knowledge/prospect_to_cash", `${moduleName}.md`);
const workbookPath = path.join(root, "data/qa/prospect_to_cash", `${moduleName}.xlsx`);
const previewDir = path.join(root, "tmp/pdfs");
await fs.mkdir(previewDir, {recursive:true});

const article = await fs.readFile(articlePath, "utf8");
const sections = [];
for (const block of article.split(/^## /m).slice(1)) {
  const heading = block.slice(0, block.indexOf("\n")).trim();
  if (heading === "Document Metadata") continue;
  const pages = block.match(/^\*\*Guide pages:\*\* ([^\n]+)/m)?.[1]?.trim();
  const qa = [...block.matchAll(/^\d+\. \*\*(.+?\?)\*\* (.+)$/gm)]
    .map(([,question,answer]) => [question.trim(),answer.trim()]);
  if (!pages || qa.length !== 5) throw new Error(`${moduleName}: ${heading} has ${qa.length} questions or no source pages`);
  sections.push({heading,pages,qa});
}
if (sections.length !== config.expected) throw new Error(`${moduleName}: expected ${config.expected} sections, got ${sections.length}`);
const formByHeading = new Map(config.formGroups.flatMap(([form,headings]) => headings.map(heading => [heading,form])));
if (formByHeading.size !== sections.length || sections.some(({heading}) => !formByHeading.has(heading))) {
  throw new Error(`${moduleName}: a heading lacks a form mapping`);
}
const sectionByHeading = new Map(sections.map(section => [section.heading, section]));
const book = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const master = book.worksheets.getItem("qa_master");
const variations = book.worksheets.getItem("question_variations");
console.log((await book.inspect({kind:"workbook,sheet,table",maxChars:800,tableMaxRows:2,tableMaxCols:3})).ndjson);
const before = await book.render({sheetName:"qa_master",range:"A1:D4",scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,`${moduleName}_qa_before.png`),new Uint8Array(await before.arrayBuffer()));
const statusBefore = await book.render({sheetName:"qa_master",range:"S1:V4",scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,`${moduleName}_approval_before.png`),new Uint8Array(await statusBefore.arrayBuffer()));
if (previewOnly) {
  console.log(`Previewed ${moduleName} source workbook; no workbook edit`);
  process.exit(0);
}

const legacyRows = master.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith(`${config.prefix}-`));
const legacyVariations = variations.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith(`${config.prefix}-`));
const seen = new Set(legacyRows.map(row => String(row[8]).trim().toLowerCase()));
const newRows = [];
const newVariations = [];
let serial = 0;
for (const {heading,pages,qa} of sections) {
  const form = formByHeading.get(heading);
  for (const [question,answer] of qa) {
    const key = question.toLowerCase();
    if (seen.has(key)) throw new Error(`${moduleName}: duplicate question: ${question}`);
    seen.add(key);
    const id = `${config.prefix}-${String(++serial).padStart(4,"0")}`;
    const intent = /which|where|field|form|what is/i.test(question) ? "HELP_FIELD" : "HELP_PROCESS";
    newRows.push([id,"PROSPECT_TO_CASH","Customer-to-Cash",moduleName,form,"",intent,"",question,answer,heading.toLowerCase(),"","FAST_QA",`${moduleName}.md`,`${config.title} > ${heading}`,`${config.source}, printed pp. ${pages}`,"Verify current site","Effective SyteLine permissions","APPROVED",approvalNote,"2026-10-08",true,"","en"]);
    const lower = question[0].toLowerCase()+question.slice(1);
    newVariations.push([id,"V1",`In SyteLine ${moduleName}, ${lower}`,"en","editorial_variation",false]);
    newVariations.push([id,"V2",`Could you explain this ${moduleName} question: ${question}`,"en","editorial_variation",false]);
    newVariations.push([id,"V3",`For the ${form} screen, ${lower}`,"en","editorial_variation",false]);
  }
}
if (newRows.length !== sections.length*5) throw new Error("Unexpected question count");
for (const row of legacyRows) {
  const detail = config.legacy[String(row[0])];
  if (!detail) throw new Error(`${moduleName}: legacy row ${row[0]} needs source review`);
  const [heading,answer] = detail;
  const section = sectionByHeading.get(heading);
  row[3] = moduleName;
  row[4] = formByHeading.get(heading);
  row[9] = answer;
  row[13] = `${moduleName}.md`;
  row[14] = `${config.title} > ${heading}`;
  row[15] = `${config.source}, printed pp. ${section.pages}`;
  row[18] = "APPROVED";
  row[19] = approvalNote;
  row[20] = "2026-10-08";
  row[21] = true;
}
const rows = [...legacyRows,...newRows];
const vars = [...legacyVariations,...newVariations];
master.getRange(`A2:X${rows.length+1}`).values = rows;
variations.getRange(`A2:F${vars.length+1}`).values = vars;
master.getRange(`A1:A${rows.length+1}`).format.columnWidth = 17;
master.getRange(`D1:E${rows.length+1}`).format.columnWidth = 26;
master.getRange(`I1:I${rows.length+1}`).format.columnWidth = 58;
master.getRange(`J1:J${rows.length+1}`).format.columnWidth = 88;
master.getRange(`I2:J${rows.length+1}`).format.wrapText = true;
master.getRange(`A2:X${rows.length+1}`).format.rowHeight = 48;
master.getRange(`O1:P${rows.length+1}`).format.columnWidth = 56;
master.getRange(`S1:S${rows.length+1}`).format.columnWidth = 18;
master.getRange(`T1:T${rows.length+1}`).format.columnWidth = 60;
master.getRange(`U1:U${rows.length+1}`).format.columnWidth = 17;
variations.getRange(`C1:C${vars.length+1}`).format.columnWidth = 76;
book.recalculate();
console.log(`${moduleName}: rows=${rows.length}; new=${newRows.length}; variations=${vars.length}`);
console.log((await book.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const after = await book.render({sheetName:"qa_master",range:`I${legacyRows.length+2}:J${legacyRows.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,`${moduleName}_qa_after.png`),new Uint8Array(await after.arrayBuffer()));
const approval = await book.render({sheetName:"qa_master",range:`S${legacyRows.length+2}:V${legacyRows.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,`${moduleName}_approval_after.png`),new Uint8Array(await approval.arrayBuffer()));
const variation = await book.render({sheetName:"question_variations",range:`A${legacyVariations.length+2}:D${legacyVariations.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,`${moduleName}_variations_after.png`),new Uint8Array(await variation.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(workbookPath);
console.log(`Saved ${workbookPath}`);
