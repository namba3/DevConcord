---
name: sync-guidance
description: "Update shared guidance already adopted by a repository using per-document Git baselines. Use when synchronizing DevConcord rules, templates, or other adopted documentation while preserving local edits and held differences."
---

# Sync Adopted Guidance

This workflow applies document changes to an existing target repository. It does not update the globally installed DevConcord Skills. Use `adopt-guidance` for first-time adoption.

## Required safety checks

- Preserve target and source worktrees, history, remotes, and user changes. Never fetch, unshallow, reset, force-update, or rewrite baselines without explicit authorization.
- Verify full source commit IDs exist and that normal updates move forward from each document's own baseline. Treat same commit as a no-op; distinguish behind, diverged, missing, shallow/incomplete, and Git-error states.
- Do not overwrite local edits or reapply previously applied changes. Keep partial and held notes until resolved. Update a document's baseline only after its changes and required validation succeed.
- Keep shared-guidance provenance separate from Skill manifests. Do not run global or project Skill updates unless the user separately requests them.
- Do not report a check as successful unless it was run. Deterministic helper tests do not establish that an AI agent made a correct adoption decision.

## Workflow

Read [the detailed synchronization workflow](references/workflow.md) before applying changes. It covers provenance rows, per-file history checks, rename handling, conflict classes, selective updates, validation, and reporting.

For exact DevConcord source documents, use [the version-pinned local reference procedure](references/local-devconcord.md). Do not assume that a local checkout or the required source commit is available.

## Completion report

Report source baseline and target commit, documents updated and their new states, differences held or excluded, target changes preserved, validations run and not run, and unresolved history or content conflicts.
