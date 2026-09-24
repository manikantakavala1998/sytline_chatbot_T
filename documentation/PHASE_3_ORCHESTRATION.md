# Phase 3 — Security, Classification, Routing & LangGraph Orchestration

**Status: complete (2026-09-24).**

This phase inserts the orchestration layer between the trusted SyteLine/session boundary and the
retrieval or future tool layers. It implements master prompt build steps 10–15 and preserves the
runtime-order decisions recorded in `ARCHITECTURE_DECISIONS.md`.

---

## 1. Runtime boundary and complete flow

Session validation, user resolution, normalized context creation, and the base assistant
permission remain ordinary trusted application code in `api/routes.py`. They are deliberately not
placed inside AI prompts. After those checks, one normalized `RequestContext` enters LangGraph:

```text
HTTP /chat
  → Validate SyteLine session (mock adapter until live integration is confirmed)
  → Build trusted RequestContext
  → Check base assistant permission
  → LangGraph START
      → Input Security Gate
      → Five-label Scope Classifier
      → Ambiguity Resolver
      → Selective Query Transformation
      → Hierarchical Intent/Complexity/Emotion Classification
      → Code-enforced Route Selection
      ├─ BLOCK
      ├─ OUT_OF_SCOPE
      ├─ CLARIFY
      ├─ DIRECT_RESPONSE
      ├─ FAST_QA → optional Markdown RAG fallback
      ├─ MARKDOWN_RAG
      └─ Phase-4-or-later route → CAPABILITY_PENDING
  → API response + safe decision trace
  → LangGraph END
```

The agreed ordering is preserved: ambiguity resolution runs before intent classification. It uses
trusted UI/record context and does not rely on a pre-existing intent label.

---

## 2. Level-by-level implementation

### Level A — Input Security Gate

`backend/app/security/input_gate.py`

- Normalizes Unicode and common leetspeak.
- Inspects URL-decoded, separated-letter, and bounded base64-decoded variants.
- Uses category-specific regular expressions and contextual verb/object combinations; it is not a
  single keyword blacklist.
- Uses the orchestration LLM only for suspicious but inconclusive input.
- Fails closed if suspicious input needs semantic classification and the classifier is unavailable.
- Definite attacks never reach retrieval, answer generation, or any current/future SyteLine tool.

Security labels:

- `SEC_SAFE`
- `SEC_PROMPT_INJECTION`
- `SEC_PERMISSION_BYPASS`
- `SEC_SOCIAL_ENGINEERING`
- `SEC_OBFUSCATED_ATTACK`
- `SEC_TOOL_ABUSE`
- `SEC_DATA_EXFILTRATION`
- `SEC_CREDENTIAL_REQUEST`
- `SEC_MALICIOUS_INSTRUCTION`

### Level B — Scope Classification

`backend/app/classification/scope.py`

Internal labels are richer than the final binary decision:

- `SYTELINE_RELATED` → continue
- `OFF_TOPIC` → fixed scope response
- `GENERAL_KNOWLEDGE` → fixed scope response
- `COMPETITOR_OTHER_ERP` → fixed scope response
- `IRRELEVANT` → fixed scope response

The classifier uses curated SyteLine/Prospect-to-Cash vocabulary, the business glossary, explicit
out-of-scope categories, trusted UI context, and an LLM for unresolved cases. Out-of-scope input is
never sent to a general-answer LLM.

### Level C — Ambiguity Resolution

`backend/app/classification/ambiguity.py`

Labels:

- `A0_CLEAR`
- `A1_MISSING_TOPIC`
- `A2_MISSING_DETAIL`
- `A3_CONTRADICTORY`
- `A4_VERSION_RECENCY`
- `A5_REFERENTIAL_AMBIGUITY`
- `A6_MULTIPLE_ENTITY_MATCH`
- `A7_UNANSWERABLE`

The resolver first substitutes trusted current-record, field, and form references such as “this
customer” or “this field.” If required context is unavailable, it asks a clarification question
instead of guessing an identifier. Conversation-history resolution remains a later enhancement
because current history is browser-local and is not yet included in the API request.

### Level D — Selective Query Transformation

`backend/app/classification/query_transformer.py`

Implemented transformations:

- Unicode and whitespace normalization
- Focused spelling normalization for common domain mistakes
- Business-glossary synonym and acronym expansion
- Prospect-to-Cash entity and identifier extraction
- Multi-part query decomposition when explicit separators are present

Transformations are selected from the query shape; the pipeline does not run every possible NLP
technique on every request. HyDE remains optional future retrieval work, not a mandatory Phase 3
step.

### Level E — Hierarchical Classification

`backend/app/classification/taxonomy.py` and `router.py`

The classifier returns structured dimensions rather than one oversized intent list:

- Intent: greeting, chitchat, help variants, troubleshooting, live data, navigation, action,
  analysis, feedback, complaint, security help, mixed, or unknown.
- Complexity: direct, synonym variation, context shift, concept mapping, constraint-based,
  negative/exception, process/workflow, hypothetical, reverse logic, multi-part, comparison,
  root cause, or calculation.
- Emotion: normal, confused, complaint, frustrated, or persistent.
- Context fields: module, form, field, entity, operation, and an approved tool candidate.

The configured orchestration LLM performs the initial structured classification. Deterministic
classification provides resilient fallback behavior and handles trivial greetings without a model
call. The LLM may select only declared taxonomy values and a fixed candidate allowlist; code drops
unknown tool names.

### Level F — Code-Enforced Route Selection

Internal routes:

- `DIRECT_RESPONSE`
- `FAST_QA`
- `MARKDOWN_RAG`
- `LIVE_DATA`
- `RAG_IDO`
- `NAVIGATION`
- `ACTION`
- `LLM_REASONING`
- `CLARIFY`
- `OUT_OF_SCOPE`
- `BLOCK`

The final route is enforced from the structured intent in Python. Prompts cannot grant
authorization, enable writes, or invent tools.

### Level G — LangGraph Execution

`backend/app/orchestration/state.py` defines the typed graph state and final result.
`backend/app/orchestration/graph.py` compiles the graph once at application startup.

Available routes execute as follows:

| Selected route | Current behavior |
|---|---|
| `DIRECT_RESPONSE` | Deterministic greeting/chitchat/feedback response |
| `FAST_QA` | Route-specific permission → curated Excel Q&A → optional RAG fallback |
| `MARKDOWN_RAG` | Route-specific permission → hybrid RAG → grounded answer |
| `BLOCK` | Fixed safe security response; processing stops |
| `OUT_OF_SCOPE` | Fixed SyteLine scope response; processing stops |
| `CLARIFY` | Returns a targeted clarification question |
| `LIVE_DATA` / `RAG_IDO` | Clearly reports Phase 4 live-data dependency; never fabricates ERP values |
| `NAVIGATION` | Reports that the navigation connector is pending; opens nothing |
| `ACTION` | Reports read-only POC status; changes nothing |
| `LLM_REASONING` | Reports that controlled advanced reasoning is not enabled yet |

---

## 3. Greeting/chitchat correction

Before Phase 3, every message—including `hi`—was sent directly to Fast Q&A and then RAG, producing
an incorrect “No match found” answer. Greetings and basic chitchat now terminate before retrieval:

- `hi`, `hello`, and time-of-day greetings
- `How are you?`
- `Who are you?` / `What can you do?`
- thanks
- goodbye

These routes are deterministic, fast, and do not spend an LLM call.
Each chitchat sub-intent has its own answer: wellbeing directly answers “How are you?”, identity
describes the assistant, capabilities explains supported work, casual check-in stays conversational,
and introduction/thanks/acknowledgement/farewell each use appropriate wording.

---

## 4. API contract and UI visibility

`ChatResponse` now includes `decision_trace`, containing safe labels only:

```json
{
  "security": "SEC_SAFE",
  "scope": "SYTELINE_RELATED",
  "ambiguity": "A0_CLEAR",
  "intent": "HELP_GENERIC",
  "complexity": "DIRECT",
  "emotion": "F0_NORMAL",
  "selected_route": "FAST_QA",
  "tool_candidate": null,
  "transformations": ["entity_extraction"]
}
```

It never contains the session token, credentials, raw prompt, raw answer, or retrieved document
content. The frontend shows the response route plus a compact `intent → selected route` note.

---

## 5. Event and error logging

Every orchestration level emits the existing request ID to the terminal and `logs/chatbot.log`:

- `security_gate_completed`
- `scope_classification_completed`
- `ambiguity_resolution_completed`
- `query_transformation_completed`
- `query_classification_completed`
- `orchestration_route_selected`
- route-specific retrieval/permission events
- `orchestration_blocked`, `orchestration_out_of_scope`, or
  `orchestration_clarification_requested`
- `orchestration_completed`
- `chat_response_ready`

Classifier failures include stack traces and use safe fallback behavior. Raw questions and answers
remain excluded from logs.

---

## 6. Configuration

`.env.example` now documents:

- `ORCHESTRATOR_MODEL=gpt-4.1-mini`
- `ORCHESTRATOR_LLM_ENABLED=true`
- `ORCHESTRATOR_TIMEOUT_SECONDS=12`

`langgraph` and `pytest` are recorded in the single project `requirements.txt`.

---

## 7. Verification and acceptance results

- 37 deterministic tests cover security categories, obfuscated attacks, five-label scope,
  context-based ambiguity, transformations, hierarchical routes, and terminal LangGraph paths.
- Real HTTP verification covers greeting/chitchat, off-topic refusal, clarification, prompt
  injection blocking, Fast Q&A, live-data classification, navigation classification, and action
  classification.
- Browser verification confirms a newly submitted `hi` renders a direct greeting response.
- Live-data/navigation/action requests stop safely as `CAPABILITY_PENDING`; they are not answered
  from RAG or model memory and do not execute anything.

---

## 8. Phase 4 handoff

Phase 4 can connect the already-selected `LIVE_DATA`, `RAG_IDO`, and `NAVIGATION` branches to the
Prospect-to-Cash metadata catalogue, approved IDO/API connector, IDO Security Gateway, fixed Tool
Registry, and navigation bridge. `ACTION` remains read-only until the separately controlled-write
phase and explicit business approval.
