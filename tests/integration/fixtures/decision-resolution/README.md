# Decision Resolution evaluation fixture

This is a disposable behavioral-evaluation fixture, not a DevConcord issue or production API. Copy the entire directory to separate fresh worktrees for each evaluation arm. The initial state is the checked-out fixture commit; record its full SHA before running an agent.

Contents:

- `docs/requirements.md`: stable public export and privacy requirements.
- `docs/parser.md`: current internal parser input/error contract, which ISS-1003 may clarify.
- `docs/adr.md`: an existing approved decision that is relevant but does not approve the proposed contract change.
- `docs/issues.md`: two issues sharing an approval-gated DEC and one independent issue.
- `docs/risks.md`: future residual risk with a linked mitigation task.
- `docs/handoff.md`: checkpoint evidence tied to the initial fixture state.
- `src/exporter.py` and `tests/test_exporter.py`: the current public export implementation and baseline contract check.
- `src/parser.py` and `tests/test_parser.py`: a small internal parser with deliberately broad baseline errors for ISS-1003.

The `tests/integration/README.md` section “Controlled before/after fixture and prompts” gives the paired prompts, equal budget, checkpoint/resume setup, evidence capture, and rubric. To invalidate one piece of checkpoint evidence, edit `src/exporter.py` or `tests/test_exporter.py` in the resume copy; to model an unrelated change, edit a separate unused documentation path. Record exact diffs and hashes. Do not alter the source fixture between paired runs.
