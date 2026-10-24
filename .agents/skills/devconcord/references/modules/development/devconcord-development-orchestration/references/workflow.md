# Development Orchestration Workflow

This internal workflow reference is distributed inside the public `devconcord` package.
Follow the target repository's contracts, issue lifecycle, verification rules,
and document ownership. Keep the work bounded and preserve existing user work.

## 1. Establish a current baseline

At the start of every session, inspect the target, current HEAD/branch, index,
worktree and untracked files; applicable `AGENTS.md` and `REVIEW.md`; current
requirements, accepted ADRs and design; the existing issue register and risk
record; relevant implementation/tests; and available CI or verification
environments. Confirm the user's scope, exclusions, mode, and any explicit
iteration, change, time, or verification budget.

Treat prior reports as leads, not proof. Recheck current code and records, and
reassess whether earlier test evidence still applies after intervening changes.
Protect pre-existing changes. If relevant concurrent edits make ownership
unclear, do not touch those paths; report the conflict and continue only with
independent work that is clearly within scope.

If no usable issue register exists, do not invent issue IDs or a parallel
tracker. Use only a work source the user explicitly authorizes; otherwise
remain in Plan or report the missing prerequisite.

## 2. Select one work unit and plan its evidence

Use the target's issue register as the work authority. Confirm candidate issue
state, acceptance conditions, dependencies and blockers against current
evidence. Consider user impact, urgency, formal priority, dependencies, shared
cause, risk, verification readiness, regression surface, locality and
downstream value. Keep formal priority distinct from implementation order;
resolve actual prerequisites first without rewriting priority. Detect missing
references or dependency cycles rather than guessing an order.

Choose one semantically coherent unit that can be reviewed and verified on its
own. Do not copy the issue-selection or Batch procedure from
the `develop issue` internal workflow for issue selection and completion when
that bounded unit is in scope and authorized. Use
`devconcord-implementation-planning` when connected changes need sequencing.
For the selected unit, record the intended outcome, existing contract,
acceptance condition, proportionate verification, affected boundaries, and
the stop condition. Do not add work just because it shares a file or looks
easy.

Before execution, assess only material risk dimensions and select relevant
specialist expertise and verification evidence. Consider impact, likelihood,
uncertainty, affected scope, reversibility, and evidence confidence where they
change the decision; preserve severe/irreversible red flags instead of
averaging them into a low classification. Use the existing conditional Skill
mapping in `docs/common/ai-assisted-development.md` §17.5, not a per-unit
inventory of every Skill. Skill availability, selection, application, and
verification are distinct; selection does not authorize work or expand the
iteration budget.

## 3. Implement within the delegated boundary

Make the smallest change that meets the accepted contract. Apply relevant
Design by Contract, TDD, UX, performance, robustness, replaceability,
security, observability, and documentation principles in proportion to the
change. Preserve dependency direction and compatibility where required.
Update implementation, tests, docs, design assets, or issue records only when
that change is within the user's authorization and the repository's rules.

Do not silently change requirements, API/data compatibility, product policy,
security guarantees, or major architecture. Distinguish an implementation
defect from a design gap or unresolved requirement. If a consequential design
decision is needed, stop dependent implementation and provide the evidence,
impact, alternatives, and approval needed. Safe independent work may continue.

In Stabilize mode, do not add features. Prefer high-impact defects,
regressions, integrity/recovery risks, security defects, measurable
performance regressions, stale design assets, and important unverified
acceptance conditions. Verification, test, and documentation consistency
work can be useful without code changes. Avoid speculative refactoring.

## 4. Verify the changed state

Select checks from the acceptance condition and risk. They can include unit,
integration, acceptance, regression, state-machine, property, fuzz, fault,
performance, security, UI-transition, or platform-specific verification; do
not require every method mechanically.

Report distinctly whether a test was designed, added, run, passed, whether an
acceptance condition was checked, and whether the actual target environment
was verified. Record commands/results and constraints. Confirm that evidence
covers the final relevant diff; rerun affected checks after repairs. Static
validation, fixtures, mocks, browser, native/device behavior, remote CI, and
real-agent execution are separate evidence categories.

For material fixes or optimizations, keep reasoning proportionate: record the
observed problem, cause hypothesis, supporting or contradicting evidence,
proposed change, expected effect, failure/reversal condition, and actual
result. Trivial mechanical edits do not need a formal hypothesis record.
Reassess evidence freshness against changed code, configuration, dependencies,
contracts, and environment; rerun checks whose basis changed, not unrelated
suites by ritual.

If a check fails, identify whether evidence supports an implementation defect,
test issue, pre-existing failure, environment problem, design conflict,
requirement uncertainty, regression, or evidence gap. A single focused repair
pass per work unit is allowed within the default budget. Do not keep changing
code while the cause is unknown, weaken expected behavior, or delete failing
tests to pass a gate. If unresolved, stop dependent units and report the safe
recovery point.

Reassess risk and verification after implementation, failures, and review if
new evidence changes a contract boundary, data integrity, security exposure,
compatibility, availability, performance constraint, affected scope, or
confidence in prior evidence. Increase or reduce depth to address the changed
residual risk; do not skip a material check because a specialist Skill is
unavailable, and do not continue expensive checks without a relevant oracle.
This reassessment does not expand permissions, repair limits, or approval
authority.

## 5. Review and integrate

Detect stagnation such as repeated identical failures, unknown cause,
successive changes without verification, weakened expectations that hide the
defect, no acceptance/risk progress, exhausted budget, or change risk exceeding
likely benefit. Switch to diagnosis, revise the plan within authority, or stop
safely; do not add a loop ledger or score.

Review the final diff against the request, requirements, acceptance
conditions, target review criteria, and initial worktree. Look for contract
violations, logic/state/error defects, cancellation/retry issues, regressions,
security or performance risk, unnecessary complexity, test gaps, and stale
documentation or design assets. Keep findings evidence-based and finite;
report severity, basis, impact, and a repair path for material findings.

Update only authorized canonical artifacts and existing records. Preserve
issue IDs, priority/status meanings, history, the existing ten quality axes
and weights, and SDS separation. Mark work complete only when the local
Definition of Done and acceptance/verification obligations are met. Record
evidence with the target revision or worktree state where the register
requires it. Keep concrete known defects in the existing issue register and
future uncertainty in the existing risk record. Do not add a loop ledger,
score, or duplicate defect list.

## 6. Pass quality gates and decide what happens next

Assess the following gates in proportion to the unit's risk. A gate is an
evidence-based decision, not a requirement to fill a checklist mechanically.

| Gate | Evidence to consider | If it does not pass |
|---|---|---|
| Scope integrity | Changes remain authorized; original local work is preserved; no unapproved requirement change | Stop conflicting/out-of-scope work and report it |
| Contract integrity | Requirements, invariants, compatibility, state/error behavior and design agree | Repair within scope or route a design decision; do not advance dependent work |
| Verification evidence | Relevant checks ran and passed, or limitations are explicit; evidence covers final changes | Diagnose, use the bounded repair pass, or stop as blocked |
| Regression control | Relevant regression surface and material security/reliability/performance risks were assessed | Repair or stop dependent work if regression remains unresolved |
| Progress validity | Acceptance or material risk moved with evidence; next unit has a credible benefit | Stop if there is no supported progress or useful next step |

At the end of a unit, choose one state for this orchestration decision (these
do not replace project issue statuses or quality axes):

- **Progressing:** an acceptance condition or material risk moved forward with
  current evidence.
- **Stabilizing:** existing behavior or verification is being made safer
  without new features.
- **Regressing:** a material contract, quality attribute, or prior passing
  behavior got worse; stop expansion and repair or report.
- **Blocked:** required approval, dependency, source, or environment evidence
  is unavailable.
- **Converged:** the delegated target is met, remaining material blockers are
  absent or explicitly accepted, and another change has low or unsupported
  value.

Then decide:

1. **Continue** with another in-scope unit only if it has a credible benefit,
   required dependencies are resolved, gates passed, and budget remains.
2. **Repair** only a diagnosed in-scope issue and only within remaining repair
   budget; rerun affected verification and review.
3. **Reconsider design** if approved requirements conflict with implementation
   or a major decision is needed. Route to `devconcord-design-orchestration`
   when available; do not assume automatic handoff or approval.
4. **Blocked** when further safe progress depends on unavailable approval,
   input, prerequisite, or environment.
5. **Stop** when the user boundary or finite budget is reached, the goal is
   converged, progress lacks evidence, competing changes appear, or expected
   value no longer justifies the change.

Do not expand the budget automatically. Discovery can reveal more issues
without proving quality regressed; record verified findings in the existing
register only if authorized, then reassess whether they are in scope. Never
equate closed-issue count with quality.

## 7. Resume and report

On a later session, rebuild the baseline from current HEAD/worktree, issue
register, implementation/tests, acceptance evidence, blockers and residual
risks. Verify old evidence against current changes; do not resume from a prior
agent report alone.

Report mode and boundary; selected work units and rationale; changes;
commands and results; review findings and repairs; authorized record updates;
remaining issues, blockers, assumptions and risks; and why the loop continued
or stopped. State which environments, real agents, or checks were not run.
Do not create a durable progress report when existing issues/CI records or a
concise final response are sufficient.
