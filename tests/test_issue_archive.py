"""Issue archive CLI and validator regression tests."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from scripts import manage_issue_archive as archive
from scripts import validate_docs


ROW_HEADERS = "| ID | 分類 | タグ（任意） | 優先度 | 状態 | 課題・影響 | 完了条件 | 根拠・検証 | 完了日 |\n"
ROW_SEPARATOR = "|---|---|---|---|---|---|---|---|---|\n"
DONE = "| ISS-0001 | QA | — | P2 | 完了 | 既存問題 | 動作確認 | tests passed | 2026-01-01 |\n"
OPEN = "| ISS-0002 | QA | — | P3 | 未着手 | 次の問題 | tests | evidence | — |\n"


class IssueArchiveTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.active = self.root / "issues.md"
        self.archive = self.root / "issues/archive"
        self.active.write_text(
            "# Issue Register\n\n## 共通ISS採番\n\n- 次の未割当番号: ISS-0003\n\n"
            "## 課題一覧\n\n" + ROW_HEADERS + ROW_SEPARATOR + DONE + OPEN,
            encoding="utf-8",
        )

    def cli(self, *args):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = archive.main(["--issue-register", str(self.active), "--archive-dir", str(self.archive), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_inspect_and_dry_run_do_not_create_archive(self):
        original = self.active.read_bytes()
        self.assertEqual(self.cli("inspect")[0], 0)
        code, output, err = self.cli("archive", "--ids", "ISS-0001")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("dry-run", output)
        self.assertEqual(original, self.active.read_bytes())
        self.assertFalse(self.archive.exists())

    def test_archive_then_restore_one_canonical_record(self):
        code, output, err = self.cli("archive", "--ids", "ISS-0001", "--apply")
        self.assertEqual((code, err), (0, ""), err)
        year = __import__("datetime").date.today().year
        closed = self.archive / f"closed-{year}.md"
        self.assertTrue(closed.is_file())
        self.assertNotIn(DONE.strip(), self.active.read_text())
        self.assertIn(DONE.strip(), closed.read_text())
        self.assertEqual(validate_docs.validate_single_issue_register(self.active, self.archive), [])
        self.assertIn("ISS-0002", self.active.read_text())

        code, output, err = self.cli("restore", "--ids", "ISS-0001", "--apply")
        self.assertEqual((code, err), (0, ""), err)
        self.assertIn(DONE.strip(), self.active.read_text())
        self.assertNotIn(DONE.strip(), closed.read_text())
        self.assertEqual(validate_docs.validate_single_issue_register(self.active, self.archive), [])

    def test_duplicate_active_archive_id_is_rejected(self):
        self.archive.mkdir(parents=True)
        old = self.active.read_text()
        self.active.write_text(old + "\n## 完了課題アーカイブ\n- [closed](issues/archive/closed-2026.md)\n", encoding="utf-8")
        (self.archive / "closed-2026.md").write_text(
            "# Archive\n\n## ISS-0001\n\n" + ROW_HEADERS + ROW_SEPARATOR + DONE, encoding="utf-8"
        )
        errors = validate_docs.validate_single_issue_register(self.active, self.archive)
        self.assertTrue(any("duplicate issue ID" in e for e in errors), errors)
        self.assertEqual(self.cli("inspect")[0], 1)

    def test_unindexed_archive_rejected(self):
        self.archive.mkdir(parents=True)
        (self.archive / "closed-2026.md").write_text("# Archive\n", encoding="utf-8")
        errors = validate_docs.validate_single_issue_register(self.active, self.archive)
        self.assertTrue(any("unindexed archive" in e for e in errors), errors)

    def test_nonterminal_and_detail_require_manual_review(self):
        code, _, err = self.cli("archive", "--ids", "ISS-0002")
        self.assertEqual(code, 1)
        self.assertIn("terminal status", err)
        self.active.write_text(self.active.read_text() + "\n### ISS-0001 details\nhistory\n", encoding="utf-8")
        code, _, err = self.cli("archive", "--ids", "ISS-0001")
        self.assertEqual(code, 1)
        self.assertIn("detailed heading", err)

    def test_auto_skips_insufficient_eligible_candidates(self):
        code, output, _ = self.cli("archive", "--auto")
        self.assertEqual(code, 0)
        self.assertIn("no batch", output)
        self.assertFalse(self.archive.exists())
        code, output, _ = self.cli("archive", "--auto", "--min-closed-count", "1")
        self.assertEqual(code, 0)
        self.assertIn("dry-run", output)

    def test_archive_link_requires_explicit_scope(self):
        self.active.write_text(self.active.read_text() + "\n## 完了課題アーカイブ\n- [missing](issues/archive/closed-2026.md)\n", encoding="utf-8")
        errors = validate_docs.validate_single_issue_register(self.active)
        self.assertTrue(any("require explicit --archive-dir" in e for e in errors), errors)

    def test_federated_archive_with_nested_managed_directory(self):
        main = self.root / "ISSUES.md"
        managed = self.root / "issues"
        managed.mkdir(exist_ok=True)
        sub = managed / "quality.md"
        sub.write_text("# Quality\n\n## 課題一覧\n" + ROW_HEADERS + ROW_SEPARATOR + DONE, encoding="utf-8")
        main.write_text(
            "# Main\n\n## 共通ISS採番\n- 次の未割当番号: ISS-0003\n\n"
            "## サブ課題表\n- [Quality](issues/quality.md)\n", encoding="utf-8"
        )
        self.assertEqual(validate_docs.validate_federated_issue_register(main, managed), [])
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = archive.main([
                "archive", "--issue-main", str(main), "--managed-dir", str(managed),
                "--archive-dir", str(managed / "archive"), "--ids", "ISS-0001", "--apply"
            ])
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertEqual(validate_docs.validate_federated_issue_register(main, managed, managed / "archive"), [])
        self.assertNotIn(DONE.strip(), sub.read_text())

    def test_archive_status_and_counter_are_validated(self):
        self.archive.mkdir(parents=True)
        self.active.write_text(self.active.read_text() + "\n## 完了課題アーカイブ\n- [closed](issues/archive/closed-2026.md)\n", encoding="utf-8")
        (self.archive / "closed-2026.md").write_text(
            "# Archive\n\n## 共通ISS採番\n- 次の未割当番号: ISS-9999\n\n"
            + ROW_HEADERS + ROW_SEPARATOR + OPEN.replace("ISS-0002", "ISS-0008"), encoding="utf-8"
        )
        errors = validate_docs.validate_single_issue_register(self.active, self.archive)
        self.assertTrue(any("terminal status" in e for e in errors), errors)
        self.assertTrue(any("second ISS counter" in e for e in errors), errors)
        self.assertTrue(any("next ISS counter" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
