# Project File Guide

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

### `security/permission_seam.py`
**What it is**: a stand-in permission check that always says "allowed". Every place that will
eventually need a real SyteLine permission check already calls through this one function, so
Phase 2 only has to change what's *inside* this file, not every place that calls it.

**Why it exists**: per `ARCHITECTURE_DECISIONS.md` / `BUILD_ROADMAP.md` Phase 1 — the general
engine gets built now, but with the security seam already in place, never bolted on after.

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

---

> Living index of every file in this repository: what it is, why it exists, and what it's for.
> Update this file whenever a new file/folder is added to the project — treat it as mandatory
> bookkeeping for every future phase, not a one-time document. New entries go under the section
> matching where the file lives; add new sections as new top-level folders appear.

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
