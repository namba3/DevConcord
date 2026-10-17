---
name: ux-functional-design
description: "Derive functional requirements and application behavior from user goals, tasks, and usability principles. Use when designing features, workflows, interaction states, cancellation, recovery, accessibility, or non-GUI user touchpoints."
---

# UX-Driven Functional Design

## Workflow

1. Establish the target users, context, important tasks, success outcomes, frequency, input modes, error impact and known evidence. Mark hypotheses and unknowns.
2. Use relevant HCD, JTBD, mental/conceptual models, Norman action cycle, Nielsen heuristics, Hick–Hyman/Fitts, cognitive load, recognition, progressive disclosure, information architecture, error prevention/recovery, accessibility, feedback and consistency principles as reasoning tools—not a mandatory checklist.
3. Derive task flows, operations, state transitions, discoverability, primary/secondary actions, reversibility/confirmation, feedback and recovery. For async or bulk work, define progress, cancellation point, partial success, retry/idempotency and consistency in the application/domain contract, not only in UI controls.
4. Convert the rationale into verifiable TASK/REQ acceptance criteria and suitable user, accessibility, state-machine, boundary or integration tests. Link source evidence → task → requirement → design/use case → acceptance → evidence using existing project records; do not require a separate matrix for small projects.
5. Fit the user touchpoint: GUI-specific keyboard/touch/screen-reader behavior only where applicable; CLI command, output, exit/error contract for CLI; stable API and diagnostics for library/service.
6. Review conflicts with performance, robustness, security and replaceability. Record consequential tradeoffs in the project's ADR process.

## Quality check

The output must explain why a user need implies a function or behavior, how success/failure is observable, and how the acceptance condition can be verified. Naming usability theories without a resulting design decision is insufficient.
