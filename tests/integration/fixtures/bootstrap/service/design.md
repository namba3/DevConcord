# Inventory API design input

- Project: Inventory API
- Platform: Containerized Linux service.
- Language/build: Rust and Cargo.
- HTTP: A Rust HTTP server framework is selected by the project owner.
- Persistence: PostgreSQL is selected. Updates to a single inventory reservation must be atomic.
- User goal: Internal clients reserve and release stock.
- Failure contract: Duplicate request identifiers must not create duplicate reservations. Database/network failures must not be reported as successful writes.
- Security: Authenticated service-to-service calls; credentials must come from the deployment environment and must not be committed.
- Testing: Core reservation rules must be unit-testable; persistence and HTTP adapters need integration/contract tests against representative dependencies.
- Initial bootstrap scope: Development foundation and core reservation use-case skeleton only; no production endpoint or persistence implementation.
- Replaceability: Preserve reservation semantics and transaction guarantees at the application boundary; do not add an unused second storage implementation.
