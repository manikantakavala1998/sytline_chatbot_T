# Architecture Decisions Log — SyteLine Prospect-to-Cash AI Chatbot

> Tracks decisions made where the flowchart diagrams and the written master prompt
> (`SyteLine_Prospect_to_Cash_AI_Chatbot_MASTER_PROMPT.md`) disagreed, per that document's own
> §76 rule: never silently pick a side, identify the conflict, get an explicit decision. Append
> to this log as new conflicts/decisions arise in later phases — do not overwrite prior entries.

---

## Environment facts confirmed

- Target system is the classic **SyteLine WebClient** (ASP.NET), not the Infor OS / CloudSuite
  portal shell: `https://syteline.myhumanet.com/WSWebClient/Default.aspx?ConfigGroup=AIDEMO`
  (`ConfigGroup=AIDEMO`).
- This narrows (but does not fully resolve) how the chatbot panel gets embedded and how it
  receives the trusted logged-in session — still `[NEEDS SYTELINE CONFIRMATION]` (see below).
- Real SyteLine WebClient demo login credentials were given (2026-09-24), stored in `.env` only
  (never committed — see `.gitignore`): configuration name `AI_DEMO_DALS`, username `manikanta.k`.
  **This does not by itself resolve any `[NEEDS SYTELINE CONFIRMATION]` item** — knowing a
  username/password doesn't tell us the actual API surface (REST v2 / ION / Mongoose) the chatbot
  would need to call, which is still unconfirmed. Useful for a future live-connectivity
  exploration step (likely alongside Phase 4's SyteLine connector), not wired into any code yet.

---

## Resolved conflicts (2026-09-24)

### 1. Who generates the answer text for Help/RAG questions
**Decision: SLM generates simple answers by default; LLM handles complex reasoning as fallback.**

- Diagram (image 2 stage table, image 5 "Response Generation & Validation") wins over master
  prompt §41's stricter assignment ("RAG answer generation" = LLM-only job) and over the
  build-order implication in §72 (SLM only ever replaces the *router*, step 14 → 48; response
  generation is step 38, untouched by the SLM track).
- **Consequence for later phases**: the SLM needs its own groundedness/hallucination guardrail
  (can't rely solely on "LLM did it, LLM self-checks" the way the master prompt assumed).
  Define the confidence threshold that decides SLM-generates vs. LLM-fallback during the
  Response Generation Service phase (§72 step 38) and the SLM Router phase (§72 step 48).

### 2. Pipeline order: ambiguity resolution vs. intent/query classification
**Decision: Ambiguity resolution runs BEFORE intent/query classification**, matching the literal
LangGraph sequence written in master prompt §40 (`Security Gate → Scope Check → Ambiguity
Resolution → Query Classification → Route`) rather than the flowchart's order (image 2 runs
intent classification in step 4, ambiguity in step 5).

- **Consequence**: the Ambiguity Resolver (§72 step 13) must do its job (module/topic/persona
  ambiguity per master prompt §24) using only UI context, selected record, conversation history,
  and coreference resolution — *without* a prior intent label to lean on. Design it to be
  intent-agnostic.

### 3. Scope classification granularity
**Decision: 5-category internal classification** (SyteLine-related / Off-topic /
General-Knowledge / Competitor-or-Other-ERP / Irrelevant), still collapsing to a binary
in-scope/out-of-scope gate downstream — matching the flowchart (image 2 step 3) rather than
master prompt §22's literal binary-only definition (`SYTELINE | OFF_TOPIC`).

- **Consequence**: the Scope Classifier (§72 step 11) needs a 5-label taxonomy + a deterministic
  mapping table down to the binary route decision. The binary route/response behavior specified
  in §22 (fixed "outside scope" message, no general-LLM call) still applies unchanged — only the
  classifier's internal label set is richer, for telemetry/refusal-wording purposes.

### 4. Fast Q&A (Source A) vs. Markdown RAG (Source B) routing
**Decision: Keep FAST_QA and MARKDOWN_RAG as two distinct routes**, per master prompt §8–9 and
§26 — curated/approved Excel Q&A is tried first (fast, low-hallucination-risk); only a weak match
falls through to Markdown RAG. This overrides the flowcharts, which show a single consolidated
"Help/Knowledge (RAG)" flow with no separate curated-Q&A fast path.

- **Consequence**: the Fast Q&A Retriever (§72 step 18) is a standalone service/module, called
  before the RAG Service (§72 steps 19–32), exactly as master prompt §9's pipeline
  (normalization → acronym expansion → synonym mapping → context enrichment → exact match →
  BM25 → embedding similarity → hybrid Q&A score → evidence gate) describes. The Help/RAG
  flowchart module should be read as covering Source B only.

---

## Still open — `[NEEDS SYTELINE CONFIRMATION]`

Carried forward from master prompt §73, unresolved by the flowcharts or the login URL:

1. Exact technical mechanism for the chatbot to receive the logged-in SyteLine user/session
   (no second login) — WebClient context narrows the *shape* of the answer, doesn't give it.
2. How configuration, current site, user groups, individual overrides are obtained live.
3. How effective form/component/IDO/property permissions and row filters are obtained.
4. How current form/field/component/selected-record context is detected from the WebClient UI.
5. How the chatbot can trigger navigation (open form / open record) inside the WebClient.
6. Which integration method is approved: REST v2 / ION / Mongoose.
7. Which Prospect-to-Cash IDOs, properties, and methods are approved for the POC.
8. Which operations must stay read-only vs. may later support writes.
9. Where the chatbot UI is meant to be embedded within the WebClient shell.
10. Whether help/knowledge documents are themselves subject to form/module access rules.
11. Required permission-change propagation speed and audit/compliance retention policy.

None of these are invented or assumed — they block Level-1 (frontend context bridge) and the
live-data path (Source C) specifically, not the Fast-Q&A/RAG/security/classification work, which
can proceed against mocks per master prompt §18 ("create mocks so development can continue").
