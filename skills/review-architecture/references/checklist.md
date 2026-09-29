# Software Architecture Fitness Checklist

Detailed checklist for reviewing code against software architecture fundamentals. Use alongside the review-architecture skill to systematically evaluate each dimension.

---

## 1. Coupling Indicators

### Circular Dependencies
- [ ] **Import cycle detection** -- Module A imports from B, B imports from A. Trace import chains to find circular paths. These make independent testing and deployment impossible.
- [ ] **Transitive circular dependencies** -- A depends on B, B depends on C, C depends on A. These are harder to spot but equally harmful.
- [ ] **Package-level cycles** -- Even if individual files do not cycle, packages or directories may. Check at the directory level.

### Dependency Direction
- [ ] **Dependencies point inward** -- Infrastructure (database, HTTP, file system) depends on business logic, not the reverse. Domain code should not import from infrastructure packages.
- [ ] **No upward dependencies** -- Lower layers (data access) should not depend on higher layers (presentation). Check that data access code does not reference HTTP types or UI components.
- [ ] **Abstractions at boundaries** -- Module boundaries use interfaces, protocols, or abstract classes, not concrete implementations. This allows swapping implementations without changing consumers.

### Shared State
- [ ] **No global mutable state between modules** -- Modules should not communicate through shared global variables, singletons that carry request state, or mutable module-level dictionaries.
- [ ] **No hidden temporal coupling** -- Functions that must be called in a specific order should enforce that order through the type system or constructor injection, not documentation.
- [ ] **Event-driven over direct mutation** -- When one module needs to react to another's state change, prefer events or callbacks over direct state mutation across boundaries.

### Data Coupling
- [ ] **Pass what is needed, not what is available** -- Functions receive specific parameters, not entire objects when only one field is used. Passing a full `User` object to a function that only needs `user_id` creates unnecessary coupling.
- [ ] **No internal type leakage** -- Module-internal types (ORM models, internal DTOs) should not appear in public interfaces. Expose data transfer objects or value objects instead.
- [ ] **Shared types live in shared packages** -- Types used across module boundaries should live in a shared package, not be re-exported from one module's internals.

### God Modules
- [ ] **No module imported by more than 70% of the codebase** -- A utility module imported everywhere is a coupling hub. If it changes, everything may need retesting.
- [ ] **Utility modules are topic-scoped** -- Instead of one `utils` module, use `string_utils`, `date_utils`, `validation_utils`. Each is smaller and changes less frequently.
- [ ] **Hub classes are decomposed** -- Classes with 20+ methods or 500+ lines that serve multiple consumers should be split by responsibility.

Source: [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/)

---

## 2. Cohesion Assessment

### Single Responsibility
- [ ] **Each class has one reason to change** -- If a class changes when the database schema changes AND when the API format changes AND when business rules change, it has too many responsibilities.
- [ ] **Methods share instance data** -- In a class, methods should operate on the same fields. If half the methods use fields A and B, and the other half use fields C and D, the class should be split.
- [ ] **Module description fits one sentence** -- If describing a module requires "and" to list unrelated functions, it lacks cohesion.

### Concern Separation
- [ ] **HTTP handling is separate from business logic** -- Request parsing, header reading, and response formatting live in one layer. Business rules live in another. They do not mix.
- [ ] **Database queries are separate from business rules** -- SQL or ORM calls live in a data access layer. Business logic calls data access functions but does not construct queries.
- [ ] **Validation is separate from persistence** -- Input validation happens before data reaches the persistence layer. The database should not be the primary validation mechanism.
- [ ] **Configuration is separate from behavior** -- Config values (thresholds, feature flags, connection strings) are injected, not hardcoded into business logic.

### Feature Cohesion
- [ ] **Related code lives together** -- Code for "user registration" (handler, service, repository, tests) is grouped, not scattered across `handlers/`, `services/`, `repositories/` directories far apart.
- [ ] **Changes for one feature touch minimal files** -- Adding a field to user registration should require changes in one module, not across five directories.
- [ ] **No shotgun surgery** -- A single conceptual change should not require edits to 10+ files across the codebase. If it does, related logic is too scattered.

### Anti-Patterns
- [ ] **No util/helper dumping grounds** -- Files named `utils.py`, `helpers.js`, or `common.go` that accumulate unrelated functions. Each function should live in a module related to its purpose.
- [ ] **No feature envy** -- A method that uses more data from another class than from its own class should probably live in that other class.
- [ ] **No data clumps** -- Groups of parameters that always appear together (e.g., `street`, `city`, `state`, `zip`) should be extracted into a value object (e.g., `Address`).

Source: [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of Software Maintainability](https://jeffbailey.us/blog/2025/12/30/fundamentals-of-software-maintainability/)

---

## 3. Layering and Architecture Patterns

### Layer Identification
- [ ] **Presentation layer exists** -- There is a clear layer that handles HTTP requests, CLI commands, or UI rendering. It translates external input into internal function calls.
- [ ] **Business logic layer exists** -- There is a clear layer containing domain rules, workflows, and calculations. It does not know about HTTP, databases, or file systems.
- [ ] **Data access layer exists** -- There is a clear layer that handles persistence: SQL queries, file reads, API calls to external services. Business logic calls it through interfaces.

### Layer Discipline
- [ ] **No skip-layer access** -- Presentation code does not directly call the database. It goes through business logic, which calls data access. Each layer calls only the one directly below it.
- [ ] **No upward dependencies** -- Data access code does not import presentation types. Business logic does not import HTTP framework types.
- [ ] **Framework isolation** -- The framework (Rails, Django, Express, Spring) is confined to the presentation and infrastructure layers. Business logic can run without the framework.

### Architecture Pattern Fit
- [ ] **Pattern matches the problem** -- Monolith for small teams and simple domains. Microservices for large teams needing independent deployment. Event-driven for complex workflows with multiple consumers. Layered for traditional business applications.
- [ ] **Pattern is consistently applied** -- If the system is a layered architecture, all features follow the layering. Exceptions are documented and justified.
- [ ] **Boundaries are explicit** -- Whether the system is a monolith or microservices, boundaries between areas of responsibility are explicitly defined through directories, packages, or service contracts.

### Distributed Systems Concerns (if applicable)
- [ ] **Communication patterns are intentional** -- Direct function calls for in-process, message queues for async decoupled work, REST/gRPC for synchronous cross-service. The choice is documented.
- [ ] **Failure handling across boundaries** -- Cross-service calls have timeouts, retries with backoff, and circuit breakers. A failing dependency degrades gracefully rather than cascading.
- [ ] **Consistency model is chosen** -- Strong consistency where correctness requires it (payments, inventory). Eventual consistency where freshness can lag (analytics, feeds). The choice is explicit per data type.
- [ ] **No distributed monolith** -- If services must be deployed together, share a database, or call each other synchronously in lockstep, the system has the complexity of microservices without the benefits. Consolidate or decouple.

Source: [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Distributed Systems](https://jeffbailey.us/blog/2025/10/11/fundamentals-of-distributed-systems/), [Fundamentals of Centralized Software Systems](https://jeffbailey.us/blog/2026/01/19/fundamentals-of-centralized-software-systems/)

---

## 4. Modularity Checks

### Module Boundaries
- [ ] **Each module has a public interface** -- An `index` file, `__init__.py`, facade class, or API module that defines what is exposed. Consumers import from the public interface, not internal files.
- [ ] **Internal details are hidden** -- Implementation classes, helper functions, and data structures internal to a module are not imported by other modules.
- [ ] **Boundaries align with domain concepts** -- Modules are named after business concepts (orders, payments, users) not technical layers (models, controllers, services).

### Independence
- [ ] **Modules are independently testable** -- Each module can be tested with its dependencies mocked or stubbed, without starting the entire application.
- [ ] **Adding a feature touches few modules** -- New functionality requires changes in one or two modules, not coordinated changes across five.
- [ ] **Module removal is clean** -- Removing a module requires updating only its direct consumers, not cascading changes through the codebase.

### Interface Design
- [ ] **Interfaces are narrow** -- Module interfaces expose the minimum necessary. A module with 30 public functions likely exposes internal details.
- [ ] **Interfaces are stable** -- Public interfaces change infrequently. Internal implementations change freely without affecting consumers.
- [ ] **Contracts are explicit** -- Function signatures, type annotations, or schema definitions make the contract visible. Consumers do not need to read implementation to understand usage.

### Organization Patterns
- [ ] **Consistent directory structure** -- All modules follow the same organizational pattern. If one module uses `module/handlers/`, `module/services/`, `module/models/`, all modules do.
- [ ] **Appropriate depth** -- Directory nesting is deep enough to organize but shallow enough to navigate. More than 4 levels of nesting indicates over-organization.
- [ ] **Logical grouping** -- Related files are adjacent. Test files are near the code they test. Configuration is near the code it configures.

Source: [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of Software Maintainability](https://jeffbailey.us/blog/2025/12/30/fundamentals-of-software-maintainability/)

---

## 5. Naming Quality

### Clarity
- [ ] **Functions use verbs** -- `calculateTotal()`, `validateInput()`, `sendNotification()`. Not `total()`, `input()`, `notification()`.
- [ ] **Variables use nouns** -- `userAccount`, `orderTotal`, `paymentStatus`. Not `x`, `data`, `tmp`.
- [ ] **Booleans use question words** -- `isValid`, `hasPermission`, `canEdit`, `shouldRetry`. Not `valid`, `permission`, `edit`.
- [ ] **No abbreviations that require lookup** -- `userAccount` not `usrAcct`. Standard abbreviations (ID, URL, API, HTTP) are acceptable.
- [ ] **No generic names on public interfaces** -- `processData()`, `handleRequest()`, `Manager` without a domain prefix provide no information about purpose.

### Consistency
- [ ] **Same pattern for same concept** -- If retrieval uses `get`, all retrieval uses `get`, not sometimes `fetch`, `retrieve`, `find`, `load`.
- [ ] **Consistent suffixes for similar types** -- If coordinating classes use `Service`, all do. Not `Service`, `Manager`, `Handler`, `Processor` for the same pattern.
- [ ] **Consistent casing** -- One casing style per element type: camelCase for variables and functions, PascalCase for classes, UPPER_SNAKE_CASE for constants. No mixing.
- [ ] **Consistent terminology** -- The same concept uses the same term everywhere. If it is `userAccount` in one place, it is not `account` or `user` elsewhere.

### Context Appropriateness
- [ ] **Local scope allows brevity** -- `order` inside `processOrders()` is clear. `order` as a global variable is ambiguous.
- [ ] **Public interfaces use full specificity** -- Public API methods use complete, self-documenting names. Private helpers can be more concise.
- [ ] **Domain context is used** -- In an e-commerce module, `Order` is sufficient. In a generic module, `CustomerOrder` provides necessary context.

### Discoverability
- [ ] **Names are searchable** -- `calculateTotalPrice` is findable. `calc` matches too many things.
- [ ] **Names are distinctive** -- `processPayment` narrows search results. `process` does not.
- [ ] **Hierarchical names reflect organization** -- `UserAccountManager` indicates the domain and role. `Manager` alone does not.

### Anti-Patterns
- [ ] **No names that lie** -- A function called `getUser()` that creates a user is misleading. Names must match behavior.
- [ ] **No names that do not scale** -- `Manager`, `Service`, `Handler` without domain prefixes become ambiguous as the system grows.
- [ ] **No inconsistent abbreviation** -- If `ID` is used, do not mix it with `Id`, `id`, or `identifier` for the same concept.

Source: [Fundamentals of Naming](https://jeffbailey.us/blog/2025/12/31/fundamentals-of-naming/)

---

## 6. API Design and Contracts

### Contract Clarity
- [ ] **Inputs and outputs are defined** -- Each endpoint or function has documented parameters, return types, and side effects. Consumers do not need to read implementation code.
- [ ] **Field semantics are explicit** -- Fields like `amount` specify units (cents vs dollars), `timestamp` specifies timezone (UTC), `status` values are enumerated.
- [ ] **Invariants are documented** -- Required fields, valid ranges, ordering guarantees, and uniqueness constraints are part of the contract.

### Error Handling
- [ ] **Consistent error shape** -- All endpoints return errors in the same format: an error code, a human-readable message, and field-level detail where applicable.
- [ ] **Errors distinguish client vs server** -- 4xx errors mean the client sent a bad request. 5xx errors mean the server failed. This distinction is consistently applied.
- [ ] **Retryable errors are identified** -- The contract specifies which errors are transient (retry) and which are permanent (fix the request).
- [ ] **Error codes are stable** -- Consumers can match on error codes programmatically. Codes do not change between releases.

### Compatibility and Versioning
- [ ] **Backward-compatible changes are the default** -- New optional fields are added. Existing fields are not removed or renamed without a migration path.
- [ ] **Breaking changes have a versioning strategy** -- URL versioning, header versioning, or content negotiation. The strategy is documented and consistently applied.
- [ ] **Deprecation is communicated** -- Deprecated fields or endpoints are marked, consumers are notified, and a timeline for removal is published.
- [ ] **Schema changes vs contract changes are distinguished** -- Adding an optional field is a schema change, not a contract break. Removing a required field is a contract break.

### Idempotency
- [ ] **Write operations specify idempotency behavior** -- POST endpoints document whether repeating the request creates duplicates.
- [ ] **Idempotency keys are supported for critical writes** -- Payment, order creation, and other mutation endpoints accept client-generated idempotency keys.
- [ ] **GET, PUT, DELETE are idempotent by design** -- Repeating these operations produces the same result. This follows HTTP specification.

### RESTful Design (if applicable)
- [ ] **Resource-based URLs** -- `/api/users/123` not `/api/getUser?id=123`. Resources are nouns, actions are HTTP methods.
- [ ] **Proper HTTP method usage** -- GET for reads, POST for creation, PUT for full update, PATCH for partial update, DELETE for removal.
- [ ] **Consistent pagination** -- List endpoints use cursor-based or offset pagination. Response includes total count or next-page indicator.
- [ ] **HATEOAS or linking where useful** -- Related resources are linked or discoverable, reducing client hardcoding of URL patterns.

Source: [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/), [Fundamentals of Backend Engineering](https://jeffbailey.us/blog/2025/10/14/fundamentals-of-backend-engineering/)

---

## 7. Maintainability Indicators

### Code Smells
- [ ] **No god classes** -- Classes over 500 lines likely have multiple responsibilities. Split by responsibility.
- [ ] **No long methods** -- Methods over 50 lines are hard to understand and test. Extract sub-functions.
- [ ] **No deep nesting** -- More than 4 levels of indentation indicates missing abstractions. Use early returns, guard clauses, or extract functions.
- [ ] **No magic numbers** -- Numbers like `86400`, `3600`, `1024` appear without context. Extract to named constants: `SECONDS_PER_DAY = 86400`.
- [ ] **No magic strings** -- Strings like `"active"`, `"pending"`, `"admin"` scattered through code. Use enums or named constants.
- [ ] **No duplicated logic** -- The same validation, calculation, or transformation appears in multiple places. Extract to a shared function.

### Technical Debt Tracking
- [ ] **TODO/FIXME/HACK comments are tracked** -- These comments indicate known issues. They should be in a tracking system, not just inline comments.
- [ ] **Suppressed warnings are justified** -- Lint or compiler warning suppressions have a comment explaining why the suppression is necessary.
- [ ] **Dead code is removed** -- Commented-out code, unused functions, and unreachable branches are removed, not left to confuse readers.

### Test Coverage
- [ ] **Critical paths have tests** -- Business-critical workflows (payments, authentication, data processing) have automated test coverage.
- [ ] **Tests verify behavior, not implementation** -- Tests check what the code does, not how it does it. Implementation changes should not break tests.
- [ ] **Tests are fast and independent** -- Tests run in seconds, not minutes. Tests do not depend on execution order or shared state.

### Documentation
- [ ] **Non-obvious decisions have "why" documentation** -- Architecture Decision Records, code comments explaining trade-offs, or README sections that explain design choices.
- [ ] **API documentation is current** -- API docs match the actual API behavior. Outdated docs are worse than no docs.
- [ ] **Onboarding path exists** -- A new developer can understand the system structure, set up their environment, and make a change within a reasonable timeframe.

### Dependency Health
- [ ] **Dependencies are current** -- Major dependencies are within one major version of latest. Security patches are applied promptly.
- [ ] **No abandoned dependencies** -- Dependencies with no commits in 2+ years and open security advisories are risks.
- [ ] **License compatibility** -- Dependency licenses are compatible with the project license. No GPL in MIT projects without acknowledgment.
- [ ] **Dependency count is intentional** -- Each dependency provides clear value. Trivial dependencies (left-pad problems) are candidates for removal.

### Refactoring Readiness
- [ ] **Code is testable** -- Functions have explicit inputs and outputs. Side effects are isolated. Dependencies can be injected.
- [ ] **Small changes are safe** -- There is enough test coverage that a developer can refactor with confidence that regressions will be caught.
- [ ] **Refactoring happens incrementally** -- Code is improved continuously, not saved for large refactoring sprints that never happen.

Source: [Fundamentals of Software Maintainability](https://jeffbailey.us/blog/2025/12/30/fundamentals-of-software-maintainability/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/)

---

## 8. Integration and Communication Patterns

### Internal Integration
- [ ] **Module communication is through defined interfaces** -- Modules call each other through public APIs, not by reaching into internal implementation.
- [ ] **Data flows in one direction through layers** -- Requests flow down (presentation to data access), responses flow up. No callback chains that reverse direction.
- [ ] **Shared data has a single owner** -- Each piece of data has one module responsible for writes. Other modules read through that module's interface.

### External Integration
- [ ] **External service calls are wrapped** -- Calls to third-party APIs are encapsulated in adapter classes. Business logic does not directly call external SDKs.
- [ ] **External contracts are tested** -- Contract tests verify that the integration behaves as expected. A change in the external service triggers test failures, not production failures.
- [ ] **Fallback behavior exists** -- When an external service is unavailable, the system degrades gracefully: cached data, default values, or queued-for-later processing.

### Communication Pattern Selection
- [ ] **Synchronous for request-response** -- When the caller needs a result immediately, synchronous communication is appropriate.
- [ ] **Asynchronous for fire-and-forget** -- When the caller does not need the result immediately (notifications, logging, analytics), async processing reduces latency.
- [ ] **Event-driven for multiple consumers** -- When multiple parts of the system need to react to the same event, publish-subscribe decouples the producer from consumers.
- [ ] **Batch for scheduled processing** -- When data can be processed in bulk at intervals, batch processing is simpler than streaming.

Source: [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Backend Engineering](https://jeffbailey.us/blog/2025/10/14/fundamentals-of-backend-engineering/), [Fundamentals of Centralized Software Systems](https://jeffbailey.us/blog/2026/01/19/fundamentals-of-centralized-software-systems/)

---

## 9. Architecture Decision Quality

### Decision Documentation
- [ ] **Significant decisions are recorded** -- Architecture Decision Records (ADRs) or equivalent documentation exists for choices like database selection, framework choice, and architectural pattern.
- [ ] **Decisions include trade-offs** -- Each decision documents what was gained and what was sacrificed. "We chose eventual consistency for read performance at the cost of stale reads up to 5 seconds."
- [ ] **Decisions include context** -- The constraints and requirements at the time of the decision are recorded, so future developers understand why the choice was made.

### Trade-off Analysis
- [ ] **Flexibility vs simplicity is balanced** -- Over-engineered abstractions for hypothetical future needs violate YAGNI. Under-engineered code that resists real change violates the Open/Closed Principle.
- [ ] **Performance vs maintainability is balanced** -- Start with maintainable code. Optimize only when measured performance requires it and the bottleneck is identified.
- [ ] **Consistency vs context is balanced** -- Consistent patterns across the codebase with intentional exceptions where a different approach is justified and documented.

### Pattern Application
- [ ] **Patterns solve real problems** -- Design patterns are used because they solve a specific, identified problem, not because they demonstrate knowledge.
- [ ] **Patterns are not over-applied** -- Factory factories, strategy strategies, and patterns nested inside patterns indicate over-engineering.
- [ ] **The chosen pattern fits the scale** -- Microservices for a 3-person team with 100 users is premature. A single-file script for a 50-person team with 10 million users is insufficient.

Source: [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/)

---

## Quick Reference: The Seven Most Common Architecture Problems

1. **Circular dependencies** -- Module A imports B, B imports A. Fix: extract shared code into a third module, or invert the dependency using interfaces.
2. **God class** -- A class with 1000+ lines handling multiple unrelated responsibilities. Fix: split by responsibility into focused classes.
3. **Leaky layers** -- Controllers contain SQL queries or business logic. Fix: extract business logic to a service layer, data access to a repository layer.
4. **Inconsistent naming** -- `getUser()`, `fetchOrder()`, `retrieveProduct()` for the same pattern. Fix: pick one convention and apply it everywhere.
5. **Missing module boundaries** -- Any file can import any other file with no structure. Fix: define public interfaces per module, hide internals.
6. **Inconsistent error handling** -- Every endpoint returns errors differently. Fix: define a single error response schema and enforce it.
7. **Premature distribution** -- Microservices for an application that fits in a monolith. Fix: consolidate into a modular monolith with clear internal boundaries.

---

## Source Articles

- [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/)
- [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/)
- [Fundamentals of Naming](https://jeffbailey.us/blog/2025/12/31/fundamentals-of-naming/)
- [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/)
- [Fundamentals of Software Maintainability](https://jeffbailey.us/blog/2025/12/30/fundamentals-of-software-maintainability/)
- [Fundamentals of Distributed Systems](https://jeffbailey.us/blog/2025/10/11/fundamentals-of-distributed-systems/)
- [Fundamentals of Centralized Software Systems](https://jeffbailey.us/blog/2026/01/19/fundamentals-of-centralized-software-systems/)
- [Fundamentals of Backend Engineering](https://jeffbailey.us/blog/2025/10/14/fundamentals-of-backend-engineering/)
- [Fundamental Software Concepts](https://jeffbailey.us/blog/2025/10/11/fundamental-software-concepts/)
