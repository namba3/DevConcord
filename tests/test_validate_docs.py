from __future__ import annotations

import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_docs


class LinkValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.root_patch = patch.object(validate_docs, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_bytes(self, name: str, content: bytes) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_valid_inline_reference_image_and_html_links(self) -> None:
        source = self.write(
            "index.md",
            """[inline](target.md#section)
![image][diagram]

[Guide]: target.md#section
[diagram]: target.md#section-1
![section-1]
[section-1]: target.md#section-1
<a href="target.md#section">guide</a>
<img src="target.md#section-1" />
""",
        )
        self.write("target.md", "## Section\n\n## Section\n")

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_missing_file_anchor_and_reference_are_reported(self) -> None:
        source = self.write(
            "index.md",
            """[missing](absent.md)
<img src="target.md#absent" />
![missing reference][unknown]
""",
        )
        self.write("target.md", "## Present\n")

        errors = validate_docs.check_links([source])
        self.assertTrue(any("missing link target absent.md" in error for error in errors))
        self.assertTrue(any("missing anchor 'absent'" in error for error in errors))
        self.assertTrue(any("undefined link reference 'unknown'" in error for error in errors))

    def test_parenthesized_and_percent_encoded_paths_and_empty_destination(self) -> None:
        source = self.write(
            "index.md",
            """[literal](docs/example(v2).md)
[encoded](docs/example%28v2%29.md)
[this document]()
""",
        )
        self.write("docs/example(v2).md", "## Example\n")

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_escaped_parentheses_in_reference_destination(self) -> None:
        source = self.write(
            "index.md",
            r"""[Guide]: docs/example\(v2\).md

[Guide]
""",
        )
        self.write("docs/example(v2).md", "# Guide\n")

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_first_duplicate_reference_definition_wins(self) -> None:
        source = self.write(
            "index.md",
            """[Guide]: target.md
[guide]: missing.md
[read this][GUIDE]
""",
        )
        self.write("target.md", "# Guide\n")

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_fenced_headings_are_not_anchors_and_duplicate_headings_are_sluggified(self) -> None:
        source = self.write(
            "index.md",
            """```markdown
## Example
```

## Example
## Example
[second heading](#example-1)
[code heading](#example-2)
## **Bold** Title
[formatted heading](#bold-title)
""",
        )

        anchors = validate_docs.heading_anchors(source.read_text(encoding="utf-8"))
        self.assertIn("example", anchors)
        self.assertIn("example-1", anchors)
        self.assertNotIn("example-2", anchors)
        errors = validate_docs.check_links([source])
        self.assertTrue(any("missing anchor 'example-2'" in error for error in errors))
        self.assertFalse(any("missing anchor 'example-1'" in error for error in errors))

    def test_links_in_comments_indented_code_and_inline_code_are_ignored(self) -> None:
        source = self.write(
            "index.md",
            r"""<!-- [missing](absent.md#missing) -->
    [indented code](absent.md#missing)

```md
[fenced code](absent.md#missing)
```

`[inline code](absent.md#missing)`

\[escaped label\](absent.md#missing)
[real link](target.md#present)
[directory](docs/)
""",
        )
        self.write("target.md", "# Present\n")
        (self.root / "docs").mkdir()

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_html_id_attributes_and_non_markdown_fragments(self) -> None:
        source = self.write(
            "index.md",
            """[html](page.HTML#chapter)
[pdf](manual.pdf#page=2)
""",
        )
        self.write("page.HTML", '<section id=chapter><a name="legacy"></a></section>')
        self.write_bytes("manual.pdf", b"%PDF-1.7\xff\xfe\x00")

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_html_id_and_name_anchors_are_recognized(self) -> None:
        source = self.write(
            "index.md",
            """[id](page.html#chapter)
[legacy](page.html#legacy)
""",
        )
        self.write("page.html", '<section id="chapter"><a name=legacy></a></section>')

        self.assertEqual(validate_docs.check_links([source]), [])

    def test_relative_path_outside_repository_is_reported(self) -> None:
        source = self.write("index.md", "[outside](../outside.md)\n")

        errors = validate_docs.check_links([source])

        self.assertTrue(any("link escapes repository" in error for error in errors))

    def test_malformed_url_is_reported_without_raising(self) -> None:
        source = self.write("index.md", '<a href="http://[::1">invalid</a>\n')

        errors = validate_docs.check_links([source])

        self.assertTrue(any("invalid link destination" in error for error in errors))

    def test_invalid_utf8_source_is_reported_without_raising(self) -> None:
        source = self.write_bytes("index.md", b"[invalid](\xff)\n")

        errors = validate_docs.check_links([source])

        self.assertTrue(any("cannot read Markdown links" in error for error in errors))

    def test_invalid_utf8_fragment_target_is_reported_without_raising(self) -> None:
        source = self.write("index.md", "[target](bad.md#anchor)\n")
        self.write_bytes("bad.md", b"# \xff\n")

        errors = validate_docs.check_links([source])

        self.assertTrue(any("cannot read fragment" in error for error in errors))


class MarkdownDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.root_patch = patch.object(validate_docs, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def write(self, name: str, content: str = "# Document\n") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_includes_new_markdown_and_checks_its_links(self) -> None:
        self.write("guide.md")
        added = self.write("new/added.MD", "[broken](missing.md)\n")
        self.write("reference.markdown")

        files = validate_docs.markdown_files()

        self.assertIn(added, files)
        self.assertEqual(
            [validate_docs.relative_path(path) for path in files],
            ["guide.md", "new/added.MD", "reference.markdown"],
        )
        errors = validate_docs.check_links(files)
        self.assertTrue(any("new/added.MD" in error and "missing.md" in error for error in errors))

    def test_skips_dependency_environment_and_generated_trees(self) -> None:
        self.write("guide.md")
        for directory in (
            ".git",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            ".nox",
            "htmlcov",
            "package.egg-info",
            "build",
            "dist",
        ):
            self.write(f"{directory}/nested/ignored.md", "[broken](missing.md)\n")

        self.assertEqual(
            [validate_docs.relative_path(path) for path in validate_docs.markdown_files()],
            ["guide.md"],
        )

    def test_keeps_markdown_under_nested_build_named_directory(self) -> None:
        document = self.write("docs/build/guide.md")

        self.assertEqual(validate_docs.markdown_files(), [document])

    def test_does_not_follow_symlinked_markdown_or_directory(self) -> None:
        self.write("guide.md")
        outside = Path(self.temp_dir.name).parent / f"{self.root.name}-outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        try:
            (self.root / "linked.md").symlink_to(outside)
            (self.root / "linked-dir").symlink_to(outside.parent, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlinks are unavailable: {type(error).__name__}")

        errors: list[str] = []
        files = validate_docs.markdown_files(errors)

        self.assertEqual([validate_docs.relative_path(path) for path in files], ["guide.md"])
        self.assertTrue(any("linked.md" in error and "regular files only" in error for error in errors))
        self.assertTrue(any("linked-dir" in error and "does not follow directory links" in error for error in errors))
        self.assertNotIn(str(outside), "\n".join(errors))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are unavailable")
    def test_rejects_special_markdown_files_without_opening_them(self) -> None:
        fifo = self.root / "pipe.md"
        os.mkfifo(fifo)

        errors: list[str] = []
        files = validate_docs.markdown_files(errors)

        self.assertEqual(files, [])
        self.assertTrue(any("pipe.md" in error and "regular files only" in error for error in errors))


class PrivacyHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.root_patch = patch.object(validate_docs, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_reports_sensitive_patterns_without_echoing_values(self) -> None:
        source = self.root / "example.md"
        source.write_text(
            """/home/alice/private-project
C:\\Users\\Alice\\Documents\\project
person@private-corp.com
api_key = verysecretcredentialvalue123
https://build-user:embedded-secret@service.example/path
""",
            encoding="utf-8",
        )

        errors = validate_docs.check_privacy_hygiene([source])
        combined = "\n".join(errors)

        self.assertTrue(any("personal home path" in error for error in errors))
        self.assertTrue(any("personal contact address" in error for error in errors))
        self.assertTrue(any("embedded credential" in error for error in errors))
        self.assertTrue(any("embedded URL credentials" in error for error in errors))
        self.assertNotIn("alice", combined)
        self.assertNotIn("person@private-corp.com", combined)
        self.assertNotIn("verysecretcredentialvalue123", combined)
        self.assertNotIn("embedded-secret", combined)

    def test_allows_generic_paths_and_placeholder_values(self) -> None:
        source = self.root / "example.md"
        source.write_text(
            """$HOME/projects/app
C:\\Users\\<USERNAME>\\Project
user@example.org
api_key = <YOUR_TOKEN>
""",
            encoding="utf-8",
        )

        self.assertEqual(validate_docs.check_privacy_hygiene([source]), [])

    def test_detects_multiple_private_key_header_formats_without_echoing_content(self) -> None:
        source = self.root / "key-markers.md"
        source.write_text(
            """-----BEGIN EC PRIVATE KEY-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
-----BEGIN OPENSSH PRIVATE KEY-----
""",
            encoding="utf-8",
        )

        errors = validate_docs.check_privacy_hygiene([source])

        self.assertEqual(len(errors), 3)
        self.assertTrue(all("private key material" in error for error in errors))
        self.assertNotIn("EC PRIVATE KEY", "\n".join(errors))


class ConventionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        repository = Path(__file__).resolve().parents[1]
        shutil.copytree(repository / "docs", self.root / "docs")
        shutil.copytree(repository / ".agents/skills", self.root / ".agents/skills")
        constants = {
            "ROOT": self.root,
            "ISSUE_RULES": self.root / "docs/work-management/issue-tracking.md",
            "ISSUE_TEMPLATE": self.root / "docs/work-management/templates/issue-register.md",
            "ADR_GUIDE": self.root / "docs/common/ai-assisted-development.md",
            "ADR_TEMPLATE": self.root / "docs/application-design/templates/adr.md",
            "REQUIREMENTS_TEMPLATE": self.root / "docs/application-design/templates/requirements.md",
            "RISK_GUIDE": self.root / "docs/work-management/risk-management.md",
        }
        self.constants_patch = patch.multiple(validate_docs, **constants)
        self.constants_patch.start()
        self.addCleanup(self.constants_patch.stop)

    def conventions(self) -> list[str]:
        return validate_docs.check_conventions(validate_docs.markdown_files())

    def test_canonical_documents_pass(self) -> None:
        self.assertEqual(self.conventions(), [])

    def test_retired_prompts_directory_is_rejected(self) -> None:
        (self.root / "prompts").mkdir()

        errors = self.conventions()

        self.assertTrue(any("remove the retired directory" in error for error in errors))

    def test_invalid_evaluation_axis_is_reported(self) -> None:
        template = self.root / "docs/work-management/templates/issue-register.md"
        text = template.read_text(encoding="utf-8").replace("| UI/UX | 5% |", "| UI/UX | 6% |", 1)
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("evaluation axes or weights differ" in error for error in errors))

    def test_mismatched_priority_is_reported(self) -> None:
        template = self.root / "docs/work-management/templates/issue-register.md"
        text = template.read_text(encoding="utf-8").replace("`P0`（緊急）", "`P4`（緊急）", 1)
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("issue priorities must use P0" in error for error in errors))

    def test_requirement_table_must_keep_traceability_columns(self) -> None:
        template = self.root / "docs/application-design/templates/requirements.md"
        text = template.read_text(encoding="utf-8").replace("| 検証方法・証跡 |", "| 検証方法 |", 1)
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("requirement rows must connect state" in error for error in errors))

    def test_user_task_table_must_link_to_requirement_ids(self) -> None:
        template = self.root / "docs/application-design/templates/requirements.md"
        text = template.read_text(encoding="utf-8").replace("| 関連要求ID |", "| 機能 |", 1)
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()

        self.assertTrue(any("user tasks must link to stable requirement IDs" in error for error in errors))

    def test_requirement_template_must_record_design_sources(self) -> None:
        template = self.root / "docs/application-design/templates/requirements.md"
        text = template.read_text(encoding="utf-8").replace(
            "**入力設計書・版/コミット等:**", "**関連資料:**", 1
        )
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()

        self.assertTrue(any("trace to source design documents" in error for error in errors))

    def test_unrecognized_requirement_state_is_reported(self) -> None:
        template = self.root / "docs/application-design/templates/requirements.md"
        text = template.read_text(encoding="utf-8").replace(
            "`廃止` を使います", "`廃止` / `試験中` を使います", 1
        )
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("requirement lifecycle states" in error for error in errors))

    def test_risk_lifecycle_state_drift_is_reported(self) -> None:
        guide = self.root / "docs/work-management/risk-management.md"
        text = guide.read_text(encoding="utf-8").replace("| 顕在化 |", "| 発生済み |", 1)
        guide.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("risk lifecycle states" in error for error in errors))

    def test_unrecognized_risk_state_is_reported(self) -> None:
        guide = self.root / "docs/work-management/risk-management.md"
        text = guide.read_text(encoding="utf-8")
        marker = "| 解消 |"
        index = text.index(marker)
        end = text.index("\n", index)
        text = text[:end] + "\n| 発生済み | 不正な状態 |" + text[end:]
        guide.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("risk lifecycle states" in error for error in errors))

    def test_unrelated_table_after_risk_states_is_ignored(self) -> None:
        guide = self.root / "docs/work-management/risk-management.md"
        text = guide.read_text(encoding="utf-8")
        text += "\n## 補足資料\n\n| 項目 | 値 |\n|---|---|\n| 例 | 任意 |\n"
        guide.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertFalse(any("risk lifecycle states" in error for error in errors))

    def test_sds_axes_and_weights_must_match_the_rules(self) -> None:
        template = self.root / "docs/work-management/templates/issue-register.md"
        text = template.read_text(encoding="utf-8").replace(
            "| ドメイン表現力 | 25% |", "| ドメイン表現力 | 24% |", 1
        )
        template.write_text(text, encoding="utf-8")

        errors = self.conventions()
        self.assertTrue(any("SDS axes or weights" in error for error in errors))


class FederatedIssueRegisterValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        source = Path(__file__).resolve().parent / "integration/fixtures/federated-issue-registers/docs"
        shutil.copytree(source, root / "docs")
        self.main = root / "docs/ISSUES.md"
        self.managed = root / "docs/issues"

    def validate(self) -> list[str]:
        return validate_docs.validate_federated_issue_register(self.main, self.managed)

    def test_official_japanese_columns_and_decorated_counter_validate_cleanly(self) -> None:
        official_single = validate_docs.ROOT / "docs/work-management/templates/issue-register.md"
        self.assertEqual(validate_docs.validate_single_issue_register(official_single), [])
        official_records = validate_docs._issue_record_rows(official_single.read_text(encoding="utf-8"), official_single)
        self.assertEqual(official_records, [])
        self.main.write_text(
            "# 課題索引\n\n## 共通ISS採番\n\n- **次の未割当番号:** `ISS-0003`\n\n"
            "## サブ課題表\n\n| 領域 | 課題表 |\n|---|---|\n"
            "| 設計 | [設計](issues/architecture.md) |\n\n"
            "## タグ定義\n\n| タグ | 意味 |\n|---|---|\n| ARCH | 設計 |\n| REL | 信頼性 |\n",
            encoding="utf-8",
        )
        (self.managed / "architecture.md").write_text(
            "# 設計課題\n\n## 課題一覧\n\n"
            "| ID | 分類 | タグ（任意） | 作業種別（任意） | 優先度 | 状態 | 内容 | 完了条件 | 根拠 | 更新日 | 独自列 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| ISS-0001 | 設計 | ARCH, REL | リファクタリング | P2 | 未着手 | 分割 | テスト | CI | 2026-10-26 | extra |\n",
            encoding="utf-8",
        )
        (self.managed / "quality.md").unlink()
        errors = self.validate()
        self.assertEqual(errors, [])

    def test_issue_rows_use_headers_after_reordering_and_ignore_code_examples(self) -> None:
        text = """# Issues

## Global issue allocation
- Next unused ID: ISS-0002

## Register
| Status | Extra | Tags | Issue ID | Priority |
|---|---|---|---|---|
| Open | value | QA | ISS-0001 | P2 |

```markdown
| ID | Tags |
|---|---|
| ISS-9000 | INVALID |
```
Reference: ISS-8000
"""
        path = self.managed.parent / "single.md"
        path.write_text(text, encoding="utf-8")
        self.assertEqual(validate_docs.validate_single_issue_register(path), [])

    def test_legacy_table_without_tag_column_and_counter_variants_are_supported(self) -> None:
        path = self.managed.parent / "single.md"
        path.write_text(
            "# Issues\n\n## 共通ISS採番\n- 次の未割当番号: ISS-0002\n\n"
            "## Issues\n| 状態 | ID | 分類 | 独自 |\n|---|---|---|---|\n"
            "| Open | ISS-0001 | 設計 | value |\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_docs.validate_single_issue_register(path), [])
        content = path.read_text(encoding="utf-8").replace(
            "次の未割当番号: ISS-0002", "**Next unused ID:** `ISS-0002`"
        )
        content = content.replace(
            "**Next unused ID:** `ISS-0002`",
            "**Next unused ID:** `ISS-0002`\n```markdown\n- Next unused ID: ISS-9999\n```",
        )
        path.write_text(content, encoding="utf-8")
        self.assertEqual(validate_docs.validate_single_issue_register(path), [])

    def test_noncanonical_and_numerically_duplicate_ids_are_reported_with_locations(self) -> None:
        path = self.managed / "architecture.md"
        content = path.read_text(encoding="utf-8").replace("ISS-0125", "ISS-00001")
        content = content.replace("ISS-0126", "ISS-0001")
        path.write_text(content, encoding="utf-8")
        quality = self.managed / "quality.md"
        quality.write_text(quality.read_text(encoding="utf-8").replace("ISS-0127", "ISS-0001"), encoding="utf-8")
        errors = self.validate()
        self.assertTrue(any("non-canonical issue ID ISS-00001" in error for error in errors))
        collision = next(error for error in errors if "duplicate issue ID" in error and "numeric value 1" in error)
        self.assertIn("architecture.md", collision)
        self.assertIn("quality.md", collision)

    def test_counter_duplicates_malformed_and_missing_are_distinguished(self) -> None:
        source = self.main.read_text(encoding="utf-8")
        self.main.write_text(source.replace("Next unused ID: `ISS-0131`", "Next unused ID: `ISS-0131`\n- 次の未割当番号: ISS-0132"), encoding="utf-8")
        self.assertTrue(any("exactly one valid next unused ISS counter" in error for error in self.validate()))
        self.main.write_text(source.replace("ISS-0131", "ISS-ABCD"), encoding="utf-8")
        self.assertTrue(any("invalid next unused ISS counter" in error for error in self.validate()))
        self.main.write_text(source.replace("- Next unused ID: `ISS-0131`\n", ""), encoding="utf-8")
        self.assertTrue(any("missing a next unused ISS counter" in error for error in self.validate()))

    def test_cli_read_only_validation_accepts_explicit_single_path(self) -> None:
        register = self.managed.parent / "single.md"
        register.write_text(
            "# Issues\n## Global issue allocation\n- Next unused ID: `ISS-0002`\n"
            "## Issues\n| ID | Tags | Status |\n|---|---|---|\n| ISS-0001 | — | Open |\n",
            encoding="utf-8",
        )
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(validate_docs.main(["--issue-register", str(register)]), 0)
        self.assertIn("Validation passed", output.getvalue())

    def test_cli_validates_explicit_federated_scope_read_only(self) -> None:
        before = {
            path: path.read_bytes()
            for path in (self.main, *self.managed.glob("*.md"))
        }
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(
                validate_docs.main([
                    "--issue-main", str(self.main), "--managed-dir", str(self.managed)
                ]),
                0,
            )
        self.assertIn("Validation passed", output.getvalue())
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_id_width_expands_after_9999_without_reusing_gaps(self) -> None:
        register = self.managed.parent / "single.md"
        register.write_text(
            "# Issues\n## Global issue allocation\n- Next unused ID: ISS-10000\n"
            "## Issues\n| ID | Status |\n|---|---|\n| ISS-9999 | Open |\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_docs.validate_single_issue_register(register), [])

    def test_invalid_utf8_and_external_symlink_are_reported(self) -> None:
        quality = self.managed / "quality.md"
        quality.write_bytes(b"\xff\xfe")
        errors = self.validate()
        self.assertTrue(any("cannot read" in error and "quality.md" in error for error in errors))

        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("# external\n", encoding="utf-8")
        link = self.managed / "external.md"
        link.symlink_to(outside)
        self.main.write_text(
            self.main.read_text(encoding="utf-8").replace(
                "| Architecture | [`architecture.md`](issues/architecture.md) |",
                "| External | [outside](issues/external.md) |",
            ),
            encoding="utf-8",
        )
        errors = self.validate()
        self.assertTrue(any("escapes managed issue directory" in error for error in errors))

    def test_malformed_id_and_ambiguous_table_headers_are_reported(self) -> None:
        path = self.managed.parent / "single.md"
        path.write_text(
            "# Issues\n## Global issue allocation\n- Next unused ID: ISS-0002\n"
            "## Records\n| ID | Issue ID | Tags |\n|---|---|---|\n| ISS-00X1 | ISS-0001 | QA |\n",
            encoding="utf-8",
        )
        errors = validate_docs.validate_single_issue_register(path)
        self.assertTrue(any("ambiguous issue table header" in error for error in errors))
        path.write_text(
            "# Issues\n## Global issue allocation\n- Next unused ID: ISS-0002\n"
            "## Records\n| ID | Tags |\n|---|---|\n| ISS-00X1 | QA |\n",
            encoding="utf-8",
        )
        self.assertTrue(any("malformed issue ID ISS-00X1" in error for error in validate_docs.validate_single_issue_register(path)))
        path.write_text(
            "# Issues\n## Global issue allocation\n- Next unused ID: ISS-0002\n"
            "## Records\n| ID | Tags |\n|---|---|\n| ISS-0001 | QA | Extra |\n",
            encoding="utf-8",
        )
        self.assertTrue(any("issue table row has" in error for error in validate_docs.validate_single_issue_register(path)))

    def test_single_register_counter_accepts_five_digits_and_rejects_reuse(self) -> None:
        register = self.managed.parent / "single.md"
        register.write_text(
            "# Issues\n\n## 共通ISS採番\n\n- 次の未割当番号: ISS-10001\n\n"
            "## 課題一覧\n\n| ID | Tags | Status |\n|---|---|---|\n"
            "| ISS-10000 | — | Open |\n",
            encoding="utf-8",
        )
        self.assertEqual(validate_docs.validate_single_issue_register(register), [])
        register.write_text(
            register.read_text(encoding="utf-8") + "| ISS-10000 | — | Open |\n",
            encoding="utf-8",
        )
        self.assertTrue(any(
            "duplicate issue ID ISS-10000" in error
            for error in validate_docs.validate_single_issue_register(register)
        ))
        register.write_text(
            register.read_text(encoding="utf-8").replace("ISS-10001", "ISS-10000"),
            encoding="utf-8",
        )
        self.assertTrue(any(
            "next ISS counter" in error
            for error in validate_docs.validate_single_issue_register(register)
        ))

    def test_valid_federation_supports_five_digit_ids_and_optional_tags(self) -> None:
        text = self.main.read_text(encoding="utf-8").replace("ISS-0131", "ISS-10001")
        text += "\nThis index also mentions ISS-99999 as an example reference, not a record.\n"
        self.main.write_text(text, encoding="utf-8")
        architecture = self.managed / "architecture.md"
        content = architecture.read_text(encoding="utf-8").replace("ISS-0126", "ISS-10000")
        architecture.write_text(content, encoding="utf-8")

        self.assertEqual(self.validate(), [])

    def test_stale_important_issue_anchor_is_reported(self) -> None:
        self.main.write_text(
            self.main.read_text(encoding="utf-8").replace(
                "#iss-0125-storage-responsibilities", "#iss-0125-old-location"
            ),
            encoding="utf-8",
        )

        self.assertTrue(any("mismatched anchor" in error for error in self.validate()))

    def test_duplicate_id_preserves_both_paths_in_diagnostic(self) -> None:
        quality = self.managed / "quality.md"
        quality.write_text(
            quality.read_text(encoding="utf-8").replace("ISS-0127", "ISS-0125"),
            encoding="utf-8",
        )

        errors = self.validate()

        duplicate = next(error for error in errors if "duplicate issue ID ISS-0125" in error)
        self.assertIn("architecture.md", duplicate)
        self.assertIn("quality.md", duplicate)

    def test_counter_collision_missing_subregister_and_orphan_are_reported(self) -> None:
        main_text = self.main.read_text(encoding="utf-8")
        main_text = main_text.replace("ISS-0131", "ISS-0125")
        main_text = main_text.replace("issues/quality.md", "issues/missing.md")
        self.main.write_text(main_text, encoding="utf-8")
        (self.managed / "orphan.md").write_text("# Unindexed\n", encoding="utf-8")

        errors = self.validate()

        self.assertTrue(any("next ISS counter" in error for error in errors))
        self.assertTrue(any("missing subregister target" in error for error in errors))
        self.assertTrue(any("orphan.md" in error for error in errors))

    def test_undefined_tag_and_case_normalized_duplicate_are_reported(self) -> None:
        quality = self.managed / "quality.md"
        quality.write_text(
            quality.read_text(encoding="utf-8").replace("DOC |", "DOC, doc |", 1),
            encoding="utf-8",
        )
        architecture = self.managed / "architecture.md"
        architecture.write_text(
            architecture.read_text(encoding="utf-8").replace("ARCH, REL", "UNKNOWN, REL", 1),
            encoding="utf-8",
        )

        errors = self.validate()

        self.assertTrue(any("duplicate tags after case normalization" in error for error in errors))
        self.assertTrue(any("uses undefined tags: UNKNOWN" in error for error in errors))

    def test_important_issue_link_must_resolve_to_canonical_record(self) -> None:
        self.main.write_text(
            self.main.read_text(encoding="utf-8").replace("ISS-0125](issues/architecture.md", "ISS-0126](issues/quality.md"),
            encoding="utf-8",
        )

        self.assertTrue(any("does not resolve to its canonical record" in error for error in self.validate()))

    def test_duplicate_subregister_index_link_is_reported(self) -> None:
        main = self.main.read_text(encoding="utf-8")
        main = main.replace(
            "| Quality and operations | [`quality.md`](issues/quality.md) |",
            "| Quality and operations | [`quality.md`](issues/quality.md) |\n"
            "| Quality duplicate | [`quality-again.md`](issues/quality.md) |",
        )
        self.main.write_text(main, encoding="utf-8")

        self.assertTrue(any("duplicate subregister index link" in error for error in self.validate()))

    def test_defined_project_specific_tag_is_allowed(self) -> None:
        main = self.main.read_text(encoding="utf-8").replace(
            "| DOC | Documentation |", "| DOC | Documentation |\n| DATA | Project data subsystem |"
        )
        self.main.write_text(main, encoding="utf-8")
        quality = self.managed / "quality.md"
        quality.write_text(
            quality.read_text(encoding="utf-8").replace("ISS-0128 | DOC |", "ISS-0128 | DOC, DATA |"),
            encoding="utf-8",
        )

        self.assertEqual(self.validate(), [])

    def test_issue_reference_in_prose_is_not_a_main_index_record(self) -> None:
        self.main.write_text(
            self.main.read_text(encoding="utf-8")
            + "\nThis prose references ISS-99999 but does not define a task.\n",
            encoding="utf-8",
        )

        self.assertFalse(any("main index contains issue records" in error for error in self.validate()))



if __name__ == "__main__":
    unittest.main()
