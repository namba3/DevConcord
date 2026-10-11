#!/usr/bin/env python3
"""Validate local docs, conventions, and likely privacy leaks in Markdown."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


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
PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----")
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


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.relative_to(ROOT).parts
        and "node_modules" not in path.relative_to(ROOT).parts
    )


def without_fenced_code(text: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    fence_char: str | None = None
    fence_size = 0
    for line in lines:
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence_char is None:
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                fence_char, fence_size = None, 0
            result.append("")
        elif fence_char is None:
            result.append(line)
        else:
            result.append("")
    return "\n".join(result)


def slugify_heading(heading: str) -> str:
    heading = re.sub(r"`([^`]*)`", r"\1", heading)
    heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s-]+", "-", heading)


def heading_anchors(text: str) -> set[str]:
    text = without_fenced_code(text)
    anchors = {
        match.group(1)
        for match in re.finditer(
            r"<(?:a|[^>]+)\b(?:id|name)=[\"']([^\"']+)[\"']",
            text,
            flags=re.IGNORECASE,
        )
    }
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        slug = slugify_heading(match.group(1))
        index = counts.get(slug, 0)
        counts[slug] = index + 1
        anchors.add(slug if index == 0 else f"{slug}-{index}")
    return anchors


def normalized_reference(label: str) -> str:
    return re.sub(r"\s+", " ", label).strip().casefold()


def unescape_markdown_punctuation(value: str) -> str:
    return re.sub(r"\\([^\w\s])", r"\1", value)


def closing_markdown_delimiter(text: str, start: int, opening: str, closing: str) -> int | None:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def inline_link_destination(text: str, opening: int) -> tuple[str, int] | None:
    link_close = closing_markdown_delimiter(text, opening, "(", ")")
    if link_close is None:
        return None
    index = opening + 1
    while index < link_close and text[index].isspace():
        index += 1

    if index < link_close and text[index] == "<":
        start = index + 1
        index = start
        while index < link_close:
            if text[index] == "\\":
                index += 2
                continue
            if text[index] == ">":
                return unescape_markdown_punctuation(text[start:index]), link_close + 1
            index += 1
        return None

    start = index
    nested_parentheses = 0
    while index < link_close:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "(":
            nested_parentheses += 1
        elif char == ")":
            nested_parentheses -= 1
        elif char.isspace() and nested_parentheses == 0:
            break
        index += 1
    return unescape_markdown_punctuation(text[start:index]), link_close + 1


def inline_link_destinations(text: str) -> list[str]:
    destinations: list[str] = []
    index = 0
    while index < len(text):
        opener = index + 1 if text[index] == "!" and index + 1 < len(text) and text[index + 1] == "[" else index
        if text[opener] != "[" or (opener > 0 and text[opener - 1] == "\\"):
            index += 1
            continue
        close_bracket = closing_markdown_delimiter(text, opener, "[", "]")
        if close_bracket is None:
            index += 1
            continue
        link_open = close_bracket + 1
        if link_open >= len(text) or text[link_open] != "(":
            index = close_bracket + 1
            continue
        parsed = inline_link_destination(text, link_open)
        if parsed is None:
            index = close_bracket + 1
            continue
        destination, index = parsed
        destinations.append(destination)
    return destinations


def markdown_link_destinations(text: str) -> tuple[list[str], list[str]]:
    """Return inline, reference, and HTML link targets plus unresolved references."""
    text = without_fenced_code(text)
    text = re.sub(r"(`+)[^`\n]*?\1", "", text)

    reference_pattern = re.compile(
        r"^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))[^\n]*$",
        flags=re.MULTILINE,
    )
    references: dict[str, str] = {}

    def remove_reference(match: re.Match[str]) -> str:
        destination = unescape_markdown_punctuation(match.group(2) or match.group(3))
        references.setdefault(normalized_reference(match.group(1)), destination)
        return ""

    body = reference_pattern.sub(remove_reference, text)
    destinations = list(references.values())
    unresolved: list[str] = []

    destinations.extend(inline_link_destinations(body))

    explicit_reference = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
    for match in explicit_reference.finditer(body):
        label = match.group(2) or match.group(1)
        key = normalized_reference(label)
        if key in references:
            destinations.append(references[key])
        else:
            unresolved.append(label)

    used_ranges = [match.span() for match in explicit_reference.finditer(body)]
    shortcut_reference = re.compile(r"!?\[([^\]]+)\](?![\[(])")
    for match in shortcut_reference.finditer(body):
        if any(start <= match.start() < end for start, end in used_ranges):
            continue
        key = normalized_reference(match.group(1))
        if key in references:
            destinations.append(references[key])

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

    html_links = LinkAttributeParser()
    html_links.feed(body)
    destinations.extend(html_links.destinations)
    return destinations, unresolved


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    cache: dict[Path, tuple[str, set[str]]] = {}

    for source in files:
        source_text = source.read_text(encoding="utf-8")
        destinations, unresolved = markdown_link_destinations(source_text)
        for label in unresolved:
            errors.append(f"{source.relative_to(ROOT)}: undefined link reference {label!r}")
        for destination in destinations:
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                continue

            relative_path = unquote(parsed.path)
            target = (source.parent / relative_path).resolve() if relative_path else source
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

            if target not in cache and target.is_file():
                text = target.read_text(encoding="utf-8")
                cache[target] = (text, heading_anchors(text))
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
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            relative = path.relative_to(ROOT)
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
    rules = ISSUE_RULES.read_text(encoding="utf-8")
    template = ISSUE_TEMPLATE.read_text(encoding="utf-8")
    guide = ADR_GUIDE.read_text(encoding="utf-8")
    adr_template = ADR_TEMPLATE.read_text(encoding="utf-8")
    requirements_template = REQUIREMENTS_TEMPLATE.read_text(encoding="utf-8")
    risk_guide = RISK_GUIDE.read_text(encoding="utf-8")

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
        "| ID | 要求 | 優先度 | 状態 | 受け入れ条件 | 検証方法・証跡 | 設計・実装・課題 |",
        "| ID | 品質特性 | 要求・条件 | 状態 | 受け入れ条件・検証方法・証跡 | 設計・実装・課題 |",
    ):
        if expected_header not in requirements_template:
            errors.append("requirements.md: requirement rows must connect state, acceptance, evidence, and references")

    risk_status_line = next(
        (line for line in risk_guide.splitlines() if line.startswith("状態は `")), ""
    )
    risk_status_match = re.search(r"状態は (.*?) を使う", risk_status_line)
    declared_risk_statuses = (
        backtick_values(risk_status_match.group(1)) if risk_status_match else []
    )
    risk_table_start = risk_guide.find("| 状態 | 意味・更新条件 |")
    risk_table_lines = (
        risk_guide[risk_table_start:].splitlines()[2:]
        if risk_table_start >= 0
        else []
    )
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
        text = path.read_text(encoding="utf-8")
        if deprecated_examples.search(text):
            errors.append(f"{path.relative_to(ROOT)}: use canonical ISS/P-priority/Japanese-state examples")

    scoring = rules[rules.find("### 3.3 総合完成度の算出") : rules.find("### 3.4 評価の確度")]
    if "N/A" not in scoring or "未評価" not in scoring:
        errors.append("issue-tracking.md: scoring rules must distinguish N/A from 未評価")
    if "正式な総合完成度" not in rules or "評価済みカバレッジ" not in rules:
        errors.append("issue-tracking.md: scoring rules must define formal score and evaluation coverage")

    agents_prompt = (ROOT / "prompts/create-agents-md.md").read_text(encoding="utf-8")
    review_instruction = (ROOT / "prompts/create-reviews-md.md").read_text(encoding="utf-8")
    if "## コードレビュー" not in agents_prompt or "REVIEWS.md" not in agents_prompt:
        errors.append("create-agents-md.md: must require a review-time REVIEWS.md instruction")
    if "AGENTS.md" not in review_instruction or "レビュー開始前" not in review_instruction:
        errors.append("create-reviews-md.md: must connect REVIEWS.md to AGENTS.md loading")
    return errors


def main() -> int:
    files = markdown_files()
    errors = check_links(files)
    errors.extend(check_privacy_hygiene(files))
    errors.extend(check_conventions(files))
    return fail(errors)


if __name__ == "__main__":
    sys.exit(main())
