# Gap Analysis Report Format

Use this as a flexible report contract for `devconcord-gap-analysis`. Keep the
report proportionate to the assessment scope; omit empty sections and fields
that do not apply. Do not invent IDs, metrics, evidence, or prior findings to
fill a template.

```markdown
# DevConcord Gap Analysis Report

## 1. Assessment overview

- Target repository and commit:
- Working-tree state:
- Date:
- Mode: Full / Incremental
- Scope and exclusions:
- DevConcord source identity and reference commit(s):
- Criteria documents actually read:
- Checks actually run:
- Constraints and unassessed areas:

## 2. Executive summary

- Overall assessment and confidence:
- Strengths:
- Highest-impact gaps:
- Residual risks and recommended first actions:

## 3. Area assessment

| Area | Applicability | State | Evidence | Main gap or reason |
|---|---|---|---|---|

## 4. Prioritized findings

### GAP-001: <short title>

- Type: confirmed defect / design gap / verification gap / documentation gap /
  improvement opportunity / unresolved question
- Priority: use the target's existing scale when available
- Assessment state: conforms / partially conforms / gap / not applicable /
  not assessed
- Applicable principle(s):
- Current and expected state:
- Evidence: paths, symbols, lines, tests, CI, IDs, and commit as verified
- Impact and triggering conditions:
- Recommendation and alternatives, including whether no change is reasonable:
- Approximate cost and dependencies:
- Acceptance conditions:
- Verification method and evidence still needed:
- Related REQ / ADR / issue / risk IDs:
- Confidence and limitations:

## 5. Improvement roadmap

| Order | Improvement candidate | Expected value | Cost/dependency | Acceptance or verification | Existing record |
|---|---|---|---|---|---|

## 6. Strengths and evidence of conformance

## 7. Unassessed areas and residual risks

## 8. Checks performed and results

## 9. Items for the next assessment
```

`GAP-001` and similar labels are local report references only. These local GAP
labels do not replace formal issue IDs. Do not create a DevConcord-specific numerical score
or quality axis. If the user requests a completion assessment or the target's
established workflow requires one, use the target's rules and, when applicable,
the existing DevConcord ten-axis weighted system with its `N/A`, `未評価`,
confidence, and formal/provisional distinctions. Report known limitations
even when no score is requested.
