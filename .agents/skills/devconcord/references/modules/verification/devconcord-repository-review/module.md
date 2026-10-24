
# Repository Review

## Select the work mode

Follow the user's request:

- **Change Impact Assessment** is for a proposed change before implementation. Analyze its likely scope, affected contracts, dependencies, migration and regression risks, and verification needs. Treat these as forecasts and open questions, not confirmed defects. This is read-only by default and does not produce an implementation sequence; use `devconcord-implementation-planning` when sequencing work is needed.
- **Repository / Change Review** is for existing code, architecture, or a concrete diff. Find evidenced defects, contract violations, regressions, and verification gaps. Preserve the existing evidence-based severity and remediation behavior.
- If the request clearly asks for both, separate predicted impacts from findings about current behavior. If the mode is unclear, use Repository / Change Review for a supplied diff or existing implementation, and ask or state the assumption for an unimplemented proposal.

## Workflow

1. Read repository `AGENTS.md` and review criteria before reviewing. Prefer root `REVIEW.md`; if it is absent, read legacy root `REVIEWS.md` when present and identify it as legacy. If both exist, read both and compare substantive rules. Report important differences or contradictions as uncertainty; do not edit, delete, or silently merge either file. If neither exists, use evidence-based general criteria without inventing project-specific guarantees.
2. Establish review scope and inspect relevant source, tests, CI, requirements, ADRs, issue/risk records and actual diff. Distinguish observed behavior from documented intent.
3. Evaluate correctness, user task/function fit, contracts and invariants, boundary/failure behavior, and—where relevant—assets, trust boundaries, threats, least privilege, secure defaults, data lifecycle, dependency/supply-chain risk, security invariants, compatibility, resource/performance implications, dependency direction and verification evidence.
   For GUI-affecting changes, trace the diff's meaning (including state, ViewModel, async and error handling) to relevant approved UI intent and existing design assets. Check whether assets need synchronization, are already stale, differ intentionally by platform, or have an unresolved conflict. Do not infer impact from paths alone, require mockups where none exist, or treat stale mockups as current specification. Compare user-visible structure, operations and states rather than requiring pixel equality; report only evidence-backed discrepancies and verification limits. Trace changed contracts to callers, consumers, persisted/exchanged formats, state transitions, and failure paths. Compare semantic before/after behavior, not changed-file count. Check whether verification evidence still covers the final code/config/dependency/contract state. Identify material regression candidates and distinguish implementation defects from unresolved design choices. Consider a focused architecture fitness check only when it detects consequential drift and has a reliable oracle.
4. Report only actionable findings with severity, file/line, concrete impact, reproduction or evidence, confidence and a minimal remedy. Separate findings from questions, residual risks, and unverified assumptions.
5. Do not infer missing code or tests as present; do not claim tests passed unless run. Avoid speculative findings, style-only comments and fixes unless the user requests implementation.

Set review breadth from the semantic change and material risk, not changed
file or line count. Consider impact, uncertainty, affected consumers,
reversibility, and evidence confidence only where they can change the review.
Unknown scope is not low risk; keep severe or irreversible consequences
visible without an arithmetic score. Match verification claims to the final
diff and its tested conditions. For the shared decision principles, see
`docs/common/ai-assisted-development.md` §17.5.

## Optional specialist workflows

Compatibility Migration, Release Engineering, and Dependency Governance are
not default review gates. Consider them only when a changed public/data
contract, an explicit release task, or a dependency decision/material risk
makes them relevant. Their absence or non-use does not stop unrelated review;
basic compatibility, release, and dependency checks still apply when a real
risk is present. A finding does not authorize migration, dependency changes,
distribution, or release approval.

## Change Impact Assessment

For the selected proposal, inspect relevant requirements, acceptance conditions, existing implementation, project guidance, tests and CI, ADRs, and existing issue/risk records. Select only affected areas from:

- public APIs, compatibility, domain responsibilities, and module boundaries;
- persisted formats, data migration, state transitions, invariants, and error/cancel/retry behavior;
- user workflows and UI state, where relevant;
- workload, resource use, security assets and trust boundaries, external dependencies, and OS-specific behavior;
- tests, CI, documentation, configuration, and operations.

Distinguish confirmed current facts from assumptions about the proposal. Do not attach normal defect severity labels to unverified forecasts; state confidence, impact, and the evidence needed to resolve uncertainty. Prefer analysis of concrete downstream effects over a checklist of unaffected areas.

When useful, report the change purpose and scope, inspected specifications and implementation, likely change locations, affected contracts and dependencies, plausible regressions or migration risks, decisions still needed, suggested verification, unknowns, and related REQ / ADR / ISSUE IDs. Keep implementation sequencing in `develop implementation-plan` and test-case design in `verify test-design`; these internal workflows are optional and are not invoked automatically.

Do not edit source, configuration, requirements, issue or risk records as part of this assessment. A separately requested implementation or record update is a separate scope and follows the target repository's rules.

## Completion

Summarize scope and evidence, prioritized findings, checks performed and limitations. Do not treat a score or successful CI as proof of correctness.

## DevConcord References

When one of these canonical references is needed, use `devconcord manage reference` if available. Identify this workflow as the requester and pass only the needed repository-relative path.

- `REVIEW.md`
- `docs/common/ai-assisted-development.md`
- `docs/work-management/issue-tracking.md`

If the Reference workflow cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this workflow. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord review criteria](https://github.com/namba3/DevConcord/blob/main/REVIEW.md)
- [Repository review workflow](https://github.com/namba3/DevConcord/blob/main/docs/README.md)

For an external target, apply its local `REVIEW.md` as the project-specific source of review criteria. These upstream references are optional and may require network access.
