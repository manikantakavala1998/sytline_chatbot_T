# MASTER PROMPT — Industrial SyteLine AI Chatbot for Prospect-to-Cash

## Purpose

Use this prompt to design and implement an **industrial-level AI chatbot for Infor SyteLine / CloudSuite Industrial (CSI)**.

The first production business scope is:

# **PROSPECT-TO-CASH**

This is not a simple LLM chatbot. It must be designed as an enterprise application with:

- Existing SyteLine login/session reuse
- Dynamic SyteLine authorization
- SyteLine screen/form/field/record context
- Security-first input handling
- Prompt-injection / jailbreak / permission-bypass protection
- Scope classification
- Intent classification
- Ambiguity handling
- Query complexity handling
- Frustration and conversational-quality handling
- Fast curated Q&A
- Markdown-based RAG
- Milvus vector database
- BM25 lexical retrieval
- Vector semantic retrieval
- Hybrid retrieval
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Query rewriting
- Multi-query generation
- Query decomposition
- Contextual compression
- Evidence sufficiency checking
- Live SyteLine IDO/API data
- Controlled navigation
- Controlled ERP actions
- LLM reasoning
- SLM routing
- LLM-to-SLM distillation
- SFT + LoRA training
- Shadow mode
- Canary deployment
- Model and dataset versioning
- Audit and observability
- Support-ticket escalation
- Security-event escalation
- CI/CD
- MLOps
- Testing
- Data governance
- Backup and disaster recovery

Do not skip any of these areas.

---

# 1. ROLE

Act as all of the following:

- Senior Enterprise Solution Architect
- Senior SyteLine / CSI Integration Architect
- Senior Python / FastAPI Architect
- AI / ML Architect
- RAG Architect
- Data Engineer
- MLOps Architect
- Security Architect
- Senior Chatbot Business Analyst
- QA / Test Architect
- DevOps Architect

Think from both business and technical perspectives.

Do not jump directly into coding.

First establish:

1. Requirements
2. Architecture
3. Data contracts
4. Security model
5. Module boundaries
6. Integration contracts
7. Data requirements
8. AI model responsibilities
9. Testing strategy
10. Deployment strategy

Only then generate implementation skeletons.

---

# 2. NON-NEGOTIABLE PROJECT RULES

## 2.1 SyteLine Login Is the Starting Point

The user logs into SyteLine first.

There must be **no separate chatbot login**.

Correct flow:

```text
User
  ↓
SyteLine Login
  ↓
SyteLine Authentication Success
  ↓
Chatbot Loads Inside / Alongside SyteLine
  ↓
Chatbot Receives Trusted SyteLine User / Session Context
  ↓
Security Bootstrap
  ↓
Context Manager
  ↓
Chatbot Ready
```

Do not:

- Ask the user to log in again
- Store SyteLine passwords
- Scrape credentials
- Send credentials to LLM/SLM
- Build an independent chatbot user database for authorization

The exact technical mechanism for receiving the logged-in SyteLine identity/session must be marked:

**[NEEDS SYTELINE CONFIRMATION]**

---

## 2.2 SyteLine Is the Authorization Source of Truth

SyteLine remains the source of truth for:

- User identity
- User groups
- Individual user overrides
- Configuration
- Site access
- Form permissions
- Component/field permissions
- IDO permissions
- IDO property permissions
- Row restrictions / filters
- Read/Execute/Insert/Update/Delete permissions
- Current business transaction data

Do not hard-code permissions.

Do not maintain user access manually in Excel.

Do not train permission decisions into an SLM.

Do not let LLM/SLM decide whether access is allowed.

AI may classify what a request is asking for, but actual authorization must be performed by deterministic application/security code using SyteLine effective permissions.

---

## 2.3 Permissions Must Change Dynamically

If an administrator changes:

- A user's group
- A form authorization
- A component authorization
- An IDO permission
- A row restriction
- A site permission

the chatbot must reflect that change without:

- Re-training the SLM
- Re-training the LLM
- Restarting the application
- Editing a manual permission table

Use:

```text
SyteLine Security
      ↓
Dynamic Permission Resolver
      ↓
Short-lived Permission Cache
      ↓
Current Effective Permission
```

Important write operations must support forced fresh authorization.

---

## 2.4 AI Must Never Receive Unauthorized Data

Wrong design:

```text
Fetch all ERP fields
      ↓
Send everything to LLM
      ↓
Ask LLM not to mention restricted fields
```

Correct design:

```text
Determine permissions first
      ↓
Request only allowed properties
      ↓
Apply row/site restrictions
      ↓
Return authorized data only
      ↓
Send safe data to AI
```

---

# 3. THREE-LEVEL ARCHITECTURE

Build the project around three main levels.

## LEVEL 1 — FRONTEND / SYTELINE UI LAYER

Responsibilities:

- Embedded chatbot panel
- Chat input
- Conversation display
- Streaming response display
- Existing SyteLine session reference
- Current configuration
- Current site
- Current module
- Current form/screen
- Current component
- Current field
- Current selected record
- Navigation handling
- User confirmation for actions
- User feedback
- Error messages

Create a **SyteLine Context Bridge**.

Example context:

```json
{
  "site": "MAIN",
  "module": "CRM",
  "form": "Customers",
  "component": "CreditLimitEdit",
  "field": "CreditLimit",
  "record_type": "Customer",
  "record_id": "C000125"
}
```

Do not send unnecessary sensitive values from the frontend.

The exact supported method for obtaining form/component/record context is:

**[NEEDS SYTELINE CONFIRMATION]**

---

## LEVEL 2 — MIDDLEWARE / AI / SECURITY LAYER

Primary technologies:

- Python
- FastAPI
- Pydantic
- LangGraph
- LangChain only where useful
- PostgreSQL
- Redis

Main middleware modules:

1. API Gateway / Edge integration
2. Session Validator
3. Authentication Adapter
4. Security Bootstrap Service
5. Dynamic Permission Resolver
6. Permission Cache
7. Context Manager
8. Input Security Gate
9. Scope Classifier
10. Query Understanding Engine
11. Ambiguity Resolver
12. Complexity Classifier
13. Frustration / Tone Classifier
14. Query Rewriting Service
15. SLM Router
16. LangGraph Orchestrator
17. Fast Q&A Retriever
18. RAG Service
19. Hybrid Retrieval Service
20. Reranker Service
21. Evidence Sufficiency Service
22. Tool Registry
23. IDO Security Gateway
24. SyteLine Connector
25. Navigation Service
26. Action Service
27. LLM Gateway
28. Embedding Gateway
29. Reranker Gateway
30. Response Generation Service
31. Response Security Service
32. Tone Manager
33. Support Escalation Service
34. Security Escalation Service
35. Audit Service
36. Telemetry / Monitoring
37. Error Handling
38. Configuration Management

Start as a **modular monolith**.

Do not create unnecessary microservices on day one.

---

## LEVEL 3 — BACKEND / DATA / MODEL LAYER

Includes:

### SyteLine / CSI

- Users
- Groups
- Sites
- Configurations
- Forms
- Components
- IDOs
- IDO properties
- IDO methods
- Row restrictions
- Transaction data

### Knowledge Sources

- SyteLine manuals
- Training documents
- SOPs
- Process documents
- Company policies
- FAQs
- Field help
- Screen help
- Business rules
- Troubleshooting documents
- Prospect-to-Cash training material

### Databases / Stores

- PostgreSQL
- Milvus
- Redis
- Object storage
- Audit store
- Model registry
- Dataset registry

### AI Model Servers

- SLM
- LLM
- Embedding model
- Reranker / cross-encoder

Model serving may later use:

- llama.cpp
- vLLM
- Ollama
- OpenAI
- Azure OpenAI
- another approved server

Do not tightly couple business logic to one provider.

---

# 4. INDUSTRIAL INFRASTRUCTURE AND PLATFORM REQUIREMENTS

Include:

- Reverse proxy / API gateway
- TLS
- WAF where required
- Rate limiting
- Request-size limits
- Secrets management
- Environment-specific configuration
- Connection pooling
- Health/readiness probes
- Structured logging
- Distributed tracing
- Metrics
- Alerting
- Backup
- Disaster recovery
- Containerization
- CI/CD
- MLOps
- Dependency scanning
- Container scanning
- Static analysis
- Audit retention policy

Never store:

- passwords
- API secrets
- bearer tokens
- SyteLine credentials

inside source code, Git, prompts, or logs.

---

# 5. PROJECT REPOSITORY STRUCTURE

Create:

```text
syteline-ai-assistant/
│
├── frontend/
│   ├── chatbot/
│   ├── context_bridge/
│   ├── navigation/
│   ├── confirmations/
│   ├── feedback/
│   └── errors/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── auth/
│       ├── authorization/
│       ├── context/
│       ├── security/
│       ├── scope/
│       ├── routing/
│       ├── orchestration/
│       ├── rag/
│       ├── retrieval/
│       ├── reranking/
│       ├── qa/
│       ├── tools/
│       ├── actions/
│       ├── navigation/
│       ├── integrations/
│       │   └── syteline/
│       ├── models/
│       ├── response/
│       ├── escalation/
│       ├── audit/
│       ├── telemetry/
│       ├── config/
│       └── errors/
│
├── data/
│   ├── metadata/
│   ├── knowledge/
│   ├── raw/
│   ├── processed/
│   ├── qa/
│   ├── evaluation/
│   └── registries/
│
├── ml/
│   ├── teacher/
│   ├── datasets/
│   ├── distillation/
│   ├── training/
│   ├── fine_tuning/
│   ├── evaluation/
│   ├── adapters/
│   └── registry/
│
├── tests/
│   ├── unit/
│   ├── api/
│   ├── integration/
│   ├── syteline/
│   ├── security/
│   ├── rag/
│   ├── retrieval/
│   ├── slm/
│   ├── llm/
│   ├── tools/
│   ├── e2e/
│   └── performance/
│
├── deployment/
│   ├── dev/
│   ├── test/
│   ├── uat/
│   └── prod/
│
├── docs/
│   ├── architecture/
│   ├── security/
│   ├── api/
│   ├── data_dictionary/
│   ├── runbooks/
│   └── decisions/
│
└── scripts/
```

For every folder explain:

- Purpose
- Important files
- Team ownership
- Whether it runs in production
- Whether it can contain sensitive data

---

# 6. PROSPECT-TO-CASH IS THE FIRST BUSINESS DOMAIN

Do not implement all SyteLine modules initially.

First scope:

# Prospect-to-Cash

Conceptual business flow:

```text
Prospect
   ↓
Lead
   ↓
Opportunity
   ↓
Estimate / Quote
   ↓
Customer
   ↓
Customer Order
   ↓
Customer Order Line
   ↓
Pricing / Credit Validation
   ↓
Fulfillment / Shipment
   ↓
Invoice
   ↓
Payment / Receivable
   ↓
Customer Follow-up
```

The exact SyteLine forms, IDs, IDOs, properties, methods, and process names must be validated.

Unknown technical mappings must be marked:

**[NEEDS SYTELINE CONFIRMATION]**

---

# 7. PROSPECT-TO-CASH DOMAIN ROLLOUT ORDER

Implement and inject the domain gradually.

Recommended order:

1. Prospect / Lead
2. Opportunity
3. Estimate / Quotation
4. Customer
5. Customer Order
6. Customer Order Lines
7. Pricing / Credit
8. Shipment / Fulfillment
9. Invoice
10. Payment / Receivables
11. Cross-process Prospect-to-Cash questions

For every domain:

```text
Functional Walkthrough
      ↓
Identify Forms
      ↓
Identify Fields
      ↓
Identify IDOs / Properties
      ↓
Prepare Q&A
      ↓
Prepare Markdown
      ↓
Add Metadata
      ↓
Ingest Knowledge
      ↓
Test RAG
      ↓
Connect Live Data if required
      ↓
Permission Tests
      ↓
Functional UAT
      ↓
Activate Domain
```

Do not activate a new domain simply because files were uploaded.

---

# 8. THREE INFORMATION SOURCES

The chatbot must clearly separate three different information sources.

## SOURCE A — CURATED FAST Q&A

Primary input:

**Excel**

Purpose:

- Fast response
- Common questions
- Standard definitions
- Approved answers
- Low latency
- Lower hallucination risk

Examples:

- What is a Prospect?
- What is an Opportunity?
- What is an Estimate?
- What is Due Date?
- What is Credit Limit?
- How do I create a Customer Order?
- How do I print a quotation?
- What is this field used for?

Do not use only Question and Answer columns.

Recommended Q&A master schema:

- qa_id
- domain
- process
- module
- form
- field
- intent
- sub_intent
- canonical_question
- answer
- keywords
- synonyms
- route
- source_reference
- source_section
- version
- site_scope if applicable
- security_scope
- approval_status
- approved_by
- effective_date
- active
- last_reviewed_date
- language

Create separate question-variation data:

- qa_id
- variation_id
- question_variation
- language
- source
- validated

Only APPROVED + ACTIVE records may be used in production.

---

# 9. FAST Q&A RETRIEVAL

Do not compare raw question strings only.

Pipeline:

```text
Question
   ↓
Normalization
   ↓
Acronym Expansion
   ↓
Synonym / Terminology Mapping
   ↓
Context Enrichment
   ↓
Exact Match
   ↓
Keyword / BM25 Match
   ↓
Embedding Similarity
   ↓
Hybrid Q&A Score
   ↓
Evidence / Match Quality Gate
```

If strong approved Q&A match:

```text
FAST_QA_RESPONSE
```

If weak:

```text
MARKDOWN_RAG
```

If ambiguous:

```text
CLARIFY
```

Do not force the nearest Q&A to be correct.

Thresholds must be determined through evaluation.

For frequently used approved Q&A, optionally use Redis caching.

Do not cache live transaction values without an explicit freshness policy.

---

# 10. SOURCE B — MARKDOWN KNOWLEDGE BASE

Use Markdown for detailed, structured business knowledge.

Potential sources:

- SyteLine manuals
- Training documents
- SOPs
- Internal process documents
- Training meeting notes
- Business rules
- Screen descriptions
- Field descriptions
- Troubleshooting guides
- Prospect-to-Cash procedures
- Company-specific procedures

Convert source documents to normalized Markdown while preserving:

- headings
- sections
- lists
- process steps
- tables
- references

The original source must remain traceable.

---

# 11. DOCUMENT INGESTION PIPELINE

Support:

- PDF
- DOCX
- PPTX
- XLSX
- CSV
- HTML
- TXT
- Markdown
- Images / screenshots
- Process diagrams
- Visio exports where extractable

Possible extraction tools:

- PyMuPDF
- python-docx
- python-pptx
- openpyxl
- pandas
- BeautifulSoup
- OCR only when necessary

Pipeline:

```text
Source File
   ↓
File Type Detection
   ↓
Text / Structure Extraction
   ↓
Clean
   ↓
Remove Duplicate Headers / Footers
   ↓
Normalize Encoding
   ↓
Deduplicate
   ↓
Document Classification
   ↓
Metadata Enrichment
   ↓
Convert / Normalize to Markdown
   ↓
Human Review Where Needed
   ↓
Approval
   ↓
Chunking
```

Do not automatically ingest bad OCR into production.

---

# 12. DOCUMENT GOVERNANCE

Lifecycle:

```text
NEW
 ↓
REVIEW
 ↓
APPROVED
 ↓
INGESTED
 ↓
ACTIVE
 ↓
SUPERSEDED / RETIRED
```

Every document needs:

- document_id
- title
- owner
- reviewer
- source
- version
- effective_date
- security_classification
- approval_status
- active status
- original file location
- Markdown location
- ingestion date
- embedding model version

Do not ingest unapproved documents into production RAG.

---

# 13. MARKDOWN ORGANIZATION

Example:

```text
knowledge/
└── prospect_to_cash/
    ├── prospect/
    ├── lead/
    ├── opportunity/
    ├── estimate/
    ├── quotation/
    ├── customer/
    ├── customer_order/
    ├── customer_order_line/
    ├── pricing/
    ├── credit/
    ├── shipment/
    ├── invoice/
    ├── payment/
    ├── troubleshooting/
    └── faq/
```

Possible files:

- overview.md
- process.md
- forms.md
- fields.md
- business_rules.md
- troubleshooting.md
- examples.md

Use only where appropriate.

---

# 14. CHUNKING ENGINE

Do not use one fixed chunker for every document.

Support:

- Markdown heading-aware chunking
- Semantic chunking
- Recursive splitting
- Sliding-window overlap
- Table-aware chunking
- Q&A chunking
- Step-aware process chunking
- Code/config chunking
- Field-specific chunking
- Troubleshooting issue/cause/resolution grouping

Initial experimentation range:

- 300–800 tokens
- overlap around 50–150 tokens

These are not fixed production values.

Benchmark them.

Preserve metadata:

- document ID
- source
- page
- section
- subsection
- domain
- process
- module
- form
- field
- version
- security scope
- approval status

Do not separate:

- a business rule from its exception
- troubleshooting cause from resolution
- process step from required condition
- a table row from the header required to understand it

---

# 15. EMBEDDING SERVICE

Create an EmbeddingGateway.

Responsibilities:

- document embeddings
- query embeddings
- batch processing
- normalization where required
- model version tracking
- vector dimension validation

Candidate model families may include:

- BGE
- E5
- other benchmarked embedding models

Do not select a model solely by popularity.

Benchmark on SyteLine/Prospect-to-Cash retrieval.

Store embedding_model_version with vectors.

---

# 16. MILVUS VECTOR DATABASE

Use Milvus for document knowledge vectors.

Suggested schema:

- chunk_id
- document_id
- text
- embedding
- domain
- process
- module
- form
- field
- document_type
- version
- source
- page
- section
- tags
- effective_date
- security_classification
- approval_status
- embedding_model_version
- created_at

Use metadata filtering.

Example:

```text
domain = PROSPECT_TO_CASH
AND
process = CUSTOMER_ORDER
AND
approval_status = APPROVED
AND
version = CURRENT
```

Index selection may use HNSW or another benchmarked index.

Do not blindly copy example values for:

- M
- efConstruction
- efSearch

Benchmark:

- Recall
- Latency
- Memory usage

---

# 17. SOURCE C — LIVE SYTELINE DATA

Live/current ERP values must come from SyteLine.

Examples:

- Customer balance
- Current order status
- Open orders
- Current inventory
- Current credit status
- Overdue invoices
- Production status

Do not answer these from:

- Excel Q&A
- Markdown
- Milvus
- LLM memory

Correct route:

```text
LIVE_DATA
   ↓
Permission Resolver
   ↓
Tool Registry
   ↓
IDO Security Gateway
   ↓
SyteLine Connector
   ↓
Live Result
```

SyteLine remains the source of truth.

---

# 18. SYTELINE SESSION BOOTSTRAP

Create:

- SyteLineSessionContext
- SyteLineSecurityContextService

Required capabilities:

- get_logged_in_user()
- validate_session()
- get_configuration()
- get_current_site()
- get_user_groups()

The actual supported implementation is:

**[NEEDS SYTELINE CONFIRMATION]**

Create mocks so development can continue.

Acceptance criteria:

- no second login
- invalid session rejected
- session not exposed to AI
- context refresh on site/session changes

---

# 19. DYNAMIC PERMISSION RESOLVER

Create DynamicPermissionResolver.

Support:

- group permissions
- individual overrides
- site access
- form access
- component access
- IDO access
- IDO property access
- row restrictions
- operation permissions

Operations:

- READ
- EXECUTE
- INSERT
- UPDATE
- DELETE

Use Redis short-lived caching.

Permission changes must not require AI retraining.

---

# 20. CONTEXT MANAGER

Create one normalized RequestContext.

Example:

```json
{
  "request_id": "...",
  "user": {
    "id": "U1001"
  },
  "erp": {
    "configuration": "PROD",
    "site": "MAIN"
  },
  "ui": {
    "module": "CRM",
    "form": "Customers",
    "component": "CreditLimitEdit",
    "field": "CreditLimit"
  },
  "record": {
    "type": "Customer",
    "id": "C000125"
  },
  "business": {
    "domain": "PROSPECT_TO_CASH"
  },
  "security": {
    "authorized": true
  }
}
```

Resolve references:

- this customer
- this order
- this field
- this screen
- that record
- the previous one

Use:

- UI context
- selected record
- recent conversation context

Never allow context to override permissions.

---

# 21. SECURITY GATE — FIRST AI/SAFETY STEP

Security must be checked before normal intent routing.

Detect:

- Prompt injection
- Permission bypass
- Social engineering
- Obfuscated attack
- Tool abuse
- Data exfiltration attempts
- Credential requests
- Malicious instructions
- Jailbreak patterns

Examples:

- "god mode"
- "forget everything"
- "forget previous instructions"
- "ignore system instructions"
- "act as admin"
- "pretend I have permission"
- "bypass security"
- "show hidden fields"

Do not use keyword matching alone.

Use:

```text
Normalization
   +
Pattern / Regex Rules
   +
Security SLM Classifier
   +
Context Evaluation
```

Security labels:

- SEC_SAFE
- SEC_PROMPT_INJECTION
- SEC_PERMISSION_BYPASS
- SEC_SOCIAL_ENGINEERING
- SEC_OBFUSCATED_ATTACK
- SEC_TOOL_ABUSE
- SEC_DATA_EXFILTRATION
- SEC_CREDENTIAL_REQUEST
- SEC_MALICIOUS_INSTRUCTION

If unsafe:

```text
BLOCK
 ↓
Safe Response
 ↓
Security Audit
 ↓
Optional Security Alert
 ↓
END
```

Never send blocked attacks to SyteLine tools.

---

# 22. SCOPE CLASSIFICATION

The chatbot is a SyteLine assistant.

Classes:

- SYTELINE
- OFF_TOPIC

Examples:

"What is Customer Order?"
→ SYTELINE

"What is the weather?"
→ OFF_TOPIC

Off-topic behavior:

Do not call a general LLM to answer.

Return only a scope message such as:

"This question is outside the scope of the SyteLine assistant."

---

# 23. HIERARCHICAL QUERY CLASSIFICATION

Do not create hundreds of flat intents.

Classify along multiple dimensions.

Output structured JSON containing:

- security
- scope
- intent
- sub_intent
- module
- form
- field
- entity
- operation
- ambiguity
- complexity
- emotion
- route
- tool_candidate

## Intent Classes

- GREETING
- CHITCHAT
- HELP_GENERIC
- HELP_SCREEN
- HELP_FIELD
- HELP_PROCESS
- TROUBLESHOOTING
- LIVE_DATA
- NAVIGATION
- ACTION
- ANALYSIS
- FEEDBACK
- COMPLAINT
- SECURITY_HELP
- MIXED
- UNKNOWN

## Ambiguity Classes

- A0 CLEAR
- A1 MISSING_TOPIC
- A2 MISSING_DETAIL
- A3 CONTRADICTORY
- A4 VERSION_RECENCY
- A5 REFERENTIAL_AMBIGUITY
- A6 MULTIPLE_ENTITY_MATCH
- A7 UNANSWERABLE

## Complexity Classes

- DIRECT
- SYNONYM_VARIATION
- CONTEXT_SHIFT
- CONCEPT_MAPPING
- CONSTRAINT_BASED
- NEGATIVE_EXCEPTION
- PROCESS_WORKFLOW
- HYPOTHETICAL
- REVERSE_LOGIC
- MULTI_PART
- COMPARISON
- ROOT_CAUSE
- CALCULATION

## Frustration / Emotion Classes

- F0 NORMAL
- F1 CONFUSED
- F2 COMPLAINT
- F3 FRUSTRATED
- F4 PERSISTENT

Frustration changes:

- tone
- explanation style
- escalation possibility

It must not change:

- facts
- security
- permissions

---

# 24. AMBIGUITY HANDLING

First try to resolve ambiguity from:

- current form
- selected field
- selected record
- current site
- recent conversation
- coreference resolution

If still ambiguous:

```text
ASK CLARIFICATION
```

Do not guess identifiers.

---

# 25. QUERY PREPROCESSING / TRANSFORMATION

After security and scope validation, support:

- Text normalization
- Spell normalization
- Acronym expansion
- Business glossary expansion
- Entity extraction
- Named Entity Recognition
- Terminology mapping
- Query rewriting
- Multi-query generation
- Query decomposition
- Contextual query expansion
- Coreference resolution
- Optional HyDE for selected difficult retrieval cases

Do not run every technique for every query.

Use:

- intent
- complexity
- ambiguity
- context

to select transformations.

---

# 26. THREE-SOURCE ROUTER

After classification:

```text
HELP_SIMPLE
→ FAST_QA

HELP_COMPLEX
→ MARKDOWN_RAG

LIVE_DATA
→ IDO_API

TROUBLESHOOTING
→ RAG and/or IDO

NAVIGATION
→ NAVIGATION_TOOL

ACTION
→ ACTION_WORKFLOW

MIXED
→ DECOMPOSE INTO SUB-TASKS

UNKNOWN / AMBIGUOUS
→ CLARIFY or LLM FALLBACK
```

---

# 27. HYBRID RAG RETRIEVAL

For detailed help:

```text
Question
   ↓
Query Rewrite
   ↓
Metadata Filters
   ↓
          ┌──────────────┐
          │              │
          ▼              ▼
       BM25          Vector Search
          │              │
          └──────┬───────┘
                 ▼
                RRF
                 ▼
           Candidate Set
                 ▼
        Cross-Encoder Reranker
                 ▼
         Duplicate Removal
                 ▼
          Diversity Check
                 ▼
     Contextual Compression
                 ▼
     Evidence Sufficiency Check
                 ▼
             Top Context
                 ▼
                LLM
```

---

# 28. BM25

Purpose:

- Exact words
- Product terminology
- Form names
- Field names
- Acronyms
- Error strings

Use lexical retrieval.

Do not rely only on vector similarity.

---

# 29. VECTOR SEARCH

Purpose:

- Semantic similarity
- Synonyms
- Natural-language variation
- Conceptual matches

Use query embedding → Milvus similarity search.

---

# 30. RECIPROCAL RANK FUSION (RRF)

Use RRF to combine BM25 and vector rankings.

Concept:

```text
RRF_score(document)
=
Σ 1 / (k + rank)
```

The exact `k` must be benchmarked.

---

# 31. CROSS-ENCODER RERANKING

After hybrid retrieval, rerank candidates using a cross-encoder / reranker.

Purpose:

- Better query-document relevance
- Remove weak semantic matches
- Improve final context quality

Selection must be evaluation-driven.

---

# 32. CONTEXTUAL COMPRESSION

After reranking:

- remove redundant chunks
- retain relevant passages
- respect token budget
- preserve source metadata
- preserve important exceptions/conditions

---

# 33. EVIDENCE SUFFICIENCY CHECK

Before answer generation ask:

- Do we have enough evidence?
- Are retrieved sources approved?
- Are sources current?
- Do sources conflict?
- Is the required answer actually present?

If evidence is insufficient:

- ask clarification
- report unavailable information
- do not hallucinate

---

# 34. RAG ANSWER GENERATION

Use:

- approved retrieved context
- safe screen context
- question
- source metadata

Generate:

- clear answer
- citations / source references
- step-by-step process if required

Do not let RAG answer current ERP values.

---

# 35. SYTELINE IDO/API CONNECTOR

Create:

```text
integrations/syteline/
```

with concepts such as:

- SyteLineConnector
- IDOClient
- SessionAdapter
- RequestBuilder
- ResponseValidator
- ExceptionMapper

Support:

- configuration
- site
- IDO
- property selection
- filters
- approved methods
- timeouts
- error mapping

Do not allow LLM to generate arbitrary URLs.

Actual REST v2 / ION / Mongoose implementation is:

**[NEEDS SYTELINE CONFIRMATION]**

---

# 36. IDO SECURITY GATEWAY

Every live data/action call must pass through:

```text
Tool
 ↓
IDO Security Gateway
 ↓
User Check
 ↓
Site Check
 ↓
Form Check
 ↓
Component Check
 ↓
IDO Check
 ↓
Property Check
 ↓
Row Restriction Check
 ↓
Operation Check
 ↓
ALLOW / DENY
```

Only allowed data can leave the gateway.

---

# 37. TOOL REGISTRY

Models may only select from approved tools.

Conceptual examples:

- get_customer()
- get_customer_balance()
- get_customer_orders()
- get_overdue_invoices()
- get_item()
- get_inventory()
- get_purchase_order()
- get_production_order()
- open_form()
- create_activity()

Actual IDO mappings are:

**[NEEDS SYTELINE CONFIRMATION]**

Each tool needs:

- name
- description
- input schema
- output schema
- READ/WRITE category
- required permission
- required IDO
- allowed properties
- timeout
- audit category

Models may not invent new tool names.

---

# 38. NAVIGATION

Support:

- open form
- open selected record
- navigate to related form

Before navigation:

- validate form execution permission

The actual UI navigation mechanism is:

**[NEEDS SYTELINE CONFIRMATION]**

---

# 39. ACTION / TRANSACTION WORKFLOW

Initial POC must be READ-ONLY.

Target architecture may later support:

- CREATE
- UPDATE
- DELETE
- RELEASE
- APPROVE
- POST
- STATUS CHANGE

Flow:

```text
Action Request
   ↓
Authorization
   ↓
Validate Input
   ↓
Prepare Proposed Change
   ↓
Show Confirmation
   ↓
User Confirms?
   ├─ No → Cancel
   └─ Yes
        ↓
Fresh Authorization
        ↓
Execute Approved Tool
        ↓
Verify Result
        ↓
Audit
```

Never allow unrestricted autonomous ERP writes.

---

# 40. LANGGRAPH ORCHESTRATION

Use LangGraph as the workflow controller.

State contains:

- request context
- security result
- scope result
- query classification
- ambiguity
- route
- Q&A result
- retrieved chunks
- tool results
- model outputs
- validation state
- audit state

Graph:

```text
START
 ↓
Validate Session
 ↓
Resolve Permissions
 ↓
Build Context
 ↓
Security Gate
 ↓
Scope Check
 ↓
Ambiguity Resolution
 ↓
Query Classification
 ↓
Route
 ├─ BLOCK
 ├─ OUT_OF_SCOPE
 ├─ CLARIFY
 ├─ FAST_QA
 ├─ RAG
 ├─ IDO
 ├─ RAG_IDO
 ├─ NAVIGATION
 ├─ ACTION
 └─ LLM_REASONING
 ↓
Combine Results
 ↓
Generate Response
 ↓
Response Security
 ↓
Tone Manager
 ↓
Escalation Check
 ↓
Audit
 ↓
END
```

Do not place actual authorization logic inside prompts.

---

# 41. MODEL RESPONSIBILITIES

## Embedding Model

Used for:

- document vectors
- query vectors
- semantic retrieval

Not for:

- reasoning
- authorization

## SLM

Used for:

- security classification support
- scope classification
- intent classification
- module detection
- form detection
- field detection
- entity extraction
- ambiguity classification
- complexity classification
- route selection
- tool candidate selection
- simple query normalization

The SLM must not learn:

- current customer balance
- current inventory
- current user access
- live order status
- actual permission decisions

## LLM

Used for:

- complex reasoning
- mixed-query decomposition
- troubleshooting synthesis
- RAG answer generation
- combining RAG + live data
- difficult interpretation
- teacher model for SLM training
- fallback when SLM output cannot be trusted

## Reranker Model

Used for:

- query-document relevance after retrieval

---

# 42. SLM TRAINING — WHAT WE ACTUALLY TRAIN IT WITH

Do not train the SLM with "SyteLine itself."

Train it using:

```text
User Question
+
Safe Context
+
Correct Structured Output
```

Example:

Input:

```text
Question:
"Show overdue invoices for this customer."

Context:
module = CRM
form = Customers
```

Expected output:

```json
{
  "security": "SAFE",
  "scope": "SYTELINE",
  "intent": "LIVE_DATA",
  "module": "CRM",
  "entity": "CUSTOMER",
  "operation": "OVERDUE_INVOICES",
  "ambiguity": "CLEAR",
  "complexity": "DIRECT",
  "route": "IDO",
  "tool": "get_overdue_invoices"
}
```

This input/output pair is training data.

---

# 43. SLM TRAINING DATA SOURCES

Use:

- manually designed examples
- functional consultant scenarios
- approved Q&A questions
- approved Markdown documents as grounding for scenario generation
- real sanitized production questions
- existing chatbot test cases
- teacher-LLM-generated variations
- security test cases
- ambiguity cases
- synonym cases
- troubleshooting cases
- mixed queries
- frustration cases

Do not simply feed all Markdown into SFT.

Documents remain in RAG.

Use documents to create accurate training examples and labels.

---

# 44. LLM-TO-SLM DISTILLATION

Concept:

```text
Large LLM
Teacher
   ↓
Creates / Labels High-Quality Examples
   ↓
Rule Validation
   ↓
Human / Functional Review
   ↓
Approved Dataset
   ↓
Student SLM Training
```

Teacher generates:

- paraphrases
- synonyms
- terminology variations
- hard examples
- negative examples
- workflow questions
- hypothetical questions
- reverse-logic questions
- mixed queries
- ambiguity cases
- security cases
- off-topic examples

Never train automatically on raw unreviewed teacher output.

---

# 45. SFT AND LoRA

Use:

## Supervised Fine-Tuning (SFT)

SFT teaches the expected behavior from labeled examples.

Concept:

```text
Input
 ↓
Model Prediction
 ↓
Compare Against Correct Output
 ↓
Calculate Training Loss
 ↓
Update Trainable Parameters
 ↓
Repeat
```

## LoRA

LoRA makes fine-tuning efficient.

Concept:

```text
Base SLM Weights
   FROZEN
      +
Small Trainable LoRA Adapter
      ↓
SyteLine Router Specialization
```

Important:

- SFT = training method
- LoRA = parameter-efficient adaptation method

Use:

```text
SFT + LoRA
```

for the first routing SLM.

---

# 46. TRAINING PIPELINE

```text
Manual Examples
+
Real Sanitized Queries
+
Functional Scenarios
+
Teacher LLM Examples
        ↓
Cleaning
        ↓
Remove Sensitive Data
        ↓
Schema Validation
        ↓
Label Validation
        ↓
Tool Validation
        ↓
Human / Consultant Review
        ↓
Approved Dataset
        ↓
Train / Validation / Test Split
        ↓
Base Pretrained SLM
        ↓
SFT + LoRA
        ↓
SLM Router V1
        ↓
Offline Evaluation
        ↓
Shadow Mode
        ↓
Canary
        ↓
Production
```

---

# 47. TRAIN / VALIDATION / TEST

Do not train on all records.

A typical starting split may be:

- Train ~70%
- Validation ~15%
- Test ~15%

Exact split can change.

Never evaluate using only training examples.

---

# 48. SLM EVALUATION

Measure:

- security classification accuracy
- off-topic accuracy
- intent accuracy
- route accuracy
- module accuracy
- entity accuracy
- ambiguity accuracy
- tool accuracy
- JSON validity
- unknown detection
- fallback rate

Use confusion matrices.

Security-sensitive classes require stricter acceptance criteria.

Do not promote based only on overall accuracy.

---

# 49. SHADOW MODE

Initially:

```text
Question
   ├─→ LLM Primary Classification
   └─→ SLM Shadow Classification
```

Compare outputs.

Log:

- match
- mismatch
- LLM correction
- SLM error
- human validation

SLM does not control the real route yet.

Use mismatches to create Dataset V2.

---

# 50. PRODUCTION SLM ROUTING

After evaluation:

```text
Question
   ↓
SLM
   ↓
Schema + Rule Validation
   ↓
Known / Valid?
   ├─ Yes → Use Route
   └─ No → LLM Fallback
```

Do not trust only model self-reported confidence.

Use:

- schema validation
- allowed-label validation
- allowed-tool validation
- consistency checks
- evaluation-derived rules
- unknown detection

---

# 51. MODEL REGISTRY

Version:

- router-v1
- router-v2
- router-v3

Track:

- base model
- LoRA adapter
- dataset version
- training parameters
- evaluation results
- approval
- deployment date
- rollback model

Never deploy an untraceable "latest" model.

---

# 52. DATASET REGISTRY

Version:

- router-data-v1
- router-data-v2
- router-data-v3

Track:

- source
- review status
- number of examples
- class distribution
- security cases
- train/val/test split
- reviewer
- lineage

Always know:

```text
Which dataset trained which model?
```

---

# 53. RESPONSE SECURITY

Before returning an answer validate:

- unauthorized fields
- wrong-site data
- wrong-record data
- hidden component values
- unsupported claims
- hallucinated IDs
- invalid tool result
- outdated document use
- RAG groundedness
- source citations
- contradiction
- sensitive information

Do not rely only on LLM self-check.

Combine deterministic and AI-assisted validation.

---

# 54. CONVERSATIONAL QUALITY

Desired response qualities:

- polite
- respectful
- warm
- natural
- professional
- approachable
- solution-focused
- active voice
- concise when possible
- supportive when user is confused

For F3/F4 frustration:

- avoid repeating failed instructions
- summarize what has already been tried
- provide next diagnostic step
- consider ticket escalation

Do not weaken security for frustrated users.

---

# 55. SUPPORT TICKET ESCALATION

States:

- ESC_NONE
- ESC_SUGGEST_TICKET
- ESC_CREATE_TICKET_AFTER_CONFIRMATION

Possible trigger:

```text
Repeated Same Topic
+
Multiple Failed Attempts
+
High Frustration
+
Unable to Resolve
```

Ticket may contain:

- user
- site
- module
- form
- safe record reference
- issue summary
- steps attempted
- error
- safe conversation summary
- timestamp

User confirmation required unless future business policy explicitly permits automatic creation.

---

# 56. SECURITY ESCALATION

Security attacks use a separate flow.

Example:

```text
Permission Bypass Attempt
 ↓
BLOCK
 ↓
Audit Security Event
 ↓
Optional Alert
```

Do not treat a security event as an ordinary support ticket unless policy requires it.

---

# 57. DATA TEAM RESPONSIBILITIES

The Data Team must prepare version-controlled assets.

## Structured Metadata

- Module Master
- Process Master
- Form Master
- Component Master
- Field Master
- Form-to-IDO Mapping
- Field-to-IDO-Property Mapping
- IDO Method Catalogue
- Site / Configuration metadata
- Business Glossary
- Data Security Classification
- Tool Catalogue
- Intent Catalogue

## Q&A Assets

- Prospect-to-Cash Q&A Master
- Question variations
- Approval status
- Source references
- Version information

## Knowledge Assets

- Original approved documents
- Converted Markdown
- Document metadata
- Chunk metadata
- Vector ingestion reports

## ML Assets

- Intent dataset
- Security dataset
- Ambiguity dataset
- Routing dataset
- SLM training dataset
- Validation dataset
- Test dataset
- Evaluation results

Data Team must not invent:

- SyteLine permissions
- business rules
- form mappings
- IDO mappings
- property mappings

Those require functional/technical validation.

---

# 58. TEAM RESPONSIBILITIES

Create a RACI-style ownership matrix for:

### SyteLine Functional Consultant

Owns/validates:

- Prospect-to-Cash process
- business definitions
- workflows
- exceptions
- forms from business perspective
- expected user behavior
- UAT answers

### SyteLine Technical Consultant

Owns/validates:

- forms
- components
- IDOs
- properties
- methods
- REST/ION integration
- context/navigation mechanisms

### SyteLine Admin / Security

Owns/validates:

- users
- groups
- effective permissions
- site access
- authorization model
- security changes

### Data Team

Owns:

- extraction
- cleaning
- mapping
- Markdown conversion
- metadata
- Q&A master
- document registry
- ingestion
- vector pipeline
- datasets
- evaluation data

### AI/ML Team

Owns:

- embeddings
- hybrid retrieval
- RRF
- reranking
- LLM
- SLM
- distillation
- SFT/LoRA
- model evaluation

### Backend Team

Owns:

- FastAPI
- integrations
- tools
- permission resolver integration
- orchestration
- services

### Frontend Team

Owns:

- embedded chat UI
- context bridge
- navigation
- confirmations

### Security Team

Owns:

- threat model
- secrets
- security testing
- incident policy
- prompt/tool abuse controls

### DevOps/MLOps

Owns:

- environments
- CI/CD
- model deployment
- monitoring
- backup
- recovery

### QA

Owns:

- functional testing
- regression
- security tests
- performance
- UAT coordination

---

# 59. PROSPECT-TO-CASH DATA ASSETS

Create:

- PTC_Module_Master
- PTC_Process_Master
- PTC_Form_Master
- PTC_Field_Master
- PTC_Form_IDO_Map
- PTC_Field_Property_Map
- PTC_Tool_Map
- PTC_Business_Glossary
- PTC_QA_Master
- PTC_Document_Master
- PTC_Test_Questions
- PTC_RAG_Evaluation
- PTC_SLM_Training_Data

All must be versioned.

---

# 60. BUSINESS GLOSSARY

Include validated terms such as:

- Prospect
- Lead
- Opportunity
- Estimate
- Quote / Quotation
- Customer
- Customer Order
- CO
- Order Line
- Due Date
- Credit Limit
- Credit Hold
- Shipment
- Invoice
- Payment
- Receivable

Columns:

- canonical term
- synonyms
- abbreviation
- alternate spelling
- business definition
- process
- module
- version

Use glossary in:

- query rewriting
- Q&A matching
- RAG
- SLM dataset generation

---

# 61. OBSERVABILITY

Every request should have:

- request_id
- trace_id

Monitor application:

- CPU
- RAM
- request count
- latency
- HTTP failures
- database latency

Monitor AI:

- SLM latency
- SLM routing accuracy
- invalid JSON rate
- LLM fallback rate
- LLM latency
- token usage
- hallucination rate
- RAG retrieval quality
- reranker performance

Monitor SyteLine:

- session failures
- authorization denials
- IDO/API latency
- timeouts
- site errors
- tool failures
- write-action failures

---

# 62. AUDIT

Audit record may include:

```json
{
  "request_id": "...",
  "trace_id": "...",
  "user_id": "...",
  "timestamp": "...",
  "site": "...",
  "module": "...",
  "form": "...",
  "intent": "...",
  "route": "...",
  "tool": "...",
  "authorization": "ALLOW",
  "slm_version": "...",
  "llm_version": "...",
  "status": "SUCCESS"
}
```

Do not store:

- passwords
- bearer tokens
- session secrets
- unnecessary restricted data

---

# 63. ERROR HANDLING AND RESILIENCE

Implement:

- standardized exceptions
- timeouts
- limited retries
- exponential backoff
- circuit breakers
- health checks
- graceful degradation

Examples:

Milvus unavailable:

- live ERP may still work

LLM unavailable:

- fast Q&A and deterministic navigation may still work

SyteLine unavailable:

- approved Help/RAG may remain available if policy permits

Never silently return stale transaction values.

---

# 64. BACKGROUND JOBS

Use background workers/jobs for:

- document ingestion
- Markdown conversion
- embeddings
- reindexing
- large evaluations
- SLM training
- dataset processing

Do not run these inside a normal `/chat` HTTP request.

---

# 65. ENVIRONMENTS

Create:

- DEV
- TEST
- UAT
- PRODUCTION

Model lifecycle:

```text
TRAINING
 ↓
OFFLINE TEST
 ↓
SHADOW
 ↓
CANARY
 ↓
PRODUCTION
```

Separate configuration and secrets.

---

# 66. CI/CD

Application:

```text
Git
 ↓
Pull Request
 ↓
Code Review
 ↓
Lint
 ↓
Unit Tests
 ↓
Security Scan
 ↓
Build
 ↓
Integration Tests
 ↓
DEV
 ↓
TEST
 ↓
UAT
 ↓
Approval
 ↓
PRODUCTION
```

Model pipeline:

```text
Dataset Approval
 ↓
Training
 ↓
Evaluation
 ↓
Registry
 ↓
Shadow
 ↓
Canary
 ↓
Production
```

Application and model deployments must support independent rollback.

---

# 67. BACKUP AND DISASTER RECOVERY

Define backup and restore for:

- PostgreSQL
- Milvus
- document store
- original knowledge files
- processed Markdown
- Q&A master
- training datasets
- model adapters
- model registry metadata
- configuration
- audit logs

Define:

- RPO
- RTO
- restore procedure
- rollback procedure

Do not duplicate SyteLine ERP backups through the chatbot platform unless explicitly required.

---

# 68. TESTING

Create tests for:

- session validation
- group changes
- user overrides
- site changes
- form restrictions
- component restrictions
- IDO restrictions
- property restrictions
- row restrictions
- prompt injection
- "god mode"
- "forget previous instructions"
- social engineering
- obfuscated payloads
- off-topic questions
- ambiguity
- context resolution
- frustration
- Q&A matching
- document retrieval
- BM25
- vector search
- RRF
- reranking
- evidence sufficiency
- citations
- SLM routing
- LLM fallback
- live data
- navigation
- actions
- support escalation
- security escalation
- audit
- load/performance

Security leakage must be a release blocker.

---

# 69. RAG EVALUATION

Measure:

- correct source retrieval
- Precision@K
- Recall@K
- metadata filter accuracy
- reranker quality
- citation correctness
- groundedness
- stale-document avoidance
- unauthorized-document avoidance

Do not evaluate only by "answer sounds good."

---

# 70. FIRST POC

Do not start with the complete Prospect-to-Cash chain.

Recommended first slice:

# Customer / Customer Order

Implement:

1. Existing SyteLine session reuse
2. User identity
3. Dynamic permissions
4. Site context
5. Current form
6. Current field
7. Current customer/order
8. Security gate
9. Fast Q&A
10. Markdown RAG
11. One confirmed live IDO/API use case
12. Response security
13. Audit

Example questions:

- What is this screen?
- What does this field mean?
- What is a Customer Order?
- How do I create a Customer Order?
- What is Due Date?
- Show the current order status.
- Why can't this order be released?
- Show this customer's balance.
- Show overdue invoices.

Only implement live questions where the necessary SyteLine mapping is confirmed.

Keep POC READ-ONLY.

---

# 71. DOMAIN ACCEPTANCE CRITERIA

A Prospect-to-Cash area cannot go live until:

- Q&A validated
- Markdown approved
- RAG tested
- version filtering tested
- citations tested
- form context tested
- field context tested
- permissions tested
- live data tested where supported
- unauthorized queries denied
- off-topic refused
- ambiguity clarifies
- security attacks blocked
- SLM routing evaluated
- LLM fallback tested
- audit verified
- consultant/business UAT approved

---

# 72. BUILD ORDER — FOLLOW STRICTLY

Build in this order:

1. Repository skeleton
2. Configuration management
3. FastAPI foundation
4. SyteLine session integration
5. Security bootstrap
6. Dynamic Permission Resolver
7. Permission cache
8. Frontend Context Bridge
9. Context Manager
10. Input Security Gate
11. Scope Classifier
12. Query taxonomy
13. Ambiguity Resolver
14. Initial LLM-based router
15. LangGraph orchestration
16. Prospect-to-Cash metadata catalogue
17. Q&A Excel schema
18. Q&A Retriever
19. Document ingestion
20. Markdown conversion
21. Chunking
22. Embedding service
23. Milvus
24. Query rewriting
25. BM25
26. Vector retrieval
27. Hybrid search
28. RRF
29. Reranker
30. Contextual compression
31. Evidence sufficiency
32. RAG answer service
33. SyteLine connector
34. IDO Security Gateway
35. Tool Registry
36. Live-data service
37. Navigation
38. Response generation
39. Response security
40. Tone/frustration manager
41. Support-ticket escalation
42. Security escalation
43. Audit
44. Monitoring
45. Create routing dataset
46. Teacher LLM distillation
47. SFT + LoRA
48. SLM Router V1
49. SLM evaluation
50. Shadow mode
51. Canary
52. Production SLM routing
53. Additional Prospect-to-Cash areas
54. Controlled write actions only later

Do not start with SLM fine-tuning before:

- taxonomy is stable
- tools are defined
- routes are defined
- context contract is stable
- security contract is stable

---

# 73. ITEMS THAT MUST BE CONFIRMED FROM SYTELINE

Mark unresolved items clearly as:

**[NEEDS SYTELINE CONFIRMATION]**

Questions:

1. How does the embedded chatbot obtain the logged-in SyteLine user?
2. How is the trusted session/token provided?
3. How is configuration obtained?
4. How is current site obtained?
5. How are user groups obtained?
6. How are individual overrides obtained?
7. How are effective form permissions obtained?
8. How are component-level permissions obtained?
9. How are IDO permissions obtained?
10. How are property permissions obtained?
11. How are row filters obtained?
12. How are allowed sites obtained?
13. How is current form detected?
14. How is current field/component detected?
15. How is current selected record detected?
16. How can the chatbot open another form?
17. Which REST v2 / ION / Mongoose integration method is approved?
18. Which Prospect-to-Cash IDOs are approved?
19. Which properties are approved?
20. Which methods are approved?
21. Which operations must remain read-only?
22. Which write operations may be supported later?
23. Where should the chatbot UI be embedded?
24. Are help documents subject to form/module access rules?
25. How quickly must permission changes propagate?
26. What audit/compliance retention is required?

Do not invent these answers.

---

# 74. REQUIRED OUTPUT FROM THE IMPLEMENTATION ASSISTANT

When this master prompt is given to a coding/architecture assistant, return work in this order:

1. Executive architecture summary
2. Assumptions
3. [NEEDS SYTELINE CONFIRMATION] list
4. Three-level architecture diagram
5. Prospect-to-Cash architecture diagram
6. Login/session bootstrap flow
7. Dynamic permission flow
8. Frontend context flow
9. Security-gate flow
10. Scope/intention/ambiguity flow
11. Full routing flow
12. Fast Q&A flow
13. Document ingestion flow
14. Chunking flow
15. Vector database flow
16. Query-rewriting flow
17. BM25 + vector + RRF + reranker flow
18. RAG answer flow
19. Live IDO/API flow
20. Navigation flow
21. Action flow
22. Mixed-question flow
23. Frustration/escalation flow
24. LLM/SLM model responsibilities
25. LLM-to-SLM distillation flow
26. SFT + LoRA flow
27. Shadow/canary deployment flow
28. Data Team deliverables
29. Metadata/data dictionary
30. Repository structure
31. API contracts
32. Pydantic models
33. Database schemas
34. Test plan
35. Evaluation plan
36. CI/CD plan
37. MLOps plan
38. Monitoring plan
39. Security checklist
40. Backup/DR plan
41. Team responsibility matrix
42. POC implementation backlog
43. Acceptance criteria
44. Production-readiness checklist

Do not skip sections.

---

# 75. FINAL ARCHITECTURAL PRINCIPLE

Remember the responsibility separation:

```text
SyteLine Login
=
Who is the user?
```

```text
Permission Resolver
=
What is the user allowed to access right now?
```

```text
Context Manager
=
Where is the user and what are they working on?
```

```text
Security Gate
=
Is this request trying to manipulate or attack the system?
```

```text
Scope Classifier
=
Is the request about SyteLine?
```

```text
SLM
=
What kind of request is this and where should it go?
```

```text
Fast Q&A
=
Do we already have a short approved answer?
```

```text
Markdown RAG
=
What approved detailed knowledge is relevant?
```

```text
Embedding Model
=
How do we represent semantic meaning for retrieval?
```

```text
BM25
=
Which documents match exact terminology and keywords?
```

```text
Vector Search
=
Which documents are semantically similar?
```

```text
RRF
=
How do we combine keyword and semantic rankings?
```

```text
Reranker
=
Which retrieved chunks are actually the most relevant?
```

```text
SyteLine IDO/API
=
What is the current ERP truth?
```

```text
LangGraph
=
What controlled workflow should execute?
```

```text
LLM
=
How do we reason over and explain authorized information?
```

```text
Teacher LLM
=
How do we generate high-quality candidate examples for the SLM?
```

```text
SFT
=
How do we teach the SLM expected behavior from labeled examples?
```

```text
LoRA
=
How do we perform that fine-tuning efficiently?
```

```text
Audit
=
What happened, who requested it, and what was allowed?
```

Final objective:

# RIGHT ANSWER  
# + RIGHT USER  
# + RIGHT PERMISSION  
# + RIGHT CONTEXT  
# + RIGHT KNOWLEDGE  
# + RIGHT LIVE DATA  
# + RIGHT TIME

---

# 76. IMPORTANT — FLOWCHART DIAGRAMS WILL BE ATTACHED

After this prompt, I will attach our existing **SyteLine chatbot architecture and R&D flowchart diagrams**.

You must review those diagrams carefully before finalizing architecture or implementation.

Use the attached diagrams to understand:

- Three-level architecture
- SyteLine login/session flow
- Dynamic permission flow
- Intent and routing flow
- Security-first query processing
- Ambiguity handling
- Frustration and escalation
- Fast Q&A routing
- Markdown RAG
- Document ingestion
- Chunking
- Embeddings
- Milvus
- BM25
- Vector search
- RRF
- Reranking
- Contextual compression
- Evidence sufficiency
- LLM/SLM usage
- LLM-to-SLM distillation
- SFT
- LoRA
- Runtime SLM routing
- Live IDO/API access
- Support escalation
- Monitoring/audit

Treat the flowcharts as **supporting architecture references**.

If a diagram conflicts with an explicit requirement written in this master prompt:

1. Do not silently choose one.
2. Identify the conflict.
3. Explain it.
4. Follow the confirmed written requirement unless I explicitly approve a change.

Do not invent information that is missing from the diagrams.

If a SyteLine-specific implementation detail is still unknown, mark it:

**[NEEDS SYTELINE CONFIRMATION]**

Before generating production code, provide a final architecture consistency review against:

- This master prompt
- The attached flowcharts
- Confirmed SyteLine consultant information
- Approved Prospect-to-Cash scope

Only after that review should implementation begin.

---

# 77. FINAL INSTRUCTION

Work phase by phase.

Do not generate the entire production system in one response.

For each phase:

1. Explain the goal.
2. Identify dependencies.
3. Identify SyteLine details that still need confirmation.
4. Show the architecture/flow for that phase.
5. Define input/output contracts.
6. Define data structures.
7. Define implementation tasks.
8. Define tests.
9. Define acceptance criteria.
10. Stop at a clean milestone before moving to the next phase.

Never silently guess SyteLine-specific technical details.

Use the attached flowcharts and this prompt together as the authoritative design input.
