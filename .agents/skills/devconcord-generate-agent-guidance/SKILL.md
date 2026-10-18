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
- `reviews`: create or update `REVIEWS.md`. Read `AGENTS.md` to preserve its contract; do not change it as a side effect. If it lacks the required instruction to read `REVIEWS.md` before reviewing, make only that narrow safety correction and report it.
- `both`: create or update both files consistently, writing `REVIEWS.md` first and ensuring `AGENTS.md` tells reviewers to read it.

Infer the mode from the user's request. If it is ambiguous, work only on the clearly requested file and report the other as out of scope.

## Required safety checks

- Ground current-state statements and commands in the target's actual source, manifests, tests, CI, and documentation. Mark unknowns as unverified; do not invent functionality, guarantees, licenses, or checks.
- Preserve valid existing instructions, project-specific rules, issue/requirement IDs, and unrelated edits. Integrate changes instead of replacing unexamined files.
- Keep `AGENTS.md` concise and operational; keep repository-specific review findings in `REVIEWS.md`. Do not copy a generic rulebook or add unsupported vendor-specific invocation syntax.
- Preserve the distinction between applying relevant design principles, recommending a specialist Skill, and executing it. Derive any AGENTS.md guidance from the target's actual design risks and verified Skill availability; never require every Skill or imply an unavailable Skill is installed. In REVIEWS.md, tie an optional Skill recommendation to a concrete finding and impact, without substituting it for the finding or its remediation.
- Check Project Scope Skill files in the target's actual discovery locations. Check User Scope only through the current environment's verifiable agent discovery locations and installed state; installed files alone do not prove an agent discovers or selects them, and availability in one user environment does not apply to CI or other users. Never install Skills as part of guidance generation.
- A DevConcord source update does not update existing target guidance. Report that users need to install or synchronize the updated generator Skill and invoke it in the target repository to regenerate or integrate guidance; never mutate target repositories outside the requested scope.
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
