---
name: devconcord-observability-design
description: >
  Design proportionate observability and diagnostics for important system
  states, operations, failures, and recovery, including safe signals and
  verification. Use when a project needs to understand behavior in normal or
  abnormal operation; do not require a telemetry stack by default.
---

# Observability & Diagnosability by Design

Design for understanding what the system did, what failed, its impact, and
whether it recovered, using the smallest useful and safe evidence. Logs,
metrics, traces, diagnostic reports, and user-facing errors are means to answer
real user, developer, or operator questions; their volume is not a quality
goal. A diagnostic signal can narrow investigation without proving a root
cause.

## When to use

Use this Skill when important behavior is difficult to understand during
normal or abnormal operation, or a change adds logging, metrics, tracing,
diagnostic export, error reporting, or telemetry. Use it proportionately for
the system's scale and risk. A small CLI may need only useful error categories
and exit codes; distributed tracing or remote telemetry needs a concrete
requirement.

## Workflow

Read [the detailed workflow](references/workflow.md). Inspect project
instructions, user/operator tasks, relevant requirements and architecture,
errors and state transitions, existing signals, deployment/runtime constraints,
privacy/security obligations, tests, and support or runbooks as applicable.
Keep confirmed facts, design proposals, assumptions, and unknowns distinct.

Define the diagnostic questions first, then select only useful signals and
their owners, semantics, retention, access, failure behavior, and verification.
Connect requirements to the existing request/specification and issue system.
Prefer explicit collection of needed context over collecting broad data and
trying to redact it later. Do not promise that telemetry can identify every
root cause or that all events are retained.

## Boundaries

- `devconcord-design-robustness` defines failure contracts, state consistency,
  and recovery; this Skill defines how relevant behavior and outcomes can be
  observed. Both are needed when diagnostics affect recovery guarantees.
- `devconcord-design-performance` defines workload and performance constraints;
  this Skill defines useful measurements and their semantics. Do not invent
  SLI/SLO targets or claim a performance result without measurement.
- `devconcord-design-security` defines assets, threats, trust boundaries, and
  protections. This Skill applies them to emitted, stored, exported, and sent
  diagnostic data. Logs and correlation IDs are not credentials or audit
  controls by default.
- `devconcord-ux-functional-design` handles user-facing error, progress, and
  recovery workflows; `devconcord-test-design` derives independent tests;
  `devconcord-documentation-architecture` structures support documentation.

These Skills are optional, separate workflows. Check availability in the
target's User Scope or Project Scope; do not assume automatic handoff. Continue
from verified project guidance when an optional Skill is unavailable.

## Deliverable

For the requested scope, report the diagnostic questions and affected users,
selected signals and why, important event/metric/trace/error semantics, data
minimization and privacy/security controls, operational and performance
failure behavior, acceptance and verification conditions, existing requirement
or issue references, tradeoffs, and unverified limits. Use the target's
existing design records; do not create a parallel observability score or
tracking ledger.

## DevConcord References

Use `devconcord-reference` when available. Identify this Skill as the requester and retrieve the required common development guide. If the common Skill cannot be selected, run the configured source checkout's CLI directly. For Project Scope, pass `--scope project --target <target-repository>` as well.

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-observability-design \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

Requirements, ADR, UI/UX, and Secrets by Design references are optional when relevant. Read only needed paths, one CLI invocation per path. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop that part of the assessment; if it is optional and unavailable, report it and continue only if the result remains grounded.
