---
name: devconcord-sync-guidance
description: >
  DevConcord workflow for updating shared guidance already adopted by a
  repository using per-document Git baselines. Use to synchronize rules,
  templates, and documentation while preserving local edits and held
  differences; it does not update installed Skill packages.
---

# Sync Adopted Guidance

This workflow applies document changes to an existing target repository. It does not update the globally installed DevConcord Skills. Use `devconcord-adopt-guidance` for first-time adoption.

## Required safety checks

- Preserve target and source worktrees, history, remotes, and user changes. Never fetch, unshallow, reset, force-update, or rewrite baselines without explicit authorization.
- Verify full source commit IDs exist and that normal updates move forward from each document's own baseline. Treat same commit as a no-op; distinguish behind, diverged, missing, shallow/incomplete, and Git-error states.
- Do not overwrite local edits or reapply previously applied changes. Keep partial and held notes until resolved. Update a document's baseline only after its changes and required validation succeed.
- Keep shared-guidance provenance separate from Skill manifests. Do not run global or project Skill updates unless the user separately requests them.
- Do not report a check as successful unless it was run. Deterministic helper tests do not establish that an AI agent made a correct adoption decision.

## Workflow

Read [the detailed synchronization workflow](references/workflow.md) before applying changes. It covers provenance rows, per-file history checks, rename handling, conflict classes, selective updates, validation, and reporting.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/agent-skills.md`
- `docs/README.md`
- `docs/work-management/issue-tracking.md`
- `docs/application-design/secrets-by-design.md` (when this guide was already adopted and its changes are in scope)

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-sync-guidance --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## Completion report

Report source baseline and target commit, documents updated and their new states, differences held or excluded, target changes preserved, validations run and not run, and unresolved history or content conflicts.
