
# Test Design

Design how important behavior should be verified. This workflow produces a test
plan; it does not implement tests or run them unless the user explicitly asks
for that work.

## Workflow

1. Read the relevant requirements and acceptance conditions, ADRs, public
   contracts, existing tests, and repository test/CI conventions. Use existing
   REQ / NFR / ADR / ISSUE identifiers and test suites where available.
2. Identify the behavior under test, responsible boundary, externally
   observable result, important state, and consequences of a missed defect.
3. Derive expected outcomes from requirements, contracts, independent
   specifications, or a trusted oracle. **Do not treat the existing
   implementation as its own specification.** If the contract is unclear,
   state the question or a clearly labeled assumption instead of matching the
   test to current behavior.
4. Select the normal, boundary, invalid-input, failure, and recovery cases
   that matter to the behavior and risk. Include invariants and state
   transitions where they affect correctness.
5. Choose suitable test levels and methods: unit, integration, acceptance,
   contract, boundary, property-based, state-machine, fault-injection,
   recovery, concurrency, regression, benchmark, or security-negative tests.
   Use only methods that answer a relevant question; do not maximize technique
   count or require every change to use every test level.
6. Specify test data, fixtures, dependencies, isolation, cleanup, determinism,
   environment, tolerances, and CI placement where relevant. Avoid hidden
   shared state, brittle timing assumptions, and tests whose expected value is
   copied from the code under test.
7. Map important acceptance conditions and invariants to the planned
   observation and test. Record uncovered conditions, unavailable oracles,
   and checks that need a real service, platform, device, or manual evaluator.
8. Report the strategy and evidence boundary. Distinguish a proposed case,
   implemented test, executed test, pass/failure result, and the requirement's
   actual fulfillment.

## Select verification methods by defect model

Choose a method only when its oracle and cost are justified by the contract:
the desired evidence should be proportional to impact, likelihood,
uncertainty, affected scope, reversibility, and confidence in existing
verification. Do not treat unknown risk as low risk or verification cost as a
reason to ignore a serious consequence. Reassess method and depth if new
implementation or test evidence changes these conditions. The canonical risk
and Skill-selection rules are in `docs/common/ai-assisted-development.md`
§17.5.

| Method | Useful for | Entry condition and oracle | Cost / limit; when to omit |
|---|---|---|---|
| Unit / integration / acceptance | Local logic, boundaries, user-visible flows | Stable contract and observable result at the chosen boundary | Environment and maintenance cost; omit redundant layers without a distinct observation |
| Property-based | Broad input spaces and invariants | General property plus reproducible/shrinkable counterexample | Runtime and property quality; omit for a tiny finite domain covered by examples |
| Fuzzing | Parsers, decoders, hostile inputs | Safe harness, crash/invariant oracle, corpus handling | Long/noisy runs do not prove absence; omit without actionable oracle |
| Mutation | Whether tests detect selected fault classes | Defined mutation operators and kill/survival interpretation | Compute and triage cost; not required for every suite |
| Model-based | Stateful workflows and operation sequences | Reviewed reference model and observable state contract | Model may share specification defects; omit for simple stateless behavior |
| Differential | Compatibility or equivalent implementations | Trusted independent implementation/version and normalized comparison | Comparators can share defects or semantics can differ; omit without sound comparator |
| Fault injection | Recovery, timeout, partial success, cancellation | Failure points and required post-failure invariants | Instrumentation and realism limits; omit irrelevant failure modes |
| Concurrency | Races, ordering, atomicity, deadlock | Required histories/invariants and controlled schedules where possible | Nondeterminism; stress alone cannot prove absence; omit for single-threaded contracts |
| Benchmarking | Performance requirements/regressions | Representative workload/environment, repeated measurements, tolerance | Noise and machine cost; omit when no performance claim or constraint is affected |
| Security verification | Threat-specific controls and negative cases | Asset, threat, invariant, observable rejection/containment | Scope and tool limits; choose by threat, not tool availability |
| Formal verification | Critical invariants with tractable formal model | Precise model, assumptions, proof boundary | Expertise/model cost; omit when evidence value does not justify it |

Passing tests establish only the observations and conditions exercised. Keep
test presence, execution, result, acceptance fulfillment, and residual risk as
separate claims. Do not use implementation behavior alone as the oracle when
the requirement or independent contract is available.

## Boundaries

- UX-Driven Functional Design defines user tasks, behavior, and acceptance
  conditions; relevant Performance, Robustness, and Security Skills define
  their own requirements and invariants. This workflow chooses how to verify
  those contracts; it does not invent or replace them.
- Use Repository Review to investigate concrete defects or proposed change
  impacts. Use Implementation Planning to sequence implementation work. Do
  not duplicate those workflows in a test matrix.
- Reuse existing test suites and issue tracking. Do not create a permanent
  test-case ledger or update issue records unless the user explicitly includes
  that work.
- A test passing is evidence only for the conditions, data, configuration,
  and environment actually exercised. Test presence alone does not show a
  requirement is met; passing tests do not prove the complete requirement or
  guarantee untested behavior.

## Deliverable

Provide only the useful artifacts for the task: a test strategy, cases with
preconditions/actions/expected observations, test-level allocation, fixture
and environment notes, requirement links, regression plan, and uncovered or
unverified areas. Keep the result in an existing project document or issue
when requested; otherwise return it without creating a new file.

## DevConcord References

Use `devconcord manage reference` when available. Identify this workflow as the requester
and read only relevant paths, such as:

- `docs/common/ai-assisted-development.md` (BDD / ATDD / TDD and verification)
- `docs/application-design/templates/requirements.md`
- `docs/work-management/issue-tracking.md`

If the Reference workflow cannot be selected, use the configured source checkout's
CLI directly, one reference path per invocation:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/application-design/templates/requirements.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue only where the task remains self-contained.

## Completion

State the target behavior and requirements, selected verification approach,
independent source of expected results, test coverage and evidence actually
available, checks not run, assumptions, and remaining questions. Do not claim
tests were implemented, executed, passed, or sufficient unless evidence shows
that status.
