# Shared Workflow Contracts

## Request, scope, and authority

- Preserve explicit requirements, existing design decisions, repository rules, user constraints, and issue-register source of truth.
- Track implementation/investigation work and blocker status in the issue register. A material open judgment may have a distinct DEC ID/state in that register (or one authorized canonical decisions file); ADRs hold durable design rationale, risk records hold possible future events, and handoffs only point to current context. Do not create duplicate sources of truth.
- Distinguish read-only assessment/planning from authorized modification. A command selects a procedure; it grants no extra permission.
- A decision recommendation is not approval; resolving a DEC does not complete or automatically unblock dependent issues. Recheck every affected issue and its other prerequisites independently.
- Protect unrelated working-tree changes. Do not contact external systems, publish, approve, commit, push, or rewrite Git history unless the user authorized that action.
- Treat important requirement changes, public compatibility breaks, data-loss risk, external side effects, and irreversible actions as approval boundaries.

## Risk-proportional analysis

Assess material impact, uncertainty, propagation, reversibility, and evidence quality. Select only relevant specialist modules and proportionate verification. Reassess after discoveries. Do not use a low-risk label to conceal unknowns or serious consequences, or use module count as a quality score. Optional lifecycle procedures do not waive basic safeguards.

## Evidence and verification

Connect requirements and contracts to observable outcomes and verification. Keep static checks, unit tests, fixtures, browser evidence, native/runtime behavior, devices, remote CI, and real-agent discovery/execution distinct. Do not claim an unobserved result. Choose independent expected behavior where useful; verify the final state after repairs.

## Shared design and development principles

Apply DDD, SDD, TDD, DbC, self-documenting code, UX-driven functional design, performance/robustness/replaceability/security by design, and documentation by design where relevant. Use doc comments for API intent and annotation comments for non-obvious constraints. Work-management issue tables remain the work-tracking source of truth; do not create duplicate risk or quality ledgers.

## References

Use installed-revision reference when version-pinned shared guidance is required and available. Verify source identity, commit, manifest, package integrity, path, and symlink safety through the CLI. On failure, do not silently substitute another revision or online content. State unavailable evidence and decide whether the workflow can safely continue.

## Completion and stopping

Complete only the authorized scope with proportionate verification and required documentation/evidence updates. Stop when the scope is complete, an approval or unresolved material decision is required, the environment is unsafe, required evidence cannot be obtained, or a finite budget is exhausted. Report changed artifacts, verification performed and not performed, remaining risks, and the reason for stopping.
