// Rebuild only the manual-grounded Credit Q&A; preserve prior rows for review.
import fs from "node:fs/promises";
import path from "node:path";
import {FileBlob, SpreadsheetFile} from "@oai/artifact-tool";

const root = path.resolve(import.meta.dirname, "..");
const articlePath = path.join(root, "data/knowledge/prospect_to_cash/credit.md");
const workbookPath = path.join(root, "data/qa/prospect_to_cash/credit.xlsx");
const approvalNote = "User-authorized automatic approval (SME review pending)";
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
  if (!pages || qa.length !== 5) throw new Error(`${heading}: expected pages and five Q&A; found ${qa.length}`);
  sections.push({heading, pages, qa});
}
if (sections.length !== 31) throw new Error(`Expected 31 Credit sections, got ${sections.length}`);

const formByHeading = new Map([
  ["Credit form map", "Multiple Credit Forms"],
  ["Customer-level credit hold", "Customers"],
  ["Order-level credit hold", "Customer Orders"],
  ["Red X hold indicator", "Customers / Customer Orders"],
  ["Automatic over-limit hold activation", "Accounts Receivable Parameters"],
  ["Missing automatic hold reason", "Accounts Receivable Parameters"],
  ["New line credit evaluation", "Customer Order Lines"],
  ["Allow Over Credit Limit selected", "Customer Order Lines"],
  ["Allow Over Credit Limit cleared", "Customer Order Lines"],
  ["Existing line changes", "Customer Order Lines"],
  ["Corporate customer exposure", "Customer Orders"],
  ["Held-order cross-references", "Customer Order Lines"],
  ["EDI credit validation", "EDI Customer Profiles"],
  ["EDI post-then-hold alternative", "EDI Customer Profiles"],
  ["Replicated credit limits", "Customers"],
  ["Multi-site On Order Balance", "Customers"],
  ["Originating-site hold control", "Customer Orders"],
  ["Utility across sites", "Order Credit Hold Change Utility"],
  ["Manually placing a customer hold", "Customers"],
  ["Manually placing an order hold", "Customer Orders"],
  ["Releasing a customer hold", "Customers"],
  ["Releasing an order hold", "Customer Orders"],
  ["Credit-field authorization", "Users / Groups"],
  ["Utility scope and aging inputs", "Order Credit Hold Change Utility"],
  ["Utility Hold selection", "Order Credit Hold Change Utility"],
  ["Utility Release selection", "Order Credit Hold Change Utility"],
  ["Blank customer aging thresholds", "Customers"],
  ["Shipping consequence and hold level", "Customers / Customer Orders"],
  ["Order-entry warning interpretation", "Customer Order Lines"],
  ["Credit diagnostic decision path", "Multiple Credit Forms"],
  ["Guide and live-data boundary", "Multiple Credit Forms"],
]);
if (formByHeading.size !== sections.length || sections.some(s => !formByHeading.has(s.heading))) {
  throw new Error("Missing Credit form mapping");
}

const book = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const master = book.worksheets.getItem("qa_master");
const variations = book.worksheets.getItem("question_variations");
console.log((await book.inspect({kind:"workbook,sheet,table",maxChars:900,tableMaxRows:2,tableMaxCols:3})).ndjson);
const before = await book.render({sheetName:"qa_master",range:"A1:D4",scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"credit_qa_before.png"),new Uint8Array(await before.arrayBuffer()));
const legacyRows = master.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("CRED-"));
const legacyVariations = variations.getUsedRange().values.slice(1).filter(row => !String(row[0]).startsWith("CRED-"));
const seen = new Set(legacyRows.map(row => String(row[8]).trim().toLowerCase()));
const newRows = [];
const newVariations = [];
let serial = 0;
for (const {heading, pages, qa} of sections) {
  for (const [question, answer] of qa) {
    const key = question.toLowerCase();
    if (seen.has(key)) throw new Error(`Duplicate Credit question: ${question}`);
    seen.add(key);
    const id = `CRED-${String(++serial).padStart(4,"0")}`;
    const form = formByHeading.get(heading);
    const intent = /which|where|field|form|what is/i.test(question) ? "HELP_FIELD" : "HELP_PROCESS";
    newRows.push([id,"PROSPECT_TO_CASH","Customer-to-Cash","credit",form,"",intent,"",question,answer,heading.toLowerCase(),"","FAST_QA","credit.md",`Credit Review and Credit Hold Module > ${heading}`,`Infor SyteLine Customer Service User Guide 9.01.x, printed pp. ${pages}`,"Verify current site","Effective SyteLine permissions","APPROVED",approvalNote,"2026-10-08",true,"","en"]);
    const lower = question[0].toLowerCase()+question.slice(1);
    newVariations.push([id,"V1",`In SyteLine Credit, ${lower}`,"en","editorial_variation",false]);
    newVariations.push([id,"V2",`Could you explain this Credit question: ${question}`,"en","editorial_variation",false]);
    newVariations.push([id,"V3",`For the ${form} screen, ${lower}`,"en","editorial_variation",false]);
  }
}
if (newRows.length !== 155) throw new Error(`Expected 155 new Credit Q&A, got ${newRows.length}`);
for (const row of legacyRows) {
  row[3] = "credit";
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
master.getRange(`D1:E${rows.length+1}`).format.columnWidth = 24;
master.getRange(`I1:I${rows.length+1}`).format.columnWidth = 56;
master.getRange(`J1:J${rows.length+1}`).format.columnWidth = 84;
master.getRange(`I2:J${rows.length+1}`).format.wrapText = true;
master.getRange(`A2:X${rows.length+1}`).format.rowHeight = 34;
master.getRange(`O1:P${rows.length+1}`).format.columnWidth = 54;
master.getRange(`S1:S${rows.length+1}`).format.columnWidth = 18;
master.getRange(`T1:T${rows.length+1}`).format.columnWidth = 60;
master.getRange(`U1:U${rows.length+1}`).format.columnWidth = 17;
variations.getRange(`C1:C${vars.length+1}`).format.columnWidth = 76;
book.recalculate();
console.log(`rows=${rows.length}; new=${newRows.length}; variations=${vars.length}`);
console.log((await book.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},maxChars:500})).ndjson);
const after = await book.render({sheetName:"qa_master",range:`I${legacyRows.length+2}:J${legacyRows.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"credit_qa_after.png"),new Uint8Array(await after.arrayBuffer()));
const approvalPreview = await book.render({sheetName:"qa_master",range:`S${legacyRows.length+2}:V${legacyRows.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"credit_approval_after.png"),new Uint8Array(await approvalPreview.arrayBuffer()));
const variantPreview = await book.render({sheetName:"question_variations",range:`A${legacyVariations.length+2}:D${legacyVariations.length+5}`,scale:1,format:"png"});
await fs.writeFile(path.join(previewDir,"credit_variations_after.png"),new Uint8Array(await variantPreview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(workbookPath);
console.log(`Saved ${workbookPath}`);
