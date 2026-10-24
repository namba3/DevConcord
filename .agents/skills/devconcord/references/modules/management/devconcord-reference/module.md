# Version-Pinned DevConcord Reference

Provide a deterministic, read-only interface for retrieving local DevConcord documents. Use `scripts/manage_skills.py reference` for configuration, source, manifest, package revision, and path validation; do not reproduce those checks.

## Identity model

- **Public package identity:** `devconcord`. This is the only official installed package and the value passed to `--skill`.
- **Internal workflow identity:** a logical command such as `develop iterate` or a module path such as `development/devconcord-development-orchestration`. This identifies why a document is needed; it is not an installed package identity and must not be passed to `--skill`.
- **Installed revision identity:** the source commit and package hash recorded for `devconcord` in the manifest for the selected User or Project Scope.

The command accepts `--skill` for package lookup. When useful, state the requesting workflow separately in the agent's explanation or task notes; do not invent a CLI flag for it.

## Request flow

1. Identify the internal workflow that needs the document, the repository-relative path, and the requested revision. Use `installed` by default. For Project Scope, identify the target repository.
2. Resolve the configured local DevConcord source and run its `scripts/manage_skills.py reference` command. Do not assume the current working directory is the source checkout.
3. Pass `--skill devconcord`. Do not pass an internal module ID or former public Skill ID. The `installed` revision verifies the single package against its manifest and the Git Skill tree at the recorded commit. Dirty-source installations cannot prove an exact committed version and are rejected for `installed`; select `head` or `working-tree` explicitly only when that basis is intended.
4. Return the CLI's verified source identity, commit or working-tree status, requested path, and retrieved contents. For `working-tree`, report that uncommitted or untracked source content may be included. Git revisions allow only regular files in the selected commit tree; `working-tree` rejects symlinks and paths that escape the configured checkout.
5. On failure, report the actual diagnostic. Do not claim the document was read, silently switch to `head`, another package revision, or an online copy. The CLI returns no document content or success metadata on failure. Tell the requesting workflow whether the missing material is required or optional so it can stop safely or continue its self-contained workflow.

The CLI verifies consistency between the manifest, installed `devconcord` package, and local Git history; this is not cryptographic authentication of a fully altered manifest. A package tree hash also cannot distinguish commits that contain the same package tree but different documents. The recorded commit must exist locally but need not be an ancestor of current HEAD; unrelated files do not block this read. See `docs/agent-skills.md` in the configured source checkout for exact guarantees and limits.

## Example

For a workflow that needs the installed-version development guidance:

```sh
python3 /configured/source_root/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`. If this internal workflow cannot be selected or invoked, the root `devconcord` workflow can provide the same CLI instruction directly. Agent-to-agent invocation and access to a user's local files are not guaranteed across agents or runtimes. The detailed CLI, scope, setup, and troubleshooting contract is in `docs/agent-skills.md`.
