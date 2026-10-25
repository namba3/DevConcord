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

The index includes one important-issue link to a real record heading. The
deterministic fixture unit tests exercise duplicate IDs across files, a stale
next counter, a missing index destination, an orphan inside the explicitly managed
`docs/issues/` directory, stale important-issue references, optional/undefined
tags, case-normalized duplicates, and five-digit IDs. These are deterministic
fixture checks; they do not prove historical ID non-use, branch coordination,
or real-agent search quality.
