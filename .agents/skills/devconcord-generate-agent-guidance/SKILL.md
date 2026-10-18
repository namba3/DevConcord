---
name: devconcord-generate-agent-guidance
description: >
  DevConcord workflow for creating or updating repository-specific AGENTS.md,
  REVIEWS.md, or both from actual code, architecture, tests, CI, and existing
  rules. Use to establish coding-agent instructions or review criteria without
  inventing project contracts.
---

# Generate Agent Guidance

Choose the smallest mode that matches the request:

- `agents`: create or update only `AGENTS.md`.
- `reviews`: create or update only `REVIEWS.md`.
- `both`: create or update both files consistently, writing `REVIEWS.md` first and ensuring `AGENTS.md` tells reviewers to read it.

Infer the mode from the user's request. If it is ambiguous, work only on the clearly requested file and report the other as out of scope.

## Required safety checks

- Ground current-state statements and commands in the target's actual source, manifests, tests, CI, and documentation. Mark unknowns as unverified; do not invent functionality, guarantees, licenses, or checks.
- Preserve valid existing instructions, project-specific rules, issue/requirement IDs, and unrelated edits. Integrate changes instead of replacing unexamined files.
- Keep `AGENTS.md` concise and operational; keep repository-specific review findings in `REVIEWS.md`. Do not copy a generic rulebook or add unsupported vendor-specific invocation syntax.
- Do not change source code, settings, or tests as a side effect. Report checks actually run and those not run.

## Workflow

Read [the AGENTS.md generation procedure](references/agents-md.md) and/or [the REVIEWS.md generation procedure](references/reviews-md.md) for the selected mode. Use both references in `both` mode and create the review criteria first.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `REVIEWS.md`
- `docs/common/ai-assisted-development.md`
- `docs/common/documentation-design.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-generate-agent-guidance --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## Completion report

Report the selected mode, files changed, verified repository evidence, preserved or reconciled existing rules, link and command checks, unknowns, checks run and not run, and remaining issues.
