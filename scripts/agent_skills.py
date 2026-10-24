"""Validation helpers for portable Agent Skills."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

import yaml


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEVCONCORD_SKILL_PREFIX = "devconcord-"
ALLOWED_FRONTMATTER = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
}
DISCOVERY_PATHS = (".agents/skills", ".claude/skills", ".github/skills")


def _frontmatter(skill_file: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        content = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return None, f"cannot read SKILL.md ({type(error).__name__})"
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        return None, "YAML frontmatter must start at the first line"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None, "YAML frontmatter is not closed"
    try:
        value = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        return None, f"invalid YAML frontmatter ({type(error).__name__})"
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        return None, "YAML frontmatter must be a mapping with string keys"
    return value, None


def _validate_skill_entries(skill_dir: Path) -> list[str]:
    """Reject links and special files before any package content is read."""
    errors: list[str] = []
    pending = [skill_dir]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError as error:
            errors.append(
                f"{directory}: cannot inspect Skill package ({type(error).__name__})"
            )
            continue
        for entry in entries:
            path = Path(entry.path)
            try:
                is_junction = _is_junction(path)
                metadata = path.lstat()
            except OSError as error:
                errors.append(
                    f"{path}: cannot inspect Skill package entry ({type(error).__name__})"
                )
                continue
            if stat.S_ISLNK(metadata.st_mode) or is_junction:
                errors.append(f"{path}: links are not allowed in portable Skill packages")
            elif stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif not stat.S_ISREG(metadata.st_mode):
                errors.append(f"{path}: Skill packages accept regular files only")
    return errors


def _is_junction(path: Path) -> bool:
    """Keep junction checks compatible with Python versions before 3.12."""
    return getattr(path, "is_junction", lambda: False)()


def validate_skill_directory(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"
    if not skill_dir.is_dir() or skill_dir.is_symlink() or _is_junction(skill_dir):
        return [f"{skill_dir}: skill directory must be a real directory"]
    if skill_file.is_symlink():
        return [f"{skill_file}: SKILL.md must not be a symlink"]
    entry_errors = _validate_skill_entries(skill_dir)
    if entry_errors:
        return entry_errors
    if not skill_file.is_file():
        return [f"{skill_file}: SKILL.md must be a regular file"]
    if not SKILL_NAME.fullmatch(name) or len(name) > 64:
        errors.append(f"{skill_dir}: invalid skill directory name")
    metadata, problem = _frontmatter(skill_file)
    if problem is not None:
        return [*errors, f"{skill_file}: {problem}"]
    assert metadata is not None
    unknown = set(metadata) - ALLOWED_FRONTMATTER
    if unknown:
        errors.append(
            f"{skill_file}: unsupported/non-portable frontmatter keys: "
            + ", ".join(sorted(unknown))
        )
    frontmatter_name = metadata.get("name")
    if not isinstance(frontmatter_name, str) or frontmatter_name != name:
        errors.append(f"{skill_file}: name must match skill directory {name!r}")
    description = metadata.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        errors.append(f"{skill_file}: description must contain 1-1024 characters")
    if "license" in metadata and (
        not isinstance(metadata["license"], str) or not metadata["license"].strip()
    ):
        errors.append(f"{skill_file}: license must be a non-empty string")
    if "compatibility" in metadata and (
        not isinstance(metadata["compatibility"], str)
        or not 1 <= len(metadata["compatibility"].strip()) <= 500
    ):
        errors.append(f"{skill_file}: compatibility must contain 1-500 characters")
    if "metadata" in metadata and (
        not isinstance(metadata["metadata"], dict)
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in metadata["metadata"].items()
        )
    ):
        errors.append(f"{skill_file}: metadata must be a string-to-string mapping")
    if "allowed-tools" in metadata:
        errors.append(
            f"{skill_file}: agent-specific allowed-tools permissions are not allowed "
            "in shared portable Skills"
        )

    if skill_file.is_file():
        try:
            body = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            body = ""
        if len(body.splitlines()) > 500:
            errors.append(f"{skill_file}: keep SKILL.md under 500 lines; move detail to references")

    if skill_file.is_file():
        try:
            if __package__:
                from . import validate_docs
            else:
                import validate_docs

            previous_root = validate_docs.ROOT
            try:
                validate_docs.ROOT = skill_dir.resolve()
                link_errors = validate_docs.check_links(
                    sorted(skill_dir.rglob("*.md"))
                )
            finally:
                validate_docs.ROOT = previous_root
            errors.extend(link_errors)
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(f"{skill_dir}: cannot validate local skill references ({type(error).__name__})")
    return errors


def skill_directories(skills_root: Path) -> list[Path]:
    if not skills_root.exists():
        return []
    if not skills_root.is_dir() or skills_root.is_symlink():
        raise ValueError(f"skills root must be a real directory: {skills_root}")
    entries = sorted(skills_root.iterdir())
    symlinks = [path for path in entries if path.is_symlink()]
    if symlinks:
        raise ValueError(
            "skill roots must not contain symlinked packages: "
            + ", ".join(str(path) for path in symlinks)
        )
    return [path for path in entries if path.is_dir()]


def _skill_fingerprint(skill_dir: Path) -> str:
    """Hash exact installed filesystem state, including empty dirs and modes."""
    digest = hashlib.sha256()
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"cannot fingerprint symlinked Skill content: {path}")
        relative = path.relative_to(skill_dir).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        if not path.is_dir() and not path.is_file():
            raise ValueError(f"unsupported non-regular Skill content: {path}")
        digest.update(b"D" if path.is_dir() else b"F")
        digest.update(stat.S_IMODE(path.stat().st_mode).to_bytes(4, "big"))
        if path.is_file():
            content = path.read_bytes()
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
    return digest.hexdigest()


def _mode_is_reliable(root: Path) -> bool:
    if os.name == "nt":
        return False
    try:
        repository = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if repository.returncode:
            return True
        configured = subprocess.run(
            ["git", "-C", str(root), "config", "--bool", "--get", "core.filemode"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return True
    return configured.returncode != 0 or configured.stdout.strip() == "true"


def _filesystem_executable_files(skill_dir: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file() and path.stat().st_mode & 0o111
        )
    )


def _portable_skill_fingerprint(
    skill_dir: Path,
    executable_files: tuple[str, ...],
) -> str:
    """Compare portable package contents with explicit executable metadata."""
    executable_set = set(executable_files)
    digest = hashlib.sha256()
    regular_files: set[str] = set()
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"cannot fingerprint symlinked Skill content: {path}")
        relative_path = path.relative_to(skill_dir).as_posix()
        relative = relative_path.encode("utf-8")
        if not path.is_dir() and not path.is_file():
            raise ValueError(f"unsupported non-regular Skill content: {path}")
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
        raise ValueError(
            "executable-file metadata references missing package paths: "
            + ", ".join(sorted(missing))
        )
    return digest.hexdigest()


def validate_skill_roots(
    skills_roots: list[Path],
    *,
    agent_exposures: dict[str, set[str]] | None = None,
    duplicate_allowances: set[tuple[str, tuple[str, str]]] | None = None,
) -> list[str]:
    errors: list[str] = []
    names: dict[str, list[tuple[Path, Path]]] = {}
    for root in skills_roots:
        if not root.exists():
            continue
        try:
            skills = skill_directories(root)
        except ValueError as error:
            errors.append(str(error))
            continue
        for skill_dir in skills:
            errors.extend(validate_skill_directory(skill_dir))
            name = skill_dir.name.casefold()
            previous_locations = names.get(name, [])
            if previous_locations:
                for previous, previous_root in previous_locations:
                    try:
                        current_exec = (
                            _filesystem_executable_files(skill_dir)
                            if _mode_is_reliable(root)
                            else ()
                        )
                        previous_exec = (
                            _filesystem_executable_files(previous)
                            if _mode_is_reliable(previous_root)
                            else ()
                        )
                        identical = _portable_skill_fingerprint(
                            skill_dir, current_exec
                        ) == _portable_skill_fingerprint(previous, previous_exec)
                    except (OSError, ValueError) as error:
                        errors.append(
                            f"{skill_dir}: cannot compare duplicate Skill package "
                            f"({type(error).__name__})"
                        )
                        continue
                    current_root_key = f"{root.parent.name}/{root.name}"
                    previous_root_key = f"{previous_root.parent.name}/{previous_root.name}"
                    current_agents = (
                        agent_exposures.get(current_root_key)
                        if agent_exposures is not None
                        else None
                    )
                    previous_agents = (
                        agent_exposures.get(previous_root_key)
                        if agent_exposures is not None
                        else None
                    )
                    disjoint_exposure = (
                        current_agents is not None
                        and previous_agents is not None
                        and current_agents.isdisjoint(previous_agents)
                    )
                    allowance = (
                        name,
                        tuple(sorted((current_root_key, previous_root_key))),
                    )
                    if identical and (
                        disjoint_exposure
                        or (
                            duplicate_allowances is not None
                            and allowance in duplicate_allowances
                        )
                    ):
                        continue
                    if identical:
                        errors.append(
                            f"{skill_dir}: identical Skill copy also discovered at {previous}; "
                            "one agent may discover duplicate copies from multiple paths"
                        )
                    else:
                        errors.append(
                            f"{skill_dir}: conflicting same-name Skill also discovered at {previous}"
                        )
            names.setdefault(name, []).append((skill_dir, root))
    return errors


def _manifest_agent_exposures(
    repository_root: Path,
) -> tuple[
    dict[str, set[str]] | None,
    set[tuple[str, tuple[str, str]]],
    list[str],
]:
    metadata_root = repository_root / ".devconcord"
    manifest_path = metadata_root / "skills-manifest.json"
    if metadata_root.is_symlink():
        return None, set(), [f"{metadata_root}: metadata directory must not be a symlink"]
    if not manifest_path.exists() and not manifest_path.is_symlink():
        return None, set(), []
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return None, set(), [f"{manifest_path}: must be a regular manifest file"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, set(), [
            f"{manifest_path}: cannot read agent exposure metadata ({type(error).__name__})"
        ]
    if not isinstance(manifest, dict):
        return None, set(), [f"{manifest_path}: invalid agent exposure metadata"]
    exposures: dict[str, set[str]] = {}
    allowances: set[tuple[str, tuple[str, str]]] = set()
    schema = manifest.get("schema_version")
    if type(schema) is int and schema == 2 and isinstance(manifest.get("packages"), dict):
        for path, package in manifest["packages"].items():
            valid_agents = (
                {"codex", "copilot"}
                if path == ".agents/skills"
                else {"claude", "copilot"}
            )
            if (
                path not in {".agents/skills", ".claude/skills"}
                or not isinstance(package, dict)
                or not isinstance(package.get("agents"), list)
                or not package["agents"]
                or any(not isinstance(agent, str) for agent in package["agents"])
                or len(package["agents"]) != len(set(package["agents"]))
                or not set(package["agents"]) <= valid_agents
            ):
                return None, set(), [f"{manifest_path}: invalid package exposure metadata"]
            exposures[path] = set(package["agents"])
            package_errors = _validate_installed_package(
                repository_root / path,
                package.get("skills"),
                manifest_path,
            )
            if package_errors:
                return None, set(), package_errors
        records = manifest.get("duplicate_discovery_allowances", [])
        if not isinstance(records, list):
            return None, set(), [f"{manifest_path}: invalid duplicate-discovery allowances"]
        for record in records:
            if (
                not isinstance(record, dict)
                or set(record) != {"skill", "paths"}
                or not isinstance(record.get("skill"), str)
                or not SKILL_NAME.fullmatch(record["skill"])
                or not isinstance(record.get("paths"), list)
                or len(record["paths"]) != 2
                or any(not isinstance(path, str) or path not in DISCOVERY_PATHS for path in record["paths"])
                or len(set(record["paths"])) != 2
            ):
                return None, set(), [
                    f"{manifest_path}: invalid duplicate-discovery allowance"
                ]
            allowance = (
                record["skill"].casefold(),
                tuple(sorted(record["paths"])),
            )
            if allowance in allowances:
                return None, set(), [
                    f"{manifest_path}: duplicate duplicate-discovery allowance"
                ]
            allowances.add(allowance)
        return exposures, allowances, []
    if type(schema) is int and schema == 1 and isinstance(manifest.get("installations"), dict):
        for path, installation in manifest["installations"].items():
            if (
                path not in {".agents/skills", ".claude/skills"}
                or not isinstance(installation, dict)
                or not isinstance(installation.get("agent"), str)
                or installation["agent"]
                not in (
                    {"codex", "copilot"}
                    if path == ".agents/skills"
                    else {"claude", "copilot"}
                )
            ):
                return None, set(), [f"{manifest_path}: invalid legacy exposure metadata"]
            exposures[path] = {installation["agent"]}
            package_errors = _validate_installed_package(
                repository_root / path,
                installation.get("skills"),
                manifest_path,
            )
            if package_errors:
                return None, set(), package_errors
        return exposures, set(), []
    return None, set(), [f"{manifest_path}: unknown exposure manifest format"]


def _validate_installed_package(
    skills_root: Path,
    records: Any,
    manifest_path: Path,
) -> list[str]:
    if not isinstance(records, dict):
        return [f"{manifest_path}: package Skill records must be a mapping"]
    errors: list[str] = []
    try:
        actual_skills = {path.name: path for path in skill_directories(skills_root)}
        if skills_root.exists():
            unexpected_entries = [
                path for path in skills_root.iterdir() if not path.is_dir()
            ]
            errors.extend(
                f"{path}: unexpected non-Skill entry in managed package"
                for path in unexpected_entries
            )
    except (OSError, ValueError) as error:
        return [f"{skills_root}: cannot inspect managed Skills ({type(error).__name__})"]
    for name, record in records.items():
        if (
            not isinstance(name, str)
            or not SKILL_NAME.fullmatch(name)
            or not isinstance(record, dict)
            or not isinstance(record.get("source_tree_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["source_tree_sha256"])
            or not isinstance(record.get("installed_tree_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["installed_tree_sha256"])
            or not isinstance(record.get("source_repository"), str)
            or not record["source_repository"]
            or not isinstance(record.get("source_commit"), str)
            or not (
                record["source_commit"] == "unversioned"
                or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", record["source_commit"])
            )
            or not isinstance(record.get("source_dirty"), bool)
        ):
            errors.append(f"{manifest_path}: invalid provenance record for Skill {name!r}")
            continue
        hash_version = record.get("hash_version", 1)
        executable_files = record.get("source_executable_files")
        if type(hash_version) is int and hash_version == 2:
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
                errors.append(
                    f"{manifest_path}: invalid executable-file metadata for Skill {name!r}"
                )
                continue
        elif type(hash_version) is not int or hash_version != 1 or executable_files is not None:
            errors.append(f"{manifest_path}: unsupported hash version for Skill {name!r}")
            continue
        skill_dir = actual_skills.get(name)
        if skill_dir is None:
            errors.append(f"{skills_root / name}: manifest records a missing Skill")
            continue
        try:
            if hash_version == 2:
                expected_executable_files = tuple(executable_files)
                if (
                    _mode_is_reliable(skills_root)
                    and _filesystem_executable_files(skill_dir)
                    != expected_executable_files
                ):
                    errors.append(
                        f"{skill_dir}: executable bits differ from manifest"
                    )
                    continue
                digest = _portable_skill_fingerprint(
                    skill_dir,
                    expected_executable_files,
                )
            else:
                digest = _skill_fingerprint(skill_dir)
        except (OSError, ValueError) as error:
            errors.append(
                f"{skill_dir}: cannot verify installed Skill hash ({type(error).__name__})"
            )
            continue
        if digest != record["installed_tree_sha256"]:
            errors.append(f"{skill_dir}: installed Skill differs from manifest hash")
    for name in sorted(set(actual_skills) - set(records)):
        errors.append(f"{actual_skills[name]}: installed Skill is not recorded in manifest")
    return errors


def validate_repository_skills(
    repository_root: Path,
    *,
    require_canonical_source: bool = True,
) -> list[str]:
    roots = [repository_root / relative for relative in DISCOVERY_PATHS]
    exposures, allowances, exposure_errors = _manifest_agent_exposures(repository_root)
    errors = [
        *exposure_errors,
        *validate_skill_roots(
            roots,
            agent_exposures=exposures,
            duplicate_allowances=allowances,
        ),
    ]
    canonical_root = repository_root / DISCOVERY_PATHS[0]
    if require_canonical_source and not canonical_root.exists():
        errors.append(f"{canonical_root}: canonical Agent Skills source directory is missing")
    elif require_canonical_source:
        try:
            if not skill_directories(canonical_root):
                errors.append(f"{canonical_root}: canonical Agent Skills source is empty")
        except ValueError:
            pass
    return errors


def validate_official_skill_names(skills_root: Path) -> list[str]:
    """Require the namespace only for DevConcord's official source set."""
    try:
        skills = skill_directories(skills_root)
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    for skill_dir in skills:
        if not skill_dir.name.startswith(DEVCONCORD_SKILL_PREFIX):
            errors.append(
                f"{skill_dir}: official DevConcord Skill names must start with "
                f"{DEVCONCORD_SKILL_PREFIX!r}"
            )
        elif skill_dir.name.startswith(DEVCONCORD_SKILL_PREFIX * 2):
            errors.append(
                f"{skill_dir}: official DevConcord Skill names must not repeat "
                "the namespace prefix"
            )
    return errors
