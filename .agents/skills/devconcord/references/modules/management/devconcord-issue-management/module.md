# Issue Register Management

The public `devconcord` Skill routes `manage issue inspect`, `manage issue archive`, and `manage issue restore` here. These are logical agent instructions, not native shell commands. Manage records, not feature implementation: use `develop issue` for project work. The active and archived issue records form one logical register with a single ISS allocation scheme.

## Authority and prerequisites

Inspect the target's current branch/worktree, instructions, canonical single register or federated index/subregisters, and explicit archive index. For any write, require the user's authorization for record changes; selecting this module never grants permission to edit, commit, push, or change history. Never overwrite unrelated user edits or invent completion evidence, terminal dates, issue IDs, or source provenance. Preserve existing architecture, risk records, quality scores, and local naming. `inspect` is read-only.

## Modes

- **Inspect:** Identify duplicate IDs, noncanonical IDs, next-ID collisions, broken references, unexpected archive states, and missing evidence. Use the read-only validator. Report relevant uncertainties and evidence scope.
- **Archive:** Select only genuine terminal ISS (`完了`/`見送り`) with verified acceptance/evidence. Prefer a bounded batch and dry-run; initial optional heuristic is 50 terminal active records and 30 days from verified terminal date, not a mandatory gate. Explicitly named IDs may be considered independently. Preserve the entire canonical record, its details and stable references. Keep per-year archives, splitting oversized files without renaming already-linked files.
- **Restore:** For mistaken terminal disposition, move the same canonical ISS back to Active without reassigning its ID; preserve the original history and record the reason. A genuinely new issue after closure should receive a new ID with a link to the original.

## Workflow and validation

1. Read `docs/work-management/issue-tracking.md` §2.3; identify the active scope and all indexed archives. Do not load the entire archive into the model for ordinary development.
2. Build a finite plan from actual records. Recheck state and ID uniqueness across both locations, terminal evidence, dates, dependencies, old anchors/links, source and destination files, and ongoing concurrent edits. Unknown is not safe by default.
3. For deterministic simple transfers, use `scripts/manage_issue_archive.py` (defaults to dry-run; `--apply` is explicit) with `--issue-register` for single mode or `--issue-main` and `--managed-dir` for federated mode, plus `--archive-dir`. Use `--ids` for explicit selection or `--auto` for eligible old terminal issues. For complex Markdown, details, references or conflicting styles which the CLI cannot preserve, prepare a manually reviewed migration instead of destructive automation.
4. After any authorized change, check both active and archive with `scripts/validate_docs.py` and review final diff. Ensure canonical-record uniqueness, preserved ID allocation and evidence, links, and rollback/retry constraints. Do not claim an unexecuted validation passed.
5. Report changed records/files, checks run and not run, skipped cases, remaining risk, and whether external operations were authorized.

This module does not create another project tracker, move nonterminal records, close issues as a side effect, or make archived historical tests current evidence.
