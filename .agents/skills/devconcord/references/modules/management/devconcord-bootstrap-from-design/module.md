
# Design-to-Repository Bootstrap

Build a small, verifiable repository foundation from design inputs. Use for a new project; use `devconcord-adopt-guidance` for an existing project's first guidance adoption and `devconcord-sync-guidance` for updates to guidance already adopted.

## Required safety checks

- Inspect the target, its files, Git history, index, remotes, and worktree before editing. Distinguish an empty directory, explicitly listed design files, verified DevConcord Skills, an unborn repository, and a repository with history or implementation.
- Preserve existing files, design inputs, history, remotes, and user changes. Never reinitialize an existing Git repository, push, create a remote, or commit unless explicitly requested. If the start state or a conflict is uncertain, stop before destructive work.
- A preinstalled Skill alone does not make a target an existing project only when its schema 2 manifest and every package hash validate, there are no other files or unlisted Skills, and any Git repository has no history, remotes, or unrelated changes. Otherwise preserve and stop or work additively without treating it as empty.
- Do not invent requirements, technical choices, licenses, commands, numeric targets, implemented features, tests, or guarantees. Do not claim to have read inaccessible design inputs or references.
- Keep design-input provenance separate from shared-guidance provenance. Do not copy design inputs without permission and redistribution rights.

## Workflow

Read [the detailed Bootstrap workflow](references/workflow.md) before carrying out the task. Follow its input review, scope selection, requirement traceability, documentation architecture, minimal implementation, validation, rerun, and reporting steps. Read additional reference files only when needed.

Use the **Foundation**, **Scaffold** (default), or **Initial Implementation** scope requested by the user. Implement only the agreed scope; a Bootstrap result does not imply feature completion.

## DevConcord References

When one of these canonical references is needed, use `devconcord manage reference` if available. Identify this workflow as the requester and pass only the needed repository-relative path.

- `README.md`
- `docs/README.md`
- `docs/common/ai-assisted-development.md`
- `docs/common/documentation-design.md`
- `docs/application-design/templates/requirements.md`
- `docs/application-design/templates/adr.md`
- `docs/application-design/secrets-by-design.md` (when credential or identity choices are in scope)
- `docs/work-management/issue-tracking.md`

If the Reference workflow cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## Completion report

Report the actual target start state, input files and unread portions, assumptions and conflicts, scope, changed outputs, checks run and results, checks not run, and unresolved issues. When unresolved design work warrants it, include scoped follow-up Skill recommendations under the contract in `docs/common/ai-assisted-development.md` §17.3. This recommendation is outside Bootstrap scope and does not run or install a Skill. Preserve the target's Git and worktree state except for the requested additions.
