# Observability & Diagnostics Workflow

This workflow is distributed with `devconcord-observability-design`. Apply the
target's actual requirements, platform contracts, privacy rules, security
controls, and operational practices. Select only the depth needed by the
system's purpose, scale, data sensitivity, failure impact, and support model.

## 1. Establish context and users

1. Read applicable `AGENTS.md`, `REVIEW.md`, existing requirements, ADRs,
   architecture, issue/risk records, implementation, tests, CI, deployment and
   support guidance. Record the starting Git state and protect unrelated work.
2. Identify who needs to understand behavior: end users, developers, support,
   operators, incident responders, or auditors. Identify their actual tasks
   and access boundaries; do not assume all audiences should see the same data.
3. Map important operations, state transitions, external dependencies, async
   boundaries, failure contracts, recovery paths, and current diagnostics.
   Distinguish existing behavior from a proposed design and unknowns.
4. Check applicable privacy, security, retention, regulatory, deployment,
   offline, and resource constraints. Do not infer remote collection, consent,
   or access rights from the presence of a logging library.

## 2. Define diagnostic questions

For each important operation or state, choose questions that matter to its
users or operators. Where relevant, answer:

- What operation or state transition occurred, and where?
- When did it occur and how long did it take?
- Which safe operation/correlation context connects related events?
- What failed, with what category/cause, and what was affected?
- Was the outcome partial, retried, cancelled, recovered, or left for manual
  intervention?
- What user-visible consequence or next action is appropriate?
- What necessary evidence is missing, and which safe reproduction or support
  path could fill the gap?

Do not require every question for every subsystem. A diagnostic signal narrows
investigation; it cannot prove a root cause unless the evidence supports that
conclusion. Preserve uncertainty rather than guessing from a generic error.

## 3. Select proportionate signals

Choose among user-facing errors, structured events/logs, metrics, traces,
health/state endpoints, diagnostic reports, and audit records only where they
answer a defined question. A system may need one or none of these mechanisms
beyond its existing interface.

Examples of scale-appropriate choices:

- **Small CLI:** stable error categories, actionable safe messages, and
  meaningful exit codes may be enough. Do not add a monitoring service.
- **Desktop application:** separate user guidance from developer diagnostics;
  consider local bounded logs or an explicitly reviewed diagnostic export.
  Distinguish local collection from remote sending.
- **Background service:** consider operation outcomes, queue/backlog,
  dependency health, resource use, and error/latency measurements tied to
  operator decisions.
- **Distributed system:** use request/operation/correlation IDs and distributed
  traces only where they connect real cross-process causal paths.
- **Library:** return stable, useful errors or diagnostics through its API;
  avoid unexpected output, global logging configuration, or telemetry.

Do not mandate OpenTelemetry, a cloud vendor, a central logging backend,
continuous profiling, SLI/SLO, or remote telemetry without a product or
operational requirement and a justified cost/benefit decision.

## 4. Define signal semantics

### Structured events and logs

When logs are warranted, decide which event needs to exist, its stable event
name or ID, severity, component/operation, outcome, safe error category,
timestamp, and useful context. Add duration, count, state transition, or
correlation fields only when they answer a question. Use structured fields
where automated filtering matters; do not make consumers parse prose or exact
message wording as a stable API.

Use wall-clock time for cross-system event time and a monotonic clock for
elapsed duration. Clarify timestamp format, precision, and clock assumptions
where comparisons matter. Choose levels consistently. Avoid repeated logging
of the same propagated failure, routine success spam, unbounded per-item
output, and important events buried in low-value noise. Bound or aggregate
high-frequency signals where appropriate without dropping evidence required
for safety, security, or audit obligations.

### Metrics

For each metric, state its decision/use, meaning, unit, aggregation, observed
population, and update window. Examine label dimensions for unbounded
cardinality and sensitive values. Track latency, throughput, errors, retries,
resource use, queue depth, cache behavior, startup, or recovery time only when
relevant. SLI/SLO targets need a stated user/operational requirement and
baseline; do not invent target values or equate metric count with quality.

### Traces and correlation

Use traces when causal flow crosses meaningful boundaries, such as async tasks,
processes, network services, or background work. Define propagation and parent
operation semantics, including retry/cancel behavior, only as needed. A local
operation ID can be enough for a single process. IDs are not authorization,
authentication, or secrets; consider guessability and trust boundaries before
accepting externally supplied IDs. Do not attach raw user input or credentials
to spans.

### Errors and diagnostics

Separate the user's safe explanation and next step from developer/operator
details. Where useful, preserve typed error category, cause chain, source
operation, safe OS/dependency error code, retryability, recovery outcome, and
operation ID. Do not leak paths, internals, personal data, or secrets merely to
make an error detailed. Avoid duplicate reporting across layers and fragile
log-text parsing.

## 5. Minimize and protect diagnostic data

Treat emitted, buffered, persisted, exported, attached to crash dumps, and
remotely sent diagnostics as data flows with their own trust boundaries.

- Collect only fields tied to a defined diagnostic or audit need. Prefer an
  allowlist of safe context over collecting broad input and relying on
  blacklists, masking, or anonymization later.
- Exclude passwords, API keys, access/refresh tokens, cryptographic material,
  file contents, and unnecessary personal data. Review paths, usernames,
  request bodies, query strings, exception text, labels, and user-controlled
  strings for sensitive values and log injection.
- Define access controls, storage location, retention, rotation, deletion,
  diagnostic bundle review, and whether information leaves the device or
  service. Remote telemetry requires product requirements, appropriate
  disclosure/choice and authorization, and applicable legal review; it is
  never implied by this Skill.
- Separate audit records from debug/operational logs when their integrity,
  access, or retention requirements differ. Ordinary logs are not an audit
  trail by default.
- Verify the data at boundaries and in tests/reports without copying real
  secrets or personal data into fixtures. Redaction is defense in depth, not a
  guarantee that collected data is safe.

For relevant security or credential changes, consult Security by Design and
Secrets by Design. Do not duplicate their threat or credential lifecycle
workflows.

## 6. Design signal failure and cost

Treat the observability pipeline as a dependency with bounded resources and
failure behavior. Decide as needed:

- What happens when a local file, remote backend, or exporter is unavailable?
- Can the product operation proceed, degrade, or fail safely? Which critical
  records must be surfaced if they cannot be written?
- What queue/buffer size, backpressure, rate limit, aggregation, or sampling is
  justified? How is loss or truncation visible?
- How do rotation, disk-full, shutdown, crash, concurrency, and restart affect
  pending data and application state?
- What CPU, memory, storage, network, and latency overhead is acceptable, and
  how will it be measured on representative workloads?

Avoid making a noncritical logging failure break user work, while preserving
explicit handling where security/audit obligations require delivery. Do not
promise complete event retention, exactly-once delivery, or zero overhead
without evidence. Keep buffers and labels bounded. Sample or suppress only
where it preserves the evidence required by the operation's contract.

Use `devconcord-design-robustness` for the primary operation's failure,
consistency, and recovery contract and `devconcord-design-performance` for
workload and measurement design; this workflow covers the additional
observability consequences.

## 7. Define acceptance and verification

Derive acceptance conditions from the diagnostic questions and data/operation
contracts. Select only relevant checks, such as:

- event names, levels, field types, units, timestamps, correlation propagation,
  and metric aggregation;
- expected signal for normal completion, classified failure, retry,
  cancellation, partial success, and recovery;
- absence of secrets, personal data, unsafe paths, injection, and unexpected
  remote transmission;
- access, export review, retention, rotation, deletion, or audit-integrity
  behavior where required;
- bounded memory/disk/queue growth and acceptable overhead under representative
  load;
- behavior when the sink/exporter fails, disk fills, process exits, or events
  are dropped.

Use unit/contract tests, fault injection, integration checks, privacy scans,
load measurements, or operational exercises as justified. A test's existence,
execution, result, and covered condition are distinct. Verify instrumentation
without treating the instrumented behavior as proof of the underlying
business requirement. Report uncovered environments and failure modes.
When fault injection or a reproducible failure is available, exercise the
diagnostic path and verify expected context survives redaction, transport,
storage, and resource limits. Separate an unexecuted scenario from a
successful diagnosis; do not require fault injection without a meaningful
failure condition or safe harness.

## 8. Use existing records and report

Place requirements, design decisions, tests, operation guidance, and known
work in their existing sources of truth. Link signal requirements to relevant
REQ/NFR/ADR/ISSUE IDs where useful. Do not create a new quality axis,
observability score, issue list, or risk ledger. Reflect observability effects
in existing reliability, maintainability, security, performance, and release
readiness axes only when distinct evidence supports those effects; do not
double-count one finding.

Report the target questions/users, selected and excluded mechanisms with
reasons, data and trust boundaries, event/metric/trace/error semantics,
failure/cost behavior, acceptance and checks, assumptions, residual risks,
and what remains unverified. Distinguish measured results from design intent,
generated diagnostics from successful diagnosis, and local observation from
remote collection.

## 9. Scenario review

Use these contrasting scenarios to check proportionality; they are not fixed
implementation recipes:

| Scenario | Design question |
|---|---|
| Rust desktop image conversion | Can the user understand what to do, while a safe operation ID, error chain, local diagnostic log, or reviewed report provides enough context to investigate without leaking image data or personal paths? |
| Media server | Which request, conversion, background scan, and network signals help operators identify queueing, latency, dependency failures, retries, and recovery? Are metric labels and tracing bounded? |
| Encrypted storage | Can mount, I/O, partial-write, integrity, and recovery outcomes be distinguished without logging keys, file contents, or sensitive paths? Are diagnostics consistent with recovery and audit contracts? |
| Small CLI | Are categorized errors, actionable output, and exit codes sufficient, without adding an unnecessary monitoring or telemetry stack? |

Evaluate whether the chosen evidence answers a real diagnostic question, is
safe and proportionate, has a defined failure contract, and can be verified.
Do not require particular wording, tools, or signals when another design meets
the stated need.
