from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import agent_skills, manage_skills


def paths_equal(left: Path, right: Path) -> bool:
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(
        str(Path(right).resolve())
    )


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
        source_repo.joinpath("scripts").mkdir()
        source_repo.joinpath("scripts", "manage_skills.py").write_text(
            "# test source marker\n", encoding="utf-8"
        )
        source_repo.joinpath("docs").mkdir()
        source_repo.joinpath("docs", "reference.md").write_text(
            "# Versioned reference\n\nInitial committed guidance.\n", encoding="utf-8"
        )
        source_repo.joinpath("docs", "subdir").mkdir()
        source_repo.joinpath("docs", "subdir", "nested.md").write_text(
            "Nested fixture.\n", encoding="utf-8"
        )
        for name in ("README.md", "AGENTS.md", "REVIEW.md", "REVIEWS.md"):
            source_repo.joinpath(name).write_text(
                f"# {name}\n\nRoot reference fixture.\n", encoding="utf-8"
            )
        source_repo.joinpath("LICENSE.md").write_text(
            "Not an allowlisted root reference.\n", encoding="utf-8"
        )
        source_repo.joinpath("prompts").mkdir()
        source_repo.joinpath("prompts", "bootstrap-from-design.md").write_text(
            "Historical prompt content.\n", encoding="utf-8"
        )
        self.git(source_repo, "init", "-q")
        self.git(source_repo, "config", "user.email", "test@example.invalid")
        self.git(source_repo, "config", "user.name", "Test")
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v1")
        self.user_home = self.root / "user-home"
        self.user_home.mkdir()

    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not reliable on Windows")
    def test_install_and_validate_ignore_non_executable_permission_differences(self) -> None:
        source_repo = self.source.parents[1]
        for path in (self.source / "sample-skill").rglob("*"):
            if path.is_file():
                path.chmod(0o600)
        self.assertEqual(self.git(source_repo, "status", "--porcelain"), "")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual((result, error), (0, ""))
        target_skill = self.target / ".agents" / "skills" / "sample-skill"
        for path in target_skill.rglob("*"):
            if path.is_file():
                path.chmod(0o644)
        self.assertEqual(self.run_validation()[0], 0)

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not reliable on Windows")
    def test_local_executable_bit_change_is_protected(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        installed_skill = self.target / ".agents" / "skills" / "sample-skill"
        skill_file = installed_skill / "SKILL.md"
        skill_file.chmod(stat.S_IMODE(skill_file.stat().st_mode) | 0o100)

        self.assertEqual(self.run_validation()[0], 1)
        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual(result, 2)
        self.assertIn("local modifications detected", error.lower())

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not reliable on Windows")
    def test_source_core_filemode_false_ignores_non_executable_permission_changes(self) -> None:
        source_repo = self.source.parents[1]
        self.git(source_repo, "config", "core.fileMode", "false")
        for path in (self.source / "sample-skill").rglob("*"):
            if path.is_file():
                path.chmod(0o600)
        self.assertEqual(self.git(source_repo, "status", "--porcelain"), "")

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual((result, error), (0, ""))

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not reliable on Windows")
    def test_committed_executable_bit_change_is_synchronized(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        source_repo = self.source.parents[1]
        source_file = self.source / "sample-skill" / "SKILL.md"
        source_file.chmod(stat.S_IMODE(source_file.stat().st_mode) | 0o100)
        self.git(
            source_repo,
            "update-index",
            "--chmod=+x",
            source_file.relative_to(source_repo).as_posix(),
        )
        self.git(source_repo, "commit", "-qm", "mark Skill executable")

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual((result, error), (0, ""))
        installed_file = (
            self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        )
        self.assertTrue(installed_file.stat().st_mode & 0o100)

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

    def commit_skill(self, name: str, version: str) -> None:
        self.write_skill(name, version)
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", f"{name} {version}")

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

    def run_user_operation(
        self,
        command: str,
        *,
        target: Path | None = None,
        agents: list[str] | None = None,
        skills: list[str] | None = None,
        apply: bool = False,
        source: Path | None = None,
        allow_duplicate_discovery: bool = False,
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command=command,
            scope="user",
            target=target,
            source=source,
            agent=None,
            agents=agents,
            skills=skills,
            apply=apply,
            allow_duplicate_discovery=allow_duplicate_discovery,
            allow_dirty_source=False,
            force=False,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_config(self, command: str, **kwargs: object) -> tuple[int, str, str]:
        args = SimpleNamespace(command="config", config_command=command, **kwargs)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_reference(
        self,
        *,
        path: str,
        revision: str = "installed",
        scope: str = "user",
        target: Path | None = None,
        skill: str = "sample-skill",
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="reference",
            skill=skill,
            path=path,
            revision=revision,
            scope=scope,
            target=target,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_doctor(
        self, *, target: Path | None = None, summary: bool = False
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(command="doctor", target=target, summary=summary)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(self.user_home)
        environment["USERPROFILE"] = str(self.user_home)
        return subprocess.run(
            [sys.executable, str(Path(manage_skills.__file__).resolve()), *arguments],
            cwd=self.target,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def run_user_recovery(self, *, apply: bool = False, force: bool = False) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="recover",
            scope="user",
            target=None,
            apply=apply,
            force=force,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
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
            if paths_equal(path, manifest_path):
                raise KeyboardInterrupt()
            real_write(path, text)

        with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_manifest):
            with self.assertRaises(KeyboardInterrupt):
                self.run_operation("sync", apply=True)
        return manifest_path

    def test_user_scope_defaults_without_target_and_dry_run_does_not_write_home(self) -> None:
        result, output, error = self.run_user_operation(
            "install",
            agents=["codex"],
            skills=["sample-skill"],
            source=self.source,
        )

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Scope: user", output)
        self.assertIn("Dry run only", output)
        self.assertFalse((self.user_home / ".agents").exists())
        self.assertFalse((self.user_home / ".devconcord").exists())

    def test_namespaced_skill_user_install_sync_reference_and_doctor(self) -> None:
        skill_name = "devconcord-bootstrap-from-design"
        self.commit_skill(skill_name, "v1")
        source_repo = self.source.parents[1]

        result, output, error = self.run_user_operation(
            "install",
            agents=["codex", "copilot"],
            skills=[skill_name],
            source=self.source,
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn(f".agents/skills/{skill_name}", output)
        self.assertFalse((self.user_home / ".agents").exists())

        result, _, error = self.run_user_operation(
            "install",
            agents=["codex", "copilot"],
            skills=[skill_name],
            apply=True,
            source=self.source,
        )
        self.assertEqual((result, error), (0, ""))
        installed_skill = self.user_home / ".agents" / "skills" / skill_name
        self.assertTrue((installed_skill / "SKILL.md").is_file())
        self.assertFalse(
            (self.user_home / ".agents" / "skills" / "bootstrap-from-design").exists()
        )
        manifest_path = self.user_home / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest["packages"][".agents/skills"]["skills"]
        self.assertEqual(set(records), {skill_name})
        self.assertEqual(
            self.run_config("set-source", source_root=source_repo, replace=False)[0],
            0,
        )
        result, output, error = self.run_reference(
            path="docs/reference.md", skill=skill_name
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Initial committed guidance.", output)

        project_skill = self.target / ".agents" / "skills" / skill_name
        project_skill.mkdir(parents=True)
        project_skill.joinpath("SKILL.md").write_text(
            "project-owned Skill\n", encoding="utf-8"
        )
        result, output, error = self.run_user_operation(
            "doctor", target=self.target, source=self.source
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("same-name User/Project Skill", output)
        self.assertIn(skill_name, output)

        self.commit_skill(skill_name, "v2")
        result, _, error = self.run_user_operation(
            "sync", apply=True, source=self.source
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Version: v2", (installed_skill / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_user_operation("validate")[0], 0)

        result, _, error = self.run_user_operation(
            "install",
            agents=["codex"],
            skills=["bootstrap-from-design"],
            apply=True,
            source=self.source,
        )
        self.assertEqual(result, 2)
        self.assertIn("unknown Skill", error)

    def test_namespaced_skill_project_install_sync_reference_and_rebind(self) -> None:
        skill_name = "devconcord-adopt-guidance"
        source_repo = self.source.parents[1]
        self.git(source_repo, "remote", "add", "origin", "https://github.com/team/original.git")
        self.commit_skill(skill_name, "v1")

        result, _, error = self.run_operation(
            "install", skills=[skill_name], apply=True
        )
        self.assertEqual((result, error), (0, ""))
        installed_skill = self.target / ".agents" / "skills" / skill_name
        self.assertTrue((installed_skill / "SKILL.md").is_file())
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest["packages"][".agents/skills"]["skills"]
        self.assertEqual(set(records), {skill_name})
        self.assertEqual(
            self.run_config(
                "set-source", source_root=source_repo, replace=False
            )[0],
            0,
        )
        result, output, error = self.run_reference(
            path="docs/reference.md",
            scope="project",
            target=self.target,
            skill=skill_name,
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Initial committed guidance.", output)
        self.assertEqual(self.run_validation()[0], 0)

        fork = self.root / "namespaced-fork"
        self.git(self.root, "clone", "-q", str(source_repo), str(fork))
        self.git(fork, "config", "user.email", "test@example.invalid")
        self.git(fork, "config", "user.name", "Test")
        self.git(fork, "remote", "set-url", "origin", "git@github.com:team/fork.git")
        fork_skill = fork / ".agents" / "skills" / skill_name
        fork_skill.joinpath("SKILL.md").write_text(
            fork_skill.joinpath("SKILL.md").read_text(encoding="utf-8").replace(
                "Version: v1", "Version: v2"
            ),
            encoding="utf-8",
        )
        self.git(fork, "add", ".")
        self.git(fork, "commit", "-qm", "namespaced fork update")
        self.source = fork / ".agents" / "skills"

        result, _, error = self.run_operation("sync", apply=True)
        self.assertEqual(result, 2)
        self.assertIn("source identity changed", error.lower())
        result, output, error = self.run_operation("rebind-source", apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("explicitly accepts", output.lower())
        self.assertIn("Version: v2", (installed_skill / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_validation()[0], 0)

    def test_user_scope_installs_under_home_and_preserves_unrelated_skills(self) -> None:
        unrelated = self.user_home / ".agents" / "skills" / "my-private-skill"
        unrelated.mkdir(parents=True)
        unrelated.joinpath("SKILL.md").write_text("user-authored\n", encoding="utf-8")
        snapshot = unrelated.joinpath("SKILL.md").read_bytes()

        result, _, error = self.run_user_operation(
            "install",
            agents=["codex", "copilot"],
            skills=["sample-skill"],
            apply=True,
            source=self.source,
        )

        self.assertEqual((result, error), (0, ""))
        self.assertTrue(
            (self.user_home / ".agents" / "skills" / "sample-skill" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (self.user_home / ".devconcord" / "skills-manifest.json").is_file()
        )
        if os.name != "nt":
            self.assertEqual(
                stat.S_IMODE((self.user_home / ".devconcord").stat().st_mode),
                0o700,
            )
        self.assertFalse((self.target / ".devconcord").exists())
        self.assertEqual(unrelated.joinpath("SKILL.md").read_bytes(), snapshot)
        self.assertEqual(self.run_user_operation("validate")[0], 0)

    def test_user_scope_detects_copilot_native_personal_skill_collision(self) -> None:
        existing = self.user_home / ".copilot" / "skills" / "sample-skill"
        existing.mkdir(parents=True)
        skill_file = existing / "SKILL.md"
        skill_file.write_text("user-authored Copilot Skill\n", encoding="utf-8")
        original = skill_file.read_bytes()

        result, _, error = self.run_user_operation(
            "install",
            agents=["copilot"],
            skills=["sample-skill"],
            apply=True,
            source=self.source,
        )

        self.assertEqual(result, 2)
        self.assertIn("same-name", error)
        self.assertEqual(skill_file.read_bytes(), original)
        self.assertFalse(
            (self.user_home / ".agents" / "skills" / "sample-skill").exists()
        )

    def test_user_scope_rejects_explicit_project_target_without_writing(self) -> None:
        args = SimpleNamespace(
            command="install",
            scope="user",
            target=self.target,
            source=self.source,
            agent="codex",
            agents=None,
            skills=["sample-skill"],
            apply=True,
        )
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual(result, 2)
        self.assertIn("--target cannot be combined", stderr.getvalue())
        self.assertFalse((self.target / ".agents").exists())
        self.assertFalse((self.user_home / ".agents").exists())

    def test_cli_scope_defaults_preserve_legacy_target_behavior(self) -> None:
        parser = manage_skills.build_parser()
        user_args = parser.parse_args(
            ["install", "--agents", "codex", "copilot", "--skills", "sample-skill"]
        )
        project_args = parser.parse_args(
            [
                "install",
                "--target",
                str(self.target),
                "--agent",
                "codex",
                "--skills",
                "sample-skill",
            ]
        )

        self.assertEqual(manage_skills._resolve_scope_target(user_args), ("user", Path.home().resolve()))
        scope, target = manage_skills._resolve_scope_target(project_args)
        self.assertEqual(scope, "project")
        self.assertEqual(target, self.target.resolve())

    def test_migrate_cli_exposes_explicit_duplicate_discovery_opt_in(self) -> None:
        parser = manage_skills.build_parser()
        args = parser.parse_args(
            ["migrate", "--scope", "user", "--allow-duplicate-discovery"]
        )
        self.assertTrue(args.allow_duplicate_discovery)
        self.assertFalse(args.apply)

    def test_user_config_requires_explicit_replace_and_does_not_rewrite_manifest(self) -> None:
        repository = self.source.parents[1]
        result, _, error = self.run_config("set-source", source_root=repository, replace=False)
        self.assertEqual((result, error), (0, ""))
        config_path = self.user_home / ".devconcord" / "config.json"
        first = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(first, {"schema_version": 1, "source_root": str(repository.resolve())})
        self.assertEqual(self.run_config("set-source", source_root=repository, replace=False)[0], 2)

        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        manifest_path = self.user_home / ".devconcord" / "skills-manifest.json"
        manifest_before = manifest_path.read_bytes()
        result, output, error = self.run_config(
            "set-source", source_root=repository, replace=True
        )

        self.assertEqual((result, error), (0, ""))
        self.assertIn("manifest was not changed", output)
        self.assertEqual(manifest_path.read_bytes(), manifest_before)
        self.assertEqual(self.run_config("show")[0], 0)

    def test_user_source_move_preserves_local_git_identity(self) -> None:
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        result, _, error = self.run_user_operation(
            "install",
            agents=["codex"],
            skills=["sample-skill"],
            apply=True,
        )
        self.assertEqual((result, error), (0, ""))

        moved_repository = self.root / "relocated-devconcord"
        shutil.move(str(repository), moved_repository)
        self.source = moved_repository / ".agents" / "skills"
        self.assertEqual(
            self.run_config("set-source", source_root=moved_repository, replace=True)[0],
            0,
        )

        args = SimpleNamespace(
            command="reference",
            skill="sample-skill",
            path="docs/reference.md",
            scope="user",
            target=None,
            revision="installed",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("Initial committed guidance.", stdout.getvalue())

        result, output, error = self.run_user_operation("sync", agents=["codex"])
        self.assertEqual((result, error), (0, ""))
        self.assertIn("unchanged: .agents/skills/sample-skill", output)
        result, output, error = self.run_user_operation(
            "sync", agents=["codex"], apply=True
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("No Skill or manifest changes are needed.", output)

    def test_user_config_rejects_malformed_settings_and_symlinks(self) -> None:
        state = self.user_home / ".devconcord"
        state.mkdir()
        config = state / "config.json"
        config.write_text('{"schema_version": 99}', encoding="utf-8")
        result, _, error = self.run_user_operation(
            "install", agents=["codex"], source=self.source
        )
        self.assertEqual(result, 2)
        self.assertIn("invalid user DevConcord config", error)
        config.unlink()
        config.symlink_to(self.source / "sample-skill" / "SKILL.md")
        result, _, error = self.run_config("show")
        self.assertEqual(result, 2)
        self.assertIn("must not be a symlink", error)

    def test_user_sync_defaults_to_all_managed_agents_and_protects_edits(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex", "copilot"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        result, output, error = self.run_user_operation("sync", source=self.source)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Dry run only", output)

        skill_file = self.user_home / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        result, _, error = self.run_user_operation("sync", apply=True, source=self.source)
        self.assertEqual(result, 2)
        self.assertIn("local modifications detected", error.lower())
        self.assertIn("local edit", skill_file.read_text(encoding="utf-8"))

    def test_user_scope_recovers_interrupted_sync_in_its_own_state_directory(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        self.write_skill("sample-skill", "v2")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "v2")
        manifest_path = self.user_home / ".devconcord" / "skills-manifest.json"
        real_write = manage_skills._write_atomically

        def interrupt_manifest(path: Path, text: str) -> None:
            if paths_equal(path, manifest_path):
                raise KeyboardInterrupt()
            real_write(path, text)

        with patch.object(Path, "home", return_value=self.user_home):
            with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_manifest):
                with self.assertRaises(KeyboardInterrupt):
                    self.run_user_operation("sync", apply=True, source=self.source)
        self.assertTrue(
            (self.user_home / ".devconcord" / "skills-transactions").is_dir()
        )
        self.assertEqual(self.run_user_recovery()[0], 0)
        result, output, error = self.run_user_recovery(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("rolled back", output)
        installed_file = self.user_home / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        self.assertIn("Version: v1", installed_file.read_text(encoding="utf-8"))
        self.assertEqual(self.run_user_operation("validate")[0], 0)

    def test_reference_cli_runs_from_a_different_project_working_directory(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )
        environment = os.environ.copy()
        environment["HOME"] = str(self.user_home)
        environment["USERPROFILE"] = str(self.user_home)
        script = Path(manage_skills.__file__).resolve()

        user_result = subprocess.run(
            [sys.executable, str(script), "reference", "--skill", "sample-skill",
             "--path", "docs/reference.md", "--revision", "installed"],
            cwd=self.target,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        project_result = subprocess.run(
            [sys.executable, str(script), "reference", "--skill", "sample-skill",
             "--path", "docs/reference.md", "--revision", "installed",
             "--scope", "project", "--target", str(self.target)],
            cwd=self.target,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual((user_result.returncode, user_result.stderr), (0, ""))
        self.assertIn("Initial committed guidance.", user_result.stdout)
        self.assertEqual((project_result.returncode, project_result.stderr), (0, ""))
        self.assertIn("Initial committed guidance.", project_result.stdout)

    def test_cli_install_validate_doctor_and_reference_from_project_directory(self) -> None:
        install = self.run_cli(
            "install", "--scope", "project", "--target", str(self.target),
            "--source", str(self.source), "--agent", "codex", "--apply",
        )
        self.assertEqual((install.returncode, install.stderr), (0, ""))
        self.assertIn("Scope: project", install.stdout)
        config = self.run_cli(
            "config", "set-source", "--source-root", str(self.source.parents[1]),
        )
        self.assertEqual((config.returncode, config.stderr), (0, ""))
        validate = self.run_cli("validate", "--scope", "project", "--target", str(self.target))
        self.assertEqual((validate.returncode, validate.stderr), (0, ""))
        doctor = self.run_cli("doctor", "--target", str(self.target), "--summary")
        self.assertEqual((doctor.returncode, doctor.stderr), (0, ""))
        self.assertIn("Project Scope:\n  Target:", doctor.stdout)
        self.assertIn("Status: HEALTHY", doctor.stdout)
        user_doctor = self.run_cli("doctor", "--summary")
        self.assertEqual((user_doctor.returncode, user_doctor.stderr), (0, ""))
        self.assertIn("User Scope:\n  Status: NOT INSTALLED", user_doctor.stdout)
        reference = self.run_cli(
            "reference", "--skill", "sample-skill", "--path", "docs/reference.md",
            "--revision", "installed", "--scope", "project", "--target", str(self.target),
        )
        self.assertEqual((reference.returncode, reference.stderr), (0, ""))
        self.assertIn("Initial committed guidance.", reference.stdout)

    def test_cli_migrate_recover_doctor_sequence_uses_safe_project_scope_state(self) -> None:
        legacy = self.prepare_migration_source()
        source_repo = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=source_repo, replace=False)[0], 0
        )
        common = (
            "migrate", "--scope", "project", "--target", str(self.target),
            "--source", str(self.source), "--agents", "codex",
        )
        dry_run = self.run_cli(*common)
        self.assertEqual((dry_run.returncode, dry_run.stderr), (0, ""))
        self.assertIn("Operation: DRY RUN", dry_run.stdout)
        self.assertIn("Expected outcome if applied: COMPLETE", dry_run.stdout)
        self.assertTrue(legacy.is_dir())
        applied = self.run_cli(*common, "--apply")
        self.assertEqual((applied.returncode, applied.stderr), (0, ""))
        self.assertIn("Migration status (applied): COMPLETE", applied.stdout)
        self.assertFalse(legacy.exists())
        recovered = self.run_cli("recover", "--scope", "project", "--target", str(self.target))
        self.assertEqual((recovered.returncode, recovered.stderr), (0, ""))
        self.assertIn("No interrupted Skill transactions found", recovered.stdout)
        doctor = self.run_cli("doctor", "--target", str(self.target), "--summary")
        self.assertEqual((doctor.returncode, doctor.stderr), (0, ""))
        self.assertIn("Project Scope:\n  Target:", doctor.stdout)
        self.assertIn("Status: HEALTHY", doctor.stdout)
        no_change = self.run_cli(*common)
        self.assertEqual((no_change.returncode, no_change.stderr), (0, ""))
        self.assertIn("Planned changes: NONE", no_change.stdout)
        self.assertNotIn("pass --apply to migrate", no_change.stdout)

    def test_reference_uses_installed_commit_and_head_or_worktree_are_explicit(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        args = SimpleNamespace(
            command="reference",
            skill="sample-skill",
            path="docs/reference.md",
            revision="installed",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("Initial committed guidance.", stdout.getvalue())
        self.assertIn("source commit", stdout.getvalue())
        self.assertIn("Reference path: docs/reference.md", stdout.getvalue())
        self.assertIn("Source identity:", stdout.getvalue())

        reference_file = repository / "docs" / "reference.md"
        reference_file.write_text("# Versioned reference\n\nWorking tree guidance.\n", encoding="utf-8")
        args.revision = "installed"
        stdout = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                result = manage_skills._run(args)
        self.assertEqual(result, 0)
        self.assertIn("Initial committed guidance.", stdout.getvalue())
        args.revision = "working-tree"
        stdout = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                result = manage_skills._run(args)
        self.assertEqual(result, 0)
        self.assertIn("Working tree guidance.", stdout.getvalue())
        self.assertIn("uncommitted", stdout.getvalue())
        self.assertIn("Source identity:", stdout.getvalue())

        head_only = repository / "docs" / "head-only.md"
        head_only.write_text("Committed after Skill installation.\n", encoding="utf-8")
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "add newer reference")
        args.path = "docs/head-only.md"
        args.revision = "installed"
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        self.assertEqual(result, 2)
        self.assertIn("does not exist at Git commit", stderr.getvalue())
        args.revision = "head"
        stdout = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                result = manage_skills._run(args)
        self.assertEqual(result, 0)
        self.assertIn("Committed after Skill installation.", stdout.getvalue())
        self.assertIn("Source identity:", stdout.getvalue())

    def test_installed_reference_is_independent_of_checkout_head_and_other_skills(self) -> None:
        repository = self.source.parents[1]
        unrelated_skill = self.source / "unrelated-skill"
        unrelated_skill.mkdir()
        (unrelated_skill / "SKILL.md").write_text(
            "---\nname: unrelated-skill\ndescription: Unrelated valid fixture.\n---\n",
            encoding="utf-8",
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "add unrelated fixture skill")
        base_commit = self.git(repository, "rev-parse", "HEAD")
        self.git(repository, "checkout", "-qb", "installed-reference")
        self.write_skill("sample-skill", "installed branch")
        (repository / "docs" / "reference.md").write_text(
            "Installed branch reference.\n", encoding="utf-8"
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "installed reference version")
        installed_commit = self.git(repository, "rev-parse", "HEAD")
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation("install", skills=["sample-skill"], apply=True)[0], 0
        )
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )

        self.git(repository, "checkout", "-qb", "unrelated-head", base_commit)
        (unrelated_skill / "SKILL.md").write_text(
            "broken unrelated Skill frontmatter\n", encoding="utf-8"
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "diverge and break unrelated skill")
        unrelated_head = self.git(repository, "rev-parse", "HEAD")
        self.assertNotEqual(unrelated_head, installed_commit)
        self.assertNotEqual(
            self.git(repository, "merge-base", installed_commit, unrelated_head),
            installed_commit,
        )

        for scope, target in (("user", None), ("project", self.target)):
            with self.subTest(scope=scope):
                result, output, error = self.run_reference(
                    path="docs/reference.md", scope=scope, target=target
                )
                self.assertEqual((result, error), (0, ""))
                self.assertIn("Installed branch reference.", output)
                self.assertIn(installed_commit, output)

        (unrelated_skill / "SKILL.md").write_text(
            "another invalid uncommitted edit\n", encoding="utf-8"
        )
        result, output, error = self.run_reference(path="docs/reference.md")
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Installed branch reference.", output)

    def test_reference_reads_allowlisted_root_files_and_rejects_other_root_paths(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )

        for filename in ("README.md", "AGENTS.md", "REVIEW.md", "REVIEWS.md"):
            with self.subTest(filename=filename):
                result, output, error = self.run_reference(path=filename)
                self.assertEqual((result, error), (0, ""))
                self.assertIn("Root reference fixture.", output)

        self.git(repository, "rm", "REVIEWS.md")
        self.git(repository, "commit", "-qm", "retire legacy review filename")
        result, output, error = self.run_reference(
            path="REVIEWS.md", revision="installed"
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Root reference fixture.", output)
        result, _output, error = self.run_reference(path="REVIEWS.md", revision="head")
        self.assertEqual(result, 2)
        self.assertIn("does not exist at Git commit", error)

        result, _output, error = self.run_reference(path="LICENSE.md")
        self.assertEqual(result, 2)
        self.assertIn("must be under docs/", error)
        result, _output, error = self.run_reference(path="docs/subdir")
        self.assertEqual(result, 2)
        self.assertIn("not a regular Git file", error)

    def test_reference_path_rejects_traversal_absolute_and_invalid_roots(self) -> None:
        for path in (
            "",
            "../outside.md",
            "docs/../../outside.md",
            "/etc/passwd",
            "C:/Windows/win.ini",
            "docs\\reference.md",
            "docs//reference.md",
            "docs/./reference.md",
            "LICENSE.md",
            "scripts/manage_skills.py",
        ):
            with self.subTest(path=path):
                with self.assertRaises(manage_skills.SkillManagementError):
                    manage_skills._safe_reference_path(path)

        self.assertEqual(manage_skills._safe_reference_path("docs/reference.md"), "docs/reference.md")
        self.assertEqual(manage_skills._safe_reference_path(".agents/skills/sample/SKILL.md"), ".agents/skills/sample/SKILL.md")
        self.assertEqual(manage_skills._safe_reference_path("prompts/old.md"), "prompts/old.md")
        self.assertEqual(manage_skills._safe_reference_path("REVIEW.md"), "REVIEW.md")
        self.assertEqual(manage_skills._safe_reference_path("REVIEWS.md"), "REVIEWS.md")

    def test_reference_reads_deleted_prompt_from_installed_commit_only(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        self.git(repository, "rm", "-r", "prompts")
        self.git(repository, "commit", "-qm", "remove current prompts")

        result, output, error = self.run_reference(
            path="prompts/bootstrap-from-design.md", revision="installed"
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Historical prompt content.", output)

        result, _output, error = self.run_reference(
            path="prompts/bootstrap-from-design.md", revision="head"
        )
        self.assertEqual(result, 2)
        self.assertIn("does not exist at Git commit", error)

    def test_reference_git_tree_accepts_only_regular_files_and_parses_exact_paths(self) -> None:
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        regular = repository / "docs" / "reference with space 日本語.md"
        regular.write_text("unicode and space path\n", encoding="utf-8")
        executable = repository / "docs" / "executable.md"
        executable.write_text("executable regular file\n", encoding="utf-8")
        self.git(
            repository,
            "add",
            "docs/reference with space 日本語.md",
            "docs/executable.md",
        )
        symlink_blob = subprocess.run(
            ["git", "-C", str(repository), "hash-object", "-w", "--stdin"],
            input=b"reference.md",
            capture_output=True,
            check=True,
        ).stdout.decode("ascii").strip()
        self.git(
            repository,
            "update-index",
            "--add",
            "--cacheinfo",
            f"120000,{symlink_blob},docs/symlink.md",
        )
        self.git(repository, "update-index", "--chmod=+x", "docs/executable.md")
        self.git(repository, "commit", "-qm", "add reference entry types")
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        for path, expected in (
            ("docs/reference with space 日本語.md", "unicode and space path"),
            ("docs/executable.md", "executable regular file"),
        ):
            with self.subTest(path=path):
                result, output, error = self.run_reference(path=path, revision="head")
                self.assertEqual((result, error), (0, ""))
                self.assertIn(expected, output)

        symlink = repository / "docs" / "symlink.md"
        symlink.write_text("working tree regular file\n", encoding="utf-8")
        result, output, error = self.run_reference(
            path="docs/symlink.md", revision="working-tree"
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("working tree regular file", output)
        for revision in ("installed", "head"):
            if revision == "installed":
                result, _output, error = self.run_reference(
                    path="docs/symlink.md",
                    revision=revision,
                    scope="project",
                    target=self.target,
                )
            else:
                result, _output, error = self.run_reference(
                    path="docs/symlink.md", revision=revision
                )
            self.assertEqual(result, 2)
            self.assertIn("not a regular Git file", error)

        symlink.unlink()
        for path in ("docs/subdir", "docs/not-present.md"):
            with self.subTest(path=path):
                result, _output, error = self.run_reference(path=path, revision="head")
                self.assertEqual(result, 2)
                if path == "docs/not-present.md":
                    self.assertIn("does not exist at Git commit", error)
                else:
                    self.assertIn("not a regular Git file", error)

        self.git(
            repository,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{self.git(repository, 'rev-parse', 'HEAD')},docs/submodule",
        )
        self.git(repository, "commit", "-qm", "add submodule tree entry")
        result, _output, error = self.run_reference(
            path="docs/submodule", revision="head"
        )
        self.assertEqual(result, 2)
        self.assertIn("not a regular Git file", error)

        original_git = manage_skills._git

        def malformed_tree(root: Path, *arguments: str, check: bool = True):
            if arguments and arguments[0] == "ls-tree":
                return subprocess.CompletedProcess(
                    ["git", *arguments], 0, "not-tree-data\0", ""
                )
            return original_git(root, *arguments, check=check)

        with patch.object(manage_skills, "_git", side_effect=malformed_tree):
            result, output, error = self.run_reference(
                path="docs/reference.md", revision="head"
            )
        self.assertEqual(result, 2)
        self.assertIn("malformed tree data", error)
        self.assertEqual(output, "")

    def test_reference_failures_never_emit_partial_success_metadata(self) -> None:
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        original_git = manage_skills._git_bytes

        def failed_read(root: Path, *arguments: str):
            if arguments and arguments[0] == "show":
                return subprocess.CompletedProcess(
                    ["git", *arguments], 1, b"partial content", b"injected read error"
                )
            return original_git(root, *arguments)

        with patch.object(manage_skills, "_git_bytes", side_effect=failed_read):
            result, output, error = self.run_reference(
                path="docs/reference.md", revision="head"
            )
        self.assertEqual(result, 2)
        self.assertIn("could not read reference", error)
        self.assertEqual(output, "")

        invalid_utf8 = repository / "docs" / "invalid-utf8.md"
        invalid_utf8.write_bytes(b"\xff\xfe")
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "add invalid UTF-8 fixture")
        result, output, error = self.run_reference(
            path="docs/invalid-utf8.md", revision="head"
        )
        self.assertEqual(result, 2)
        self.assertIn("utf-8", error.lower())
        self.assertEqual(output, "")

        reference_path = repository / "docs" / "reference.md"
        original_read_text = Path.read_text

        def denied_reference(path: Path, *args, **kwargs):
            if paths_equal(path, reference_path):
                raise PermissionError("injected permission denial")
            return original_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", denied_reference):
            result, output, error = self.run_reference(
                path="docs/reference.md", revision="working-tree"
            )
        self.assertEqual(result, 2)
        self.assertIn("permission", error.lower())
        self.assertEqual(output, "")

    def test_reference_scope_manifests_are_independent(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation(
                "install", agents=["codex"], skills=["sample-skill"], apply=True
            )[0],
            0,
        )
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )

        user_result, user_output, user_error = self.run_reference(
            path="docs/reference.md", scope="user"
        )
        project_result, project_output, project_error = self.run_reference(
            path="docs/reference.md", scope="project", target=self.target
        )
        self.assertEqual((user_result, user_error), (0, ""))
        self.assertEqual((project_result, project_error), (0, ""))
        self.assertIn("Initial committed guidance.", user_output)
        self.assertIn("Initial committed guidance.", project_output)

        user_record = self.user_home / ".devconcord/skills-manifest.json"
        user_manifest = json.loads(user_record.read_text(encoding="utf-8"))
        user_skill = user_manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        user_skill["source_repository"] = "https://example.invalid/other-source.git"
        user_record.write_text(json.dumps(user_manifest), encoding="utf-8")

        result, _output, error = self.run_reference(path="docs/reference.md", scope="user")
        self.assertEqual(result, 2)
        self.assertIn("source identity differs", error)
        self.assertEqual(_output, "")
        result, output, error = self.run_reference(
            path="docs/reference.md", scope="project", target=self.target
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Initial committed guidance.", output)

    def test_reference_uses_requesting_skill_commit_in_user_and_project_scope(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation("install", skills=["sample-skill"], apply=True)[0],
            0,
        )
        repository = self.source.parents[1]
        source_commit = self.git(repository, "rev-parse", "HEAD")
        self.write_skill("devconcord-reference", "helper-at-newer-commit")
        reference_file = repository / "docs" / "reference.md"
        reference_file.write_text(
            "# Versioned reference\n\nGuidance added with the helper Skill.\n",
            encoding="utf-8",
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "add reference Skill at newer revision")
        helper_commit = self.git(repository, "rev-parse", "HEAD")

        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["devconcord-reference"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation(
                "install", skills=["devconcord-reference"], apply=True
            )[0],
            0,
        )
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0],
            0,
        )
        self.assertEqual(
            self.run_user_operation("validate", source=self.source)[0], 0
        )
        self.assertEqual(self.run_operation("validate")[0], 0)

        for scope, target in (("user", None), ("project", self.target)):
            with self.subTest(scope=scope):
                requester_result, requester_output, requester_error = self.run_reference(
                    path="docs/reference.md",
                    scope=scope,
                    target=target,
                    skill="sample-skill",
                )
                helper_result, helper_output, helper_error = self.run_reference(
                    path="docs/reference.md",
                    scope=scope,
                    target=target,
                    skill="devconcord-reference",
                )
                self.assertEqual((requester_result, requester_error), (0, ""))
                self.assertIn("Initial committed guidance.", requester_output)
                self.assertIn(source_commit, requester_output)
                self.assertEqual((helper_result, helper_error), (0, ""))
                self.assertIn("Guidance added with the helper Skill.", helper_output)
                self.assertIn(helper_commit, helper_output)

    def test_reference_rejects_missing_installed_source_commit(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        manifest_path = self.user_home / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        record["source_commit"] = "f" * 40
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result, _output, error = self.run_reference(path="docs/reference.md")

        self.assertEqual(result, 2)
        self.assertIn("recorded source commit is missing", error)
        self.assertEqual(_output, "")

    def test_reference_installed_verifies_source_commit_and_hash_in_each_scope(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation("install", skills=["sample-skill"], apply=True)[0], 0
        )
        repository = self.source.parents[1]
        pinned_commit = self.git(repository, "rev-parse", "HEAD")
        reference = repository / "docs" / "reference.md"
        reference.write_text("new committed guidance\n", encoding="utf-8")
        (self.source / "sample-skill" / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Updated fixture Skill.\n---\n\nChanged.\n",
            encoding="utf-8",
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "change reference only")
        later_commit = self.git(repository, "rev-parse", "HEAD")
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )

        for scope, target in (("user", None), ("project", self.target)):
            with self.subTest(scope=scope):
                manifest_path = (
                    self.user_home / ".devconcord/skills-manifest.json"
                    if scope == "user"
                    else self.target / ".devconcord/skills-manifest.json"
                )
                installed_skill = (
                    self.user_home / ".agents/skills/sample-skill"
                    if scope == "user"
                    else self.target / ".agents/skills/sample-skill"
                )
                original_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                record = original_manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
                installed_before = manage_skills._recorded_package_digest(
                    installed_skill, record
                )

                for changed_field, changed_value, diagnostic in (
                    ("source_commit", later_commit, "source_tree_sha256"),
                    ("source_tree_sha256", "0" * 64, "source_tree_sha256"),
                ):
                    changed = json.loads(json.dumps(original_manifest))
                    changed_record = changed["packages"][".agents/skills"]["skills"]["sample-skill"]
                    changed_record[changed_field] = changed_value
                    manifest_path.write_text(json.dumps(changed), encoding="utf-8")
                    manifest_before = manifest_path.read_bytes()

                    result, output, error = self.run_reference(
                        path="docs/reference.md", scope=scope, target=target
                    )

                    self.assertEqual(result, 2)
                    self.assertIn(diagnostic, error)
                    self.assertEqual(output, "")
                    self.assertEqual(manifest_path.read_bytes(), manifest_before)
                    self.assertEqual(
                        manage_skills._recorded_package_digest(installed_skill, record),
                        installed_before,
                    )
                manifest_path.write_text(json.dumps(original_manifest), encoding="utf-8")
                self.assertEqual(record["source_commit"], pinned_commit)

    def test_reference_installed_rejects_dirty_source_and_local_skill_edits(self) -> None:
        source_repo = self.source.parents[1]
        ignored = self.source / "sample-skill" / "ignored.local"
        (source_repo / ".gitignore").write_text("*.local\n", encoding="utf-8")
        self.git(source_repo, "add", ".gitignore")
        self.git(source_repo, "commit", "-qm", "ignore local files")
        ignored.write_text("uncommitted source content\n", encoding="utf-8")
        self.assertEqual(
            self.run_operation(
                "install", skills=["sample-skill"], apply=True, allow_dirty_source=True
            )[0],
            0,
        )
        self.assertEqual(
            self.run_config("set-source", source_root=source_repo, replace=False)[0], 0
        )
        result, output, error = self.run_reference(path="docs/reference.md", scope="project", target=self.target)
        self.assertEqual(result, 2)
        self.assertIn("source was dirty", error)
        self.assertEqual(output, "")

        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        record["source_dirty"] = False
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        installed = self.target / ".agents/skills/sample-skill/SKILL.md"
        installed.write_text("local edit\n", encoding="utf-8")
        result, output, error = self.run_reference(path="docs/reference.md", scope="project", target=self.target)
        self.assertEqual(result, 2)
        self.assertIn("locally modified", error)
        self.assertEqual(output, "")

    @unittest.skipIf(os.name == "nt", "symlink behavior is platform-specific")
    def test_reference_working_tree_refuses_symlink_escape(self) -> None:
        repository = self.source.parents[1]
        outside = self.root / "outside.md"
        outside.write_text("outside content\n", encoding="utf-8")
        link = repository / "docs" / "outside-link.md"
        link.symlink_to(outside)
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )

        result, _output, error = self.run_reference(
            path="docs/outside-link.md", revision="working-tree"
        )

        self.assertEqual(result, 2)
        self.assertIn("symlinked local reference path", error)

    def test_doctor_reports_user_project_name_collisions_without_modifying_either_scope(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        project_skill = self.target / ".agents" / "skills" / "sample-skill"
        project_skill.mkdir(parents=True)
        project_skill.joinpath("SKILL.md").write_text(
            "project-owned version\n", encoding="utf-8"
        )
        before_global = (
            self.user_home / ".agents" / "skills" / "sample-skill" / "SKILL.md"
        ).read_bytes()
        before_project = project_skill.joinpath("SKILL.md").read_bytes()
        args = SimpleNamespace(command="doctor", target=self.target)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("same-name User/Project Skill", stdout.getvalue())
        self.assertIn("DevConcord Skill Health", stdout.getvalue())
        self.assertIn("Status: NEEDS ATTENTION", stdout.getvalue())
        self.assertIn("Most important issue: WARNING: same-name User/Project Skill", stdout.getvalue())
        self.assertIn("Recommended next action: Compare both Skill definitions", stdout.getvalue())
        self.assertIn("precedence are not normalized", stdout.getvalue())
        self.assertEqual(
            (self.user_home / ".agents" / "skills" / "sample-skill" / "SKILL.md").read_bytes(),
            before_global,
        )
        self.assertEqual(project_skill.joinpath("SKILL.md").read_bytes(), before_project)

    def test_doctor_reports_project_health_independently_when_user_scope_is_uninstalled(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        project_manifest = self.target / ".devconcord/skills-manifest.json"
        before_manifest = project_manifest.read_bytes()
        before_skill = (self.target / ".agents/skills/sample-skill/SKILL.md").read_bytes()

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("User Scope:\n  Status: NOT INSTALLED", output)
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("  Status: HEALTHY", output)
        self.assertIn("Requested Project Scope is healthy", output)
        self.assertNotIn("Detailed diagnostics", output)
        self.assertEqual(project_manifest.read_bytes(), before_manifest)
        self.assertEqual((self.target / ".agents/skills/sample-skill/SKILL.md").read_bytes(), before_skill)

    def test_doctor_reports_user_health_independently_when_project_scope_is_uninstalled(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("User Scope:\n  Status: HEALTHY", output)
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("  Status: NOT INSTALLED", output)
        self.assertIn("Install DevConcord only if you intend to use it in this scope", output)

    def test_doctor_reports_both_valid_scopes_separately(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("User Scope:\n  Status: HEALTHY", output)
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("  Status: HEALTHY", output)

    def test_doctor_rejects_unverified_unified_source_provenance(self) -> None:
        self.write_skill("devconcord", "v1")
        self.git(self.source.parents[1], "add", ".")
        self.git(self.source.parents[1], "commit", "-qm", "add unified package")
        self.assertEqual(
            self.run_operation("install", skills=["devconcord"], apply=True)[0], 0
        )
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packages"][".agents/skills"]["skills"]["devconcord"]["source_repository"] = "https://invalid.example/other.git"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        before_manifest = manifest_path.read_bytes()

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("Status: NEEDS ATTENTION", output.split("Project Scope:", 1)[1])
        self.assertIn("source provenance is not verified", output)
        self.assertEqual(manifest_path.read_bytes(), before_manifest)

    def test_doctor_reports_project_hash_mismatch_without_changing_legacy_exit_code(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        installed = self.target / ".agents/skills/sample-skill/SKILL.md"
        installed.write_text("local edit\n", encoding="utf-8")

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("Status: NEEDS ATTENTION", output.split("Project Scope:", 1)[1])
        self.assertIn("differs from its manifest", output)
        self.assertEqual(installed.read_text(encoding="utf-8"), "local edit\n")

    def test_doctor_finding_reports_unified_package_hash_mismatch_read_only(self) -> None:
        self.write_skill("devconcord", "v1")
        repository = self.source.parents[1]
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-qm", "add unified package")
        self.assertEqual(
            self.run_operation("install", skills=["devconcord"], apply=True)[0], 0
        )
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        installed = self.target / ".agents/skills/devconcord/SKILL.md"
        installed.write_text("local package edit\n", encoding="utf-8")
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()

        diagnosis = manage_skills._diagnose_scope(
            self.target,
            scope="Project Scope",
            discovery_paths=manage_skills.DISCOVERY_PATHS,
            source_root=repository,
        )
        result, output, error = self.run_doctor(target=self.target)

        self.assertEqual((diagnosis.status, diagnosis.exit_code), ("NEEDS ATTENTION", 0))
        self.assertTrue(
            any(finding.code == "unified_package_mismatch" for finding in diagnosis.findings)
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Status: NEEDS ATTENTION", output)
        self.assertIn("Unified package: present or recorded; state differs", output)
        self.assertEqual(manifest_path.read_bytes(), before_manifest)
        self.assertEqual(installed.read_text(encoding="utf-8"), "local package edit\n")

    def test_doctor_continues_project_diagnosis_after_user_manifest_corruption_read_only(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        manifest = self.user_home / ".devconcord/skills-manifest.json"
        manifest.write_text("{broken\n", encoding="utf-8")
        before_manifest = manifest.read_bytes()
        project_manifest = (self.target / ".devconcord/skills-manifest.json").read_bytes()

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (2, ""))
        self.assertIn("User Scope:\n  Status: NEEDS ATTENTION", output)
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("  Status: HEALTHY", output)
        self.assertIn("Requested Project Scope is healthy.", output)
        self.assertNotIn("Overall: Requested Project Scope is healthy.", output)
        self.assertEqual(manifest.read_bytes(), before_manifest)
        self.assertEqual((self.target / ".devconcord/skills-manifest.json").read_bytes(), project_manifest)

    @unittest.skipIf(os.name == "nt", "symlink behavior is platform-specific")
    def test_doctor_continues_user_diagnosis_after_project_discovery_symlink(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        outside = self.root / "outside-skills"
        outside.mkdir()
        (self.target / ".agents").mkdir()
        (self.target / ".agents/skills").symlink_to(outside, target_is_directory=True)

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (2, ""))
        self.assertIn("User Scope:\n  Status: HEALTHY", output)
        self.assertIn("Project Scope:\n  Target:", output)
        self.assertIn("  Status: NEEDS ATTENTION", output)
        self.assertIn("symlinked destination path", output)

    def test_doctor_summary_suppresses_detail_without_changing_diagnostic_state(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        summary_result, summary, summary_error = self.run_doctor(target=self.target, summary=True)
        detail_result, detailed, detail_error = self.run_doctor(target=self.target)

        self.assertEqual((summary_result, detail_result), (0, 0))
        self.assertEqual((summary_error, detail_error), ("", ""))
        self.assertEqual(
            [line for line in summary.splitlines() if "Status:" in line],
            [line for line in detailed.splitlines() if "Status:" in line],
        )
        self.assertIn("Detailed diagnostics", detailed)
        self.assertNotIn("Detailed diagnostics", summary)

    def test_blocked_legacy_status_cannot_be_downgraded_without_a_finding(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)

        with patch.object(
            manage_skills,
            "_diagnose_legacy_state",
            return_value=manage_skills.LegacyDiagnosis("BLOCKED"),
        ):
            diagnosis = manage_skills._diagnose_scope(
                self.target,
                scope="Project Scope",
                discovery_paths=manage_skills.DISCOVERY_PATHS,
                source_root=self.source.parents[1],
            )

        self.assertEqual((diagnosis.status, diagnosis.exit_code, diagnosis.findings),
                         ("NEEDS ATTENTION", 0, ()))

    def test_doctor_summary_keeps_same_kind_findings_for_distinct_skills(self) -> None:
        self.write_skill("second-skill", "v1")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "add second Skill")
        self.assertEqual(
            self.run_operation(
                "install", skills=["sample-skill", "second-skill"], apply=True
            )[0],
            0,
        )
        for name in ("sample-skill", "second-skill"):
            (self.target / ".agents/skills" / name / "SKILL.md").write_text(
                "local change\n", encoding="utf-8"
            )

        result, output, error = self.run_doctor(target=self.target, summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("differs from its manifest: .agents/skills/sample-skill", output)
        self.assertIn("differs from its manifest: .agents/skills/second-skill", output)

    def test_user_scope_health_is_separate_from_unrelated_source_validation(self) -> None:
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_user_operation(
                "install",
                agents=["codex"],
                skills=["sample-skill"],
                apply=True,
                source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        (self.source / "unrelated-broken-skill").mkdir()

        result, output, error = self.run_user_operation("validate")
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Validated 1 DevConcord-managed Skill package", output)
        self.assertIn("separate from User Scope installation health", output)
        self.assertIn("source Skill validation failed", output)

        result, output, error = self.run_user_operation("doctor")
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Status: HEALTHY", output)
        self.assertIn("Validated 1 DevConcord-managed Skill package", output)
        self.assertIn("separate from User Scope installation health", output)

        args = SimpleNamespace(
            command="validate", scope=None, target=None, source=self.source
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            source_result = manage_skills._run(args)
        self.assertEqual(source_result, 1)
        self.assertIn("unrelated-broken-skill", stderr.getvalue())

        installed_skill = self.user_home / ".agents/skills/sample-skill/SKILL.md"
        installed_skill.write_text("locally modified\n", encoding="utf-8")
        result, _output, error = self.run_user_operation("validate")
        self.assertEqual(result, 1)
        self.assertIn("installed Skill differs from its manifest hash", error)

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
        self.assertEqual(record["hash_version"], 2)
        self.assertEqual(record["source_executable_files"], [])
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

    def test_install_validate_sync_validate_preserves_digest_contract(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        self.assertEqual(self.run_validation()[0], 0)

        installed = self.target / ".agents" / "skills" / "sample-skill"
        (installed / "unexpected-empty-directory").mkdir()
        result, _, error = self.run_validation()
        self.assertEqual((result, error), (0, ""))
        unexpected_file = installed / "unexpected-empty-directory" / "unexpected.txt"
        unexpected_file.write_text("local modification\n", encoding="utf-8")
        result, _, error = self.run_validation()
        self.assertEqual(result, 1)
        self.assertIn("differs from manifest hash", error)
        unexpected_file.unlink()
        (installed / "unexpected-empty-directory").rmdir()
        self.assertEqual(self.run_validation()[0], 0)

        self.write_skill("sample-skill", "v2")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "v2")
        self.assertEqual(self.run_operation("sync", apply=True)[0], 0)
        self.assertEqual(self.run_validation()[0], 0)

    def test_target_validation_detects_deleted_managed_skill_file(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        details = (
            self.target
            / ".agents"
            / "skills"
            / "sample-skill"
            / "references"
            / "details.md"
        )
        self.assertTrue(details.is_file())
        details.unlink()

        result, _, error = self.run_validation()

        self.assertEqual(result, 1)
        self.assertIn("differs from manifest hash", error)

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

    def test_install_ignores_untracked_empty_directories_in_clean_skill(self) -> None:
        (self.source / "sample-skill" / "references" / "nested").mkdir(parents=True)

        result, _, error = self.run_operation("install", apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertTrue(
            (self.target / ".agents" / "skills" / "sample-skill" / "SKILL.md").is_file()
        )

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

    def test_legacy_manifest_hashes_are_verified_then_migrated(self) -> None:
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        record = manifest["packages"][".agents/skills"]["skills"]["sample-skill"]
        skill_dir = self.target / ".agents" / "skills" / "sample-skill"
        record.pop("hash_version")
        record.pop("source_executable_files")
        record["source_tree_sha256"] = manage_skills._git_skill_digest(
            self.source,
            record["source_commit"],
            "sample-skill",
            legacy=True,
        )
        record["installed_tree_sha256"] = manage_skills.tree_digest(skill_dir)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(self.run_validation()[0], 0)
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        result, output, error = self.run_reference(
            path="docs/reference.md", scope="project", target=self.target
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Initial committed guidance.", output)

        result, _, error = self.run_operation("sync", apply=True)

        self.assertEqual((result, error), (0, ""))
        migrated = json.loads(manifest_path.read_text(encoding="utf-8"))
        migrated_record = migrated["packages"][".agents/skills"]["skills"]["sample-skill"]
        self.assertEqual(migrated_record["hash_version"], 2)
        self.assertEqual(migrated_record["source_executable_files"], [])
        self.assertEqual(self.run_validation()[0], 0)

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
                        manage_skills._portable_tree_digest(
                            installed_skill,
                            tuple(
                                package["skills"]["sample-skill"][
                                    "source_executable_files"
                                ]
                            ),
                        ),
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

    def test_source_revision_selects_origin_or_unique_remote_and_rejects_ambiguity(self) -> None:
        repository = self.source.parents[1]
        self.assertTrue(
            manage_skills.source_revision(self.source)[2].startswith("local-git-sha256:")
        )
        self.git(repository, "remote", "add", "upstream", "https://example.com/team/upstream.git")
        self.assertEqual(
            manage_skills.source_revision(self.source)[2], "example.com/team/upstream"
        )
        self.git(repository, "remote", "rename", "upstream", "origin")
        self.assertEqual(
            manage_skills.source_revision(self.source)[2], "example.com/team/upstream"
        )
        self.git(repository, "remote", "add", "fork", "git@example.com:team/fork.git")
        self.assertEqual(
            manage_skills.source_revision(self.source)[2], "example.com/team/upstream"
        )
        self.git(
            repository,
            "remote",
            "set-url",
            "origin",
            "git@example.com:team/upstream.git",
        )
        self.assertEqual(
            manage_skills.source_revision(self.source)[2], "example.com/team/upstream"
        )
        self.git(
            repository,
            "remote",
            "set-url",
            "origin",
            "https://example.com/team/other.git",
        )
        self.assertEqual(
            manage_skills.source_revision(self.source)[2], "example.com/team/other"
        )
        self.git(repository, "remote", "rename", "origin", "selected-origin")
        with self.assertRaisesRegex(manage_skills.SkillManagementError, "ambiguous"):
            manage_skills.source_revision(self.source)

    def test_ambiguous_remotes_block_sync_without_mutating_either_scope(self) -> None:
        repository = self.source.parents[1]
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        self.assertEqual(
            self.run_operation("install", skills=["sample-skill"], apply=True)[0], 0
        )
        self.assertEqual(
            self.run_config("set-source", source_root=repository, replace=False)[0], 0
        )
        user_manifest = self.user_home / ".devconcord/skills-manifest.json"
        project_manifest = self.target / ".devconcord/skills-manifest.json"
        user_skill = self.user_home / ".agents/skills/sample-skill/SKILL.md"
        project_skill = self.target / ".agents/skills/sample-skill/SKILL.md"
        snapshots = {
            path: path.read_bytes()
            for path in (user_manifest, project_manifest, user_skill, project_skill)
        }
        self.git(repository, "remote", "add", "upstream", "https://example.com/team/upstream.git")
        self.git(repository, "remote", "add", "fork", "https://example.com/team/fork.git")

        user_result, _, user_error = self.run_user_operation("sync", apply=True)
        project_result, _, project_error = self.run_operation("sync", apply=True)

        self.assertEqual(user_result, 2)
        self.assertEqual(project_result, 2)
        self.assertIn("ambiguous", user_error)
        self.assertIn("ambiguous", project_error)
        for path, expected in snapshots.items():
            self.assertEqual(path.read_bytes(), expected)

        user_result, _, user_error = self.run_user_operation("rebind-source", apply=True)
        project_result, _, project_error = self.run_operation("rebind-source", apply=True)
        self.assertEqual((user_result, project_result), (2, 2))
        self.assertIn("ambiguous", user_error)
        self.assertIn("ambiguous", project_error)
        for scope, target in (("user", None), ("project", self.target)):
            result, output, error = self.run_reference(
                path="docs/reference.md", scope=scope, target=target
            )
            self.assertEqual(result, 2)
            self.assertEqual(output, "")
            self.assertIn("ambiguous", error)
        for path, expected in snapshots.items():
            self.assertEqual(path.read_bytes(), expected)

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
            if paths_equal(path, manifest_file):
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
            if paths_equal(Path(destination), installed_file.parent):
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
            if paths_equal(path, manifest_path):
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
            if paths_equal(path, manifest_path):
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
            if paths_equal(Path(path), target_skill):
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

    def test_process_liveness_check_handles_running_and_missing_processes(self) -> None:
        self.assertTrue(manage_skills._process_is_running(os.getpid()))
        self.assertFalse(manage_skills._process_is_running(2**31 - 1))

    def test_recovery_preserves_staging_without_a_valid_journal(self) -> None:
        orphan = self.target / ".devconcord" / "skills-transactions" / "orphan"
        (orphan / "staged").mkdir(parents=True)
        (orphan / "backups").mkdir()

        result, _, error = self.run_recovery(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("no valid journal", error)
        self.assertTrue(orphan.is_dir())

    def test_repository_identity_preserves_nonstandard_ports_and_normalizes_defaults(self) -> None:
        identities = {
            "https://git.example.com:8443/team/repo.git": "git.example.com:8443/team/repo",
            "https://git.example.com:9443/team/repo.git": "git.example.com:9443/team/repo",
            "https://git.example.com:443/team/repo.git": "git.example.com/team/repo",
            "ssh://git@git.example.com:22/team/repo.git": "git.example.com/team/repo",
            "git://git.example.com:9418/team/repo.git": "git.example.com/team/repo",
            "ssh://user@[2001:db8::1]:2222/team/repo.git": "[2001:db8::1]:2222/team/repo",
            "git@[2001:db8::1]:team/repo.git": "[2001:db8::1]/team/repo",
        }
        for remote, expected in identities.items():
            with self.subTest(remote=remote):
                self.assertEqual(manage_skills._repository_identity(remote), expected)

        self.assertNotEqual(
            manage_skills._repository_identity("https://git.example.com:8443/team/repo.git"),
            manage_skills._repository_identity("https://git.example.com:9443/team/repo.git"),
        )
        self.assertFalse(
            manage_skills._source_identities_match(
                "git.example.com/team/repo",
                "git.example.com:8443/team/repo",
            )
        )
        self.assertTrue(
            manage_skills._source_identities_match(
                "git.example.com/team/repo",
                "https://git.example.com:443/team/repo.git",
            )
        )

    def test_source_repository_identifier_redacts_credentials_and_query(self) -> None:
        results = [
            SimpleNamespace(returncode=0, stdout="/source/repo\n"),
            SimpleNamespace(returncode=0, stdout="abc123\n"),
            SimpleNamespace(returncode=0, stdout=""),
            SimpleNamespace(returncode=0, stdout="origin\n"),
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


    def prepare_migration_source(self, *, agents: list[str] | None = None) -> Path:
        shutil.rmtree(self.source / "sample-skill")
        self.commit_skill("devconcord-repository-review", "legacy")
        selected_agents = agents or ["codex"]
        self.assertEqual(
            self.run_operation(
                "install", agents=selected_agents,
                skills=["devconcord-repository-review"], apply=True,
                allow_duplicate_discovery=(
                    "copilot" in selected_agents
                    and "codex" in selected_agents
                    and "claude" in selected_agents
                ),
            )[0],
            0,
        )
        shutil.rmtree(self.source / "devconcord-repository-review")
        self.commit_skill("devconcord", "unified")
        return self.target / ".agents" / "skills" / "devconcord-repository-review"

    def prepare_user_migration_source(
        self, *, agents: list[str] | None = None, allow_duplicate_discovery: bool = False
    ) -> Path:
        shutil.rmtree(self.source / "sample-skill")
        self.commit_skill("devconcord-repository-review", "legacy")
        result, _, error = self.run_user_operation(
            "install", agents=agents or ["codex"],
            skills=["devconcord-repository-review"], apply=True, source=self.source,
            allow_duplicate_discovery=allow_duplicate_discovery,
        )
        self.assertEqual((result, error), (0, ""))
        shutil.rmtree(self.source / "devconcord-repository-review")
        self.commit_skill("devconcord", "unified")
        return self.user_home / ".agents" / "skills" / "devconcord-repository-review"

    def run_user_migration(
        self, *, apply: bool = False, allow_duplicate_discovery: bool = False,
        agents: list[str] | None = None,
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="migrate", scope="user", target=None, source=self.source,
            agents=agents, apply=apply,
            allow_duplicate_discovery=allow_duplicate_discovery,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_user_scope_legacy_migration_is_explicit_and_transactional(self) -> None:
        legacy = self.prepare_user_migration_source()
        before = (self.user_home / ".devconcord/skills-manifest.json").read_bytes()
        result, output, error = self.run_user_migration()
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Dry run only", output)
        self.assertTrue(legacy.is_dir())
        self.assertEqual((self.user_home / ".devconcord/skills-manifest.json").read_bytes(), before)

        result, _, error = self.run_user_migration(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertFalse(legacy.exists())
        self.assertTrue((self.user_home / ".agents/skills/devconcord/SKILL.md").is_file())
        manifest = json.loads((self.user_home / ".devconcord/skills-manifest.json").read_text())
        self.assertEqual(set(manifest["packages"][".agents/skills"]["skills"]), {"devconcord"})

    def test_user_migration_reports_and_preserves_legacy_copy_in_unmanaged_discovery_root(self) -> None:
        legacy = self.prepare_user_migration_source()
        external = self.user_home / ".copilot/skills/devconcord-repository-review"
        external.mkdir(parents=True)
        (external / "SKILL.md").write_text("external copy\n", encoding="utf-8")

        result, output, error = self.run_user_migration(apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Migration status (applied): PARTIAL", output)
        self.assertIn(".copilot/skills/devconcord-repository-review", output)
        self.assertFalse(legacy.exists())
        self.assertTrue(external.is_dir())

    def test_user_migration_explicit_source_bypasses_stale_user_config(self) -> None:
        self.prepare_user_migration_source()
        config = self.user_home / ".devconcord/config.json"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("not valid json\n", encoding="utf-8")

        result, output, error = self.run_user_migration()

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Dry run only", output)

    def test_migration_scopes_removals_to_requested_agent_destinations(self) -> None:
        shutil.rmtree(self.source / "sample-skill")
        self.commit_skill("devconcord-repository-review", "legacy")
        self.assertEqual(
            self.run_operation("install", agents=["codex", "claude"],
                               skills=["devconcord-repository-review"], apply=True)[0], 0
        )
        shutil.rmtree(self.source / "devconcord-repository-review")
        self.commit_skill("devconcord", "unified")
        args = SimpleNamespace(
            command="migrate", scope="project", target=self.target, source=self.source,
            agents=["codex"], apply=True,
        )
        stdout = io.StringIO(); stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertFalse((self.target / ".agents/skills/devconcord-repository-review").exists())
        self.assertTrue((self.target / ".claude/skills/devconcord-repository-review").is_dir())
        self.assertFalse((self.target / ".claude/skills/devconcord").exists())

    def run_migration(
        self, *, apply: bool = False, allow_duplicate_discovery: bool = False,
        agents: list[str] | None = None,
    ) -> tuple[int, str, str]:
        args = SimpleNamespace(
            command="migrate", scope="project", target=self.target, source=self.source,
            agents=agents, apply=apply,
            allow_duplicate_discovery=allow_duplicate_discovery,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = manage_skills._run(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_unified_migration_defaults_to_dry_run_then_applies_as_one_manifest_transition(self) -> None:
        legacy = self.prepare_migration_source()
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        before = manifest_path.read_bytes()

        result, output, error = self.run_migration()

        self.assertEqual((result, error), (0, ""))
        self.assertIn("remove: .agents/skills/devconcord-repository-review", output)
        self.assertIn("install: .agents/skills/devconcord", output)
        self.assertIn("Migration status (planned): COMPLETE", output)
        self.assertIn("Operation: DRY RUN", output)
        self.assertIn("Expected outcome if applied: COMPLETE", output)
        self.assertIn("Changes applied: NO", output)
        self.assertIn("rerun with --apply", output)
        self.assertIn("Migration operation: PLANNED", output)
        self.assertIn("Dry run only", output)
        self.assertTrue(legacy.is_dir())
        self.assertFalse((self.target / ".agents/skills/devconcord").exists())
        self.assertEqual(manifest_path.read_bytes(), before)

        result, output, error = self.run_migration(apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertLess(
            output.index("Migration transaction applied"),
            output.index("Migration status (applied): COMPLETE"),
        )
        self.assertIn("Removed legacy Skills (verified):", output)
        self.assertIn("Migration status (applied): COMPLETE", output)
        self.assertFalse(legacy.exists())
        self.assertTrue((self.target / ".agents/skills/devconcord/SKILL.md").is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["packages"][".agents/skills"]["skills"]), {"devconcord"})
        self.assertEqual(manage_skills._transaction_directories(self.target), [])
        self.assertEqual(self.run_operation("validate")[0], 0)
        applied_manifest = manifest_path.read_bytes()
        result, dry_run_output, error = self.run_migration()
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Operation: DRY RUN", dry_run_output)
        self.assertIn("Changes applied: NO", dry_run_output)
        self.assertIn("Planned changes: NONE", dry_run_output)
        self.assertIn("no migration changes are required", dry_run_output)
        self.assertIn("--apply is unnecessary", dry_run_output)
        self.assertNotIn("pass --apply to migrate", dry_run_output)
        result, second_output, error = self.run_migration(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Migration status (applied): COMPLETE", second_output)
        self.assertEqual(manifest_path.read_bytes(), applied_manifest)
        self.assertEqual(
            self.run_config(
                "set-source", source_root=self.source.parents[1], replace=False
            )[0],
            0,
        )
        result, output, error = self.run_reference(
            path="docs/reference.md", scope="project", target=self.target, skill="devconcord"
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Initial committed guidance.", output)

    def test_migration_failure_does_not_report_applied_and_reports_rollback_state(self) -> None:
        legacy = self.prepare_migration_source()
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest_before = manifest_path.read_bytes()
        real_write = manage_skills._write_atomically

        def fail_manifest(path: Path, content: str) -> None:
            if paths_equal(path, manifest_path):
                raise OSError("injected manifest write failure")
            real_write(path, content)

        with patch.object(manage_skills, "_write_atomically", side_effect=fail_manifest):
            result, output, error = self.run_migration(apply=True)

        self.assertEqual(result, 2)
        self.assertNotIn("Migration status (applied):", output + error)
        self.assertIn("Migration operation: APPLY FAILED; ROLLBACK VERIFIED", error)
        self.assertIn("Migration content status: restored to the pre-migration state", error)
        self.assertIn("Rollback status: VERIFIED", error)
        self.assertIn("injected manifest write failure", error)
        self.assertIn("Actual state after failure:", error)
        self.assertTrue(legacy.is_dir())
        self.assertFalse((self.target / ".agents/skills/devconcord").exists())
        self.assertEqual(manifest_path.read_bytes(), manifest_before)

    def test_migration_post_apply_verification_failure_is_not_reported_as_rollback(self) -> None:
        legacy = self.prepare_migration_source()
        real_plan = manage_skills._migration_plan
        calls = 0

        def fail_verification(*args: object, **kwargs: object) -> tuple[object, ...]:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise manage_skills.SkillManagementError("injected verification failure")
            return real_plan(*args, **kwargs)

        with patch.object(manage_skills, "_migration_plan", side_effect=fail_verification):
            result, output, error = self.run_migration(apply=True)

        self.assertEqual(result, 2)
        self.assertIn("Migration operation: VERIFICATION FAILED", error)
        self.assertIn("Migration content status: CHANGED", error)
        self.assertIn("Rollback status: NOT ATTEMPTED", error)
        self.assertNotIn("Rollback status: VERIFIED", error)
        self.assertNotIn("Migration status (applied):", output + error)
        self.assertFalse(legacy.exists())
        self.assertTrue((self.target / ".agents/skills/devconcord/SKILL.md").is_file())

    def test_doctor_detects_orphan_legacy_manifest_record_without_mutating_it(self) -> None:
        legacy = self.prepare_migration_source()
        self.assertEqual(self.run_operation("install", apply=True)[0], 0)
        shutil.rmtree(legacy)
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()
        unified = self.target / ".agents/skills/devconcord"
        before_unified = manage_skills._portable_tree_digest(unified, ())

        args = SimpleNamespace(command="doctor", target=self.target)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertTrue(stdout.getvalue().startswith("DevConcord Skill Health\n"))
        self.assertIn("Status: NEEDS ATTENTION", stdout.getvalue())
        self.assertIn("Most important issue: Orphan legacy manifest record:", stdout.getvalue())
        self.assertIn("Recommended next action:", stdout.getvalue())
        self.assertIn("Orphan legacy manifest record:", stdout.getvalue())
        self.assertIn("Migration status: BLOCKED", stdout.getvalue())
        self.assertFalse((self.target / ".agents/skills/devconcord-repository-review").exists())
        self.assertEqual(manifest_path.read_bytes(), before_manifest)
        self.assertEqual(manage_skills._portable_tree_digest(unified, ()), before_unified)

    def test_user_doctor_detects_orphan_legacy_manifest_record(self) -> None:
        legacy = self.prepare_user_migration_source()
        self.assertEqual(
            self.run_user_operation("install", agents=["codex"], apply=True, source=self.source)[0],
            0,
        )
        shutil.rmtree(legacy)
        manifest_path = self.user_home / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()

        args = SimpleNamespace(command="doctor", target=None)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("User Scope migration diagnosis", stdout.getvalue())
        self.assertIn("Orphan legacy manifest record:", stdout.getvalue())
        self.assertIn("Migration status: BLOCKED", stdout.getvalue())
        self.assertEqual(manifest_path.read_bytes(), before_manifest)

    def test_user_doctor_reports_legacy_hash_mismatch_read_only(self) -> None:
        legacy = self.prepare_user_migration_source()
        self.assertEqual(
            self.run_user_operation("install", agents=["codex"], apply=True, source=self.source)[0],
            0,
        )
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )
        legacy_file = legacy / "SKILL.md"
        legacy_file.write_text("local modification\n", encoding="utf-8")
        manifest_path = self.user_home / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()
        before_legacy = legacy_file.read_bytes()
        diagnosis = manage_skills._diagnose_scope(
            self.user_home,
            scope="User Scope",
            discovery_paths=manage_skills.GLOBAL_DISCOVERY_PATHS,
            source_root=self.source.parents[1],
        )

        args = SimpleNamespace(command="doctor", target=None)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual((diagnosis.status, diagnosis.exit_code), ("NEEDS ATTENTION", 0))
        self.assertTrue(any(finding.code == "legacy_hash_mismatch" for finding in diagnosis.findings))
        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("Status: NEEDS ATTENTION", stdout.getvalue())
        self.assertIn("Most important issue: A legacy Skill", stdout.getvalue())
        self.assertIn("User Scope migration diagnosis:", stdout.getvalue())
        self.assertIn("local changes or manifest hash mismatch; preserved", stdout.getvalue())
        self.assertIn("Migration status: BLOCKED", stdout.getvalue())
        self.assertEqual(manifest_path.read_bytes(), before_manifest)
        self.assertEqual(legacy_file.read_bytes(), before_legacy)

    @unittest.skipIf(os.name == "nt", "symlink behavior is platform-specific")
    def test_doctor_reports_symlinked_legacy_skill_as_blocking_without_name_heuristics(self) -> None:
        legacy = self.prepare_user_migration_source()
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )
        outside = self.root / "legacy-skill-outside"
        outside.mkdir()
        (outside / "SKILL.md").write_text("preserve outside data\n", encoding="utf-8")
        shutil.rmtree(legacy)
        legacy.symlink_to(outside, target_is_directory=True)
        manifest_path = self.user_home / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()
        diagnosis = manage_skills._diagnose_scope(
            self.user_home,
            scope="User Scope",
            discovery_paths=manage_skills.GLOBAL_DISCOVERY_PATHS,
            source_root=self.source.parents[1],
        )

        detailed_result = self.run_cli("doctor")
        summary_result = self.run_cli("doctor", "--summary")

        self.assertEqual((diagnosis.status, diagnosis.exit_code), ("NEEDS ATTENTION", 0))
        self.assertTrue(any(finding.code == "legacy_unsafe_path" for finding in diagnosis.findings))
        self.assertEqual((detailed_result.returncode, detailed_result.stderr), (0, ""))
        self.assertEqual((summary_result.returncode, summary_result.stderr), (0, ""))
        output = detailed_result.stdout
        summary_output = summary_result.stdout
        self.assertIn("Status: NEEDS ATTENTION", output)
        self.assertIn("Most important issue: A legacy Skill path is unsafe", output)
        self.assertIn("Migration status: BLOCKED", output)
        self.assertIn("Status: NEEDS ATTENTION", summary_output)
        self.assertIn("Most important issue: A legacy Skill path is unsafe", summary_output)
        self.assertEqual(
            [line for line in output.splitlines() if "Status:" in line],
            [line for line in summary_output.splitlines() if "Status:" in line],
        )
        self.assertNotIn("Detailed diagnostics", summary_output)
        self.assertTrue(legacy.is_symlink())
        self.assertEqual((outside / "SKILL.md").read_text(encoding="utf-8"), "preserve outside data\n")
        self.assertEqual(manifest_path.read_bytes(), before_manifest)

    def test_doctor_summary_preserves_each_legacy_hash_finding(self) -> None:
        first = self.prepare_user_migration_source()
        self.assertEqual(
            self.run_config("set-source", source_root=self.source.parents[1], replace=False)[0],
            0,
        )
        second = self.user_home / ".agents/skills/devconcord-root-cause-analysis"
        shutil.copytree(first, second)
        manifest_path = self.user_home / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        first_record = manifest["packages"][".agents/skills"]["skills"][first.name]
        manifest["packages"][".agents/skills"]["skills"][second.name] = dict(first_record)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (first / "SKILL.md").write_text("first local edit\n", encoding="utf-8")
        (second / "SKILL.md").write_text("second local edit\n", encoding="utf-8")
        before_manifest = manifest_path.read_bytes()
        before_files = ((first / "SKILL.md").read_bytes(), (second / "SKILL.md").read_bytes())

        result, output, error = self.run_doctor(summary=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Status: NEEDS ATTENTION", output)
        self.assertIn(".agents/skills/devconcord-repository-review", output)
        self.assertIn(".agents/skills/devconcord-root-cause-analysis", output)
        self.assertEqual(manifest_path.read_bytes(), before_manifest)
        self.assertEqual(
            ((first / "SKILL.md").read_bytes(), (second / "SKILL.md").read_bytes()),
            before_files,
        )

    def test_migration_refuses_local_legacy_edits(self) -> None:
        legacy = self.prepare_migration_source()
        (legacy / "local.md").write_text("keep me\n", encoding="utf-8")
        result, _, error = self.run_migration(apply=True)
        self.assertEqual(result, 2)
        self.assertIn("local modifications detected", error)
        self.assertTrue(legacy.is_dir())
        self.assertFalse((self.target / ".agents/skills/devconcord").exists())

    def test_migration_transaction_recovers_interrupted_legacy_deletion(self) -> None:
        self.assertEqual(
            self.run_user_operation(
                "install", agents=["codex"], skills=["sample-skill"],
                apply=True, source=self.source,
            )[0],
            0,
        )
        legacy = self.prepare_migration_source(agents=["codex", "claude", "copilot"])
        manifest_path = self.target / ".devconcord" / "skills-manifest.json"
        original_allowances = json.loads(manifest_path.read_text(encoding="utf-8"))[
            "duplicate_discovery_allowances"
        ]
        real_write = manage_skills._write_atomically

        def interrupt_manifest(path: Path, content: str) -> None:
            if paths_equal(path, manifest_path):
                raise KeyboardInterrupt()
            real_write(path, content)

        with patch.object(manage_skills, "_write_atomically", side_effect=interrupt_manifest):
            with self.assertRaises(KeyboardInterrupt):
                self.run_migration(apply=True, allow_duplicate_discovery=True)

        self.assertFalse(legacy.exists())
        self.assertTrue((self.target / ".agents/skills/devconcord").exists())
        self.assertEqual(len(manage_skills._transaction_directories(self.target)), 1)
        migrate_result, migrate_output, migrate_error = self.run_migration(apply=True)
        self.assertEqual(migrate_result, 2)
        self.assertIn("Migration operation: RECOVERY REQUIRED", migrate_error)
        self.assertNotIn("Migration status (applied):", migrate_output + migrate_error)
        self.assertIn("recover", migrate_error)
        valid_manifest = manifest_path.read_bytes()
        manifest_path.write_text("{broken\n", encoding="utf-8")
        corrupt_manifest = manifest_path.read_bytes()
        doctor_args = SimpleNamespace(command="doctor", target=self.target)
        doctor_stdout = io.StringIO()
        doctor_stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(doctor_stdout), contextlib.redirect_stderr(doctor_stderr):
                doctor_result = manage_skills._run(doctor_args)
        self.assertEqual((doctor_result, doctor_stderr.getvalue()), (0, ""))
        self.assertIn("User Scope:\n  Status: HEALTHY", doctor_stdout.getvalue())
        self.assertIn("Status: NEEDS ATTENTION", doctor_stdout.getvalue())
        self.assertIn("Project Scope:\n  Target:", doctor_stdout.getvalue())
        self.assertIn("  Status: NEEDS ATTENTION", doctor_stdout.getvalue())
        self.assertIn("Migration status: RECOVERY REQUIRED", doctor_stdout.getvalue())
        self.assertNotIn("Validated 1 DevConcord-managed Skill package(s) in Project Scope", doctor_stdout.getvalue())
        self.assertEqual(manifest_path.read_bytes(), corrupt_manifest)
        manifest_path.write_bytes(valid_manifest)
        result, _, error = self.run_recovery(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertTrue(legacy.is_dir())
        self.assertTrue((self.target / ".claude/skills/devconcord-repository-review").is_dir())
        self.assertFalse((self.target / ".agents/skills/devconcord").exists())
        recovered_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(recovered_manifest["duplicate_discovery_allowances"], original_allowances)
        self.assertEqual(manage_skills._transaction_directories(self.target), [])

    def test_migration_preserves_unmanaged_legacy_looking_directory(self) -> None:
        legacy = self.prepare_migration_source()
        unmanaged = self.target / ".agents/skills/devconcord-unmanaged"
        unmanaged.mkdir(parents=True)
        (unmanaged / "user.md").write_text("do not delete\n", encoding="utf-8")
        result, output, error = self.run_migration(apply=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("preserving unmanaged legacy-looking", output)
        self.assertTrue(unmanaged.is_dir())
        self.assertFalse(legacy.exists())

    def test_migration_preserves_managed_unknown_devconcord_prefixed_skill(self) -> None:
        legacy = self.prepare_migration_source()
        local_extension = self.target / ".agents/skills/devconcord-local-workflow"
        local_extension.mkdir()
        (local_extension / "SKILL.md").write_text(
            "---\nname: devconcord-local-workflow\ndescription: Local workflow.\n---\n\nBody.\n",
            encoding="utf-8",
        )
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        extension_hash = manage_skills._portable_tree_digest(local_extension, ())
        legacy_record = manifest["packages"][".agents/skills"]["skills"][
            "devconcord-repository-review"
        ]
        manifest["packages"][".agents/skills"]["skills"]["devconcord-local-workflow"] = {
            **legacy_record,
            "source_tree_sha256": extension_hash,
            "installed_tree_sha256": extension_hash,
            "hash_version": 2,
            "source_executable_files": [],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result, output, error = self.run_migration(apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("not a known legacy official Skill", output)
        self.assertFalse(legacy.exists())
        self.assertTrue(local_extension.is_dir())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn(
            "devconcord-local-workflow",
            manifest["packages"][".agents/skills"]["skills"],
        )

    def test_migration_preserves_unverified_source_identity(self) -> None:
        legacy = self.prepare_migration_source()
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packages"][".agents/skills"]["skills"]["devconcord-repository-review"][
            "source_repository"
        ] = "github.com/untrusted/other"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result, output, error = self.run_migration(apply=True)

        self.assertEqual((result, error), (0, ""))
        self.assertIn("source identity, commit, or source hash could not be verified", output)
        self.assertIn("Migration status (applied): PARTIAL", output)
        self.assertIn("Next action:", output)
        self.assertTrue(legacy.is_dir())
        self.assertIn(
            "devconcord-repository-review",
            json.loads(manifest_path.read_text(encoding="utf-8"))["packages"][".agents/skills"]["skills"],
        )
        self.assertTrue((self.target / ".agents/skills/devconcord/SKILL.md").is_file())
        result, doctor_output, doctor_error = self.run_user_operation("doctor", target=self.target)
        self.assertEqual((result, doctor_error), (0, ""))
        self.assertIn("Project Scope migration diagnosis", doctor_output)
        self.assertIn("Migration status: PARTIAL", doctor_output)

    def test_migration_requires_explicit_duplicate_discovery_opt_in(self) -> None:
        self.prepare_migration_source(agents=["codex", "claude", "copilot"])
        manifest_path = self.target / ".devconcord/skills-manifest.json"

        result, _, error = self.run_migration()
        self.assertEqual(result, 2)
        self.assertIn("explicitly pass --allow-duplicate-discovery", error)

        result, output, error = self.run_migration(allow_duplicate_discovery=True)
        self.assertEqual((result, error), (0, ""))
        self.assertIn("duplicate discovery paths are exposed to Copilot", output)
        self.assertIn("Dry run only", output)

        result, _, error = self.run_migration(
            apply=True, allow_duplicate_discovery=True
        )
        self.assertEqual((result, error), (0, ""))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn(
            {"skill": "devconcord", "paths": [".agents/skills", ".claude/skills"]},
            manifest["duplicate_discovery_allowances"],
        )
        self.assertEqual(
            set(manifest["packages"][".agents/skills"]["skills"]), {"devconcord"}
        )
        self.assertEqual(
            set(manifest["packages"][".claude/skills"]["skills"]), {"devconcord"}
        )
        result, doctor_output, doctor_error = self.run_user_operation("doctor", target=self.target)
        self.assertEqual((result, doctor_error), (0, ""))
        self.assertIn("Unified package: installed; manifest and package hashes verified", doctor_output)
        self.assertIn("Unified duplicate contents: identical", doctor_output)
        self.assertIn("Unified duplicate discovery allowance recorded", doctor_output)

    def test_migration_prunes_only_retired_legacy_allowance_and_keeps_unified_allowance(self) -> None:
        self.prepare_migration_source(agents=["codex", "claude", "copilot"])
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["duplicate_discovery_allowances"].append(
            {"skill": "devconcord-test-design", "paths": [".agents/skills", ".claude/skills"]}
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        result, output, error = self.run_migration(
            apply=True, allow_duplicate_discovery=True
        )

        self.assertEqual((result, error), (0, ""))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertNotIn(
            "devconcord-repository-review",
            {entry["skill"] for entry in manifest["duplicate_discovery_allowances"]},
        )
        self.assertIn(
            {"skill": "devconcord", "paths": [".agents/skills", ".claude/skills"]},
            manifest["duplicate_discovery_allowances"],
        )
        self.assertIn(
            {"skill": "devconcord-test-design", "paths": [".agents/skills", ".claude/skills"]},
            manifest["duplicate_discovery_allowances"],
        )
        self.assertIn("Migration status (applied): COMPLETE", output)

    @unittest.skipIf(os.name == "nt", "case-distinct Skill directories require a case-sensitive filesystem")
    def test_migration_preserves_allowance_when_casefold_duplicate_remains(self) -> None:
        self.prepare_migration_source(agents=["codex", "claude", "copilot"])
        duplicate = self.target / ".agents/skills/DEVCONCORD-REPOSITORY-REVIEW"
        duplicate.mkdir()
        (duplicate / "user.md").write_text("preserve case-distinct copy\n", encoding="utf-8")
        manifest_path = self.target / ".devconcord/skills-manifest.json"

        result, output, error = self.run_migration(
            apply=True, allow_duplicate_discovery=True
        )

        self.assertEqual((result, error), (0, ""))
        self.assertIn("Migration status (applied): PARTIAL", output)
        self.assertTrue(duplicate.is_dir())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn(
            {"skill": "devconcord-repository-review", "paths": [".agents/skills", ".claude/skills"]},
            manifest["duplicate_discovery_allowances"],
        )

    def test_doctor_reports_project_legacy_state_read_only(self) -> None:
        legacy = self.prepare_migration_source()
        manifest_path = self.target / ".devconcord/skills-manifest.json"
        before_manifest = manifest_path.read_bytes()
        before_legacy = (legacy / "SKILL.md").read_bytes()
        args = SimpleNamespace(command="doctor", target=self.target)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(Path, "home", return_value=self.user_home):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = manage_skills._run(args)

        self.assertEqual((result, stderr.getvalue()), (0, ""))
        self.assertIn("Project Scope migration diagnosis", stdout.getvalue())
        self.assertIn("Legacy .agents/skills/devconcord-repository-review", stdout.getvalue())
        self.assertIn("Project Scope:\n  Target:", stdout.getvalue())
        self.assertIn("  Status: REVIEW NEEDED", stdout.getvalue())
        self.assertIn("Status: REVIEW NEEDED", stdout.getvalue())
        self.assertIn("Migration status: PARTIAL", stdout.getvalue())
        self.assertEqual(manifest_path.read_bytes(), before_manifest)
        self.assertEqual((legacy / "SKILL.md").read_bytes(), before_legacy)

    def test_project_migration_supports_all_agent_combinations(self) -> None:
        combinations = (
            ["codex"], ["claude"], ["copilot"], ["codex", "copilot"],
            ["claude", "copilot"], ["codex", "claude"],
            ["codex", "claude", "copilot"],
        )
        for agents in combinations:
            with self.subTest(agents=agents):
                fixture = SkillManagementTests("runTest")
                fixture.setUp()
                try:
                    fixture.prepare_migration_source(agents=agents)
                    duplicate_risk = "copilot" in agents and "codex" in agents and "claude" in agents

                    result, _, error = fixture.run_migration()
                    if duplicate_risk:
                        self.assertEqual(result, 2)
                        self.assertIn("explicitly pass --allow-duplicate-discovery", error)
                        result, output, error = fixture.run_migration(
                            allow_duplicate_discovery=True
                        )
                    else:
                        output = ""
                    self.assertEqual((result, error), (0, ""))
                    if duplicate_risk:
                        self.assertIn("duplicate discovery paths are exposed to Copilot", output)
                    result, _, error = fixture.run_migration(
                        apply=True, allow_duplicate_discovery=duplicate_risk
                    )
                    self.assertEqual((result, error), (0, ""))

                    roots = manage_skills._package_paths(set(agents))
                    manifest = json.loads(
                        (fixture.target / ".devconcord/skills-manifest.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    for root in roots:
                        self.assertTrue((fixture.target / root / "devconcord/SKILL.md").is_file())
                        self.assertFalse(
                            (fixture.target / root / "devconcord-repository-review").exists()
                        )
                        self.assertEqual(
                            set(manifest["packages"][root]["skills"]), {"devconcord"}
                        )
                    self.assertEqual(fixture.run_validation()[0], 0)
                finally:
                    fixture.doCleanups()

    def test_user_migration_supports_multi_agent_duplicate_opt_in(self) -> None:
        agents = ["codex", "claude", "copilot"]
        self.prepare_user_migration_source(
            agents=agents, allow_duplicate_discovery=True
        )

        result, _, error = self.run_user_migration()
        self.assertEqual(result, 2)
        self.assertIn("explicitly pass --allow-duplicate-discovery", error)

        result, output, error = self.run_user_migration(
            allow_duplicate_discovery=True
        )
        self.assertEqual((result, error), (0, ""))
        self.assertIn("duplicate discovery paths are exposed to Copilot", output)
        result, _, error = self.run_user_migration(
            apply=True, allow_duplicate_discovery=True
        )
        self.assertEqual((result, error), (0, ""))

        manifest = json.loads(
            (self.user_home / ".devconcord/skills-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(manifest["packages"]),
            {".agents/skills", ".claude/skills"},
        )
        self.assertIn(
            {"skill": "devconcord", "paths": [".agents/skills", ".claude/skills"]},
            manifest["duplicate_discovery_allowances"],
        )

    def test_migration_refuses_manifest_only_legacy_record(self) -> None:
        legacy = self.prepare_migration_source()
        shutil.rmtree(legacy)
        result, _, error = self.run_migration(apply=True)
        self.assertEqual(result, 2)
        self.assertIn("legacy manifest record", error)
        manifest = json.loads((self.target / ".devconcord/skills-manifest.json").read_text())
        self.assertIn("devconcord-repository-review", manifest["packages"][".agents/skills"]["skills"])
        self.assertFalse((self.target / ".agents/skills/devconcord").exists())

    def test_unified_reference_uses_package_manifest_identity(self) -> None:
        skill = self.write_skill("devconcord", "package-v1")
        (skill / "references").mkdir(exist_ok=True)
        (skill / "references" / "shared.md").write_text("Package-level reference.\n", encoding="utf-8")
        source_repo = self.source.parents[1]
        self.git(source_repo, "add", ".")
        self.git(source_repo, "commit", "-qm", "unified package")
        shutil.rmtree(self.source / "sample-skill")
        self.git(source_repo, "add", "-A")
        self.git(source_repo, "commit", "-qm", "remove external fixture")
        repository = self.source.parents[1]
        self.assertEqual(self.run_config("set-source", source_root=repository, replace=False)[0], 0)
        self.assertEqual(self.run_user_operation("install", agents=["codex"], apply=True, source=self.source)[0], 0)
        result, output, error = self.run_reference(path=".agents/skills/devconcord/references/shared.md", skill="devconcord")
        self.assertEqual((result, error), (0, ""))
        self.assertIn("Package-level reference", output)
        self.assertIn("Reference: installed Skill", output)

    def test_cli_old_skills_option_explains_unified_migration(self) -> None:
        stderr = io.StringIO()
        with patch("sys.argv", ["manage_skills.py", "install", "--agent", "codex",
                                "--skills", "devconcord-design-security"]):
            with contextlib.redirect_stderr(stderr):
                result = manage_skills.main()
        self.assertEqual(result, 2)
        self.assertIn("--skills selection is retired", stderr.getvalue())
        self.assertIn("migrate --scope", stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
