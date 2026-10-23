# Issue-Driven Development Workflow

This reference is distributed with `devconcord-issue-driven-development`.
Apply the target repository's actual issue lifecycle, Definition of Done,
verification commands, and scope rules. DevConcord's issue-tracking guide is
the canonical shared reference, but target-specific rules and user direction
remain in force when compatible.

## 1. Establish a safe baseline

1. Confirm the target repository and read its `AGENTS.md`, `REVIEW.md`, and
   other applicable instructions. For review work, apply `REVIEW.md` first.
2. Record the initial HEAD, branch, staged/unstaged/untracked changes, and
   relevant worktree state. Do not overwrite, stage, or attribute unrelated
   changes to this task. If concurrent edits appear, stop before touching the
   affected paths and report them.
3. Locate the existing issue register and read its lifecycle, priority,
   evidence, and completion conventions. If multiple candidate registers or
   conflicting sources of truth exist, do not create another; report the
   ambiguity and use only an explicitly authoritative source.
4. Inspect relevant requirements, acceptance criteria, ADRs, architecture,
   implementation, tests, CI, and operational constraints. Verify issue status
   against current evidence and preserve confirmed facts separately from
   assumptions or missing information.

If the required issue register or its rules cannot be found, stop before
changing issue state. Do not manufacture IDs, statuses, requirements, or a
project-specific Definition of Done.

## 2. Choose work with evidence

Do not sort by priority label alone and do not use a numeric score as an
automatic selector. For each candidate, consider:

- stated impact and urgency;
- blockers and real dependency order;
- shared causes or components that allow a coherent change;
- user and quality value;
- implementation and regression risk;
- ability to verify acceptance conditions;
- locality and reviewability;
- downstream work that becomes possible.

Explain material tradeoffs. Keep implementation order distinct from the
issue's formal priority. Do not alter priority merely to simplify execution.
An unresolved blocker prevents implementation unless the issue explicitly
allows a safe independent slice. Recheck whether a reported issue is already
fixed, duplicated, obsolete, or underspecified before acting; preserve its ID
and record the evidence rather than silently deleting or rewriting its history.

## 3. Plan Mode — read-only

Use Plan when the request asks what to do next, asks for an assessment, or does
not authorize implementation clearly enough. Verify candidate IDs, states,
dependencies, blockers, current implementation, and verification gaps. Propose
a feasible order and bounded work units with reasons and acceptance evidence.
Do not edit source, configuration, documentation, issue records, or scores. A
plan in chat is not a register update and is not completed work.

## 4. Single Mode — one specified issue

1. Confirm the specified issue exists, is actionable, and is not blocked by an
   unmet dependency. Do not invent a missing issue ID or scope. If missing
   context materially affects safe implementation, stop and report it.
2. Derive the smallest implementation slice that can satisfy the issue's
   acceptance conditions. Check relevant contracts and impact on persistence,
   UX, performance, robustness, replaceability, security, and documentation as
   applicable. Do not duplicate specialist Skills' detailed workflows.
3. Add or update focused verification from requirements and contracts. Apply
   TDD when practical and useful; do not force ceremony on every change.
4. Implement only the authorized issue scope. Avoid unrelated cleanup and
   speculative requirements. Preserve UI requirements and design assets when
   a change affects them; follow the target's UI design guidance.
5. Run proportionate targeted checks and required regressions. Record each
   check as not run, failed, or passed. Investigate failures and distinguish
   existing failures from regressions where evidence allows.
6. Review the diff against the issue, acceptance conditions, target review
   criteria, and unrelated-change protection. Update only relevant existing
   documentation and the existing issue row/history.
7. Set the issue to its local lifecycle state that matches the evidence. Use
   `完了` only when all required acceptance conditions and verification/review
   obligations are met. Otherwise retain or set the accurate state (`進行中`,
   `レビュー待ち`, or `ブロック`, according to local rules) and record why.

## 5. Batch Mode — bounded multi-issue work

1. Honor the user's explicit issue range, time/effort limit, exclusions, and
   stopping condition. If the requested boundary is not specified, choose a
   small coherent slice and state it before making changes.
2. Select only actionable issues whose prerequisites are met. Order by actual
   dependencies and coherent shared causes, considering value, risk, and
   verification. Do not start blocked issues unconditionally.
3. Keep each issue's implementation and evidence separable where possible.
   Verify and review each change before expanding the scope. Stop when the
   user's boundary is reached, a blocker occurs, unrelated concurrent changes
   appear, or remaining work would exceed the authorized scope.
4. Evaluate each issue independently. One successful change does not complete
   dependent or neighboring issues. Update the existing register with the
   result and evidence for each addressed issue; preserve other rows and IDs.

Batch is not open-ended autonomous execution. Report partial completion and
the reason for stopping.

## 6. Issue records, quality assessment, and new findings

- Preserve existing issue IDs, priority conventions, lifecycle states, and
  history. Never recycle an ID or silently remove an issue.
- Add a newly discovered defect only after checking for duplicates and only
  when the task permits register edits. State observed impact, reproducible
  evidence, and verifiable completion conditions; do not record speculation as
  a confirmed defect.
- Keep known defects in the existing issue register and future uncertainties
  in the existing risk record. Do not add a TODO, implementation-progress,
  quality, or Skill-recommendation ledger.
- Preserve the existing ten completion axes, their weights, SDS separation,
  and meanings of `未評価` and `N/A`. Do not adjust the score to reward fewer
  open issues. Reassess only existing axes materially affected by significant
  evidence; explain the distinct impact and avoid double counting.
- Do not mark an issue complete because code or a test exists. Record whether
  tests were added, run, passed, and whether acceptance and review obligations
  were met. Unrun tests and residual risks remain explicit.

## 7. Scope and safety boundaries

- Plan is read-only. Single and Batch are limited to user-authorized work.
- Do not install Skills, assume an automatic Skill handoff, or claim Skill
  availability outside the checked User/Project Scope.
- Do not commit, push, reset, rebase, or otherwise rewrite Git history unless
  the user explicitly requests that operation. Do not infer such permission
  from issue completion.
- Do not edit external repositories or paths outside the target's authorized
  scope. Do not introduce breaking behavior, destructive changes, or major
  design decisions without authority and sufficient evidence.
- Stop safely when required information, dependency decisions, or verification
  capability is missing. State the blocker, verified progress, and next action.

## 8. Completion report

For Single or Batch, report:

- addressed issue IDs and implementation summary;
- changed files;
- checks run and their results, including checks not run;
- issue-register state/evidence updates;
- incomplete issues, blockers, and residual risks;
- material new findings;
- a reasonable next issue, only when evidence supports one.

For Plan, report proposed issue IDs, dependencies, rationale, bounded work
units, acceptance/verification conditions, unknowns, and explicitly confirm
that no files or issue records were changed. Static tests, fixture checks,
remote CI, native/device behavior, and actual agent execution are distinct
evidence categories; report only what was observed.
