#!/usr/bin/env python3
"""Validate, install, and safely synchronize portable Agent Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

if __package__:
    from .agent_skills import DISCOVERY_PATHS, skill_directories, validate_skill_roots
else:
    from agent_skills import DISCOVERY_PATHS, skill_directories, validate_skill_roots


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / ".agents" / "skills"
MANIFEST_PATH = Path(".devconcord") / "skills-manifest.json"
SCHEMA_VERSION = 1
AGENT_ROOTS = {
    "codex": Path(".agents/skills"),
    "copilot": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
}


class SkillManagementError(ValueError):
    """An unsafe or inconsistent skill operation was requested."""


SkillAction = tuple[str, Path, str, str, str | None]


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise SkillManagementError(f"symlinks are not supported in skill packages: {path}")
        if not path.is_dir() and not path.is_file():
            raise SkillManagementError(f"unsupported non-regular file in skill package: {path}")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        mode = stat.S_IMODE(path.stat().st_mode)
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(b"D" if path.is_dir() else b"F")
        digest.update(mode.to_bytes(4, "big"))
        if path.is_dir():
            continue
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def source_revision(source_root: Path) -> tuple[str, bool, str]:
    top = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode:
        return "unversioned", False, "local source directory"
    commit = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if commit.returncode:
        raise SkillManagementError("could not read the Skill source repository revision")
    status = subprocess.run(
        ["git", "-C", str(source_root), "status", "--porcelain", "--", "."],
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode:
        raise SkillManagementError("could not inspect Skill source repository status")
    remote = subprocess.run(
        ["git", "-C", str(source_root), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if remote.returncode:
        repository = "local Git repository"
    else:
        origin = remote.stdout.strip()
        if "://" in origin:
            parsed = urlsplit(origin)
            repository = (
                f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
                if parsed.hostname
                else "redacted Git origin"
            )
        elif "@" in origin and ":" in origin:
            repository = origin.rsplit("@", maxsplit=1)[1]
        else:
            repository = "local Git repository"
    repository = "".join(character for character in repository if character.isprintable())[:512]
    return commit.stdout.strip(), bool(status.stdout.strip()), repository


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise SkillManagementError("Skill manifest must not be a symlink")
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "installations": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillManagementError(
            f"cannot read Skill manifest ({type(error).__name__})"
        ) from error
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != SCHEMA_VERSION
        or not isinstance(value.get("installations"), dict)
    ):
        raise SkillManagementError("unrecognized Skill manifest format; refusing to replace it")
    return value


def _relative_target(target_root: Path, destination_root: Path) -> str:
    try:
        return destination_root.relative_to(target_root).as_posix()
    except ValueError as error:
        raise SkillManagementError("Skill destination must be inside the target repository") from error


def _reject_duplicate_discovery(
    target_root: Path, destination_root: Path, skill_names: set[str]
) -> None:
    for relative in DISCOVERY_PATHS:
        other_root = target_root / relative
        _check_destination_path(target_root, other_root)
        if other_root.resolve() == destination_root.resolve():
            continue
        if not other_root.exists():
            continue
        if not other_root.is_dir():
            raise SkillManagementError(
                f"agent discovery path is not a real directory: {other_root}"
            )
        duplicates = sorted(
            name
            for name in skill_names
            if (other_root / name).exists() or (other_root / name).is_symlink()
        )
        if duplicates:
            raise SkillManagementError(
                "duplicate skill names across agent discovery paths: "
                + ", ".join(duplicates)
                + f" ({other_root}); keep one discoverable copy per repository"
            )


def _check_destination_path(target_root: Path, destination_root: Path) -> None:
    current = target_root
    try:
        relative = destination_root.relative_to(target_root)
    except ValueError as error:
        raise SkillManagementError("Skill destination escapes target repository") from error
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise SkillManagementError(f"refusing symlinked destination path: {current}")
        if current.exists() and not current.is_dir():
            raise SkillManagementError(f"destination path is not a directory: {current}")


def _manifest_installation(
    manifest: dict[str, Any], destination_key: str, agent: str
) -> dict[str, Any]:
    installations = manifest["installations"]
    installation = installations.get(destination_key)
    if installation is None:
        return {"agent": agent, "skills": {}}
    if (
        not isinstance(installation, dict)
        or not isinstance(installation.get("skills"), dict)
        or installation.get("agent") != agent
    ):
        raise SkillManagementError(
            f"Skill manifest entry for {destination_key} is invalid or belongs to another agent"
        )
    return installation


def _plan(
    operation: str,
    target_root: Path,
    source_root: Path,
    agent: str,
    selected: list[str] | None,
) -> tuple[list[SkillAction], dict[str, Any], Path, str, bool, str, str]:
    target_root = target_root.resolve()
    source_root = source_root.resolve()
    if not target_root.is_dir():
        raise SkillManagementError(f"target repository does not exist: {target_root}")
    if not source_root.is_dir():
        raise SkillManagementError(f"Skill source directory does not exist: {source_root}")

    validation_errors = validate_skill_roots([source_root])
    if validation_errors:
        raise SkillManagementError(
            "Skill source validation failed:\n" + "\n".join(validation_errors)
        )
    available = {path.name: path for path in skill_directories(source_root)}
    if not available:
        raise SkillManagementError(f"no Agent Skills found in {source_root}")
    manifest_path = target_root / MANIFEST_PATH
    destination_relative = AGENT_ROOTS[agent]
    destination_root = target_root / destination_relative
    _check_destination_path(target_root, destination_root)
    _check_destination_path(target_root, manifest_path.parent)
    manifest = _read_manifest(manifest_path)
    resolved_destination = destination_root.resolve()
    source_target_overlap = (
        resolved_destination == source_root
        or source_root in resolved_destination.parents
        or resolved_destination in source_root.parents
    )
    if source_target_overlap:
        raise SkillManagementError(
            "refusing to install into the canonical Skill source directory"
        )
    destination_key = _relative_target(target_root, destination_root)
    installation = _manifest_installation(manifest, destination_key, agent)
    installed = installation["skills"]

    if operation == "install":
        names = selected or sorted(available)
        unknown = sorted(set(names) - set(available))
        if unknown:
            raise SkillManagementError("unknown Skill names: " + ", ".join(unknown))
    else:
        names = selected or sorted(installed)
        absent = sorted(set(names) - set(installed))
        if absent:
            raise SkillManagementError(
                "cannot sync Skills without a recorded installation: " + ", ".join(absent)
            )

    if len(set(names)) != len(names):
        raise SkillManagementError("Skill names were specified more than once")
    _reject_duplicate_discovery(target_root, destination_root, set(names))

    revision, dirty, repository = source_revision(source_root)
    actions: list[SkillAction] = []
    conflicts: list[str] = []
    for name in names:
        source = available.get(name)
        target = destination_root / name
        recorded = installed.get(name)
        if source is None:
            conflicts.append(f"{name}: Skill was removed from source; target preserved")
            continue
        source_hash = tree_digest(source)
        if target.is_symlink():
            conflicts.append(f"{name}: target is a symlink; target preserved")
            continue
        if target.exists() and not target.is_dir():
            conflicts.append(f"{name}: target is not a directory; target preserved")
            continue
        if target.exists() and recorded is None:
            conflicts.append(f"{name}: same-name untracked Skill exists; target preserved")
            continue
        if not target.exists() and recorded is not None:
            conflicts.append(f"{name}: recorded Skill is missing at target; target preserved")
            continue
        if target.exists():
            current_hash = tree_digest(target)
            if not isinstance(recorded, dict) or current_hash != recorded.get(
                "installed_tree_sha256"
            ):
                conflicts.append(f"{name}: local modifications detected; target preserved")
                continue
            if source_hash == recorded.get("source_tree_sha256"):
                actions.append(("unchanged", source, name, source_hash, current_hash))
            elif operation == "sync":
                actions.append(("update", source, name, source_hash, current_hash))
            else:
                conflicts.append(f"{name}: source has changed; run sync to review update")
        else:
            actions.append(("install", source, name, source_hash, None))

    if conflicts:
        raise SkillManagementError("preflight conflicts; no files changed:\n- " + "\n- ".join(conflicts))
    return actions, installation, manifest_path, destination_key, dirty, revision, repository


def _write_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".skills-manifest-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _apply(
    actions: list[SkillAction],
    target_root: Path,
    agent: str,
    installation: dict[str, Any],
    manifest_path: Path,
    destination_key: str,
    source_dirty: bool,
    source_commit: str,
    source_repository: str,
) -> None:
    destination_root = target_root / AGENT_ROOTS[agent]
    _check_destination_path(target_root, destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".devconcord-skills-", dir=destination_root))
    changes: list[tuple[Path, Path | None]] = []
    try:
        staged: dict[str, tuple[Path, str | None]] = {}
        packages_root = staging_root / "packages"
        backups_root = staging_root / "backups"
        packages_root.mkdir()
        backups_root.mkdir()
        for action, source, name, source_hash, expected_target_hash in actions:
            if action in {"install", "update"}:
                staged_dir = packages_root / name
                shutil.copytree(source, staged_dir)
                if tree_digest(staged_dir) != source_hash:
                    raise SkillManagementError(f"staged Skill differs from source: {name}")
                staged[name] = staged_dir, expected_target_hash

        for name, (staged_dir, expected_target_hash) in staged.items():
            destination = destination_root / name
            backup: Path | None = None
            if destination.is_symlink():
                raise SkillManagementError(
                    f"target changed after preflight; refusing to replace {name}"
                )
            if destination.exists():
                if expected_target_hash is None:
                    raise SkillManagementError(
                        f"target changed after preflight; refusing to replace {name}"
                    )
                if tree_digest(destination) != expected_target_hash:
                    raise SkillManagementError(
                        f"target changed after preflight; refusing to replace {name}"
                    )
                backup = backups_root / name
                os.replace(destination, backup)
            elif expected_target_hash is not None:
                raise SkillManagementError(
                    f"target disappeared after preflight; refusing to update {name}"
                )
            try:
                os.replace(staged_dir, destination)
            except BaseException:
                if backup is not None:
                    os.replace(backup, destination)
                raise
            changes.append((destination, backup))

        skills = dict(installation["skills"])
        for action, _source, name, source_hash, _expected_target_hash in actions:
            if action in {"install", "update"}:
                skills[name] = {
                    "source_repository": source_repository,
                    "source_commit": source_commit,
                    "source_dirty": source_dirty,
                    "source_tree_sha256": source_hash,
                    "installed_tree_sha256": source_hash,
                }
        installation["skills"] = skills
        # Preserve the rest of the manifest and replace only this installation record.
        _check_destination_path(target_root, manifest_path.parent)
        manifest = _read_manifest(manifest_path)
        manifest["installations"][destination_key] = installation
        rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        _check_destination_path(target_root, manifest_path.parent)
        _write_atomically(manifest_path, rendered)
    except BaseException:
        for destination, backup in reversed(changes):
            if destination.exists():
                shutil.rmtree(destination)
            if backup is not None and backup.exists():
                os.replace(backup, destination)
        raise
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)


def _run(args: argparse.Namespace) -> int:
    if args.command == "validate":
        root = args.source.resolve()
        try:
            directories = skill_directories(root)
        except (OSError, ValueError) as error:
            print(f"ERROR: invalid Skill source directory ({type(error).__name__}: {error})")
            return 1
        if not directories:
            print(f"ERROR: no Agent Skills found in {root}", file=sys.stderr)
            return 1
        errors = validate_skill_roots([root])
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Validated {len(directories)} Agent Skills in {root}")
        return 0

    target_root = args.target.resolve()
    source_root = args.source.resolve()
    try:
        (
            actions,
            installation,
            manifest_path,
            destination_key,
            dirty,
            revision,
            repository,
        ) = _plan(
            args.command, target_root, source_root, args.agent, args.skills
        )
    except (SkillManagementError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    for action, _source, name, _source_hash, _expected_target_hash in actions:
        print(f"{action}: {name}")
    print(
        f"Source: {repository} @ {revision}"
        + (" (uncommitted Skill changes)" if dirty else "")
    )
    if not args.apply:
        print("Dry run only; pass --apply to write changes.")
        return 0
    changes = [action for action in actions if action[0] in {"install", "update"}]
    if not changes:
        print("No Skill files need changes.")
        return 0
    try:
        _apply(
            actions,
            target_root,
            args.agent,
            installation,
            manifest_path,
            destination_key,
            dirty,
            revision,
            repository,
        )
    except (OSError, SkillManagementError, UnicodeError) as error:
        print(
            f"ERROR: Skill update failed; attempted rollback of managed changes "
            f"({type(error).__name__}: {error})",
            file=sys.stderr,
        )
        return 2
    print(f"Applied {len(changes)} Skill change(s); manifest: {manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate Skill source directories")
    validate.add_argument("--source", type=Path, default=DEFAULT_SOURCE)

    for command in ("install", "sync"):
        action = commands.add_parser(command, help=f"plan and optionally {command} Skills")
        action.add_argument("--target", type=Path, required=True, help="target repository root")
        action.add_argument(
            "--agent", choices=sorted(AGENT_ROOTS), required=True, help="agent discovery path"
        )
        action.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
        action.add_argument(
            "--skills",
            nargs="+",
            help="skill names; install defaults to all, sync defaults to recorded Skills",
        )
        action.add_argument(
            "--apply",
            action="store_true",
            help="apply the planned operation (without this flag the command is a dry run)",
        )
    return parser


def main() -> int:
    return _run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
