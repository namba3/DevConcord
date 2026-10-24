# Fixture issue register

All records below are synthetic evaluation data and do not belong to the DevConcord repository's own issue history.

## Issues

| ID | State | Work | Acceptance / evidence | Blocker or dependency |
|---|---|---|---|---|
| ISS-1001 | Blocked | Add an optional provenance field to the public export | Preserve REQ-1001/1002; tests must cover compatibility and path privacy | DEC-1001; requires product-owner approval |
| ISS-1002 | Blocked | Add a CLI option exposing export provenance | Preserve the existing CLI/output contract; do not reveal local paths | DEC-1001; requires product-owner approval |
| ISS-1003 | Ready | Clarify internal parser error messages and their documentation | Distinguish invalid input shape from missing `id` / `value`; keep exceptions free of raw input and filesystem paths; tests cover each failure; no public response, stored data, or configuration changes | No known blocker; recheck current code and tests |

## Open decisions

| ID | Question | Related Issue | State | Authority | Evidence / scope | Reconsideration condition |
|---|---|---|---|---|---|---|
| DEC-1001 | Should provenance be added through a versioned or opt-in export contract? | ISS-1001, ISS-1002 | 承認待ち | Product owner | ADR-1001, REQ-1001/1002; do not change current schema | Product owner provides explicit approval or rejects the proposal |

DEC-1001 is not an implementation Issue. A recommendation, the state `承認待ち`, and a HANDOFF entry are not approval. Resolving it would not automatically unblock either issue; each issue's remaining acceptance and safety conditions must be checked separately.
