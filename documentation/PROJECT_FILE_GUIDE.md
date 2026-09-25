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
step from the master prompt's Fast Q&A pipeline (§9).

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
answers, or retrieved document text. Events record operational metadata only (route, duration,
score, counts, permission result, and safe context labels). Ingestion visibility remains included:
each source load, embedding operation, Milvus step, and index build still appears in both outputs.

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

### `scripts/generate_sample_qa.py`
**What it is**: the generator that writes the files above. Re-run it any time to regenerate all
14 files from the `LEVELS` dict inside it (it overwrites them). Add more dummy/starter rows here,
or edit the `.xlsx` files directly once real content replaces the placeholders. Generated starter
rows now carry DRAFT approval status. **Superseded (2026-09-24)** by `build_qa_from_knowledge.py`
below; kept only because that script reuses its column definitions.

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
**What it is**: calls the primary LLM to generate a grounded, cited answer from the retrieved
chunks (master prompt §34) — a deliberately simplified version of the full answer-generation
prompt. Role-aware tone and RBAC scope enforcement (the replica pattern's big system prompt) land
in Phase 5 per the roadmap; this only needs to prove grounded, cited answers work end to end,
which it does.

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
can be followed end to end without exposing credentials.

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

### `classification/conversation.py` (added 2026-09-25 — replaces `followup.py`)
**What it is**: LLM conversation understanding, run on every message right after the security gate.
One `gpt-4.1-mini` JSON call reads the message (plus the last 3 turns) and returns: `kind` (greeting,
wellbeing, thanks, farewell, identity, capabilities, acknowledgement, introduction, casual_checkin or
business), `greeting` (good_morning / good_afternoon / good_evening / good_night / hello),
`asked_wellbeing`, and `question` — the business request alone, greetings and pleasantries removed,
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

## `backend/app/history/` (added 2026-09-24 — conversation history)

### `history/store.py`
**What it is**: conversation history in PostgreSQL (`ptc-postgres`). Creates two tables on startup
if missing — `chat_sessions` (session_id, user_id, title, created/updated time) and
`chat_messages` (every question and answer: content, the follow-up rewrite, route, sources, score,
decision trace, 👍/👎 rating, request id). Provides `recent_turns` (for follow-ups — skips BLOCKED
turns so rejected text is never fed to a model), `save_exchange`, `list_sessions`,
`get_session_messages`, `delete_session`, `delete_all_sessions`, `set_rating`.

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
