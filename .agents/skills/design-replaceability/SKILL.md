---
name: design-replaceability
description: "Assess boundaries for replaceable UI frameworks, storage, network, OS APIs, external services, and runtimes. Use when a technology change may have broad impact or when designing modular architecture without over-abstraction."
---

# Replaceability by Design

## Workflow

1. Identify only consequential technical dependencies; assess probability/value of change, current coupling impact, migration cost and the cost of an abstraction.
2. Keep domain concepts and application use cases independent of UI widget/event/lifecycle types where justified. Separate domain/application state from presentation state. Permit views to require rewriting when changing fundamentally different UI frameworks.
3. For storage, network, OS and services, define a domain/application-owned contract and place technology-specific code at an adapter boundary only when the expected change value justifies it.
4. Specify semantic compatibility, not just method signatures: errors, transactions, atomicity, consistency, concurrency, performance, security, persistence formats, migrations and user-visible behavior.
5. Avoid interface-for-everything, unused alternative implementations, one-to-one library wrappers, least-common-denominator APIs and costly conversions/dispatch without evidence. A single concrete implementation can be correct.
6. Verify the claim with dependency-direction checks, adapter contract tests, integration/migration tests, or a small replacement experiment as appropriate. State exactly what can be preserved and what must change.

## Completion

Document the dependency, reason to isolate it, boundary/semantic contract, allowed migration scope, abstraction costs and verification evidence. Do not promise zero-change replacement.
