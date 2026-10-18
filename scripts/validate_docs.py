#!/usr/bin/env python3
"""Validate local docs, conventions, and likely privacy leaks in Markdown."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
ISSUE_RULES = ROOT / "docs/work-management/issue-tracking.md"
ISSUE_TEMPLATE = ROOT / "docs/work-management/templates/issue-register.md"
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


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_utf8(path: Path, purpose: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(
            f"{relative_path(path)}: cannot read {purpose} ({type(error).__name__})"
        )
        return None


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.relative_to(ROOT).parts
        and "node_modules" not in path.relative_to(ROOT).parts
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

    for source in files:
        source_text = read_utf8(source, "Markdown links", errors)
        if source_text is None:
            continue
        destinations, unresolved = markdown_link_destinations(source_text)
        for label in unresolved:
            errors.append(f"{source.relative_to(ROOT)}: undefined link reference {label!r}")
        for destination in destinations:
            try:
                parsed = urlsplit(destination)
            except ValueError:
                errors.append(
                    f"{source.relative_to(ROOT)}: invalid link destination {destination!r}"
                )
                continue
            if parsed.scheme or parsed.netloc:
                continue

            relative_path = unquote(parsed.path)
            try:
                target = (source.parent / relative_path).resolve() if relative_path else source
            except (OSError, RuntimeError) as error:
                errors.append(
                    f"{source.relative_to(ROOT)}: cannot resolve link target "
                    f"{destination!r} ({type(error).__name__})"
                )
                continue
            try:
                target.relative_to(ROOT)
            except ValueError:
                errors.append(f"{source.relative_to(ROOT)}: link escapes repository {destination}")
                continue
            if not target.exists():
                errors.append(f"{source.relative_to(ROOT)}: missing link target {destination}")
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
                    f"{source.relative_to(ROOT)}: missing anchor {parsed.fragment!r} in "
                    f"{target.relative_to(ROOT)}"
                )
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
    required_issue_header = "| ID | 分類 | 優先度 | 状態 | 課題・影響 | 完了条件 | 根拠・検証 | 更新日 |"
    if required_issue_header not in template:
        errors.append("issue-register.md: required issue columns are missing or out of order")
    for value in ["未確定", "暫定総合完成度", "評価済みカバレッジ", "N/A", "未評価"]:
        if value not in template:
            errors.append(f"issue-register.md: missing completion-evaluation field {value}")

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

    skill_references = ROOT / ".agents/skills/generate-agent-guidance/references"
    agents_guidance = read_utf8(
        skill_references / "agents-md.md", "AGENTS.md generation guidance", errors
    ) or ""
    review_guidance = read_utf8(
        skill_references / "reviews-md.md", "REVIEWS.md generation guidance", errors
    ) or ""
    if "## コードレビュー" not in agents_guidance or "REVIEWS.md" not in agents_guidance:
        errors.append("generate-agent-guidance/agents-md.md: must require a review-time REVIEWS.md instruction")
    if "AGENTS.md" not in review_guidance or "レビュー開始前" not in review_guidance:
        errors.append("generate-agent-guidance/reviews-md.md: must connect REVIEWS.md to AGENTS.md loading")

    if (ROOT / "prompts").exists():
        errors.append("prompts/: remove the retired directory; Skills are the canonical workflow sources")
    return errors


def main() -> int:
    files = markdown_files()
    errors = check_links(files)
    errors.extend(check_privacy_hygiene(files))
    errors.extend(check_conventions(files))
    if __package__:
        from .agent_skills import validate_repository_skills
    else:
        from agent_skills import validate_repository_skills
    errors.extend(validate_repository_skills(ROOT))
    return fail(errors)


if __name__ == "__main__":
    sys.exit(main())
