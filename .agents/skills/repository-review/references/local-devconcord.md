# Local DevConcord References

Use this reference only when a task needs detailed DevConcord guidance or a canonical template. The Skill workflow remains usable without the local checkout.

## Resolve the configured checkout

The per-user configuration is `~/.devconcord/config.json` in the current runtime's home directory. Read its `source_root`; it must be an absolute path to the DevConcord repository containing `scripts/manage_skills.py` and `.agents/skills/`. Windows, WSL, containers, and remote agents can have different home directories and filesystem access. Do not copy this machine-specific path into a project.

The installed Skill version is recorded in `~/.devconcord/skills-manifest.json` for User Scope, or in the target repository's `.devconcord/skills-manifest.json` for Project Scope. Prefer the installed Skill's exact `source_commit`, not local `HEAD` or the online `main` branch.

## Read a reference

When a terminal and Python/Git are available, run the configured checkout's `scripts/manage_skills.py reference` with argument arrays (not a dynamically evaluated shell string):

```text
reference --skill <this-skill-name> --path <repository-relative-path>
```

The default `installed` revision verifies that the configured repository has the same source identity recorded for the installed Skill, checks the installed Skill hash, and reads the requested file from its recorded Git commit. For Project Scope, add `--scope project --target <target-repository>`. Use `--revision head` only when the current committed checkout is intentionally wanted; it excludes uncommitted edits. Use `--revision working-tree` only when those edits are intentionally wanted, and identify them as uncommitted. These modes do not fetch or use the network.

Useful paths include:

- Bootstrap: `docs/application-design/templates/requirements.md`, `docs/common/ai-assisted-development.md`
- Adoption: `docs/common/documentation-design.md`, `docs/README.md`
- Synchronization and Skills: `docs/agent-skills.md`, `docs/work-management/issue-tracking.md`
- Documentation architecture: `docs/common/documentation-design.md`
- Agent guidance: `REVIEWS.md`
- UI/UX: `docs/application-design/ui-ux-guide.md`, `docs/application-design/ui-ux-quick-reference.md`
- Performance and robustness: `docs/common/ai-assisted-development.md`, `docs/application-design/templates/requirements.md`
- Replaceability: `docs/application-design/templates/adr.md`
- Repository review: `REVIEWS.md`, `docs/work-management/issue-tracking.md`

## Failure handling

If config is absent, malformed, stale, points outside a Git-managed DevConcord checkout, or the exact source commit/reference is unavailable, do not claim to have read the reference. Report whether the failure was configuration, filesystem access, source identity, missing commit, missing file, or tool permission. Do not fetch, rebind, or silently substitute `HEAD`, online documentation, or another local checkout. Ask the user to repair the source registration or explicitly authorize a different revision. If the agent cannot read the user's home directory or run the helper, request an accessible copy/revision of only the needed reference.

The helper is read-only. Applying guidance to a project remains a separate, explicit project change; keep project provenance distinct from the global Skill manifest.
