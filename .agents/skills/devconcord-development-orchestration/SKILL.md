---
name: devconcord-development-orchestration
description: >
  Orchestrate bounded, evidence-driven development cycles across existing
  requirements, designs, and issue registers. Select this Skill when the user
  delegates iterative implementation, verification, review, repair, and
  continue-or-stop decisions across multiple work units. Includes read-only
  planning and stabilization without new features. Use issue-driven development
  for a single issue or bounded batch, and use review or design Skills for
  those focused tasks.
---

# Development Orchestration

This Skill applies **Iterative & Evidence-Driven Development** to projects
whose requirements, design decisions, and work tracking are sufficiently
established. Its goal is verified user value, requirement fulfillment, and
reduced material risk—not the number of iterations, edits, or closed issues.

## Choose a mode

- **Plan:** Read-only assessment and a bounded iteration plan. Do not edit
  source, tests, settings, design artifacts, issue records, or scores. A plan
  does not grant implementation permission.
- **Iterate:** Execute user-authorized implementation, verification, review,
  integration, and next-step decisions across a finite number of work units.
- **Stabilize:** Improve existing behavior, verification, and consistency
  without adding features. Prefer defects, regressions, important verification
  gaps, security/reliability risks, and stale design evidence. Avoid broad
  refactoring or architecture changes without clear evidence and authority.

Infer the mode from the request. If implementation authority or scope is
unclear, use Plan. A request for one issue or a small bounded batch normally
belongs to `devconcord-issue-driven-development` instead.

## Iteration contract

Follow [`references/workflow.md`](references/workflow.md): establish a fresh
baseline; select one coherent, verifiable work unit from existing project
tracking; implement only within scope; verify; review the final diff; update
authorized existing records; then decide to continue, repair, reconsider
design, report blocked, or stop. Use proportionate checks and tie evidence to
the final changed state.

Use a finite iteration and change budget. Honor user limits; when none are
specified, begin with at most three work units and at most one focused repair
pass per unit. Do not expand those limits without renewed user direction.
Stop early when the goal is met, progress is unsupported, important gates
fail, approval or evidence is missing, competing changes appear, or further
work has low value.

## Authority and quality gates

User authorization bounds code, tests, documentation, issue updates, and
external effects separately. Do not infer permission for out-of-scope work,
major requirement or architecture changes, destructive actions, commit, push,
or history rewriting. If implementation reveals a consequential design
conflict, pause dependent work and route it to `devconcord-design-orchestration`
when available; continue only safe independent work.

Before advancing, check scope integrity, contract integrity, relevant
verification evidence, regression risk, and whether another iteration has a
credible benefit. A failed gate requires diagnosis; do not weaken expectations,
delete tests, or keep editing blindly until checks pass. Preserve the existing
issue register as the work source of truth, existing completion axes and
weights, issue IDs and history, and separate risk records. Add no parallel
progress ledger or quality score.

## Related Skills and completion

Do not duplicate specialist workflows or assume automatic Skill handoffs:

- `devconcord-issue-driven-development` selects and completes a specified
  issue or bounded batch, including evidence and issue-state updates.
- `devconcord-implementation-planning` orders complex implementation units.
- `devconcord-test-design` defines independent expected outcomes and strategy.
- `devconcord-repository-review` finds concrete defects and regressions;
  `devconcord-gap-analysis` assesses cross-cutting quality gaps.
- `devconcord-design-orchestration` handles authorized design evolution;
  focused design Skills address individual quality attributes.
- `devconcord-root-cause-analysis` can be considered when a material failure
  has an unclear or disputed cause; diagnosis does not authorize repair.
- `devconcord-compatibility-migration` is considered when a changed public
  contract or persisted/exchanged format creates a real compatibility risk.
- `devconcord-release-engineering` can be proposed from Stabilize when the
  user asks to assess a release candidate, distribution, upgrade, or recovery.
- `devconcord-dependency-governance` is considered when dependency adoption,
  change, removal, or a material dependency risk is in scope.
- `devconcord-agent-behavior-evaluation` evaluates whether agents discover,
  select, and execute Skills; it is not a gate for ordinary product work.

These optional Skills are not standard-loop steps, mandatory dependencies, or
quality gates. Do not create a per-run checklist for them. Do not stop unrelated
work because an optional Skill is unavailable, or treat non-use as a defect. Consider one
only when the user explicitly requests it or the work reveals a material
related risk. Core compatibility, security, and data-loss checks remain part
of the relevant work even when a specialist Skill is not used. A suggestion
does not authorize an automatic handoff, broader permissions, release action,
or approval. Continue to use the existing requirements, issue register,
verification, and review contracts without these optional Skills.

Check Skill availability in the actual User or Project Scope before relying on
it. Report the selected scope, completed and partial work units, changed
artifacts, checks and results, issue/evidence updates, remaining blockers,
unverified conditions, and the continue/stop rationale. Do not claim real
agent or target-environment evidence from static tests.

## DevConcord References

Use `devconcord-reference` when available, identify this Skill as the
requester, and retrieve only needed canonical paths at the installed revision.
For Project Scope, also pass `--scope project --target <target-repository>`.
If the common Skill cannot be selected, run the configured source checkout's
CLI directly, one path per invocation:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-development-orchestration \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

Other useful paths include `docs/work-management/issue-tracking.md`,
`docs/work-management/risk-management.md`,
`docs/application-design/templates/requirements.md`, and
`docs/application-design/templates/adr.md`. Do not silently switch revisions
or claim unread references were applied. If a required reference cannot be read, stop; if it is optional,
report the failure and continue only independent work
supported by available evidence.
