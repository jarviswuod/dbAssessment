# Technical Design Decisions

## Overview

This document explains the technical design decisions behind the Data Connector Platform with more engineering depth than a high-level project summary. The goal of the system is not only to satisfy the assessment checklist, but to do so using patterns and abstractions that remain understandable, testable, and extensible as the application grows.

The platform has a few architectural pressures that shaped most decisions:

- it integrates with heterogeneous external databases
- it accepts and transforms user-editable data
- it has a trust boundary between frontend and backend
- it stores both structured application data and exported artifacts
- it needs reproducible infrastructure for demonstration and deployment

Because of those constraints, I generally preferred explicit abstractions, clear ownership boundaries, and backend-enforced controls over quick but tightly coupled implementations.

## 1. System Architecture: Decoupled Frontend and API

### Decision

The system is implemented as a decoupled web application:

- **Next.js** provides the frontend presentation layer
- **Django REST Framework** provides the backend API layer
- **Docker Compose** orchestrates infrastructure and service composition

### Why this architecture

This separation gives each layer a well-defined responsibility:

- the frontend handles rendering, routing, stateful UI interactions, and API consumption
- the backend owns validation, business rules, persistence, permissions, and integration with source systems
- infrastructure handles environment consistency, process isolation, and service discovery

From a software architecture perspective, this keeps the application closer to a layered system than a tightly mixed monolith. That improves maintainability and makes deployment concerns easier to evolve independently. It also fits the assessment well because the product behaves like an integration platform rather than a server-rendered website.

### Why not a more monolithic design

A more coupled Django-rendered frontend would reduce some moving parts, but it would blur the boundary between UI concerns and API/business concerns. For a platform that may later support other clients, API-first design is the better long-term choice.

### Trade-off

This architecture adds more coordination between frontend and backend, but the separation of concerns is much cleaner.

## 2. Backend Domain Modeling: Modular Django Apps

### Decision

The backend is organized into domain-oriented apps:

- `accounts`
- `connections`
- `extraction`
- `storage`

### Why this approach

This is a modularization decision based on cohesion. Each app owns a bounded area of the system:

- `accounts` owns identity, authentication, and authorization primitives
- `connections` owns connection metadata and connector behavior
- `extraction` owns data retrieval workflows and extraction history
- `storage` owns submit jobs, processed records, exports, and file access

This improves navigability and reduces accidental coupling. It also supports more focused tests because domain behavior is grouped with the models, serializers, views, and permissions that implement it.

### Why not keep everything in one app

A single app would reduce file count, but it would create a maintenance problem quickly. Multi-database integration, auth, async jobs, exports, and permissions are already distinct concerns. Mixing them would make the codebase harder to reason about and harder to extend safely.

### Engineering principle behind it

This choice reflects **high cohesion** and **separation of concerns**, which are foundational software design principles even outside formal pattern catalogs.

## 3. Connector Layer: Strategy Pattern + Factory Pattern

### Decision

Database-specific behavior is implemented through an abstraction layer:

- `BaseConnector` defines the contract
- each supported database has a concrete implementation
- `ConnectorFactory` resolves the appropriate connector instance

### Why this approach

This is the most important structural decision in the project because multi-database support is the core feature. Different database engines have different client libraries, query dialects, schema discovery behavior, and update semantics. Hiding all of that in views would tightly couple HTTP handling to infrastructure-specific logic.

Using an abstract base class gives a uniform interface for the operations the application cares about:

- `connect`
- `list_tables`
- `get_columns`
- `get_row_count`
- `fetch_batch`
- `update_rows`

This is effectively an application of the **Strategy Pattern**: at runtime, the system chooses a different implementation based on the configured database type while keeping the calling code stable. The factory acts as a lightweight **Factory Pattern** that centralizes object creation and avoids leaking database selection logic into the API layer.

### Why this is preferable to conditionals

An `if/elif` approach would work for two databases, but it becomes brittle as support grows. Every new connector would require changes across the request layer, increasing coupling and violating the **Open/Closed Principle** in **SOLID**. With the current design, the integration surface for a new database is mostly isolated to a new connector class plus registration in the factory.

### Trade-off

The cost is more upfront abstraction and more boilerplate. The benefit is much better extensibility and cleaner separation between business logic and infrastructure concerns.

## 4. Object-Oriented Design and Abstractions

### Decision

The connector subsystem is designed in an object-oriented style rather than as a collection of unrelated procedural helpers.

### Why this approach

`BaseConnector` serves as an abstraction boundary. Each connector object encapsulates its own connection state, lifecycle, and implementation details. That matters because the application needs polymorphic behavior without the rest of the code caring about the low-level details of PostgreSQL, MySQL, MongoDB, or ClickHouse.

Using an OOP design here improves:

- **encapsulation**: database-specific details stay inside the connector class
- **substitutability**: callers interact with a stable interface
- **testability**: connectors can be tested individually
- **maintainability**: changes in one connector do not force broad refactors elsewhere

### Why not use purely procedural helper functions

Procedural helpers can be fine for small scripts, but they tend to spread state and increase coupling once the workflow becomes more complex. Since this project manages multiple connector types with lifecycle behavior, an object-oriented abstraction is more suitable.

## 5. Persistent ConnectionConfig Model Instead of Ephemeral Connection Inputs

### Decision

External connection definitions are persisted in the database using a `ConnectionConfig` model.

### Why this approach

Treating a connection as a first-class domain object gives the application a stable representation of source systems. That supports:

- connection reuse
- ownership and RBAC enforcement
- auditing and logging
- cleaner frontend workflows
- easier system testing

This is more robust than asking users to submit raw host credentials every time they extract data. It also better reflects how real integration platforms work: connections are managed resources, not just one-off request payloads.

### Production implication

Persisting connection configuration introduces a security burden, because the system is now responsible for protecting credentials at rest and during use. That is why encryption and server-side authorization become non-negotiable.

## 6. Credential Handling: Encrypted at Rest

### Decision

Connection passwords are not stored as plain text. They are encrypted before persistence and decrypted through the model property when needed.

### Why this approach

This is a practical application of **defense in depth**. Even though the project is an assessment and demo deployment, external database credentials are sensitive infrastructure secrets. Storing them in raw form would be a weak design from both a security and architecture standpoint.

Encryption at rest reduces exposure in the event of a database leak, accidental logging, or improper inspection of stored values.

### Why not plain text or hashing

- **Plain text** is obviously unsafe for credentials
- **Hashing** is useful for one-way verification, but not for values the system must later use to connect outward

So reversible encryption is the correct primitive in this context.

### Real production note

In a mature production environment, I would likely move this concern into a dedicated secret-management layer such as Vault, cloud KMS, or environment-backed secret injection rather than relying only on application-managed field encryption.

## 7. Authentication: JWT Instead of OAuth or Session-Based Auth

### Decision

The platform uses JWT-based authentication with refresh tokens.

### Why this approach

Because the frontend and backend are decoupled, a token-based authentication model fits naturally. The frontend can authenticate once, send bearer tokens with API requests, and refresh access tokens when they expire. This keeps the API stateless and aligns well with SPA behavior.

### Why not Django session auth

Session authentication is excellent when Django is serving the frontend directly or when cookie/session semantics are the central model. In this application, the client and API are deliberately separated, so JWT is the cleaner fit.

### Why not OAuth 2.0 / OIDC

I considered the broader authentication space, but **OAuth 2.0** would only be justified if I needed delegated authorization or third-party identity federation. This system currently authenticates users directly within the application, so JWT is sufficient. If this were integrated with Google, Okta, Microsoft Entra ID, or another enterprise IdP, then OAuth/OIDC would be the better design.

### Security caveat

The current frontend stores tokens client-side, which is acceptable for demonstration but not ideal for high-security environments. In production, I would consider hardened cookie-based auth, stricter CSP, tighter XSS controls, and more formal token rotation strategies.

## 8. Authorization: RBAC Enforced on the Backend

### Decision

The system uses **RBAC** with a simple role model:

- admin
- regular user

Permission logic is enforced server-side through DRF permissions and queryset scoping.

### Why this approach

The assessment requirements are role-oriented rather than attribute-heavy. Admins need global visibility; standard users need ownership-based access plus shared-file visibility. A compact RBAC model is a good fit for that requirement.

From a backend design perspective, the important decision is not just using RBAC, but enforcing it in the API layer rather than trusting the frontend. The backend is the actual trust boundary. UI restrictions are convenience features, not security controls.

### Why not a more granular authorization model

More detailed permission systems can be powerful, but they also increase cognitive and implementation complexity across the data model, serializers, endpoints, and frontend states. For the current problem, that would be unnecessary complexity.

### Trade-off

The model is intentionally simple. That limits flexibility, but it makes correctness easier to reason about and easier to test.

## 9. Input Validation and Injection Resistance

### Decision

Table names are validated using a whitelist-style pattern before connector operations use them.

### Why this approach

This is a targeted security decision. In SQL and SQL-like systems, parameterized queries usually protect values, but **identifiers** such as table names often need separate handling. Because the application allows users to choose tables dynamically, this becomes an injection surface.

Validating the identifier at a shared abstraction point gives consistent behavior across connectors and reduces the chance that one connector handles the problem safely while another does not.

### Why this matters architecturally

This is not just an implementation detail. It reflects a design philosophy: security-sensitive validation should live close to the abstraction boundary where unsafe input enters the infrastructure layer.

### Trade-off

The whitelist is intentionally conservative, which may reject some unusual but technically valid identifiers. That is acceptable here because the safer default is more valuable than maximum permissiveness.

## 10. Batch Extraction Instead of Full Table Pulls

### Decision

The extraction API operates on `batch_size` and `offset` rather than reading entire tables into memory.

### Why this approach

This is both a requirement and a performance decision. Different source systems can contain very different dataset sizes, and the application does not control those tables. Pulling an entire table by default would increase:

- query time
- memory consumption
- response payload size
- browser rendering cost

Batched access keeps the extraction workflow more predictable and aligns with the frontend editing model, where the user only works on a subset of rows at a time.

### Why not cursor streaming

Cursor/stream-based extraction could be more efficient in some cases, but it introduces more connector-specific complexity and state management. For the scope of this application, offset-based batch extraction was the clearer and more consistent trade-off.

### Scalability implication

Offset-based pagination becomes less efficient at very high row counts depending on the database engine. In a production system with larger datasets, keyset pagination or engine-specific retrieval strategies may be more appropriate.

## 11. ExtractionJob as an Audit and Traceability Layer

### Decision

Each extraction attempt is logged in `ExtractionJob`, including success/failure metadata.

### Why this approach

Even though extraction is synchronous from the HTTP client’s perspective, the act of recording extraction jobs adds observability and traceability. This turns extraction from a purely transient interaction into an auditable workflow step.

That matters in a connector platform because debugging often depends on knowing:

- which connection was used
- which table was targeted
- which batch settings were applied
- whether the attempt failed or succeeded

### Why not keep extraction stateless only

A stateless-only approach would reduce writes, but it would lose operational context that becomes valuable for support, debugging, and administrative visibility.

## 12. EditableGrid: Custom Component Instead of a Heavy Grid Framework

### Decision

The frontend uses a focused custom editable grid rather than adopting a large enterprise grid library.

### Why this approach

The required editing capabilities are bounded:

- render extracted rows
- allow inline cell edits
- capture updated data
- support basic keyboard interactions

For that scope, a custom component keeps the implementation understandable and avoids the overhead of a large third-party grid package. It also gives direct control over UI behavior without adapting the project around a library’s API.

### Why not a dedicated grid package

A richer data-grid package would help if the product required:

- virtualization for very large datasets
- frozen columns
- advanced sorting and filtering
- formula-like editing
- schema-aware cell editors

Those are valuable features, but they would be disproportionate for the current requirements.

### Performance implication

The current grid is adequate for moderate batch sizes. For much larger client-side datasets, I would move toward virtualization and more optimized rendering strategies.

## 13. Frontend API Layer: Axios Service Wrappers and Interceptors

### Decision

API requests are centralized in a frontend service layer rather than scattered directly across page components.

### Why this approach

This is a maintainability decision. The frontend repeatedly needs to:

- attach bearer tokens
- retry after refresh
- target consistent endpoint URLs
- avoid duplicating transport logic across pages

By centralizing those concerns, components remain more focused on view logic and state transitions rather than HTTP plumbing.

### Why not inline `fetch` calls everywhere

That works for very small applications, but as the number of endpoints grows, duplication increases and auth-related mistakes become easier to make. The service layer acts as an abstraction that reduces those risks.

## 14. Dual Storage: Database Record Plus Exported Artifact

### Decision

Submitted data is persisted in two representations:

- a structured database record
- a generated file artifact in JSON or CSV

### Why this approach

These two storage targets serve different access patterns:

- the structured record supports relational queries, ownership tracking, and application state
- the exported file supports portability, download, and sharing

This is not redundancy for its own sake. It is an intentional split between **system-of-record storage** and **user-facing export storage**.

### Why not database-only

Database-only persistence would retain the data, but it would not produce a portable artifact suitable for download and sharing.

### Why not file-only

File-only persistence would weaken queryability, metadata relationships, and RBAC-aware application behavior.

### Trade-off

There is duplication in storage, but the design is significantly more useful than either single-storage approach.

## 15. Async Submit Workflow: Celery for Non-Trivial Post-Processing

### Decision

The submit workflow creates a `SubmitJob`, stores the structured data record immediately, and offloads heavier work to **Celery**.

### Why this approach

Submit is the most complex path in the application. It can involve:

- validating user-submitted edits
- persisting processed data
- writing changes back to the source database
- generating file exports
- updating job status

Doing all of that inside one synchronous request would increase timeout risk and reduce resilience, especially because external databases are part of the path. Offloading the heavier work to a queue separates user responsiveness from longer-running integration work.

### Why not keep it synchronous

Synchronous processing would be simpler conceptually, but much more fragile operationally. If the source system is slow or temporarily unavailable, the user experience degrades quickly.

### Scalability implication

The async design is much better for scaling submit workloads, but it also means the operational health of the worker and broker becomes part of the system’s reliability story.

## 16. Partial Success Semantics for Source Write-Back

### Decision

The background submit task can still complete export generation even if source write-back fails, while recording the write-back failure separately.

### Why this approach

This reflects a deliberate failure-model decision. The application has two related but distinct responsibilities after submission:

- preserve the processed output
- attempt to propagate the changes back to the source system

Those do not always need to fail together. If the source system is unavailable, losing the processed export as well would be unnecessarily destructive.

### Why this is useful

This creates a more fault-tolerant workflow. It acknowledges that external integrations are often the least reliable part of a system and that partial success can still deliver value.

### Production note

In a more mature production design, I would likely make this even more explicit in the state model with statuses like `completed_with_warnings` or separate sub-status fields.

## 17. OpenAPI and Self-Documenting APIs

### Decision

The backend exposes OpenAPI schema and interactive documentation via `drf-spectacular`.

### Why this approach

This improves the developer experience and reduces friction for testing and integration. It also strengthens the professionalism of the API layer because endpoints, request shapes, and error responses are documented from the codebase itself rather than manually maintained elsewhere.

Configured endpoints are:

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Schema: `http://localhost:8000/api/schema/`
- API base: `http://localhost:8000/api/v1/`

### Why this matters technically

Schema-driven documentation reduces drift between implementation and docs. It also supports tooling, testing, and easier debugging for consumers of the API.

## 18. Logging and Observability

### Decision

The production-oriented setup currently uses log files for:

- auditing
- debugging
- basic monitoring

### Why this approach

For a local demonstration deployment, file-based structured logging is a pragmatic starting point. It gives local durability and basic operational visibility without requiring a full observability platform.

### Limitations

This approach does not scale well in terms of:

- centralized search
- alerting
- dashboarding
- cross-service correlation
- long-term retention policies

### Production direction

For a more serious production environment, I would move toward **Loki + Grafana + Prometheus** or a similar central observability stack, potentially combined with metrics and tracing.

## 19. Risks, Constraints, and What I Would Change in a Larger Production System

### Security risks

- JWT stored on the client is practical for demo use, but more exposed to XSS than hardened httpOnly cookie strategies.
- Persisting connector credentials creates a sensitive-data surface area that would benefit from a dedicated secret manager.
- RBAC is intentionally simple; larger organizations may require finer-grained authorization or audit controls.

### Scalability risks

- offset-based extraction can degrade with very large tables
- synchronous extraction requests may become a bottleneck under heavier load
- the custom grid is not optimized for very large result sets

### Performance implications

- each extraction round-trip depends on an external database, so latency is partly outside application control
- connector behavior differs across engines, so performance tuning would eventually need to become engine-aware
- file-based logging is fine at small scale but becomes operationally expensive to manage over time

### What I would change in a production-grade version

- move secrets to a dedicated secret-management solution
- consider cookie-based auth or stronger browser-side hardening
- add rate limiting and stricter production security headers
- introduce engine-aware pagination and metadata caching
- use centralized logging and metrics
- formalize job states and retry policies

## Conclusion

The system is intentionally designed with software engineering discipline rather than just feature completeness. The main themes are:

- **abstractions over conditionals**
- **backend-enforced trust boundaries**
- **object-oriented connector design**
- **RBAC over ad hoc permission checks**
- **async processing for integration-heavy workflows**
- **dual persistence for different access patterns**

In other words, the implementation is assessment-sized, but the design decisions aim to be production-aware.
