# Federated Issue Register fixture

This disposable fixture provides deterministic expected records for manual
evaluation of cross-register issue discovery and optional multi-tag filtering.
It is not a runtime implementation or an agent-execution result.

## Expected exact-tag intersections

| Query | Expected issue IDs |
|---|---|
| `ARCH` AND `REL` | `ISS-0125` |
| `SEC` AND `QA` | `ISS-0129` |
| `QA` AND `OPS` | `ISS-0127` |

`ISS-0130` is deliberately untagged and remains a valid issue. The main index
contains links and the global next ID only; issue status and details are
canonical in the linked subregisters.
