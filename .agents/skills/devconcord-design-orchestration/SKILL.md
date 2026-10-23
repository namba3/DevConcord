---
name: devconcord-design-orchestration
description: >
  Orchestrate user-delegated design exploration, progressive specification,
  architecture improvement, cross-cutting tradeoffs, and consistency across
  requirements, decisions, design artifacts, and verification. Use for bounded
  design evolution across connected areas; use specialist review, gap-analysis,
  planning, or implementation Skills for their distinct tasks.
---

# Design Orchestration

This Skill helps an agent develop or improve a project's design within the
user's delegated scope. Its formal design concept is **Autonomous &
Evolutionary Design**: make useful, evidence-based progress in bounded steps,
preserve approved contracts, and escalate decisions that exceed delegated
authority. Optimize for user value, requirement fit, consistency,
verifiability, changeability, implementability, and proportionate complexity;
do not optimize document volume or number of changes.

## When to use

- Use when design work spans related requirements, architecture, decisions, or
  design assets; when a design needs progressive specification; or when the
  user delegates bounded improvement and reassessment of existing design.
- Use `devconcord-gap-analysis` for a read-only, cross-cutting assessment of
  alignment, evidence gaps, and improvement priorities. Use
  `devconcord-repository-review` for concrete defects or change impact,
  `devconcord-implementation-planning` for implementation increments,
  `devconcord-issue-driven-development` for authorized issue execution, and
  specialist design Skills for a focused quality-attribute decision.
- Do not use this Skill to bootstrap a new repository foundation when
  `devconcord-bootstrap-from-design` is the requested workflow, or to replace
  a focused design, review, planning, or implementation task.

## Modes

- **Explore:** read-only analysis and proposals. Do not edit project files,
  requirements, ADRs, issue/risk records, or other artifacts.
- **Design:** develop new or incomplete design from established goals,
  requirements, and constraints. Update only authorized design artifacts;
  this mode does not authorize implementation.
- **Evolve:** assess and improve existing design against approved intent,
  implementation evidence, and current constraints. Update only authorized
  artifacts; preserve valid designs when no material improvement is supported.

Choose the mode from the user's request. If permission to modify artifacts or
the target scope is unclear, use Explore. Design/Evolve do not authorize
implementation code changes, work outside the stated artifact scope,
external-system operations, commits, or pushes. Major requirement changes
still need explicit approval.

## Workflow

Follow the bounded evolution loop in [`references/workflow.md`](references/workflow.md).
Select only the design areas that matter to the task's users, scope, risks, and
constraints. Do not require every principle, specialist Skill, artifact, or
quality attribute for every change. Do not assume that one Skill can invoke
another automatically.

## Authority and completion

Keep approved requirements, accepted ADRs, verified implementation facts,
assumptions, proposals, and unknowns distinct. Resolve details that follow
clearly from approved contracts; label evidence-dependent proposals as
hypotheses; seek explicit approval before changing major user-visible
behavior, breaking data/API compatibility, weakening security guarantees,
reversing product direction, or choosing large migrations or new ongoing
external costs. Continue safe, independent work within scope while such a
decision is pending.

Finish when the delegated slice is consistent and verifiable, no material
in-scope improvement remains, a blocker or approval boundary is reached, or
the user-defined limit is met. Report changed artifacts, decisions and their
basis, acceptance/verification conditions, unresolved matters, and checks
actually performed. Do not treat a design proposal as implementation or
verification evidence.

## DevConcord References

Use `devconcord-reference` when available. Request only the needed canonical
paths, identify this Skill as the requester, and use the installed revision.
Common sources include:

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`
- `docs/application-design/templates/adr.md`
- `docs/work-management/issue-tracking.md`
- `docs/work-management/risk-management.md`
- `docs/application-design/ui-ux-guide.md` when UI behavior or design assets
  are relevant
- `docs/common/documentation-design.md` when source-of-truth or document
  structure decisions are relevant

If the common Skill cannot be selected, use the configured source checkout's
CLI for each needed path:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-design-orchestration \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop decisions that depend on it; if it is optional,
report the failure and continue only independent work whose basis is available.
If source identity or the recorded revision cannot be verified, stop that
reference operation and report the limitation.
