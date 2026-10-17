from __future__ import annotations

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
        shutil.copytree(repository / "prompts", self.root / "prompts")
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


if __name__ == "__main__":
    unittest.main()
