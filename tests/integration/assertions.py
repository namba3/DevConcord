"""Reusable invariants for inspecting an AI-produced guidance update."""

from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path

from scripts import validate_docs


PROVENANCE_STATES = {"適用済み", "部分適用", "保留", "対象外"}
FULL_COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
ISSUE_ID = re.compile(r"ISS-\d{4,}")


class HistoryValidationError(ValueError):
    """A requested update cannot safely be compared using available Git history."""


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def check_forward_history(repo: Path, base_sha: str, target_sha: str) -> str:
    """Return same/forward/behind/diverged/incomplete or fail on unavailable history."""
    for label, sha in (("baseline", base_sha), ("target", target_sha)):
        if not FULL_COMMIT.fullmatch(sha):
            raise HistoryValidationError(f"{label} must be a full commit SHA")
        result = _git(repo, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        if result.returncode:
            if result.returncode == 1:
                raise HistoryValidationError(f"{label} commit is unavailable: {sha}")
            raise HistoryValidationError(
                f"Git could not verify {label} commit (exit {result.returncode})"
            )

    if base_sha == target_sha:
        return "same"

    shallow = _git(repo, "rev-parse", "--is-shallow-repository")
    if shallow.returncode:
        raise HistoryValidationError(
            f"Git could not determine whether history is shallow (exit {shallow.returncode})"
        )
    shallow_state = shallow.stdout.strip()
    if shallow_state not in {"true", "false"}:
        raise HistoryValidationError("Git returned an invalid shallow-history status")
    is_shallow = shallow_state == "true"

    forward = _git(repo, "merge-base", "--is-ancestor", base_sha, target_sha)
    if forward.returncode == 0:
        return "forward"
    if forward.returncode != 1:
        raise HistoryValidationError(
            f"Git ancestry check failed (exit {forward.returncode})"
        )

    backward = _git(repo, "merge-base", "--is-ancestor", target_sha, base_sha)
    if backward.returncode == 0:
        return "behind"
    if backward.returncode != 1:
        raise HistoryValidationError(
            f"Git reverse ancestry check failed (exit {backward.returncode})"
        )
    if is_shallow:
        return "incomplete"
    return "diverged"


def snapshot_files(root: Path) -> dict[str, bytes]:
    """Capture file contents and file type/mode while excluding Git metadata."""
    snapshot: dict[str, bytes] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            snapshot[relative.as_posix()] = b"SYMLINK\0" + str(path.readlink()).encode("utf-8")
        elif path.is_file():
            mode = stat.S_IMODE(path.stat().st_mode)
            snapshot[relative.as_posix()] = f"FILE:{mode:o}\0".encode() + path.read_bytes()
    return snapshot


def snapshot_git_state(repo: Path) -> tuple[str, str]:
    head = _git(repo, "rev-parse", "HEAD")
    if head.returncode:
        raise AssertionError(f"cannot read Git HEAD (exit {head.returncode})")
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode:
        raise AssertionError(f"cannot read Git worktree status (exit {status.returncode})")
    return head.stdout.strip(), status.stdout


def changed_paths(before: dict[str, bytes], after: dict[str, bytes]) -> set[str]:
    return {
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    }


def assert_paths_unchanged(before: dict[str, bytes], after: dict[str, bytes], paths: set[str]) -> None:
    changed = changed_paths(before, after) & paths
    if changed:
        raise AssertionError(f"protected files changed: {', '.join(sorted(changed))}")


def assert_changes_within(
    before: dict[str, bytes], after: dict[str, bytes], allowed_paths: set[str]
) -> None:
    unexpected = changed_paths(before, after) - allowed_paths
    if unexpected:
        raise AssertionError(f"unexpected changed paths: {', '.join(sorted(unexpected))}")


def assert_issue_records_preserved(before_text: str, after_text: str) -> None:
    def records(text: str) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue
            identifier = line.strip().strip("|").split("|", maxsplit=1)[0].strip().strip("`")
            if ISSUE_ID.fullmatch(identifier):
                result.setdefault(identifier, []).append(line.strip())
        return result

    before_records = records(before_text)
    after_records = records(after_text)
    missing_ids = set(before_records) - set(after_records)
    changed = [
        identifier
        for identifier, rows in before_records.items()
        if rows != after_records.get(identifier, [])
    ]
    if missing_ids or changed:
        affected = sorted(missing_ids | set(changed))
        raise AssertionError(
            f"existing issue records were changed, removed, or duplicated: {', '.join(affected)}"
        )


def assert_markdown_links_resolve(root: Path) -> None:
    root = root.resolve()
    markdown = sorted(
        path
        for path in root.rglob("*.md")
        if not {".git", "node_modules"}.intersection(path.relative_to(root).parts)
    )
    previous_root = validate_docs.ROOT
    try:
        validate_docs.ROOT = root.resolve()
        errors = validate_docs.check_links(markdown)
    finally:
        validate_docs.ROOT = previous_root
    if errors:
        raise AssertionError("unresolved Markdown links:\n" + "\n".join(errors))


def assert_idempotent(first: dict[str, bytes], second: dict[str, bytes]) -> None:
    changed = changed_paths(first, second)
    if changed:
        raise AssertionError(
            f"repeat application changed files: {', '.join(sorted(changed))}"
        )


def assert_source_tree_unchanged(
    before_files: dict[str, bytes],
    source_repo: Path,
    before_git_state: tuple[str, str],
) -> None:
    changed = changed_paths(before_files, snapshot_files(source_repo))
    if changed:
        raise AssertionError(f"source files changed: {', '.join(sorted(changed))}")
    if before_git_state != snapshot_git_state(source_repo):
        raise AssertionError("source Git HEAD or worktree status changed")


def assert_provenance(
    record: Path, source_repo: Path, target_root: Path, expected_source_sha: str
) -> None:
    try:
        text = record.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise AssertionError(f"cannot read provenance ({type(error).__name__})") from error
    expected_header = [
        "資料集のパス",
        "導入先のパス",
        "比較基準コミット",
        "状態",
        "適用メモ・保留差分",
    ]
    header = next(
        (line for line in text.splitlines() if all(item in line for item in expected_header)),
        None,
    )
    if header is None:
        raise AssertionError("provenance table is missing required columns")
    columns = [cell.strip().replace("`", "") for cell in header.strip().strip("|").split("|")]
    column_index = {name: columns.index(name) for name in expected_header}
    rows = [
        [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()[text.splitlines().index(header) + 1 :]
        if line.strip().startswith("|") and not re.fullmatch(r"[|:\-\s]+", line.strip())
    ]
    if not rows:
        raise AssertionError("provenance table has no material records")
    if expected_source_sha and not FULL_COMMIT.fullmatch(expected_source_sha):
        raise AssertionError("expected source commit must be a full SHA")
    for row in rows:
        if len(row) < len(columns):
            raise AssertionError("provenance row has fewer cells than its header")
        source_path = row[column_index["資料集のパス"]]
        target_path = row[column_index["導入先のパス"]]
        baseline = row[column_index["比較基準コミット"]]
        state = row[column_index["状態"]]
        note = row[column_index["適用メモ・保留差分"]]
        if state not in PROVENANCE_STATES:
            raise AssertionError(f"invalid provenance state for {source_path}: {state}")
        if state == "対象外":
            if baseline != "—" or not note:
                raise AssertionError(f"excluded material needs a reason and no baseline: {source_path}")
            continue
        if not FULL_COMMIT.fullmatch(baseline):
            raise AssertionError(f"provenance baseline must be a full SHA: {source_path}")
        baseline_object = _git(
            source_repo, "rev-parse", "--verify", "--quiet", f"{baseline}^{{commit}}"
        )
        source_object = _git(source_repo, "cat-file", "-e", f"{baseline}:{source_path}")
        if baseline_object.returncode or source_object.returncode:
            raise AssertionError(f"provenance source or baseline is unavailable: {source_path}")
        if state in {"部分適用", "保留"} and not note:
            raise AssertionError(f"partial or held material needs a note: {source_path}")
        if state == "適用済み":
            destination = (target_root / target_path).resolve()
            try:
                destination.relative_to(target_root.resolve())
            except ValueError as error:
                raise AssertionError(f"provenance target escapes project: {target_path}") from error
            if not destination.is_file():
                raise AssertionError(f"applied material is missing: {target_path}")
    recorded_commit = re.search(
        r"^\s*-\s*確認済み資料集コミット:\s*`?([0-9a-f]{40}|[0-9a-f]{64})`?\s*$",
        text,
        flags=re.MULTILINE,
    )
    if expected_source_sha and (
        recorded_commit is None or recorded_commit.group(1) != expected_source_sha
    ):
        raise AssertionError("provenance's checked source commit does not match the inspected source")


def assert_no_undefined_requirement_ids(task_to_ids: dict[str, set[str]], defined_ids: set[str]) -> None:
    undefined = {
        requirement_id
        for requirement_ids in task_to_ids.values()
        for requirement_id in requirement_ids - defined_ids
    }
    if undefined:
        raise AssertionError(
            f"task references undefined requirement IDs: {', '.join(sorted(undefined))}"
        )


def assert_validation_failure_kept_pending(
    state: str, baseline_before: str, baseline_after: str
) -> None:
    if state == "適用済み" or baseline_before != baseline_after:
        raise AssertionError(
            "failed validation must not mark material applied or advance its baseline"
        )
