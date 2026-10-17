# Small CLI design input

- Project: Log Triage
- Platform: Rust CLI on supported current Linux and Windows environments.
- Build: Cargo.
- Scope: Create a CLI that filters newline-delimited log records by severity and writes matching records to stdout.
- Input contract: Read UTF-8 from a named file or stdin. Malformed records are reported with line numbers to stderr; processing continues for later records and exits non-zero if any record is invalid.
- Performance: Process input as a stream; do not load the entire file into memory. No numeric latency target is specified.
- Robustness: A read error is reported and does not produce a success exit status.
- Initial bootstrap scope: Development foundation and minimal executable skeleton only; filtering behavior is a later feature.
- UI: CLI only. No graphical interface is required.
