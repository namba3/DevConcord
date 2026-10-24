---
name: devconcord-root-cause-analysis
description: >
  Diagnose failures, regressions, and unexplained behavior by testing
  falsifiable cause hypotheses. Use when symptoms exist but the cause is
  unclear; diagnosis does not authorize product changes.
---

# Root Cause Analysis

Use evidence to narrow causes before recommending repair. A root cause may be
uncertain, multiple, or not recoverable from available evidence.

## Modes and authority

- **Diagnose:** inspect evidence and report causes or bounded uncertainty.
- **Experiment:** run safe, authorized reproductions and discriminating checks.
- **Repair Guidance:** propose repair and prevention conditions.

None grants permission to edit product code. Implement through the user's
existing Issue-Driven Development or Development Orchestration authority.

## Workflow

1. Preserve the initial state and capture the symptom, impact, environment,
   timing, recent changes, logs, and available traces. Minimize sensitive data.
2. Separate observed facts from interpretation. Reproduce when safe and
   useful; record the exact conditions and distinguish failure to reproduce
   from evidence that the defect is absent.
3. Form a small set of competing, falsifiable hypotheses. For each, state
   supporting evidence, contradicting evidence, and a test that distinguishes
   it from alternatives.
4. Run the least invasive, highest-information experiments first. Do not
   change expected behavior, suppress errors, add synchronization, or alter
   unrelated variables just to obtain a passing result.
5. Identify the cause only to the confidence the evidence supports. If no
   hypothesis is sufficiently distinguished, report the bounded uncertainty,
   missing evidence, and next safe experiment.
6. Compare repair options against the actual cause, contracts, data/state,
   security, performance, compatibility, and rollback cost. State prevention
   conditions that can be independently verified.
7. After an authorized repair, verify the original reproduction, relevant
   regression boundary, and final diff. A new test passing alone does not
   prove the cause or prevent recurrence.

## Boundaries

- Symptom, trigger, contributing condition, and root cause may differ.
- Correlation, temporal order, and a plausible story are not causal proof.
- Preserve competing causes and confidence; do not overstate certainty.
- For nondeterministic or production-only failures, use existing safe
  diagnostics and evidence retention contracts. Do not introduce telemetry or
  expose secrets as an improvised diagnostic step.
- Use `devconcord-repository-review` for concrete defect findings,
  `devconcord-test-design` for independent verification strategy,
  Robustness for failure/state/recovery contracts, Performance for measured
  bottlenecks, and Observability for diagnostic signals. These are optional
  and are not invoked automatically.

## Deliverable

Report symptom and impact, environment and reproduction, observed evidence,
hypotheses and discriminating experiments, cause/confidence or uncertainty,
repair options, prevention evidence, and work that requires separate
implementation authority.

## DevConcord References

Use `devconcord-reference` when available for relevant requirements,
observability, robustness, or issue-tracking guidance. If the common Skill
cannot be selected, run the configured source checkout's CLI for each needed
path:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-root-cause-analysis \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread references were used. If a
required reference cannot be read, stop
the dependent analysis; if it is optional, report the gap and continue only
where the result remains grounded.
