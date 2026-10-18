---
name: devconcord-repository-review
description: >
  DevConcord workflow for evidence-based repository reviews across code,
  architecture, requirements, tests, CI, and project guidance. Use for audits,
  design or code reviews, and readiness assessments that need concrete
  findings; distinguish defects from optional improvements.
---

# Repository Review

## Workflow

1. Read repository `AGENTS.md` and `REVIEWS.md` before reviewing. If `REVIEWS.md` is absent, say so and use evidence-based general review criteria without inventing project-specific guarantees.
2. Establish review scope and inspect relevant source, tests, CI, requirements, ADRs, issue/risk records and actual diff. Distinguish observed behavior from documented intent.
3. Evaluate correctness, user task/function fit, contracts and invariants, boundary/failure behavior, security/privacy, compatibility, resource/performance implications, dependency direction and verification evidence where relevant.
4. Report only actionable findings with severity, file/line, concrete impact, reproduction or evidence, confidence and a minimal remedy. Separate findings from questions, residual risks, and unverified assumptions.
5. Do not infer missing code or tests as present; do not claim tests passed unless run. Avoid speculative findings, style-only comments and fixes unless the user requests implementation.

## Completion

Summarize scope and evidence, prioritized findings, checks performed and limitations. Do not treat a score or successful CI as proof of correctness.

## DevConcord References

When one of these canonical references is needed, use `devconcord-reference` if available. Identify this Skill as the requester and pass only the needed repository-relative path.

- `REVIEWS.md`
- `docs/common/ai-assisted-development.md`
- `docs/work-management/issue-tracking.md`

If the common Skill cannot be selected, run the configured source checkout's `scripts/manage_skills.py reference --skill devconcord-repository-review --path <path> --revision installed` directly. For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue the self-contained workflow.

## References

The GitHub `main` links below are for browsing and may show newer material than this Skill. Use the `DevConcord References` CLI flow above for authoritative, version-pinned guidance; online content is not an automatic fallback.

- [DevConcord review criteria](https://github.com/namba3/DevConcord/blob/main/REVIEWS.md)
- [Repository review workflow](https://github.com/namba3/DevConcord/blob/main/docs/README.md)

For an external target, apply its local `REVIEWS.md` as the project-specific source of review criteria. These upstream references are optional and may require network access.
