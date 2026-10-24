
# Robustness by Design

## Workflow

1. Identify trust boundaries, state and data invariants, operation preconditions/postconditions, resource ownership, and the impact of a failed or duplicated operation.
2. Select relevant failure modes: malformed/corrupt input, permission/resource/disk limits, network delay/timeout, dependency or OS failure, partial completion, cancellation, process crash, concurrency conflict, unexpected scale.
3. Decide whether concurrent execution is needed to meet a requirement. If sequential execution is sufficient, retain it. For justified concurrency, define ownership, ordering, visibility/commit points, and the consistency contract before selecting a mechanism.
4. Define the failure contract: what remains committed, what is rolled back or recoverable, whether retry is safe/idempotent, how resumption works, what the user/operator is told, and what diagnostics are recorded.
5. Choose only justified controls: transactions/atomic replacement, fail-safe defaults, validation at trust boundaries, fault isolation, graceful degradation, bounded retries/timeouts, resource cleanup. Never swallow errors, retry indiscriminately, or multiply implementations as a substitute for a contract.
6. Map important invariants to boundary/property/state-machine/concurrency/fault-injection/recovery/resource-exhaustion/regression tests as risk and cost warrant. Verify both “state is not corrupted” and “failure is accurately observable.”
7. Connect requirements, ADRs and follow-up work to existing IDs/registers; report untested guarantees as unverified.

## Concurrency and shared state

Apply this section only where operations overlap, share mutable state/resources, or depend on ordering. Concurrency is controlled overlap, not a goal to maximize parallelism.

- State the need for overlap and the independent work units. Identify owners and lifetimes for mutable state, locks, handles, tasks, buffers, and external resources; name who may read or change each value.
- Define the required visibility and consistency at operation boundaries: which changes are committed, when other work can observe them, and whether readers need a consistent snapshot. Use serialization, version checks, transactions, or stronger guarantees such as linearizability only when the contract needs them.
- Distinguish language-level data races from logical races. Memory-safe Rust can still have lost updates, TOCTOU, duplicate execution, stale reads, inconsistent snapshots, reentrancy, ordering violations, partial commits, or resource-ownership conflicts.
- Check competing operations against the invariant and transition they can interleave with. Identify whether the design prevents the harmful schedule, detects and rejects it, or tolerates and repairs it.
- Consider deadlock, livelock, starvation, priority inversion, and lock contention by examining wait-for relationships, lock/resource acquisition order, locks held across `await`, synchronous/asynchronous boundaries, and shutdown/join dependencies. State a consistent order or other chosen prevention where needed; “use a mutex” alone is not a contract.
- Choose a single owner, message passing/actor, immutable snapshot, bounded lock, serialized state transition, or optimistic conflict check only when its tradeoffs fit the workload and failure contract. Do not add a pattern or abstraction by default.

## Cancellation and state transitions

Model cancellation as an operation outcome, not as a UI event or stop request alone. Where relevant, distinguish: request accepted, cancellation observed, work stopped at a safe point, child tasks joined, resources released, and state committed or recovered. Define which already-committed effects remain, whether rollback/compensation is possible, how timeout differs from explicit cancellation, and whether retry can duplicate side effects. Resolve the race between cancellation and commit: once commit wins, do not report a terminal `Cancelled` outcome that implies its effects were undone. Structured concurrency, cancellation tokens, and task groups are candidates only when supported and useful.

For critical work, derive a state machine from the contract. Record valid and forbidden transitions, transition preconditions, postconditions/invariants, retry/recovery paths, and any concurrent transitions that race. Include unreachable or non-terminating states only when material. A table or diagram is optional; do not require one for a simple operation.

## Concurrency verification

Choose verification that can exercise or systematically reason about the harmful interleaving: deterministic scheduler/model checks, state-machine or property tests, barriers/channels, fault injection, stress tests, or formal methods as appropriate. Repeated runs alone do not prove that a particular interleaving occurred or that races are absent. For Rust, tools such as loom, Shuttle, Miri, Kani, or Verus are optional candidates; verify tool availability and the behavior it can cover before relying on it. State fixture determinism, execution cost, covered schedules/failures, and remaining unknowns.

When reviewing evidence, check the trigger, observed state/result, invariant, recovery behavior, and whether later changes invalidate the result. Distinguish a proposed test, a present test, a test run, its outcome, and the condition actually covered. Use `devconcord-test-design` when independent expected outcomes or test cases need a dedicated design; do not duplicate its test plan here.

## Boundaries with related Skills

- `devconcord-ux-functional-design` defines user tasks, cancellation controls, and feedback; this workflow defines whether cancellation stopped safely and preserved the operation/data contract.
- When available, `devconcord-observability-design` selects diagnostic questions and signals; this workflow defines the underlying failure, consistency, and recovery guarantee those signals must explain.
- `devconcord-issue-driven-development` executes authorized issue work and tracks its evidence; it does not replace this workflow's design contract. `devconcord-test-design` derives independent expectations for verifying the contract.

These workflows are separate and optional; do not assume automatic Skill handoff or reproduce their detailed checklists here.

## Evaluate verification evidence

When reviewing existing tests or failure-test results, start from the stated
failure contract and invariant rather than from the test names or mechanisms
used. For each important invariant, check that the evidence identifies the
triggered fault or transition, the state and observable result, the expected
failure guarantee, and—where recovery is part of the contract—the state after
retry, restart, rollback, or resumption. Select only the failure conditions
that matter to the operation and its impact.

Distinguish a proposed test, a test present in the repository, a test actually
executed, its result, and the failure modes it covers. A Fault Injection,
State Machine, Property-Based, or concurrency test does not by itself show
that all important invariants hold. Check that the fixture can trigger the
intended condition, that the observation would detect the prohibited state,
and that the test does not merely reproduce implementation assumptions. If
evidence is missing or narrow, state the uncovered condition and a proportionate
next verification. Do not report unexecuted failure behavior as tested.

Use `devconcord-test-design` when the independent test cases or expected
observations need a dedicated design; this workflow remains responsible for the
failure contract and invariant being assessed.

## Completion

For each critical operation, state the normal contract, important failure outcomes, preserved invariants, recovery/retry semantics, observable diagnostics and concrete verification evidence.

## DevConcord References

When one of these canonical references is needed, use `devconcord manage reference` if available. Identify this workflow as the requester and pass only the needed repository-relative path.

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`
- `docs/work-management/issue-tracking.md`

If the Reference workflow cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this workflow. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord AI-assisted development guide](https://github.com/namba3/DevConcord/blob/main/docs/common/ai-assisted-development.md)
- [Issue tracking and quality rules](https://github.com/namba3/DevConcord/blob/main/docs/work-management/issue-tracking.md)
