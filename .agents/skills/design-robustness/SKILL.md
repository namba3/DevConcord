---
name: design-robustness
description: "Design contracts and recovery for failures, partial success, cancellation, retries, concurrency, corruption, and resource limits. Use when a feature or architecture must remain consistent and diagnosable under abnormal conditions."
---

# Robustness by Design

## Workflow

1. Identify trust boundaries, state and data invariants, operation preconditions/postconditions, resource ownership, and the impact of a failed or duplicated operation.
2. Select relevant failure modes: malformed/corrupt input, permission/resource/disk limits, network delay/timeout, dependency or OS failure, partial completion, cancellation, process crash, concurrency conflict, unexpected scale.
3. Define the failure contract: what remains committed, what is rolled back or recoverable, whether retry is safe/idempotent, how resumption works, what the user/operator is told, and what diagnostics are recorded.
4. Choose only justified controls: transactions/atomic replacement, fail-safe defaults, validation at trust boundaries, fault isolation, graceful degradation, bounded retries/timeouts, resource cleanup. Never swallow errors, retry indiscriminately, or multiply implementations as a substitute for a contract.
5. Map important invariants to boundary/property/state-machine/concurrency/fault-injection/recovery/resource-exhaustion/regression tests as risk and cost warrant. Verify both “state is not corrupted” and “failure is accurately observable.”
6. Connect requirements, ADRs and follow-up work to existing IDs/registers; report untested guarantees as unverified.

## Completion

For each critical operation, state the normal contract, important failure outcomes, preserved invariants, recovery/retry semantics, observable diagnostics and concrete verification evidence.
