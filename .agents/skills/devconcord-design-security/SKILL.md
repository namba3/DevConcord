---
name: devconcord-design-security
description: >
  DevConcord security design workflow for identifying relevant assets, trust
  boundaries, threats, security invariants, proportionate controls, and
  verification, including credential lifecycle and secretless options. Use when
  a change introduces or alters security-sensitive data, privileges, external
  inputs, dependencies, deployment, or attack surfaces.
---

# Security by Design

Use this workflow for design and change planning. Scale the analysis to the affected assets, attack surface, and impact. A small local change may need only a brief scope decision; a changed trust boundary, privileged operation, sensitive data flow, or high impact failure needs explicit threat analysis. Do not claim certification, complete threat coverage, or security from a passing test suite.

## Workflow

1. **Set scope and assumptions.** Identify the feature/change, affected users and operators, deployment context, assets, data sensitivity, security objectives, and what is out of scope. State assumptions and unknowns instead of inventing requirements.
2. **Map boundaries and flows.** Mark trust boundaries, actors, entry and exit points, commands/data flows, privileged components, external services, build/update paths, and dependencies. Include local IPC, files, plugins, AI tools/models, and operator interfaces when relevant.
3. **Select plausible threats.** Consider attacker capabilities and access, misuse/abuse cases, attack paths, and impact to confidentiality, integrity, availability, privacy, and safety. Prioritize scenarios that change design decisions; do not enumerate threats without a decision purpose.
4. **Define security requirements and invariants.** Express required authentication/authorization, least privilege, safe defaults, validation/encoding, isolation, rate/resource limits, auditability, and data lifecycle controls only where justified. State forbidden outcomes, failure behavior, and acceptance criteria in observable terms.
5. **Choose proportionate controls.** Reduce unnecessary attack surface and retained data; use defense in depth at relevant boundaries. Consider dependency provenance/update paths, secrets and key lifecycle, logging/telemetry, and recovery. Do not mandate encryption, authentication, abstractions, or a particular scanner without a threat, requirement, or deployment basis.
   When credentials are involved, first consider whether the application can avoid managing a long-lived secret (長期秘密). Identify the principal and bootstrap trust, distinguish authentication from authorization, and compare identity/federation, short-lived or dynamic credentials, brokered access, and protected storage against the actual provider and runtime. For detail, request `docs/application-design/secrets-by-design.md` through `devconcord-reference`; scale this analysis to the change and do not require specific infrastructure.
6. **Plan independent verification.** Connect each important invariant to suitable review, unit/integration/negative tests, static or dynamic analysis, dependency/secrets/configuration scanning, deployment checks, or manual assessment. Record scope, tool/version/configuration, exceptions, and untested areas. A scanner or test covers only its stated scope.
7. **Record decisions and residual risk.** Use existing requirements (`REQ`/`NFR`), ADRs, risk records, and issue register. Track implementation, investigation, and verification work in the existing issue register. Do not create a second security ledger or quality score. Revisit analysis when assets, boundaries, dependencies, deployment, or threat assumptions change.

## Compare security requirements with implementation evidence

When assessing an existing change or security posture, trace material threat
scenarios to the security requirement or invariant, the intended control, its
implementation and configuration, and evidence that exercises it. Select
only threats relevant to the changed assets, trust boundaries, deployment,
and attacker capabilities. Check where responsibility is enforced, how
failure or denial is observed, and whether a negative test exercises the
relevant boundary rather than a mock that bypasses it.

Report each link's status separately: **required**, **designed**,
**implemented/configured**, **test or analysis present**, **executed and
passed/failed**, and **adequately verified for the stated threat**. These
statuses are not interchangeable. A control described in an ADR is not
implementation evidence; a test file is not an executed result; a passing
scanner or negative test covers only its stated scope and configuration.
Identify missing links, exceptions, test environment limits, and residual
risks without treating unknowns as safe or claiming complete threat coverage.

Use `devconcord-test-design` when independent security test cases or expected
denial behavior need dedicated design. Keep this Skill focused on threat
scenarios, controls, and security invariants; use Repository Review for
concrete code defects and do not turn this into a general-purpose code review.

## Completion

For each material change, report the assets and relevant boundaries, selected threats or reason for limited analysis, requirements/invariants, chosen controls and tradeoffs, verification evidence and limits, and residual risks or follow-up issue IDs. When security analysis is not applicable, state the change facts supporting that decision.

## DevConcord References

Use `devconcord-reference` when available. Identify this Skill as the requester and request only the paths needed for the current design:

- `docs/common/ai-assisted-development.md`
- `docs/application-design/templates/requirements.md`
- `docs/application-design/templates/adr.md`
- `docs/application-design/secrets-by-design.md` (when credentials, identity, or secret lifecycle are in scope)
- `docs/work-management/risk-management.md`
- `docs/work-management/issue-tracking.md`

If the common Skill cannot be selected, run the configured source checkout's reference CLI directly, using this Skill's name as `--skill`. The CLI accepts one reference path per invocation, so run it separately for each needed path:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-design-security \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

For a Project Scope installation, also pass `--scope project --target <target-repository>`. Do not silently switch revisions or claim unread material was applied. If a required reference cannot be read, stop; if it is optional, report the failure and continue this self-contained workflow.

## References

These official sources are starting points, not blanket conformance claims. Select material that fits the product, architecture, and threat model; verify versions when using it as a formal requirement.

- [CISA et al., Secure by Design software guidance](https://www.cisa.gov/sites/default/files/2023-10/Shifting-the-Balance-of-Cybersecurity-Risk-Principles-and-Approaches-for-Secure-by-Design-Software.pdf)
- [NIST Secure Software Development Framework (SSDF)](https://csrc.nist.gov/Projects/ssdf/publications)
- [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- [MITRE Common Weakness Enumeration (CWE)](https://cwe.mitre.org/)
