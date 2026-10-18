---
name: sync-guidance
description: "Safely update previously adopted shared guidance using per-document Git baselines. Use when syncing DevConcord rules, templates, or Skills while preserving local edits and held differences."
---

# Sync Adopted Guidance

## Workflow

1. Inspect both worktrees and the existing `docs/guidance-provenance.md`. Preserve target-local changes, per-document baselines, application states and hold notes.
2. Resolve requested source revisions to full commit IDs in the source repository. Verify both commits exist. For a normal forward sync, require `git merge-base --is-ancestor "$BASE_SHA" "$TARGET_SHA"` to exit `0`. Exit `1` means not ancestor; check reverse ancestry to distinguish behind from diverged. Treat other exit codes as Git errors. A shallow history that cannot prove ancestry is incomplete, not evidence of divergence.
3. For equal commits, make no content or provenance change. Never fetch, unshallow, reset, rewrite baselines, or update remote configuration without explicit authorization.
4. Compare each adopted source file from its own recorded baseline to the checked target revision. Review the target's current file and notes before applying: preserve local edits, prior applied changes, and unresolved holds. Do not bulk-copy unrelated or unadopted files.
5. Classify differences as safe, locally adapted, held, or excluded. Keep partial/held status and reasons. If files change, run relevant validation before updating the baseline or marking applied. A failed or unavailable required check leaves the baseline/state unchanged.
6. Check links, provenance rows, allowed paths, source-tree immutability and rerun behavior. Report actual source revisions, conflicts, validations and unresolved items.
7. For documentation-design changes, evaluate relevance to the target's readers, existing information architecture, publishing system, public URLs/anchors and local rules. A shared-rule update does not imply rewriting all target documentation. Apply only relevant differences and keep local adaptations, holds and provenance consistent.

## Skill synchronization

When syncing installed Skills as well as documents, use the repository's `scripts/manage_skills.py sync` tool if present. Run its plan/dry-run first. It updates only managed, unchanged copies; local modifications and same-name collisions are reported and preserved. The shared-guidance record and the Skill install manifest track distinct artifacts; do not duplicate or overwrite either record.

## Safety

Do not resolve uncertain history by guessing. Stop automatic application on missing commits, behind/diverged history, incomplete shallow history, or Git errors. Never silently overwrite local changes or report a partial synchronization as complete.
