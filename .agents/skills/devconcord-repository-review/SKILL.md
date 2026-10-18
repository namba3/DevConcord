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

For detailed DevConcord review criteria or templates, use the [version-pinned local reference procedure](references/local-devconcord.md) when relevant. Do not depend on local checkout access for general repository reviews.

## References

The links below follow `main` and can be newer than this installed Skill. For version-matched detail, read this Skill's `source_commit` from `.devconcord/skills-manifest.json` and replace `main` in the DevConcord links with that full SHA. If no commit is recorded or the revision is unavailable, do not assume the linked guide matches; the workflow above remains the usable baseline.

- [DevConcord review criteria](https://github.com/namba3/DevConcord/blob/main/REVIEWS.md)
- [Repository review workflow](https://github.com/namba3/DevConcord/blob/main/docs/README.md)

For an external target, apply its local `REVIEWS.md` as the project-specific source of review criteria. These upstream references are optional and may require network access.
