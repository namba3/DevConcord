---
name: generate-agent-guidance
description: "Create or update repository-specific AGENTS.md and REVIEWS.md based on actual code, architecture, tests, CI, and existing rules. Use when configuring coding-agent instructions or review guidance."
---

# Generate Agent Guidance

## Workflow

1. Inspect existing `AGENTS.md`, `REVIEWS.md`, README, architecture, source, manifests, test commands, CI and project issue/requirements records. Preserve valid existing rules and IDs.
2. Record only verified current facts as such. Label requirements for future work and unverified constraints separately. Keep AGENTS concise and operational; put review-specific contracts and risks in REVIEWS.
3. Include relevant commands only when confirmed in manifests, CI or existing docs. Do not invent architecture, guarantees, license, or available tests.
4. Maintain the instruction that reviewers read repository-root `REVIEWS.md` before review. Avoid copying a large generic rulebook; link to nearby project docs where present.
5. Discover Skills by inspecting the repository/user agent skill paths that actually exist. Mention available skill names and when to use them; do not assume every agent recognizes every path or impose vendor-specific invocation syntax in shared instructions.
6. Validate Markdown links and changed paths. Report missing evidence and tests not run.

## Compatibility

When the repository contains DevConcord generation prompts, use `prompts/create-agents-md.md` and `prompts/create-reviews-md.md` as the detailed source of procedure. Otherwise follow the portable steps above without requiring the DevConcord repository.
