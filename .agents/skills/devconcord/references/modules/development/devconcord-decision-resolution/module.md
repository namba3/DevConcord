# Decision Resolution & Unblocking

Use this optional internal workflow to identify a material unresolved decision,
gather decision-changing evidence, make a bounded recommendation, and help
remove a verified development blocker. It does not add a public Skill or
replace the issue register, risk record, ADRs, or handoff.

## Logical commands

| Command | Purpose | Default authority |
|---|---|---|
| `decide scan` | Find and classify blockers/open decisions; check existing records and shared causes | Read-only |
| `decide investigate` | Gather evidence and propose discriminating checks | Read-only; experiments require authorization |
| `decide compare` | Compare feasible alternatives and challenge the leading option | Read-only |
| `decide recommend` | Present recommendation, evidence, uncertainty, consequences, and required authority | Read-only |
| `decide resolve` | Record an authorized decision in its canonical source and propagate references | Update only when authorized; never implies implementation permission |
| `develop unblock` | Find a safe path through blockers, resolve in-scope causes, or escalate | Bounded by current work authority and budget |

These are logical instructions, not shell commands or native slash commands.
Command selection does not grant permission. Read
[`references/workflow.md`](references/workflow.md) for the procedure.

## Record ownership

- The existing issue register remains the source of truth for work, issue
  status, priority, dependencies, blockers, acceptance, and issue evidence.
- An **Open Decision (DEC)** is a judgment to settle, not an implementation
  task. Give it a distinct `DEC-####` identifier and lifecycle state. By
  default, record it in an issue-register section. If volume harms readability,
  one authorized canonical decisions file may hold DEC details; the register
  then keeps references, not duplicate details. Never maintain both as sources
  of truth.
- A **Blocker** is a verified condition preventing an issue or work unit from
  proceeding safely. Track its work/status and references in the issue
  register. Not every blocker is a decision: prerequisite work, unavailable
  environments, and unexplained failures may instead need an Issue or Root
  Cause Analysis.
- **Risk** records a possible future event and impact in the existing risk
  record. **ADR** records a material design decision and its rationale.
  **HANDOFF** carries only the DEC ID, blocker context, evidence freshness, and
  next safe action needed to resume; it does not own DEC state.
- A **Decision Packet** is a temporary or linked presentation of evidence and a
  recommendation. It is not another decision record. Use an ADR for durable
  design rationale when appropriate.

## Lifecycle and authority

Use the target's existing labels when compatible; otherwise the recommended
DEC states are `未整理`, `調査中`, `判断可能`, `承認待ち`, `解決済み`, and
`保留`. A DEC is resolved only when the question and selected answer are clear,
required evidence or approval is recorded, scope is known, canonical
requirements/design/ADR are updated as needed, and material unresolved
conditions are visible. Resolution does not complete or automatically unblock
an issue. A hold includes its reason, safe independent work, owner, and
reconsideration condition; it is not resolution. Reopen/reconsider without
erasing prior decisions when new evidence changes assumptions.

Follow the user's current authority and the selected mode. Scanning,
investigation, comparison, and recommendation default to read-only. A
recommendation is not approval. Do not independently settle changed user
requirements, breaking public contracts, data-loss acceptance, critical
security guarantees, external-service/data policy, material cost/operational
ownership, or explicit risk acceptance. Resolve other matters only when they
are clearly delegated and consistent with accepted requirements and ADRs.
`decide resolve` does not authorize implementation, experiments, external
operations, issue-state changes, or Git operations by itself.

## Boundaries with existing workflows

Use `design orchestration` for creating/evolving design, `root-cause analysis`
for an unexplained actual failure, `develop issue` for bounded issue selection
and completion, and `develop iterate` for a finite development loop. Decision
Resolution frames and investigates the unresolved judgment and supports
unblocking; it does not repeat those workflows. Consider this module only when
the work reveals a material blocker or decision, or the user requests it. Do
not add it to every development iteration, a standard quality gate, or a
mandatory dependency. Preserve finite investigation/repair budgets and safe
stopping conditions. Optional parallel investigation may be used when available
and independent; otherwise perform the same checks sequentially.
