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

### `.gitignore`
**What it is**: tells git which files/folders to never track — `.venv/`, `.env` (real secrets),
`__pycache__/`, generated data, editor folders.

**Why it exists**: keeps the real OpenAI key and other machine-specific junk out of version
control from the very first commit.

### `.env.example`
**What it is**: a template listing every setting the app reads from the environment, with blank
or safe default values. Safe to commit.

**Why it exists**: shows anyone setting up the project which settings exist and what to fill in,
without exposing real secrets.

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

---

## `backend/app/` (Phase 1 — foundation)

### `config.py`
**What it is**: loads every setting from `.env` into one `settings` object, and fails immediately
on startup if `OPENAI_API_KEY` is missing — never fails later mid-conversation.

### `main.py`
**What it is**: the FastAPI app itself. Deliberately small right now — just wires in the health
routes. The real `/chat` endpoint and the Q&A/Markdown search engine are the next Phase 1 step,
not yet built.

### `api/routes.py`
**What it is**: `/health` and `/api/info` — routes that prove the server is running. More routes
get added here as each later step builds them (starting with `/chat` next).

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
approved/active records may be used in production.

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
(`MARKDOWN_RAG`, not built yet). The score thresholds are starter values, explicitly not tuned —
the master prompt insists these come from real evaluation later, not a guess.

### `api/models.py`
**What it is**: the `ChatRequest`/`ChatResponse` shapes for the `/chat` endpoint.

### `utils/logger.py`
**What it is**: a shared logger so ingestion actually prints what it's doing to the terminal.
Added because startup used to jump straight from "Waiting for application startup" to
"Application startup complete" with zero visibility — the user asked why they couldn't see files
being ingested into Milvus, and the honest answer was that nothing logged it. Now every ingestion
step (each Q&A/Markdown file as it's read, embedding calls, the Milvus connect/rebuild/insert
sequence, BM25 index builds) prints a line via `get_logger(__name__)`.

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

### `scripts/generate_sample_qa.py`
**What it is**: the generator that writes the files above. Re-run it any time to regenerate all
14 files from the `LEVELS` dict inside it (it overwrites them). Add more dummy/starter rows here,
or edit the `.xlsx` files directly once real content replaces the placeholders.

### `data/knowledge/prospect_to_cash/*.md`
**What it is**: dummy Markdown knowledge docs (`customer_order.md`, `credit.md`, `shipment.md`,
`invoice.md`, `faq.md`) — the deeper content Fast Q&A can't answer (troubleshooting, business
rules and their exceptions, multi-step processes). Written with real heading hierarchy, a
`### Keywords` block, and a `**Section Summary:**` line per section — the authoring convention
the chunker is built around (see `rag/markdown_processor.py`).

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
shows *only* this project's `markdown_chunks` collection, nothing from any other project.

### `reranker.py`
**What it is**: the cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`, master prompt
§31) — scores each (query, chunk) pair directly for a more accurate relevance signal than
embedding similarity alone, run only on the already-narrowed candidate pool.

### `retriever.py`
**What it is**: the actual Markdown RAG pipeline (master prompt §27) — vector search + BM25 in
parallel, Reciprocal Rank Fusion to combine them, cross-encoder rerank, an evidence-sufficiency
gate (starter threshold, tested against this project's own dummy data — not a benchmarked
number), and simple contextual compression (caps total context by character budget, keeps only
chunks that clear the relevance bar rather than blindly keeping the top 5 regardless of score).

**Known limitation (found while testing, not fixed yet on purpose)**: some troubleshooting-style
questions ("why won't my order release") still get intercepted by Fast Q&A with a related-but-not-
quite-right answer (e.g. the "what is a Customer Order" definition), because Phase 1 has no intent
classifier yet to tell "define X" apart from "how do I fix X." That's Phase 3's job (Scope/Intent
Classification, per `BUILD_ROADMAP.md`) — expected at this stage, not a bug to chase down now.

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

### `context/manager.py`
**What it is**: builds one normalized `RequestContext` per turn (master prompt §20) — user
identity, groups, configuration/site, and whatever screen/field/record context the frontend sent.
Everything downstream reads this one object instead of raw session/UI data.

### `security/bootstrap.py`
**What it is**: Security Bootstrap (master prompt §2.1/§18) — establishes who the current user is
before anything else runs; no separate chatbot login. Raises `InvalidSessionError` on a missing
session token, which `/chat` turns into a `BLOCKED` response.

---

## `frontend/chatbot/` (Phase 1, extended in Phase 2)

### `index.html` / `style.css` / `script.js`
**What it is**: the chat page — plain HTML/CSS/JS, no build step, no framework (matches the
replica project's approach). Styled with neumorphism (soft, single-background-color panels with
light/dark dual shadows instead of borders), per the user's explicit request at the start of this
project. Served directly by the backend at `/` (see `main.py` below), so there's no separate
frontend server or port to keep in sync.

Layout is a sidebar (New Chat button + a history list) plus the main chat column — the standard
chat-app pattern, and what the replica project's own frontend spec (§13) described. **History is
client-side only right now** (saved in the browser's `localStorage`, capped at 50 conversations,
collapsed into a `ptc_chat_sessions` / `ptc_active_session_id` pair of keys) — there is no
backend conversation storage yet, so history won't follow you to another device or browser. Real
server-side session/history storage is a later phase (master prompt §10.2 History Manager /
§20 Context Manager), not built yet.

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

### `main.py` (updated)
Now also mounts `frontend/chatbot/` as static files at `/`, registered *after* the API router so
`/chat`, `/health`, `/api/info` are matched first — only requests those don't handle fall through
to serving the page/CSS/JS.

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
