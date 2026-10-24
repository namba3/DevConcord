# Command and Intent Routing

These are logical instructions interpreted by the agent using this Skill. They are not shell commands, guaranteed native slash commands, or proof that a host discovered or executed a workflow.

## Command map

| Logical command | Primary internal module | Typical result and authority |
|---|---|---|
| `design explore` | `design/devconcord-design-orchestration` | Read-only exploration and bounded options |
| `design create` | `design/devconcord-design-orchestration` plus relevant design specialist | User-authorized design artifacts |
| `design evolve` | `design/devconcord-design-orchestration` | Improve delegated design assets and preserve approved contracts |
| `develop plan` | `development/devconcord-development-orchestration` | Read-only next-work/iteration plan, quality gates, budget, and continue/stop criteria |
| `develop implementation-plan` | `development/devconcord-implementation-planning` | Read-only decomposition of a specified change into ordered, verifiable increments |
| `develop issue` | `development/devconcord-issue-driven-development` | Select and implement bounded existing issue work when authorized |
| `develop batch` | `development/devconcord-issue-driven-development` | Bounded issue batch with dependency and evidence controls |
| `develop iterate` | `development/devconcord-development-orchestration` | Finite implementation, verification, review, and continue/stop cycle |
| `develop stabilize` | `development/devconcord-development-orchestration` | Authorized stabilization without feature expansion |
| `develop unblock` | `development/devconcord-decision-resolution` | Bounded blocker discovery, decision support, safe resolution/bypass, or escalation |
| `decide scan` | `development/devconcord-decision-resolution` | Read-only classification of blockers/open decisions and canonical record checks |
| `decide investigate` | `development/devconcord-decision-resolution` | Decision-changing evidence gathering; experiments need separate authorization |
| `decide compare` | `development/devconcord-decision-resolution` | Evidence-based alternative comparison and counterarguments |
| `decide recommend` | `development/devconcord-decision-resolution` | Decision Packet or concise recommendation; not approval |
| `decide resolve` | `development/devconcord-decision-resolution` | Authorized canonical decision update; does not authorize implementation |
| `review repository` | `verification/devconcord-repository-review` | Evidence-based read-only findings |
| `review impact` | `verification/devconcord-repository-review` | Proposed-change impact assessment |
| `review gap` | `verification/devconcord-gap-analysis` | Read-only cross-cutting assessment and priorities |
| `verify test-design` | `verification/devconcord-test-design` | Independent verification strategy and cases |
| `diagnose root-cause` | `verification/devconcord-root-cause-analysis` | Falsifiable hypotheses, evidence, and safe experiments |
| `quality performance` | `quality/devconcord-design-performance` | Workload-grounded performance requirements/design |
| `quality robustness` | `quality/devconcord-design-robustness` | Failure contracts, invariants, and recovery design |
| `quality security` | `quality/devconcord-design-security` | Risk-scoped assets, threats, controls, and verification |
| `quality replaceability` | `quality/devconcord-design-replaceability` | Value-based dependency boundary decisions |
| `quality observability` | `quality/devconcord-observability-design` | Diagnostic questions and proportionate safe signals |
| `quality ux` | `design/devconcord-ux-functional-design` | User tasks, behavior, state, and acceptance conditions |
| `quality documentation` | `quality/devconcord-documentation-architecture` | Reader-centered structure, source of truth, and navigation |
| `lifecycle compatibility` | `lifecycle/devconcord-compatibility-migration` | Actual public/persisted/exchanged contract change only |
| `lifecycle release` | `lifecycle/devconcord-release-engineering` | Explicit release candidate/distribution assessment; no automatic release |
| `lifecycle dependencies` | `lifecycle/devconcord-dependency-governance` | Dependency decisions or material dependency risks |
| `manage bootstrap` | `management/devconcord-bootstrap-from-design` | Design-grounded repository foundation within requested scope |
| `manage adopt` | `management/devconcord-adopt-guidance` | Selective guidance adoption preserving local rules |
| `manage sync` | `management/devconcord-sync-guidance` | Safe synchronization with per-document baselines |
| `manage guidance` | `management/devconcord-generate-agent-guidance` | Requested AGENTS.md, REVIEW.md, or both |
| `manage reference` | `management/devconcord-reference` | Version-pinned local source material |
| `evaluate agent` | `evaluation/devconcord-agent-behavior-evaluation` | Scenario-based evaluation with independent evidence |

## Natural-language routing

Route by desired outcome, target, expected artifact, and authority, not by a keyword alone:

- “Review this repository” → `review repository`.
- “How should we proceed with development from here?” → `develop plan` (read-only iteration plan and stop conditions).
- “How should this feature be divided into implementation steps?” → `develop implementation-plan`.
- “Implement the next important issues and verify them iteratively” → `develop issue` for issue selection, or `develop iterate` when the user delegates the broader loop.
- “Improve the existing design” → `design evolve`.
- “Find why this test/regression fails” → `diagnose root-cause`; diagnosis alone does not authorize the fix.
- “Stabilize quality without adding features” → `develop stabilize`.
- “Find and remove the blockers preventing these issues from progressing” → `develop unblock`; resolve only within current authority, otherwise identify safe independent work or escalate.
- “Find unresolved decisions” → `decide scan` (read-only).
- “Investigate/compare/recommend/resolve this decision” → the matching `decide` workflow; investigation defaults to read-only, recommendations are not approvals, and `resolve` requires current authority.
- “Resume this long-running task from its handoff” → the applicable `develop issue` or `develop iterate` workflow; inspect and revalidate the existing handoff before continuing. Do not create a handoff for routine work or treat it as authority.
- “Synchronize adopted DevConcord guidance” → `manage sync`.
- “Migrate safely from an old persisted format” → `lifecycle compatibility`.
- A dependency update or security/licensing/supply-chain assessment → `lifecycle dependencies`.
- A request to prepare a release candidate or validate installation/update/rollback → `lifecycle release`.

## Normalize and resolve ambiguity

Accept case differences, whitespace variations, and a short form only when it maps to exactly one command. Reject unknown command areas/intents with the nearest valid commands. If required context is missing, first inspect repository evidence and available guidance. Ask only if competing interpretations change scope, permissions, or deliverables. For read-only requests, keep work read-only. For multiple outcomes, name the primary workflow and the small set of relevant supporting modules; never imply automatic cross-Skill invocation.

Resolve `develop plan` versus `develop implementation-plan` by the requested outcome: planning the development loop and its continue/stop decision selects Development Orchestration; splitting a specified change into implementation increments selects Implementation Planning. Do not infer implementation permission from either plan.
