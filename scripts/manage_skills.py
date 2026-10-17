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
import uuid
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
CURRENT_SCHEMA_VERSION = 2
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
    top = _git(source_root, "rev-parse", "--show-toplevel", check=False)
    if top.returncode:
        return "unversioned", False, "local source directory"
    commit = _git(source_root, "rev-parse", "HEAD")
    if commit.returncode:
        raise SkillManagementError(f"could not read Skill source revision: {commit.stderr.strip()}")
    status = _git(source_root, "status", "--porcelain", "--", ".")
    if status.returncode:
        raise SkillManagementError(f"could not inspect Skill source status: {status.stderr.strip()}")
    remote = _git(source_root, "remote", "get-url", "origin", check=False)
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


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise SkillManagementError(f"Git is unavailable ({type(error).__name__})") from error
    if check and result.returncode:
        raise SkillManagementError(
            f"Git command failed ({' '.join(arguments)}): {result.stderr.strip()}"
        )
    return result


def _full_commit_id(value: str) -> bool:
    return len(value) in {40, 64} and all(character in "0123456789abcdef" for character in value)


def _validate_history(source_root: Path, baseline: str, current: str) -> str:
    if baseline == "unversioned" or current == "unversioned":
        raise SkillManagementError(
            "source history is unavailable; use the explicit rebind-source command to change "
            "or adopt an unversioned source"
        )
    if not _full_commit_id(baseline) or not _full_commit_id(current):
        raise SkillManagementError("source manifest contains an invalid commit identifier")
    if baseline == current:
        return "unchanged"
    shallow = _git(source_root, "rev-parse", "--is-shallow-repository", check=False)
    if shallow.returncode:
        raise SkillManagementError("Git could not determine whether source history is shallow")
    is_shallow = shallow.stdout.strip() == "true"
    base_exists = _git(source_root, "cat-file", "-e", f"{baseline}^{{commit}}", check=False)
    if base_exists.returncode:
        if is_shallow:
            raise SkillManagementError(
                "source history is shallow and the recorded commit is unavailable; ancestry "
                "cannot be proven without fetching more history"
            )
        raise SkillManagementError(
            "recorded source commit is missing from this checkout; history is incomplete or "
            "the source changed"
        )
    target_exists = _git(source_root, "cat-file", "-e", f"{current}^{{commit}}", check=False)
    if target_exists.returncode:
        raise SkillManagementError("current source commit is missing from the checkout")
    forward = _git(source_root, "merge-base", "--is-ancestor", baseline, current, check=False)
    if forward.returncode == 0:
        return "forward"
    if forward.returncode != 1:
        raise SkillManagementError(f"Git could not verify source ancestry: {forward.stderr.strip()}")
    reverse = _git(source_root, "merge-base", "--is-ancestor", current, baseline, check=False)
    if reverse.returncode == 0:
        raise SkillManagementError("source history rewind detected; normal sync will not downgrade")
    if reverse.returncode != 1:
        raise SkillManagementError(f"Git could not verify reverse ancestry: {reverse.stderr.strip()}")
    if is_shallow:
        raise SkillManagementError(
            "source history is shallow; ancestry cannot be proven without fetching more history"
        )
    raise SkillManagementError("source history is different or diverged; normal sync is blocked")


def _read_manifest(path: Path) -> tuple[dict[str, Any], bool]:
    if path.is_symlink():
        raise SkillManagementError("Skill manifest must not be a symlink")
    if not path.exists():
        return {"schema_version": CURRENT_SCHEMA_VERSION, "packages": {}}, False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillManagementError(
            f"cannot read Skill manifest ({type(error).__name__})"
        ) from error
    if not isinstance(value, dict):
        raise SkillManagementError("unrecognized Skill manifest format; refusing to replace it")
    schema = value.get("schema_version")
    if type(schema) is int and schema == CURRENT_SCHEMA_VERSION:
        packages = value.get("packages")
        if not isinstance(packages, dict):
            raise SkillManagementError("invalid Skill packages manifest; refusing to replace it")
        _validate_packages(packages)
        return value, False
    if type(schema) is not int or schema != 1 or not isinstance(value.get("installations"), dict):
        raise SkillManagementError("unrecognized Skill manifest format; refusing to replace it")
    packages: dict[str, Any] = {}
    for path, installation in value["installations"].items():
        if (
            not isinstance(path, str)
            or not isinstance(installation, dict)
            or not isinstance(installation.get("agent"), str)
            or installation.get("agent") not in AGENT_ROOTS
            or path != AGENT_ROOTS[installation["agent"]].as_posix()
            or not isinstance(installation.get("skills"), dict)
        ):
            raise SkillManagementError(
                f"invalid legacy installation record at {path!r}; preserving manifest"
            )
        package = {
            key: item
            for key, item in installation.items()
            if key not in {"agent", "skills"}
        }
        package.update({
            "agents": [installation["agent"]],
            "skills": installation["skills"],
        })
        packages[path] = package
    migrated = {
        key: item
        for key, item in value.items()
        if key not in {"schema_version", "installations"}
    }
    migrated.update({"schema_version": CURRENT_SCHEMA_VERSION, "packages": packages})
    _validate_packages(packages)
    return migrated, True


def _validate_packages(packages: dict[str, Any]) -> None:
    valid_paths = {path.as_posix() for path in AGENT_ROOTS.values()}
    for package_path, package in packages.items():
        if package_path not in valid_paths:
            raise SkillManagementError(
                f"unknown Skill package path {package_path!r}; preserving manifest"
            )
        if not isinstance(package, dict):
            raise SkillManagementError(f"invalid Skill package at {package_path!r}")
        agents = package.get("agents")
        skills = package.get("skills")
        valid_agents = (
            {"codex", "copilot"}
            if package_path == ".agents/skills"
            else {"claude", "copilot"}
        )
        if (
            not isinstance(agents, list)
            or not agents
            or any(not isinstance(agent, str) for agent in agents)
            or len(agents) != len(set(agents))
            or not set(agents) <= valid_agents
            or not isinstance(skills, dict)
        ):
            raise SkillManagementError(f"invalid Skill package metadata at {package_path!r}")
        for name, record in skills.items():
            if (
                not _valid_skill_name(name)
                or not isinstance(record, dict)
                or not _is_sha256(record.get("source_tree_sha256"))
                or not _is_sha256(record.get("installed_tree_sha256"))
                or not isinstance(record.get("source_commit"), str)
                or not (
                    record["source_commit"] == "unversioned"
                    or _full_commit_id(record["source_commit"])
                )
                or not isinstance(record.get("source_repository"), str)
                or not isinstance(record.get("source_dirty"), bool)
            ):
                raise SkillManagementError(
                    f"invalid provenance for Skill {name!r} at {package_path!r}"
                )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_skill_name(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value.isascii()
        and value[0] != "-"
        and value[-1] != "-"
        and "--" not in value
        and all(character.islower() or character.isdigit() or character == "-" for character in value)
    )


def _relative_target(target_root: Path, destination_root: Path) -> str:
    try:
        return destination_root.relative_to(target_root).as_posix()
    except ValueError as error:
        raise SkillManagementError("Skill destination must be inside the target repository") from error


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
    manifest: dict[str, Any], destination_key: str
) -> dict[str, Any]:
    packages = manifest["packages"]
    installation = packages.get(destination_key)
    if installation is None:
        return {"agents": [], "skills": {}}
    if (
        not isinstance(installation, dict)
        or not isinstance(installation.get("skills"), dict)
        or not isinstance(installation.get("agents"), list)
        or any(agent not in AGENT_ROOTS for agent in installation["agents"])
    ):
        raise SkillManagementError(f"Skill manifest entry for {destination_key} is invalid")
    return installation


def _package_paths(agents: set[str]) -> list[str]:
    if agents <= {"codex", "copilot"}:
        return [".agents/skills"]
    if agents <= {"claude", "copilot"}:
        return [".claude/skills"]
    if agents == {"codex", "claude", "copilot"}:
        return [".agents/skills", ".claude/skills"]
    return [".agents/skills", ".claude/skills"]


def _plan(
    operation: str,
    target_root: Path,
    source_root: Path,
    requested_agents: set[str],
    selected: list[str] | None,
    allow_duplicate_discovery: bool,
    allow_dirty_source: bool,
) -> tuple[list[tuple[SkillAction, str]], dict[str, Any], Path, bool, bool, str, str, str]:
    target_root = target_root.resolve()
    source_root = source_root.resolve()
    if operation not in {"install", "sync", "rebind-source"}:
        raise SkillManagementError(f"unsupported Skill operation: {operation}")
    if not requested_agents or not requested_agents <= set(AGENT_ROOTS):
        raise SkillManagementError("at least one supported agent must be selected")
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
    _check_destination_path(target_root, manifest_path.parent)
    manifest, migrated = _read_manifest(manifest_path)
    requested_roots = (
        _package_paths(requested_agents)
        if operation == "install"
        else sorted(
            key
            for key, package in manifest["packages"].items()
            if isinstance(package, dict)
            and requested_agents.intersection(package.get("agents", []))
        )
    )
    if operation != "install" and not requested_roots:
        raise SkillManagementError("no managed Skill package is recorded for the requested agent(s)")
    for relative in requested_roots:
        if relative not in {path.as_posix() for path in AGENT_ROOTS.values()}:
            raise SkillManagementError(f"invalid Skill package path in manifest: {relative}")
        destination = target_root / relative
        _check_destination_path(target_root, destination)
        resolved_destination = destination.resolve()
        source_target_overlap = (
            resolved_destination == source_root
            or source_root in resolved_destination.parents
            or resolved_destination in source_root.parents
        )
        if source_target_overlap:
            raise SkillManagementError(
                "refusing to install into or from overlapping canonical Skill source paths"
            )

    if operation == "install":
        names = selected or sorted(available)
        unknown = sorted(set(names) - set(available))
        if unknown:
            raise SkillManagementError("unknown Skill names: " + ", ".join(unknown))
    else:
        all_installed = {
            name
            for relative in requested_roots
            for name in _manifest_installation(manifest, relative)["skills"]
        }
        names = selected or sorted(all_installed)
        absent = sorted(set(names) - all_installed)
        if absent:
            raise SkillManagementError(
                "cannot sync Skills without a recorded installation: " + ", ".join(absent)
            )

    if len(set(names)) != len(names):
        raise SkillManagementError("Skill names were specified more than once")
    source_hashes = {
        name: tree_digest(available[name]) for name in names if name in available
    }
    requested_destinations = {Path(path).as_posix() for path in requested_roots}
    duplicate_exposure = False
    if "copilot" in requested_agents:
        for relative in DISCOVERY_PATHS:
            if relative in requested_destinations:
                continue
            other_root = target_root / relative
            _check_destination_path(target_root, other_root)
            if not other_root.exists():
                continue
            if not other_root.is_dir():
                raise SkillManagementError(f"agent discovery path is not a directory: {other_root}")
            for name in names:
                other_skill = other_root / name
                if not other_skill.exists() and not other_skill.is_symlink():
                    continue
                if other_skill.is_symlink() or not other_skill.is_dir():
                    raise SkillManagementError(
                        f"ambiguous duplicate Skill exposure for Copilot: {other_skill}"
                    )
                source_path = available.get(name)
                if source_path is None:
                    continue
                source_hash = source_hashes[name]
                existing_hash = tree_digest(other_skill)
                if source_hash != existing_hash:
                    raise SkillManagementError(
                        f"conflicting same-name Skill visible to Copilot: {other_skill}"
                    )
                if not allow_duplicate_discovery:
                    raise SkillManagementError(
                        f"identical Skill copies in multiple Copilot discovery roots: "
                        f"{other_skill}; use --allow-duplicate-discovery only after confirming "
                        "the host's duplicate behavior"
                    )
                duplicate_exposure = True

    revision, dirty, repository = source_revision(source_root)
    if dirty and not allow_dirty_source:
        raise SkillManagementError(
            "Skill source has uncommitted changes; commit them or explicitly pass "
            "--allow-dirty-source"
        )
    if "copilot" in requested_agents and len(requested_roots) > 1:
        overlap = sorted(set(names))
        if overlap and not allow_duplicate_discovery:
            raise SkillManagementError(
                "the requested agents expose the same Skill name in multiple roots that "
                "Copilot may scan; use --allow-duplicate-discovery only after verifying "
                "duplicate handling for your Copilot host"
            )
        duplicate_exposure = bool(overlap)
    actions: list[tuple[SkillAction, str]] = []
    conflicts: list[str] = []
    for relative in requested_roots:
        destination_root = target_root / relative
        destination_key = _relative_target(target_root, destination_root)
        package = _manifest_installation(manifest, destination_key)
        stored_agents = set(package["agents"])
        applicable_agents = set(requested_agents)
        if relative == ".agents/skills":
            applicable_agents &= {"codex", "copilot"}
        else:
            applicable_agents &= {"claude", "copilot"}
        package["agents"] = sorted(stored_agents | applicable_agents)
        manifest["packages"][destination_key] = package
        installed = package["skills"]
        package_names = names if operation == "install" else [
            name for name in names if name in installed
        ]
        if operation == "install" and not selected:
            package_names = sorted(available)
        for name in package_names:
            source = available.get(name)
            target = destination_root / name
            recorded = installed.get(name)
            if source is None:
                conflicts.append(f"{name}: Skill was removed from source; target preserved")
                continue
            source_hash = source_hashes[name]
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
                baseline = recorded.get("source_commit", "unversioned")
                if operation == "rebind-source":
                    history = "rebind"
                else:
                    try:
                        history = _validate_history(source_root, baseline, revision)
                    except SkillManagementError as error:
                        conflicts.append(f"{name} ({relative}): {error}")
                        continue
                source_is_same = source_hash == recorded.get("source_tree_sha256")
                if source_is_same:
                    action = (
                        "unchanged"
                        if history == "unchanged" or operation == "install"
                        else "metadata"
                    )
                elif operation in {"sync", "rebind-source"}:
                    action = "update"
                else:
                    conflicts.append(f"{name}: source has changed; run sync to review update")
                    continue
                actions.append(((action, source, name, source_hash, current_hash), relative))
            else:
                actions.append((("install", source, name, source_hash, None), relative))

    if conflicts:
        raise SkillManagementError("preflight conflicts; no files changed:\n- " + "\n- ".join(conflicts))
    return actions, manifest, manifest_path, migrated, duplicate_exposure, dirty, revision, repository


def _write_bytes_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".skills-manifest-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_atomically(path: Path, text: str) -> None:
    _write_bytes_atomically(path, text.encode("utf-8"))


def _write_journal(transaction_root: Path, journal: dict[str, Any]) -> None:
    _write_atomically(
        transaction_root / "journal.json",
        json.dumps(journal, ensure_ascii=False, indent=2) + "\n",
    )


def _safe_target_path(target_root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise SkillManagementError(f"unsafe path in recovery journal: {relative}")
    resolved = target_root / path
    _check_destination_path(target_root, resolved.parent)
    if resolved.is_symlink():
        raise SkillManagementError(f"symlink found in recovery path: {relative}")
    try:
        resolved.resolve().relative_to(target_root)
    except ValueError as error:
        raise SkillManagementError(f"recovery path escapes target repository: {relative}") from error
    return resolved


def _safe_backup_path(transaction_root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 2 or path.parts[0] != "backups":
        raise SkillManagementError(f"unsafe backup path in recovery journal: {relative}")
    resolved = transaction_root / path
    if resolved.is_symlink() or resolved.parent.is_symlink():
        raise SkillManagementError(f"symlink found in recovery backup path: {relative}")
    try:
        resolved.resolve().relative_to((transaction_root / "backups").resolve())
    except ValueError as error:
        raise SkillManagementError(f"backup path escapes transaction: {relative}") from error
    return resolved


def _tree_digest_or_missing(path: Path) -> str | None:
    if path.is_symlink():
        raise SkillManagementError(f"symlink found while checking transaction path: {path}")
    if path.is_dir():
        return tree_digest(path)
    if path.exists():
        raise SkillManagementError(f"recovery path is not a directory: {path}")
    return None


def _recover_transaction(target_root: Path, transaction_root: Path) -> str:
    journal_path = transaction_root / "journal.json"
    if journal_path.is_symlink() or not journal_path.is_file():
        raise SkillManagementError(
            f"transaction has no valid journal; preserve it for manual inspection: {transaction_root}"
        )
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillManagementError(
            f"transaction journal is unreadable; preserve it for manual inspection "
            f"({type(error).__name__})"
        ) from error
    if (
        not isinstance(journal, dict)
        or type(journal.get("version")) is not int
        or journal.get("version") != 1
        or not isinstance(journal.get("state"), str)
        or journal.get("state") not in {"prepared", "committed"}
    ):
        raise SkillManagementError("unsupported recovery journal; preserve it for manual inspection")
    entries = journal.get("entries")
    if not isinstance(entries, list):
        raise SkillManagementError("invalid recovery journal entries")
    allowed_top_level = {"journal.json", "staged", "backups"}
    if journal.get("manifest_backup") is not None:
        allowed_top_level.add("manifest.previous")
    for child in transaction_root.iterdir():
        if child.name.startswith(".skills-manifest-") and child.is_file() and not child.is_symlink():
            continue
        if child.name not in allowed_top_level or child.is_symlink():
            raise SkillManagementError(
                f"unexpected item in recovery transaction; preserving it: {child}"
            )
    for directory_name in ("staged", "backups"):
        directory = transaction_root / directory_name
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise SkillManagementError(f"invalid {directory_name} transaction directory")
    journal_manifest_path = journal.get("manifest_path")
    if not isinstance(journal_manifest_path, str):
        raise SkillManagementError("invalid manifest path in recovery journal")
    manifest_path = _safe_target_path(target_root, journal_manifest_path)
    if manifest_path != target_root / MANIFEST_PATH:
        raise SkillManagementError("recovery journal references an unexpected manifest path")
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.is_file() else None
    old_manifest_hash = journal.get("old_manifest_sha256")
    new_manifest_hash = journal.get("new_manifest_sha256")
    if (
        (old_manifest_hash is not None and not _is_sha256(old_manifest_hash))
        or not _is_sha256(new_manifest_hash)
    ):
        raise SkillManagementError("invalid manifest digest in recovery journal")
    manifest_backup_name = journal.get("manifest_backup")
    if (
        (old_manifest_hash is None and manifest_backup_name is not None)
        or (old_manifest_hash is not None and manifest_backup_name != "manifest.previous")
    ):
        raise SkillManagementError("invalid manifest backup reference in recovery journal")
    if manifest_hash not in {old_manifest_hash, new_manifest_hash}:
        raise SkillManagementError(
            "manifest changed after interruption; preserve the transaction and resolve it manually"
        )
    if old_manifest_hash is not None and manifest_hash != old_manifest_hash:
        if manifest_backup_name != "manifest.previous":
            raise SkillManagementError("manifest backup is missing from recovery journal")
        manifest_backup = transaction_root / manifest_backup_name
        if (
            not manifest_backup.is_file()
            or manifest_backup.is_symlink()
            or hashlib.sha256(manifest_backup.read_bytes()).hexdigest() != old_manifest_hash
        ):
            raise SkillManagementError("manifest backup is missing or corrupt")

    destinations: set[str] = set()
    backups: set[str] = set()
    staged_paths: set[str] = set()
    staged_roots: set[tuple[str, ...]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise SkillManagementError("invalid package entry in recovery journal")
        destination_relative = entry.get("destination")
        if not isinstance(destination_relative, str):
            raise SkillManagementError("invalid destination in recovery journal")
        destination = _safe_target_path(target_root, destination_relative)
        destination_parts = Path(destination_relative).parts
        if len(destination_parts) != 3 or destination_parts[:2] not in {
            (".agents", "skills"),
            (".claude", "skills"),
        } or not _valid_skill_name(destination_parts[2]):
            raise SkillManagementError("recovery journal destination is not a managed Skill path")
        if destination_relative in destinations:
            raise SkillManagementError("duplicate destination in recovery journal")
        destinations.add(destination_relative)
        if not _is_sha256(entry.get("new_tree_sha256")) or (
            entry.get("old_tree_sha256") is not None
            and not _is_sha256(entry.get("old_tree_sha256"))
        ):
            raise SkillManagementError("invalid content digest in recovery journal")
        backup_relative = entry.get("backup")
        if not isinstance(backup_relative, str) or backup_relative in backups:
            raise SkillManagementError("invalid or duplicate backup in recovery journal")
        backup_parts = Path(backup_relative).parts
        if len(backup_parts) != 2 or backup_parts[0] != "backups" or not backup_parts[1].isdigit():
            raise SkillManagementError("backup path is not a managed transaction backup")
        backups.add(backup_relative)
        backup = (
            _safe_backup_path(transaction_root, backup_relative)
            if backup_relative
            else None
        )
        staged_relative = entry.get("staged")
        if not isinstance(staged_relative, str):
            raise SkillManagementError("invalid staged path in recovery journal")
        staged_parts = Path(staged_relative).parts
        if (
            len(staged_parts) != 4
            or staged_parts[0] != "staged"
            or staged_parts[1:3] not in {
                (".agents", "skills"),
                (".claude", "skills"),
            }
            or not _valid_skill_name(staged_parts[3])
            or staged_parts[1:3] != destination_parts[:2]
            or staged_parts[3] != destination_parts[2]
        ):
            raise SkillManagementError("staged path is not a managed Skill package")
        if staged_relative in staged_paths:
            raise SkillManagementError("duplicate staged path in recovery journal")
        staged_paths.add(staged_relative)
        staged_roots.add(staged_parts[1:])
        staged = transaction_root / Path(staged_relative)
        try:
            staged.resolve().relative_to((transaction_root / "staged").resolve())
        except ValueError as error:
            raise SkillManagementError("staged path escapes transaction") from error
        if staged.is_symlink():
            raise SkillManagementError("staged Skill is a symlink")
        if staged.exists() and tree_digest(staged) != entry["new_tree_sha256"]:
            raise SkillManagementError(f"staged Skill integrity check failed: {staged}")
        if backup is not None and backup.exists():
            if entry.get("old_tree_sha256") is None or tree_digest(backup) != entry["old_tree_sha256"]:
                raise SkillManagementError(f"backup integrity check failed: {backup}")

    backup_root = transaction_root / "backups"
    expected_backup_names = {Path(relative).name for relative in backups}
    unexpected_backups = (
        [
            path
            for path in backup_root.iterdir()
            if path.name not in expected_backup_names or path.is_symlink()
        ]
        if backup_root.exists()
        else []
    )
    if unexpected_backups:
        raise SkillManagementError(
            "unexpected backup item; preserving transaction: "
            + ", ".join(map(str, unexpected_backups))
        )
    staged_root = transaction_root / "staged"
    if staged_root.exists():
        for path in staged_root.rglob("*"):
            relative_parts = path.relative_to(staged_root).parts
            is_known = any(
                relative_parts[: len(skill_parts)] == skill_parts
                or skill_parts[: len(relative_parts)] == relative_parts
                for skill_parts in staged_roots
            )
            if path.is_symlink() or not is_known:
                raise SkillManagementError(
                    f"unexpected staged item; preserving transaction: {path}"
                )

    if manifest_hash == new_manifest_hash:
        for entry in entries:
            destination = _safe_target_path(target_root, entry["destination"])
            if _tree_digest_or_missing(destination) != entry["new_tree_sha256"]:
                raise SkillManagementError(
                    "manifest records a transaction whose package files are incomplete; "
                    "preserve the journal for manual recovery"
                )
        shutil.rmtree(transaction_root)
        return "completed"

    for entry in reversed(entries):
        destination = _safe_target_path(target_root, entry["destination"])
        current_hash = _tree_digest_or_missing(destination)
        backup = (
            _safe_backup_path(transaction_root, entry["backup"])
            if entry.get("backup")
            else None
        )
        old_hash = entry.get("old_tree_sha256")
        if current_hash == old_hash:
            continue
        if current_hash not in {None, entry.get("new_tree_sha256")}:
            raise SkillManagementError(
                f"target changed after interruption; preserving {destination}"
            )
        if backup is not None and backup.exists():
            if tree_digest(backup) != old_hash:
                raise SkillManagementError(f"backup integrity check failed: {backup}")
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(backup, destination)
        elif old_hash is None:
            if destination.exists():
                shutil.rmtree(destination)
        else:
            raise SkillManagementError(
                f"required transaction backup is missing for {destination}"
            )

    backup_name = manifest_backup_name
    if old_manifest_hash is not None and backup_name and manifest_hash != old_manifest_hash:
        if backup_name != "manifest.previous":
            raise SkillManagementError("invalid manifest backup path in recovery journal")
        backup = transaction_root / backup_name
        if not backup.is_file() or hashlib.sha256(backup.read_bytes()).hexdigest() != old_manifest_hash:
            raise SkillManagementError("manifest backup is missing or corrupt")
        _write_bytes_atomically(manifest_path, backup.read_bytes())
    elif old_manifest_hash is None and manifest_hash is not None:
        manifest_path.unlink()
    shutil.rmtree(transaction_root)
    return "rolled back"


def _transaction_directories(target_root: Path) -> list[Path]:
    root = target_root / ".devconcord" / "skills-transactions"
    _check_destination_path(target_root, root)
    if root.is_symlink():
        raise SkillManagementError("Skill transaction directory must not be a symlink")
    if not root.exists():
        return []
    if not root.is_dir():
        raise SkillManagementError("Skill transaction path is not a directory")
    children = sorted(root.iterdir())
    invalid = [path for path in children if path.is_symlink() or not path.is_dir()]
    if invalid:
        raise SkillManagementError(
            "unexpected item in Skill transaction directory: " + ", ".join(map(str, invalid))
        )
    return children


def _acquire_lock(target_root: Path, *, force: bool = False) -> Path:
    lock_path = target_root / ".devconcord" / "skills.lock"
    _check_destination_path(target_root, lock_path.parent)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if force and lock_path.exists():
        if lock_path.is_symlink():
            raise SkillManagementError("refusing to remove a symlinked Skill lock")
        try:
            lock_text = lock_path.read_text(encoding="ascii")
            pid = int(lock_text.removeprefix("pid=").strip())
        except (OSError, UnicodeError, ValueError) as error:
            raise SkillManagementError(
                "cannot establish whether the existing lock is stale; inspect it manually"
            ) from error
        if pid <= 0:
            raise SkillManagementError("existing Skill lock has an invalid process ID")
        if _process_is_running(pid):
            raise SkillManagementError("existing Skill lock belongs to an active process")
        lock_path.unlink()
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise SkillManagementError(
            f"another Skill operation holds {lock_path}; if it was interrupted, verify no "
            "process is active and use recover --apply --force"
        ) from error
    with os.fdopen(descriptor, "w", encoding="ascii") as lock:
        lock.write(f"pid={os.getpid()}\n")
        lock.flush()
        os.fsync(lock.fileno())
    return lock_path


def _process_is_running(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    open_process.restype = ctypes.c_void_p
    get_exit_code = kernel32.GetExitCodeProcess
    get_exit_code.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    get_exit_code.restype = ctypes.c_int
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int
    handle = open_process(0x1000, 0, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:
            return False
        if error == 5:
            return True
        raise OSError(error, "could not inspect the process recorded in the Skill lock")
    try:
        exit_code = ctypes.c_ulong()
        if not get_exit_code(handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return exit_code.value == 259
    finally:
        close_handle(handle)


def _release_lock(lock_path: Path) -> None:
    try:
        if lock_path.is_symlink():
            raise SkillManagementError("Skill operation lock was replaced by a symlink")
        if lock_path.is_file() and lock_path.read_text(encoding="ascii") == f"pid={os.getpid()}\n":
            lock_path.unlink()
            _fsync_directory(lock_path.parent)
    except SkillManagementError:
        raise
    except OSError as error:
        raise SkillManagementError(f"could not release Skill operation lock: {error}") from error


def _apply(
    actions: list[tuple[SkillAction, str]],
    target_root: Path,
    manifest: dict[str, Any],
    manifest_path: Path,
    source_dirty: bool,
    source_commit: str,
    source_repository: str,
    expected_manifest: bytes | None,
) -> None:
    _check_destination_path(target_root, manifest_path.parent)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    transactions_root = manifest_path.parent / "skills-transactions"
    transactions_root.mkdir(exist_ok=True)
    transaction_root = transactions_root / str(uuid.uuid4())
    transaction_root.mkdir()
    _fsync_directory(transactions_root)
    staged_root = transaction_root / "staged"
    backups_root = transaction_root / "backups"
    journal_entries: list[dict[str, Any]] = []
    journal_written = False
    try:
        if manifest_path.is_symlink():
            raise SkillManagementError("Skill manifest became a symlink during preflight")
        old_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        if old_manifest != expected_manifest:
            raise SkillManagementError("manifest changed during preflight; refusing to overwrite it")
        staged_root.mkdir()
        backups_root.mkdir()
        for index, (action_tuple, relative) in enumerate(actions):
            action, source, name, source_hash, expected_target_hash = action_tuple
            if action not in {"install", "update"}:
                continue
            staged_dir = staged_root / relative / name
            staged_dir.parent.mkdir(parents=True, exist_ok=True)
            destination = target_root / relative / name
            _check_destination_path(target_root, destination.parent)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.parent.stat().st_dev != transactions_root.stat().st_dev:
                raise SkillManagementError(
                    "Skill destination and transaction journal are on different filesystems; "
                    "cross-filesystem atomic recovery is unavailable"
                )
            shutil.copytree(source, staged_dir)
            if tree_digest(staged_dir) != source_hash:
                raise SkillManagementError(f"staged Skill differs from source: {name}")
            journal_entries.append(
                {
                    "destination": destination.relative_to(target_root).as_posix(),
                    "staged": staged_dir.relative_to(transaction_root).as_posix(),
                    "backup": f"backups/{index}",
                    "new_tree_sha256": source_hash,
                    "old_tree_sha256": expected_target_hash,
                }
            )

        for action_tuple, relative in actions:
            action, _source, name, source_hash, _expected_target_hash = action_tuple
            package = manifest["packages"][relative]
            if action in {"install", "update", "metadata", "unchanged"}:
                package["skills"][name] = {
                    "source_repository": source_repository,
                    "source_commit": source_commit,
                    "source_dirty": source_dirty,
                    "source_tree_sha256": source_hash,
                    "installed_tree_sha256": source_hash,
                }
        rendered_manifest = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        manifest_backup = None
        if old_manifest is not None:
            manifest_backup = "manifest.previous"
            _write_bytes_atomically(transaction_root / manifest_backup, old_manifest)
        journal = {
            "version": 1,
            "state": "prepared",
            "manifest_path": manifest_path.relative_to(target_root).as_posix(),
            "manifest_backup": manifest_backup,
            "old_manifest_sha256": (
                hashlib.sha256(old_manifest).hexdigest() if old_manifest is not None else None
            ),
            "new_manifest_sha256": hashlib.sha256(rendered_manifest.encode("utf-8")).hexdigest(),
            "entries": journal_entries,
        }
        _write_journal(transaction_root, journal)
        journal_written = True

        for entry in journal_entries:
            destination = _safe_target_path(target_root, entry["destination"])
            staged_dir = transaction_root / entry["staged"]
            backup = transaction_root / entry["backup"]
            if destination.is_symlink():
                raise SkillManagementError(
                    f"target changed after preflight; refusing to replace {destination.name}"
                )
            current_hash = _tree_digest_or_missing(destination)
            if current_hash != entry["old_tree_sha256"]:
                raise SkillManagementError(
                    f"target changed after preflight; refusing to replace {destination.name}"
                )
            if destination.exists():
                os.replace(destination, backup)
                try:
                    backup_hash = tree_digest(backup)
                except SkillManagementError:
                    if not destination.exists():
                        os.replace(backup, destination)
                    raise
                if backup_hash != entry["old_tree_sha256"]:
                    if not destination.exists():
                        os.replace(backup, destination)
                    raise SkillManagementError(
                        f"target changed during replacement; refusing to overwrite {destination.name}"
                    )
            os.replace(staged_dir, destination)
            _fsync_directory(destination.parent)

        rendered_manifest = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        for entry in journal_entries:
            destination = _safe_target_path(target_root, entry["destination"])
            if _tree_digest_or_missing(destination) != entry["new_tree_sha256"]:
                raise SkillManagementError(
                    f"target changed during Skill update; refusing to commit manifest for "
                    f"{destination.name}"
                )
        if manifest_path.is_symlink():
            raise SkillManagementError("manifest changed to a symlink during Skill update")
        current_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
        if current_manifest != old_manifest:
            raise SkillManagementError("manifest changed during Skill update; refusing to overwrite it")
        _write_atomically(manifest_path, rendered_manifest)
        journal["state"] = "committed"
        _write_journal(transaction_root, journal)
        shutil.rmtree(transaction_root)
    except Exception as error:
        if journal_written:
            outcome = _recover_transaction(target_root, transaction_root)
            if outcome == "completed":
                print(
                    "WARNING: transaction contents were verified as committed after a "
                    f"post-commit error ({type(error).__name__})."
                )
                return
        else:
            shutil.rmtree(transaction_root, ignore_errors=True)
        raise


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
    if args.command == "recover":
        lock_path: Path | None = None
        status = 0
        try:
            if not target_root.is_dir():
                raise SkillManagementError(f"target repository does not exist: {target_root}")
            if not args.apply:
                transactions = _transaction_directories(target_root)
                if not transactions:
                    print("No interrupted Skill transactions found.")
                else:
                    for transaction in transactions:
                        print(f"needs-recovery: {transaction}")
                    print("Dry run only; pass --apply to recover interrupted updates.")
            else:
                lock_path = _acquire_lock(target_root, force=getattr(args, "force", False))
                transactions = _transaction_directories(target_root)
                if not transactions:
                    print("No interrupted Skill transactions found.")
                else:
                    for transaction in transactions:
                        outcome = _recover_transaction(target_root, transaction)
                        print(f"{outcome}: {transaction.name}")
        except (SkillManagementError, OSError, ValueError) as error:
            print(f"ERROR: Skill recovery stopped safely: {error}", file=sys.stderr)
            status = 2
        finally:
            if lock_path is not None:
                try:
                    _release_lock(lock_path)
                except SkillManagementError as error:
                    print(f"ERROR: {error}", file=sys.stderr)
                    status = 2
        return status

    target_root = args.target.resolve()
    source_root = args.source.resolve()
    requested_agents = set(getattr(args, "agents", None) or [args.agent])
    if getattr(args, "command") == "rebind-source":
        print(
            "WARNING: rebind-source explicitly accepts a different or older Skill source; "
            "review the plan before applying."
        )
    lock_path: Path | None = None
    status = 0
    try:
        if not target_root.is_dir():
            raise SkillManagementError(f"target repository does not exist: {target_root}")
        if args.apply:
            lock_path = _acquire_lock(target_root)
            pending = _transaction_directories(target_root)
            if pending:
                raise SkillManagementError(
                    "interrupted Skill transactions must be recovered first: "
                    + ", ".join(path.name for path in pending)
                )
        else:
            lock_candidate = target_root / ".devconcord" / "skills.lock"
            _check_destination_path(target_root, lock_candidate.parent)
            if lock_candidate.exists() or lock_candidate.is_symlink():
                raise SkillManagementError(
                    "a Skill operation lock exists; wait for it to finish or inspect it before "
                    "recovering an interrupted operation"
                )
            pending = _transaction_directories(target_root)
            if pending:
                raise SkillManagementError(
                    "interrupted Skill transactions must be recovered before planning: "
                    + ", ".join(path.name for path in pending)
                )
        expected_manifest = (
            _read_expected_manifest(target_root)
        )
        (
            actions,
            manifest,
            manifest_path,
            migrated,
            duplicate_exposure,
            dirty,
            revision,
            repository,
        ) = _plan(
            args.command,
            target_root,
            source_root,
            requested_agents,
            args.skills,
            getattr(args, "allow_duplicate_discovery", False),
            getattr(args, "allow_dirty_source", False),
        )
        for (action, _source, name, _source_hash, _expected_target_hash), package_path in actions:
            print(f"{action}: {package_path}/{name}")
        print(
            f"Source: {repository} @ {revision}"
            + (" (uncommitted Skill changes)" if dirty else "")
        )
        if duplicate_exposure:
            print(
                "WARNING: duplicate discovery paths are exposed to Copilot; duplicate "
                "resolution is host-dependent and has not been verified."
            )
        if not args.apply:
            print("Dry run only; pass --apply to write changes.")
        else:
            changes = [entry for entry in actions if entry[0][0] in {"install", "update"}]
            original_manifest = (
                _read_manifest(manifest_path)[0]
                if manifest_path.exists()
                else {"schema_version": CURRENT_SCHEMA_VERSION, "packages": {}}
            )
            manifest_changed = migrated or manifest != original_manifest
            metadata_changes = any(entry[0][0] == "metadata" for entry in actions)
            if not changes and not manifest_changed and not metadata_changes:
                print("No Skill or manifest changes are needed.")
            else:
                _apply(
                    actions,
                    target_root,
                    manifest,
                    manifest_path,
                    dirty,
                    revision,
                    repository,
                    expected_manifest,
                )
                print(f"Applied {len(changes)} Skill file change(s); manifest: {manifest_path}")
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        print(f"ERROR: Skill operation stopped safely: {error}", file=sys.stderr)
        status = 2
    finally:
        if lock_path is not None:
            try:
                _release_lock(lock_path)
            except SkillManagementError as error:
                print(f"ERROR: {error}", file=sys.stderr)
                status = 2
    return status


def _read_expected_manifest(target_root: Path) -> bytes | None:
    manifest_path = target_root / MANIFEST_PATH
    _check_destination_path(target_root, manifest_path.parent)
    if manifest_path.is_symlink():
        raise SkillManagementError("Skill manifest must not be a symlink")
    if not manifest_path.exists():
        return None
    if not manifest_path.is_file():
        raise SkillManagementError("Skill manifest path is not a regular file")
    return manifest_path.read_bytes()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate Skill source directories")
    validate.add_argument("--source", type=Path, default=DEFAULT_SOURCE)

    for command in ("install", "sync", "rebind-source"):
        action = commands.add_parser(command, help=f"plan and optionally {command} Skills")
        action.add_argument("--target", type=Path, required=True, help="target repository root")
        agent_group = action.add_mutually_exclusive_group(required=True)
        agent_group.add_argument(
            "--agent", choices=sorted(AGENT_ROOTS), help="single agent discovery path"
        )
        agent_group.add_argument(
            "--agents",
            nargs="+",
            choices=sorted(AGENT_ROOTS),
            help="agents sharing or discovering the selected Skill package(s)",
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
        action.add_argument(
            "--allow-duplicate-discovery",
            action="store_true",
            help="explicitly allow duplicate discovery paths when host behavior is unverified",
        )
        action.add_argument(
            "--allow-dirty-source",
            action="store_true",
            help="explicitly install from a source checkout with uncommitted changes",
        )
    recover = commands.add_parser("recover", help="inspect or recover interrupted Skill updates")
    recover.add_argument("--target", type=Path, required=True, help="target repository root")
    recover.add_argument("--apply", action="store_true", help="apply safe transaction recovery")
    recover.add_argument(
        "--force",
        action="store_true",
        help="remove a lock only when its recorded process no longer exists",
    )
    return parser


def main() -> int:
    return _run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
