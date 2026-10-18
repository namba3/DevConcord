---
name: generate-agent-guidance
description: "Create or update repository-specific AGENTS.md and REVIEWS.md based on actual code, architecture, tests, CI, and existing rules. Use when configuring coding-agent instructions or review guidance."
---

# Generate Agent Guidance

## Workflow

1. Inspect existing `AGENTS.md`, `REVIEWS.md`, README, documentation conventions, architecture, source, manifests, test commands, CI and project issue/requirements records. Preserve valid existing rules and IDs.
2. Record only verified current facts as such. Label requirements for future work and unverified constraints separately. Keep AGENTS concise and operational; put review-specific contracts and risks in REVIEWS.
3. Include relevant commands only when confirmed in manifests, CI or existing docs. Do not invent architecture, guarantees, license, or available tests. Keep `AGENTS.md` concise and include a proportional document-impact rule only when useful; keep documentation-specific review concerns in `REVIEWS.md`.
4. Maintain the instruction that reviewers read repository-root `REVIEWS.md` before review. Avoid copying a large generic rulebook; link to nearby project docs where present.
5. Discover Skills by inspecting the repository/user agent skill paths that actually exist. Mention available skill names and when to use them; do not assume every agent recognizes every path or impose vendor-specific invocation syntax in shared instructions.
6. Validate Markdown links and changed paths. Report missing evidence and tests not run.

For documentation principles, prefer the target's own adopted guide. The optional DevConcord [documentation-design guide](https://github.com/namba3/DevConcord/blob/main/docs/common/documentation-design.md) is a reference, not a mandated layout. For version-matched guidance, use this Skill's recorded `source_commit` when available; otherwise make no claim that the remote guide matches the Skill.

## Compatibility

When the repository contains DevConcord generation prompts, use `prompts/create-agents-md.md` and `prompts/create-reviews-md.md` as the detailed source of procedure. Otherwise follow the portable steps above without requiring the DevConcord repository.
