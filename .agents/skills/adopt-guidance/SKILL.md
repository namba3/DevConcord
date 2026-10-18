---
name: adopt-guidance
description: "Selectively introduce shared development guidance, templates, and agent instructions into an existing software repository. Use when adopting common coding standards without replacing existing project rules."
---

# Adopt Shared Guidance

## Purpose

Safely select and integrate reusable guidance into a project that already exists.

## When to use / not use

- Use when an existing repository needs selected development guidance or templates.
- Do not use for a new repository bootstrapped from design inputs; use `bootstrap-from-design`.
- Do not use to update guidance already recorded as adopted; use `sync-guidance`.

## Workflow

1. Inspect the target root, worktree, README, docs and their reader/publishing roles, code, toolchain, CI, requirements, ADRs, issue register, `AGENTS.md` and `REVIEWS.md`. Capture relevant existing content, links, conventions and Git state; do not stage, commit, or discard unrelated edits.
2. Read the source guidance and select only materials useful for the target's technology, risk, scale and existing conventions. Prefer source-controlled, committed guidance. Reuse the target's issue and risk registers; never replace existing instructions or tracking identifiers.
3. Resolve overlap and conflicts explicitly. Preserve effective local rules, statuses, history, links, requirements, and decisions. Consider the documentation-design guidance only when it improves reader navigation or maintainability; do not force its directory layout, README pattern or a documentation site. Do not impose GUI-specific conventions on CLI/library/service projects, add duplicate ledgers, force all dependencies behind interfaces, or invent project-specific facts.
4. Integrate only the agreed materials. For `AGENTS.md` / `REVIEWS.md`, use the repository's generation prompts if available; inspect what is implemented separately from constraints intended for future work. Keep the review-file loading instruction in `AGENTS.md`.
5. Record shared-material source, checked revision and per-material destination/baseline, application state and hold notes in the established `docs/guidance-provenance.md` format when adopting shared materials. Do not confuse it with design-document provenance or claim a held/partial material is fully applied.
6. Check changed-file scope, existing content and issue records, relative links, publishing/build conventions, provenance, and relevant project tests. Re-run only if it will not create duplicate files or entries.

## Documentation references

The optional [documentation-design guide](https://github.com/namba3/DevConcord/blob/main/docs/common/documentation-design.md) provides reusable reader-centred principles. It may require network access and may follow a newer revision than this Skill. For version-matched guidance, resolve this Skill's `source_commit` from `.devconcord/skills-manifest.json` and replace `main` with that full SHA. The workflow remains usable if the guide is unavailable.

## Safety and completion

Do not overwrite an unexamined file with the same name, change Git history/remotes, or make remote changes. Report selected and excluded material, preserved local rules, conflicts/holds, exact revision, changed paths, checks and unresolved items. A successful document copy alone does not prove the guidance was correctly adopted.
