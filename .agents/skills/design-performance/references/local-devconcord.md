# Local DevConcord References

Read these shared guides or templates only when this task needs their detail. The bundled Skill workflow remains usable without the source checkout.

Relevant source paths:

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`

Use the configured checkout's `scripts/manage_skills.py reference --skill design-performance --path <path>` for a needed file. The default `installed` revision reads the exact source commit recorded for this Skill; use `--revision head` or `working-tree` only when that version is intended, and label working-tree content uncommitted. For Project Scope, add `--scope project --target <target-repository>`.

If configuration, source identity, commit, file access, or the requested path is unavailable, report that and do not claim the material was read or silently substitute another revision. The helper is read-only; applying guidance is a separate target-repository change.
