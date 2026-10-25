
# Issue-Driven Development

Use the target repository's existing issue register to make verified progress
on requested work. Optimize for validated user value, quality, and
maintainability, not the number of closed issues. The register's existing
conventions remain authoritative; this workflow does not create a parallel task,
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
assuming automatic handoff. Assess risk from the issue's actual contract,
impact, uncertainty, affected scope, reversibility, and applicable evidence;
do not infer risk from formal priority or change size alone. Reassess the
verification and Skill choices when implementation or test results expose a
materially different risk. Follow `docs/common/ai-assisted-development.md`
§17.5 without adding a risk score or parallel issue ledger.

Before implementing a blocked or decision-dependent issue, verify its blocker
and any related DEC against the current issue register, requirements, ADRs,
implementation, and evidence. Plan may identify a decision or suggest
`develop unblock`, but remains read-only. Single/Batch may use
`develop unblock` when relevant and authorized; do not make Decision
Resolution a required phase for ordinary issues. A resolved DEC does not
complete or automatically unblock an issue.

## Completion contract

Implementation alone does not complete an issue. Distinguish implementation,
tests added, tests run, tests passed, acceptance conditions met, and review or
other required confirmation. Update the existing issue register only in Single
or Batch mode and only with evidence supported by the work. Preserve IDs,
history, evaluation axes, weights, and status meanings. Do not change a
completion score for routine work; reassess only materially affected existing
axes when evidence warrants it.

Include relevant warnings in verification and completion evidence. Normally
resolve warnings introduced by the issue's changes in the same work unit; for
related pre-existing warnings, use impact and safe fix cost to decide whether
to address them. Record only important unresolved warnings in an existing
issue row or a justified new issue after checking for duplicates and confirming
register edits are authorized. Do not create one issue per warning, broaden the
issue scope to unrelated cleanup, or mark work complete before required warning
remediation and verification are satisfied. Follow
`docs/common/ai-assisted-development.md` §10.5.

Lead with the completed outcome and any blocker, failure, approval need, or
important unverified condition. Include issue IDs, relevant changes, checks and
results, and authorized issue-state updates. Mention a reasonable next issue
only when useful. Keep routine success reports concise; do not repeat command
logs or narrate internal workflow selection. Never describe static checks as
real-agent evaluation. Follow the user's requested work boundary and the
repository's own commit instructions.

## Related internal workflows

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

## Optional development handoff

For material multi-session or incomplete work, consider the target's existing
handoff document at meaningful checkpoints. The issue register remains the
only source of issue state, dependencies, acceptance, and issue-level evidence;
do not duplicate its rows, history, risks, or quality assessment. Plan mode is
read-only and must not edit a handoff. Single/Batch may update an authorized
handoff when needed, but do not generate one in every target or create multiple
handoff files. See the shared AI-assisted development guide's Evidence-Grounded
Development Handoff section for resume freshness, concurrency, and authority
contracts. Place a newly created handoff beside the target's authoritative
issue register; do not impose a fixed target path or duplicate an existing
equivalent handoff elsewhere.

## DevConcord References

Use `devconcord manage reference` when available, identify this workflow as the
requester, and retrieve the required issue-tracking rules. If the Reference workflow cannot be selected,
run the configured source checkout's CLI directly. For
Project Scope, pass `--scope project --target <target-repository>` as well.

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/work-management/issue-tracking.md \
  --revision installed
```

The issue-register template and AI-assisted development guide are optional
references when the target needs them. Read only the needed path, one CLI
invocation per path. Do not silently switch revisions or claim unread content
was applied. If a required reference cannot be read, stop; if it is optional,
report the failure and continue only if the work remains self-contained.
