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

## Phase 3 implementation decisions (2026-09-24)

### 5. Trusted boundary vs. LangGraph boundary
**Decision: session validation, identity/context construction, and base assistant authorization stay
in ordinary application code before LangGraph; LangGraph starts at the Input Security Gate.**

- The master graph draws Validate Session / Resolve Permissions / Build Context as graph nodes, but
  its non-negotiable security rules also say actual authorization must never live in prompts.
- **Consequence**: the API creates one trusted `RequestContext`, checks the user's base access, and
  then invokes the graph. Q&A and Markdown RAG nodes repeat route-specific permission checks.
  Models receive no session token and cannot change permission outcomes.

### 6. Phase 4 routes recognized before their connectors exist
**Decision: classify `LIVE_DATA`, `RAG_IDO`, `NAVIGATION`, and `ACTION` now, but terminate them as
`CAPABILITY_PENDING` until their authorized Phase 4 connectors exist.**

- Falling back to Q&A/RAG for a live balance or order status could return stale or invented data.
- Pretending navigation/action succeeded would violate the read-only POC and security architecture.
- **Consequence**: the user gets an explicit, route-specific explanation; no tool executes and no
  live ERP value is generated from documents or model memory.

### 7. Security classifier before the trained SLM exists
**Decision: use layered local detection plus the configured orchestration LLM only for suspicious
but inconclusive input, with a fail-closed result when semantic classification is unavailable.**

- The target architecture names a security SLM, but that model is produced in Phase 7 and cannot be
  assumed in Phase 3.
- Keyword-only blocking is insufficient and creates false positives for legitimate questions such
  as “How do SyteLine permissions work?”
- **Consequence**: normalization, bounded decoding, category regexes, and contextual combinations
  handle clear attacks locally. Only unresolved suspicious text reaches the temporary classifier.
  Phase 7 can replace that semantic component without changing the gate contract or graph.

### 8. Greeting/chitchat is a deterministic terminal route
**Decision: greetings and basic conversational messages use `DIRECT_RESPONSE`; they never enter
Fast Q&A, Markdown RAG, or a paid classifier call.**

- Before Phase 3, `hi` fell through Q&A/RAG and incorrectly returned “No match found.”
- **Consequence**: greetings, wellbeing/capability questions, thanks, and farewells are fast,
  reliable, and visible as `GREETING`/`CHITCHAT → DIRECT_RESPONSE` in the decision trace.

### 9. Starter Q&A cannot override reviewed Markdown drafts
**Decision: exclude the known `PTC Training Guide` sample rows from Fast Q&A ingestion, even when
older sample workbooks mark them APPROVED. Future generated samples are DRAFT.**

- The original sample answers included incorrect universal claims about order release and credit
  holds, and Fast Q&A takes precedence over Markdown RAG.
- **Consequence**: until real Q&A rows have a traceable source and business approval, help queries
  reach the expanded Markdown knowledge base. This does not weaken the `APPROVED` + active gate for
  genuine future Q&A rows.

### 9. Excel and Markdown share one index; the most confident source answers (2026-09-24)
**Decision: follow the replica pattern — Excel Q&A rows and Markdown chunks live in one Milvus
collection (`ptc_knowledge`, `source_type` = `excel` | `markdown`). Each question retrieves 10
candidates per source (vector + BM25 + RRF), one cross-encoder reranks all 20, and a curated Excel
answer is shown verbatim only when two independent signals agree.**

- Verbatim Excel requires an exact question/variation match, **or** question-match score ≥ 0.90
  **and** the reranker ranking that same row #1 of all 20. Measured on the knowledge-derived rows:
  correct matches 0.95–1.00, wrong near-misses 0.88–0.89 (e.g. "What is a customer order?" hit
  the order-*line* row). Everything else is generated from the strongest evidence of both sources.
- This supersedes decision #4's standalone Fast Q&A thresholds (0.80 strong / hybrid-gap
  "did you mean"), which mis-fired once the corpus grew to 132 similar rows. The Fast Q&A route
  still exists and still answers exact matches instantly.
- The earlier 19 starter rows were retired: they were placeholders and contradicted the
  knowledge base. The 132 new rows (`KB-xxxx`) are generated by
  `scripts/build_qa_from_knowledge.py` from the Markdown files with a grounding gate; they are
  marked APPROVED so the loader uses them, with `approved_by` stating SME review is still pending.

### 10. Conversation history in PostgreSQL; follow-ups resolved before scope (2026-09-24)
**Decision (user's choice): store sessions and messages in PostgreSQL (`ptc-postgres`), not Redis
or the browser. Use the last 3 exchanges to rewrite follow-up questions into standalone questions
in a new graph node between the security gate and the scope check.**

- Postgres over Redis: history is durable, relational (session → messages), audited (route,
  sources, rating per answer) and queried per user; Redis stays the permission cache.
- Resolution runs *before* scope/ambiguity (decision #2 said ambiguity must use conversation
  history): without it "how do I convert it?" is judged vague and gets a clarification request.
- Security gate still sees the raw message first; blocked turns are never fed back as history.
  History is owned by the trusted `user_id` — never by the client-supplied session id alone.
- History is fail-soft: Postgres being down removes memory, never the ability to answer.

### 11. An LLM understands greetings and small talk; rules are only the fallback (2026-09-25)
**Decision (user's request): a `gpt-4.1-mini` "conversation understanding" step reads every
message after the security gate and returns the message kind, greeting, "how are you" flag and the
clean standalone question (follow-ups resolved, translated to English). It replaces both the
word-list greeting detection as the primary path and the separate follow-up call.**

- Why: word lists can't keep up with real users ("good morning buddy" failed; slang, typos,
  emoji and other languages are endless). Measured live: 20/20 unseen phrasings in 5 languages
  handled after the prompt fixes, with no word added anywhere.
- Guardrails: the model only labels and rewrites — replies stay fixed templates, labels are enum-
  validated, and the security gate still runs first on the raw text (supersedes decision #8's
  "no model call for greetings").
- Cost/latency: one extra small call (≈0.8–1 s) per new message; pure small talk is cached
  (repeats ≈0.01 s). If the LLM is off or fails, `small_talk.py` rules answer instead.
- Future: fold this call and the intent classifier into one call to save ≈1 s per business
  question; Phase 7's SLM can take over the same JSON contract.

### 12. Every generated answer is validated against its evidence before it is sent (2026-09-25)
**Decision (Phase 5 step 1): `quality/answer_validator.py` runs rule checks (leaks, read-only
action claims, invented numbers) and a `gpt-4.1-mini` grounding check on every generated answer.
Unsupported claims → one regeneration without them; still unsupported → a safe refusal.**

- Why: the answer prompt already says "context only", but a prompt is a request, not a guarantee.
  A wrong SyteLine step or number is worse than no answer.
- Refusals and "not in the documents" replies become `NO_ANSWER`, so Phase 5 step 4 can list
  every unanswered question as a content gap.
- Fail behaviour: leaks are always blocked (rules, no LLM needed). If the grounding LLM is down,
  rule-clean answers are sent marked `unverified` rather than refusing every question.
- Curated Excel answers shown word for word skip the check — they are SME-approved text.
- Checker model: `gpt-4.1`, not `gpt-4.1-mini`. Mini was measured too literal (slang sweep fell
  49/52 → 42/52 because it rejected supported steps); `gpt-4.1` gave 50/52 and still caught 4/4
  invented forms, numbers, behaviours and buttons. Configurable via `ANSWER_VALIDATION_MODEL`.

### 13. Mood is read from the raw message; it changes tone only (2026-09-25)
**Decision (Phase 5 step 2): the conversation-understanding LLM returns the user's mood (F0–F4)
alongside its other labels — no extra call — and `quality/tone.py` rules act as a floor and
offline fallback. The strongest reading wins.**

- Why not the classifier's emotion: it reads the cleaned-up question, which has already lost the
  "!!!", CAPS, insults and "still not working" — it labelled almost everything F0.
- Mood changes the answer's tone, explanation style and the support offer (F3/F4). It never
  changes facts (the validator still runs after), security, permissions, or any refusal template.
- SME-approved Excel answers are never rewritten for tone; they only get a short opener.
- F3/F4 lead to a ticket offer through decision #14's escalation policy.

### 14. Support tickets need the user's confirmation; security events are a separate flow (2026-09-25)
**Decision (Phase 5 step 3): the bot offers a ticket (frustration, a persistent problem, two
unresolved answers, or the user asking for a human) but creates one only when the user presses
Confirm. Blocked attacks and blocked answer leaks go to `security_events`, never to tickets.
Storage is Postgres only for now; notifications go through a pluggable notifier (log today).**

- Why confirmation: master prompt §55 — no automatic tickets unless a business policy says so.
- Why build the ticket server-side from stored messages: the browser can't inject text into a
  ticket that the chatbot never saw; blocked turns and secrets are kept out.
- Why a separate security flow (§56): an attacker should not be able to file support tickets with
  their attack text, and security staff need severity, counts and alerts — not a support queue.
- Alert once per burst (3 blocks in 15 minutes by one user), so a scripted attack doesn't send
  hundreds of alerts. A missing permission is not an attack and is not recorded as one.
- Email (2026-09-28): tickets and alerts are emailed through Outlook — Microsoft Graph by default
  (app-only, Mail.Send), SMTP as a fallback — because the team already handles tickets in Outlook.
  Postgres stays the source of truth; mail is sent in the background and its delivery status is
  stored per ticket, so a mail failure is visible, never silent, and never blocks the user.
  The settings also accept the names the team's other bots use, so one `.env` style works for all.

### 15. The feedback console is a work queue, read from the conversation tables (2026-09-28)
**Decision (Phase 5 step 4): one admin page (`admin.html`, SUPPORT_ADMIN only) turns 👎 answers,
unanswered questions, tickets and security events into queues with review actions, instead of a
reporting dashboard. Unanswered questions are grouped by topic so the content team sees "payment
terms — asked 5 times by 3 users", not five separate rows.**

- Why read the existing tables instead of copying events: nothing new to keep in sync; the answer
  check, mood and escalation are already in each message's decision trace.
- Why a review status: without one the same 👎 stays on top forever and nobody knows what was done.
  "Needs a document" stays visible and goes into the CSV; "reviewed"/"dismissed" leave the queue.
- Known gap: deleting a chat deletes its feedback. Phase 6 (audit) adds retention that users can't
  delete.
- A separate page (not a panel inside the chat) keeps admin data and code away from every user's
  chat page.

### 16. Two log streams: a readable step trace and technical events (2026-09-28)
**Decision (user's request): every step of startup and of every question is written as a clear,
numbered trace to both the terminal and `logs/chatbot.log`; the technical `event=` lines stay in
the file and leave the terminal unless `LOG_TERMINAL=all`.**

- Why: the old log had ~25 key=value lines per question but never said what was asked, what was
  searched, which documents scored what, why the Excel answer was or wasn't used, or what the
  answer check flagged. The trace answers exactly those questions.
- Question / answer / document text now appears in the trace (it didn't before). It is on by
  default for development; `LOG_CONVERSATION_TEXT=false` hides it in production. Secrets are
  always masked and every value stays on one line.
- It paid off immediately: the trace showed "What is an estimate?" losing its approved Excel answer
  because the SyteLine-terms rewording won by 0.01. The user's own words now win unless the
  rewording is better by more than 0.05 (`TERMINOLOGY_MATCH_MARGIN`).
- It also showed why "what is so" was answered only sometimes: the right customer-order evidence
  was found, but the answer model only saw "What is SO?". When the question contains an ERP
  abbreviation (SO, CO, RMA, A/R, POs), the answer model and the answer check now also get the
  SyteLine-terms wording. Only then — giving the hint for ordinary wording was measured to pull
  "Explain the invoice lifecycle" toward generic process evidence (2 of 3 runs refused).

### 17. Tables: one vector per row, sentences instead of pipes, short keyword text (2026-09-29)
**Decision: every Markdown table row is written as a labelled sentence and gets its own vector
pointing back to its section; the section vector reads 1,500 characters instead of 300; keyword
search keeps its short text.**

- Why: the data team's documents are mostly tables. Before, 48% of table rows were invisible to
  search (only the first 300 characters of a section were indexed).
- Why sentences: an embedding of "Field: Credit Hold Reason · Form: Customer Orders · Meaning: why
  the order is held" is far closer to "what does credit hold reason mean?" than a row of `|` pipes.
- Why a vector per row (not a chunk per row): the answer still needs the whole table for context,
  and the Milvus search already keeps the best vector per section (as for Excel variations).
- Why keyword search stays short: indexing whole sections (or every row label) was measured to push
  the right section down for "how to ship an order"; the row vectors already cover the rows.
- Measured: 0 of 201 rows hidden; three questions about previously hidden rows now return the right
  section first; regression 50/50, slang 50/52 (the 2 known content gaps).

### 18. An append-only audit trail in Postgres; health alerts computed from it (2026-09-29)
**Decision (Phase 6): every question and every admin/user action is written to one `audit_events`
table that the application cannot edit or delete (database trigger); retention is a separate,
self-audited purge after 365 days. Monitoring reads the same table — no separate metrics system.**

- Why a database trigger instead of "the code doesn't update": the guarantee then holds for any
  code path, a bug or a manual SQL session. Only the purge sets `audit.retention_purge` for its own
  transaction.
- Why keep the audit apart from chat history: users may delete their chats (their right); the
  audit and the feedback console must still see what was asked and rated (closes the gap in #15).
- Why hashes plus masked text: the SHA-256 proves which question was asked even when text storage
  is switched off for production (`AUDIT_STORE_QUESTION_TEXT=false`).
- Why measure cost per call: six OpenAI calls per document answer (~$0.015); the per-purpose table
  shows where the money goes before Phase 7 moves calls to an SLM.
- Why Postgres instead of Prometheus/Grafana now: one server, tens of users; the same numbers can be
  exported later. Alerts are raised once and resolved once, so a slow afternoon sends one mail, not
  twelve; rate rules wait for 10 questions so one slow question at night is not an alert.
- Still to come with Phase 4: SyteLine API monitoring (call times, failures) — there are no live
  SyteLine calls yet.

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
