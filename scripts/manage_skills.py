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
import tarfile
import tempfile
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

if __package__:
    from .agent_skills import (
        DISCOVERY_PATHS,
        skill_directories,
        validate_official_skill_names,
        validate_repository_skills,
        validate_skill_directory,
        validate_skill_roots,
    )
else:
    from agent_skills import (
        DISCOVERY_PATHS,
        skill_directories,
        validate_official_skill_names,
        validate_repository_skills,
        validate_skill_directory,
        validate_skill_roots,
    )


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / ".agents" / "skills"
MANIFEST_PATH = Path(".devconcord") / "skills-manifest.json"
USER_CONFIG_PATH = Path(".devconcord") / "config.json"
CURRENT_SCHEMA_VERSION = 2
SKILL_HASH_VERSION = 2
# Copilot also loads personal Skills from ~/.copilot/skills. This directory is
# never a DevConcord destination, but it must participate in collision checks.
GLOBAL_DISCOVERY_PATHS = (".agents/skills", ".claude/skills", ".copilot/skills")
AGENT_ROOTS = {
    "codex": Path(".agents/skills"),
    "copilot": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
}


class SkillManagementError(ValueError):
    """An unsafe or inconsistent skill operation was requested."""


SkillAction = tuple[str, Path, str, str, str | None, tuple[str, ...]]


def _user_home() -> Path:
    try:
        home = Path.home().resolve(strict=True)
    except OSError as error:
        raise SkillManagementError(
            f"could not resolve the current user's home directory ({type(error).__name__})"
        ) from error
    if not home.is_dir():
        raise SkillManagementError("the current user's home directory is not a directory")
    return home


def _user_state_directory(*, create: bool = False) -> Path:
    state = _user_home() / ".devconcord"
    if state.is_symlink():
        raise SkillManagementError("user DevConcord state directory must not be a symlink")
    if state.exists() and not state.is_dir():
        raise SkillManagementError("user DevConcord state path is not a directory")
    if create:
        state.mkdir(mode=0o700, exist_ok=True)
        if state.is_symlink() or not state.is_dir():
            raise SkillManagementError("user DevConcord state directory changed during creation")
    return state


def _resolve_source_repository(source_root: Path) -> tuple[Path, Path]:
    try:
        repository = source_root.expanduser().resolve(strict=True)
    except OSError as error:
        raise SkillManagementError(
            f"DevConcord source path does not exist or cannot be resolved "
            f"({type(error).__name__})"
        ) from error
    if not repository.is_dir():
        raise SkillManagementError("DevConcord source root must be a directory")
    git_root = _git(repository, "rev-parse", "--show-toplevel", check=False)
    if git_root.returncode:
        raise SkillManagementError("DevConcord source root must be inside a Git repository")
    if Path(git_root.stdout.strip()).resolve() != repository:
        raise SkillManagementError("source_root must be the root of the DevConcord Git repository")
    if not (repository / "scripts" / "manage_skills.py").is_file():
        raise SkillManagementError("source_root does not contain scripts/manage_skills.py")
    skills_root = repository / ".agents" / "skills"
    if not skills_root.is_dir() or skills_root.is_symlink():
        raise SkillManagementError("source_root does not contain a regular .agents/skills directory")
    return repository, skills_root


def _validate_source_repository(source_root: Path) -> tuple[Path, Path]:
    repository, skills_root = _resolve_source_repository(source_root)
    validation_errors = validate_skill_roots([skills_root])
    if validation_errors:
        raise SkillManagementError(
            "DevConcord Skill source validation failed:\n" + "\n".join(validation_errors)
        )
    return repository, skills_root


def _read_user_config(
    *, validate_skills: bool = True
) -> tuple[dict[str, Any] | None, Path]:
    _user_state_directory()
    path = _user_home() / USER_CONFIG_PATH
    if path.is_symlink():
        raise SkillManagementError("user DevConcord config must not be a symlink")
    if not path.exists():
        return None, path
    if not path.is_file():
        raise SkillManagementError("user DevConcord config is not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillManagementError(
            f"cannot read user DevConcord config ({type(error).__name__})"
        ) from error
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "source_root"}
        or type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
        or not isinstance(value.get("source_root"), str)
        or not Path(value["source_root"]).is_absolute()
    ):
        raise SkillManagementError(
            "invalid user DevConcord config; expected schema_version 1 and an absolute source_root"
        )
    source_validation = (
        _validate_source_repository if validate_skills else _resolve_source_repository
    )
    repository, _skills_root = source_validation(Path(value["source_root"]))
    if value["source_root"] != str(repository):
        raise SkillManagementError(
            "user DevConcord config source_root is not normalized; use config set-source "
            "to register the resolved repository path"
        )
    return value, path


def _configured_source_skills(*, required: bool) -> Path | None:
    config, _path = _read_user_config()
    if config is None:
        if required:
            raise SkillManagementError(
                "no local DevConcord source is registered; run "
                "config set-source --source-root <repository>"
            )
        return None
    return Path(config["source_root"]) / ".agents" / "skills"


def _resolve_scope_target(args: argparse.Namespace) -> tuple[str, Path]:
    target = getattr(args, "target", None)
    scope = getattr(args, "scope", None)
    if scope is None:
        scope = "project" if target is not None else "user"
    if scope == "user":
        if target is not None:
            raise SkillManagementError(
                "--target cannot be combined with --scope user; omit --target to use User Scope"
            )
        return scope, _user_home()
    if scope == "project":
        if target is None:
            raise SkillManagementError("--target is required with --scope project")
        return scope, target.expanduser().resolve()
    raise SkillManagementError(f"unsupported Skill scope: {scope}")


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


def _executable_mode_is_reliable(root: Path) -> bool:
    if os.name == "nt":
        return False
    if _git(root, "rev-parse", "--show-toplevel", check=False).returncode:
        return True
    configured = _git(root, "config", "--bool", "--get", "core.filemode", check=False)
    return configured.returncode != 0 or configured.stdout.strip() == "true"


def _filesystem_executable_files(root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.stat().st_mode & 0o111
        )
    )


def _portable_tree_digest(root: Path, executable_files: tuple[str, ...]) -> str:
    executable_set = set(executable_files)
    regular_files: set[str] = set()
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise SkillManagementError(f"symlinks are not supported in skill packages: {path}")
        if not path.is_dir() and not path.is_file():
            raise SkillManagementError(f"unsupported non-regular file in skill package: {path}")
        relative_path = path.relative_to(root).as_posix()
        relative = relative_path.encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(b"D" if path.is_dir() else b"F")
        if path.is_file():
            regular_files.add(relative_path)
            digest.update(b"X" if relative_path in executable_set else b"-")
            content = path.read_bytes()
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
    missing = executable_set - regular_files
    if missing:
        raise SkillManagementError(
            "executable-file metadata references missing package paths: "
            + ", ".join(sorted(missing))
        )
    return digest.hexdigest()


def _git_skill_executable_files(source_root: Path, commit: str, skill_name: str) -> tuple[str, ...]:
    source_prefix = _git(source_root, "rev-parse", "--show-prefix").stdout.strip().strip("/")
    git_path = "/".join(part for part in (source_prefix, skill_name) if part)
    result = _git(
        source_root,
        "ls-tree",
        "-rz",
        "--full-tree",
        commit,
        "--",
        git_path,
    )
    executable_files: list[str] = []
    prefix = f"{git_path}/"
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", maxsplit=1)
        mode, _object_type, _object_id = metadata.split()
        if mode == "100755":
            if not path.startswith(prefix):
                raise SkillManagementError(
                    f"Git returned an unexpected path for Skill {skill_name!r}"
                )
            executable_files.append(path[len(prefix):])
    return tuple(sorted(executable_files))


def _source_executable_files(
    source_root: Path,
    revision: str,
    skill_name: str,
    *,
    dirty: bool,
) -> tuple[str, ...]:
    if revision == "unversioned":
        return (
            _filesystem_executable_files(source_root / skill_name)
            if _executable_mode_is_reliable(source_root)
            else ()
        )
    committed = _git_skill_executable_files(source_root, revision, skill_name)
    if not _executable_mode_is_reliable(source_root):
        return committed
    actual = _filesystem_executable_files(source_root / skill_name)
    if not dirty and actual != committed:
        raise SkillManagementError(
            f"Skill {skill_name!r} executable bits differ from Git; commit the change "
            "or explicitly pass --allow-dirty-source"
        )
    return actual if dirty else committed


def _verify_executable_files(
    root: Path,
    expected: tuple[str, ...],
) -> bool:
    if not _executable_mode_is_reliable(root):
        return True
    return _filesystem_executable_files(root) == expected


def _apply_executable_files(root: Path, executable_files: tuple[str, ...]) -> None:
    executable_set = set(executable_files)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.relative_to(root).as_posix() in executable_set:
            mode |= 0o100
        else:
            mode &= ~0o111
        path.chmod(mode)


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
    remotes = _git(source_root, "remote", check=False)
    if remotes.returncode:
        raise SkillManagementError(
            f"could not inspect Git remotes: {remotes.stderr.strip()}"
        )
    remote_names = remotes.stdout.splitlines()
    if "origin" in remote_names:
        remote_name = "origin"
    elif len(remote_names) == 1:
        remote_name = remote_names[0]
    elif len(remote_names) > 1:
        raise SkillManagementError(
            "source identity is ambiguous: multiple Git remotes exist without origin; "
            "add or select a unique origin remote before using this source"
        )
    else:
        remote_name = None
    if remote_name is None:
        repository = _local_repository_identity(Path(top.stdout.strip()))
    else:
        remote = _git(source_root, "remote", "get-url", remote_name, check=False)
        urls = remote.stdout.splitlines()
        if remote.returncode or len(urls) != 1 or not urls[0]:
            raise SkillManagementError(
                f"could not establish a unique source identity from Git remote "
                f"{remote_name!r}"
            )
        repository = _repository_identity(urls[0], source_root)
    repository = "".join(character for character in repository if character.isprintable())[:512]
    return commit.stdout.strip(), bool(status.stdout.strip()), repository


def _user_source_revision(source_root: Path) -> tuple[str, bool, str]:
    revision, dirty, repository = source_revision(source_root)
    if not repository.startswith("local-git-sha256:"):
        return revision, dirty, repository
    roots = _git(source_root, "rev-list", "--max-parents=0", "HEAD", check=False)
    if roots.returncode or not roots.stdout.strip():
        raise SkillManagementError(
            "could not establish a stable identity for the local User Scope source"
        )
    identity = hashlib.sha256(
        "\n".join(sorted(roots.stdout.splitlines())).encode("ascii")
    ).hexdigest()
    return revision, dirty, f"local-git-history-sha256:{identity}"


def _local_repository_identity(repository_root: Path) -> str:
    common_dir = _git(repository_root, "rev-parse", "--git-common-dir")
    common_path = Path(common_dir.stdout.strip())
    if not common_path.is_absolute():
        common_path = repository_root / common_path
    identity = hashlib.sha256(str(common_path.resolve()).encode("utf-8")).hexdigest()
    return f"local-git-sha256:{identity}"


def _repository_identity(remote: str, source_root: Path | None = None) -> str:
    parsed = urlsplit(remote)
    if parsed.scheme == "file":
        local_path = Path(parsed.path)
        if local_path.is_dir():
            return _local_repository_identity(local_path)
        return "local Git repository"
    if parsed.hostname:
        host = parsed.hostname.lower()
        path = parsed.path.strip("/")
    elif "@" in remote and ":" in remote and "://" not in remote:
        host, path = remote.rsplit("@", maxsplit=1)[1].split(":", maxsplit=1)
        host = host.lower()
    elif (
        source_root is not None
        and (remote.startswith(("./", "../")) or Path(remote).is_absolute())
    ):
        local_path = Path(remote)
        if not local_path.is_absolute():
            local_path = source_root / local_path
        if local_path.is_dir():
            return _local_repository_identity(local_path)
        return "local Git repository"
    elif "/" in remote and "://" not in remote:
        if remote.startswith("/"):
            local_path = Path(remote)
            if local_path.is_dir():
                return _local_repository_identity(local_path)
            return "local Git repository"
        host, path = remote.split("/", maxsplit=1)
        host = host.lower()
    else:
        return "local Git repository"
    if path.endswith(".git"):
        path = path[:-4]
    if not path:
        return "local Git repository"
    return f"{host}/{path}"


def _source_identity_is_verified(value: Any) -> bool:
    return isinstance(value, str) and value not in {"", "local Git repository"}


def _normalize_recorded_source_identity(value: str) -> str:
    if value == "local Git repository":
        return value
    if value.startswith(("local-git-sha256:", "local-git-history-sha256:")):
        return value
    return _repository_identity(value)


def _git_skill_digest(
    source_root: Path,
    commit: str,
    skill_name: str,
    *,
    legacy: bool = False,
) -> str:
    with tempfile.TemporaryDirectory(prefix="devconcord-skill-baseline-") as temporary:
        temporary_root = Path(temporary)
        archive_path = temporary_root / "skill.tar"
        with archive_path.open("wb") as archive_file:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(source_root),
                    "archive",
                    "--format=tar",
                    commit,
                    "--",
                    skill_name,
                ],
                stdout=archive_file,
                stderr=subprocess.PIPE,
                check=False,
                text=False,
            )
        if result.returncode:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise SkillManagementError(
                f"could not read baseline Skill {skill_name!r} at {commit}: {detail}"
            )
        extracted_root = temporary_root / "extracted"
        extracted_root.mkdir()
        directory_modes: list[tuple[Path, int]] = []
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive.getmembers():
                member_path = Path(member.name)
                if (
                    member_path.is_absolute()
                    or ".." in member_path.parts
                    or not member_path.parts
                    or member_path.parts[0] != skill_name
                ):
                    raise SkillManagementError(
                        f"baseline archive contains an unsafe path for Skill {skill_name!r}"
                    )
                destination = extracted_root / member_path
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    directory_modes.append((destination, 0o755))
                elif member.isfile():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source_file = archive.extractfile(member)
                    if source_file is None:
                        raise SkillManagementError(
                            f"baseline archive has an unreadable file for Skill {skill_name!r}"
                        )
                    with source_file, destination.open("xb") as output_file:
                        shutil.copyfileobj(source_file, output_file)
                    file_mode = 0o755 if member.mode & 0o111 else 0o644
                    os.chmod(destination, file_mode)
                else:
                    raise SkillManagementError(
                        f"baseline archive contains unsupported content for Skill {skill_name!r}"
                    )
        for directory, mode in reversed(directory_modes):
            os.chmod(directory, mode)
        skill_root = extracted_root / skill_name
        if not skill_root.is_dir():
            raise SkillManagementError(
                f"baseline commit {commit} does not contain Skill {skill_name!r}"
            )
        if legacy:
            return tree_digest(skill_root)
        return _portable_tree_digest(
            skill_root,
            _git_skill_executable_files(source_root, commit, skill_name),
        )


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
        _duplicate_allowances(value)
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
            hash_version = record.get("hash_version", 1)
            executable_files = record.get("source_executable_files")
            if type(hash_version) is int and hash_version == SKILL_HASH_VERSION:
                if (
                    not isinstance(executable_files, list)
                    or any(
                        not isinstance(path, str)
                        or not path
                        or path.startswith("/")
                        or "\\" in path
                        or any(part in {"", ".", ".."} for part in path.split("/"))
                        for path in executable_files
                    )
                    or executable_files != sorted(set(executable_files))
                ):
                    raise SkillManagementError(
                        f"invalid executable-file metadata for Skill {name!r} "
                        f"at {package_path!r}"
                    )
            elif type(hash_version) is not int or hash_version != 1 or executable_files is not None:
                raise SkillManagementError(
                    f"unsupported Skill hash version for {name!r} at {package_path!r}"
                )


def _recorded_package_digest(skill_dir: Path, record: dict[str, Any]) -> str:
    if record.get("hash_version", 1) == SKILL_HASH_VERSION:
        executable_files = tuple(record["source_executable_files"])
        if not _verify_executable_files(skill_dir, executable_files):
            raise SkillManagementError(
                f"installed Skill executable bits differ from manifest: {skill_dir}"
            )
        return _portable_tree_digest(skill_dir, executable_files)
    return tree_digest(skill_dir)


def _duplicate_allowances(
    manifest: dict[str, Any],
) -> set[tuple[str, tuple[str, str]]]:
    records = manifest.get("duplicate_discovery_allowances", [])
    if not isinstance(records, list):
        raise SkillManagementError("invalid duplicate-discovery allowances in Skill manifest")
    allowed_paths = set(DISCOVERY_PATHS)
    allowances: set[tuple[str, tuple[str, str]]] = set()
    for record in records:
        if (
            not isinstance(record, dict)
            or set(record) != {"skill", "paths"}
            or not _valid_skill_name(record.get("skill"))
            or not isinstance(record.get("paths"), list)
            or len(record["paths"]) != 2
            or any(not isinstance(path, str) for path in record["paths"])
            or any(path not in allowed_paths for path in record["paths"])
            or len(set(record["paths"])) != 2
        ):
            raise SkillManagementError(
                "invalid duplicate-discovery allowance in Skill manifest"
            )
        pair = tuple(sorted(record["paths"]))
        allowance = (record["skill"].casefold(), pair)
        if allowance in allowances:
            raise SkillManagementError(
                "duplicate duplicate-discovery allowance in Skill manifest"
            )
        allowances.add(allowance)
    return allowances


def _copilot_is_exposed(manifest: dict[str, Any]) -> bool:
    return any(
        "copilot" in package.get("agents", [])
        for package in manifest["packages"].values()
    )


def _discovery_state(
    target_root: Path,
    names: set[str],
    *,
    actions: list[tuple[SkillAction, str]] | None = None,
    manifest: dict[str, Any],
    discovery_paths: tuple[str, ...] = DISCOVERY_PATHS,
) -> dict[str, dict[str, tuple[str, str]]]:
    interested_names = {name.casefold() for name in names}
    state: dict[str, dict[str, tuple[str, str]]] = {}
    for relative in discovery_paths:
        root = target_root / relative
        _check_destination_path(target_root, root)
        if not root.exists():
            continue
        if root.is_symlink() or not root.is_dir():
            raise SkillManagementError(f"cannot inspect Skill discovery path {relative}")
        recorded_skills = manifest["packages"].get(relative, {}).get("skills", {})
        try:
            entries = sorted(root.iterdir())
        except OSError as error:
            raise SkillManagementError(
                f"cannot inspect Skill discovery path {relative} ({type(error).__name__})"
            ) from error
        for skill_dir in entries:
            name_key = skill_dir.name.casefold()
            if name_key not in interested_names:
                continue
            if skill_dir.is_symlink():
                raise SkillManagementError(
                    f"{relative}/{skill_dir.name}: same-name Skill path is a symlink; "
                    "preserving it"
                )
            if not skill_dir.is_dir():
                raise SkillManagementError(
                    f"{relative}/{skill_dir.name}: same-name Skill path is not a directory"
                )
            recorded = recorded_skills.get(skill_dir.name)
            if recorded is not None:
                recorded_digest = _recorded_package_digest(skill_dir, recorded)
                if recorded_digest != recorded.get("installed_tree_sha256"):
                    raise SkillManagementError(
                        f"{relative}/{skill_dir.name}: installed Skill differs from its "
                        "manifest hash; refusing to plan around an externally changed package"
                    )
                if recorded.get("hash_version", 1) == SKILL_HASH_VERSION:
                    executable_files = tuple(recorded["source_executable_files"])
                else:
                    executable_files = (
                        _filesystem_executable_files(skill_dir)
                        if _executable_mode_is_reliable(target_root)
                        else ()
                    )
                digest = _portable_tree_digest(skill_dir, executable_files)
            else:
                digest = _portable_tree_digest(
                    skill_dir,
                    _filesystem_executable_files(skill_dir)
                    if _executable_mode_is_reliable(target_root)
                    else (),
                )
            roots = state.setdefault(name_key, {})
            if relative in roots:
                raise SkillManagementError(
                    f"{relative}: case-insensitive duplicate Skill name {skill_dir.name!r}"
                )
            roots[relative] = (skill_dir.name, digest)

    for action_tuple, relative in actions or []:
        action, _source, name, source_hash, _expected_target_hash, _executable_files = action_tuple
        if action not in {"install", "update", "metadata", "unchanged"}:
            continue
        if name.casefold() in interested_names:
            state.setdefault(name.casefold(), {})[relative] = (name, source_hash)
    return state


def _check_duplicate_discovery(
    state: dict[str, dict[str, tuple[str, str]]],
    manifest: dict[str, Any],
    *,
    allow_duplicates: bool,
) -> tuple[bool, list[str]]:
    allowances = _duplicate_allowances(manifest)
    updated_allowances = set(allowances)
    conflicts: list[str] = []
    has_duplicates = False
    for skill_key, roots in state.items():
        if len(roots) < 2:
            continue
        paths = sorted(roots)
        if len({digest for _, digest in roots.values()}) != 1:
            conflicts.append(
                f"{skill_key}: same-name Skills in Copilot discovery paths have different "
                "contents; synchronize all managed copies together"
            )
            continue
        has_duplicates = True
        for index, first_path in enumerate(paths):
            for second_path in paths[index + 1 :]:
                allowance = (skill_key, (first_path, second_path))
                if allowance in allowances:
                    continue
                if not allow_duplicates:
                    conflicts.append(
                        f"{skill_key}: identical Skills in {first_path} and {second_path} "
                        "may be discovered more than once; explicitly pass "
                        "--allow-duplicate-discovery after reviewing the host behavior"
                    )
                    continue
                updated_allowances.add(allowance)
    if updated_allowances != allowances:
        manifest["duplicate_discovery_allowances"] = [
            {"skill": skill, "paths": list(paths)}
            for skill, paths in sorted(updated_allowances)
        ]
    return has_duplicates, conflicts


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
    discovery_paths: tuple[str, ...] = DISCOVERY_PATHS,
    scope: str = "project",
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
    duplicate_exposure = False
    revision, dirty, repository = (
        _user_source_revision(source_root) if scope == "user" else source_revision(source_root)
    )
    if dirty and not allow_dirty_source:
        raise SkillManagementError(
            "Skill source has uncommitted changes; commit them or explicitly pass "
            "--allow-dirty-source"
        )
    source_executable_files = {
        name: _source_executable_files(
            source_root,
            revision,
            name,
            dirty=dirty,
        )
        for name in names
        if name in available
    }
    source_hashes = {
        name: _portable_tree_digest(available[name], executable_files)
        for name, executable_files in source_executable_files.items()
    }
    if revision != "unversioned" and not dirty:
        for name, source_hash in source_hashes.items():
            committed_hash = _git_skill_digest(source_root, revision, name)
            if committed_hash != source_hash:
                if not allow_dirty_source:
                    raise SkillManagementError(
                        f"Skill {name!r} differs from its Git commit baseline; commit the "
                        "complete Skill source or explicitly pass --allow-dirty-source"
                    )
                dirty = True
    actions: list[tuple[SkillAction, str]] = []
    conflicts: list[str] = []
    history_cache: dict[tuple[str, str], str] = {}
    baseline_digest_cache: dict[tuple[str, str], str] = {}
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
                if not isinstance(recorded, dict):
                    conflicts.append(f"{name}: local modifications detected; target preserved")
                    continue
                try:
                    recorded_digest = _recorded_package_digest(target, recorded)
                except SkillManagementError:
                    recorded_digest = None
                if recorded_digest != recorded.get("installed_tree_sha256"):
                    conflicts.append(f"{name}: local modifications detected; target preserved")
                    continue
                baseline = recorded.get("source_commit", "unversioned")
                if operation == "rebind-source":
                    history = "rebind"
                else:
                    try:
                        history_key = (baseline, revision)
                        history = history_cache.get(history_key)
                        if history is None:
                            history = _validate_history(source_root, baseline, revision)
                            history_cache[history_key] = history
                        recorded_source = recorded.get("source_repository")
                        if (
                            not _source_identity_is_verified(recorded_source)
                            or not _source_identity_is_verified(repository)
                            or _normalize_recorded_source_identity(recorded_source)
                            != _normalize_recorded_source_identity(repository)
                        ):
                            raise SkillManagementError(
                                "Skill source identity changed or cannot be verified; "
                                "use rebind-source only after reviewing the new source"
                            )
                        if recorded.get("source_dirty"):
                            raise SkillManagementError(
                                "the recorded baseline contains uncommitted source changes; "
                                "use rebind-source to establish a new baseline"
                            )
                        digest_key = (baseline, name)
                        baseline_digest = baseline_digest_cache.get(digest_key)
                        if baseline_digest is None:
                            baseline_digest = _git_skill_digest(
                                source_root,
                                baseline,
                                name,
                                legacy=recorded.get("hash_version", 1) == 1,
                            )
                            baseline_digest_cache[digest_key] = baseline_digest
                        if baseline_digest != recorded.get("source_tree_sha256"):
                            raise SkillManagementError(
                                "recorded baseline Skill content does not match the "
                                "source_commit and source_tree_sha256"
                            )
                    except SkillManagementError as error:
                        conflicts.append(f"{name} ({relative}): {error}")
                        continue
                if recorded.get("hash_version", 1) == 1:
                    if baseline != "unversioned":
                        source_is_same = (
                            source_hash == _git_skill_digest(source_root, baseline, name)
                        )
                    else:
                        source_is_same = source_hash == _portable_tree_digest(
                            target,
                            source_executable_files[name],
                        )
                else:
                    source_is_same = source_hash == recorded.get("source_tree_sha256")
                if source_is_same:
                    action = (
                        "unchanged"
                        if (
                            recorded.get("hash_version", 1) == SKILL_HASH_VERSION
                            and (history == "unchanged" or operation == "install")
                        )
                        else "metadata"
                    )
                elif operation in {"sync", "rebind-source"}:
                    action = "update"
                else:
                    conflicts.append(f"{name}: source has changed; run sync to review update")
                    continue
                actions.append(
                    (
                        (
                            action,
                            source,
                            name,
                            source_hash,
                            current_hash,
                            source_executable_files[name],
                        ),
                        relative,
                    )
                )
            else:
                actions.append(
                    (
                        (
                            "install",
                            source,
                            name,
                            source_hash,
                            None,
                            source_executable_files[name],
                        ),
                        relative,
                    )
                )

    if "copilot" in requested_agents or _copilot_is_exposed(manifest):
        try:
            projected = _discovery_state(
                target_root,
                set(names),
                actions=actions,
                manifest=manifest,
                discovery_paths=discovery_paths,
            )
            duplicate_exposure, duplicate_conflicts = _check_duplicate_discovery(
                projected,
                manifest,
                allow_duplicates=allow_duplicate_discovery,
            )
            conflicts.extend(duplicate_conflicts)
        except (OSError, SkillManagementError) as error:
            conflicts.append(f"cannot validate post-operation Skill discovery state: {error}")

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
    if old_manifest_hash is not None:
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

    rollback_plan: list[tuple[Path, Path | None, str | None, str | None]] = []
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
        if old_hash is not None and (backup is None or not backup.is_dir()):
            raise SkillManagementError(
                f"required transaction backup is missing for {destination}"
            )
        rollback_plan.append((destination, backup, old_hash, current_hash))

    manifest_needs_restore = manifest_hash != old_manifest_hash
    manifest_backup = (
        transaction_root / manifest_backup_name
        if manifest_backup_name is not None
        else None
    )

    for destination, backup, old_hash, expected_current_hash in rollback_plan:
        if _tree_digest_or_missing(destination) != expected_current_hash:
            raise SkillManagementError(
                f"target changed during recovery; preserving {destination}"
            )
        if backup is not None:
            if not backup.is_dir() or tree_digest(backup) != old_hash:
                raise SkillManagementError(
                    f"backup changed during recovery; preserving {backup}"
                )
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(backup, destination)
        elif destination.exists():
            shutil.rmtree(destination)

    if manifest_needs_restore and old_manifest_hash is not None:
        if manifest_backup is None or not manifest_backup.is_file():
            raise SkillManagementError("manifest backup changed during recovery")
        current_manifest = (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if manifest_path.is_file()
            else None
        )
        if current_manifest != new_manifest_hash:
            raise SkillManagementError(
                "manifest changed during recovery; preserve the transaction"
            )
        _write_bytes_atomically(manifest_path, manifest_backup.read_bytes())
    elif manifest_needs_restore and old_manifest_hash is None:
        current_manifest = (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            if manifest_path.is_file()
            else None
        )
        if current_manifest != new_manifest_hash:
            raise SkillManagementError(
                "manifest changed during recovery; preserve the transaction"
            )
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
    discovery_paths: tuple[str, ...] = DISCOVERY_PATHS,
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
            (
                action,
                source,
                name,
                source_hash,
                expected_target_hash,
                executable_files,
            ) = action_tuple
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
            if _executable_mode_is_reliable(target_root):
                _apply_executable_files(staged_dir, executable_files)
            if _portable_tree_digest(staged_dir, executable_files) != source_hash:
                raise SkillManagementError(f"staged Skill differs from source: {name}")
            journal_entries.append(
                {
                    "destination": destination.relative_to(target_root).as_posix(),
                    "staged": staged_dir.relative_to(transaction_root).as_posix(),
                    "backup": f"backups/{index}",
                    "new_tree_sha256": tree_digest(staged_dir),
                    "old_tree_sha256": expected_target_hash,
                }
            )

        for action_tuple, relative in actions:
            (
                action,
                _source,
                name,
                source_hash,
                _expected_target_hash,
                executable_files,
            ) = action_tuple
            package = manifest["packages"][relative]
            if action in {"install", "update", "metadata", "unchanged"}:
                package["skills"][name] = {
                    "source_repository": source_repository,
                    "source_commit": source_commit,
                    "source_dirty": source_dirty,
                    "source_tree_sha256": source_hash,
                    "installed_tree_sha256": source_hash,
                    "hash_version": SKILL_HASH_VERSION,
                    "source_executable_files": list(executable_files),
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
        if _copilot_is_exposed(manifest):
            changed_names = {action[0][2] for action in actions}
            discovery_state = _discovery_state(
                target_root,
                changed_names,
                manifest=manifest,
                discovery_paths=discovery_paths,
            )
            _has_duplicates, duplicate_conflicts = _check_duplicate_discovery(
                discovery_state,
                manifest,
                allow_duplicates=False,
            )
            if duplicate_conflicts:
                raise SkillManagementError(
                    "post-apply discovery validation failed:\n- "
                    + "\n- ".join(duplicate_conflicts)
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
    if args.command == "config":
        return _config_command(args)
    if args.command == "reference":
        return _reference_command(args)
    if args.command == "doctor":
        return _doctor_command(args)

    if args.command == "validate":
        target = getattr(args, "target", None)
        scope = getattr(args, "scope", None)
        if scope == "user":
            if target is not None:
                print("ERROR: --target cannot be combined with --scope user", file=sys.stderr)
                return 2
            try:
                _read_user_config()
                errors = _validate_user_installation(_user_home())
            except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
                errors = [f"User Scope validation stopped safely ({error})"]
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            return 0
        if scope not in {None, "project"}:
            print(f"ERROR: unsupported Skill scope: {scope}", file=sys.stderr)
            return 2
        if target is not None:
            root = target.expanduser().resolve()
            if not root.is_dir():
                print(f"ERROR: target repository does not exist: {root}", file=sys.stderr)
                return 1
            errors = validate_repository_skills(root, require_canonical_source=False)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"Validated Agent Skills in target repository {root}")
            return 0
        if scope == "project":
            print("ERROR: --target is required with --scope project", file=sys.stderr)
            return 2
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
        if root == DEFAULT_SOURCE.resolve():
            errors.extend(validate_official_skill_names(root))
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"Validated {len(directories)} Agent Skills in {root}")
        return 0

    try:
        scope, target_root = _resolve_scope_target(args)
    except (SkillManagementError, OSError, ValueError) as error:
        print(f"ERROR: Skill scope could not be resolved safely: {error}", file=sys.stderr)
        return 2

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
                if scope == "user":
                    _user_state_directory(create=True)
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

    explicit_agents = getattr(args, "agents", None)
    single_agent = getattr(args, "agent", None)
    requested_agents = set(explicit_agents or ([single_agent] if single_agent else []))
    if not requested_agents:
        try:
            existing_manifest, _migrated = _read_manifest(target_root / MANIFEST_PATH)
            requested_agents = {
                    agent
                    for package in existing_manifest["packages"].values()
                    for agent in package["agents"]
            }
        except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
            print(f"ERROR: cannot determine managed agents safely: {error}", file=sys.stderr)
            return 2
    if not requested_agents:
        print(
            "ERROR: no managed Skills found; specify --agent or --agents",
            file=sys.stderr,
        )
        return 2
    try:
        configured_source = (
            _configured_source_skills(required=False) if scope == "user" else None
        )
        source_root = (
            args.source.expanduser().resolve()
            if getattr(args, "source", None) is not None
            else configured_source or DEFAULT_SOURCE.resolve()
        )
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        print(f"ERROR: Skill source could not be resolved safely: {error}", file=sys.stderr)
        return 2
    discovery_paths = GLOBAL_DISCOVERY_PATHS if scope == "user" else DISCOVERY_PATHS
    if getattr(args, "command") == "rebind-source":
        print(
            "WARNING: rebind-source explicitly accepts a different or older Skill source; "
            "review the plan before applying."
        )
    lock_path: Path | None = None
    status = 0
    try:
        if not target_root.is_dir():
            raise SkillManagementError(
                f"{scope} Skill destination root does not exist: {target_root}"
            )
        if args.apply:
            if scope == "user":
                _user_state_directory(create=True)
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
            discovery_paths,
            scope,
        )
        for (
            action,
            _source,
            name,
            _source_hash,
            _expected_target_hash,
            _executable_files,
        ), package_path in actions:
            print(f"{action}: {package_path}/{name}")
        print(
            f"Source: {repository} @ {revision}"
            + (" (uncommitted Skill changes)" if dirty else "")
        )
        print(f"Scope: {scope} ({target_root})")
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
                    discovery_paths,
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


def _config_command(args: argparse.Namespace) -> int:
    try:
        if args.config_command == "show":
            config, path = _read_user_config()
            if config is None:
                raise SkillManagementError(
                    f"no local DevConcord source is registered in {path}; "
                    "run config set-source --source-root <repository>"
                )
            root = Path(config["source_root"])
            revision, dirty, repository = _user_source_revision(root / ".agents" / "skills")
            print(f"Config: {path}")
            print(f"Source root: {root}")
            print(f"Source: {repository} @ {revision}")
            if dirty:
                print("WARNING: DevConcord Skills have uncommitted changes.")
            return 0

        if args.config_command != "set-source":
            raise SkillManagementError(f"unsupported config operation: {args.config_command}")

        repository, _skills_root = _validate_source_repository(args.source_root)
        _user_state_directory()
        config_path = _user_home() / USER_CONFIG_PATH
        if config_path.is_symlink():
            raise SkillManagementError("user DevConcord config must not be a symlink")
        if config_path.exists() and not args.replace:
            raise SkillManagementError(
                "user DevConcord config already exists; inspect it and pass --replace "
                "to change or repair source_root"
            )
        home = _user_home()
        lock_path = home / ".devconcord" / "skills.lock"
        if lock_path.exists() or lock_path.is_symlink() or _transaction_directories(home):
            raise SkillManagementError(
                "cannot change source configuration while a Skill operation is active "
                "or awaiting recovery"
            )
        _user_state_directory(create=True)
        content = json.dumps(
            {"schema_version": 1, "source_root": str(repository)},
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        _write_atomically(config_path, content)
        print(f"Registered local DevConcord source: {repository}")
        print(f"Config: {config_path}")
        if args.replace:
            print(
                "Existing Skill manifest was not changed; source changes still require "
                "an explicit rebind-source operation."
            )
        return 0
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        print(f"ERROR: user configuration operation stopped safely: {error}", file=sys.stderr)
        return 2


def _validate_user_installation(home: Path) -> list[str]:
    manifest_path = home / MANIFEST_PATH
    if manifest_path.is_symlink():
        return ["user Skill manifest must not be a symlink"]
    if not manifest_path.exists():
        return ["no User Scope Skill manifest was found"]
    try:
        manifest, _migrated = _read_manifest(manifest_path)
        pending = _transaction_directories(home)
        if pending:
            return [
                "interrupted User Scope Skill transaction requires recovery: "
                + ", ".join(path.name for path in pending)
            ]
        managed: dict[str, set[str]] = {}
        names: set[str] = set()
        errors: list[str] = []
        for relative, package in manifest["packages"].items():
            root = home / relative
            _check_destination_path(home, root)
            for name, record in package["skills"].items():
                names.add(name)
                managed.setdefault(name, set()).update(package["agents"])
                skill_dir = root / name
                if skill_dir.is_symlink() or not skill_dir.is_dir():
                    errors.append(f"{relative}/{name}: managed Skill is missing or unsafe")
                    continue
                errors.extend(validate_skill_directory(skill_dir))
                try:
                    digest = _recorded_package_digest(skill_dir, record)
                except (SkillManagementError, OSError, ValueError) as error:
                    errors.append(f"{relative}/{name}: cannot verify managed Skill ({error})")
                    continue
                if digest != record["installed_tree_sha256"]:
                    errors.append(f"{relative}/{name}: installed Skill hash differs from manifest")
        if names:
            state = _discovery_state(
                home,
                names,
                manifest=manifest,
                discovery_paths=GLOBAL_DISCOVERY_PATHS,
            )
            _has_duplicates, conflicts = _check_duplicate_discovery(
                state, manifest, allow_duplicates=False
            )
            errors.extend(conflicts)
        count = sum(len(package["skills"]) for package in manifest["packages"].values())
        if not errors:
            print(f"Validated {count} DevConcord-managed Skill package(s) in User Scope")
        return errors
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        return [f"cannot validate User Scope Skills safely ({type(error).__name__}: {error})"]


def _safe_reference_path(value: str) -> str:
    path = Path(value)
    parts = value.split("/")
    # Retain prompts/ for version-pinned reads of files in older Skill commits.
    allowed_directory_roots = {"docs", ".agents", "prompts"}
    allowed_root_files = {"README.md", "AGENTS.md", "REVIEWS.md"}
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or "\0" in value
        or any(part in {"", ".", ".."} for part in parts)
        or not (
            (len(parts) == 1 and parts[0] in allowed_root_files)
            or (len(parts) > 1 and parts[0] in allowed_directory_roots)
        )
    ):
        raise SkillManagementError(
            "reference path must be under docs/, .agents/, historical prompts/, "
            "or one of README.md, AGENTS.md, and REVIEWS.md"
        )
    return path.as_posix()


def _reference_command(args: argparse.Namespace) -> int:
    try:
        config, _config_path = _read_user_config(validate_skills=False)
        if config is None:
            raise SkillManagementError(
                "no local DevConcord source is registered; run "
                "config set-source --source-root <repository>"
            )
        source_root = Path(config["source_root"])
        relative = _safe_reference_path(args.path)
        source_path = source_root / relative
        target = getattr(args, "target", None)
        scope = getattr(args, "scope", None)
        if scope is None:
            scope = "project" if target is not None else "user"
        if scope == "user":
            if target is not None:
                raise SkillManagementError(
                    "--target cannot be combined with --scope user"
                )
            installation_root = _user_home()
        elif scope == "project":
            if target is None:
                raise SkillManagementError("--target is required with --scope project")
            installation_root = target.expanduser().resolve()
            if not installation_root.is_dir():
                raise SkillManagementError("Project Scope reference target does not exist")
        else:
            raise SkillManagementError(f"unsupported Skill scope: {scope}")
        current_source_revision = (
            _user_source_revision if scope == "user" else source_revision
        )
        source_identity: str
        source_head: str
        metadata_lines: list[str] = []
        commit_validated = False
        if args.revision == "working-tree":
            for parent in (source_path, *source_path.parents):
                if parent == source_root.parent:
                    break
                if parent.is_symlink():
                    raise SkillManagementError(
                        "refusing to read a symlinked local reference path"
                    )
            if not source_path.resolve().is_relative_to(source_root):
                raise SkillManagementError("local reference path escapes source_root")
            if not source_path.is_file():
                raise SkillManagementError(f"local reference does not exist: {relative}")
            content = source_path.read_text(encoding="utf-8")
            source_head, _source_dirty, source_identity = current_source_revision(
                source_root / ".agents" / "skills"
            )
            changed = _git(
                source_root, "status", "--porcelain", "--", relative, check=False
            )
            if changed.returncode:
                raise SkillManagementError("could not inspect local reference Git state")
            metadata_lines.append(
                f"Reference: local working tree"
                + (" (uncommitted or untracked changes)" if changed.stdout.strip() else "")
            )
        else:
            if args.revision == "installed":
                manifest, _migrated = _read_manifest(installation_root / MANIFEST_PATH)
                records = [
                    (package_path, record)
                    for package_path, package in manifest["packages"].items()
                    if args.skill in package["skills"]
                    for record in [package["skills"][args.skill]]
                ]
                if not records:
                    raise SkillManagementError(
                        f"Skill {args.skill!r} is not installed in {scope.title()} Scope"
                    )
                baselines = {
                    (record["source_commit"], record["source_repository"])
                    for _package_path, record in records
                }
                if len(baselines) != 1:
                    raise SkillManagementError(
                        f"User Scope copies of {args.skill!r} have different source baselines"
                    )
                commit, recorded_repository = next(iter(baselines))
                if commit == "unversioned":
                    raise SkillManagementError(
                        "installed Skill has no Git commit baseline; use --revision head "
                        "or --revision working-tree"
                    )
                if any(record.get("source_dirty") for _path, record in records):
                    raise SkillManagementError(
                        "installed Skill source was dirty; strict installed reference cannot "
                        "prove an exact Git version; choose --revision head or working-tree "
                        "explicitly if that version is intended"
                    )
                revision, _dirty, current_repository = current_source_revision(
                    source_root / ".agents" / "skills"
                )
                if (
                    not _source_identity_is_verified(recorded_repository)
                    or not _source_identity_is_verified(current_repository)
                    or _normalize_recorded_source_identity(recorded_repository)
                    != _normalize_recorded_source_identity(current_repository)
                ):
                    raise SkillManagementError(
                        "configured source identity differs from the installed Skill; "
                        "review the source and use rebind-source only if the change is intentional"
                    )
                if not _full_commit_id(commit):
                    raise SkillManagementError("installed Skill source commit is invalid")
                commit_check = _git(
                    source_root,
                    "cat-file",
                    "-e",
                    f"{commit}^{{commit}}",
                    check=False,
                )
                if commit_check.returncode:
                    raise SkillManagementError(
                        f"recorded source commit is missing from the configured local "
                        f"repository: {commit}"
                    )
                commit_validated = True
                for package_path, record in records:
                    skill_dir = installation_root / package_path / args.skill
                    if skill_dir.is_symlink() or not skill_dir.is_dir():
                        raise SkillManagementError(
                            f"installed Skill package is missing or unsafe: {package_path}/{args.skill}"
                        )
                    if _recorded_package_digest(skill_dir, record) != record["installed_tree_sha256"]:
                        raise SkillManagementError(
                            f"installed Skill was locally modified: {package_path}/{args.skill}"
                        )
                    try:
                        source_digest = _git_skill_digest(
                            source_root / ".agents" / "skills",
                            commit,
                            args.skill,
                            legacy=record.get("hash_version", 1) == 1,
                        )
                    except SkillManagementError as error:
                        raise SkillManagementError(
                            f"cannot verify installed Skill source baseline: {error}"
                        ) from error
                    if source_digest != record["source_tree_sha256"]:
                        raise SkillManagementError(
                            "installed Skill source baseline does not match the recorded "
                            "source_tree_sha256 at source_commit"
                        )
                metadata_lines.append(
                    f"Reference: installed Skill {args.skill} source commit {commit}"
                    f" (current source HEAD {revision})"
                )
                source_identity = current_repository
                source_head = revision
            else:
                revision, _dirty, source_identity = current_source_revision(
                    source_root / ".agents" / "skills"
                )
                commit = revision
                source_head = revision
                metadata_lines.append(
                    f"Reference: configured source HEAD {commit}; uncommitted edits excluded"
                )
            if not commit_validated:
                commit_check = _git(
                    source_root,
                    "cat-file",
                    "-e",
                    f"{commit}^{{commit}}",
                    check=False,
                )
                if commit_check.returncode:
                    raise SkillManagementError(
                        f"required Git commit {commit} is not available in the configured local repository"
                    )
            tree_entry = _git(
                source_root,
                "ls-tree",
                "-z",
                "--full-tree",
                commit,
                "--",
                relative,
                check=False,
            )
            if tree_entry.returncode:
                raise SkillManagementError(
                    f"Git could not inspect reference {relative!r} at commit {commit}: "
                    f"{tree_entry.stderr.strip()}"
                )
            entries = [entry for entry in tree_entry.stdout.split("\0") if entry]
            if not entries:
                raise SkillManagementError(
                    f"reference {relative!r} does not exist at Git commit {commit}"
                )
            if len(entries) != 1 or "\t" not in entries[0]:
                raise SkillManagementError(
                    f"Git returned malformed tree data for reference {relative!r}"
                )
            metadata, tree_path = entries[0].split("\t", maxsplit=1)
            fields = metadata.split()
            if (
                len(fields) != 3
                or tree_path != relative
                or fields[1] not in {"blob", "tree", "commit"}
                or not _full_commit_id(fields[2])
            ):
                raise SkillManagementError(
                    f"Git returned malformed tree data for reference {relative!r}"
                )
            mode, object_type, _object_id = fields
            if mode not in {"100644", "100755"} or object_type != "blob":
                raise SkillManagementError(
                    f"reference {relative!r} is not a regular Git file at commit {commit} "
                    f"(mode {mode}, type {object_type})"
                )
            result = _git(
                source_root, "show", f"{commit}:{relative}", check=False
            )
            if result.returncode:
                raise SkillManagementError(
                    f"Git could not read reference {relative!r} at commit {commit}"
                )
            content = result.stdout
        metadata_lines.extend(
            (
                f"Reference path: {relative}",
                f"Source identity: {source_identity}; source HEAD {source_head}",
            )
        )
        output = "\n".join(metadata_lines) + "\n" + content
        if content and not content.endswith("\n"):
            output += "\n"
        sys.stdout.write(output)
        return 0
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        print(f"ERROR: local DevConcord reference unavailable: {error}", file=sys.stderr)
        return 2


def _doctor_command(args: argparse.Namespace) -> int:
    try:
        config, config_path = _read_user_config()
        if config is None:
            print(
                f"Local DevConcord source is not configured ({config_path}); "
                "run config set-source when local reference access is needed."
            )
        home = _user_home()
        manifest_path = home / MANIFEST_PATH
        managed: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        if manifest_path.exists():
            manifest, _migrated = _read_manifest(manifest_path)
            errors = _validate_user_installation(home)
            if errors:
                raise SkillManagementError("; ".join(errors))
            for package_path, package in manifest["packages"].items():
                for name, record in package["skills"].items():
                    managed.setdefault(name.casefold(), []).append((package_path, record))
        else:
            print("No User Scope DevConcord Skill manifest is installed.")

        target = getattr(args, "target", None)
        if target is None:
            print(f"User Scope Skills validated: {len(managed)}")
            return 0
        project = target.expanduser().resolve()
        if not project.is_dir():
            raise SkillManagementError(f"project directory does not exist: {project}")
        found = False
        for relative in DISCOVERY_PATHS:
            root = project / relative
            if not root.exists():
                continue
            if root.is_symlink() or not root.is_dir():
                raise SkillManagementError(f"project Skill discovery path is unsafe: {relative}")
            for local in sorted(root.iterdir()):
                key = local.name.casefold()
                if key not in managed:
                    continue
                found = True
                global_records = ", ".join(
                    f"{package_path} @ {record['source_commit']}"
                    for package_path, record in managed[key]
                )
                print(
                    f"WARNING: same-name User/Project Skill: {local.name} "
                    f"(global {global_records}; project {relative}/{local.name})"
                )
                print(
                    "  Host-specific selection and precedence are not normalized by "
                    "DevConcord; compare both definitions before relying on either."
                )
        if not found:
            print("No same-name User Scope and Project Scope Skills found.")
        return 0
    except (SkillManagementError, OSError, ValueError, UnicodeError) as error:
        print(f"ERROR: Skill environment diagnosis stopped safely: {error}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate Skill source directories")
    validate.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    validate.add_argument("--scope", choices=("user", "project"))
    validate.add_argument(
        "--target",
        type=Path,
        help="Project Scope repository to validate; omit with --scope user",
    )

    for command in ("install", "sync", "rebind-source"):
        action = commands.add_parser(command, help=f"plan and optionally {command} Skills")
        action.add_argument(
            "--scope",
            choices=("user", "project"),
            help="installation scope; defaults to user without --target and project with it",
        )
        action.add_argument(
            "--target",
            type=Path,
            help="Project Scope repository root; must be omitted for User Scope",
        )
        agent_group = action.add_mutually_exclusive_group(required=command == "install")
        agent_group.add_argument(
            "--agent", choices=sorted(AGENT_ROOTS), help="single agent discovery path"
        )
        agent_group.add_argument(
            "--agents",
            nargs="+",
            choices=sorted(AGENT_ROOTS),
            help="agents sharing or discovering the selected Skill package(s); sync/rebind default to all managed agents",
        )
        action.add_argument(
            "--source",
            type=Path,
            help="Skill source directory; User Scope defaults to the configured DevConcord repository",
        )
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
    recover.add_argument("--scope", choices=("user", "project"))
    recover.add_argument("--target", type=Path, help="Project Scope repository root")
    recover.add_argument("--apply", action="store_true", help="apply safe transaction recovery")
    recover.add_argument(
        "--force",
        action="store_true",
        help="remove a lock only when its recorded process no longer exists",
    )

    config = commands.add_parser("config", help="inspect or set the per-user DevConcord source")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    config_commands.add_parser("show", help="show the validated local DevConcord source")
    set_source = config_commands.add_parser(
        "set-source", help="register a local DevConcord repository for User Scope"
    )
    set_source.add_argument("--source-root", type=Path, required=True)
    set_source.add_argument(
        "--replace",
        action="store_true",
        help="explicitly replace or repair an existing config without changing the Skill manifest",
    )

    reference = commands.add_parser(
        "reference",
        help="print a local DevConcord document for the installed Skill version",
    )
    reference.add_argument("--skill", required=True, help="installed User Scope Skill name")
    reference.add_argument(
        "--path",
        required=True,
        help="path under docs/, .agents/, historical prompts/, or README.md, AGENTS.md, REVIEWS.md",
    )
    reference.add_argument(
        "--scope",
        choices=("user", "project"),
        help="Skill installation scope; defaults to user without --target and project with it",
    )
    reference.add_argument(
        "--target",
        type=Path,
        help="Project Scope repository containing the Skill manifest",
    )
    reference.add_argument(
        "--revision",
        choices=("installed", "head", "working-tree"),
        default="installed",
        help="which local source version to read (default: installed Skill commit)",
    )
    doctor = commands.add_parser(
        "doctor",
        help="validate User Scope management state and optionally report project name collisions",
    )
    doctor.add_argument(
        "--target",
        type=Path,
        help="project repository to inspect for same-name local Skills",
    )
    return parser


def main() -> int:
    return _run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
