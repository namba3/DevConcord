---
name: devconcord-compatibility-migration
description: >
  Assess compatibility and safe migration for changed public APIs, persisted
  or exchanged formats, protocols, configuration, schemas, and plugin
  contracts. Use when such a boundary actually changes.
---

# Compatibility & Migration

Apply this workflow to a real version boundary. Routine internal changes do
not need a migration plan; basic compatibility checks remain necessary when
an actual compatibility risk exists.

## Workflow

1. Identify affected consumers, producers, stored data, supported versions,
   deployment order, and the current compatibility promise. Separate public
   and internal contracts.
2. Classify the change (API/FFI, IPC/RPC, protocol, persisted data, config,
   database schema, plugin, client/server) and assess old/new combinations,
   mixed-version operation, downgrade, and unsupported-version behavior.
3. State invariants before and after migration, version detection, preconditions,
   atomicity, idempotency, interruption/partial progress, and failure reporting.
4. Compare expand/contract, in-place, offline, staged, or no migration options
   only where applicable. Define backup/restore and rollback limits; do not
   promise rollback after irreversible external effects or lossy conversion.
5. Specify a compatibility matrix and independent tests for old data/API,
   upgrade, restart/retry, interruption, rollback/downgrade, and rejection of
   unsupported versions as relevant. Use representative historical fixtures.
6. Connect implementation and deployment sequencing to existing ADRs, issue
   records, release planning, and verification. Report unknown consumer/version
   facts instead of inventing support guarantees.

## Boundaries

- `devconcord-design-replaceability` chooses dependency boundaries; this Skill
  handles version transition and migration safety.
- `devconcord-release-engineering` owns release-candidate/distribution
  evidence. This Skill supplies compatibility and migration conditions to it.
- Do not create a migration framework, compatibility layer, or data copy for
  hypothetical change. Match effort to an observed contract and impact.
- A breaking change or data-loss risk remains material even when this optional
  Skill is unavailable or not selected. Use the project's ordinary design,
  review, and verification process.

## Deliverable

State the changed boundary, compatibility matrix, invariants, rollout and
migration contract, interruption/retry/rollback limits, test evidence, owners
and sequencing assumptions, and unresolved risks.

## DevConcord References

Use `devconcord-reference` when available for requirements, ADR, robustness,
and release-checklist material. If the common Skill cannot be selected, run
the configured source checkout's CLI, one needed path per invocation:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-compatibility-migration \
  --path docs/work-management/templates/release-checklist.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread references were used. If a
required reference cannot be read, stop
dependent analysis; if it is optional, report the gap and continue only where
the result remains grounded.
