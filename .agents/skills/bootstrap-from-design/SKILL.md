---
name: bootstrap-from-design
description: "Initialize a new software repository from design documents, requirements, architecture decisions, and technical constraints. Use when creating a project scaffold or initial implementation from one or more specifications."
---

# Design-to-Repository Bootstrap

## Purpose

Turn design inputs into a small, buildable and verifiable repository foundation. This is not a code-generation dump or an existing-project guidance adoption.

## When to use / not use

- Use for a new repository initialized from requirements, architecture, UI/UX, quality, or technical-selection documents.
- Do not use to add common rules to an existing project; use the repository's `adopt-guidance` skill/workflow.
- Do not use to update already adopted shared guidance; use `sync-guidance`.
- If the target already contains meaningful source or project records, inspect and preserve them; stop before conflicting or destructive changes.

## Inputs

Identify all design-document paths, target directory, project name and constraints when known, bootstrap scope, and user-specific instructions. Bootstrap scope defaults to **Scaffold**: the smallest meaningful buildable/testable skeleton. The available scopes are **Foundation** (development foundation only), **Scaffold**, and **Initial Implementation** (only explicitly requested initial features).

## Workflow

1. Inspect target files, Git state, remotes, and existing rules before editing. Distinguish an empty uninitialized directory, a populated uninitialized directory, an initialized empty repository, and an implemented project. Never discard files, history, uncommitted changes, or remotes. Run `git init` only for an empty uninitialized target or when explicitly authorized; never push, create a hosted repository, or commit without explicit instruction.
2. Read each input using available tools. For PDF/DOCX or image-based material, report what was actually extracted and what remains unread; do not invent content or install an extractor without approval. Record source filename, version/date/commit and section/page where available. Keep design-source provenance distinct from shared-guidance provenance. Do not copy design documents without permission to redistribute and store them.
3. Analyze purpose/scope, users and tasks, platform/toolchain, selected technology, use cases/domain, contracts/invariants, dependencies, quality and security requirements, verification/release conditions, contradictions, unknowns, assumptions and risks. Preserve source references. Resolve document precedence only when the documents state it. Ask about consequential contradictions; proceed only with reversible foundation work where safe.
4. Convert evidence into a lightweight trace: source section → TASK/REQ/NFR → architecture/ADR → initial modules and tasks → acceptance criteria → tests/evidence. Use existing project tables and avoid a second tracking ledger. Do not choose an unprovided license or invent numeric targets.
5. Shape the initial structure to the selected stack and scope. Keep core use cases independently testable. Isolate UI/OS/storage/network dependencies only where change value justifies the abstraction; preserve semantic contracts. Avoid unused interfaces, duplicate implementations, and one-to-one wrappers.
6. Apply user-centered functional design to actual user touchpoints (GUI, CLI, service, library): derive operations, state/feedback, asynchronous progress/cancellation, errors/recovery and accessibility only as relevant. Design performance around workload and resource flow. Design robustness around invariants, partial failure, atomicity, idempotency, cancellation and recovery. State what is a future constraint versus an implemented behavior.
7. Create only in-scope outputs: build/development setup, README with verified commands, requirements/ADR/project notes, the existing issue register, CI/test setup, `AGENTS.md` / `REVIEWS.md` as useful, and the smallest meaningful entry point and smoke test for Scaffold. Never make a stub report success for an unimplemented feature. Reuse existing repository-specific instruction/review generation workflows when available.
8. Validate changed paths, source links, build/syntax, tests, dependency boundaries and configuration as applicable. Re-run against the same inputs and ensure it creates no unnecessary differences or duplicate records. Report executed checks separately from future checks.

## Safety and completion

Stop before destructive changes or consequential unresolved design decisions. Preserve existing Git history and worktree. Report inputs and unread portions, starting state, decisions/assumptions, changed outputs, checks and results, unresolved issues and residual risks. Bootstrap completion does not imply feature completion or verified quality claims.
