---
name: devconcord-dependency-governance
description: >
  Evaluate adoption, update, replacement, removal, or material risk of
  external packages, services, build tools, and runtime dependencies. Use
  when dependency decisions or risks are in scope.
---

# Dependency Governance

Make dependency decisions from project value, lifecycle, and evidence. An
available update is not automatically the best choice.

## Workflow

1. Identify the dependency, direct/transitive role, affected targets, current
   version/source, actual use, owner, and the decision being requested.
2. Gather current evidence proportionate to impact: maintenance and release
   health, supported platforms/runtimes, API stability, known vulnerabilities,
   license and obligations, provenance/supply-chain controls, performance,
   dependency graph complexity, and alternatives. Record source and date for
   volatile claims; do not infer security from version recency alone.
3. Compare keep, patch, update, replace, reduce use, remove, or accept risk.
   Include user value, migration cost, compatibility, test burden, operational
   and security impact, and reversibility. Do not recommend a change without
   checking the actual dependency contract and consumers.
4. For a selected change, connect version/API/data migration to
   `devconcord-compatibility-migration` when material, and connect significant
   assets/threats or dependency boundaries to Security/Replaceability
   contracts. These are conditional specialist workflows, not automatic
   dependencies.
5. Define verification from the decision: build/test matrix, vulnerability or
   license evidence, runtime/platform checks, performance comparison, and
   rollback or lockfile reproducibility as relevant. Separate proposed checks
   from checks actually run.
6. Record the decision and follow-up in existing ADR/issue/risk records. Do not
   create a parallel dependency inventory unless the project already uses one.

## Boundaries

- If dependencies are unchanged and no material dependency risk is in scope,
  do not require detailed dependency analysis for routine development.
- Security by Design owns assets, threats, and security invariants;
  Replaceability by Design owns dependency boundaries. This Skill compares
  dependency lifecycle choices without copying those detailed workflows.
- Use current authoritative sources for vulnerability, license, release, and
  support status. Unverified or inaccessible sources remain unknown.
- A serious discovered risk requires a proportionate response even if this
  Skill is unavailable or not used. Optionality does not excuse ignoring it.

## Deliverable

State the decision and dependency scope, evidence sources/date, options and
tradeoffs, compatibility/security/performance consequences, chosen verification
and results, unresolved uncertainty, and existing record references.

## DevConcord References

Use `devconcord-reference` when available for security, replaceability,
requirements, ADR, and issue/risk guidance. If the common Skill cannot be
selected, use the configured source checkout directly, one needed path at a
time:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-dependency-governance \
  --path docs/common/ai-assisted-development.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a
required reference cannot be read, stop
the dependent decision; if it is optional, report the gap and continue only
where evidence remains sufficient.
