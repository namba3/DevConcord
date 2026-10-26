# Issue-Driven Development Workflow

This internal workflow reference is distributed inside the public `devconcord` package.
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
3. Locate the authoritative issue register. For a single register, read it
   directly. For a federated register, start from its main index, follow the
   subregister links, and read the relevant canonical issue record and its
   lifecycle, priority, evidence, and completion conventions. A main index
   points to task records; it does not duplicate their status or history. If
   the index is missing, links conflict, or multiple unindexed authorities
   remain, do not create another register; report the ambiguity and use only
   an explicitly authoritative source.
4. Inspect relevant requirements, acceptance criteria, ADRs, architecture,
   implementation, tests, CI, and operational constraints. Verify issue status
   against current evidence and preserve confirmed facts separately from
   assumptions or missing information.
5. For a blocked or materially decision-dependent issue, verify the reported
   blocker and existing DEC/ADR/requirement. If a distinct judgment prevents
   safe progress, consider the optional Decision Resolution workflow. Do not
   edit records in Plan or create duplicate DEC entries.

If the required issue register or its rules cannot be found, stop before
changing issue state. Do not manufacture IDs, statuses, requirements, or a
project-specific Definition of Done.

## 2. Choose work with evidence

For a feature request, enhancement, or idea, first search the authoritative
registers and related requirements, DEC, ADR, and risk records for duplicates
or an existing resolution. Record a proposal as an ordinary `ISS-####` only
when continued tracking has value and register edits are authorized; do not
register every idea. Proposal disposition (`未判断` / `採用` / `保留` /
`不採用`) is optional issue detail and must remain distinct from the issue's
work state. A lightweight idea may need only a summary and expected value;
explore or compare options only when that evidence can affect the decision.
Adoption does not grant implementation authority. When authorized and useful,
create a separate implementation issue linked to the proposal and preserve
the disposition and rationale. Keep routine disposition in the proposal record;
use DEC, ADR, or the risk record only for their distinct responsibilities.
Unadopted proposals alone do not lower completion assessment. See the shared
issue-tracking guide §4.14.

Issues may call for design, research, documentation, organization, testing,
refactoring, implementation, or a combination. Select evidence and deliverables
from the actual acceptance conditions; a code change is not a default
requirement. Do not sort by priority label alone and do not use a numeric score as an
automatic selector. For each candidate, consider:

- stated impact and urgency;
- blockers and real dependency order;
- shared causes or components that allow a coherent change;
- user and quality value;
- work and regression risk;
- ability to verify acceptance conditions;
- locality and reviewability;
- downstream work that becomes possible.

Explain material tradeoffs. Keep work order distinct from the
issue's formal priority. Do not alter priority merely to simplify execution.
An unresolved blocker prevents implementation unless the issue explicitly
allows a safe independent slice. Recheck whether a reported issue is already
fixed, duplicated, obsolete, or underspecified before acting; preserve its ID
and record the evidence rather than silently deleting or rewriting its history.
If a DEC has been resolved, re-evaluate this issue's remaining blockers,
prerequisites, approvals, acceptance conditions, and safe readiness. Do not
infer readiness or completion from the DEC state alone.

Assess actual issue risk separately from priority and change size. Consider
impact, likelihood, uncertainty, affected scope, reversibility, and whether
existing evidence applies; include data integrity, security, compatibility,
availability, or operational consequences when relevant. Unknown impact is
not low risk, and a severe or irreversible outcome must not be averaged away.
Select only specialist expertise and verification that can change the
decision or detect a material failure.

Use the existing single or federated issue register as the only
issue/dependency source. Follow declared prerequisite links and verify their
current state against the repository; identify missing references, cycles,
and blockers before ordering work. When useful and available, optional tags
can narrow discovery across the indexed subregisters; multi-tag filtering
matches records containing every requested tag after case normalization.
Read the canonical issue row to verify its status and readiness. Tags do not
replace priority, dependencies, risk, authorization, or acceptance
conditions. Do not infer a dependency from a shared file alone. When a formal
high-priority issue depends on a lower-priority prerequisite, carry out the
prerequisite first if needed and actionable without changing either issue's
priority. Prefer work that clears a real blocker or creates a reviewable,
verifiable slice, but explain tradeoffs among urgency, user value, risk,
verification cost, locality, and uncertainty. Do not manufacture a numeric
ranking or estimate unsupported by the register or evidence.

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
2. Derive the smallest work slice and deliverables that can satisfy the issue's
   acceptance conditions. Check relevant contracts and impact on persistence,
   UX, performance, robustness, replaceability, security, and documentation as
   applicable. Do not duplicate specialist Skills' detailed workflows.
3. Add or update focused verification from requirements and contracts. Apply
   TDD when practical and useful; do not force ceremony on every change.
4. Perform only the authorized issue scope. Avoid unrelated cleanup and
   speculative requirements. Preserve UI requirements and design assets when
   a change affects them; follow the target's UI design guidance.
5. Run proportionate targeted checks and required regressions. Record each
   check as not run, failed, or passed. Investigate failures and distinguish
   existing failures from regressions where evidence allows.
6. When the work affects code, builds, or static analysis, inspect relevant
   compiler, linter, and static-analysis warnings. Treat
   warnings introduced by this issue's changes as same-unit remediation
   candidates by default. Consider related existing warnings when a safe,
   proportionate fix fits the issue. Use a comparable baseline before labeling
   warnings new or pre-existing; otherwise record that classification as
   unknown. Do not weaken checks or expand the issue into unrelated cleanup.
   For material unresolved warnings, use the existing issue register only if
   authorized and warranted, after checking for duplicates; do not create a
   warning ledger or one issue per warning.
7. Review changed artifacts against the issue, acceptance conditions, target review
   criteria, and unrelated-change protection. Update only relevant existing
   documentation and the existing issue row/history.
8. Set the issue to its local lifecycle state that matches the evidence. Use
   `完了` only when all required acceptance conditions and verification/review
   obligations are met. Otherwise retain or set the accurate state (`進行中`,
   `レビュー待ち`, or `ブロック`, according to local rules) and record why.

When a failure has an unclear cause, separate observations from hypotheses
and prefer a discriminating reproduction/check before repair. This is
proportionate reasoning, not a separate issue ledger or a requirement to
invoke Root Cause Analysis. Keep evidence fresh against the final relevant diff.
If implementation or verification reveals a materially different contract,
affected scope, failure impact, or invalidated oracle, pause dependent work and
reassess the selected workflows and checks. Do not alter priority, invent a risk
score, or expand the authorized scope.

## 5. Batch Mode — bounded multi-issue work

1. Honor the user's explicit issue range, time/effort limit, exclusions, and
   stopping condition. If the requested boundary is not specified, choose a
   small coherent slice and state it before making changes.
2. Select only actionable issues whose prerequisites are met. Order by actual
   dependencies and coherent shared causes, considering value, risk, and
   verification. Do not start blocked issues unconditionally.
3. Batch may include different work types when the user authorized the bounded
   set and each issue can be evaluated independently. Order work by actual
   dependencies and preserve separable deliverables/evidence. A shared cause,
   dependency, or coordinated change may justify grouping; same-file location
   alone does not. Before combining, verify that the user authorized the
   combined scope, each issue still has an independently checkable completion
   condition, and failure can be isolated and reviewed.
4. Keep each issue's implementation and evidence separable where possible.
   Verify and review each deliverable with applicable checks—including warning
   output where code/build analysis applies and
   unresolved-warning disposition under §4's same-unit remediation contract—
   before expanding the scope. Stop when the user's boundary is reached, a
   blocker occurs, unrelated concurrent changes appear, or remaining work
   would exceed the authorized scope.
5. Evaluate each issue independently. One successful change does not complete
   dependent or neighboring issues. Update the existing register with the
   result and evidence for each addressed issue; preserve other rows and IDs.

If a batch step fails, stop before moving to dependent work. Preserve completed
and partial changes within the authorized scope, identify which issue
acceptance conditions are met or unmet, rerun checks that may have become
stale after later edits, and report the safe recovery point. Do not mark
neighboring issues complete because a shared component changed.

Batch is not open-ended autonomous execution. Report partial completion and
the reason for stopping.

## 6. Issue records, quality assessment, and new findings

- Preserve existing issue IDs, priority conventions, lifecycle states, and
  history. Never recycle an ID or silently remove an issue.
- Treat `ISS-####` as a project-wide sequential identifier across all
  subregisters. The main register is the sole allocation counter for a
  federated setup. Before creating a new issue, check the indexed registers
  for duplicates and an unused number; if the allocation history or a
  concurrent allocation is uncertain, stop and reconcile before assigning an
  ID. Do not change an ID when tags or register location change.
- Work type, quality classification, register location, optional tags,
  priority, and state are separate attributes. Existing untagged records stay
  valid; do not bulk-tag them. Tags do not affect issue state, priority, or
  the ten-axis completion assessment.
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
- Do not mark an issue complete because an artifact or test exists. Record
  applicable checks as designed, added, run, and passed, and whether acceptance
  and review obligations were met. Unrun checks and residual risks remain explicit.
- For material deliverable evidence, record the target commit or worktree
  state and relevant environment/command/result in the existing register or
  point to an existing CI/test/review record. Do not paste long logs into the
  issue. If the code, configuration, fixture, or environment changed after a
  check, decide whether that evidence still covers the final state and rerun
  affected checks when needed.
- Keep warning-related issue records proportional to impact and authorization.
  Avoid duplicates and do not use warning count as an issue or quality score.

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

- addressed issue IDs and deliverable summary;
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

## Optional handoff checkpoints

An existing handoff may help when a Single or Batch spans sessions or stops
with material work or verification incomplete. Plan mode may read it and report
staleness, but never modify it. At an authorized checkpoint, keep only the
current execution context and point to the issue register; do not copy issue
states, the Batch list, or a TODO backlog. On completion, update the issue
register under its own rules and trim an obsolete snapshot only when authorized.
Before editing, recheck the current handoff and Git state to protect concurrent
changes. Absence of a handoff does not block this workflow.
