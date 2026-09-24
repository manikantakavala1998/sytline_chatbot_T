# Build Roadmap — Phase Plan

> Groups the master prompt's 54-step build order (§72) into coherent, shippable phases. Each
> phase, when we execute it, gets the full §77 treatment (goal, dependencies, open
> `[NEEDS SYTELINE CONFIRMATION]` items, architecture/flow, I/O contracts, data structures, tasks,
> tests, acceptance criteria) and stops at a clean milestone before the next one starts. This file
> is the map; it is not itself a phase deliverable.
>
> Note: the numbering below is *implementation* order (which module gets built first), not
> *runtime* order. The runtime request flow inside Phase 3's LangGraph orchestrator follows the
> resolved decisions in `ARCHITECTURE_DECISIONS.md` (e.g. ambiguity resolution runs before intent
> classification at request time, even though the Scope Classifier gets *coded* before the
> Ambiguity Resolver).

---

## Phase 1 — General Foundation (replica-style RAG core, with a mocked permission seam)
Repo skeleton, config management, FastAPI foundation (§72.1–3) + a proven-pattern RAG engine
matching `REPLICA_BUILD_PROMPT.md`'s architecture: Excel Q&A schema + Fast Q&A retriever, document
ingestion + Markdown conversion + chunking, embedding service + Milvus, BM25 + vector + hybrid
retrieval + RRF + reranker, contextual compression + evidence sufficiency, RAG answer service
(§72.17–32). A basic `/chat` endpoint wires it together, plus a first-pass neumorphism-styled chat
UI so there's something to actually look at and test.

**Not skipped, just mocked**: every call that would eventually need a real permission check
passes through a stub `PermissionResolver` seam that always returns "allowed" (per master prompt
§18's own instruction to mock SyteLine dependencies so development can continue). The seam exists
architecturally from day one — Phase 2 swaps the mock for the real thing, it doesn't insert the
check for the first time.

**Proves**: the general engine works end-to-end — ingest → retrieve → answer — independent of any
SyteLine specifics.

---

## Phase 2 — Real SyteLine Identity, Session & Dynamic Permissions
SyteLine session integration, security bootstrap, Dynamic Permission Resolver, permission cache,
Frontend Context Bridge, Context Manager (§72.4–9).

**Blocked on**: most of the `[NEEDS SYTELINE CONFIRMATION]` list in `ARCHITECTURE_DECISIONS.md`
(session mechanism, permission APIs, form/field/record context detection). Where an item is still
unconfirmed when this phase starts, we build against a mock with the same interface the real
integration will have, so swapping it later doesn't touch calling code.

**Proves**: the Phase-1 mock permission seam gets replaced with real (or best-available) SyteLine
plumbing; the frontend chat panel knows what screen/field/record the user is actually looking at.

---

## Phase 3 — Security Gate, Classification & Routing
Input Security Gate, Scope Classifier, query taxonomy, Ambiguity Resolver, initial LLM-based
router, LangGraph orchestration (§72.10–15).

Implements the resolved decisions: 5-category internal scope taxonomy collapsing to a binary
route; ambiguity resolution wired to run before intent classification in the actual graph, even
though the modules are built in the order listed above.

**Proves**: malicious, off-topic, and ambiguous requests are caught and handled correctly before
ever reaching retrieval or generation — the security-first ordering the master prompt insists on.

---

## Phase 4 — Prospect-to-Cash Domain Data & Live ERP Integration
Prospect-to-Cash metadata catalogue, SyteLine connector, IDO Security Gateway, Tool Registry,
live-data service, navigation (§72.16, §72.33–37).

**Blocked on**: which IDOs/properties/methods are approved, REST v2 vs ION vs Mongoose (§73).

**Proves**: Source C (live ERP values — balances, order status, overdue invoices) becomes real,
gated through permissions and a fixed tool registry, never a freeform LLM-generated call.

---

## Phase 5 — Response Generation, Security & Conversational Quality
Response generation (SLM-default / LLM-fallback per the resolved decision), response security,
tone/frustration manager, support-ticket escalation, security escalation (§72.38–42).

**Proves**: answers are generated, validated against unauthorized/hallucinated content, toned
appropriately by role and frustration level, and both escalation paths (support vs. security) work.

---

## Phase 6 — Audit & Monitoring
Audit trail, application/AI/SyteLine monitoring (§72.43–44).

**Proves**: every request is traceable end to end (who asked, what was retrieved, what was
allowed, what was answered) and operational health is visible.

---

## Phase 7 — SLM Training, Distillation & MLOps
Routing dataset creation, teacher-LLM distillation, SFT + LoRA, SLM Router V1, SLM evaluation,
shadow mode, canary, production SLM routing (§72.45–52).

Replaces Phase 3's LLM-based router with a trained SLM router, and matures the Phase-5
SLM-generates-simple-answers threshold with real evaluation data before trusting it in production.

**Proves**: the cheaper/faster SLM path is measurably safe (schema-valid, correctly routed,
doesn't regress security classes) before it ever controls a real request.

---

## Phase 8 — Scale Out & Controlled Writes
Roll out the remaining Prospect-to-Cash domain areas in the order given in master prompt §7
(Lead → Opportunity → Estimate → Customer → Order → Pricing/Credit → Shipment → Invoice →
Payment → cross-process questions), each going through the full domain-activation checklist in
§71 before going live. Only after the read-only POC is proven does §72.54 (controlled
CREATE/UPDATE/RELEASE/APPROVE actions) get considered.

---

## Cross-cutting, not a numbered phase
CI/CD, environments (DEV/TEST/UAT/PROD), backup/DR, and the test suite (§65–68) are not a single
phase at the end — each gets whatever slice it needs added incrementally alongside the phase that
introduces the thing it's testing/deploying/backing up.
