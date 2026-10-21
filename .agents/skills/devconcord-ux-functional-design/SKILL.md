---
name: devconcord-ux-functional-design
description: >
  DevConcord design workflow for deriving functional requirements and
  application behavior from user goals, tasks, and usability evidence. Use for
  feature workflows, interaction states, cancellation, recovery,
  accessibility, proportionate GUI mockups, and non-GUI user touchpoints.
---

# UX-Driven Functional Design

## Workflow

1. Establish the target users, context, important tasks, success outcomes, frequency, input modes, error impact and known evidence. Mark hypotheses and unknowns.
2. Use relevant HCD, JTBD, mental/conceptual models, Norman action cycle, Nielsen heuristics, Hick–Hyman/Fitts, cognitive load, recognition, progressive disclosure, information architecture, error prevention/recovery, accessibility, feedback and consistency principles as reasoning tools—not a mandatory checklist.
3. Derive task flows, operations, state transitions, discoverability, primary/secondary actions, reversibility/confirmation, feedback and recovery. For async or bulk work, define progress, cancellation point, partial success, retry/idempotency and consistency in the application/domain contract, not only in UI controls.
4. Convert the rationale into verifiable TASK/REQ acceptance criteria and suitable user, accessibility, state-machine, boundary or integration tests. Link source evidence → task → requirement → design/use case → acceptance → evidence using existing project records; do not require a separate matrix for small projects.
5. Fit the user touchpoint: GUI-specific keyboard/touch/screen-reader behavior only where applicable; CLI command, output, exit/error contract for CLI; stable API and diagnostics for library/service.
6. Review conflicts with performance, robustness, security and replaceability. Record consequential tradeoffs in the project's ADR process.
7. For GUI work, when a mockup would resolve meaningful ambiguity or risk, create or update a proportionate, editable representation. Markdown may capture task, information hierarchy, states and acceptance criteria; HTML/CSS/SVG can make a framework-independent visual mockup, and JavaScript is optional for interactions. Reuse existing design tools when appropriate. Keep previews self-contained where practical; avoid external resources and unsafe insertion of untrusted content. Do not require a separate design document or a web implementation for native UI.
8. For GUI implementation changes, trace the meaning of the diff to existing UI requirements, decisions, design documents and mockups. Include ViewModel, application/domain state, async and error/recovery behavior when they affect user-visible behavior; file paths/extensions alone do not determine impact. Classify each relevant asset as needing update, no update, uncertain, already stale, or absent/out of scope. Update confirmed design changes in the same change unit when practical. If deferred, record target, mismatch/impact, reason, follow-up condition or existing issue ID, and how readers/agents will know the asset is stale. Do not create a mockup just because none exists or update it for internal changes with no UI impact.
9. When design and implementation disagree, compare approved requirements/decisions, change intent and verification evidence; do not silently treat the implementation as approval to change requirements. Distinguish implementation defects, stale design assets, intentional platform differences, unresolved conflicts and minor presentation differences. Do not use a confirmed stale mockup as unqualified current-spec evidence; retire assets and references when their maintenance value ends.
10. Review source structure and rendered appearance separately. Exercise important mock interactions when useful, but do not treat mock behavior as application evidence. After implementation, compare task intent, information priority, operations, states and acceptance criteria; pixel equality is not a universal acceptance condition. Verify native platform behavior in the actual target environment where applicable.

## Quality check

The output must explain why a user need implies a function or behavior, how success/failure is observable, and how the acceptance condition can be verified. For GUI work, choose design artifacts and mockup fidelity in proportion to ambiguity, risk and project scale; consider design-asset impact when implementation changes; and distinguish source review, rendered visual review, interaction checks and implementation evidence. Naming usability theories without a resulting design decision is insufficient.

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
