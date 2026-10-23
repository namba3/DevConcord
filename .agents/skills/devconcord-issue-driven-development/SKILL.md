---
name: devconcord-issue-driven-development
description: >
  Use an existing project issue register as the source of truth to select,
  implement, verify, and update bounded work in Plan, Single, or Batch mode.
---

# Issue-Driven Development

Use the target repository's existing issue register to make verified progress
on requested work. Optimize for validated user value, quality, and
maintainability, not the number of closed issues. The register's existing
conventions remain authoritative; this Skill does not create a parallel task,
risk, or quality ledger.

## Select a mode

- **Plan:** The user asks what to do next or requests assessment/planning. Read
  only; do not edit code, settings, documents, or issue records.
- **Single:** The user names an issue or clearly asks for one issue to be
  implemented. Work only on that issue and its necessary, authorized scope.
- **Batch:** The user asks to continue issue-driven development across multiple
  issues. Select a bounded set using dependencies, value, risk, and their
  stated limits. Stop at the requested boundary; do not run indefinitely.
- If implementation intent or scope is unclear, use Plan and explain the
  assumption. Never infer permission to implement, commit, push, reset, or
  rewrite history.

## Workflow

Read [the detailed workflow](references/workflow.md). First inspect repository
instructions, HEAD, worktree and index state, the existing issue register,
related requirements/design, implementation, tests, and CI. Protect unrelated
changes. Confirm issue facts against the current repository; do not treat
stale issue text as proof.

In every mode, distinguish confirmed facts, assumptions, unknowns, and
verification evidence. Respect dependencies and blockers. Keep implementation
increments small enough to review and verify. Apply relevant design principles
proportionately; use specialized Skills only when available and useful, without
assuming automatic handoff.

## Completion contract

Implementation alone does not complete an issue. Distinguish implementation,
tests added, tests run, tests passed, acceptance conditions met, and review or
other required confirmation. Update the existing issue register only in Single
or Batch mode and only with evidence supported by the work. Preserve IDs,
history, evaluation axes, weights, and status meanings. Do not change a
completion score for routine work; reassess only materially affected existing
axes when evidence warrants it.

Report issue IDs, changes, checks and results, issue-state updates, blockers,
unverified work, material new findings, and a reasonable next issue when
applicable. Never describe static checks as real-agent evaluation. Follow the
user's requested work boundary and the repository's own commit instructions.

## Related Skills

- `devconcord-implementation-planning` plans complex changes; it does not
  execute them by default.
- `devconcord-test-design` derives independent verification expectations.
- `devconcord-repository-review` reviews concrete changes; `devconcord-gap-analysis`
  assesses cross-cutting quality gaps.
- `devconcord-design-*`, `devconcord-ux-functional-design`, and
  `devconcord-documentation-architecture` address material design questions.

Check User Scope or Project Scope availability in the actual target context.
These are optional aids, not automatic calls or prerequisites. If unavailable,
continue from verified project guidance within the safe scope.

## DevConcord References

Use `devconcord-reference` when available, identify this Skill as the
requester, and retrieve the required issue-tracking rules. If the common Skill cannot be selected,
run the configured source checkout's CLI directly. For
Project Scope, pass `--scope project --target <target-repository>` as well.

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-issue-driven-development \
  --path docs/work-management/issue-tracking.md \
  --revision installed
```

The issue-register template and AI-assisted development guide are optional
references when the target needs them. Read only the needed path, one CLI
invocation per path. Do not silently switch revisions or claim unread content
was applied. If a required reference cannot be read, stop; if it is optional,
report the failure and continue only if the work remains self-contained.
