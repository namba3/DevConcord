
# Release Engineering

Support an explicit release, candidate, distribution, installation, update,
rollback, or post-release task. `docs/work-management/templates/release-checklist.md`
is the canonical checklist; do not copy it into another ledger.

## Workflow

1. Confirm the requested release target, supported platforms, artifact and
   channels, version, authorized operations, approver, and release checklist.
   Treat missing policy or authority as unresolved.
2. Collect evidence by stage and artifact identity: source revision, build
   configuration, CI, reproducibility if required, artifact hashes/integrity,
   platform coverage, install/update/rollback, release notes, and post-release
   observations. Apply SBOM, signature, checksum, and provenance controls
   where policy or risk requires them.
3. Distinguish CI success, build success, artifact generation, integrity
   verification, installation, update, runtime behavior, requirement
   fulfillment, and release approval. Evidence at one stage does not imply a
   later stage passed.
4. Verify the actual artifact and supported environment for each claimed path.
   Record tests not run, environment mismatch, residual risks, and evidence
   freshness against the candidate revision/artifact.
5. Assess upgrade, rollback, downgrade, recovery, and post-release checks using
   compatibility/migration contracts where relevant. Do not claim recoverability
   without exercising or otherwise independently verifying the path.
6. Present evidence, gaps, residual risk, and a recommendation to the
   authorized approver. Never publish, distribute, sign, alter a release, or
   approve it unless explicitly authorized for that operation.

## Boundaries

- Ordinary implementation iterations do not require release readiness,
  SBOM generation, signing, or distribution tests on every change.
- Development Orchestration may suggest this workflow from Stabilize when release
  work is relevant; suggestion is not an automatic handoff or approval.
- Reuse existing checklist, requirements, issue records, CI, and artifact
  systems. Do not add a duplicate release checklist or quality score.
- A successful CI or build does not prove installability, runtime support, or
  user acceptance.

## Deliverable

Report target and candidate identity, stage-by-stage evidence, platform and
artifact coverage, unverified paths, residual risk, requested approval and
approver, and the next safe action. Keep recommendation separate from release
authorization.

## DevConcord References

Use `devconcord manage reference` when available to read the canonical checklist and
only relevant project requirements/operational guidance. If the Reference workflow
cannot be selected, run the configured source checkout's CLI:

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/work-management/templates/release-checklist.md \
  --revision installed
```

For Project Scope, also pass `--scope project --target <target-repository>`.
Do not silently switch revisions or claim unread material was applied. If a
required reference cannot be read, stop
the dependent evaluation; if it is optional, report the gap and continue only
where evidence remains sufficient.
