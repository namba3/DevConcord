
# Development Orchestration

This workflow applies **Iterative & Evidence-Driven Development** to projects
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
belongs to `develop issue` instead.

## Iteration contract

Follow [`references/workflow.md`](references/workflow.md): establish a fresh
baseline; select one coherent, verifiable work unit from existing project
tracking; implement only within scope; verify; review the final diff; update
authorized existing records; then decide to continue, repair, reconsider
design, report blocked, or stop. Use proportionate checks and tie evidence to
the final changed state. Assess relevant risk before selecting specialist
Skills and verification depth, then reassess after implementation, failures,
and review when evidence changes impact, uncertainty, affected scope, or
evidence confidence. Follow the canonical principles in
`docs/common/ai-assisted-development.md` §17.5; they do not add a checklist,
score, or mandatory Skill gate.

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
conflict, pause dependent work and select `design evolve` for authorized design
work; continue only safe independent work.

Before advancing, check scope integrity, contract integrity, relevant
verification evidence, regression risk, and whether another iteration has a
credible benefit. A failed gate requires diagnosis; do not weaken expectations,
delete tests, or keep editing blindly until checks pass. Preserve the existing
issue register as the work source of truth, existing completion axes and
weights, issue IDs and history, and separate risk records. Add no parallel
progress ledger or quality score.

When current evidence reveals a material blocker or unresolved judgment,
consider `develop unblock` or the matching `decide` command before selecting
dependent implementation. This is conditional, not a standard loop step or
quality gate. Keep the existing finite iteration/investigation budget; route
approval-dependent choices to the authorized decision maker and continue only
safe independent work.

## Related internal workflows and completion

Do not duplicate specialist workflows or assume automatic Skill handoffs:

- `develop issue` selects and completes a specified issue or bounded batch,
  including evidence and issue-state updates.
- `develop implementation-plan` orders complex implementation units.
- `verify test-design` defines independent expected outcomes and strategy.
- `review repository` finds concrete defects and regressions; `review gap`
  assesses cross-cutting quality gaps.
- `design evolve` handles authorized design evolution; focused `quality`
  commands address individual quality attributes.
- `diagnose root-cause` can be considered when a material failure has an
  unclear or disputed cause; diagnosis does not authorize repair.
- `lifecycle compatibility` is considered when a changed public contract or
  persisted/exchanged format creates a real compatibility risk.
- `lifecycle release` can be proposed from Stabilize when the user asks to
  assess a release candidate, distribution, upgrade, or recovery.
- `lifecycle dependencies` is considered when dependency adoption, change,
  removal, or a material dependency risk is in scope.
- `evaluate agent` evaluates whether an agent discovers, selects, and executes
  the public `devconcord` package; it is not a gate for ordinary product work.

These optional workflows are not standard-loop steps, mandatory dependencies, or
quality gates. Do not create a per-run checklist for them. Do not stop unrelated work
because an optional workflow is not selected, or treat non-use as a defect. Consider one
only when the user explicitly requests it or the work reveals a material
related risk. Core compatibility, security, and data-loss checks remain part
of the relevant work even when a specialist workflow is not selected. A suggestion
does not authorize an automatic handoff, broader permissions, release action,
or approval. Continue to use the existing requirements, issue register,
verification, and review contracts without these optional workflows.

Check whether the single public `devconcord` package is available in the actual
User or Project Scope before relying on its internal workflows; package files
alone do not prove that the host discovers or selects them. Report the selected scope, completed and partial work units, changed
artifacts, checks and results, issue/evidence updates, remaining blockers,
unverified conditions, and the continue/stop rationale. Do not claim real
agent or target-environment evidence from static tests.

## DevConcord References

Use `devconcord manage reference` when the public package is available, state
the requesting internal workflow as context, and retrieve only needed canonical
paths at the installed package revision. The CLI package identity remains
`--skill devconcord`.
For Project Scope, also pass `--scope project --target <target-repository>`.
If the Reference workflow cannot be selected, run the configured source checkout's
CLI directly, one path per invocation:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord \
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

## Optional session handoff

For long-running, complex incomplete, or multi-session work, use an existing
handoff as a concise checkpoint snapshot when useful. It supplements the issue
register and current repository evidence; it is not a required loop artifact,
quality gate, evidence source, or permission grant. Absence does not block
Plan/Iterate/Stabilize. At meaningful checkpoints, capture the current work
unit, verified progress and its state, material pending verification, findings,
blockers, and next safe action without copying quality-gate output or issue
lists. Place a newly created handoff beside the target's authoritative issue
register; do not impose a fixed target path or duplicate an existing equivalent
handoff elsewhere. Keep the existing finite budget and stop conditions.
