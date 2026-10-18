---
name: devconcord-adopt-guidance
description: >
  DevConcord workflow for selectively introducing shared development guidance,
  templates, and agent instructions into an existing repository. Use for a
  first-time adoption that preserves existing project rules; choose
  devconcord-bootstrap-from-design for a new repository or
  devconcord-sync-guidance for already adopted materials.
---

# Adopt Shared Guidance

Use this workflow for first-time adoption into an existing project. Use `devconcord-bootstrap-from-design` for a new repository and `devconcord-sync-guidance` to update already adopted materials.

## Required safety checks

- Inspect and preserve the target's uncommitted work, Git history, remotes, existing rules, requirement and issue IDs, statuses, links, and project-specific structure. Do not overwrite unexamined files or alter unrelated code, settings, or data.
- Select only useful materials. Do not force DevConcord's layout, README format, GUI rules, new issue or risk ledgers, all-dependency abstractions, or unrequested Agent Skill installation.
- Keep design-source provenance, shared-guidance provenance, and Skill installation manifests separate. Record only verified source commits and actual application state; partial and held material must not be marked fully applied.
- Do not claim unrun checks passed or treat deterministic fixture tests as evidence of real agent decisions.

## Workflow

Read [the detailed Adoption workflow](references/workflow.md) before making changes. It covers target and source inspection, selective adoption, link and provenance handling, test evidence, and reporting. Use `devconcord-generate-agent-guidance` when AGENTS.md or REVIEWS.md generation is in scope.

For detailed DevConcord guidance or templates, use [the version-pinned local reference procedure](references/local-devconcord.md). If the local checkout or required commit cannot be read, report that and do not claim to have applied its contents.

## Completion report

List adopted, excluded, partially applied, and held materials; target rules and records preserved; source URL and checked commit; changed paths; validations run and not run; unresolved conflicts; and remaining decisions. Keep `docs/guidance-provenance.md` consistent with the actual applied scope.
