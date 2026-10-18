---
name: devconcord-ux-functional-design
description: >
  DevConcord design workflow for deriving functional requirements and
  application behavior from user goals, tasks, and usability evidence. Use for
  feature workflows, interaction states, cancellation, recovery,
  accessibility, and non-GUI user touchpoints.
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

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/application-design/ui-ux-guide.md`
- `docs/application-design/ui-ux-quick-reference.md`
- `docs/application-design/templates/requirements.md`
- `docs/common/ai-assisted-development.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-ux-functional-design --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this Skill. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord UI/UX design guide](https://github.com/namba3/DevConcord/blob/main/docs/application-design/ui-ux-guide.md)
- [Requirements template](https://github.com/namba3/DevConcord/blob/main/docs/application-design/templates/requirements.md)
