---
name: devconcord-design-performance
description: >
  DevConcord design workflow for deriving performance requirements and
  architecture from workload evidence. Use when latency, throughput, memory,
  CPU/GPU, I/O, startup, large data, concurrency, caching, or regression risk
  matters; define measurable constraints without inventing targets.
---

# Performance by Design

## Workflow

1. Identify important user-visible and internal paths, representative workload/data sizes, target environments, latency/throughput/resource constraints, and measurement method. Keep estimates and unknowns explicit; do not invent numeric targets.
2. Evaluate algorithm and data-structure complexity, data flow/locality, full-load versus streaming/lazy/batched processing, allocations/copies, CPU/GPU/memory/I/O, startup/perceived response, concurrency/synchronization, backpressure and resource limits.
3. Derive necessary functional behavior (incremental results, cancellation, pagination, bounded work, degraded mode) where it improves the real workflow. Connect it to state and consistency contracts.
4. Choose the simplest architecture that fits the workload. Use caching, parallelism, virtualization or abstraction only when justified; include invalidation, synchronization, memory, failure and maintenance costs.
5. Define a representative benchmark/profile/regression strategy with data, environment, run procedure, acceptable variation and evidence. Do not claim measured performance before running it.
6. Record consequential tradeoffs in ADRs; preserve correctness, security, robustness and understandable code.

## Completion

Show workload evidence → design choice → acceptance/measurement condition → actual result or unverified status. Avoid post-hoc “make it fast” directives and unsupported claims.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-design-performance --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this Skill. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord AI-assisted development guide](https://github.com/namba3/DevConcord/blob/main/docs/common/ai-assisted-development.md)
- [Requirements template](https://github.com/namba3/DevConcord/blob/main/docs/application-design/templates/requirements.md)
