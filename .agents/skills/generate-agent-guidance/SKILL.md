---
name: generate-agent-guidance
description: "Create or update repository-specific AGENTS.md, REVIEWS.md, or both based on actual code, architecture, tests, CI, and existing rules. Use when configuring coding-agent instructions or review guidance."
---

# Generate Agent Guidance

Choose the smallest mode that matches the request:

- `agents`: create or update only `AGENTS.md`.
- `reviews`: create or update only `REVIEWS.md`.
- `both`: create or update both files consistently, writing `REVIEWS.md` first and ensuring `AGENTS.md` tells reviewers to read it.

Infer the mode from the user's request. If it is ambiguous, work only on the clearly requested file and report the other as out of scope.

## Required safety checks

- Ground current-state statements and commands in the target's actual source, manifests, tests, CI, and documentation. Mark unknowns as unverified; do not invent functionality, guarantees, licenses, or checks.
- Preserve valid existing instructions, project-specific rules, issue/requirement IDs, and unrelated edits. Integrate changes instead of replacing unexamined files.
- Keep `AGENTS.md` concise and operational; keep repository-specific review findings in `REVIEWS.md`. Do not copy a generic rulebook or add unsupported vendor-specific invocation syntax.
- Do not change source code, settings, or tests as a side effect. Report checks actually run and those not run.

## Workflow

Read [the AGENTS.md generation procedure](references/agents-md.md) and/or [the REVIEWS.md generation procedure](references/reviews-md.md) for the selected mode. Use both references in `both` mode and create the review criteria first.

For optional DevConcord documentation guidance, use [the version-pinned local reference procedure](references/local-devconcord.md). The generation procedures remain usable without this checkout.

## Completion report

Report the selected mode, files changed, verified repository evidence, preserved or reconciled existing rules, link and command checks, unknowns, checks run and not run, and remaining issues.
