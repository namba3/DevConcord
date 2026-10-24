# Design Orchestration Workflow

This internal workflow reference is distributed inside the public `devconcord` package. Apply
the target project's actual requirements, decision records, document
ownership, approval rules, and work tracking. Preserve their identifiers and
history; do not impose DevConcord's file layout on the target.

## 1. Establish scope and a safe baseline

1. Confirm the target, user-requested outcome, mode, allowed artifacts,
   exclusions, and any size or stopping boundary. Design scope is not
   implementation scope.
2. Read repository instructions, its review criteria for review work, purpose
   and entry points, and current HEAD/index/worktree. Preserve local and
   concurrent work. Do not edit an affected path with conflicting concurrent
   changes.
3. Locate canonical requirements, architecture/design documents, ADRs,
   existing issue and risk registers, UI assets where relevant, and the
   implementation/tests needed to understand design consequences. If source
   ownership or precedence is unclear, record the conflict; do not invent a
   new source of truth.
4. Distinguish approved requirements and accepted decisions, observed
   implementation/test facts, proposals or hypotheses, unknowns, and
   conflicting evidence. An implementation's current behavior is not by
   itself approval to change the design.

If scope or artifact-edit permission is unclear, remain in read-only Explore.
If a required source is unavailable, do not make a decision that depends on
it; proceed only with independent work supported by available evidence.

## 2. Select the mode and work unit

- **Explore:** assess and propose without modifying files, including tracking
  records. Use existing gap-analysis or review evidence where useful instead
  of repeating a broad assessment. Focus on the next consequential design
  decision and its evidence, dependencies, and approval needs.
- **Design:** derive a coherent design slice from approved goals,
  requirements, and constraints. Identify missing user, functional, quality,
  state, interface, or operational contracts only where relevant.
- **Evolve:** compare current design and implementation with approved intent.
  Separate implementation defects, stale or incomplete design assets,
  unresolved requirement conflicts, and justified improvements. Consider
  retaining the current design as a valid outcome.

For broad delegation, choose one small, coherent design unit using user value,
impact, dependencies, blocking decisions, compatibility, risk, evidence
readiness, rework avoided, and implementation cost. Keep formal issue priority
separate from design-work order. Do not create a numeric ranking unless the
target already requires one.

Assess only risk dimensions that could change the design decision: impact,
likelihood, uncertainty, affected scope, reversibility, and confidence that
available evidence applies. Include data integrity, security, compatibility,
availability, user impact, workload, operations, or deployment conditions
when material. Do not average away a severe or irreversible outcome, treat
unknown scope as low risk, or use an unsupported numeric score. Reuse the
conditional Skill candidates in the canonical guidance §17.5; select only
specialist analysis that adds decision value beyond existing evidence.

## 3. Find and frame design decisions

For each material gap or improvement, identify the evidence, affected user or
system behavior, existing contract, dependencies, and consequences. Classify
it as a documentation omission, unresolved requirement, design defect,
implementation defect, or unverified claim; do not turn uncertainty into a
confirmed defect. Check for duplicates in existing requirements, ADRs, issues,
and risk records before proposing updates.

Prioritize decisions that unblock dependent design or implementation and
reduce meaningful user, compatibility, security, reliability, performance, or
maintenance risk. Evaluate only relevant quality attributes, such as
functional correctness, UX, performance, robustness, security, replaceability,
maintainability, observability, compatibility, testability, or operational
complexity. For consequential
choices, compare the status quo, a minimal improvement, and a structural change
when those alternatives could change the decision. State benefits, costs,
migration or rollout effects, reversibility, and evidence gaps. Do not force
three alternatives for routine decisions, add abstractions without value, or
invent targets unsupported by workload or requirements.

Select focused specialist Skills only when their expertise adds value and
their availability is verified in the applicable User or Project Scope. Keep
their work optional and separate:

| Question or output | Related workflow |
|---|---|
| Cross-cutting alignment, gaps, and evidence coverage | `review gap` (read-only assessment) |
| Concrete code defects or impact of a proposed change | `review repository` |
| A focused UX, performance, robustness, security, replaceability, observability, or documentation decision | The matching `quality` or `design` command |
| Independent expected outcomes and verification strategy | `verify test-design` |
| Ordered, verifiable implementation increments | `develop implementation-plan` |
| Authorized implementation and issue-state/evidence updates | `develop issue` |

Do not imply automatic handoff or substitute a recommendation for evidence of
the related workflow's execution. If the relevant internal module cannot be
selected or read,
use the canonical, version-pinned reference material when it is available and
continue only within the contract it supports. If necessary design criteria
remain unavailable, keep dependent decisions provisional or unassessed and
report the limitation; do not install a Skill or invent its guidance.

Reassess the selected design scope and verification expectations when analysis
reveals a new public consumer, data-loss path, trust boundary, availability or
performance constraint, or material incompatibility. If evidence reduces a
previously material concern, avoid continuing heavyweight analysis without a
remaining decision need. Reassessment never approves a major design change or
increases the user's delegated scope.

## 4. Decide within authority

Classify consequential decisions before editing:

- **May resolve:** a detail clearly entailed by approved requirements or an
  accepted decision; a correction that preserves existing contracts; or a
  bounded, reversible clarification with no material user, data, security, or
  compatibility consequence.
- **Propose as a hypothesis:** multiple viable options depend on unmeasured
  workloads, unconfirmed usage, unavailable evidence, or a benefit that has
  not been demonstrated. Mark the assumptions, validation needed, and any
  dependent design as provisional.
- **Requires explicit approval:** a major user-visible behavior or product
  policy change, breaking API/protocol/data compatibility, weaker security
  guarantees, major architecture migration, irreversible operation, or new
  external dependency/cost. Do not silently resolve or apply it.

When approval is needed, finish safe independent design work and present the
decision, realistic alternatives, consequences, evidence gaps, and affected
artifacts. Do not claim blocked decisions are settled. A provisional design
must not be presented as an approved requirement or a committed
implementation plan.

## 5. Update authorized artifacts

In Design/Evolve, modify only artifacts within the user's delegated scope and
the target's document ownership rules. Prefer updating the existing canonical
requirement, ADR, architecture, interface/state contract, UI asset, or test
strategy. Preserve established IDs, status semantics, approval history, and
links. Do not create duplicate specifications, a design-drift ledger, a new
quality axis, or a separate task/risk register.

Update issue or risk records only when authorized and consistent with their
existing rules: concrete known work belongs in the existing issue register;
future uncertainty belongs in the existing risk record. Do not invent IDs or
reclassify a hypothesis as a known defect. Design/Evolve never implies
permission to change implementation code, tests, build settings, or external
systems. If implementation is needed, state that boundary and connect it to
an existing issue or recommend the appropriate planning/execution Skill.

For UI-affecting design, use the existing UX Skill and UI design guidance to
trace user tasks, requirements, accepted decisions, states, accessibility,
mockups, and implementation meaning. Preserve the existing Current/Stale/
Draft/Deprecated distinctions and do not treat code or a recent timestamp as
the specification. Do not require mockups for non-GUI work or where they add
no value.

## 6. Verify consistency and continue only within bounds

After each design unit, check only relevant relationships:

1. The change follows approved user goals, requirements, constraints, and
   accepted ADRs—or clearly identifies where approval is pending.
2. Related design assets and public/data contracts agree; affected
   compatibility and migration consequences are recorded.
3. Implementation facts and design intent are distinguished, and any gap has
   an appropriate existing work or risk destination if authorized.
4. Acceptance conditions and verification are observable and proportionate;
   distinguish a proposed test strategy from tests present, tests run, and
   results.
5. The change has not introduced unsupported assumptions, unnecessary
   complexity, duplicate tracking, or stale references.

Continue with another coherent unit only when it is within the delegated
scope, materially useful, and does not depend on an unresolved approval or
source-of-truth conflict. Stop when the requested boundary is met, there is
no supported material improvement, required evidence is unavailable, a
blocker or approval boundary is reached, competing work appears, or further
work would exceed the user's delegation. Do not loop until all repository
issues are closed or until a subjective notion of design completeness.

## 7. Report the result

Summarize the selected mode and scope; evidence and sources inspected; design
decisions resolved, proposed, or awaiting approval; artifacts changed; related
existing REQ/NFR/ADR/ISSUE/risk references; acceptance and verification
conditions; checks actually run; and remaining assumptions, limitations, and
risks. Keep the report proportional to the work. State explicitly when
implementation, specialist Skill execution, agent E2E, or target-environment
verification was not performed.
