from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import agent_skills, manage_skills


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
        source_repo = self.source.parents[1]
        self.git(source_repo, "init", "-q")
        self.git(source_repo, "config", "user.email", "test@example.invalid")
        self.git(source_repo, "config", "user.name", "Test")
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v1")

    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

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
        agents: list[str] | None = None,
        skills: list[str] | None = None,
        apply: bool = False,
        allow_duplicate_discovery: bool = False,
        allow_dirty_source: bool = False,
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command=command,
            target=self.target,
            source=self.source,
            agent=agent,
            agents=agents,
            skills=skills,
            apply=apply,
            allow_duplicate_discovery=allow_duplicate_discovery,
            allow_dirty_source=allow_dirty_source,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_recovery(self, *, apply: bool = False, force: bool = False) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="recover",
            target=self.target,
            apply=apply,
            force=force,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_validation(self) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="validate",
            source=manage_skills.DEFAULT_SOURCE,
            target=self.target,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def interrupt_sync_before_manifest(self) -> Path:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.write_skill("sample-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        real_write = manage_skills._write_atomically

        def interrupt_manifest(path: Path, text: str) -> None:
            if path == manifest_path:
                raise KeyboardInterrupt()
            real_write(path, text)

        with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_manifest):
            with self.assertRaises(KeyboardInterrupt):
                self.run_operation("sync", apply=True)
        return manifest_path

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
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        self.assertEqual(record["source_tree_sha256"], record["installed_tree_sha256"])
        self.assertIn("source_commit", record)
        self.assertTrue(record["source_repository"].startswith("local-git-sha256:"))
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
        self.assertIn("unchanged: .agents/skills/sample-skill", output)
        self.assertEqual(
            before,
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_bytes(),
        )

        self.write_skill("sample-skill", "v2")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        self.assertEqual(self.run_operation("sync", apply=True)[0], 0)
        self.assertIn(
            "Version: v2",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_install_supports_selected_skill_subset(self) -> None:
        self.write_skill("other-skill", "v1")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "add other skill")

        result, _, error = self.run_operation(
            "install", skills=["other-skill"], apply=True
        )

        self.assertEqual((result, error), (0, ""))
        skills_root = self.target / ".agents" / "skills"
        self.assertTrue((skills_root / "other-skill" / "SKILL.md").is_file())
        self.assertFalse((skills_root / "sample-skill").exists())

    def test_install_rejects_clean_git_checkout_with_ignored_skill_content(self) -> None:
        source_repo = self.source.parents[1]
        (source_repo / ".gitignore").write_text("*.local\n", encoding="utf-8")
        self.git(source_repo, "add", ".gitignore")
        self.git(source_repo, "commit", "-qm", "ignore local files")
        ignored = self.source / "sample-skill" / "private.local"
        ignored.write_text("not present in Git\n", encoding="utf-8")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("differs from its Git commit baseline", error)
        self.assertFalse((self.target / ".agents" / "skills").exists())

        result, _, error = self.run_operation(
            "install", apply=True, allow_dirty_source=True
        )
        self.assertEqual((result, error), (0, ""))
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        self.assertTrue(record["source_dirty"])

    def test_target_validation_checks_manifest_hash_and_untracked_skill_files(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.assertEqual(self.run_validation()[0], 0)
        installed_root = self.target / ".agents" / "skills"
        installed_skill = installed_root / "sample-skill"
        (installed_skill / "SKILL.md").write_text(
            "local edit\n", encoding="utf-8"
        )
        result, _, error = self.run_validation()
        self.assertEqual(result, 1)
        self.assertIn("differs from manifest hash", error)

        unmanaged = installed_root / "unmanaged-skill"
        unmanaged.mkdir()
        (unmanaged / "SKILL.md").write_text(
            "---\nname: unmanaged-skill\ndescription: A valid Skill.\n---\n",
            encoding="utf-8",
        )
        result, _, error = self.run_validation()
        self.assertEqual(result, 1)
        self.assertIn("not recorded in manifest", error)

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

    def test_copilot_duplicate_discovery_paths_are_rejected(self) -> None:
        second_skill = self.target / ".claude" / "skills" / "sample-skill"
        second_skill.mkdir(parents=True)
        (second_skill / "SKILL.md").write_text("existing", encoding="utf-8")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual(result, 0)
        self.assertEqual(error, "")

        self.target = self.root / "copilot-target"
        self.target.mkdir()
        second_skill = self.target / ".claude" / "skills" / "sample-skill"
        second_skill.mkdir(parents=True)
        (second_skill / "SKILL.md").write_text("existing", encoding="utf-8")
        result, _, error = self.run_operation("install", agent="copilot", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("different contents", error)
        self.assertFalse((self.target / ".agents" / "skills").exists())

        shutil.rmtree(second_skill)
        shutil.copytree(self.source / "sample-skill", second_skill)
        result, output, error = self.run_operation(
            "install",
            agent="copilot",
            apply=True,
            allow_duplicate_discovery=True,
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("duplicate discovery paths", output.lower())

    def test_claude_install_uses_agent_specific_path(self) -> None:
        result, _, error = self.run_operation("install", agent="claude", apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertTrue((self.target / ".claude" / "skills" / "sample-skill" / "SKILL.md").is_file())
        self.assertFalse((self.target / ".agents" / "skills" / "sample-skill").exists())

    def test_agent_matrix_uses_shared_or_agent_specific_discovery_roots(self) -> None:
        cases = (
            (["codex"], {".agents/skills"}),
            (["copilot"], {".agents/skills"}),
            (["claude"], {".claude/skills"}),
            (["codex", "copilot"], {".agents/skills"}),
            (["codex", "claude"], {".agents/skills", ".claude/skills"}),
            (["claude", "copilot"], {".claude/skills"}),
            (
                ["codex", "claude", "copilot"],
                {".agents/skills", ".claude/skills"},
            ),
        )
        for agents, expected_roots in cases:
            with self.subTest(agents=agents):
                self.target = self.root / ("target-" + "-".join(agents))
                self.target.mkdir()
                if len(agents) == 3:
                    blocked, _, blocked_error = self.run_operation(
                        "install", agents=agents, apply=True
                    )
                    self.assertEqual(blocked, 2)
                    self.assertIn("allow-duplicate-discovery", blocked_error)
                    self.assertFalse((self.target / ".agents" / "skills").exists())
                result, output, error = self.run_operation(
                    "install",
                    agents=agents,
                    apply=True,
                    allow_duplicate_discovery=len(agents) == 3,
                )
                self.assertEqual((result, error), (0, ""))
                manifest = json.loads(
                    (self.target / ".devconcord" / "skills-manifest.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(manifest["schema_version"], 2)
                self.assertEqual(set(manifest["packages"]), expected_roots)
                package_hashes = set()
                for root_name, package in manifest["packages"].items():
                    self.assertEqual(set(package["agents"]), set(agents).intersection(
                        {"codex", "copilot"} if root_name == ".agents/skills" else {"claude", "copilot"}
                    ))
                    installed_skill = self.target / root_name / "sample-skill"
                    self.assertEqual(
                        manage_skills.tree_digest(installed_skill),
                        package["skills"]["sample-skill"]["installed_tree_sha256"],
                    )
                    package_hashes.add(
                        package["skills"]["sample-skill"]["installed_tree_sha256"]
                    )
                self.assertEqual(len(package_hashes), 1)
                if len(agents) == 3:
                    self.assertIn("duplicate discovery", output.lower())

    def test_incremental_agent_install_checks_and_records_global_duplicate_exposure(self) -> None:
        self.assertEqual(
            self.run_operation("install", agents=["claude", "copilot"], apply=True)[0],
            0,
        )

        result, _, error = self.run_operation(
            "install", agent="codex", apply=True
        )

        self.assertEqual(result, 2)
        self.assertIn("duplicate-discovery", error.lower())
        self.assertFalse(
            (self.target / ".agents" / "skills" / "sample-skill").exists()
        )

        result, output, error = self.run_operation(
            "install",
            agent="codex",
            apply=True,
            allow_duplicate_discovery=True,
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("duplicate discovery", output.lower())
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn(
            {
                "skill": "sample-skill",
                "paths": [".agents/skills", ".claude/skills"],
            },
            manifest["duplicate_discovery_allowances"],
        )
        self.assertFalse(agent_skills.validate_repository_skills(self.target))
        self.assertEqual(self.run_validation()[0], 0)

        result, output, error = self.run_operation("install", agent="codex", apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("duplicate discovery", output.lower())
        repeated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            repeated_manifest["duplicate_discovery_allowances"],
            manifest["duplicate_discovery_allowances"],
        )

        self.write_skill("sample-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")
        original_claude = (
            self.target / ".claude" / "skills" / "sample-skill" / "SKILL.md"
        ).read_bytes()
        result, _, error = self.run_operation(
            "sync", agent="codex", apply=True
        )
        self.assertEqual(result, 2)
        self.assertIn("different contents", error.lower())
        self.assertEqual(
            (
                self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
            ).read_text(encoding="utf-8").count("v1"),
            1,
        )
        self.assertEqual(
            (
                self.target / ".claude" / "skills" / "sample-skill" / "SKILL.md"
            ).read_bytes(),
            original_claude,
        )

        result, _, error = self.run_operation(
            "sync", agents=["codex", "claude"], apply=True
        )
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(
            manage_skills.tree_digest(
                self.target / ".agents" / "skills" / "sample-skill"
            ),
            manage_skills.tree_digest(
                self.target / ".claude" / "skills" / "sample-skill"
            ),
        )
        self.assertFalse(agent_skills.validate_repository_skills(self.target))
        self.assertEqual(self.run_validation()[0], 0)

    def test_codex_and_copilot_share_existing_package_and_migrate_legacy_manifest(self) -> None:
        self.assertEqual(self.run_operation("install", agent="codex", apply=True)[0], 0)
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package = manifest["packages"][".agents/skills"]
        old_schema = {
            "schema_version": 1,
            "installations": {
                ".agents/skills": {
                    "agent": "codex",
                    "skills": package["skills"],
                }
            },
        }
        manifest_path.write_text(json.dumps(old_schema), encoding="utf-8")

        result, _, error = self.run_operation("install", agent="copilot", apply=True)

        self.assertEqual((result, error), (0, ""))
        migrated = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(
            migrated["packages"][".agents/skills"]["agents"], ["codex", "copilot"]
        )
        self.assertEqual(len(list((self.target / ".agents" / "skills").iterdir())), 1)

    def test_sync_rejects_rewind_divergence_foreign_and_dirty_sources(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        source_repo = self.source.parents[1]
        base_commit = self.git(source_repo, "rev-parse", "HEAD")
        self.write_skill("sample-skill", "v2")
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        self.assertEqual(self.run_operation("sync", apply=True)[0], 0)

        self.git(source_repo, "checkout", "--detach", base_commit)
        result, _, error = self.run_operation("sync", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("rewind", error.lower())

        self.git(source_repo, "checkout", "--detach", "HEAD")
        (self.source / "sample-skill" / "untracked.txt").write_text("uncommitted", encoding="utf-8")
        result, _, error = self.run_operation("sync", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("uncommitted", error.lower())

    def test_sync_rejects_unrelated_source_history(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        alternate = self.root / "alternate"
        alternate.mkdir()
        alternate_skills = alternate / ".agents" / "skills"
        alternate_skills.mkdir(parents=True)
        alternate_skill = alternate_skills / "sample-skill"
        alternate_skill.mkdir()
        alternate_skill.joinpath("SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Safe skill.\n---\n",
            encoding="utf-8",
        )
        self.git(alternate, "init", "-q")
        self.git(alternate, "config", "user.email", "test@example.invalid")
        self.git(alternate, "config", "user.name", "Test")
        self.git(alternate, "add", ".")
        self.git(alternate, "commit", "-qm", "unrelated")
        self.source = alternate_skills

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("recorded source commit is missing", error.lower())
        result, output, error = self.run_operation("rebind-source", apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("explicitly accepts", output.lower())
        self.assertIn(
            "Safe skill",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_sync_rejects_diverged_history(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        source_repo = self.source.parents[1]
        self.git(source_repo, "checkout", "--orphan", "unrelated")
        self.write_skill("sample-skill", "diverged")
        self.git(source_repo, "add", "-A")
        self.git(source_repo, "commit", "-qm", "diverged")

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("different or diverged", error.lower())

    def test_sync_rejects_same_history_from_a_different_remote(self) -> None:
        source_repo = self.source.parents[1]
        self.git(source_repo, "remote", "add", "origin", "https://github.com/team/original.git")
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)

        fork = self.root / "fork"
        self.git(self.root, "clone", "-q", str(source_repo), str(fork))
        self.git(fork, "config", "user.email", "test@example.invalid")
        self.git(fork, "config", "user.name", "Test")
        self.git(fork, "remote", "set-url", "origin", "git@github.com:team/fork.git")
        fork_skills = fork / ".agents" / "skills"
        (fork_skills / "sample-skill" / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Use this Skill for a focused task.\n---\n\nVersion: fork\n",
            encoding="utf-8",
        )
        self.git(fork, "add", ".")
        self.git(fork, "commit", "-qm", "fork update")
        self.source = fork_skills
        installed_file = self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        original = installed_file.read_bytes()

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("source identity changed", error.lower())
        self.assertEqual(installed_file.read_bytes(), original)

        result, _, error = self.run_operation("rebind-source", apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Version: fork", installed_file.read_text(encoding="utf-8"))

    def test_sync_accepts_https_to_ssh_url_change_for_same_repository(self) -> None:
        source_repo = self.source.parents[1]
        self.git(source_repo, "remote", "add", "origin", "https://github.com/team/repo.git")
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.git(source_repo, "remote", "set-url", "origin", "git@github.com:team/repo.git")
        self.write_skill("sample-skill", "v2")
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn(
            "Version: v2",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_sync_verifies_baseline_skill_content_against_recorded_commit(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packages"][".agents/skills"]["skills"]["sample-skill"][
            "source_tree_sha256"
        ] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.write_skill("sample-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("baseline skill content", error.lower())
        self.assertIn(
            "Version: v1",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_sync_identifies_shallow_history_without_fetching(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        source_repo = self.source.parents[1]
        self.write_skill("sample-skill", "v2")
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        shallow_root = self.root / "shallow"
        self.git(self.root, "clone", "-q", "--depth", "1", f"file://{source_repo}", str(shallow_root))
        self.source = shallow_root / ".agents" / "skills"

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("source history is shallow", error.lower())

    def test_corrupt_manifest_is_preserved(self) -> None:
        manifest = self.target / ".devconcord" / "skills-manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{broken", encoding="utf-8")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("cannot read Skill manifest", error)
        self.assertEqual(manifest.read_text(encoding="utf-8"), "{broken")

    def test_unknown_legacy_manifest_is_preserved(self) -> None:
        manifest = self.target / ".devconcord" / "skills-manifest.json"
        manifest.parent.mkdir(parents=True)
        original = json.dumps(
            {
                "schema_version": 1,
                "installations": {
                    "../outside": {"agent": "codex", "skills": {}}
                },
            }
        )
        manifest.write_text(original, encoding="utf-8")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("invalid legacy installation", error)
        self.assertEqual(manifest.read_text(encoding="utf-8"), original)

    def test_sync_failure_rolls_back_files_and_manifest(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        installed_file = self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        manifest_file = self.target / ".devconcord" / "skills-manifest.json"
        old_skill = installed_file.read_bytes()
        old_manifest = manifest_file.read_bytes()
        self.write_skill("sample-skill", "v2")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        write_atomically = manage_skills._write_atomically

        def fail_manifest_write(path: Path, text: str) -> None:
            if path == manifest_file:
                raise OSError("simulated manifest failure")
            write_atomically(path, text)

        with patch.object(manage_skills, "_write_atomically", side_effect=fail_manifest_write):
            result, _, _ = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertEqual(installed_file.read_bytes(), old_skill)
        self.assertEqual(manifest_file.read_bytes(), old_manifest)

    def test_git_unversioned_source_requires_explicit_rebind_for_sync(self) -> None:
        unversioned_source = self.root / "unversioned" / ".agents" / "skills"
        unversioned_source.parent.mkdir(parents=True)
        shutil.copytree(self.source, unversioned_source)
        self.source = unversioned_source

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual((result, error), (0, ""))
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        self.assertEqual(record["source_commit"], "unversioned")

        result, _, error = self.run_operation("sync", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("history is unavailable", error.lower())
        self.assertEqual(self.run_operation("rebind-source", apply=True)[0], 0)

    def test_interrupted_replace_is_recovered_from_journal(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        installed_file = self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        old_skill = installed_file.read_bytes()
        self.write_skill("sample-skill", "v2")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        real_replace = manage_skills.os.replace

        def interrupt_replace(source: Path, destination: Path) -> None:
            if Path(destination) == installed_file.parent:
                raise KeyboardInterrupt()
            real_replace(source, destination)

        with patch.object(manage_skills.os, "replace", side_effect=interrupt_replace):
            with self.assertRaises(KeyboardInterrupt):
                self.run_operation("sync", apply=True)

        self.assertFalse(installed_file.exists())
        result, _, error = self.run_recovery(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertEqual(installed_file.read_bytes(), old_skill)
        self.assertEqual(manage_skills._transaction_directories(self.target), [])

    def test_recovery_preflight_does_not_restore_any_skill_if_a_later_target_changed(self) -> None:
        self.write_skill("other-skill", "v1")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "add second Skill")
        self.assertEqual(
            self.run_operation(
                "install",
                agents=["codex", "claude"],
                apply=True,
                allow_duplicate_discovery=True,
            )[0],
            0,
        )
        self.write_skill("sample-skill", "v2")
        self.write_skill("other-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        real_write = manage_skills._write_atomically

        def interrupt_manifest(path: Path, text: str) -> None:
            if path == manifest_path:
                raise KeyboardInterrupt()
            real_write(path, text)

        with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_manifest):
            with self.assertRaises(KeyboardInterrupt):
                self.run_operation(
                    "sync",
                    agents=["codex", "claude"],
                    apply=True,
                    allow_duplicate_discovery=True,
                )

        changed_target = self.target / ".agents" / "skills" / "sample-skill"
        changed_file = changed_target / "SKILL.md"
        changed_file.write_text("external edit\n", encoding="utf-8")
        claude_target = self.target / ".claude" / "skills"
        claude_before = {
            path.relative_to(claude_target).as_posix(): (
                path.read_bytes() if path.is_file() else path.stat().st_mode
            )
            for path in claude_target.rglob("*")
            if path.is_file()
        }
        manifest_before = manifest_path.read_bytes()

        result, _, error = self.run_recovery(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("target changed after interruption", error)
        self.assertEqual(changed_file.read_text(encoding="utf-8"), "external edit\n")
        self.assertEqual(manifest_path.read_bytes(), manifest_before)
        self.assertEqual(
            claude_before,
            {
                path.relative_to(claude_target).as_posix(): (
                    path.read_bytes() if path.is_file() else path.stat().st_mode
                )
                for path in claude_target.rglob("*")
                if path.is_file()
            },
        )

    def test_recovery_preflight_preserves_files_when_a_backup_is_corrupt(self) -> None:
        manifest_path = self.interrupt_sync_before_manifest()
        transaction = manage_skills._transaction_directories(self.target)[0]
        backup = next((transaction / "backups").iterdir())
        (backup / "SKILL.md").write_text("corrupt backup\n", encoding="utf-8")
        target_skill = self.target / ".agents" / "skills" / "sample-skill"
        target_before = {
            path.relative_to(target_skill).as_posix(): path.read_bytes()
            for path in target_skill.rglob("*")
            if path.is_file()
        }
        manifest_before = manifest_path.read_bytes()

        result, _, error = self.run_recovery(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("backup integrity check failed", error)
        self.assertEqual(
            target_before,
            {
                path.relative_to(target_skill).as_posix(): path.read_bytes()
                for path in target_skill.rglob("*")
                if path.is_file()
            },
        )
        self.assertEqual(manifest_path.read_bytes(), manifest_before)
        self.assertTrue(transaction.exists())

    def test_recovery_completes_when_manifest_was_written_before_interruption(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.write_skill("sample-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        real_write = manage_skills._write_atomically

        def interrupt_after_manifest(path: Path, text: str) -> None:
            real_write(path, text)
            if path == manifest_path:
                raise KeyboardInterrupt()

        with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_after_manifest):
            with self.assertRaises(KeyboardInterrupt):
                self.run_operation("sync", apply=True)
        self.assertEqual(len(manage_skills._transaction_directories(self.target)), 1)

        result, output, error = self.run_recovery(apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("completed", output)
        self.assertIn(
            "Version: v2",
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(manage_skills._transaction_directories(self.target), [])
        self.assertEqual(self.run_recovery(apply=True)[0], 0)

    def test_recovery_io_failure_keeps_journal_and_allows_retry(self) -> None:
        manifest_path = self.interrupt_sync_before_manifest()
        target_skill = self.target / ".agents" / "skills" / "sample-skill"
        target_before = {
            path.relative_to(target_skill).as_posix(): path.read_bytes()
            for path in target_skill.rglob("*")
            if path.is_file()
        }
        manifest_before = manifest_path.read_bytes()
        real_rmtree = shutil.rmtree

        def fail_target_removal(path: Path, *args: object, **kwargs: object) -> None:
            if Path(path) == target_skill:
                raise OSError("simulated recovery I/O failure")
            real_rmtree(path, *args, **kwargs)

        with patch.object(shutil, "rmtree", side_effect=fail_target_removal):
            result, _, error = self.run_recovery(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("simulated recovery I/O failure", error)
        self.assertEqual(
            target_before,
            {
                path.relative_to(target_skill).as_posix(): path.read_bytes()
                for path in target_skill.rglob("*")
                if path.is_file()
            },
        )
        self.assertEqual(manifest_path.read_bytes(), manifest_before)
        self.assertEqual(len(manage_skills._transaction_directories(self.target)), 1)
        self.assertEqual(self.run_recovery(apply=True)[0], 0)
        self.assertIn(
            "Version: v1",
            (target_skill / "SKILL.md").read_text(encoding="utf-8"),
        )

    def test_recovery_force_removes_only_a_confirmed_stale_lock(self) -> None:
        lock_path = self.target / ".devconcord" / "skills.lock"
        lock_path.parent.mkdir()
        lock_path.write_text("pid=12345\n", encoding="ascii")

        with patch.object(manage_skills, "_process_is_running", return_value=True):
            result, _, error = self.run_recovery(apply=True, force=True)
        self.assertEqual(result, 2)
        self.assertIn("active process", error)
        self.assertTrue(lock_path.exists())

        with patch.object(manage_skills, "_process_is_running", return_value=False):
            result, _, error = self.run_recovery(apply=True, force=True)
        self.assertEqual((result, error), (0, ""))
        self.assertFalse(lock_path.exists())

    def test_install_refuses_to_plan_or_apply_while_locked(self) -> None:
        lock_path = self.target / ".devconcord" / "skills.lock"
        lock_path.parent.mkdir()
        lock_path.write_text(f"pid={manage_skills.os.getpid()}\n", encoding="ascii")

        dry_result, _, dry_error = self.run_operation("install")
        apply_result, _, apply_error = self.run_operation("install", apply=True)

        self.assertEqual(dry_result, 2)
        self.assertIn("operation lock exists", dry_error)
        self.assertEqual(apply_result, 2)
        self.assertIn("another Skill operation", apply_error)
        self.assertFalse((self.target / ".agents" / "skills").exists())
        self.assertTrue(lock_path.exists())

    def test_recovery_preserves_staging_without_a_valid_journal(self) -> None:
        orphan = self.target / ".devconcord" / "skills-transactions" / "orphan"
        (orphan / "staged").mkdir(parents=True)
        (orphan / "backups").mkdir()

        result, _, error = self.run_recovery(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("no valid journal", error)
        self.assertTrue(orphan.is_dir())

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
        self.assertEqual(repository, "example.com/org/repo")
        self.assertNotIn("password", repository)
        self.assertNotIn("secret", repository)


if __name__ == "__main__":
    unittest.main()
