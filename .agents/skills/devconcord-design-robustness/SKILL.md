---
name: devconcord-design-robustness
description: >
  DevConcord design workflow for defining contracts, state consistency, and
  recovery under abnormal conditions. Use when failures, partial success,
  cancellation, retries, concurrency, corruption, or resource limits can
  affect a feature or architecture.
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

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`
- `docs/work-management/issue-tracking.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-design-robustness --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this Skill. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord AI-assisted development guide](https://github.com/namba3/DevConcord/blob/main/docs/common/ai-assisted-development.md)
- [Issue tracking and quality rules](https://github.com/namba3/DevConcord/blob/main/docs/work-management/issue-tracking.md)
