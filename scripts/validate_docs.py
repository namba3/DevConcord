#!/usr/bin/env python3
"""Validate local docs, conventions, and likely privacy leaks in Markdown."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
ISSUE_RULES = ROOT / "docs/work-management/issue-tracking.md"
ISSUE_TEMPLATE = ROOT / "docs/work-management/templates/issue-register.md"
ISSUE_MAIN_TEMPLATE = ROOT / "docs/work-management/templates/issue-register-main.md"
ISSUE_SUBREGISTER_TEMPLATE = (
    ROOT / "docs/work-management/templates/issue-register-subregister.md"
)
FEDERATED_ISSUE_FIXTURE = (
    ROOT / "tests/integration/fixtures/federated-issue-registers/docs/ISSUES.md"
)
ADR_GUIDE = ROOT / "docs/common/ai-assisted-development.md"
ADR_TEMPLATE = ROOT / "docs/application-design/templates/adr.md"
REQUIREMENTS_TEMPLATE = ROOT / "docs/application-design/templates/requirements.md"
RISK_GUIDE = ROOT / "docs/work-management/risk-management.md"
EVALUATION_AXES = [
    ("機能完成度", 20),
    ("設計・アーキテクチャ", 10),
    ("コード品質・保守性", 10),
    ("信頼性・堅牢性", 15),
    ("テスト品質・検証", 15),
    ("セキュリティ", 10),
    ("パフォーマンス・効率性", 5),
    ("UI/UX", 5),
    ("ドキュメント整備", 5),
    ("ビルド・配布・リリース準備度", 5),
]
SDS_AXES = [
    ("ドメイン表現力", 25),
    ("意図の明確性", 25),
    ("契約の明示性", 20),
    ("構造の自己説明性", 15),
    ("振る舞いの説明性", 15),
]
ISSUE_STATUSES = ["未着手", "進行中", "レビュー待ち", "ブロック", "完了", "見送り"]
ADR_STATUSES = ["提案", "承認", "却下", "置換", "廃止"]
RISK_STATUSES = ["特定", "軽減中", "受容", "顕在化", "解消"]
REQUIREMENT_STATUSES = ["未着手", "実装中", "実装済み", "検証済み", "廃止"]
IGNORED_MARKDOWN_DIRS = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "env",
    "htmlcov",
    "node_modules",
    "venv",
}
UNIX_HOME_PATH = re.compile(r"(?<![\w])/(?:home|Users)/([^/\s<>]+)", flags=re.IGNORECASE)
WINDOWS_USER_PATH = re.compile(r"\b[A-Z]:\\Users\\([^\\\s<>]+)", flags=re.IGNORECASE)
EMAIL_ADDRESS = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", flags=re.IGNORECASE
)
SECRET_ASSIGNMENT = re.compile(
    r"(?:[\"']?(?:api[_-]?key|access[_-]?token|token|password|passwd|secret|client[_-]?secret|authorization)[\"']?)"
    r"\s*[:=]\s*[\"']?([^\s\"'`,;}]+)",
    flags=re.IGNORECASE,
)
KNOWN_SECRET_MARKER = re.compile(
    r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|"
    r"AKIA[0-9A-Z]{16}|sk_live_[A-Za-z0-9]{16,})\b"
)
PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
URL_CREDENTIAL = re.compile(r"\b(?:https?|ftp)://[^/\s:@]+:[^@\s/]+@", flags=re.IGNORECASE)
GENERIC_USER_NAMES = {
    "user", "username", "specific-user", "your-user", "yourname", "example",
    "developer", "test", "name", "placeholder", "user-name",
}
SAFE_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "localhost"}
SAFE_SECRET_VALUES = {
    "placeholder", "redacted", "changeme", "change_me", "example", "dummy",
    "your_secret", "your_token", "your_password", "none", "null", "false",
}


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Documentation checks passed.")
    return 0


def _relative_to_root(path: Path, root: Path) -> Path | None:
    try:
        absolute_path = os.path.abspath(path)
        absolute_root = os.path.abspath(root)
        common = os.path.commonpath((absolute_path, absolute_root))
    except ValueError:
        return None
    if os.path.normcase(common) != os.path.normcase(absolute_root):
        return None
    return Path(os.path.relpath(absolute_path, absolute_root))


def relative_path(path: Path) -> str:
    relative = _relative_to_root(path, ROOT)
    return relative.as_posix() if relative is not None else str(path)


def read_utf8(path: Path, purpose: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(
            f"{relative_path(path)}: cannot read {purpose} ({type(error).__name__})"
        )
        return None


def markdown_files(errors: list[str] | None = None) -> list[Path]:
    """Find regular Markdown files without entering generated/dependency trees."""
    found: list[Path] = []
    scan_errors = errors if errors is not None else []

    def on_walk_error(error: OSError) -> None:
        location = Path(error.filename) if error.filename else ROOT
        scan_errors.append(
            f"{relative_path(location)}: cannot scan Markdown directory ({type(error).__name__})"
        )

    for directory, directory_names, filenames in os.walk(
        ROOT, topdown=True, followlinks=False, onerror=on_walk_error
    ):
        parent = Path(directory)
        retained: list[str] = []
        for name in sorted(directory_names, key=lambda item: (item.casefold(), item)):
            child = parent / name
            ignored_egg_info = name.casefold().endswith(".egg-info")
            root_build_output = parent == ROOT and name.casefold() in {"build", "dist"}
            if (
                name.casefold() in IGNORED_MARKDOWN_DIRS
                or ignored_egg_info
                or root_build_output
            ):
                continue
            try:
                is_directory_link = child.is_symlink() or getattr(
                    child, "is_junction", lambda: False
                )()
            except OSError as error:
                scan_errors.append(
                    f"{relative_path(child)}: cannot inspect Markdown directory ({type(error).__name__})"
                )
                continue
            if is_directory_link:
                scan_errors.append(
                    f"{relative_path(child)}: Markdown discovery does not follow directory links"
                )
                continue
            retained.append(name)
        directory_names[:] = retained

        for name in sorted(filenames, key=lambda item: (item.casefold(), item)):
            path = parent / name
            if path.suffix.casefold() not in {".md", ".markdown"}:
                continue
            try:
                metadata = path.lstat()
            except OSError as error:
                scan_errors.append(
                    f"{relative_path(path)}: cannot inspect Markdown file ({type(error).__name__})"
                )
                continue
            if not stat.S_ISREG(metadata.st_mode):
                scan_errors.append(
                    f"{relative_path(path)}: Markdown discovery accepts regular files only"
                )
                continue
            found.append(path)

    return sorted(
        found,
        key=lambda path: (relative_path(path).casefold(), relative_path(path)),
    )


def slugify_heading(heading: str) -> str:
    heading = re.sub(r"`([^`]*)`", r"\1", heading)
    heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s-]+", "-", heading)


def heading_anchors(text: str) -> set[str]:
    tokens = MarkdownIt("commonmark").parse(text)
    html_anchors = HTMLAnchorParser()
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and index + 1 < len(tokens):
            slug = slugify_heading(tokens[index + 1].content)
            occurrence = counts.get(slug, 0)
            counts[slug] = occurrence + 1
            anchors.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
        if token.type == "html_block":
            html_anchors.feed(token.content)
        elif token.type == "inline" and token.children:
            for child in token.children:
                if child.type == "html_inline":
                    html_anchors.feed(child.content)
    anchors.update(html_anchors.anchors)
    return anchors


def markdown_link_destinations(text: str) -> tuple[list[str], list[str]]:
    """Extract CommonMark link targets and raw HTML links without scanning code."""
    class LinkAttributeParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.destinations: list[str] = []

        def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self.destinations.extend(
                value for name, value in attrs
                if name.lower() in {"href", "src"} and value is not None
            )

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self.handle_starttag(tag, attrs)

    destinations: list[str] = []
    unresolved: list[str] = []
    parser = MarkdownIt("commonmark")
    for token in parser.parse(text):
        if token.type == "inline" and token.children:
            for child in token.children:
                if child.type == "link_open" and child.attrs:
                    target = child.attrs.get("href")
                    if target is not None:
                        destinations.append(target)
                elif child.type == "image" and child.attrs:
                    target = child.attrs.get("src")
                    if target is not None:
                        destinations.append(target)
                elif child.type == "text":
                    unresolved.extend(
                        match.group(2) or match.group(1)
                        for match in re.finditer(
                            r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]", child.content
                        )
                    )
                if child.type == "html_inline" and child.content:
                    html_links = LinkAttributeParser()
                    html_links.feed(child.content)
                    destinations.extend(html_links.destinations)
        elif token.type == "html_block" and token.content:
            html_links = LinkAttributeParser()
            html_links.feed(token.content)
            destinations.extend(html_links.destinations)
    return destinations, unresolved


class HTMLAnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is not None and (
                name.lower() == "id" or (tag.lower() == "a" and name.lower() == "name")
            ):
                self.anchors.add(value)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def anchors_for_target(path: Path, text: str) -> set[str]:
    extension = path.suffix.casefold()
    if extension in {".html", ".htm"}:
        anchors = HTMLAnchorParser()
        anchors.feed(text)
        return anchors.anchors
    if extension in {".md", ".markdown"}:
        return heading_anchors(text)
    return set()


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    cache: dict[Path, tuple[str, set[str]]] = {}
    repository_root = ROOT.resolve()

    for source in files:
        source_label = relative_path(source)
        source_text = read_utf8(source, "Markdown links", errors)
        if source_text is None:
            continue
        destinations, unresolved = markdown_link_destinations(source_text)
        for label in unresolved:
            errors.append(f"{source_label}: undefined link reference {label!r}")
        for destination in destinations:
            try:
                parsed = urlsplit(destination)
            except ValueError:
                errors.append(
                    f"{source_label}: invalid link destination {destination!r}"
                )
                continue
            if parsed.scheme or parsed.netloc:
                continue

            link_path = unquote(parsed.path)
            try:
                target = (
                    (source.parent / link_path).resolve()
                    if link_path
                    else source.resolve()
                )
            except (OSError, RuntimeError) as error:
                errors.append(
                    f"{source_label}: cannot resolve link target "
                    f"{destination!r} ({type(error).__name__})"
                )
                continue
            target_relative = _relative_to_root(target, repository_root)
            if target_relative is None:
                errors.append(f"{source_label}: link escapes repository {destination}")
                continue
            if not target.exists():
                errors.append(f"{source_label}: missing link target {destination}")
                continue
            if not parsed.fragment:
                continue

            if target.is_file() and target.suffix.casefold() in {
                ".md", ".markdown", ".html", ".htm"
            } and target not in cache:
                text = read_utf8(target, f"fragment in {destination!r}", errors)
                if text is not None:
                    cache[target] = (text, anchors_for_target(target, text))
            if target in cache and unquote(parsed.fragment) not in cache[target][1]:
                errors.append(
                    f"{source_label}: missing anchor {parsed.fragment!r} in "
                    f"{target_relative.as_posix()}"
                )
    return errors


@dataclass(frozen=True)
class IssueRecord:
    issue_id: str
    path: Path
    line: int
    tags: tuple[str, ...]


ID_HEADERS = {"id", "issueid", "課題id", "課題番号", "課題id番号"}
TAG_HEADERS = {"tag", "tags", "タグ", "課題タグ"}
COUNTER_HEADINGS = {"共通iss採番", "globalissueallocation", "commonissueallocation"}
COUNTER_VALUE = re.compile(r"^(?:`(ISS-[0-9]+)`(?:（[^）]*）)?|(ISS-[0-9]+))$")
ISSUE_ID = re.compile(r"^ISS-([0-9]+)$")


def _stable_read_utf8(path: Path, label: str) -> tuple[str | None, str | None]:
    """Read one UTF-8 file and reject detectable concurrent replacement/modification."""
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            raw = stream.read()
            after = os.fstat(stream.fileno())
        current = path.stat()
        signature = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
        if signature(before) != signature(after) or signature(after) != signature(current):
            return None, f"{path}: changed while validating {label}"
        return raw.decode("utf-8"), None
    except (OSError, UnicodeError) as error:
        return None, f"{path}: cannot read {label}: {error}"


def _markdown_cells(line: str) -> list[str] | None:
    value = line.strip()
    if not value.startswith("|"):
        return None
    cells: list[str] = []
    cell: list[str] = []
    escaped = False
    code_ticks = 0
    for char in value[1:]:
        if escaped:
            cell.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
            cell.append(char)
        elif char == "`":
            code_ticks = 0 if code_ticks else 1
            cell.append(char)
        elif char == "|" and not code_ticks:
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(char)
    if cell or value.endswith("|"):
        cells.append("".join(cell).strip())
    if cells and cells[-1] == "":
        cells.pop()
    return cells


def _header_key(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\([^)]*\)|（[^）]*）", "", value)
    return re.sub(r"[\s_`*:-]+", "", value).casefold()


def _canonical_id(issue_id: str) -> tuple[int | None, bool]:
    match = ISSUE_ID.fullmatch(issue_id)
    if not match:
        return None, False
    number = int(match.group(1))
    return number, number > 0 and issue_id == f"ISS-{number:04d}"


def _issue_record_rows(text: str, path: Path | None = None, errors: list[str] | None = None) -> list[IssueRecord]:
    """Read records only from Markdown tables whose header identifies an ID column."""
    source = path or Path("<main index>")
    lines = text.splitlines()
    records: list[IssueRecord] = []
    fenced = False
    fence_char = ""
    fence_len = 0
    for index, line in enumerate(lines):
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if not fenced:
                fenced, fence_char, fence_len = True, marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                fenced = False
            continue
        if fenced or index + 1 >= len(lines):
            continue
        headers = _markdown_cells(line)
        separators = _markdown_cells(lines[index + 1])
        if headers is None:
            continue
        if separators is None or len(headers) != len(separators):
            if errors is not None and any(_header_key(header) in ID_HEADERS for header in headers):
                errors.append(f"{source}:{index + 1}: malformed issue table header or separator")
            continue
        if not all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in separators):
            if errors is not None and any(_header_key(header) in ID_HEADERS for header in headers):
                errors.append(f"{source}:{index + 1}: malformed issue table separator")
            continue
        keys = [_header_key(header) for header in headers]
        id_columns = [i for i, key in enumerate(keys) if key in ID_HEADERS]
        tag_columns = [i for i, key in enumerate(keys) if key in TAG_HEADERS]
        if len(id_columns) > 1 or len(tag_columns) > 1:
            if errors is not None:
                errors.append(f"{source}:{index + 1}: ambiguous issue table header (duplicate ID or tag columns)")
            continue
        if not id_columns:
            continue
        id_column = id_columns[0]
        tag_column = tag_columns[0] if tag_columns else None
        row_index = index + 2
        while row_index < len(lines):
            cells = _markdown_cells(lines[row_index])
            if cells is None:
                break
            if len(cells) != len(headers):
                if errors is not None and any(cell.strip(" `").casefold().startswith("iss-") for cell in cells):
                    errors.append(f"{source}:{row_index + 1}: issue table row has {len(cells)} cells; expected {len(headers)}")
                row_index += 1
                continue
            issue_id = cells[id_column].strip(" `")
            if issue_id.casefold().startswith("iss-") and not ISSUE_ID.fullmatch(issue_id):
                if errors is not None:
                    errors.append(f"{source}:{row_index + 1}: malformed issue ID {issue_id}")
            if ISSUE_ID.fullmatch(issue_id):
                if any(marker in cell for cell in cells for marker in ("具体的な問題と影響", "検証可能な条件", "YYYY-MM-DD")):
                    row_index += 1
                    continue
                raw_tags = []
                if tag_column is not None:
                    raw_tags = [tag.strip().strip("`") for tag in cells[tag_column].split(",") if tag.strip() and tag.strip() not in {"—", "-"}]
                records.append(IssueRecord(issue_id, source, row_index + 1, tuple(raw_tags)))
            row_index += 1
        continue
    return records


def _issue_counter_values(text: str) -> tuple[list[str], list[str]]:
    """Return valid and malformed counter declarations inside named allocation sections."""
    active = False
    fenced = False
    fence_char = ""
    fence_len = 0
    values: list[str] = []
    malformed: list[str] = []
    for line in text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if not fenced:
                fenced, fence_char, fence_len = True, marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                fenced = False
            continue
        if fenced:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            active = _header_key(heading.group(1)) in COUNTER_HEADINGS
            continue
        if not active:
            continue
        candidate = re.sub(r"^\s*[-*+]\s*", "", line).strip()
        candidate = candidate.replace("**", "").replace("__", "").strip()
        label = re.match(r"^(?:次の未割当番号|next\s+unused\s+(?:issue\s+)?id)\s*[:：]\s*(.*?)\s*$", candidate, re.I)
        if label:
            value = label.group(1).strip()
            match = COUNTER_VALUE.fullmatch(value)
            if match:
                values.append(match.group(1) or match.group(2))
            else:
                malformed.append(value or "<empty>")
    return values, malformed


def _validate_records(records: list[IssueRecord], errors: list[str]) -> dict[int, list[IssueRecord]]:
    by_number: dict[int, list[IssueRecord]] = {}
    for record in records:
        number, canonical = _canonical_id(record.issue_id)
        if number is None:
            continue
        by_number.setdefault(number, []).append(record)
        if not canonical:
            errors.append(f"{record.path}:{record.line}: non-canonical issue ID {record.issue_id}; use ISS-{number:04d}")
        normalized = [tag.upper() for tag in record.tags]
        if len(normalized) != len(set(normalized)):
            errors.append(f"{record.path}:{record.line}: {record.issue_id} contains duplicate tags after case normalization")
    for number, found in by_number.items():
        if len(found) > 1:
            locations = ", ".join(f"{record.path}:{record.line} ({record.issue_id})" for record in found)
            display_id = found[0].issue_id
            errors.append(f"duplicate issue ID {display_id} (numeric value {number}): {locations}")
    return by_number


def _defined_issue_tags(text: str) -> set[str]:
    lines = text.splitlines()
    tags: set[str] = set()
    in_tag_section = False
    fenced = False
    for index, line in enumerate(lines):
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            in_tag_section = "tag" in _header_key(heading.group(1)) or "タグ" in heading.group(1)
            continue
        if not in_tag_section or index + 1 >= len(lines):
            continue
        headers = _markdown_cells(line)
        separators = _markdown_cells(lines[index + 1])
        if not headers or not separators or len(headers) != len(separators):
            continue
        keys = [_header_key(item) for item in headers]
        if not keys or keys[0] not in TAG_HEADERS or not all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in separators):
            continue
        for row in lines[index + 2:]:
            cells = _markdown_cells(row)
            if cells is None:
                break
            if cells and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", cells[0]):
                tags.add(cells[0].upper())
    return tags


def _validate_counter(text: str, path: Path, records: list[IssueRecord], errors: list[str]) -> None:
    counters, malformed = _issue_counter_values(text)
    if malformed:
        errors.append(f"{path}: invalid next unused ISS counter: {', '.join(malformed)}")
    if not counters:
        if not malformed:
            errors.append(f"{path}: missing a next unused ISS counter in the allocation section")
        return
    if len(counters) != 1 or malformed:
        errors.append(f"{path}: expected exactly one valid next unused ISS counter; found {len(counters)}")
        return
    number, canonical = _canonical_id(counters[0])
    if not canonical:
        errors.append(f"{path}: non-canonical next unused issue ID {counters[0]}; use ISS-{number:04d}")
    record_numbers = [_canonical_id(record.issue_id)[0] for record in records]
    existing = [value for value in record_numbers if value is not None]
    if existing and number <= max(existing):
        errors.append(f"{path}: next ISS counter must exceed every recorded issue ID")


def validate_federated_issue_register(main_index: Path, managed_dir: Path) -> list[str]:
    """Validate an explicitly scoped read-only federated issue register."""
    errors: list[str] = []
    main_text, read_error = _stable_read_utf8(main_index, "federated issue index")
    if read_error:
        return [read_error]
    assert main_text is not None
    try:
        resolved_managed = managed_dir.resolve(strict=True)
        if not resolved_managed.is_dir():
            return [f"{main_index}: invalid federated issue scope"]
    except (OSError, RuntimeError) as error:
        return [f"{main_index}: cannot resolve federated issue scope: {error}"]

    main_records = _issue_record_rows(main_text, main_index, errors)
    records: list[IssueRecord] = []
    indexed: list[Path] = []
    indexed_text: dict[Path, str] = {}
    in_subregister_section = False
    fenced = False
    for line in main_text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r"^##\s+", line):
            in_subregister_section = bool(
                re.match(r"^##\s+(?:Subregisters|サブ課題表)\b", line, re.IGNORECASE)
            )
        if not in_subregister_section:
            continue
        for destination in re.findall(r"\[[^\]]+\]\(([^)]+)\)", line):
            parsed = urlsplit(destination)
            path_part = unquote(parsed.path)
            if not path_part or parsed.scheme or parsed.netloc:
                continue
            candidate = main_index.parent / path_part
            try:
                path = candidate.resolve(strict=False)
            except (OSError, RuntimeError):
                errors.append(f"{main_index}: cannot resolve subregister link: {destination}")
                continue
            if not path.is_relative_to(resolved_managed):
                errors.append(f"{main_index}: subregister link escapes managed issue directory: {destination}")
                continue
            if path in indexed:
                errors.append(f"{main_index}: duplicate subregister index link: {destination}")
                continue
            indexed.append(path)
            if not path.is_file():
                errors.append(f"{main_index}: missing subregister target {destination}")
                continue
            register_text, read_error = _stable_read_utf8(path, "indexed issue register")
            if read_error:
                errors.append(read_error)
                continue
            assert register_text is not None
            indexed_text[path] = register_text
            records.extend(_issue_record_rows(register_text, path, errors))

    if main_records:
        errors.append(f"{main_index}: main index contains issue records; keep canonical records in subregisters")
    if not indexed:
        errors.append(f"{main_index}: no subregister links found in the Subregisters section")

    by_number = _validate_records(records, errors)
    _validate_counter(main_text, main_index, records, errors)

    indexed_set = set(indexed)
    if managed_dir.is_dir():
        def report_walk_error(error: OSError) -> None:
            errors.append(f"{main_index}: cannot inspect managed issue directory: {error}")

        for parent, directories, files in os.walk(
            resolved_managed, followlinks=False, onerror=report_walk_error
        ):
            for name in directories + files:
                path = Path(parent) / name
                if path.is_symlink():
                    try:
                        target = path.resolve(strict=False)
                    except (OSError, RuntimeError):
                        errors.append(f"{main_index}: cannot resolve managed symlink: {path}")
                        continue
                    if not target.is_relative_to(resolved_managed):
                        errors.append(f"{main_index}: managed symlink escapes issue directory: {path}")
        for path in sorted(resolved_managed.rglob("*.md")):
            resolved_path = path.resolve()
            if not resolved_path.is_relative_to(resolved_managed):
                errors.append(f"{main_index}: managed issue path escapes managed directory: {path}")
            elif resolved_path not in indexed_set:
                errors.append(f"{main_index}: unindexed issue register in managed directory: {path}")

    in_important_section = False
    fenced = False
    for line in main_text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r"^##\s+", line):
            in_important_section = bool(
                re.match(r"^##\s+(?:Important Issues|重要課題)\b", line, re.IGNORECASE)
            )
        if not in_important_section:
            continue
        for issue_id, destination in re.findall(
            r"\[(ISS-[0-9]+)\]\(([^)]+)\)", line
        ):
            number, canonical = _canonical_id(issue_id)
            if not canonical:
                errors.append(f"{main_index}: non-canonical important issue ID {issue_id}")
            parsed = urlsplit(destination)
            path_part, anchor = unquote(parsed.path), unquote(parsed.fragment)
            target = (main_index.parent / path_part).resolve()
            target_ids = {record_number for record_number, found in by_number.items() if any(record.path.resolve() == target for record in found)}
            if target not in indexed_set or number not in target_ids:
                errors.append(f"{main_index}: important issue link {issue_id} does not resolve to its canonical record")
            else:
                anchor_matches_id = (
                    anchor.casefold() == issue_id.casefold()
                    or anchor.casefold().startswith(issue_id.casefold() + "-")
                )
                if (
                    not anchor_matches_id
                    or not target.is_file()
                    or target not in indexed_text
                    or anchor not in anchors_for_target(target, indexed_text[target])
                ):
                    errors.append(
                        f"{main_index}: important issue link {issue_id} has a mismatched anchor"
                    )

    defined_tags = _defined_issue_tags(main_text)
    if defined_tags:
        for record in records:
            unknown_tags = set(tag.upper() for tag in record.tags) - defined_tags
            if unknown_tags:
                errors.append(f"{record.path}:{record.line}: {record.issue_id} uses undefined tags: {', '.join(sorted(unknown_tags))}")
    return errors


def validate_single_issue_register(register: Path) -> list[str]:
    """Check IDs and the next counter for a concrete, single-register file."""
    text, read_error = _stable_read_utf8(register, "issue register")
    if read_error:
        return [read_error]
    assert text is not None
    errors: list[str] = []
    records = _issue_record_rows(text, register, errors)
    _validate_records(records, errors)
    _validate_counter(text, register, records, errors)
    defined_tags = _defined_issue_tags(text)
    if defined_tags:
        for record in records:
            unknown_tags = set(tag.upper() for tag in record.tags) - defined_tags
            if unknown_tags:
                errors.append(f"{register}:{record.line}: {record.issue_id} uses undefined tags: {', '.join(sorted(unknown_tags))}")
    return errors


def check_privacy_hygiene(files: list[Path]) -> list[str]:
    """Report likely sensitive Markdown values without echoing matched content."""
    errors: list[str] = []

    for path in files:
        text = read_utf8(path, "privacy patterns", errors)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            relative = relative_path(path)
            for pattern in (UNIX_HOME_PATH, WINDOWS_USER_PATH):
                for match in pattern.finditer(line):
                    username = match.group(1).casefold()
                    if username not in GENERIC_USER_NAMES:
                        errors.append(
                            f"{relative}:{line_number}: possible personal home path; review without copying the value"
                        )
            for match in EMAIL_ADDRESS.finditer(line):
                domain = match.group(0).rsplit("@", maxsplit=1)[1].casefold()
                if domain not in SAFE_EMAIL_DOMAINS and not domain.endswith((".example", ".test", ".invalid")):
                    errors.append(
                        f"{relative}:{line_number}: possible personal contact address; review without copying the value"
                    )
            for match in SECRET_ASSIGNMENT.finditer(line):
                value = match.group(1).strip().strip("\"'").casefold()
                placeholder = (
                    value in SAFE_SECRET_VALUES
                    or bool(re.fullmatch(r"<[^>]+>", value))
                    or value.startswith(("your_", "your-", "example_", "example-"))
                )
                if len(value) >= 12 and not placeholder:
                    errors.append(
                        f"{relative}:{line_number}: possible embedded credential; review without copying the value"
                    )
            if KNOWN_SECRET_MARKER.search(line):
                errors.append(
                    f"{relative}:{line_number}: possible credential marker; review without copying the value"
                )
            if PRIVATE_KEY_MARKER.search(line):
                errors.append(
                    f"{relative}:{line_number}: possible private key material; review without copying the value"
                )
            if URL_CREDENTIAL.search(line):
                errors.append(
                    f"{relative}:{line_number}: possible embedded URL credentials; review without copying the value"
                )

    return errors


def evaluation_rows(text: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for line in text.splitlines():
        match = re.match(r"^\|\s*([^|]+?)\s*\|\s*(\d+)%\s*\|", line)
        if match:
            rows.append((match.group(1), int(match.group(2))))
    return rows


def backtick_values(line: str) -> list[str]:
    return re.findall(r"`([^`]+)`", line)


def check_conventions(files: list[Path]) -> list[str]:
    errors: list[str] = []
    canonical_paths = (
        ISSUE_RULES,
        ISSUE_TEMPLATE,
        ADR_GUIDE,
        ADR_TEMPLATE,
        REQUIREMENTS_TEMPLATE,
        RISK_GUIDE,
    )
    canonical = {
        path: read_utf8(path, "canonical conventions", errors)
        for path in canonical_paths
    }
    if any(text is None for text in canonical.values()):
        return errors
    rules = canonical[ISSUE_RULES] or ""
    template = canonical[ISSUE_TEMPLATE] or ""
    guide = canonical[ADR_GUIDE] or ""
    adr_template = canonical[ADR_TEMPLATE] or ""
    requirements_template = canonical[REQUIREMENTS_TEMPLATE] or ""
    risk_guide = canonical[RISK_GUIDE] or ""

    rules_axis_section = rules[rules.find("### 3.1 評価軸と重み") : rules.find("### 3.2")]
    template_axes_start = template.find("| 評価軸 | 重み | 完成度 |")
    template_axes_end = template.find("**総評:**", template_axes_start)
    template_axis_section = template[template_axes_start:template_axes_end]
    for path, text in ((ISSUE_RULES, rules_axis_section), (ISSUE_TEMPLATE, template_axis_section)):
        rows = evaluation_rows(text)
        if rows != EVALUATION_AXES:
            errors.append(
                f"{path.relative_to(ROOT)}: evaluation axes or weights differ from the canonical list"
            )
        if sum(weight for _, weight in rows) != 100:
            errors.append(f"{path.relative_to(ROOT)}: evaluation weights must total 100%")

    sds_rules_start = rules.find("### 3.5 Self-documenting Score（SDS）")
    sds_rules_end = rules.find("## 4. 課題の記録ルール", sds_rules_start)
    sds_rules = rules[sds_rules_start:sds_rules_end]
    sds_template_start = template.find("### Self-documenting Score（SDS）")
    sds_template_end = template.find("| 評価軸 | 重み | 完成度 |", sds_template_start)
    sds_template = template[sds_template_start:sds_template_end]
    for path, text in ((ISSUE_RULES, sds_rules), (ISSUE_TEMPLATE, sds_template)):
        rows = evaluation_rows(text)
        if rows != SDS_AXES:
            errors.append(f"{path.relative_to(ROOT)}: SDS axes or weights differ from the canonical list")
        if sum(weight for _, weight in rows) != 100:
            errors.append(f"{path.relative_to(ROOT)}: SDS weights must total 100%")
    for required in ("正式なSDS", "暫定SDS", "SDS評価済みカバレッジ", "N/A", "未評価", "総合完成度"):
        if required not in sds_rules:
            errors.append(f"issue-tracking.md: SDS rules must define {required}")

    evaluation_heading = template.find("## プロジェクト完成度評価")
    issues_heading = template.find("## 課題一覧")
    if evaluation_heading < 0 or issues_heading < 0 or evaluation_heading > issues_heading:
        errors.append("issue-register.md: completion evaluation must precede the issue list")
    required_issue_header = "| ID | 分類 | タグ（任意） | 作業種別（任意） | 優先度 | 状態 | 課題・影響 | 完了条件 | 根拠・検証 | 更新日 |"
    if required_issue_header not in template:
        errors.append("issue-register.md: required issue columns are missing or out of order")
    for value in ["未確定", "暫定総合完成度", "評価済みカバレッジ", "N/A", "未評価"]:
        if value not in template:
            errors.append(f"issue-register.md: missing completion-evaluation field {value}")

    main_template = (
        read_utf8(ISSUE_MAIN_TEMPLATE, "main issue-register template", errors) or ""
    )
    main_axes_start = main_template.find("| 評価軸 | 重み | 完成度 |")
    main_axes_end = main_template.find("**総評:**", main_axes_start)
    if main_axes_start < 0 or main_axes_end < 0 or evaluation_rows(
        main_template[main_axes_start:main_axes_end]
    ) != EVALUATION_AXES:
        errors.append("issue-register-main.md: completion axes or weights must match the shared ten-axis schema")
    main_sds_start = main_template.find("### Self-documenting Score（SDS）")
    main_sds_end = main_template.find("| 評価軸 | 重み | 完成度 |", main_sds_start)
    if main_sds_start < 0 or main_sds_end < 0 or evaluation_rows(
        main_template[main_sds_start:main_sds_end]
    ) != SDS_AXES:
        errors.append("issue-register-main.md: SDS axes or weights must match the canonical schema")
    for required in ("次の未割当番号", "サブ課題表", "タグ定義", "複製しません"):
        if required not in main_template:
            errors.append(
                f"issue-register-main.md: missing federated-register contract {required}"
            )
    fixture_managed_dir = FEDERATED_ISSUE_FIXTURE.parent / "issues"
    errors.extend(validate_federated_issue_register(FEDERATED_ISSUE_FIXTURE, fixture_managed_dir))
    subregister_template = read_utf8(
        ISSUE_SUBREGISTER_TEMPLATE, "issue subregister template", errors
    ) or ""
    for required in ("唯一の正本", "ISS-####", "タグ（任意）", "作業種別（任意）"):
        if required not in subregister_template:
            errors.append(
                f"issue-register-subregister.md: missing subregister contract {required}"
            )
    if required_issue_header not in subregister_template:
        errors.append("issue-register-subregister.md: issue columns must match the single-register schema")

    status_table_start = rules.find("### 4.4 状態")
    status_table_end = rules.find("### 4.5", status_table_start)
    rule_statuses = [
        match.group(1).strip()
        for match in re.finditer(
            r"^\|\s*([^|]+?)\s*\|[^\n]+\|$",
            rules[status_table_start:status_table_end],
            flags=re.MULTILINE,
        )
        if match.group(1).strip() != "状態"
        and not match.group(1).strip().startswith("-")
    ]
    template_status_line = next(
        (line for line in template.splitlines() if line.startswith("- **状態:**")), ""
    )
    guide_status_line = next(
        (line for line in guide.splitlines() if line.startswith("| Status |")), ""
    )
    status_sets = [rule_statuses, backtick_values(template_status_line), backtick_values(guide_status_line)]
    if any(values != ISSUE_STATUSES for values in status_sets):
        errors.append("issue status values must use the same canonical set in rules, template, and guide")

    priority_section_start = rules.find("### 4.3 優先度")
    priority_section_end = rules.find("### 4.4", priority_section_start)
    rule_priorities = re.findall(
        r"^\|\s*(P[0-3]):",
        rules[priority_section_start:priority_section_end],
        flags=re.MULTILINE,
    )
    template_priority_line = next(
        (line for line in template.splitlines() if line.startswith("- **優先度:**")), ""
    )
    guide_priority_line = next(
        (line for line in guide.splitlines() if line.startswith("| Priority / Risk |")), ""
    )
    priority_sets = [
        rule_priorities,
        backtick_values(template_priority_line),
        backtick_values(guide_priority_line),
    ]
    expected_priorities = ["P0", "P1", "P2", "P3"]
    if any(values != expected_priorities for values in priority_sets):
        errors.append("issue priorities must use P0, P1, P2, P3 in rules, template, and guide")

    adr_status_guide = next(
        (line for line in guide.splitlines() if line.startswith("- ADRの状態は ")), ""
    )
    adr_status_guide = adr_status_guide.split("を一貫", maxsplit=1)[0]
    adr_status_template = next(
        (line for line in adr_template.splitlines() if line.startswith("- **状態:**")), ""
    )
    if (
        backtick_values(adr_status_guide) != ADR_STATUSES
        or backtick_values(adr_status_template) != ADR_STATUSES
    ):
        errors.append("ADR status values must match between template and development guide")

    requirement_status_line = next(
        (line for line in requirements_template.splitlines() if "状態は要求単位で管理" in line), ""
    )
    requirement_status_match = re.search(r"状態は要求単位で管理し、(.*?)を使います", requirement_status_line)
    requirement_statuses = (
        backtick_values(requirement_status_match.group(1))
        if requirement_status_match
        else []
    )
    if requirement_statuses != REQUIREMENT_STATUSES:
        errors.append("requirement lifecycle states must use the canonical ordered set")
    for expected_header in (
        "| ID | 要求 | 優先度 | 状態 | 関連タスクID | 設計書出典・節 | 受け入れ条件 | 検証方法・証跡 | 設計・実装・課題 |",
        "| ID | 品質特性 | 要求・条件 | 状態 | 設計書出典・節 | 受け入れ条件・検証方法・証跡 | 設計・実装・課題 |",
    ):
        if expected_header not in requirements_template:
            errors.append("requirements.md: requirement rows must connect state, acceptance, evidence, and references")
    if "| タスクID |" not in requirements_template or "| 関連要求ID |" not in requirements_template:
        errors.append("requirements.md: user tasks must link to stable requirement IDs")
    if (
        "| 設計書出典・節 |" not in requirements_template
        or "**入力設計書・版/コミット等:**" not in requirements_template
    ):
        errors.append("requirements.md: tasks and requirements must trace to source design documents")

    risk_status_line = next(
        (line for line in risk_guide.splitlines() if line.startswith("状態は `")), ""
    )
    risk_status_match = re.search(r"状態は (.*?) を使う", risk_status_line)
    declared_risk_statuses = (
        backtick_values(risk_status_match.group(1)) if risk_status_match else []
    )
    risk_table_start = risk_guide.find("| 状態 | 意味・更新条件 |")
    risk_table_lines = []
    if risk_table_start >= 0:
        for line in risk_guide[risk_table_start:].splitlines()[2:]:
            if not line.startswith("|"):
                break
            risk_table_lines.append(line)
    table_risk_statuses = [
        line.split("|", maxsplit=2)[1].strip()
        for line in risk_table_lines
        if line.startswith("|") and line.count("|") >= 3
    ]
    if declared_risk_statuses != RISK_STATUSES or table_risk_statuses != RISK_STATUSES:
        errors.append("risk-management.md: risk lifecycle states must use the canonical ordered set")
    for required in ("RISK-####", "発生可能性", "影響度", "根拠・不確実性", "残余リスク"):
        if required not in risk_guide:
            errors.append(f"risk-management.md: missing required risk-management field {required}")

    deprecated_examples = re.compile(r"ISSUE(?:-|_)(?:\d|\.\.\.)|^\s*-\s*(?:Status:\s*Open|Priority:\s*High)", re.MULTILINE)
    for path in files:
        text = read_utf8(path, "document conventions", errors)
        if text is None:
            continue
        if deprecated_examples.search(text):
            errors.append(f"{path.relative_to(ROOT)}: use canonical ISS/P-priority/Japanese-state examples")

    scoring = rules[rules.find("### 3.3 総合完成度の算出") : rules.find("### 3.4 評価の確度")]
    if "N/A" not in scoring or "未評価" not in scoring:
        errors.append("issue-tracking.md: scoring rules must distinguish N/A from 未評価")
    if "正式な総合完成度" not in rules or "評価済みカバレッジ" not in rules:
        errors.append("issue-tracking.md: scoring rules must define formal score and evaluation coverage")

    skill_references = ROOT / ".agents/skills/devconcord/references/modules/management/devconcord-generate-agent-guidance/references"
    agents_guidance = read_utf8(
        skill_references / "agents-md.md", "AGENTS.md generation guidance", errors
    ) or ""
    review_guidance = read_utf8(
        skill_references / "reviews-md.md", "REVIEW.md generation guidance", errors
    ) or ""
    if "## コードレビュー" not in agents_guidance or "REVIEW.md" not in agents_guidance:
        errors.append("devconcord (guidance module)/agents-md.md: must require a review-time REVIEW.md instruction")
    if "AGENTS.md" not in review_guidance or "レビュー開始前" not in review_guidance:
        errors.append("devconcord (guidance module)/reviews-md.md: must connect REVIEW.md to AGENTS.md loading")
    if (ROOT / "prompts").exists():
        errors.append("prompts/: remove the retired directory; Skills are the canonical workflow sources")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--issue-register", type=Path, help="validate one explicitly selected issue register (read-only)")
    target.add_argument("--issue-main", type=Path, help="validate an explicitly selected federated issue index (read-only)")
    parser.add_argument("--managed-dir", type=Path, help="explicit directory containing all indexed subregisters")
    args = parser.parse_args(argv)
    if args.issue_register or args.issue_main:
        if args.issue_register and args.managed_dir:
            parser.error("--managed-dir is only valid with --issue-main")
        if args.issue_main and not args.managed_dir:
            parser.error("--issue-main requires --managed-dir")
        if args.issue_register:
            errors = validate_single_issue_register(args.issue_register)
            label = f"single issue register: {args.issue_register}"
        else:
            errors = validate_federated_issue_register(args.issue_main, args.managed_dir)
            label = f"federated issue register: {args.issue_main} (managed: {args.managed_dir})"
        if errors:
            print(f"Validation failed for {label}:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Validation passed for {label}.")
        return 0
    if args.managed_dir:
        parser.error("--managed-dir requires --issue-main")
    errors: list[str] = []
    files = markdown_files(errors)
    errors.extend(check_links(files))
    errors.extend(check_privacy_hygiene(files))
    errors.extend(check_conventions(files))
    if __package__:
        from .agent_skills import (
            validate_official_skill_names,
            validate_repository_skills,
        )
    else:
        from agent_skills import validate_official_skill_names, validate_repository_skills
    errors.extend(validate_official_skill_names(ROOT / ".agents" / "skills"))
    errors.extend(validate_repository_skills(ROOT))
    return fail(errors)


if __name__ == "__main__":
    sys.exit(main())
