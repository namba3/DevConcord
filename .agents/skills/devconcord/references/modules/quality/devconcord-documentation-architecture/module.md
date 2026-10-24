
# Documentation Architecture

## Purpose

Improve documentation around real reader tasks while preserving the project's existing structure, conventions, content, links, and publishing behavior.

## When to use / not use

- Use for README or technical-documentation review, information architecture, navigation, duplication, clarity, and documentation impact analysis.
- Use with `devconcord-bootstrap-from-design` for new projects, `devconcord-adopt-guidance` for first-time guidance adoption, and `devconcord-sync-guidance` for updates to adopted shared rules; do not replace those workflows.
- Use `devconcord-repository-review` for a broader repository audit where documentation is one review area.

## Workflow

1. Inspect the target's `AGENTS.md`, `REVIEW.md`, README, docs tree, source/configuration, existing publishing system, documentation conventions, tests and CI. Establish current worktree state and protect local changes.
2. Identify actual readers, their tasks, current entry points, canonical sources, and high-impact paths such as published URLs, anchors, generated references, sidebars and examples. Separate observed facts from assumptions and unverified claims.
3. Review whether the information is findable and accurate: purpose and audience, grouping and naming, headings, progressive detail, concise but complete explanations, consistent terminology, links, examples, duplication and conflicts with code or configuration.
4. Trace only relevant change impact: features to user guidance/specifications; public APIs to API references, examples and migration notes; CLI changes to command guidance; configuration to references/deployment; architecture to design records/ADRs; CI or development-environment changes to setup; release changes to release/runbook material. Do not rewrite unaffected documents. When implementation, requirements and docs disagree, compare verifiable evidence and intended change; surface unresolved ownership instead of guessing.
5. Propose the smallest useful change. Keep the current architecture when it works; do not impose a DevConcord directory layout, README template, documentation site, language or file count. Separate pages only where audience, task, ownership, update cadence or review value justify it.
6. Preserve a clear source of truth. Replace repeated rules with summaries and links; keep generated outputs tied to an identified editable source. Preserve requirements, ADRs, issue IDs, links and existing tracking practices; do not create a parallel quality or task ledger.
7. Validate changed links, anchors, examples and the target's existing documentation build/lint/test commands. Prefer existing tooling. Report static checks separately from semantic review and real-reader/agent testing.
8. Report changed paths, preserved links/content, checks run, remaining conflicts and unverified claims. Never describe an unrun command or unimplemented feature as verified.

## Review checks

Prioritize reader task completion, correctness, discoverability, information hierarchy, single-source ownership, consistency with implementation, stable navigation, traceability where needed, and ease of future updates. Do not equate more pages, shorter documents, or a numeric score with better documentation. Keep necessary constraints, edge cases and technical detail even when simplifying prose.

## DevConcord References

When one of these canonical references is needed, use `devconcord manage reference` if available. Identify this workflow as the requester and pass only the needed repository-relative path.

- `docs/common/documentation-design.md`
- `docs/README.md`

If the Reference workflow cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The detailed reusable principles are maintained in the DevConcord documentation-design guide. The GitHub `main` link below is for browsing and may show newer material than this workflow. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [Documentation design guide](https://github.com/namba3/DevConcord/blob/main/docs/common/documentation-design.md)
