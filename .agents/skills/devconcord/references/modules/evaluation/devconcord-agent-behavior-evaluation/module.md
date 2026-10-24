
# Agent Behavior Evaluation

Evaluate actual outcomes, not whether a prompt or Skill contains expected
keywords. This workflow can assess DevConcord and other projects' agent workflows.

## Workflow

1. Identify the Skills, agent/runtime/version, discovery scope, task, authority,
   and evaluation purpose. Distinguish unavailable discovery from bad
   selection or execution.
2. Pin the Skill and scenario revisions. Reuse existing scenarios and fixtures
   (including `tests/integration/` when evaluating DevConcord); record a clean,
   reproducible starting state and the permitted paths and operations.
3. Define acceptance and prohibited outcomes independently from the agent's
   response. Use requirements, contracts, fixture state, allowed diff, and
   observable command results. Do not require a model's wording to match a
   reference answer.
4. Run the real agent when the requested environment is available. Preserve
   input, output, tool/command trace, final tree, diff, tests, and environment
   version. Do not broaden permissions to make a scenario pass.
5. Evaluate separately: **Discovery** (Skill visible), **Selection** (chosen
   for the task), **Contract compliance** (scope and constraints followed),
   **Behavioral correctness** (acceptance), **Execution reliability**,
   **Regression**, **Efficiency/proportionality**, and **permission boundaries**.
6. For risk-proportional selection, identify false negatives (missed material
   expertise), false positives (unneeded specialist workflow), excessive or
   insufficient depth, and incorrect escalation (missed approval/design
   boundary or unnecessary stop). Judge against task evidence and outcomes;
   neither fewer Skills nor a fixed Skill count is inherently better.
7. Classify each result as pass, failure, inconclusive, or not run, with direct
   evidence and uncertainty. Static metadata/link checks establish package
   validity only; manual scenario review is not real-agent E2E.
8. Compare revisions using the same scenario, initial state, agent/runtime,
   permissions, and evaluator criteria where possible. Explain any confounder;
   do not infer causality from unlike runs.
9. Recommend the smallest improvement and regression scenario. Report
   remaining risks; do not create a new score or evaluation ledger.

## Boundaries

- The agent's explanation is evidence of its report, not proof of its actions.
  Independently inspect diffs, state, executed verification, and prohibited
  side effects.
- A missing agent/runtime means E2E was not run. You may prepare a scenario or
  perform static review, but label that evidence accurately.
- Discovery, selection, and execution are separate claims. A Skill file in a
  search path does not prove a host discovered or chose it.
- Use disposable fixtures for destructive or permission-boundary scenarios.
  Stop if isolation, reset, or observation is inadequate.
- Use existing issue tracking and evaluation axes; do not score an agent from
  a single run or turn prose quality into a proxy for correctness.

## Deliverable

State scope/revisions/environment, scenario and initial state, evidence
collected, results by evaluation dimension, changes and verification,
confounders, unrun checks, and the minimal improvement/regression plan.

## DevConcord References

Use `devconcord manage reference` when available and request only needed paths. If
the Reference workflow cannot be selected, use the configured source checkout
directly:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord \
  --path tests/integration/README.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a
required reference cannot be read, stop
the dependent evaluation; if it is optional, report the gap and continue only
where evidence remains sufficient.

## Scenarios

For DevConcord, use `tests/integration/README.md` for manual agent scenarios.
Do not copy its fixtures or claim a run that did not occur.
