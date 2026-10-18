---
name: devconcord-reference
description: >
  Resolve and read version-pinned DevConcord documentation, templates,
  and canonical development guidance from the configured local repository.
  Use when a DevConcord Skill or the user needs authoritative reference
  material from a specific installed Skill revision.
---

# DevConcord Reference

Provide a deterministic, read-only interface for retrieving local DevConcord
documents. Use `scripts/manage_skills.py reference` for configuration,
source, manifest, revision, and path validation; do not reproduce those checks.

## Request flow

1. Identify the requesting Skill name, repository-relative document path, and
   requested revision. Use `installed` by default. For Project Scope, also
   identify the target repository. Ask for a basis when a direct user request
   does not identify which Skill revision to use.
2. Resolve the configured `source_root` from `~/.devconcord/config.json` and
   run its `scripts/manage_skills.py` with the existing `reference` command.
   Do not assume the current working directory is the source checkout.
3. Pass the requesting Skill's name to `--skill`. Never substitute
   `devconcord-reference` or another Skill to obtain a missing installation
   record. The requesting Skill's installed commit is the default source
   revision, even when this Skill was installed from a different commit.
4. Return the CLI's verified source identity, commit or working-tree status,
   requested path, and retrieved contents. For `working-tree`, report that
   uncommitted or untracked source content may be included.
5. On failure, report the actual diagnostic. Do not claim the document was
   read, silently switch to `head`, another Skill's commit, or an online copy.
   Tell the requesting Skill whether the missing material is required or
   optional so it can stop safely or continue its self-contained workflow.

Example for a Bootstrap request:

```sh
python3 /configured/source_root/scripts/manage_skills.py reference \
  --skill devconcord-bootstrap-from-design \
  --path docs/application-design/templates/requirements.md \
  --revision installed
```

If this Skill cannot be selected or invoked, a requesting Skill may run the
same CLI directly, passing its own Skill name. Skill-to-skill invocation and
access to a user's local files are not guaranteed across agents or runtimes.
The detailed CLI, scope, setup, and troubleshooting contract is in
`docs/agent-skills.md` in the configured source checkout.
