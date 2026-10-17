"""Validation helpers for portable Agent Skills."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

import yaml


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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


def validate_skill_directory(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"
    if not skill_dir.is_dir() or skill_dir.is_symlink():
        return [f"{skill_dir}: skill directory must be a real directory"]
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

    for path in skill_dir.rglob("*"):
        if path.is_symlink():
            errors.append(f"{path}: symlinks are not allowed in portable skill packages")
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
    digest = hashlib.sha256()
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"cannot fingerprint symlinked Skill content: {path}")
        relative = path.relative_to(skill_dir).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update((stat.S_IMODE(path.stat().st_mode)).to_bytes(4, "big"))
        if path.is_dir():
            digest.update(b"D")
        elif path.is_file():
            content = path.read_bytes()
            digest.update(b"F")
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        else:
            raise ValueError(f"unsupported non-regular Skill content: {path}")
    return digest.hexdigest()


def validate_skill_roots(
    skills_roots: list[Path],
    *,
    agent_exposures: dict[str, set[str]] | None = None,
) -> list[str]:
    errors: list[str] = []
    names: dict[str, tuple[Path, Path]] = {}
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
            if name in names:
                previous, previous_root = names[name]
                try:
                    identical = _skill_fingerprint(skill_dir) == _skill_fingerprint(previous)
                except (OSError, ValueError) as error:
                    errors.append(
                        f"{skill_dir}: cannot compare duplicate Skill package "
                        f"({type(error).__name__})"
                    )
                    continue
                if identical:
                    current_agents = (
                        agent_exposures.get(f"{root.parent.name}/{root.name}")
                        if agent_exposures is not None
                        else None
                    )
                    previous_agents = (
                        agent_exposures.get(f"{previous_root.parent.name}/{previous_root.name}")
                        if agent_exposures is not None
                        else None
                    )
                    if (
                        current_agents is not None
                        and previous_agents is not None
                        and current_agents.isdisjoint(previous_agents)
                    ):
                        continue
                    errors.append(
                        f"{skill_dir}: identical Skill copy also discovered at {previous}; "
                        "one agent may discover duplicate copies from multiple paths"
                    )
                else:
                    errors.append(
                        f"{skill_dir}: conflicting same-name Skill also discovered at {previous}"
                    )
            else:
                names[name] = (skill_dir, root)
    return errors


def _manifest_agent_exposures(repository_root: Path) -> tuple[dict[str, set[str]] | None, list[str]]:
    metadata_root = repository_root / ".devconcord"
    manifest_path = metadata_root / "skills-manifest.json"
    if metadata_root.is_symlink():
        return None, [f"{metadata_root}: metadata directory must not be a symlink"]
    if not manifest_path.exists() and not manifest_path.is_symlink():
        return None, []
    if manifest_path.is_symlink() or not manifest_path.is_file():
        return None, [f"{manifest_path}: must be a regular manifest file"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [f"{manifest_path}: cannot read agent exposure metadata ({type(error).__name__})"]
    if not isinstance(manifest, dict):
        return None, [f"{manifest_path}: invalid agent exposure metadata"]
    exposures: dict[str, set[str]] = {}
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
                return None, [f"{manifest_path}: invalid package exposure metadata"]
            exposures[path] = set(package["agents"])
        return exposures, []
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
                return None, [f"{manifest_path}: invalid legacy exposure metadata"]
            exposures[path] = {installation["agent"]}
        return exposures, []
    return None, [f"{manifest_path}: unknown exposure manifest format"]


def validate_repository_skills(repository_root: Path) -> list[str]:
    roots = [repository_root / relative for relative in DISCOVERY_PATHS]
    exposures, exposure_errors = _manifest_agent_exposures(repository_root)
    errors = [*exposure_errors, *validate_skill_roots(roots, agent_exposures=exposures)]
    canonical_root = repository_root / DISCOVERY_PATHS[0]
    if not canonical_root.exists():
        errors.append(f"{canonical_root}: canonical Agent Skills source directory is missing")
    else:
        try:
            if not skill_directories(canonical_root):
                errors.append(f"{canonical_root}: canonical Agent Skills source is empty")
        except ValueError:
            pass
    return errors
