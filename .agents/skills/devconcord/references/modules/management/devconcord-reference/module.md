
# DevConcord Reference

Provide a deterministic, read-only interface for retrieving local DevConcord
documents. Use `scripts/manage_skills.py reference` for configuration,
source, manifest, revision, and path validation; do not reproduce those checks.

## Request flow

1. Identify the requesting workflow name, repository-relative document path, and
   requested revision. Use `installed` by default. For Project Scope, also
   identify the target repository. Ask for a basis when a direct user request
   does not identify which Skill revision to use.
2. Resolve the configured `source_root` from `~/.devconcord/config.json` and
   run its `scripts/manage_skills.py` with the existing `reference` command.
   Do not assume the current working directory is the source checkout.
3. Pass the requesting workflow's name to `--skill`. Never substitute
   `devconcord manage reference` or another Skill to obtain a missing installation
   record. The `installed` revision uses the requesting workflow's recorded
   source commit, even when this workflow was installed from a different commit.
   The CLI checks the installed Skill against its manifest and the Git Skill
   tree at that commit. Dirty-source installations cannot prove an exact
   committed version and are rejected for `installed`; select `head` or
   `working-tree` explicitly only when that different basis is intended.
   The recorded commit must exist locally; it need not be an ancestor of the
   current HEAD, and unrelated current Skills do not block this read. `head`
   and `working-tree` do not promise a match with the installed Skill.
4. Return the CLI's verified source identity, commit or working-tree status,
   requested path, and retrieved contents. For `working-tree`, report that
   uncommitted or untracked source content may be included. Git revisions
   allow only regular files in the selected commit tree; `working-tree`
   rejects symlinks and paths that escape the configured checkout.
5. On failure, report the actual diagnostic. Do not claim the document was
   read, silently switch to `head`, another Skill's commit, or an online copy.
   The CLI returns no document content or success metadata on failure. Tell
   the requesting workflow whether the missing material is required or optional
   so it can stop safely or continue its self-contained workflow.

The CLI verifies consistency between the manifest, installed Skill, and local
Git history; this is not cryptographic authentication of a fully altered
manifest. A Skill tree hash also cannot distinguish commits that contain the
same Skill tree but different documents. See `docs/agent-skills.md` in the
configured source checkout for the exact guarantees and limits.

Example for a Bootstrap request:

```sh
python3 /configured/source_root/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/application-design/templates/requirements.md \
  --revision installed
```

If this workflow cannot be selected or invoked, a requesting workflow may run the
same CLI directly, passing its own Skill name. Skill-to-skill invocation and
access to a user's local files are not guaranteed across agents or runtimes.
The detailed CLI, scope, setup, and troubleshooting contract is in
`docs/agent-skills.md` in the configured source checkout.
