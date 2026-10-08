// Rebuild the new manual-grounded Pricing Q&A without touching other modules.
import fs from "node:fs/promises";
import path from "node:path";
import {FileBlob, SpreadsheetFile} from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const articlePath = path.join(root, "data/knowledge/prospect_to_cash/pricing.md");
const workbookPath = path.join(root, "data/qa/prospect_to_cash/pricing.xlsx");
const previewDir = path.join(root, "tmp/pdfs");
await fs.mkdir(previewDir, {recursive: true});

const article = await fs.readFile(articlePath, "utf8");
const sections = [];
for (const block of article.split(/^## /m).slice(1)) {
  const heading = block.slice(0, block.indexOf("\n")).trim();
  if (heading === "Document Metadata") continue;
  const pages = block.match(/^\*\*Guide pages:\*\* ([^\n]+)/m)?.[1]?.trim();
  const qa = [...block.matchAll(/^\d+\. \*\*(.+?\?)\*\* (.+)$/gm)]
    .map(([, question, answer]) => [question.trim(), answer.trim()]);
  if (!pages || qa.length !== 5) throw new Error(`${heading}: expected pages and five Q&A`);
  sections.push({heading, pages, qa});
}
if (sections.length !== 33) throw new Error(`Expected 33 Pricing sections, got ${sections.length}`);

const formByHeading = new Map([
  ["Pricing form map", "Multiple Pricing Forms"],
  ["Unit Price decision sequence", "Customer Order Lines"],
  ["Promotion in base-price calculation", "Customer Order Lines"],
  ["Customer contract matching order", "Customer Contracts"],
  ["Contract effective-date wording", "Customer Contract Prices"],
  ["Guaranteed Contract Price", "Customer Contract Prices"],
  ["Customer contract quantity breaks", "Customer Contract Prices"],
  ["Price Matrix matching", "Price Matrix Table"],
  ["Item Pricing fallback", "Item Pricing"],
  ["Customer currency pricing", "Item Pricing"],
  ["Non-inventory price entry", "Customer Order Lines"],
  ["Discounts form setup", "Discounts"],
  ["Sales Disc line override", "Customer Order Lines"],
  ["Customer Contracts creation", "Customer Contracts"],
  ["Customer Contract Prices entry", "Customer Contract Prices"],
  ["Contract manufacturing end users", "Customer Contracts"],
  ["Price Promotions and Rebates setup", "Price Promotions and Rebates"],
  ["Promotion eligibility on an order line", "Customer Order Lines"],
  ["Promotion application on Customer Order Lines", "Customer Order Lines"],
  ["Promotion exclusions and copying", "Price Promotions and Rebates"],
  ["Rebate program prerequisites", "Price Promotions and Rebates"],
  ["Rebates at invoice generation", "Earned Rebates"],
  ["Earned rebate valuation", "Earned Rebates"],
  ["Earned Rebates inquiry and hold", "Earned Rebates"],
  ["Earned Rebate Credit Workbench", "Earned Rebate Credit Workbench"],
  ["Rebate application and expiry", "Earned Rebates"],
  ["Surcharge purpose and formula", "Item Content References"],
  ["Surcharge accounts and tax setup", "Accounts Receivable Parameters"],
  ["Item content and exchange setup", "Item Content References"],
  ["Surcharge references and customer rules", "Customer Surcharge Rules"],
  ["Copy Orders and Estimates pricing handoff", "Copy Orders and Estimates"],
  ["Price Adjustment Invoice eligibility", "Price Adjustment Invoice"],
  ["Price Adjustment Invoice steps and evidence", "Price Adjustment Invoice"],
]);
if (formByHeading.size !== sections.length) throw new Error("Missing form mapping");

const book = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const master = book.worksheets.getItem("qa_master");
const variations = book.worksheets.getItem("question_variations");
console.log((await book.inspect({kind:"workbook,sheet,table",maxChars:900,tableMaxRows:2,tableMaxCols:3})).ndjson);
const before = await book.render({sheetName:"qa_master",range:"A1:D4",scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"pricing_qa_before.png"),new Uint8Array(await before.arrayBuffer()));
const legacyRows = master.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("PRIC-"));
const legacyVariations = variations.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("PRIC-"));
const seen = new Set(legacyRows.map(row => String(row[8]).trim().toLowerCase()));
const newRows = [];
const newVariations = [];
let serial = 0;
for (const {heading, pages, qa} of sections) {
  for (const [question, answer] of qa) {
    const key = question.toLowerCase();
    if (seen.has(key)) throw new Error(`Duplicate Pricing question: ${question}`);
    seen.add(key);
    const id = `PRIC-${String(++serial).padStart(4,"0")}`;
    const form = formByHeading.get(heading);
    const intent = /which|where|field|form|what is/i.test(question) ? "HELP_FIELD" : "HELP_PROCESS";
    newRows.push([id,"PROSPECT_TO_CASH","Customer-to-Cash","pricing",form,"",intent,"",question,answer,heading.toLowerCase(),"","FAST_QA","pricing.md",`Pricing and Discount Module > ${heading}`,`Infor SyteLine Customer Service User Guide 9.01.x, printed pp. ${pages}`,"Verify current site","Effective SyteLine permissions","IN_REVIEW","Pending local SyteLine SME approval","2026-10-08",false,"","en"]);
    const lower = question[0].toLowerCase()+question.slice(1);
    newVariations.push([id,"V1",`In SyteLine Pricing, ${lower}`,"en","editorial_variation",false]);
    newVariations.push([id,"V2",`Could you explain this Pricing question: ${question}`,"en","editorial_variation",false]);
    newVariations.push([id,"V3",`For the ${form} screen, ${lower}`,"en","editorial_variation",false]);
  }
}
if (newRows.length !== 165) throw new Error(`Expected 165 new Pricing Q&A, got ${newRows.length}`);
for (const row of legacyRows) {
  row[3] = "pricing";
  row[18] = "IN_REVIEW";
  row[19] = "Pending 9.01.x guide and local SyteLine SME review";
  row[21] = false;
}
const rows = [...legacyRows,...newRows];
const vars = [...legacyVariations,...newVariations];
master.getRange(`A2:X${rows.length+1}`).values = rows;
variations.getRange(`A2:F${vars.length+1}`).values = vars;
master.getRange(`A1:A${rows.length+1}`).format.columnWidth = 17;
master.getRange(`D1:E${rows.length+1}`).format.columnWidth = 24;
master.getRange(`I1:I${rows.length+1}`).format.columnWidth = 56;
master.getRange(`J1:J${rows.length+1}`).format.columnWidth = 84;
master.getRange(`I2:J${rows.length+1}`).format.wrapText = true;
master.getRange(`A2:X${rows.length+1}`).format.rowHeight = 34;
master.getRange(`O1:P${rows.length+1}`).format.columnWidth = 54;
variations.getRange(`C1:C${vars.length+1}`).format.columnWidth = 76;
book.recalculate();
console.log(`rows=${rows.length}; new=${newRows.length}; variations=${vars.length}`);
console.log((await book.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const after = await book.render({sheetName:"qa_master",range:`I${legacyRows.length+2}:J${legacyRows.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"pricing_qa_after.png"),new Uint8Array(await after.arrayBuffer()));
const variantPreview = await book.render({sheetName:"question_variations",range:`A${legacyVariations.length+2}:D${legacyVariations.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"pricing_variations_after.png"),new Uint8Array(await variantPreview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(workbookPath);
console.log(`Saved ${workbookPath}`);
