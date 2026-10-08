# Project File Guide

> Living index of every file in this repository: what it is, why it exists, and what it's for.
> Update this file whenever a new file/folder is added to the project — treat it as mandatory
> bookkeeping for every future phase, not a one-time document. New entries go under the section
> matching where the file lives; add new sections as new top-level folders appear.

---

## Root files (Phase 1)

### `requirements.txt`
**What it is**: the single list of every Python package the app needs, one file for the whole
project (per the user's request — no separate per-module requirements files).

**Why it exists**: so `uv pip install -r requirements.txt` (or plain `pip`) sets up a working
environment in one step. Grouped into Core RAG / Data processing / API-web / Utilities, with a
note on what's deliberately left out for now (PDF/DOCX/PPTX/OCR libraries — added later when the
full document-ingestion step needs them, to avoid a slow, heavy install before it's needed).

**Purpose going forward**: add a package here the moment code needs it; don't let an import exist
in the codebase that isn't listed here.

**Phase 3 addition**: `langgraph` is the orchestration engine and `pytest` runs the deterministic
security/classification/graph test suite.

### `.gitignore`
**What it is**: tells git which files/folders to never track — `.venv/`, `.env` (real secrets),
`__pycache__/`, generated data, runtime `logs/`, editor folders.

**Why it exists**: keeps the real OpenAI key and other machine-specific junk out of version
control from the very first commit.

### `.env.example`
**What it is**: a template listing every setting the app reads from the environment, with blank
or safe default values. Safe to commit.

**Why it exists**: shows anyone setting up the project which settings exist and what to fill in,
without exposing real secrets.

**Phase 3 addition**: documents the orchestration model enable switch and timeout
(`ORCHESTRATOR_MODEL`, `ORCHESTRATOR_LLM_ENABLED`, `ORCHESTRATOR_TIMEOUT_SECONDS`).

### `.env`
**What it is**: the real settings file for this machine, including the real `OPENAI_API_KEY`.
**Not committed to git** (see `.gitignore`).

**Why it exists**: `backend/app/config.py` reads this file on startup and refuses to start if
`OPENAI_API_KEY` is blank. The user fills in the real key here.

### `launcher.py`
**What it is**: the one-command way to start the server — `python launcher.py`.

**Why it exists**: matches the pattern from `REPLICA_BUILD_PROMPT.md` (a single entry point that
starts uvicorn), so starting the app doesn't require remembering a long uvicorn command.

### `docker-compose.yml`
**What it is**: this project's own dedicated infrastructure (master prompt §14) — Milvus
standalone + etcd + MinIO + Attu, plus Redis, all named `ptc-*` and running on non-default host
ports (Milvus client `19531`, Attu `3001`, Redis `6380`, MinIO `19000`/`19001`) so this project
never shares state or collides with any other project's containers on the same machine. Compose
project name is `ptc-chatbot`. Start with `docker compose up -d`, browse vectors at
`http://localhost:3001` (Attu) once `ptc-milvus` reports healthy.

**Why it exists**: initially reused an already-running Milvus from a different, older project
(`PycharmProjects/DeepChatbot/`) to answer "let me see the vectors" quickly — the user then
explicitly asked for full separation, so this dedicated stack replaced that the same day
(2026-09-24). `backend/app/config.py`'s `milvus_uri`/`redis_port` defaults point here.

**Added 2026-09-24 — `postgres` (`ptc-postgres`, `postgres:16-alpine`, host port `5433`)**: stores
conversation history (see `history/store.py`). Port 5433 (not 5432) so it never collides with a
Postgres already installed on the machine; data lives in the `ptc_postgres_data` volume. DB name,
user and password come from the `POSTGRES_*` variables (local-dev defaults if unset).

---

## `backend/app/` (Phase 1 — foundation)

### `config.py`
**What it is**: loads every setting from `.env` into one `settings` object, and fails immediately
on startup if `OPENAI_API_KEY` is missing — never fails later mid-conversation.

### `main.py`
**What it is**: the FastAPI app itself. It initializes Fast Q&A and Markdown RAG during startup,
wires in the API routes, serves the frontend, and adds request middleware that assigns an
`X-Request-ID`. Every HTTP start, completion, duration, status, and unhandled error is logged to
the terminal and central log file with that ID. Phase 3 also compiles the LangGraph workflow at
startup so routing errors fail during startup rather than during the first user request.

### `api/routes.py`
**What it is**: `/health`, `/api/info`, and the working `/chat` orchestration route. A chat turn
flows through the trusted Phase 2 session/context/base-permission boundary and then invokes the
Phase 3 LangGraph. (2026-09-24: `/chat` also loads the conversation's recent turns from Postgres
before the graph and saves the question + answer after it, returning `message_id` and
`resolved_query`; new `/api/history/sessions[/{id}]` GET/DELETE and
`/api/history/messages/{id}/rating` PUT endpoints, all scoped to the trusted user.)
The graph owns security, scope, ambiguity, transformation, classification,
route selection, Fast Q&A, and Markdown RAG execution. Each important transition is logged as a
named event tied to the request ID, without writing the raw question or answer into logs.
**2026-09-30 — parallel users**: `/chat` is a plain `def` (was `async def`), so FastAPI runs each
question on its worker threads (40 by default) instead of on the single event loop. Measured before:
6 users at once all waited 47 s and even `/health` froze for 46 s; after: 12 users at once all
answered within 17 s, `/health` stayed instant, 0 errors, no mixed sessions. The Postgres pool
(`history/store.py`) grew from 5 to `POSTGRES_POOL_MAX_SIZE` (20) connections.

### `security/permission_seam.py` — retired in Phase 2
Was a stand-in permission check that always said "allowed". Removed once
`authorization/resolver.py` (below) gave it a real replacement, exactly as planned — Phase 2's
job was always to swap the mock seam for real plumbing, not add a check for the first time.

### `security/bootstrap.py`
**What it is**: Security Bootstrap (master prompt §2.1/§18) — establishes who the current user is
from their SyteLine session, before anything else runs. No separate chatbot login. Currently
backed by the mock `session_context.py` (below); raises `InvalidSessionError` on a missing/blank
session token, which `/chat` turns into a `BLOCKED` response.

### `models/embeddings.py`
**What it is**: loads the embedding model (`BAAI/bge-base-en-v1.5`) exactly once and shares it —
loading it is slow, so both Q&A search now and Markdown search later reuse this one instance.
Has two functions: `embed()` for passage/document-side text, `embed_query()` for the user's
question — bge-base-en-v1.5 expects a different instruction prefix on the query side only; using
the same treatment for both sides was causing short technical phrases ("order line" vs "customer
order") to get confused with each other.

### `qa/loader.py`
**What it is**: reads every `data/qa/prospect_to_cash/<level>.xlsx` file (one per Prospect-to-Cash
stage) and keeps only rows marked `APPROVED` + `active`, per the master prompt's rule that only
approved/active records may be used in production. It additionally excludes the known placeholder
`PTC Training Guide` sample source until those rows are replaced with real, reviewed content.

### `qa/glossary.py`
**What it is**: reads `data/metadata/business_glossary.csv` and uses it to recognize when a user's
wording (a synonym or abbreviation, e.g. "credit ceiling", "CO") means the same thing as a formal
term in the Q&A data ("Credit Limit", "Customer Order") — the acronym-expansion/synonym-mapping
step from the master prompt's Fast Q&A pipeline (§9). **Updated 2026-09-29**: also reads the
`glossary` sheet of every Q&A workbook (the data-team template has one per module) and merges it
with the CSV — one entry per term, all synonyms kept, no duplicates (`tests/test_glossary_sheets.py`).

### `qa/retriever.py`
**What it is**: the actual Fast Q&A search — implements the pipeline from master prompt §9 exactly:
normalize → glossary expansion → exact match → BM25 (keyword) → embedding similarity → combined
hybrid score → a quality gate that decides between a confident answer (`FAST_QA_RESPONSE`), asking
the user to clarify between close candidates (`CLARIFY`), or handing off to document search
(`MARKDOWN_RAG`). The score thresholds are starter values, explicitly not tuned —
the master prompt insists these come from real evaluation later, not a guess.

### `api/models.py`
**What it is**: the `ChatRequest`/`ChatResponse` shapes for the `/chat` endpoint.

### `utils/search_tokens.py` (added 2026-09-25)
**What it is**: the one tokenizer for every BM25 keyword index (Excel Q&A and knowledge base):
lower-case, punctuation removed, Snowball English stemming plus a trailing "-ment" strip, so word
forms match ("how do I ship…" finds the shipment section). Same function on documents and
questions, so matching stays consistent. Needs `snowballstemmer` (requirements.txt).

### `utils/logger.py`
**What it is**: the central application logger. Every log line is written to both the terminal
and one active file, `logs/chatbot.log`, using the same timestamped format. `log_event()` produces
single-line lifecycle records such as `http_request_started`, `security_bootstrap_completed`,
`permission_resolved`, `fast_qa_search_completed`, and `chat_response_ready`. Request IDs make a
single turn traceable pin-to-pin across modules. The active file rotates at 5 MB and keeps three
older backups so the working log cannot grow forever.

**Privacy/security rule**: never log session tokens, credentials, raw questions, generated
answers, or retrieved document text *in event lines*. Events record operational metadata only
(route, duration, score, counts, permission result, and safe context labels).

**Updated 2026-09-28 — two streams**: *trace lines* (logger `trace`, see `utils/trace.py`) are the
clear, human-readable story and appear in the terminal **and** the file; *event lines*
(`log_event`) are the technical `event=… key=value` records and always go to the file, but reach the
terminal only with `LOG_TERMINAL=all` (default `trace`: trace lines + every warning and error).
Chatty libraries (httpx, openai, sentence-transformers, pymilvus…) are set to WARNING and the
embedding progress bar is off, so the trace isn't buried.

### `utils/trace.py` (added 2026-09-28)
**What it is**: the step-by-step trace, in both the terminal and `logs/chatbot.log`.
**At startup**: a banner, then one line per Excel workbook (rows used, question wordings, rows
skipped and why) and per Markdown file (chunks, largest chunk), then embeddings (count, model,
time), Milvus, BM25, reranker (now loaded at startup), LangGraph, Postgres, tickets + security
events, ticket email readiness, the console URL, and `READY in N s`.
**For every question**: a separator, `❓ NEW QUESTION` with the text, who is signed in, the screen,
permission, how much history was used, then numbered `STEP n` lines (one per LangGraph node, timed —
see `orchestration/step_trace.py`) with details: the clean question and SyteLine-terms wording, the
rewrite, intent/complexity/mood/route, the Excel matcher's top 3 with keyword and meaning scores
and which match was kept, **every search wording** with vector/keyword hit counts and the reranked
top 3, the final evidence list with scores, **why the approved Excel answer was or wasn't used**,
the answer model, time and tokens, the draft, **each cross-check** (rules, grounding check and the
exact statements it flagged, repair, re-check, result), security events, the ticket offer, then
`💬 ANSWER`, the sources and `✔ DONE in N s`. Tickets, ticket emails and server stop are one-line
`NOTE`s. Every request's lines carry the first 8 characters of its request id (e.g. `[2f0e4bc9]`).
**Safety**: text is shown only with `LOG_CONVERSATION_TEXT=true` (default; set `false` in
production to show only lengths); secrets (keys, bearer tokens, `password=…`) are always masked;
every value is kept on one line so a user can't forge log lines; a trace error never breaks an answer.

### `orchestration/step_trace.py` (added 2026-09-28)
**What it is**: wraps each of the 14 LangGraph nodes once so it becomes a numbered, timed step with
a plain-English title and a description of what it decided. Kept in one place so the trace can't
drift from the graph (a test checks every node has a title).

---

## `data/` (Phase 1)

### `data/metadata/business_glossary.csv`
**What it is**: the Prospect-to-Cash business glossary — canonical term, synonyms, abbreviation,
module, process — for the ~15 terms from master prompt §60 (Prospect, Lead, Opportunity, ...,
Receivable). Used by `qa/glossary.py`. A real data-governance asset per §57/§59
(`PTC_Business_Glossary`) — edit this file directly to add more terms.

### `data/qa/prospect_to_cash/*.xlsx`
**What it is**: one Q&A Excel file per Prospect-to-Cash stage (`prospect.xlsx`, `lead.xlsx`,
`opportunity.xlsx`, `estimate.xlsx`, `quotation.xlsx`, `customer.xlsx`, `customer_order.xlsx`,
`customer_order_line.xlsx`, `pricing.xlsx`, `credit.xlsx`, `shipment.xlsx`, `invoice.xlsx`,
`payment.xlsx`, `faq.xlsx`), each with the full column schema from master prompt §8 (not just
Question/Answer) plus a `question_variations` sheet.

**Why one file per level**: matches the level names the Markdown knowledge base will use later
(§13), and lets each stage be reviewed/approved independently rather than one giant spreadsheet.
Currently filled with placeholder/dummy content for structure-testing — replace with real,
reviewed content before this goes anywhere near production, per §12's document-governance rule
that only approved content may be ingested.
The generated starter rows use a placeholder `PTC Training Guide` source. The loader now excludes
that source even though older workbook copies carry an APPROVED flag; newly generated samples use
DRAFT. Review and replace them with real sourced Q&A before enabling Fast Q&A content.

**Status discrepancy to resolve separately:** A read-only test of existing Prospect,
Customer, Customer Orders, Customer Order Lines, and Pricing workbooks during the Credit
pass found `APPROVED`/active entries, although the earlier entries above describe an
intended `IN_REVIEW`/inactive state. This Credit update did not change those workbooks.

### `scripts/generate_sample_qa.py`
**What it is**: the generator that writes the files above. Re-run it any time to regenerate all
14 files from the `LEVELS` dict inside it (it overwrites them). Add more dummy/starter rows here,
or edit the `.xlsx` files directly once real content replaces the placeholders. Generated starter
rows now carry DRAFT approval status. **Superseded (2026-09-24)** by `build_qa_from_knowledge.py`
below; kept only because that script reuses its column definitions.

### `scripts/eval_understanding.py` (added 2026-10-08)
**What it is**: the before / after check for `COMBINED_UNDERSTANDING`. Runs the real chat workflow in its
own process (real OpenAI, Milvus and models — the running server is untouched) over 53 questions plus
3 follow-ups — knowledge questions, slang and typos, other languages, screen context, two-part
questions, frustration, live data / actions / navigation, small talk, ticket requests, off-topic,
unclear questions and attacks — once with the switch off and once on, and prints where each question
ended up (and whether that is right), the time, the OpenAI calls and the cost, plus every question
whose result differs between the two modes. `python -m scripts.eval_understanding [--only on|off]
[--out results.json]`; about $0.01 per question per mode.

### `scripts/validate_knowledge_data.py` (added 2026-09-29)
**What it is**: the data team's checker — `python -m scripts.validate_knowledge_data <files or
folder>`. Reads only, changes nothing; exit code 1 on errors. **Markdown**: file name, `# Title`
and `##` sections, required metadata (Module, Tags, Owner, Reviewed / Approved By, Last Reviewed,
Version, Source), unfilled `<placeholders>`, TODO/TBD, images, open `[NEEDS CONFIRMATION]` items,
e-mail addresses / phone numbers (dates excluded) / passwords / keys, duplicate sections, missing
Section Summary or Keywords, sections too long or empty — then a preview of exactly how the file
will be split into searchable sections. **Excel**: sheets and columns the loader reads, unique
`qa_id`s, required cells, allowed values (approval_status, route, intent, active), APPROVED rows
need a real `approved_by` (not "AUTO-DERIVED … pending") and an effective date, answer length,
questions ending with "?", the `source_reference` file exists, variations point at real rows (at
least 3 each, no duplicates), glossary synonyms separated with `|`. Repeated row problems are
grouped into one line.

### `scripts/convert_docx_to_md.py` (added 2026-09-29)
**What it is**: turns a module document written in Word (from the Word template) into the
Markdown file the chatbot loads — Heading 1/2/3 → `#/##/###`, numbered/bullet lists, bold
`Label:` lines, tables; grey "Note:" writer guidance removed. Checked by a round-trip test: the
Word template converts to exactly the same 14 sections as the Markdown template.

### `scripts/build_permission_search_doc.py` → `documentation/Permission_Aware_Knowledge_Search.docx` (added 2026-09-30)
**What it is**: the design note (6 pages, Word) on permission-aware document search: today's gap
(search covers all documents for anyone allowed to search), the two options (one collection per
module vs one collection with module / form / allowed-role labels and a filter), seven issues with
per-module collections each with a SyteLine example, the measured search timings (Milvus 15 ms of
331 ms), when separate collections are right, the recommended design and implementation steps.
Rebuild with `python -m scripts.build_permission_search_doc`; flow diagrams are Word tables, so the
document stays editable.

### `scripts/build_data_templates.py` (added 2026-09-29)
**What it is**: builds `documentation/data_templates/SyteLine_QA_Template.xlsx` (README, `qa_master`,
`question_variations`, `glossary`, `allowed_values`; red headers = required, a note on every
header, dropdown lists, blue EXAMPLE rows set to DRAFT so they can never go live) and the Word
version of the Markdown module template. Columns and allowed values come from the checker, so
templates, checker and loader can't drift apart.

### `scripts/build_qa_from_knowledge.py`
**What it is**: builds the Fast Q&A Excel files *from the Markdown knowledge base*, one
`<md stem>.xlsx` per article, so Excel and Markdown can never contradict each other (the old
hand-typed starter rows did). For each section the LLM drafts up to 2 Q&A pairs plus 3 question
variations using only that section's text; a deterministic grounding gate drops any answer whose
content words aren't in the section (first run: 132 kept, 21 dropped). Rows use `KB-xxxx` ids
(distinct from the retired `QA-xxxx` placeholders), `source_reference` = the `.md` file and
`source_section` = the heading path. Marked APPROVED so they load, but `approved_by` says
"AUTO-DERIVED … pending SME review" — a business owner should review them before production.
Run with `python -m scripts.build_qa_from_knowledge` after editing the Markdown (it overwrites all
Excel files).

### `data/knowledge/prospect_to_cash/*.md`
**What it is**: 20 retrieval-ready, module-wise Markdown articles covering CRM setup, campaigns and forecasts; prospect,
lead, opportunity, estimate, quotation, customer, order header/line, pricing, credit, shipment,
invoice, payment, follow-up, returns, order/billing variations, form/field guidance, and cross-process tracing. The five
original starter articles were corrected and expanded; the others were added before Phase 4. The
two gap-fill articles were added after the first 18-file Q&A generation; they are Markdown-only
until Q&A is regenerated and reviewed.
Every article uses heading hierarchy, `### Keywords`, and `**Section Summary:**` with complete
plain-text guidance and no external links. See `PROSPECT_TO_CASH_KNOWLEDGE_BASE.md` for inventory, source policy,
known limits, and verification. These are general vendor-guidance drafts, not approved site
procedures or model fine-tuning data. The index loads Markdown once at app startup, so restart or
reindex after edits. Technical IDO/API mappings remain `[NEEDS SYTELINE CONFIRMATION]`.

**Content rule worth knowing**: a line like `A. Do this` (single capital letter + period) is
treated as its own sub-heading by the chunker, not a list item — use numbered (`1.`) or bulleted
(`-`) lists for ordinary step-by-step content instead, or each step becomes its own tiny,
oddly-tagged chunk. Found and fixed this exact mistake while testing — see the "moved to
numbered lists" edit in this project's git history.

---

## `backend/app/rag/` (Phase 1 — Markdown RAG, Source B)

### `markdown_processor.py`
**What it is**: the heading-aware chunker (master prompt §14, replica pattern §6.2) — walks a
document line by line, splits on any heading (except a "Keywords" heading, which gets absorbed
into the current chunk), and also splits long sections at ~1200 characters with a 3-line overlap
seed. Extracts each chunk's keyword block and builds the synthetic embedding text
(`context path + keywords + excerpt`) the same way the Q&A side builds its search text.
**Updated 2026-09-29 (data-team template)**: keywords are also read from an inline
`**Keywords:** a, b` line (the HRMS document style), not only a `### Keywords` heading; the
`Document Metadata`, `Table of Contents` and `Change History` sections are no longer indexed (they
are for people), and the metadata `**Tags:**` are added to every chunk's keywords; `<!-- writer
notes -->` are stripped; heading-only chunks are dropped — the current knowledge base had 14 of them
(each file's `# Title` line), which took search-candidate slots while holding no content (162 → 148
chunks). **Tables (2026-09-29)**: search used to see only the first 300 characters of a section,
so **48% of table rows (111 of 228) were invisible to search**. Now `linearize_tables()` turns each
row into a labelled sentence ("Field: Credit Limit · Form: Customers · Meaning: …"); the section
vector reads up to 1,500 characters of that readable text; and every row is stored in
`row_texts` and gets **its own vector** in Milvus (`<chunk_id>::r<n>`, 201 today) pointing back to
its section — the same pattern as the Excel question variations. The answer model still gets the
original Markdown table. Keyword (BM25) text deliberately stays short (`search_text` = heading path
+ keywords + the opening 300 characters): indexing whole sections, or every row label, was measured
to push shipment.md down (rank 11 → 51 / 12) for "how to ship an order".

### `milvus_store.py`
**What it is**: the Milvus vector store for document chunks. **Switched from Milvus Lite to a
Docker Milvus standalone stack (2026-09-24)** so vectors can actually be browsed visually via
Attu — Lite has no UI, it's just an opaque local file, which defeated the point once the user
wanted to see how vectors are stored. Connects via `MILVUS_URI` in `.env`
(`http://localhost:19531`); point that at a local file path instead to fall back to Lite
(confirmed working natively on Windows earlier, kept as a documented option, e.g. for a machine
without Docker). Collection is dropped and rebuilt on every startup, same as the rest of this
project's ingestion.

**This project's Docker stack is fully separate from anything else on the machine** — first tried
reusing an already-running Milvus from a different, older project (`PycharmProjects/DeepChatbot/`),
but the user explicitly asked for full separation, so that was replaced the same day with this
project's own dedicated `docker-compose.yml` (see below): different container names (`ptc-*`
prefix), different host ports, different volumes, own Redis too. Confirmed isolated — `ptc-milvus`
shows *only* this project's collection, nothing from any other project.

**2026-09-24 — one collection for both sources.** The collection is now `ptc_knowledge` (the old
`markdown_chunks` is dropped on startup) and holds Markdown chunks *and* Excel Q&A rows, told apart
by `source_type`. Every field is declared in the schema (`source_type`, `chunk_id`, `source_file`,
`level`, `full_context_path`, `qa_id`, `question`, `text`, …) instead of hidden dynamic fields, so
Attu (http://localhost:3001) shows real columns; inserts are flushed, so the row count is right
(previously Attu showed 0 rows and only `id`/`vector`). `search()` takes an optional
`source_type` filter.

### `reranker.py`
**What it is**: the cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`, master prompt
§31) — scores each (query, chunk) pair directly for a more accurate relevance signal than
embedding similarity alone, run only on the already-narrowed candidate pool.

### `retriever.py`
**2026-09-25 search quality update**: keyword search is now **stemmed** (`utils/search_tokens.py`:
ship = shipment = shipping), the candidate pool is **20 per source** (was 10) and **6** sections go to
the answer (was 5, budget 7,000 chars). Measured on a 52-question slang/variant sweep across all
modules: 39/52 → 49/52 answered from the right module; the remaining 3 are genuine content gaps
("how to change payment terms / credit limit" steps are not in the knowledge base) or truly
ambiguous ("what is so"), where the bot correctly declines to invent. `graph.py` runs
**multi-query retrieval** — each single question is searched with the user's words and the LLM's
standard-terminology version, each keeps its top 2, the rest fill by score.
**What it is**: the actual Markdown RAG pipeline (master prompt §27) — vector search + BM25 in
parallel, Reciprocal Rank Fusion to combine them, cross-encoder rerank, an evidence-sufficiency
gate (starter threshold, tested against this project's own dummy data — not a benchmarked
number), and simple contextual compression (caps total context by character budget, keeps only
chunks that clear the relevance bar rather than blindly keeping the top 5 regardless of score).

**2026-09-24 — unified Excel + Markdown retrieval (replica pattern).** Each search now takes the
top 10 Excel candidates and top 10 Markdown candidates (each via Milvus vector search filtered by
`source_type` + BM25 + RRF), reranks all 20 with the one cross-encoder so the scores are directly
comparable, and applies the replica's guaranteed-include rescue (a vector match ≥ 0.80 is never
dropped). Results carry each item's source and the best score per source. Excel rows are
represented as chunks whose text includes their question variations, so the reranker recognises
paraphrases. How the orchestrator uses this to pick verbatim Excel vs a generated answer is in
`ARCHITECTURE_DECISIONS.md` decision #9.

### `answer_service.py`
**2026-10-08 — answer length**: simple definition questions ("what is customer", "What does CO mean?",
"define prospect") get `brief=True`, which adds `BRIEF_INSTRUCTION` (one or two sentences, about 40
words, what it is and the form where it is kept, no steps or related processes). The decision is
`graph.is_definition_question()`: the wording starts like a definition, or the classifier says
`operation = definition`, and the question has no how / why / difference / steps / process / what
happens and at most 10 words. Every answer also follows a new rule: answer only what was asked, no
related topics. Measured: "what is customer" went from ~85 words mixing prospects, credit and PO
references to 30 words; "How do I create an invoice?" and lead-vs-opportunity still get full answers.

**What it is**: calls the primary LLM to generate a grounded, cited answer from the retrieved
chunks (master prompt §34) — a deliberately simplified version of the full answer-generation
prompt. Role-aware tone and RBAC scope enforcement (the replica pattern's big system prompt) land
in Phase 5 per the roadmap; this only needs to prove grounded, cited answers work end to end,
which it does. **Updated 2026-09-25**: `generate_answer(..., avoid_claims=[...])` regenerates an
answer without the statements the answer validator flagged (see `quality/answer_validator.py`).

---

## `backend/app/quality/` (Phase 5 — answer quality, added 2026-09-25)

### `quality/answer_validator.py`
**What it is**: the hallucination guard. Every *generated* answer is checked against the evidence
it came from before the user sees it (curated Excel answers shown word for word are SME-approved
and skip it). Two layers:
1. **Rule checks** (no LLM): leaked secrets or prompt text → the answer is replaced; claims that the
   bot changed something in SyteLine ("I have released the hold") → flagged, the bot is read-only;
   numbers that appear in neither the evidence nor the question → flagged (step numbering and
   single digits are ignored).
2. **Grounding check** (`ANSWER_VALIDATION_MODEL`, default `gpt-4.1`, JSON): lists invented forms,
   fields, buttons, numbers, rules or behaviour (things the evidence doesn't contain), and says
   whether the answer actually answers the question. `gpt-4.1-mini` was tried first and was too
   literal — it rejected steps the documents clearly support (e.g. "record the lost reason").
   Refusals are also detected by wording (a reply with ≥2 real steps is never a refusal).

**Measured 2026-09-25**: invented form / number / behaviour / button all caught (4/4); 50-case
regression 50/50; slang sweep 50/52 (was 49/52 — the 2 misses are real content gaps, now
correctly `NO_ANSWER`). Generated answers take ≈5–8 s; a repair adds ≈2–4 s.

**Outcome** (`grounding` in the API response, `validation` in the decision trace): `passed`;
`repaired` (flagged claims → answer regenerated once without them → re-checked clean);
`replaced` (still unsupported → a safe "I couldn't confirm this" message, route `NO_ANSWER`);
`not_found` (the documents don't answer it → the polite "not available" reply, route `NO_ANSWER`,
so it is counted as an unanswered question); `unverified` (grounding LLM unavailable, rule checks
clean → answer sent, marked as not LLM-verified). Turn off with `ANSWER_VALIDATION_ENABLED=false`.
**Cost/latency**: one extra `gpt-4.1` call (≈1–2 s) per generated answer; a repair adds one more
answer call and check. The trace stores labels and counts only; flagged claim text goes only to
the local log (`answer_validation_flagged`) for tuning.

### `quality/tone.py` (Phase 5 step 2, added 2026-09-25)
**What it is**: the tone manager — the answer fits the user's mood. Levels: **F0 normal**, **F1
confused** (plain words, short steps, offer to explain more), **F2 complaint** (one short
acknowledgement, then the fix), **F3 frustrated** (calm, one empathy sentence, most likely fix first),
**F4 persistent** (says it's still unresolved, gives the *next* diagnostic step instead of repeating
the same steps).

**Where the mood comes from**: the conversation-understanding LLM now also returns `mood`, read from
the user's raw words and the conversation (the classifier only sees the cleaned-up question, which
has lost the "!!!", CAPS and "still not working"). `rules_mood` is a floor for obvious signals and
the fallback when the LLM is down: phrases like "still not working", "already tried", "third time",
a repeat of an earlier question (≥75% same topic words), insults / "fed up", CAPS, "!!", "don't
understand", "???". A bare "still" or "again" in a normal question ("invoice still open") is **not**
an emotion — the old classifier rule got that wrong, so `router._emotion` now uses these rules too.
The strongest reading wins and is stored as `emotion` in the decision trace.

**How it is applied**: generated answers get a style instruction added to the answer prompt (after
the grounding rules; the validator still checks every claim). SME-approved Excel answers are never
rewritten — they get a short opener in front ("No problem — here it is step by step."). F3/F4 lead
to a support-ticket offer (decided by `escalation/policy.py`, text added by the API — see below).
**Never changed by mood**: facts, security blocks, out-of-scope and clarification replies,
capability-pending replies, permissions.

**Measured 2026-09-25**: 11/11 live messages got the right mood (English, Hinglish, emoji, CAPS, and
a conversation that repeats the same credit-hold problem).

---

## `backend/app/integrations/syteline/`, `authorization/`, `context/` (Phase 2)

Real SyteLine identity, session, and dynamic permissions — per `BUILD_ROADMAP.md` Phase 2. Most
of master prompt §73's `[NEEDS SYTELINE CONFIRMATION]` items are still open (we don't yet know the
real session-bridging mechanism or permission APIs), so these modules are built with the real
*shape* and *logic* the master prompt describes, backed by clearly-labeled mock data — swapping
the mock for real SyteLine access later only touches the specific file noted below, not any
caller.

### `integrations/syteline/session_context.py`
**What it is**: the mock stand-in for SyteLine's session/security APIs —
`get_logged_in_user()`, `validate_session()`, `get_configuration()`, `get_current_site()`. Returns
one of three test users/groups (`SALES_REP`, `AR_CLERK`, `NO_ACCESS`) depending on which the
frontend's Context Simulator picked, so permission allow/deny can actually be exercised and
demonstrated, not just always-allow like the retired Phase 1 seam.

**What's real vs. mock**: real SyteLine WebClient demo credentials were given by the user for
testing (2026-09-24), stored in `.env` only (`SYTELINE_LOGIN_URL` / `SYTELINE_CONFIGURATION_NAME`
/ `SYTELINE_USERNAME` / `SYTELINE_PASSWORD`) — **not yet read by any code**. Having credentials
doesn't by itself answer *how* the chatbot would authenticate against SyteLine's actual API
surface (REST v2 / ION / Mongoose — still unconfirmed, §73 items 17). Wiring them in is later
work, likely Phase 4 (SyteLine connector) or a dedicated exploration step.

### `authorization/resolver.py`
**What it is**: the Dynamic Permission Resolver (master prompt §19) — real group-lookup logic and
real short-lived Redis caching (30s TTL), with a mock permission table
(`MOCK_GROUP_PERMISSIONS`). Confirmed a real Redis container was already running locally (Docker,
port 6379) before building this, same diligence as the earlier Milvus-on-Windows check. Fails open
on a Redis connection error (skips the cache, resolves fresh) — that's just a performance
degradation, not a security bypass, since the underlying resolve logic doesn't depend on Redis.
Permission decisions and cache outcomes now emit request-correlated events so allow/deny behavior
can be followed end to end without exposing credentials. (2026-09-25: new permissions
`INSERT support_ticket` for SALES_REP / AR_CLERK and a new mock group `SUPPORT_ADMIN` with
`READ admin_console` for the ticket and security-event console; 2026-09-28: `UPDATE admin_console`
for reviewing feedback and changing ticket status.)

### `context/manager.py`
**What it is**: builds one normalized `RequestContext` per turn (master prompt §20) — user
identity, groups, configuration/site, and whatever screen/field/record context the frontend sent.
Everything downstream reads this one object instead of raw session/UI data.

### `security/bootstrap.py`
**What it is**: Security Bootstrap (master prompt §2.1/§18) — establishes who the current user is
before anything else runs; no separate chatbot login. Raises `InvalidSessionError` on a missing
session token, which `/chat` turns into a `BLOCKED` response.

---

## `backend/app/security/`, `classification/`, `orchestration/` (Phase 3)

The orchestration layer. Full flow, taxonomy, route table, safety behavior, logging contract, and
acceptance evidence are documented in `documentation/PHASE_3_ORCHESTRATION.md`.

### `security/input_gate.py`
**What it is**: the first AI/safety gate. It combines Unicode/leetspeak normalization, bounded
URL/base64/separated-letter decoding, category-specific regex and contextual signal combinations,
plus semantic classification for suspicious-but-inconclusive requests. Known attacks are blocked
locally and never sent to retrieval or tools; suspicious classification failures fail closed.

### `classification/taxonomy.py`
**What it is**: the stable hierarchical contract shared across Phase 3: all security, five-label
scope, intent, ambiguity, complexity, emotion, and route enums, plus typed Pydantic result models.

### `classification/scope.py`
**What it is**: classifies SyteLine-related, off-topic, general-knowledge, competitor/other-ERP,
and irrelevant input, then maps those labels to a binary continue/stop decision. Uses the business
glossary and trusted UI context before an LLM fallback. Never answers off-topic questions.

### `classification/ambiguity.py`
**What it is**: the intent-agnostic ambiguity resolver. It runs before intent classification,
resolves “this customer/field/screen” from trusted context when possible, and asks a targeted
clarification when required context, detail, or version is missing or actions conflict.
(2026-09-25) A why/how question about "this order" with nothing selected is answered in general
("why can't I ship an order") plus a note to select the record for specifics, instead of only
asking "which order?"; data requests ("show me this record") still ask for the record.

### `classification/query_transformer.py`
**What it is**: selective preprocessing—normalization, focused spelling repair, glossary/acronym
expansion, entity/identifier extraction, and explicit multi-part decomposition. Records exactly
which transformations ran instead of applying every NLP technique to every query.

Retrieval-quality fixes (measured with reranker scores): a leading greeting ("good morning, how
do I …") is removed before classification and search and kept as `leading_greeting` so the reply
can greet back — it had dropped relevance from 2.9 to -1.0. The *search text only* (not the
question the answer model sees) also drops polite openers ("Can you…", "Could you please tell
me…") and rewrites "lifecycle"/"journey" to "process", the word the knowledge base actually uses.
Each decomposed sub-question gets its own search string in `expanded_subqueries`.

### `classification/router.py`
**What it is**: the initial structured LLM classifier and three-source route selector. The model
can return only declared taxonomy values and allowlisted tool candidates; Python enforces the final
intent-to-route policy and supplies a deterministic fallback. Greetings/chitchat bypass the model
and retrieval entirely. ANALYSIS intents (2026-09-25 fix) go to the knowledge search unless they ask
for live figures (trend, total, how many, this quarter…), which still wait for Phase 4 — before this,
"What is the difference between an estimate and a quotation?" was labelled ANALYSIS by the LLM and
answered "not enabled yet". Greeting and small-talk detection comes from `small_talk.py` (below); the
greeting key is recorded as `sub_intent` (`good_morning`, `good_night`, `hello`, `+wellbeing`, …).

### `classification/small_talk.py` (added 2026-09-25)
**Role since the LLM step**: the **offline fallback** for `conversation.py` (used when the LLM is
unavailable) and a cheap pre-check inside scope/classification. It is no longer the primary way
greetings are understood.
**What it is**: the single shared rule-based definition of greetings and small talk, used by scope, query
transformation, classification and the direct-response reply. Before it,
each of those had its own short pattern, so "good morning **buddy**" missed them all, fell through
to the LLM, and got a generic "Hello!". It handles time-of-day greetings and typos (good morning,
gud mrng, gm, good night), casual forms (hi/hiii, hey/heyyy, hello/helo, howdy, namaste), who is
greeted (buddy, bro, team, sir, everyone, bot…), pleasantries ("how are you", "how's it going",
"hope you are well" → the reply also says "I'm doing well, thank you for asking!"), any case,
punctuation and emoji, and small talk (thanks bro, bye buddy, see you later, got it…). Guards:
bare "morning"/"yo" only count as a greeting when they are the whole message ("morning shipment
schedule" keeps its words), and "hi-tech customers" is not stripped. The reply always reads the
greeting from the user's own words; the classifier's label is only a fallback.

### `orchestration/state.py`
**What it is**: typed `ChatWorkflowState` and `WorkflowResult` contracts. State carries the trusted
context plus each level's result; the final API-safe decision trace contains labels only.

### `orchestration/graph.py`
**What it is**: the compiled LangGraph. Nodes execute security → scope → ambiguity → transformation
→ classification → route selection, then terminate or run direct response/Fast Q&A/Markdown RAG.
Phase-4-or-later routes return `CAPABILITY_PENDING` instead of inventing ERP data or performing an
unavailable navigation/action.

Conversation understanding (2026-09-25, replaces the 2026-09-24 `followup_resolution` node): a
`conversation_understanding` node runs right after the security gate (`classification/conversation.py`).
Pure small talk goes straight to `direct_response` — no scope check, search or classifier call.
Business messages continue with the clean, standalone, English question as `query`, so
scope/ambiguity/RAG never see greetings or unresolved "it". `run()` takes the `history` list; the
decision trace reports `history_turns_used`, `followup_resolved`, `message_kind` and
`conversation_source` (llm / cache / rules).

Multi-question messages: the RAG node searches every sub-question separately
(`_search_each_question`) and interleaves the top chunks round-robin under a 9,000-character
budget, so "What is a quotation and how is an invoice created?" retrieves both quotation.md and
invoice.md instead of only the dominant topic. `_normalize_chitchat_sub_intent` maps the LLM
classifier's free-form chitchat labels (e.g. `CHECK_WELLBEING`) onto the canned replies.

**2026-10-08 — `COMBINED_UNDERSTANDING`** (setting, on by default since it was measured; `COMBINED_UNDERSTANDING=false` goes back to two calls): the understanding
call (`conversation.py`) also returns the routing `classification`, using the classifier's own rules
(`router.CLASSIFIER_RULES`, shared so both paths classify identically) and the SyteLine screen context.
`router.classify_and_route(..., precomputed=)` uses it when it is a valid object with an intent and a
route; anything missing or invalid falls back to the separate classifier call, so no routing is lost.
Code still owns the final route (`_enforce_route_policy`), unknown tool names are dropped, and the
screen's module / form come from SyteLine, never the model. The trace and the decision trace show
`classifier: combined | llm | rules`. Tests: `tests/test_combined_understanding.py` (12, faked OpenAI);
before / after measurement: `scripts/eval_understanding.py`.
A message that reads like a command ("Create a customer order…", "Open the … form", "show my open orders") but came back as a question is re-checked by the separate call (first run: the combined call read two commands as how-to questions). **Measured on 56 questions:** off 52/54 correct, on **54/54**; understand + classify 2.6 s → 1.6 s; business answers 5.9 s → 5.1 s (median); OpenAI calls per question 3.6 → 2.7; cost about the same. The same run found the scope check flipping on "What is a credit memo?" (in scope 3 of 6 times): `scope.py` now lists Prospect-to-Cash terms (credit memo, write-off, payment terms, ship-to, price book…) and tells the LLM scope check that business and accounting terms are in scope.

### `classification/conversation.py` (added 2026-09-25 — replaces `followup.py`)
**What it is**: LLM conversation understanding, run on every message right after the security gate.
One `gpt-4.1-mini` JSON call reads the message (plus the last 3 turns) and returns: `kind` (greeting,
wellbeing, thanks, farewell, identity, capabilities, acknowledgement, introduction, casual_checkin or
business), `greeting` (good_morning / good_afternoon / good_evening / good_night / hello),
`asked_wellbeing`, `mood` (F0–F4, added 2026-09-25 for the tone manager — see `quality/tone.py`),
and `question` — the business request alone, greetings and pleasantries removed,
follow-up references resolved ("how do I convert it?" → "How do I convert a quotation?") and
translated to English for the English knowledge base. Because the LLM understands meaning, new
wording, slang, typos, emoji and other languages ("mornin my dude", "top of the morning", "gn",
"cheers mate", "namaste ji kaise ho", "buenos días") work without adding words to any list.
**Business slang (2026-09-25)**: it also returns `search_query` — the same question in standard
SyteLine wording ("how to raise the quotation" → "How do I create and issue a quotation?"; punch/book
an order, cut an invoice, knock off a hold, collect money…). `graph.py` searches with it (single
questions only) while the answer keeps the user's words. Before, "raise the quotation" scored
below the evidence bar and got "no answer". The intent classifier (`router.py`) now reads the
user's own question, not the search text, and is told "how do I …" is HELP_PROCESS, not ACTION —
otherwise the command-like search text was misread as a transaction request.
**Safety**: the model only labels and rewrites; replies to small talk come from fixed templates in
`graph.py`, and every label is validated against an enum. "The user asked how we are" must be
quoted (`wellbeing_phrase`) and is accepted only if those words are really in the message and are
not the business question — the model had wrongly flagged "good morning, how do I convert it?". **Resilience**: LLM disabled, timeout or
invalid JSON → the offline rules in `small_talk.py`. **Cost/latency**: ≈0.8–1 s per new message;
pure small talk without history is cached in memory (512 entries), so repeats take ≈0.01 s.

---

## `backend/app/escalation/` (Phase 5 step 3, added 2026-09-25)

Two separate flows, as the master prompt requires: **support tickets** (§55) and **security
events** (§56). A security attack is never turned into a support ticket.

### `escalation/policy.py`
**What it is**: decides, for every answer, whether to offer a support ticket. States:
`ESC_NONE`, `ESC_SUGGEST_TICKET` (offer one), `ESC_CREATE_TICKET_AFTER_CONFIRMATION` (the user asked
for one). Triggers: **frustration** (F3), **persistent** (F4 — same problem again), **unresolved** (this
answer and one of the last 3 were NO_ANSWER / CLARIFY), **user_request** ("raise a ticket", "talk to a
human", "escalate"). Never for BLOCKED or OUT_OF_SCOPE. It never creates a ticket itself — the user
always confirms (§55). `is_ticket_request` is the offline fallback for the conversation LLM, which
has a new message kind `escalation_request`; "how do I raise a quotation" is business, not a request.

### `escalation/store.py`
**What it is**: two Postgres tables on the history pool, created at startup (fail-soft).
`support_tickets`: user, site, module, form, safe record reference, issue summary, steps attempted,
the user's optional note, a safe conversation summary (last 6 exchanges, answers cut to 300
characters), mood, trigger, priority (high for F3/F4), status, time. The ticket is built from the
**stored** conversation, cut at the answer it was raised from — never from text the browser sends —
so a user can't put words in a ticket the chatbot never saw. BLOCKED exchanges are left out and
secrets are redacted. One ticket per answer (a double click returns the same `PTC-000123`). A user can
only raise tickets on their own conversation. `security_events`: one row per blocked attack (security
gate) or blocked answer leak (answer validator), with label, severity (high for credential requests,
data exfiltration, permission bypass, tool abuse, answer leaks), screen, a SHA-256 of the message and a
redacted 300-character excerpt. When one user is blocked `SECURITY_ALERT_THRESHOLD` (3) times in
`SECURITY_ALERT_WINDOW_MINUTES` (15), one alert is raised for that burst. A missing permission
(BLOCKED with a SAFE security label) is **not** a security event.

### `escalation/notifier.py`
**What it is**: where new tickets and security alerts are sent. `log` writes a structured log event
only; `outlook` (2026-09-28) also emails them through `escalation/outlook.py`. Mail goes out on a
background thread, so confirming a ticket never waits for Outlook, and a failure never fails the
user's request. Each ticket records `notification_status` (sent / failed / not_configured / logged),
shown as a pill in the console. `startup_check()` logs at startup whether mail is ready and names
any missing `.env` values (never their contents).

### `escalation/outlook.py` (added 2026-09-28)
**What it is**: Outlook / Microsoft 365 mail. **Graph** (default): client-credentials token from
`login.microsoftonline.com/{tenant}` (cached until expiry), then `POST /v1.0/users/{sender}/sendMail`
— needs an Azure app registration with the **Mail.Send application permission + admin consent**
(ask IT to limit it to the sender mailbox with an application access policy). **SMTP**:
`smtp.office365.com:587` with STARTTLS, only if IT allows SMTP AUTH. Ticket mail subject
`[PTC-000123] HIGH priority — <issue>`, with ticket, priority, who, why offered, screen, record,
issue, steps already tried, the user's note, a short conversation summary and time; security alert
subject `[SECURITY ALERT] prompt injection — <user> (3 blocked attempts)`. Every value in the HTML
is escaped. **Settings** accept two naming styles (the team's other bots use the second):
`ESCALATION_NOTIFIER=outlook` or `ENABLE_TICKET_RAISING=True`; `OUTLOOK_SEND_METHOD` or `USE_GRAPH_API`;
`OUTLOOK_SENDER`/`TICKET_FROM_EMAIL`; `OUTLOOK_SENDER_NAME`/`TICKET_FROM_NAME` (SMTP only — Graph
shows the mailbox's own name); `SUPPORT_TICKET_EMAIL`/`TICKET_RECIPIENT_EMAIL`;
`OUTLOOK_TENANT_ID`/`GRAPH_TENANT_ID`, `OUTLOOK_CLIENT_ID`/`GRAPH_CLIENT_ID`,
`OUTLOOK_CLIENT_SECRET`/`GRAPH_CLIENT_SECRET`; `OUTLOOK_SMTP_HOST`/`OUTLOOK_SMTP_SERVER`,
`OUTLOOK_SMTP_PASSWORD`/`OUTLOOK_PASSWORD`; `SECURITY_ALERT_EMAIL` (optional). The console's
📧 card shows the setup and has **Send test email** (`POST /api/admin/notifier/test`).
**2026-09-30 — email design**: every mail is an Outlook-safe layout (nested tables, inline styles,
640px wide, shrinks on phones; Outlook for Windows ignores flex/grid/CSS classes). The ticket mail
shows (calm style since the 2026-09-30 redesign: white header under a thin blue line, soft tinted
badges): the ticket number and priority/status badges; *what the user needs help
with*; the user's note; details (who, when, SyteLine screen, record, why it was raised, mood); the
conversation before the ticket — each question with a plain-words outcome badge ("Answered from
documents", "Not found in documents", never `MARKDOWN_RAG_RESPONSE`) and the start of the answer;
*what to do next* (the same button names as the console: Start working → Mark resolved); and, when
`ADMIN_CONSOLE_URL` is set, an **Open in the support console** button. Security (red line), health
(amber / green line) and test mails use the same shell. A
plain-text copy is kept for SMTP. Working since 2026-09-30 (Graph login and a real test mail OK).
`documentation/ticket_email_preview.png` shows the ticket mail rendered from sample data.
**2026-10-05 — clearer ticket mail**: the title is now the user's actual problem, picked by
`policy.main_issue()` (the latest question that isn't the request for a person or small talk — before,
"can I talk to someone from support?" became the issue). Below it: a **Summary** panel with one plain
sentence (why the ticket exists + how far the assistant got, e.g. "The user asked to talk to the support
team. The assistant couldn't find this in the approved documents.") and Who / Where / Record / When; the
user's note; **The conversation** written as a chat (User / Assistant, with an outcome tag on real answers
only); two next steps. Mood and trigger codes are no longer listed separately. Older tickets are corrected
when read (`store._ticket_row`), so the console and the email show the real problem for them too.
**Tests never send real mail**: `tests/conftest.py` forces the log notifier for every test.

**API** (`api/routes.py`): `/chat` returns `escalation` (`state`, `trigger`, `ticket_available`) and
adds the offer text — "I can raise a support ticket… press 🎫 Create support ticket" when tickets can be
stored, otherwise "contact your SyteLine support team". `POST /api/tickets` (confirmed ticket, needs
`INSERT support_ticket`), `GET /api/tickets` (the user's own), `GET /api/admin/tickets` and
`GET /api/admin/security-events` (need `READ admin_console` — new mock group `SUPPORT_ADMIN`).
**Chat UI**: a 🎫 Create support ticket button under offered answers → optional note → Confirm →
"Ticket PTC-000123 created".

**Measured 2026-09-25 (live)**: normal questions and "how do I raise a quotation" → no offer; a
frustrated message → offer; confirm → `PTC-000005` created (high priority, steps attempted and note
filled), double click → same ticket; "can I talk to someone from support" → confirmation state; two
clarifications in a row → offer (unresolved); 3 prompt injections → 3 security events, 1 alert, no
ticket offer; a sales rep gets 403 on the admin endpoints; a NO_ACCESS user creates no security event.

---

## `backend/app/feedback/` (Phase 5 step 4, added 2026-09-28)

### `feedback/insights.py`
**What it is**: the feedback loop behind the admin console. Reads the conversation tables and
returns: a **summary** for the last N days (1–90) — answers, % answered (Excel or documents, out of
non-blocked questions), 👍/👎 and % rated helpful, open 👎 still to review, breakdowns by answer-check
result / mood / outcome, tickets by status, security events and alerts; the **👎 answers** with their
question, answer preview, route, check result, mood and sources; and the **content gaps** — every
NO_ANSWER question grouped by topic words (same helper as the tone manager's repeat check, ≥60%
overlap), most asked first, with the different wordings users typed and how many users asked.
An admin marks an item **📝 needs a document** (stays in the queue, flagged, and in the CSV),
**✅ reviewed** or **🚫 dismissed** (both leave the queue); "back to queue" clears it — stored in a new
`feedback_reviews` table. Also changes ticket status (open → in progress → resolved → closed) and
exports the gaps as CSV for the content team (cells starting with = + - @ are made plain text, so the
CSV can't run spreadsheet formulas). BLOCKED exchanges never appear (attacks live in the security
view) and every text is secret-redacted. **Limitation until Phase 6**: a user deleting a chat also
deletes its 👎 and unanswered questions from these lists.

**API** (`api/routes.py`, all need `READ admin_console`, changes need `UPDATE admin_console` — the
`SUPPORT_ADMIN` mock group): `GET /api/admin/overview?days=&include_reviewed=`,
`PUT /api/admin/feedback/{message_id}`, `PUT /api/admin/tickets/{ticket_id}`,
`GET /api/admin/content-gaps.csv`. Every console access is logged (`admin_console_access`).

### `frontend/chatbot/admin.html` / `admin.css` / `admin.js` (added 2026-09-28)
**What it is**: the feedback console at `http://127.0.0.1:8001/admin.html`, separate files so the chat
page is untouched. Filters (test group, period, show reviewed), six stat tiles, three breakdown
tables, and four tabs — 📝 Content gaps, 👎 Disliked answers, 🎫 Tickets, 🛡️ Security — each with
its review action. Status colours only for state (priority, severity, alerts), always with an icon
and a label. Light and dark mode; checked with Playwright at 1366px and 360px (no horizontal scroll,
no console errors). A non-admin role sees a 🔒 message and none of the data. All user text is set as
plain text (never HTML), so nothing a user typed can run in the admin's browser.

**2026-09-29 (Phase 6)**: two more tabs — **📈 Health** (live service checks, 24-hour tiles, four
per-day charts: questions, 95th-percentile response time, OpenAI cost, answer check; OpenAI calls
per purpose/model; time per workflow step; open and recent alerts; **Run health check now**) and
**🧾 Audit** (search the audit trail by user, event type, status or request id). Charts are plain
SVG with a hover tooltip on every mark, colours checked with the palette validator in light and
dark. `feedback/insights.py` now reads 👎 answers and content gaps from the audit trail when it is
available, so deleting a chat no longer hides them from the console.

**2026-09-30 — redesigned as the "Support console"** (the user found the tab page confusing): a
side menu (a scrolling row on phones) with **🏠 Home** first — four numbers (questions asked,
answered %, rated helpful, open tickets) and a *Needs your attention* list that shows only what has
work waiting, each with an **Open** button, plus a folded "How does this console work?" help. Then
🎫 Tickets (filter Open & in progress / Resolved / Closed / All; plain buttons **Start working**,
**Mark resolved**, **Close ticket**, **Reopen** instead of a status dropdown; the conversation and
details fold away), ❓ Unanswered questions (**Needs a document** / **Done** / **Ignore** / **Undo**,
download for the data team), 👎 Disliked answers, 🛡️ Security, 📈 System health (services in plain
names, alerts, charts, answer quality, the ticket-email card; OpenAI and per-step tables folded under
*Technical details*) and 🧾 Activity log (plain column names and results). Every internal code
(route, mood, answer check) is shown in plain words. Same API endpoints. Details added after a test
fill: each unanswered topic shows who asked (`users` in the gap, from `insights.group_questions`) and
what the assistant replied (`last_answer`); each disliked answer shows the answer, its source and up
to 4 documents it used; Security starts with a *Who was blocked* table (attempts, high risk, alerts
per user) and shows the latest 10 attempts with a **Show all** button.

**2026-09-30 — visual refinement:** the admin console now uses a blue/indigo neumorphic
workspace with stronger heading, navigation, filter and card hierarchy. Tickets separate the
user's note, conversation details and status actions; disliked answers display the assistant's
response in a distinct review panel. The chat ticket prompt also has a clearer support handoff,
labeled optional note and confirmation controls. The existing API and review actions are unchanged.
The layout was checked at phone, tablet and desktop widths and in dark mode.

`scripts/check_support_ui.py` is the repeatable visual smoke test for this UI. It exists to catch
horizontal overflow and broken ticket-form interactions after future styling changes. Run
`python -m scripts.check_support_ui` while the local server is on port 8001; it checks Home,
Tickets and Disliked answers at 390/768/1366 px, dark-mode Tickets, and the chat ticket form,
then saves screenshots under the system temporary directory without changing server data.

---

## `backend/app/audit/` and `backend/app/monitoring/` (Phase 6, added 2026-09-29)

### `monitoring/usage.py`
**What it is**: the per-request meter. `usage.start()` opens a measurement for one `/chat` request
(a contextvar, so parallel requests never mix); every OpenAI call goes through
`metered_create(purpose, client, **kwargs)`, which records model, purpose (`understanding`,
`classifier`, `scope`, `security`, `answer`, `answer_repair`, `grounding_check`), time, tokens in/out,
cost (from `MODEL_PRICES`) and failures; `traced()` records the time of every workflow step and
the history store records database time. `usage.end()` returns the totals.

### `audit/store.py`
**What it is**: the durable audit trail — Postgres table `audit_events`, **append-only** (a trigger
refuses UPDATE and DELETE; only the retention purge may delete, and it audits itself). One row per
question: request id, user, session, message id, route, status (SUCCESS / NO_ANSWER / CLARIFY /
BLOCKED / OUT_OF_SCOPE / NOT_AVAILABLE / ERROR), authorization result, security label, answer-check
result, mood, sources, SHA-256 of question and answer plus the (secret-masked) question text and a
300-character answer preview (`AUDIT_STORE_QUESTION_TEXT` / `AUDIT_STORE_ANSWER_PREVIEW` turn them
off), model versions, total / per-step / database time, every OpenAI call, tokens and cost. Also
one row per action: rating, chat deleted, ticket created, ticket status change, feedback review,
admin console access. Deleting a chat never deletes its audit rows. Rows older than
`AUDIT_RETENTION_DAYS` (365) are purged at startup and daily. Fail-soft: if Postgres is down the
chatbot still answers and the audit endpoints return 503.

### `monitoring/health.py`
**What it is**: operational health. `service_checks()` pings Postgres, Milvus and Redis and reports
process memory/CPU and uptime; `window_stats()`, `daily_series()`, `llm_breakdown()`,
`stage_breakdown()` read the audit trail. `evaluate_alerts()` runs every `MONITOR_INTERVAL_SECONDS`
(300) over the last `ALERT_WINDOW_MINUTES` (15) and checks: error rate > `ALERT_ERROR_RATE_PCT`,
95th-percentile response time > `ALERT_P95_LATENCY_SECONDS`, OpenAI fallbacks >
`ALERT_LLM_FALLBACK_RATE_PCT`, answered < `ALERT_ANSWERED_PCT_MIN` (rate rules only with at least
`ALERT_MIN_REQUESTS` questions), today's cost > `ALERT_DAILY_COST_USD`, and any service down. An
alert is raised **once** (table `monitoring_alerts`), logged, traced and sent through the notifier
(mail to `OPS_ALERT_EMAIL` when Outlook is on), and marked resolved once when the rule passes again.
The loop is started in `main.py` lifespan and cancelled at shutdown.

**API** (`api/routes.py`, need `READ admin_console`): `GET /api/admin/audit?days=&user_id=&event_type=&status=&request_id=&limit=`,
`GET /api/admin/health?days=`, `POST /api/admin/health/check` (runs the alert rules now). Each
answer's trace ends with `🧾 audit #… · ms · LLM calls · tokens · cost`.

**Tests**: `tests/test_audit.py` (12 — metering, cost, append-only trigger, purge, every action type,
search filters, console after chat delete) and `tests/test_health.py` (12 — each rule, raise-once /
resolve-once, minimum requests, endpoints and permissions).

---

## `backend/app/history/` (added 2026-09-24 — conversation history)

### `history/store.py`
**What it is**: conversation history in PostgreSQL (`ptc-postgres`). Creates two tables on startup
if missing — `chat_sessions` (session_id, user_id, title, created/updated time) and
`chat_messages` (every question and answer: content, the follow-up rewrite, route, sources, score,
decision trace, 👍/👎 rating, request id). Provides `recent_turns` (for follow-ups — skips BLOCKED
turns so rejected text is never fed to a model), `save_exchange`, `list_sessions`,
`get_session_messages`, `delete_session`, `delete_all_sessions`, `set_rating`. (2026-09-25: each
recent turn also carries its `route`, so escalation can count failed attempts; `shared_pool()` and
`owns_session()` let the escalation store use the same pool and ownership check.)

**Security**: every query is filtered by the trusted `user_id` from the session bootstrap. A user
can't read, rate, delete, or write into another user's conversation even with its session id.
**Fail-soft**: if Postgres is down at startup, the chatbot still answers (without memory) and logs
`history_store_unavailable`; only the `/api/history/*` endpoints return 503.

---

## `frontend/chatbot/` (Phase 1, extended in Phase 2)

### `index.html` / `style.css` / `script.js`
**What it is**: the chat page — plain HTML/CSS/JS, no build step, no framework (matches the
replica project's approach). Styling is neumorphic (soft dual-shadow raised/pressed shells, never
flat/glass panels), modeled on reference fintech-chat screenshots the user shared: clean near-white
panels (sidebar, context panel, chat card) with **one bold solid-blue gradient reserved for the
header bar, buttons, avatars, and user bubbles** — color is deliberate and concentrated, not spread
across every box. It is responsive from wide desktop (layout widens further past 1600px viewports)
to mobile: the chat workspace fills the available viewport, context fields reflow, message widths
adapt, and the history sidebar becomes an overlay drawer. Supports both the OS light/dark
preference and a manual override (see below), with a matching blue-only dark palette. Served
directly by the backend at `/` (see `main.py` below), so there's no separate frontend server or
port to keep in sync.

**2026-09-24 second refresh — new features**: a manual light/dark theme toggle button in the header
(🌙/☀️, persisted in `localStorage` under `ptc_theme`, overrides the OS preference via a
`data-theme` attribute on `<html>`); a 📋 copy-to-clipboard button on every bot answer; the message
composer is now an auto-resizing multi-line `<textarea>` (Enter sends, Shift+Enter inserts a
newline, grows up to 140px before scrolling); and a floating "scroll to latest message" button that
appears once the transcript is scrolled away from the bottom.

**2026-09-24 third refresh — professionalism pass**: the sidebar history list is now searchable
(`#history-search`, filters by title) and grouped into "Today / Yesterday / Previous 7 days /
Older" buckets by each conversation's last-activity timestamp — the common pattern in ChatGPT-style
tools, previously missing here. The composer shows a live character counter (`#char-counter`,
warns past 900/1000). A failed `/chat` request now renders as a distinct danger-styled message with
a **Retry** button that resends the same query (`requestAnswerFor()` in `script.js`), instead of a
plain unstyled error line. Esc now closes the context panel and, on mobile, the sidebar drawer.

Layout is a sidebar (New Chat button + a history list) plus the main chat column — the standard
chat-app pattern, and what the replica project's own frontend spec (§13) described. The sidebar
deliberately uses one clean neumorphic shell: New Chat is a single colored action and History rows
are flat with a slim active indicator, avoiding the distracting nested/double-rectangle background. The welcome state includes
quick-question chips that place a suggested question into the composer without sending it.
**History is stored in PostgreSQL (updated 2026-09-24)**: every `/chat` request sends the
conversation's `session_id`; on page load (and when the simulated group — i.e. the user — changes)
the sidebar is loaded from `/api/history/sessions`. Delete, Clear all, and 👍/👎 ratings are sent to
the server too. `localStorage` (`ptc_chat_sessions` / `ptc_active_session_id`, max 50) is now only
a fast cache and the fallback when the history service is down. A follow-up answer shows a small
"🔗 Understood as: …" note with the standalone question the bot actually answered.
**Answer check note (2026-09-25)**: answers that passed the Phase 5 validator show
"✅ Checked against approved documents"; curated Excel answers show "✅ Approved answer" (read from
the stored decision trace, so it survives a page reload).

**Why `script.js` calls `/chat` with a relative path, not a full URL**: the replica project had a
real bug where the frontend hardcoded one port while a deployment script used another. Since this
page is served by the same FastAPI app it talks to, a relative path always hits the right
host/port automatically — that whole class of bug can't happen here.

**Purpose going forward**: this is the Phase 1 "does it actually work" UI — just a chat box. Later
phases add source citations (done — see below), confidence display, and the escalation button the
master prompt describes for the full frontend (§13).

**Phase 2 addition — Context Simulator**: a collapsible panel (gear icon in the header) with a
simulated user-group dropdown (`SALES_REP` / `AR_CLERK` / `NO_ACCESS`) and Site/Module/Form text
fields, sent with every `/chat` request and persisted in `localStorage`
(`ptc_simulated_context`). Stands in for master prompt §3's real Context Bridge, which would read
this automatically from the actual SyteLine screen — not possible yet since there's no live
embedding, so this lets permissions and context flow through the pipeline be tested and
demonstrated now. The header badge next to it shows the current simulated identity at a glance.

**Phase 3 addition**: route badges now cover direct responses, out-of-scope refusals, and planned
capability routes. Bot messages persist and render a compact `intent → selected route` decision
note from the API's safe `decision_trace`. This also fixes greetings/chitchat: they now receive a
sub-intent-specific direct response (wellbeing, identity, capabilities, casual check-in,
introduction, thanks, acknowledgement, or farewell) rather than being incorrectly sent to Q&A/RAG
and displayed as “No match found.”

### `main.py` (updated)
Now also mounts `frontend/chatbot/` as static files at `/`, registered *after* the API router so
`/chat`, `/health`, `/api/info` are matched first — only requests those don't handle fall through
to serving the page/CSS/JS. The request middleware also returns the same `X-Request-ID` recorded
in the event log, which makes a browser/API failure traceable to its terminal and file entries.

---

## `logs/` (runtime output; not committed)

### `chatbot.log`
**What it is**: the single active application log requested for pin-to-pin visibility. It contains
the same application lifecycle, ingestion, request, permission, retrieval, response, and error
events shown in the terminal. Search one request ID to follow that request from entry to exit.

**Operational behavior**: created automatically on startup, ignored by git, rotated at 5 MB, and
limited to three backup files. Stack traces are captured for application failures. The log is for
diagnostics and audit development only; raw user text, answers, retrieved content, session tokens,
and credentials are intentionally excluded.

---

## `tests/` (Phase 3)

### `tests/test_phase3_orchestration.py`
**What it is**: 37 deterministic tests for attack categories and obfuscation, legitimate security
help, all five scope outcomes used by the current classifier, context-based ambiguity, query
transformation, hierarchical intent/route decisions, and LangGraph terminal branches. Tests disable
network/model classification so results stay fast and repeatable.

### `tests/test_conversation_history.py` (added 2026-09-24)
**What it is**: conversation understanding with a faked LLM (follow-up rewrite, unseen wording,
greeting + question, fallback to rules on timeout or invalid labels, caching), plus Postgres
store integration tests — recent turns skip BLOCKED, and a second user can't read/write/rate/delete
another user's conversation. The store tests skip automatically if `ptc-postgres` isn't running.

### `tests/test_small_talk.py` (added 2026-09-25)
**What it is**: 80 greeting and small-talk edge cases — 24 greeting variants, 7 look-alikes that
must NOT count as greetings, 25 chitchat variants, greeting + question stripping, the exact reply
text for each case, and scope keeping them in scope. Runs offline (LLM disabled).

### `tests/test_answer_validation.py` (added 2026-09-25)
**What it is**: 35 tests for the answer validator with a faked grounding LLM — unsupported
numbers, step numbering ignored, read-only action claims vs normal instructions, secret/prompt
leaks replaced without an LLM call, and every outcome (passed, repaired, replaced, not_found,
unverified, disabled). Runs offline.

### `tests/test_tone.py` (added 2026-09-25)
**What it is**: 50 tests for the tone manager — 23 mood phrasings (including "still"/"again" in
normal questions staying F0), repeated vs merely related questions, strongest-mood merge, approved
text kept word for word (never rewritten for any mood), lenient LLM mood labels, the conversation
LLM's mood beating the classifier, the tone reaching the answer prompt after the grounding rules,
and frustration never weakening a security block or a live-data refusal. Runs offline.

### `tests/test_escalation.py` (added 2026-09-25)
**What it is**: 38 tests for step 3 — the escalation policy table (every trigger, lookback window,
never for attacks/off-topic), ticket-request wording vs business questions, the confirmation reply,
ticket content (blocked turns left out, secrets redacted, cut at the chosen answer), and — against
`ptc-postgres`, skipped if it's down — one ticket per answer, no tickets on someone else's
conversation, one security alert per burst, severity levels, which results become security events
(a missing permission does not), and the ticket/admin API permissions.

### `tests/test_outlook.py` (added 2026-09-28)
**What it is**: 17 tests for Outlook ticket mail with Graph and SMTP faked (no real mail): subject,
recipients and HTML escaping, long issues shortened, missing `.env` values named (not shown), Graph
token + sendMail calls and token reuse, Graph errors never containing the secret, SMTP STARTTLS +
login, and the notifier recording sent / failed / not_configured / logged without ever raising.

### `tests/test_markdown_template.py` (added 2026-09-29)
**What it is**: 6 tests for the HRMS-style chunking — metadata / contents / change history not
indexed, title-only chunk dropped, inline and heading keywords both read, Tags added to every
section, writer comments stripped, section path keeps the title.

### `tests/test_data_templates.py` (added 2026-09-29)
**What it is**: 9 tests that keep the data-team templates loadable — the filled example passes the
checker, the blank template is rejected, the Markdown template indexes all 14 sections and nothing
else, the Word template converts to the same sections, the Excel template has exactly the loader's
columns, its example rows never go live, an APPROVED row needs a real reviewer, personal data and
TODOs are caught, bad file names rejected.

### `tests/test_trace.py` (added 2026-09-28)
**What it is**: 17 tests for the step-by-step logging — secrets masked, text kept on one line (no
forged log lines), long text shortened, text hidden when `LOG_CONVERSATION_TEXT=false`, helpers do
nothing outside a request, the terminal filter (trace + warnings by default, everything with
`LOG_TERMINAL=all`), the short trace format, real graph runs producing numbered steps that each end
with a result and a time (greeting, blocked attack, live-data route), a failing node traced and
re-raised, a describer bug never breaking the node, and every graph node having a title.

### `tests/conftest.py` (added 2026-09-28)
**What it is**: shared test setup — every test starts with the log-only notifier (run inline), so a
`.env` that turns Outlook mail on can never make the test suite send real email.

### `tests/test_feedback.py` (added 2026-09-28)
**What it is**: 15 tests for the feedback console — topic grouping (one gap for the same question
asked three ways, most asked first, open while any item is open), CSV formula-injection safety, and
against `ptc-postgres`: 👎 answers listed redacted and without blocked ones, gaps leaving the queue
when reviewed and returning when cleared, blocked messages can't be reviewed, summary counts, CSV
export, every console endpoint refused for SALES_REP / AR_CLERK / NO_ACCESS, and input validation
(bad status, unknown message, period over 90 days).

### `tests/__init__.py`
**What it is**: marks the test suite as a package and keeps future shared test helpers importable.

---

## `documentation/`

Planning and architecture documents. No code, nothing that runs in production — pure reference
material for whoever (human or AI) is building or maintaining this system.

### `REPLICA_BUILD_PROMPT.md`
**What it is**: a reverse-engineered build specification for a previously-built, working
role-based-access-control RAG chatbot (an HR knowledge-base assistant called "DeepChatbot" /
"HumaNET HR Chatbot").

**Why it exists**: it's the proven pattern library for this project's RAG core. Rather than
designing hybrid retrieval (BM25 + vector search + RRF fusion + cross-encoder rerank), the
ingestion pipeline (Excel Q&A + Markdown chunking), the caching layers, and the ticket-escalation
system from scratch, this project reuses that architecture where it applies and deliberately
deviates only where documented.

**Purpose going forward**: the reference to check "how did the working prior system solve this"
whenever we build a RAG-pipeline, ingestion, caching, or escalation module. Section 16 of that
document lists things the prior system did that are worth a conscious decision rather than a
blind copy (e.g. no real auth, RBAC-by-folder-duplication cost, CORS wide open) — worth
re-checking against each as we build the equivalent piece here.

### `SyteLine_Prospect_to_Cash_AI_Chatbot_MASTER_PROMPT.md`
**What it is**: the actual target specification for this project — an industrial-grade AI
chatbot for Infor SyteLine / CloudSuite Industrial (CSI), first business scope
**Prospect-to-Cash**.

**Why it exists**: it's the authoritative requirements + architecture document for what's
actually being built here. It defines the three-level architecture (frontend/SyteLine UI,
middleware/AI/security, backend/data/model), the non-negotiable rules (SyteLine is the sole
identity/permission source of truth, no separate chatbot login, AI never receives unauthorized
data), the three information sources (curated Q&A, Markdown RAG, live SyteLine data), the full
classification/routing/security pipeline, the SLM-routing + LLM-distillation + MLOps track, the
repository structure, the build order (§72), and the required phase-by-phase working process
(§77).

**Purpose going forward**: the single source of truth for scope and requirements. Every phase of
this build should trace back to a numbered section of this document. Section 73 lists everything
still marked `[NEEDS SYTELINE CONFIRMATION]` — unresolved technical facts about the real SyteLine
environment that must not be guessed.

### `SyteLine_Chatbot_Integration_Requirements.docx` / `.pdf` (added 2026-09-24)
**What it is**: the document to send to the SyteLine team. It explains how the chatbot will be embedded
in WebClient (floating button → right-side panel, one login, screen context, SyteLine-enforced
permissions), and lists 32 questions (A–H, 5 marked Blocker) with a blank "Answer" column plus a
checklist of APIs/access to provide. The `.pdf` is the same content for email. Their answers resolve
the `[NEEDS SYTELINE CONFIRMATION]` items in `ARCHITECTURE_DECISIONS.md` and unblock Phase 4.

### `Prospect_to_Cash_Modules_and_Data_Preparation_Guide.docx` / `.pdf` (added 2026-09-24)
**What it is**: a learning and content guide for the chatbot team and business users. Part A explains
the 18 Prospect-to-Cash modules in process order (flow diagram, before/after for each, and the topics
each knowledge file covers today — pulled from the `.md` files). Part B explains how to prepare the
three data sources (knowledge `.md`, Excel Q&A, glossary CSV) with writing rules, a quality checklist
and a weekly routine. Part C has fill-in templates for business users (module, Q&A, glossary).

### `SyteLine_API_Requirements_and_RBAC.docx` / `.pdf` (added 2026-09-25)
**What it is**: explains, for the SyteLine team, each of the 7 SyteLine API groups the chatbot needs
(login token, user/permission data, form/field metadata, screen context, read-only business data,
navigation, write actions — the last explicitly out of scope). For every API: what it is, why it is
needed, a numbered step-by-step example (\"Priya the Sales Rep asks…\"), an illustrative Mongoose
IDO REST request/response (marked to be confirmed), what breaks without it, how RBAC applies, and a
\"please confirm\" table. Then an end-to-end sequence diagram (\"Why is order S000123 on hold?\"),
the two RBAC layers, a same-question-two-users example, leak risks and protections, delivery
priority, and a checklist. Companion to the Integration and RBAC requirement documents.

### `SyteLine_RBAC_Permission_Requirements.docx` / `.pdf` (added 2026-09-25)
**What it is**: the RBAC-focused request to the SyteLine team (companion to the integration
requirements document). Explains how the chatbot uses permissions (read to explain, user's own
token to enforce), then 24 questions in six groups — security model, reading permissions via API,
field/record-level security, enforcement, changes/caching/audit, testing — with 7 marked Blocker and
a blank Answer column; a deliverables checklist with a Provided column; and a test-user matrix
(role × user ID, groups, sites, privileges per Prospect-to-Cash area) for them to fill. Its answers
replace the mock permission data in `authorization/resolver.py` and `session_context.py`.

### `data_templates/` (added 2026-09-29) — for the data team replacing the generic data
**What it is**: everything the data team needs to prepare our real company data per module.
`Data_Team_Instructions.docx` / `.pdf` (7 pages: what to deliver, how the chatbot uses it, the 18
module file names with priority, how to write the document and the workbook, approval workflow,
Word conversion, the checker, quality checklist, hand-over steps, FAQ).
`SyteLine_Module_Knowledge_Template.md` / `.docx` (the module document — follows the HRMS style:
metadata, contents, numbered sections each with Section Summary + Keywords, glossary — plus
SyteLine sections for roles/permissions, forms and navigation, key fields, one section per task,
status lifecycle, business rules with exact messages, what comes before/after, issues with
cause/solution/who fixes). `SyteLine_QA_Template.xlsx` (built by `scripts/build_data_templates.py`).
`example_credit.md` (a filled Credit example that passes the checker — generic content, shows the
expected detail).

### `Chatbot_Manual_Test_Cases.xlsx` (added 2026-09-25)
**What it is**: 50 manual test cases covering every flowchart level — greetings/small talk (incl.
typos and other languages), 6 security attacks + 1 legitimate security question, scope, ambiguity
A2/A4/A5/A6, Excel Q&A, Markdown RAG, transformations (typos, abbreviation, polite opener, synonym,
Spanish), multi-question/cross-module, three follow-up chats (F1–F3), live data / navigation /
action (Phase 4) and a NO_ACCESS permission test. Each row has the exact question, expected route
and badge, expected key points, and the reference answer captured from the live system (all 50
passed on 2026-09-25), plus columns for the tester's badge, notes and Pass/Fail (dropdowns). Sheets:
Test Cases, How to Test, Summary (auto-counts Pass/Fail per level).

### `SyteLine_Chatbot_Technical_Specification.docx` / `.pdf` (added 2026-09-24)
**What it is**: the full technical specification. It opens with one end-to-end flowchart of a chat
message (14 numbered steps, decisions and early exits) plus a plain-English walk-through, then covers
architecture and deployment, the request lifecycle with file/function per step, the trusted boundary,
every LangGraph node (security, follow-up, scope, ambiguity, transformation, classification and route
policy), unified retrieval with all constants, answer generation, the PostgreSQL schema, API, frontend,
security, logging, configuration, tests, how to run it, the phase-by-phase development history with
problems and fixes, the architecture decisions, known limitations and a file map.

### `ARCHITECTURE_DECISIONS.md`
**What it is**: a decisions log, created because the flowchart diagrams the user supplied and the
written master prompt disagreed on several points, and the master prompt's own §76 rule says
those conflicts must be surfaced and explicitly decided, never silently resolved.

**Why it exists**: keeps a durable record of every point where "the diagram says X, the written
spec says Y" was decided one way or the other, plus confirmed environment facts (e.g. the target
is the classic SyteLine WebClient, `ConfigGroup=AIDEMO`) and the running list of
`[NEEDS SYTELINE CONFIRMATION]` items still open.

**Purpose going forward**: append-only log. Every time a later phase surfaces a new conflict
between the written spec, the diagrams, or newly confirmed SyteLine facts, a new dated entry goes
here rather than the decision living only in chat history. This is what a future session (or a
teammate) reads to understand *why* the build deviates from the master prompt in specific,
deliberate ways.

### `BUILD_ROADMAP.md`
**What it is**: the 54-step build order from the master prompt (§72), grouped into 8 coherent,
shippable phases plus a note on cross-cutting concerns (CI/CD, environments, backup/DR, testing).

**Why it exists**: the user asked for the build to proceed phase by phase, not all at once (see
also `PROJECT_FILE_GUIDE.md`'s own update policy). This is the map that phase-by-phase work
follows, written once so each phase kickoff doesn't have to re-derive the sequencing or
re-explain why Phase 1 (the general replica-style RAG core) still includes a mocked permission
seam instead of skipping security entirely until Phase 2.

**Purpose going forward**: the checklist for "what's next." When a phase completes, its status
should be reflected here (e.g. mark it done, note any deviation from the plan) rather than only
living in chat history. If the phase grouping itself needs to change, edit this file rather than
letting the roadmap silently drift from what's actually being built.

### `PHASE_3_ORCHESTRATION.md`
**What it is**: the completed Phase 3 implementation record. It documents every orchestration
level, runtime order, full taxonomy, LangGraph branches, route behavior, greeting fix, API decision
trace, event-log sequence, configuration, tests, acceptance results, known boundary, and Phase 4
handoff.

### `PROSPECT_TO_CASH_KNOWLEDGE_BASE.md`
**What it is**: the pre-Phase-4 Markdown knowledge expansion record, including all module files,
official Infor source families, corrections to starter content, ingestion behavior, and the
site-validation work that remains before production approval.

### `PROJECT_FILE_GUIDE.md` (this file)
**What it is**: the file you're reading.

**Why it exists**: so anyone opening this repository — including a fresh Claude Code session with
no memory of this conversation — can find every file, understand what it's for, and know why it
was created, without having to reverse-engineer intent from the file alone.

**Purpose going forward**: update it in the same response that adds or meaningfully repurposes
any file in the project. When a new top-level folder is created (`backend/`, `frontend/`, `data/`,
`ml/`, `tests/`, `deployment/`, `scripts/` — per the repository structure in the master prompt
§5), add a new section here for it, and give each file within it the same three-part treatment:
what it is, why it exists, purpose going forward.
