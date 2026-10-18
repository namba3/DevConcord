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

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `docs/README.md`
- `docs/agent-skills.md`
- `docs/common/ai-assisted-development.md`
- `docs/common/documentation-design.md`
- `docs/work-management/issue-tracking.md`
- `docs/application-design/templates/requirements.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-adopt-guidance --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## Completion report

List adopted, excluded, partially applied, and held materials; target rules and records preserved; source URL and checked commit; changed paths; validations run and not run; unresolved conflicts; and remaining decisions. When useful based on evidence gathered during Adoption, include follow-up Gap Analysis or specialist Skill recommendations under `docs/common/ai-assisted-development.md` §17.3. Do not imply that adopted guidance has been implemented or that unexamined design quality was assessed. Recommendations remain outside Adoption scope and do not run or install Skills. Keep `docs/guidance-provenance.md` consistent with the actual applied scope.
