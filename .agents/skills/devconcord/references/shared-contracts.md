# Shared Workflow Contracts

## Request, scope, and authority

- Preserve explicit requirements, existing design decisions, repository rules, user constraints, and issue-register source of truth.
- Route natural-language requests by intended outcome, target, and current authority. Inspect repository evidence before asking for context that can be discovered safely; resolve routine workflow choice internally, and ask only when the remaining ambiguity materially changes intent, scope, authority, or an important outcome.
- Track implementation/investigation work and blocker status in the issue register. A material open judgment may have a distinct DEC ID/state in that register (or one authorized canonical decisions file); ADRs hold durable design rationale, risk records hold possible future events, and handoffs only point to current context. Do not create duplicate sources of truth.
- Distinguish read-only assessment/planning from authorized modification. A command selects a procedure; it grants no extra permission.
- A decision recommendation is not approval; resolving a DEC does not complete or automatically unblock dependent issues. Recheck every affected issue and its other prerequisites independently.
- Protect unrelated working-tree changes. Do not contact external systems, publish, approve, commit, push, or rewrite Git history unless the user authorized that action.
- Treat important requirement changes, public compatibility breaks, data-loss risk, external side effects, and irreversible actions as approval boundaries.

## Risk-proportional analysis

Assess material impact, uncertainty, propagation, reversibility, and evidence quality. Select only relevant specialist modules and proportionate verification. Reassess after discoveries. Do not use a low-risk label to conceal unknowns or serious consequences, or use module count as a quality score. Optional lifecycle procedures do not waive basic safeguards.

## Evidence and verification

Connect requirements and contracts to observable outcomes and verification. Keep static checks, unit tests, fixtures, browser evidence, native/runtime behavior, devices, remote CI, and real-agent discovery/execution distinct. Do not claim an unobserved result. Choose independent expected behavior where useful; verify the final state after repairs.

Select local checks from the changed surfaces and their actual risks, using existing test runners and CI contracts. Do not ask the user to choose routine verification commands when the repository provides enough evidence to choose them. Keep broad CI regression coverage intact, and report checks that were not run or could not run.

## Canonical updates and reporting

After authorized work, update only canonical records whose owned information changed and whose update is authorized. The issue register owns work/status/acceptance/evidence; DEC owns an open judgment and authority; ADR owns durable design rationale; the risk record owns future uncertainty; HANDOFF is an optional resume checkpoint. Validate IDs, links, and state against current implementation and evidence. Do not copy the same state into another record. If one required canonical update cannot be made safely, report it as incomplete and preserve the conflicting edits; do not claim the records are synchronized.

Normal completion reports should lead with the outcome, relevant verification and remaining work. Keep command logs and detailed diagnosis available in their source rather than repeating them. Put failures, blockers, approval needs, material uncertainty, unverified conditions, and the next safe action first when present. Link or point to evidence when useful; expose detailed diagnostics only when they help explain an exception or the user requests them. Omit empty sections and internal module narration unless the user asks for it. Brevity must not hide failed or unrun checks, residual risk, or authority limits.

## Shared design and development principles

Apply DDD, SDD, TDD, DbC, self-documenting code, UX-driven functional design, performance/robustness/replaceability/security by design, and documentation by design where relevant. Use doc comments for API intent and annotation comments for non-obvious constraints. Work-management issue tables remain the work-tracking source of truth; do not create duplicate risk or quality ledgers.

## References

Use installed-revision reference when version-pinned shared guidance is required and available. Verify source identity, commit, manifest, package integrity, path, and symlink safety through the CLI. On failure, do not silently substitute another revision or online content. State unavailable evidence and decide whether the workflow can safely continue.

## Completion and stopping

Complete only the authorized scope with proportionate verification and required documentation/evidence updates. Stop when the scope is complete, an approval or unresolved material decision is required, the environment is unsafe, required evidence cannot be obtained, or a finite budget is exhausted. Report changed artifacts, verification performed and not performed, remaining risks, and the reason for stopping.
