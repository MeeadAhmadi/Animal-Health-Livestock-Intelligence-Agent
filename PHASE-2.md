# Phase 2 — Source Registry + Collection Engine

## Goal

Build the first external-information ingestion foundation for the Livestock Intelligence & Early-Warning System.

Phase 2 introduces the controlled path from registered external sources to traceable evidence records while preserving provenance, collection history, failures, and security boundaries.

The purpose of this phase is not to interpret intelligence.

The purpose is to collect external information reliably, safely, and traceably so later phases can classify, correlate, score, and analyze it.

---

## Current State

Phase 1 has been completed, validated, approved, committed, pushed, reviewed, and merged into `main`.

Confirmed Phase 1 capabilities include:

- centralized backend configuration
- PostgreSQL connectivity
- SQLAlchemy 2.x
- Psycopg 3
- Alembic migration workflow
- restricted application database role
- separate migration/ownership role model
- liveness and readiness checks
- structured UTC logging
- request/correlation IDs
- centralized error handling
- backend automated tests
- Ruff validation
- frontend regression validation

Phase 2 starts from this approved baseline.

---

## Phase 2 Objective

At the end of Phase 2, the system should have a controlled collection foundation capable of:

- registering external information sources
- identifying which source produced each collected item
- collecting external content through explicit collector boundaries
- recording collection attempts and outcomes
- preserving source provenance
- preserving canonical UTC timestamps
- storing evidence needed by later intelligence phases
- preventing silent collection failures
- preventing unsafe outbound network access
- preventing source content from being treated as trusted instructions
- supporting deterministic technical duplicate detection where practical
- preserving multiple independent source records for the same future story or event

Phase 2 does **not** yet perform semantic intelligence interpretation.

---

## Core Data Principle

The system must preserve source evidence independently.

The conceptual flow is:

```text
Registered Source
      ↓
Collection Attempt
      ↓
Evidence Record
      ↓
Future Story / Event Cluster
```

If the same underlying event is reported by multiple independent sources:

- each source record must remain independently traceable
- one source must not overwrite another
- provenance must remain visible
- repeated reporting must not automatically be treated as confirmation of truth
- future intelligence logic may use source independence and source quality as evidence

Semantic cross-source story/event grouping is intentionally deferred to Phase 3.

---

## Included Scope

### 1. Source Registry

Introduce a persistent registry for external sources.

The registry must provide enough information to answer:

- What source is this?
- How is it identified?
- Where is its collection entry point?
- What collection mechanism does it require?
- Is collection currently enabled?
- When was the source record created or changed?

The exact database fields must be justified by an immediate Phase 2 consumer.

Do not add speculative fields for future scoring, AI interpretation, commercial value, reputation ranking, or intelligence significance.

---

### 2. Source Identity

Each registered source must have a stable system identifier.

Source identity must not depend solely on:

- display name
- article title
- mutable URLs
- user-facing labels

Identifiers must be deterministic or database-controlled through deterministic system logic.

Identifier generation must not depend on an LLM.

---

### 3. Collection Boundary

External retrieval must occur through an explicit collection layer.

Business/API code must not perform arbitrary outbound requests directly.

The collection boundary should be responsible for:

- outbound request policy
- timeout handling
- redirect handling
- response-size limits
- network safety validation
- collection result reporting
- collection failure reporting
- provenance capture

This boundary must be reusable by later source-specific collectors without duplicating security logic.

---

### 4. SSRF Protection

Server-Side Request Forgery protection is a mandatory Phase 2 security requirement.

Before a collector is considered safe for external URL retrieval, the system must prevent access to prohibited destinations.

At minimum, the design must address:

- allowed URL schemes
- malformed URLs
- localhost
- loopback addresses
- private/internal IP ranges
- link-local addresses
- reserved or otherwise unsafe network destinations
- hostname resolution to prohibited addresses
- redirect chains that lead to prohibited addresses

Validation must occur in deterministic code.

An LLM must never decide whether a network destination is safe.

---

### 5. Redirect Safety

Redirects must not bypass the outbound network policy.

Every relevant redirect destination must be subject to the same network safety checks as the original request.

Unrestricted redirect following is not acceptable.

---

### 6. Resource Limits

External sources are untrusted and may behave incorrectly or maliciously.

Collection must therefore include explicit operational limits where applicable, including:

- connection timeout
- request/read timeout
- redirect limit
- maximum acceptable response size

The specific limits must be configurable or centrally defined rather than scattered through collector code.

---

### 7. External Content Trust Boundary

All externally collected content must be treated as **untrusted input**.

Collected webpages, feeds, documents, metadata, embedded text, and future PDFs may contain instructions intended to manipulate automated systems.

External content is data.

External content is not trusted system instruction.

Collected content must never be allowed to:

- override trusted application instructions
- request credentials
- expose secrets
- authorize tool execution
- alter access-control decisions
- trigger arbitrary commands
- redefine system security policy

This boundary must remain valid when AI/LLM processing is introduced in later phases.

---

### 8. Provenance

Every evidence record must remain traceable to its origin.

Phase 2 provenance must support answering, where available:

- which registered source produced the item
- which source URL or external identifier was involved
- when the system collected it
- when the upstream source states it was published or updated, if available
- which collection attempt produced the record

System-generated collection timestamps must use UTC.

Source-provided timestamps must not be silently rewritten or invented.

If a source does not provide a publication timestamp, that absence must remain distinguishable from the system collection timestamp.

---

### 9. Evidence Records

Phase 2 introduces the evidence layer required by later intelligence processing.

An evidence record represents independently collected source material.

Evidence is not yet:

- an Event
- a Signal
- a Trend
- a Risk
- a Hypothesis
- an Alert
- an Intelligence Insight

Those concepts belong to later intelligence phases.

Evidence must preserve enough source context for later processing without prematurely performing semantic intelligence modeling.

---

### 10. Raw vs Derived Information

Phase 2 must maintain a clear boundary between:

- source-provided information
- system-generated collection metadata
- future derived intelligence

Collection must not silently convert interpretation into source fact.

Any later derived field or conclusion must remain distinguishable from raw evidence.

---

### 11. Collection Attempt Tracking

Every collection execution must produce an observable result.

The system must be able to distinguish outcomes such as:

- collection succeeded
- collection produced no usable item
- source responded with an HTTP/network failure
- source was rejected by security validation
- response exceeded operational limits
- content could not be processed by the supported Phase 2 path

The exact status representation must remain simple and deterministic.

---

### 12. No Silent Failure

A failed collector must not disappear silently.

Collection failures must be:

- recorded or otherwise observable
- associated with the relevant source or attempt where possible
- logged with diagnostic context
- safe from credential leakage
- distinguishable from successful collection with zero new evidence

Later alerting and operational dashboards are outside this phase, but Phase 2 must create the data foundation they require.

---

### 13. Technical Deduplication

Phase 2 may perform deterministic technical duplicate detection.

Examples include duplicates based on a verified stable external identifier or normalized technical identity.

Technical deduplication must not destroy provenance.

When duplicate retrieval of the same source item occurs, the system must avoid unnecessary duplicate evidence creation where deterministically identifiable.

---

### 14. Cross-Source Duplicate Preservation

Phase 2 must **not** collapse independent sources merely because their content appears similar.

If multiple sources report the same event:

```text
Source A → Evidence A
Source B → Evidence B
Source C → Evidence C
```

All three records remain available.

A future phase may produce:

```text
Story/Event Cluster
 ├── Evidence A
 ├── Evidence B
 └── Evidence C
```

This is required so the system can later display one canonical story while showing every supporting source.

---

### 15. Semantic Deduplication Is Deferred

Phase 2 does not determine that two independently written articles describe the same real-world event.

The system must not use title equality alone as semantic deduplication.

Future grouping may consider information such as:

- time
- location
- affected entity
- animal/species
- disease or topic
- source independence
- substantive content

That logic belongs to Phase 3.

---

### 16. Database Migration Discipline

All Phase 2 schema changes must use Alembic.

Requirements:

- migrations committed to Git
- migration reviewed before execution
- no `Base.metadata.create_all()` migration replacement
- no uncontrolled schema mutation at application startup
- no destructive migration without explicit review
- new tables/columns must have an identified Phase 2 consumer

---

### 17. Logging

Phase 2 collection operations must integrate with the structured logging foundation created in Phase 1.

Useful diagnostic context may include:

- source identifier
- collection attempt identifier
- operation/result
- HTTP status where safe and relevant
- duration
- failure category

Logs must not intentionally expose:

- passwords
- API keys
- bearer tokens
- authorization headers
- cookies
- secret query parameters
- database credentials
- sensitive response bodies

---

### 18. UTC Timestamp Discipline

Canonical system timestamps must use UTC.

This applies to system-generated records such as:

- collection time
- attempt creation/completion
- evidence creation
- registry creation/update

Source-provided time information must retain enough context to avoid pretending that an uncertain or source-local timestamp is a verified UTC timestamp.

---

## Database Design Discipline

Phase 2 introduces real domain data for the first time.

Schema design must therefore be conservative.

Rules:

1. Every significant field must have a current consumer.
2. Do not add future intelligence fields preemptively.
3. Preserve provenance.
4. Preserve historical traceability where needed.
5. Do not overwrite independent source evidence.
6. Separate collection metadata from source content.
7. Use database constraints for integrity where deterministic.
8. Use deterministic mechanisms for identifiers and uniqueness.
9. Do not use LLM output for database integrity.
10. Keep migrations small and reviewable.

---

## Collector Design Discipline

Collectors should remain focused on retrieval and source-specific extraction boundaries.

Collectors must not become intelligence engines.

A collector must not decide:

- whether something is an intelligence signal
- whether an event is important
- whether a disease is emerging
- whether a story is strategically relevant
- whether multiple independent reports form a trend

Those decisions belong to later phases.

---

## Explicitly NOT Included

Phase 2 does **not** include:

- semantic classification
- semantic deduplication
- cross-source story clustering
- event correlation
- intelligence scoring
- confidence scoring
- signal creation
- trend creation
- risk creation
- hypothesis creation
- alert generation
- early-warning logic
- LLM interpretation
- embeddings
- vector search
- pgvector
- RAG
- Ask Intelligence
- company-context intelligence
- funding intelligence
- conference intelligence
- authentication
- user management
- production deployment
- Docker adoption
- CI/CD implementation
- Teams integration
- Power BI integration
- full observability deployment
- automated pentesting infrastructure
- production scheduling

These are deferred to later phases.

---

## Security Requirements

Phase 2 security review must explicitly validate:

### Network Safety

- prohibited destinations cannot be fetched
- redirect-based SSRF bypass is prevented
- malformed or unsafe URLs fail closed
- supported URL schemes are explicit

### Resource Safety

- collection cannot read indefinitely
- response size is bounded
- redirect depth is bounded
- failure does not crash the collection system uncontrollably

### Content Safety

- external content remains untrusted data
- collected instructions have no authority over the application
- collector output cannot directly execute commands
- secrets are not intentionally exposed to collected content

### Secret Safety

- no real credentials committed
- no secret-bearing configuration checked into Git
- sensitive outbound headers are not logged

---

## Validation Requirements

Phase 2 must be validated with executed tests.

At minimum, validation should cover:

- source registry persistence
- source identity/integrity rules
- evidence provenance
- UTC system timestamps
- successful collection path
- collection failure path
- no-silent-failure behavior
- deterministic technical duplicate behavior
- preservation of independent cross-source evidence
- unsupported URL scheme rejection
- localhost rejection
- loopback/private-address rejection
- redirect-to-prohibited-destination rejection
- timeout handling
- response-size enforcement
- safe error responses/logging
- Alembic upgrade
- Alembic current/head verification
- backend test suite
- Ruff
- frontend lint/build regression checks where relevant
- secret/Git tracking review
- `git diff --check`

A validation item must only be reported as passed if it was actually executed.

---

## Known Risks

### 1. SSRF

Impact: 10/10

A collection engine that accepts external URLs can become a path into localhost, database services, cloud metadata endpoints, or private infrastructure.

This must be addressed before unrestricted external collection is considered safe.

### 2. Prompt Injection Through Collected Content

Impact: 10/10 for later AI-enabled phases

External webpages and documents may contain malicious instructions.

Phase 2 must establish the trust boundary now so later LLM integration does not treat source content as trusted instruction.

### 3. Provenance Loss

Impact: 9/10

If collection or deduplication removes source identity, later intelligence conclusions cannot be audited or supported properly.

### 4. Incorrect Cross-Source Deduplication

Impact: 8/10

Collapsing independent evidence too early would destroy corroboration information and make later confidence analysis weaker.

### 5. Silent Collector Failure

Impact: 8/10

If a source stops working without an observable failure record, the system may falsely appear to have no relevant developments.

### 6. Unbounded External Content

Impact: 8/10

Untrusted servers can return excessively large or indefinitely slow responses.

Explicit operational limits are required.

### 7. Premature Intelligence Schema Design

Impact: 7/10

Adding classification, trends, scoring, or event semantics during collection would blur system boundaries and create weak assumptions before Phase 3.

---

## Acceptance Criteria

Phase 2 can be considered complete only when:

- source registry is implemented
- source identity is deterministic and traceable
- collection occurs through the controlled collection boundary
- SSRF protections are implemented and tested
- redirects cannot bypass network policy
- resource limits are implemented
- external content is explicitly treated as untrusted
- evidence provenance is persisted
- canonical system timestamps use UTC
- collection attempts and failures are observable
- failed collection is distinguishable from successful zero-result collection
- deterministic technical deduplication works where implemented
- independent cross-source evidence is preserved
- no semantic/event clustering has leaked into Phase 2
- Alembic migrations are applied and verified
- backend tests pass
- Ruff passes
- frontend regression checks pass where applicable
- no secrets are committed
- Git diff is reviewed
- the phase is explicitly approved

---

## Expected Deliverables

At Phase 2 closeout, the report must include:

1. What was implemented
2. Files/components changed
3. Source Registry design
4. Evidence/provenance design
5. Collection architecture
6. SSRF/security controls
7. Deduplication boundary
8. Database/migration status
9. Tests performed
10. Test results
11. Security validation
12. Known limitations
13. Deferred functionality
14. What remains for Phase 3

---

## What Comes Next

After Phase 2 is implemented, tested, reviewed, approved, committed, pushed, reviewed in GitHub, and merged into `main`, the next phase is:

**Phase 3 — Classification + Deduplication + Intelligence Scoring**

Phase 3 may then build on the preserved evidence layer to introduce:

- semantic classification
- cross-source story/event grouping
- semantic duplicate detection
- intelligence relevance scoring
- evidence correlation foundations

Phase 3 must preserve the provenance created in Phase 2.

---

## Phase 2 Validation Status

**Implementation Status:** Complete
**Backend Validation Status:** Passed
**Security Validation Status:** Passed for Phase 2 scope
**Database Migration Status:** Applied and verified
**Frontend Regression Status:** Passed
**Git Closeout Status:** Pending commit, push, GitHub review, and merge
**Phase Approval Status:** Pending explicit approval

### Implemented

Phase 2 implemented:

- Source Registry with database-controlled source identifiers
- controlled HTTP collection boundary
- explicit rejection of unsupported collector types at registration and collection time
- SSRF protection with public-destination validation
- redirect destination revalidation
- DNS resolution validation and connection pinning
- bounded connection/read timeouts
- bounded total collection time budget
- bounded redirect depth
- bounded response size
- environment-independent outbound HTTP behavior with `trust_env=False`
- collection attempt lifecycle tracking
- explicit success, zero-result, and failure states
- persisted failure codes
- evidence persistence with source provenance
- deterministic exact technical deduplication
- preservation of updated source content as new evidence
- preservation of independent cross-source evidence
- batch collection execution with per-source failure isolation
- structured collection logging
- explicit treatment of collected external content as untrusted data
- least-privilege runtime database permissions

### Database and Migration Validation

Applied migrations:

- `24bdc9be06f6` — Phase 2 source registry and collection foundation
- `3c5ef3b52d3a` — Phase 2 runtime permissions

Validation confirmed:

- Alembic current revision is `3c5ef3b52d3a (head)`
- `alembic check` reports no new upgrade operations
- runtime role `li_app` can SELECT, INSERT, and UPDATE Phase 2 tables
- runtime role `li_app` can use required identifier sequences
- runtime role `li_app` does not have DELETE permission
- permission validation data was rolled back and did not remain in the database

### Automated Validation

Backend:

- 70 tests passed
- 0 test failures
- Ruff passed for `app`, `tests`, and `migrations`

Frontend regression:

- `npm run lint` passed
- `npm run build` passed

Git/security checks:

- staged diff whitespace validation passed
- no staged `.env`, private-key, certificate, or similar secret-bearing file detected
- staged diff scan found no obvious credential or private-key patterns

### Known Limitation

The existing Starlette/FastAPI test client dependency emits one deprecation warning related to `httpx`. It does not currently fail tests and is not introduced by Phase 2.

Phase 2 does not include production scheduling, semantic classification, semantic deduplication, cross-source story/event clustering, intelligence scoring, LLM interpretation, RAG, authentication, production deployment, or integrations reserved for later phases.

---

## Approval Gate

Do not begin Phase 3 until Phase 2 is:

- implemented
- tested
- security-reviewed
- technically reviewed
- explicitly approved
- committed
- pushed
- reviewed in GitHub
- merged into `main`

Phase boundaries must be respected.
