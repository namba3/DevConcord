---
name: repository-review
description: "Review a repository's code, architecture, requirements, tests, CI, and project guidance for concrete defects and risks. Use for repository audits, design reviews, code reviews, or readiness assessments."
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

## References

- [DevConcord review criteria](https://github.com/namba3/DevConcord/blob/main/REVIEWS.md)
- [Repository review workflow](https://github.com/namba3/DevConcord/blob/main/docs/README.md)

For an external target, apply its local `REVIEWS.md` as the project-specific source of review criteria. These upstream references are optional and may require network access. When installed with `manage_skills.py`, use the recorded `source_commit` in `.devconcord/skills-manifest.json` in place of `main` in these URLs to pin the references to the installed source revision.
