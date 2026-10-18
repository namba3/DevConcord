---
name: devconcord-design-replaceability
description: >
  DevConcord design workflow for deciding where replaceable UI, storage,
  network, OS, service, or runtime dependencies need boundaries. Use when a
  technology change may have broad impact; weigh change value against
  abstraction and maintenance cost instead of modularizing everything.
---

# Replaceability by Design

## Workflow

1. Identify only consequential technical dependencies; assess probability/value of change, current coupling impact, migration cost and the cost of an abstraction.
2. Keep domain concepts and application use cases independent of UI widget/event/lifecycle types where justified. Separate domain/application state from presentation state. Permit views to require rewriting when changing fundamentally different UI frameworks.
3. For storage, network, OS and services, define a domain/application-owned contract and place technology-specific code at an adapter boundary only when the expected change value justifies it.
4. Specify semantic compatibility, not just method signatures: errors, transactions, atomicity, consistency, concurrency, performance, security, persistence formats, migrations and user-visible behavior.
5. Avoid interface-for-everything, unused alternative implementations, one-to-one library wrappers, least-common-denominator APIs and costly conversions/dispatch without evidence. A single concrete implementation can be correct.
6. Verify the claim with dependency-direction checks, adapter contract tests, integration/migration tests, or a small replacement experiment as appropriate. State exactly what can be preserved and what must change.

## Completion

Document the dependency, reason to isolate it, boundary/semantic contract, allowed migration scope, abstraction costs and verification evidence. Do not promise zero-change replacement.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/adr.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-design-replaceability --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The links below follow `main` and can be newer than this installed Skill. For version-matched detail, read this Skill's `source_commit` from `.devconcord/skills-manifest.json` and replace `main` in the DevConcord links with that full SHA. If no commit is recorded or the revision is unavailable, do not assume the linked guide matches; the workflow above remains the usable baseline.

- [DevConcord AI-assisted development guide](https://github.com/namba3/DevConcord/blob/main/docs/common/ai-assisted-development.md)
- [Architecture decision record template](https://github.com/namba3/DevConcord/blob/main/docs/application-design/templates/adr.md)

These optional deeper references do not replace the workflow above and may require network access. When installed with `manage_skills.py`, use the recorded `source_commit` in `.devconcord/skills-manifest.json` in place of `main` in these URLs to pin the references to the installed source revision.
