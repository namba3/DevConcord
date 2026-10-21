# UI Design Drift evaluation fixture

This small, synthetic fixture supports the eight manual UI Design Drift cases in [`tests/integration/README.md`](../../README.md). It demonstrates how to evaluate evidence handling and semantic decisions; it is not a product UI or a required web stack.

## Baseline

- [`design.md`](design.md) is the approved, synthetic requirement baseline and states the scope this fixture calls `Current`.
- [`mockup.html`](mockup.html), [`mockup.css`](mockup.css), and [`mockup.js`](mockup.js) express one visual and interaction representation of that baseline.
- The preview buttons switch presentation panels only. They do not implement archive transfer, cancellation, progress, or persistence.

For a manual evaluation, give the agent the baseline files and one case from the eight-case table in the integration guide. Include only the change evidence for that case, such as the approved requirement delta or implementation diff. Ask the agent to identify affected assets, classify the evidence, state whether synchronization is needed, and name the verification evidence still required. Keep the fixture files unchanged during the evaluation; apply proposed changes in a temporary copy.

Record the selected case, agent/product version, exact input and response, resulting proposed file changes, reviewer judgment, and checks actually run. Judge against the expected decision in the integration table. Do not convert this into an aggregate AI score unless a separately reviewed rubric and repeatable evaluation set exist. Static tests below check fixture structure and the state switch only; they do not test an agent's semantic judgment.

## Checks

Run the dependency-free JavaScript behavior check with:

```sh
node --test tests/integration/fixtures/ui-design-drift/mockup.test.cjs
```

The repository Python unittest suite also checks the HTML structure and local-only asset references. Browser rendering, keyboard interaction with assistive technology, native OS behavior, and real-agent evaluation require separate checks and are not inferred from these tests.
