---
name: devconcord-generate-agent-guidance
description: >
  DevConcord workflow for creating or updating repository-specific AGENTS.md,
  REVIEW.md, or both from actual code, architecture, tests, CI, and existing
  rules. Use to establish coding-agent instructions or review criteria without
  inventing project contracts.
---

# Generate Agent Guidance

Choose the smallest mode that matches the request:

- `agents`: create or update only `AGENTS.md`.
- `reviews`: create or update only `REVIEW.md`, except for the `AGENTS.md` legacy-link correction required by a completed rename. Do not add or revise unrelated `AGENTS.md` guidance in this mode.
- `both`: create or update both files consistently, writing `REVIEW.md` first and ensuring `AGENTS.md` tells reviewers to read it.

Infer the mode from the user's request. If it is ambiguous, work only on the clearly requested file and report the other as out of scope.

## Existing review-file migration

Before writing either file, inspect the repository root, Git index/worktree state, tracked status and content of `REVIEW.md` and legacy `REVIEWS.md`, plus references in `AGENTS.md`, tooling, and CI. Do not assume every target is a clean Git checkout.

The `agents` mode never creates, renames, or deletes either review file. Preserve any valid existing reference, including a legacy `REVIEWS.md` reference, and report that migration requires `reviews` or `both` mode. If no review criteria file exists, keep the normal `REVIEW.md` instruction and report it as missing. The migration actions below apply only when review-file generation is selected.

- Neither file exists: create `REVIEW.md` from verified repository evidence.
- Only `REVIEW.md` exists: preserve and integrate its valid rules.
- Only `REVIEWS.md` exists: read the complete file and inspect its HEAD, index and worktree contents, status, and references. Transfer every valid rule and its relevant context into `REVIEW.md`; verify the result and links before updating the permitted `AGENTS.md` reference. Delete `REVIEWS.md` only after all deletion checks below pass. Preserve staged/unstaged intent and do not stage unrelated files; prefer a Git-recognizable rename when it does not disturb existing index state.
- Both exist: compare substantive rules, severity, prohibitions, verification conditions, Git history and status, and references. If rules are disjoint or safely reconcilable, integrate all valid rules into `REVIEW.md`, verify them, update the permitted reference, and delete `REVIEWS.md` after the deletion checks pass. If a material conflict or uncertain user edit cannot be reconciled without a decision, leave both files and references intact and report a concrete merge proposal.

Delete the legacy file only after confirming that `REVIEW.md` exists, all valid legacy rules and uncommitted content are preserved, the allowed `AGENTS.md` reference resolves, related references in the authorized scope are consistent, and no required content exists only in the old file. If any check is uncertain, preserve both files and defer deletion. Do not automatically recreate the old name. After a successful migration, later updates use only `REVIEW.md`, so the next run must not rediscover the old migration or add duplicate rules.

In `reviews` mode, change `AGENTS.md` only to replace its legacy review-file reference after a verified migration; do not add a missing review instruction or change design guidance. If that correction cannot be made safely, preserve the old valid reference and report that `both` mode is needed. In `both` mode, update the review file first, then point `AGENTS.md` to the verified `REVIEW.md`. Never leave a dangling link when migration is deferred. Bootstrap and Adoption delegate this handling to this Skill rather than implementing a second migration procedure.

## Required safety checks

- Ground current-state statements and commands in the target's actual source, manifests, tests, CI, and documentation. Mark unknowns as unverified; do not invent functionality, guarantees, licenses, or checks.
- Preserve valid existing instructions, project-specific rules, issue/requirement IDs, and unrelated edits. Integrate changes instead of replacing unexamined files.
- Keep `AGENTS.md` concise and operational; keep repository-specific review findings in `REVIEW.md`. Do not copy a generic rulebook or add unsupported vendor-specific invocation syntax.
- Preserve the distinction between applying relevant design principles, recommending a DevConcord Skill, and executing it. In generated `AGENTS.md`, recommend relevant DevConcord design Skills only when actual risks justify deeper design work. Treat `devconcord-repository-review` and `devconcord-gap-analysis` as assessment Skills; treat `devconcord-test-design` and `devconcord-implementation-planning` as optional verification/planning workflows. Recommend the latter only for a concrete need to derive independent verification or sequence complex work. Verify Project Scope or User Scope availability as applicable; never require every Skill, imply an unavailable Skill is installed, or exclude useful non-DevConcord Skills. In `REVIEW.md`, tie an optional Skill recommendation to a concrete finding and impact, without substituting it for the finding or its remediation.
- Check Project Scope Skill files in the target's actual discovery locations. Check User Scope only through the current environment's verifiable agent discovery locations and installed state; installed files alone do not prove an agent discovers or selects them, and availability in one user environment does not apply to CI or other users. Never install Skills as part of guidance generation.
- A DevConcord source update does not update existing target guidance. Report that users need to install or synchronize the updated generator Skill and invoke it in the target repository to regenerate or integrate guidance; never mutate target repositories outside the requested scope.
- Do not change source code, settings, or tests as a side effect. Report checks actually run and those not run.

## Workflow

Read [the AGENTS.md generation procedure](references/agents-md.md) and/or [the REVIEW.md generation procedure](references/reviews-md.md) for the selected mode. Use both references in `both` mode and create the review criteria first.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `REVIEW.md`
- `docs/common/ai-assisted-development.md`
- `docs/common/documentation-design.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-generate-agent-guidance --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## Completion report

Report the selected mode, files changed, verified repository evidence, preserved or reconciled existing rules, link and command checks, unknowns, checks run and not run, and remaining issues.
