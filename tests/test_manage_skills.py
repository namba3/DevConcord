from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import manage_skills


class SkillManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source" / ".agents" / "skills"
        self.target = self.root / "target"
        self.source.mkdir(parents=True)
        self.target.mkdir()
        self.write_skill("sample-skill", "v1")

    def write_skill(self, name: str, version: str) -> Path:
        skill = self.source / name
        skill.mkdir(parents=True, exist_ok=True)
        skill.joinpath("SKILL.md").write_text(
            f"""---
name: {name}
description: Use this Skill for a focused task.
---

# {name}

Version: {version}
""",
            encoding="utf-8",
        )
        (skill / "references").mkdir(exist_ok=True)
        (skill / "references" / "details.md").write_text(
            f"# Details\n\nVersion: {version}\n", encoding="utf-8"
        )
        return skill

    def run_operation(
        self,
        command: str,
        *,
        agent: str = "codex",
        skills: list[str] | None = None,
        apply: bool = False,
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command=command,
            target=self.target,
            source=self.source,
            agent=agent,
            skills=skills,
            apply=apply,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_dry_run_does_not_write_then_install_records_provenance(self) -> None:
        source_before = {
            path.relative_to(self.source).as_posix(): path.read_bytes()
            for path in self.source.rglob("*")
            if path.is_file()
        }
        result, output, _ = self.run_operation("install")
        self.assertEqual(result, 0)
        self.assertIn("Dry run only", output)
        self.assertFalse((self.target / ".agents" / "skills").exists())
        self.assertFalse((self.target / ".devconcord").exists())

        result, _, error = self.run_operation("install", apply=True)
        self.assertEqual((result, error), (0, ""))
        installed = self.target / ".agents" / "skills" / "sample-skill"
        self.assertEqual(
            (installed / "references" / "details.md").read_text(encoding="utf-8"),
            "# Details\n\nVersion: v1\n",
        )
        manifest = json.loads(
            (self.target / ".devconcord" / "skills-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        record = manifest["installations"][".agents/skills"]["skills"]["sample-skill"]
        self.assertEqual(record["source_tree_sha256"], record["installed_tree_sha256"])
        self.assertIn("source_commit", record)
        self.assertEqual(record["source_repository"], "local source directory")
        self.assertEqual(
            source_before,
            {
                path.relative_to(self.source).as_posix(): path.read_bytes()
                for path in self.source.rglob("*")
                if path.is_file()
            },
        )

    def test_install_is_idempotent_and_sync_updates_managed_skill(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        before = (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_bytes()
        result, output, error = self.run_operation("install", apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("unchanged: sample-skill", output)
        self.assertEqual(
            before,
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_bytes(),
        )

        self.write_skill("sample-skill", "v2")
        self.assertEqual(self.run_operation("sync", apply=True)[0], 0)
        self.assertIn(
            "Version: v2",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_install_supports_selected_skill_subset(self) -> None:
        self.write_skill("other-skill", "v1")

        result, _, error = self.run_operation(
            "install", skills=["other-skill"], apply=True
        )

        self.assertEqual((result, error), (0, ""))
        skills_root = self.target / ".agents" / "skills"
        self.assertTrue((skills_root / "other-skill" / "SKILL.md").is_file())
        self.assertFalse((skills_root / "sample-skill").exists())

    def test_local_edits_and_untracked_collisions_are_preserved(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        target_skill = self.target / ".agents" / "skills" / "sample-skill"
        target_skill.joinpath("SKILL.md").write_text("local edit\n", encoding="utf-8")
        result, _, error = self.run_operation("sync", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("local modifications detected", error)
        self.assertEqual(target_skill.joinpath("SKILL.md").read_text(encoding="utf-8"), "local edit\n")

        collision_target = self.root / "collision"
        collision_target.mkdir()
        collision_skill = collision_target / ".agents" / "skills" / "sample-skill"
        collision_skill.mkdir(parents=True)
        marker = collision_skill / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        self.target = collision_target
        result, _, error = self.run_operation("install", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("untracked Skill exists", error)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_duplicate_agent_discovery_paths_are_rejected(self) -> None:
        second_skill = self.target / ".claude" / "skills" / "sample-skill"
        second_skill.mkdir(parents=True)
        (second_skill / "SKILL.md").write_text("existing", encoding="utf-8")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("duplicate skill names", error)
        self.assertFalse((self.target / ".agents" / "skills").exists())

    def test_claude_install_uses_agent_specific_path(self) -> None:
        result, _, error = self.run_operation("install", agent="claude", apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertTrue((self.target / ".claude" / "skills" / "sample-skill" / "SKILL.md").is_file())
        self.assertFalse((self.target / ".agents" / "skills" / "sample-skill").exists())

    def test_sync_failure_rolls_back_files_and_manifest(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        installed_file = self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        manifest_file = self.target / ".devconcord" / "skills-manifest.json"
        old_skill = installed_file.read_bytes()
        old_manifest = manifest_file.read_bytes()
        self.write_skill("sample-skill", "v2")
        with patch.object(
            manage_skills, "_write_atomically", side_effect=OSError("simulated manifest failure")
        ):
            result, _, _ = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertEqual(installed_file.read_bytes(), old_skill)
        self.assertEqual(manifest_file.read_bytes(), old_manifest)

    def test_source_repository_identifier_redacts_credentials_and_query(self) -> None:
        results = [
            SimpleNamespace(returncode=0, stdout="/source/repo\n"),
            SimpleNamespace(returncode=0, stdout="abc123\n"),
            SimpleNamespace(returncode=0, stdout=""),
            SimpleNamespace(
                returncode=0,
                stdout="https://user:password@example.com/org/repo.git?token=secret\n",
            ),
        ]
        with patch.object(manage_skills.subprocess, "run", side_effect=results):
            commit, dirty, repository = manage_skills.source_revision(self.source)

        self.assertEqual((commit, dirty), ("abc123", False))
        self.assertEqual(repository, "https://example.com/org/repo.git")
        self.assertNotIn("password", repository)
        self.assertNotIn("secret", repository)


if __name__ == "__main__":
    unittest.main()
