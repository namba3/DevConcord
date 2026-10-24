---
name: devconcord-implementation-planning
description: >
  Turn an existing feature or change request into small, ordered, verifiable
  implementation increments connected to requirements, design decisions, and
  existing project work tracking.
---

# Implementation Planning

Create an actionable plan for an existing project's requested change. The
default output is a plan only: do not edit code, settings, requirements, ADRs,
or issue records unless the user explicitly includes those changes.

## Workflow

1. Confirm the requested outcome, users or callers, scope, constraints, and
   what is explicitly excluded. Inspect the target's HEAD, working tree, and
   repository instructions before relying on existing state.
2. Read relevant requirements and acceptance conditions, ADRs, existing issue
   register entries, architecture and code, tests, CI, and operational
   constraints. Keep each document's existing identifiers and source of truth.
3. Analyze only material change impacts: affected responsibilities and
   boundaries, public contracts and compatibility, persistent data and
   migrations, state/error behavior, dependencies, security, resource use,
   platform behavior, documentation, and operations as relevant. Use an
   available Change Impact Assessment or design Skill as an optional input
   when it adds value; do not assume automatic Skill handoff.
4. Resolve or expose design decisions that block safe sequencing. Separate
   confirmed facts, assumptions, candidate decisions, and questions. Do not
   turn an AI guess into a requirement or silently select among consequential
   alternatives.
5. Identify acceptance conditions and the verification evidence each change
   needs. Where verification itself is unclear or substantial, recommend
   `devconcord-test-design` as an optional focused follow-up; do not duplicate
   its test-case design.
6. Split work into small increments organized around responsibilities,
   contracts, or user-visible behavior. For each increment, state its outcome,
   affected area, prerequisites, acceptance/verification conditions, and
   integration or review needs. A file list may supplement this structure but
   is not a plan by itself.
7. Order increments by actual dependencies and risk. Keep independent work
   parallelizable; identify migration, compatibility, rollout, or recovery
   gates where they affect sequence. Do not add artificial phases or process
   steps.
8. Connect work to existing REQ / NFR / ADR / ISSUE identifiers. Suggest
   changes to existing issue entries only when needed and requested. Do not
   create a separate implementation-task ledger or fixed WIP system.
9. Report assumptions, blockers, residual risks, deferred scope, and
   verification that remains unrun. A plan is not implementation, test
   execution, or evidence of requirement fulfillment.

## Reassess an invalidated plan

During authorized execution, pause dependent units when evidence changes a
planning assumption: a dependency or blocker appears, a consequential design
decision is needed, a planned unit has no usable oracle/environment, or actual
scope/cost materially differs. Reconfirm constraints and dependencies,
preserve completed evidence, split/reorder/defer/remove affected units, and
state the next decision point. Do not disguise a design change as replanning or
weaken acceptance conditions to fit the plan. This Skill plans; it does not
implement or gain execution authority.

## Plan quality

A useful increment can be reviewed and verified on its own where dependencies
allow. Include enough detail to show the design intent and completion
condition, without prescribing speculative file edits or splitting work into
trivial tasks. Distinguish the breadth of a change from the number of files or
lines. Do not serialize unrelated work or put a long list of generated code
into one undifferentiated step.

Use the existing issue register as the project work authority. A plan returned
in chat or saved to a requested existing location is not automatically an
issue-register update. Preserve its IDs, statuses, and conventions; do not
create task, risk, or score tracking alongside it.

Size and order increments by semantic boundaries and material risk, not file
count. For high-impact or hard-to-reverse outcomes, split where a meaningful
contract and independent verification remain coherent; do not fragment work
when that obscures atomicity or correctness. Reassess the plan when evidence
changes impact, uncertainty, affected scope, verification oracle, or risk.
Follow `docs/common/ai-assisted-development.md` §17.5 without adding fixed
risk scoring or a parallel ledger.

## Boundaries

- Bootstrap establishes a new repository foundation; this Skill plans changes
  in an existing project. Adoption and Sync manage shared guidance, not
  feature implementation plans.
- Repository Review assesses proposed change impact or reports concrete
  findings. It can provide evidence for this plan, but does not replace
  sequencing and increment design.
- Test Design specifies independent expected outcomes and verification cases;
  this Skill connects those conditions to implementation increments without
  duplicating the test strategy.
- Specialized Design Skills define important UX, performance, robustness,
  security, replaceability, or documentation decisions. Recommend one only
  when the unresolved question warrants it. Do not treat planning as a
  substitute for that decision or execute/install Skills automatically.

## Deliverable

For the requested scope, state the target requirements or behavior, current
evidence inspected, key decisions and assumptions, affected contracts and
areas, ordered increments and real dependencies, acceptance and verification
conditions per increment, related REQ / NFR / ADR / ISSUE IDs, deferred work,
and open risks. Use the target's existing planning format when one is
established; otherwise provide a concise plan without creating a new project
document by default.

## DevConcord References

Use `devconcord-reference` when available. Identify this Skill as the requester
and retrieve only needed paths, such as:

- `docs/application-design/templates/requirements.md`
- `docs/application-design/templates/adr.md`
- `docs/work-management/issue-tracking.md`
- `docs/common/ai-assisted-development.md`

If the common Skill cannot be selected, use the configured source checkout's
CLI directly, one reference path per invocation:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-implementation-planning \
  --path docs/work-management/issue-tracking.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue only when the plan remains self-contained.

## Completion

Report the plan's target and scope, evidence inspected, assumptions and
decisions, increments and dependencies, verification conditions, linked
identifiers, blockers and deferred work. State clearly that planned work and
verification are not completed work.
