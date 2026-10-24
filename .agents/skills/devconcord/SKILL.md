---
name: devconcord
description: Use DevConcord workflows for software design, bounded development, decision resolution and unblocking, repository review, verification, diagnosis, quality design, lifecycle decisions, guidance management, and agent evaluation. Route explicit devconcord commands or natural-language requests to the smallest relevant internal workflow while preserving user authority and project contracts.
---

# DevConcord Unified Skill

DevConcord provides evidence-driven, risk-proportional workflows for software design, development, verification, quality, lifecycle, and repository guidance. This is the sole public DevConcord Skill. Specialized procedures live in internal Markdown modules and are not separately discoverable Skills.

## Route the request

Interpret `devconcord <area> <intent>` as a portable instruction to select the matching workflow below. It is not an operating-system command or a vendor-specific slash command. Natural-language requests use the same routing. Normalize clear spelling variants and unambiguous abbreviations; unknown commands should be reported with the nearest supported choices. Ask a concise clarification only when target, desired outcome, or authority materially changes the work. For mixed requests, choose one primary workflow and load only needed specialist modules.

Read [routing.md](references/routing.md) for the complete command map, natural-language routing, and ambiguity rules. Read [shared-contracts.md](references/shared-contracts.md) before material changes or when a shared safety contract is relevant. Then load the selected module at `references/modules/<area>/<legacy-id>/module.md`; legacy IDs here are internal file identifiers, not public Skills.

## Risk-Proportional Workflow Selection

Understand the request, assess material risks, select a primary workflow, add only relevant specialist modules, choose verification depth, execute within the granted authority, then reassess when evidence or risk changes. Do not read every module for routine work, equate module count with quality, or treat uncertainty as low risk. Module selection never expands permission. Basic compatibility, data protection, and security checks remain necessary whenever the change creates those risks.

The internal Compatibility Migration (`devconcord-compatibility-migration`), Release Engineering (`devconcord-release-engineering`), and Dependency Governance (`devconcord-dependency-governance`) workflows are optional. Consider them only for actual compatibility boundaries, release/distribution work, or dependency decisions/material risks. Their non-use is not a defect. Do not ignore a material risk because the specialist workflow is optional.

## Authority and completion

A workflow recommendation or explicit command does not itself authorize edits, external operations, publication, approval, or Git history changes. Follow the user's scope and repository instructions. Reviews, plans, and diagnosis are read-only unless the request separately authorizes changes. Preserve unrelated work. Do not commit, push, release, or rewrite history unless requested. Report verification evidence and unverified boundaries accurately; stop at approval gates, unresolved material decisions, unsafe state, or exhausted user-defined/finite work budgets.

## Version-pinned references

When installed-version documentation is needed and the CLI/source is available, use the package identity `devconcord`:

```sh
python3 /configured/source_root/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

Run the CLI from the registered local DevConcord source checkout, using its absolute path; the placeholder above is explanatory. The current project working directory does not need to contain DevConcord. For Project Scope, also pass `--scope project --target <target-repository>`. Use the documented source configuration and scope options for the actual environment. If the source checkout is unavailable or not configured, stop the dependent reference task and report how to register or restore it. Do not silently substitute HEAD, the working tree, another package revision, or online content when installed-reference validation fails. The [management module](references/modules/management/devconcord-reference/module.md) describes the reference contract.
