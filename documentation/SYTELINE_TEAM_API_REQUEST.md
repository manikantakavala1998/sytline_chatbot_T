# SyteLine Chatbot — Integration Questions for the SyteLine Team

**Purpose:** Agree on the supported, secure way to connect the chatbot to our SyteLine/CSI WebClient and, later, read live Prospect-to-Cash data. Please answer for **our actual SyteLine installation**, including customizations. A general product API name alone is not enough.

**Initial scope:** Read-only. The chatbot must not create, update, delete, release, post, or approve business records. It must not use direct database access or an unrestricted administrator account. We can discuss actions in a later phase.

**Why we are asking now:** The chatbot currently uses simulated SyteLine users, sites, permissions, and screen context. We need the approved integration details to replace those simulations safely. A WebClient page URL by itself does not establish an API connection or a trusted user session.

## Interfaces we need the team to identify

| Need | Required for | What we need from the SyteLine team |
| --- | --- | --- |
| Trusted user/session integration | Phase 2 | Supported method to identify and validate the existing WebClient user; token/session expiry behavior. This may be SSO or a WebClient integration, not a standalone REST endpoint. |
| Current configuration, site, user, and effective access | Phase 2 | Supported source or enforcement method for groups, overrides, allowed sites, form/component rights, IDO/property rights, and row restrictions. Do not assume one permission API covers everything. |
| Current-screen context bridge | Phase 2 | Supported WebClient method to send active form, field/component, and selected record to the chatbot. This is likely a UI integration rather than a business-data REST call. |
| Metadata/discovery for approved IDOs | Phase 4 | Approved IDO/property/key documentation or access to a metadata operation such as Mongoose `GetPropertyInformation`. |
| Read-only business-data queries | Phase 4 | Approved query interface, such as Mongoose `LoadCollection` or an approved service, plus the exact IDOs, fields, filters, and site rules for each use case. |
| Read-only business calculations | Phase 4, if needed | Approved method/service for values that cannot safely be derived from one row, such as balance or availability. An IDO method must be confirmed to have **no side effects** before the chatbot may call it. |
| WebClient navigation | Phase 4, if needed | Supported way to open an authorized form or record; this may be a WebClient command, not a REST API. |
| Protected document access | When applicable | Rules or approved interface for documents that cannot be shown to every user. |

`GetPropertyInformation`, `LoadCollection`, and `InvokeIDOMethod` are examples of documented Mongoose capabilities, **not a claim that our installation has approved these operations or any particular IDO**. The team should confirm the route and scope. We do not need unrestricted access to every available Mongoose API.

## Meeting questions — please work through these in order

### 1. Confirm the environment

- Which CSI/SyteLine and Mongoose versions are installed? Is the deployment on-premises, hosted, or cloud?
- Which configuration, configuration group, sites, and WebClient environment should the chatbot use?
- Which forms, IDOs, fields, security rules, or workflows have been customized?
- Can we use a non-production environment with representative test data?

**Please provide:** Environment names and owners, supported documentation for this version, and a test-environment contact. Do not send passwords or production tokens in meeting notes.

### 2. Choose one supported integration route

- Should the chatbot backend use Mongoose REST v2 directly, REST through ION API, or another approved service?
- What are the approved API base URL, authentication method, network/TLS requirements, and license or session requirements for our deployment?
- Is there an API catalog, Swagger/OpenAPI description, or sample client for this exact environment?

**Please provide:** The recommended route and a working, non-production connection example. We will not assume that the WebClient URL is the API URL.

### 3. Reuse the user's existing login

- How can the embedded chatbot receive and verify the **currently logged-in SyteLine user** without a second login?
- What trusted token or assertion may the chatbot backend use? Who issues it, how long is it valid, and how do logout and expiration work?
- Can API reads run as that same user? If not, how are that user's effective permissions enforced without relying on a broad service account?

**Example:** Alice opens the chatbot. Its backend must know that Alice is authenticated; a user ID supplied by the browser alone is not proof.

### 4. Get current user, site, and security context

- How do we obtain the user's ID, display name, active configuration and site, allowed sites, groups, and individual overrides?
- How is a site switch communicated while the chatbot is open?
- Is there an approved API or service for effective permissions, or must we call SyteLine under the user's identity and let SyteLine enforce them?

**Please provide:** A redacted example for a sales user, a finance user, and a user with restricted access.

### 5. Verify effective access, not just group membership

- How are form and component/field permissions checked for a user?
- How are IDO, property, operation, and row-level restrictions checked for an API request?
- Do individual user exceptions override group access? How do site and license restrictions affect API access?
- How do we distinguish **denied** from **no matching record** without revealing that a protected record exists?

**Example:** A user may see an order status but not its credit or margin fields. Another user may be unable to see the order at all. Please demonstrate the expected API behavior for both.

### 6. Connect to the current WebClient screen

- Where is the chatbot allowed to be embedded in the WebClient?
- What supported WebClient extension, event, or messaging interface exposes the current form, focused field/component, selected record key, and site?
- How are changes sent when the user selects another record, changes form, or closes a form?
- What validation is needed before the backend trusts screen context received from the browser?

**Example:** The user is viewing order 456 and asks, “Why is this order on hold?” The chatbot needs the selected order key, but must still recheck access before reading it.

### 7. Check knowledge-document access

- Are manuals, SOPs, help pages, or attachments restricted by user, group, site, form, or module?
- If yes, how can the chatbot obtain or enforce those restrictions before retrieving a document answer?
- Is there an approved document API for protected attachments, or should those documents remain outside the chatbot knowledge base?

**Please provide:** The document-access rules and one allowed/denied example.

### 8. Supply the approved read-only live-data catalog

For each Prospect-to-Cash area below, please identify the approved **IDO/API or read-only method**, exact property names, record key, relationships, site rules, and permissions:

1. Prospect and lead
2. Opportunity and activity
3. Estimate/quote
4. Customer and contact
5. Sales order, line/release, hold, and status
6. Pricing and credit information
7. Shipment and fulfillment
8. Invoice, receivable, payment, and balance
9. Cross-process links, such as opportunity → estimate → order → shipment → invoice

For calculations such as **customer balance**, **overdue invoice**, and **item availability**, please identify the authoritative SyteLine method or business rule. We should not guess a value by adding raw fields together.

**Please provide:** A table with: business question | form | IDO/API/method | key | allowed fields | filters/site | required rights | redacted example response | SyteLine owner.

### 9. Confirm API behavior for safe reads

- Which query filters are permitted? What are the page-size and paging rules? Are sorting, timeouts, and rate limits defined?
- What date/time zone, currency, site, and “as of” rules apply to financial or status answers?
- How fresh is each value? Is it transactional, cached, or delayed?
- Which fields contain personal, financial, or other sensitive information that must not enter logs or the vector database?
- What are the exact responses for expired login, denied access, not found, invalid filter, rate limit, and SyteLine outage?

**Please provide:** Request/response samples and limits for the approved read methods. The chatbot will use an allowlist of IDOs, methods, properties, and filters rather than allowing AI-generated arbitrary queries.

### 10. Confirm navigation back into SyteLine

- What supported WebClient mechanism can open an approved form and, optionally, a specific record?
- Can it check the user's form access first? What should the chatbot do when navigation is denied or the record no longer exists?

**Example:** “Open order 456” should navigate only if the user is allowed to open that form and record.

### 11. Agree on changes, audit, and support

- How soon must a group, site, property, or row-permission change take effect in the chatbot? Is there an event or callback, or should we use short-lived cache entries?
- Which request/user/site/decision details must be audited, and for how long? Which values must never be logged?
- Who will support API failures and security incidents? What correlation ID should we pass to SyteLine for troubleshooting?

### 12. Demonstrate a small pilot before the full catalog

Please show one complete, read-only example: **the logged-in user asks for an order's status**. Demonstrate it with:

- A user who is allowed to see the order.
- A user who is denied access to the order or one of its fields.
- A site change or permission change during the session.
- A missing order and an unavailable API.
- The current WebClient record context, if the question says “this order.”

This pilot should establish the pattern for later Prospect-to-Cash data sources.

## Items to take away from the meeting

1. A named decision on the supported integration route and WebClient embedding mechanism.
2. A trusted, per-user login/session design and the permission-enforcement method.
3. A screen-context and navigation contract, including whether either requires a WebClient customization rather than a REST API.
4. A versioned, approved read-only IDO/API/field mapping for the pilot order-status question, followed by the remaining Prospect-to-Cash catalog.
5. Non-production API documentation, redacted sample requests/responses, test users, and an integration owner.
6. Agreed error handling, rate limits, permission-refresh time, and audit-retention requirements.

## Explicitly later, not required for the first live-data release

- `UpdateCollection`, write-capable IDO methods, record creation/updates/deletion, transactions, approvals, and posting.
- Ticket-system, email, or Teams APIs unless the team wants to include escalation in this integration discussion.

These later capabilities need separate authorization, confirmation, and audit requirements. Please do not enable them as part of the read-only pilot.
