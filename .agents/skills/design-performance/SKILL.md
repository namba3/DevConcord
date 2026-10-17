---
name: design-performance
description: "Apply Performance by Design to requirements, feature behavior, and architecture. Use when workload, latency, throughput, memory, CPU/GPU, I/O, startup, large data, concurrency, caching, or performance regression matters."
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
