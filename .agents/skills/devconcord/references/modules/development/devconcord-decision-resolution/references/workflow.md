# Decision Resolution & Unblocking Workflow

Apply this workflow only when requested or when a material unresolved decision
or blocker is evidenced. Use target-specific records, permissions, and
verification conventions. The commands in `module.md` select procedures; they
do not expand authority.

## 1. Establish the current record set

Inspect instructions, branch/HEAD/index/worktree, the authoritative issue
register, relevant requirements/design, ADRs, risk record, HANDOFF if present,
implementation, tests, and environment. Preserve unrelated edits. Treat
handoff and prior reports as leads and revalidate them.

Before creating a DEC, search for the same question or answer in the issue
register, canonical decisions source, requirements, ADRs, and current code.
Check whether the concern is already an Issue/task, future Risk, actual failure
for Root Cause Analysis, or stale documentation. Reuse or link the existing
canonical record when sufficient. Do not invent IDs or silently migrate
history. New DEC IDs use the target's convention, preferably `DEC-####`, and
must remain distinct from `ISS-####` and ADR IDs.

## 2. Discover and classify

For each evidenced concern, classify it as one of:

- **Blocker:** a concrete condition that currently prevents safe/correct work.
- **Open Decision:** a judgment that must be settled for a decision-dependent
  design, implementation, or operation to proceed.
- **Issue/task:** work such as prerequisite implementation, investigation,
  repair, or verification; track it in the issue register.
- **Risk:** a possible future event and impact; track it in the existing risk
  record.
- **Unknown/evidence gap:** insufficient information; do not present it as a
  confirmed blocker or decision until framed and linked to an owner/action.

A blocker can exist without a DEC, and a DEC can affect multiple issues without
being the only blocker. Record evidence for shared causes and uncertain
dependencies; do not infer a relationship from issue count or proximity.

## 3. Frame the decision

For a material DEC, state the question, why and when it matters, consequence of
delay, related issue IDs, mandatory requirements/constraints, decision
authority, evidence needed, and review deadline/trigger if one exists. Separate
facts, assumptions, hypotheses, and unknowns. Do not convert ambiguity into an
unstated requirement. Use the issue register's Open Decisions section as the
default canonical source. If scale warrants a separate file, obtain authority,
select exactly one canonical DEC source, and leave references in the register.

## 4. Investigate with discriminating evidence

Ask what evidence could change the choice. Select the least costly reliable
method that can obtain it: inspect code/config/tests/requirements/ADRs, consult
official specifications, reproduce a failure, design a test, run an authorized
prototype or benchmark, or check compatibility/security/recovery as relevant.
Use only attributes that can affect this decision. State environment,
conditions, commands, observations, and limitations; distinguish measured from
estimated, passing from not run, and fact from hypothesis.

Do not edit source or settings, run side-effectful experiments, access external
systems, or update records on an investigation-only request unless separately
authorized. Stop or escalate if the required experiment exceeds authority,
environment, or budget. Stop gathering evidence when it no longer changes the
choice, costs exceed likely value, approval is the only remaining step, or
required evidence is unavailable.

## 5. Challenge and compare

Compare only realistic candidates against hard requirements and relevant
constraints. Include implementation/operational/migration costs, reversibility,
residual risk, and relevant UX, performance, robustness, replaceability, or
security effects. State the strongest counterargument to the leading option,
what could falsify it, and how failure or recovery would work. Do not use
unsupported numeric scores, majority vote, or one-sided evidence.

## 6. Recommend, resolve, or escalate

Provide the decision question, context and related issues, feasible options,
verified evidence, comparison and counterargument, recommendation and rationale,
uncertainty/evidence limits, authority required, consequences/work, and
resolution conditions. For simple matters this may be a concise issue-register
entry; a Decision Packet is optional and is not a second canonical record.

If clearly within delegated authority and consistent with approved contracts,
record the decision in the canonical source. For material design decisions,
create/update the ADR as authorized and link the DEC; do not copy ADR rationale
into a second durable source. If approval is required, set `承認待ち` and
present concrete choices and consequences. If deferred, set `保留` with reason,
safe work, authority, and reconsideration trigger. Do not call either outcome
resolved. Resolution requires the answer, evidence or explicit authorized
approval, scope, canonical follow-through, and visible remaining conditions.

## 7. Propagate and reassess readiness

After resolution, update only authorized canonical artifacts and references.
For each affected issue, independently check that this DEC was its actual
blocker, other blockers/prerequisites/approvals remain or are cleared,
acceptance conditions are unchanged, and safe work can resume. Do not
automatically change issue status, priority, completion, or quality axes. DEC
resolution alone never completes an issue.

Classify the blocker-resolution outcome separately from issue/DEC lifecycle:

- **Resolved:** the blocking cause was removed and evidence confirms it.
- **Bypassed Safely:** the cause remains, but a bounded independent work unit
  can proceed without violating contracts; retain the blocker for dependent
  work.
- **Escalated:** authority or evidence is unavailable; identify the decision
  maker, options, evidence, and safe stop/independent work.

When multiple issues share a DEC, reassess each by impact, real dependency,
urgency, decision/research cost, reversibility, residual risk, available
independent work, and evidence confidence. Issue count alone does not rank it.
Update the issue register only with authorization. Update HANDOFF only at an
authorized meaningful checkpoint, keeping DEC IDs and resume context rather
than duplicating decision details or status.

## 8. Bounded collaboration and reporting

Parallelize only genuinely independent research when the environment supports
it, each task has a bounded question and deliverable, and it will not create
shared-worktree conflicts. Reconcile assumptions and contradictory evidence;
do not decide by vote. Otherwise run the same analyses sequentially.

Stop at the user's scope/budget, unsafe evidence, unresolved approval, or low
expected value. Report classifications, canonical records/references touched,
evidence and limits, recommendation/resolution/escalation, issue-readiness
changes supported by evidence, checks run/not run, residual uncertainty, and
safe next action. Do not claim actual agent quality from static tests.
