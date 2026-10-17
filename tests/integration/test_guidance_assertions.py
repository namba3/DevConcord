from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.integration.assertions import (
    HistoryValidationError,
    assert_changes_within,
    assert_idempotent,
    assert_issue_records_preserved,
    assert_markdown_links_resolve,
    assert_no_undefined_requirement_ids,
    assert_paths_unchanged,
    assert_provenance,
    assert_source_tree_unchanged,
    assert_validation_failure_kept_pending,
    check_forward_history,
    snapshot_git_state,
    snapshot_files,
)


class GitHistoryAssertionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.org")
        (self.repo / "base.txt").write_text("base\n", encoding="utf-8")
        self.base = self.commit("base")

    def git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def commit(self, message: str) -> str:
        self.git("add", ".")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def test_forward_and_same_commit_are_safe(self) -> None:
        (self.repo / "next.txt").write_text("next\n", encoding="utf-8")
        target = self.commit("next")

        self.assertEqual(check_forward_history(self.repo, self.base, target), "forward")
        self.assertEqual(check_forward_history(self.repo, target, target), "same")

    def test_older_target_and_diverged_history_are_distinguished(self) -> None:
        (self.repo / "next.txt").write_text("next\n", encoding="utf-8")
        target = self.commit("next")
        self.assertEqual(check_forward_history(self.repo, target, self.base), "behind")

        self.git("checkout", "-q", self.base)
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        diverged = self.commit("diverged")
        self.assertEqual(check_forward_history(self.repo, target, diverged), "diverged")

    def test_missing_baseline_and_target_stop_with_diagnostic(self) -> None:
        absent = "0" * len(self.base)

        with self.assertRaisesRegex(HistoryValidationError, "baseline commit is unavailable"):
            check_forward_history(self.repo, absent, self.base)
        with self.assertRaisesRegex(HistoryValidationError, "target commit is unavailable"):
            check_forward_history(self.repo, self.base, absent)

    def test_shallow_history_with_unknown_ancestry_is_incomplete(self) -> None:
        (self.repo / "next.txt").write_text("next\n", encoding="utf-8")
        target = self.commit("next")
        shallow_file = self.repo / ".git" / "shallow"
        shallow_file.write_text(f"{self.base}\n{target}\n", encoding="utf-8")

        self.assertEqual(check_forward_history(self.repo, self.base, target), "incomplete")

    def test_shallow_history_can_still_prove_a_backward_relation(self) -> None:
        (self.repo / "next.txt").write_text("next\n", encoding="utf-8")
        newer = self.commit("next")
        shallow_file = self.repo / ".git" / "shallow"
        shallow_file.write_text(f"{self.base}\n", encoding="utf-8")

        self.assertEqual(check_forward_history(self.repo, newer, self.base), "behind")


class AdoptionInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def make_source_repo(self) -> tuple[Path, str]:
        source = self.root / "source"
        source.mkdir()
        subprocess.run(["git", "-C", str(source), "init", "-q"], check=True)
        subprocess.run(
            ["git", "-C", str(source), "config", "user.name", "Test User"], check=True
        )
        subprocess.run(
            ["git", "-C", str(source), "config", "user.email", "test@example.org"],
            check=True,
        )
        (source / "docs").mkdir()
        (source / "docs/rule.md").write_text("# Rule\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(source), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(source), "commit", "-qm", "source"], check=True
        )
        sha = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return source, sha

    def test_snapshots_detect_only_unapproved_changes(self) -> None:
        original = self.root / "AGENTS.md"
        original.write_text("keep this\n", encoding="utf-8")
        before = snapshot_files(self.root)
        original.write_text("keep this\nwith an addition\n", encoding="utf-8")
        (self.root / "unexpected.txt").write_text("no\n", encoding="utf-8")
        after = snapshot_files(self.root)

        with self.assertRaisesRegex(AssertionError, "protected files changed"):
            assert_paths_unchanged(before, after, {"AGENTS.md"})
        with self.assertRaisesRegex(AssertionError, "unexpected changed paths"):
            assert_changes_within(before, after, {"AGENTS.md"})

    def test_reapplication_and_issue_records_are_checked(self) -> None:
        initial = {"docs/rules.md": b"rule\n"}
        assert_idempotent(initial, initial.copy())
        with self.assertRaisesRegex(AssertionError, "repeat application changed"):
            assert_idempotent(initial, {"docs/rules.md": b"rule\nextra\n"})

        before = "| ISS-0042 | Keep stable API | 対応中 |\n"
        assert_issue_records_preserved(before, before + "Additional notes\n")
        with self.assertRaisesRegex(AssertionError, "ISS-0042"):
            assert_issue_records_preserved(before, "| ISS-0042 | Keep stable API | 完了 |\n")
        with self.assertRaisesRegex(AssertionError, "duplicated"):
            assert_issue_records_preserved(before, before + before)

    def test_existing_project_fixture_preserves_issue_history(self) -> None:
        fixture = (
            Path(__file__).parent
            / "fixtures"
            / "existing-project"
            / "docs"
            / "issues.md"
        )
        before = fixture.read_text(encoding="utf-8")
        assert_issue_records_preserved(before, before + "\nAdditional context\n")
        changed_state = before.replace("対応中", "完了")
        with self.assertRaisesRegex(AssertionError, "ISS-0042"):
            assert_issue_records_preserved(before, changed_state)

    def test_failed_validation_cannot_advance_provenance(self) -> None:
        sha = "a" * 40
        assert_validation_failure_kept_pending("保留", sha, sha)
        with self.assertRaisesRegex(AssertionError, "failed validation"):
            assert_validation_failure_kept_pending("適用済み", sha, sha)
        with self.assertRaisesRegex(AssertionError, "failed validation"):
            assert_validation_failure_kept_pending("部分適用", sha, "b" * 40)

    def test_markdown_links_and_requirement_references_are_checked(self) -> None:
        (self.root / "index.md").write_text("[guide](guide.md)\n", encoding="utf-8")
        (self.root / "guide.md").write_text("# Guide\n", encoding="utf-8")
        assert_markdown_links_resolve(self.root)
        with self.assertRaisesRegex(AssertionError, "missing link target"):
            (self.root / "index.md").write_text("[missing](absent.md)\n", encoding="utf-8")
            assert_markdown_links_resolve(self.root)

        assert_no_undefined_requirement_ids({"task": {"REQ-0001"}}, {"REQ-0001"})
        with self.assertRaisesRegex(AssertionError, "REQ-0002"):
            assert_no_undefined_requirement_ids({"task": {"REQ-0002"}}, {"REQ-0001"})

    def test_provenance_requires_source_commit_paths_and_state_notes(self) -> None:
        source, sha = self.make_source_repo()
        source_before = snapshot_files(source)
        source_git_before = snapshot_git_state(source)
        assert_source_tree_unchanged(source_before, source, source_git_before)
        subprocess.run(
            ["git", "-C", str(source), "commit", "--allow-empty", "-qm", "unexpected"],
            check=True,
        )
        with self.assertRaisesRegex(AssertionError, "Git HEAD or worktree status changed"):
            assert_source_tree_unchanged(source_before, source, source_git_before)
        source_git_before = snapshot_git_state(source)
        destination = self.root / "project"
        (destination / "docs").mkdir(parents=True)
        (destination / "docs/rule.md").write_text("# Rule\n", encoding="utf-8")
        record = destination / "docs/guidance-provenance.md"
        record.write_text(
            f"""- 確認済み資料集コミット: `{sha}`

| 資料集のパス | 導入先のパス | 比較基準コミット | 状態 | 適用メモ・保留差分 |
|---|---|---|---|---|
| `docs/rule.md` | `docs/rule.md` | `{sha}` | 適用済み |  |
""",
            encoding="utf-8",
        )

        assert_provenance(record, source, destination, sha)

        record.write_text(
            f"""- 確認済み資料集コミット: `{sha}`

| 資料集のパス | 導入先のパス | 比較基準コミット | 状態 | 適用メモ・保留差分 |
|---|---|---|---|---|
| `docs/rule.md` | `docs/rule.md` | `{sha}` | 保留 | local rule conflicts |
""",
            encoding="utf-8",
        )
        assert_provenance(record, source, destination, sha)

        record.write_text(
            f"""- 確認済み資料集コミット: `{sha}`

| 資料集のパス | 導入先のパス | 比較基準コミット | 状態 | 適用メモ・保留差分 |
|---|---|---|---|---|
| `docs/rule.md` | `—` | — | 対象外 | Not applicable to project |
""",
            encoding="utf-8",
        )
        assert_provenance(record, source, destination, sha)

        record.write_text(
            f"""- 確認済み資料集コミット: `{sha}`

| 資料集のパス | 導入先のパス | 比較基準コミット | 状態 | 適用メモ・保留差分 |
|---|---|---|---|---|
| `docs/rule.md` | `docs/rule.md` | `{sha}` | 部分適用 |  |
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AssertionError, "needs a note"):
            assert_provenance(record, source, destination, sha)

        (source / "docs/rule.md").write_text("# Changed\n", encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "source files changed"):
            assert_source_tree_unchanged(source_before, source, source_git_before)


if __name__ == "__main__":
    unittest.main()
