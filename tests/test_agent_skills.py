from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import agent_skills
from scripts.agent_skills import (
    validate_official_skill_names,
    validate_repository_skills,
    validate_skill_directory,
)


class AgentSkillValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.skills_root = self.root / ".agents" / "skills"

    def make_skill(self, name: str, body: str | None = None) -> Path:
        skill_dir = self.skills_root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_dir.joinpath("SKILL.md").write_text(
            body
            or f"""---
name: {name}
description: Use this Skill for a focused task.
---

# {name}
""",
            encoding="utf-8",
        )
        return skill_dir

    def manifest_record(self, skill_dir: Path) -> dict[str, object]:
        return {
            "source_repository": "test-source",
            "source_commit": "unversioned",
            "source_dirty": False,
            "source_tree_sha256": "0" * 64,
            "installed_tree_sha256": agent_skills._skill_fingerprint(skill_dir),
        }

    def test_accepts_standard_portable_skill_metadata(self) -> None:
        skill_dir = self.make_skill("sample-skill")

        self.assertEqual(validate_skill_directory(skill_dir), [])

    def test_official_skill_set_uses_devconcord_namespace(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skills_root = repository_root / ".agents" / "skills"
        skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())

        self.assertEqual(len(skill_dirs), 13)
        self.assertTrue(all(path.name.startswith("devconcord-") for path in skill_dirs))
        self.assertTrue(all(not path.name.startswith("devconcord-devconcord-") for path in skill_dirs))
        self.assertEqual(validate_official_skill_names(skills_root), [])
        self.assertEqual(validate_repository_skills(repository_root), [])

    def test_official_prefix_is_not_required_for_generic_external_skills(self) -> None:
        external_skill = self.make_skill("sample-skill")
        self.assertEqual(validate_skill_directory(external_skill), [])

        duplicate_prefix = self.make_skill("devconcord-devconcord-example")
        self.assertEqual(validate_skill_directory(duplicate_prefix), [])

        self.assertEqual(validate_repository_skills(self.root), [])
        errors = validate_official_skill_names(self.skills_root)
        self.assertTrue(any("must start with 'devconcord-'" in error for error in errors))
        self.assertTrue(any("must not repeat" in error for error in errors))

    def test_documentation_architecture_skill_is_valid_and_discoverable(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill_dir = (
            repository_root
            / ".agents"
            / "skills"
            / "devconcord-documentation-architecture"
        )
        self.assertEqual(validate_skill_directory(skill_dir), [])
        skills_guide = (repository_root / "docs" / "agent-skills.md").read_text(
            encoding="utf-8"
        )
        docs_index = (repository_root / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("devconcord-documentation-architecture", skills_guide)
        self.assertIn("documentation-design.md", docs_index)

    def test_gap_analysis_skill_covers_evidence_scope_and_read_only_contract(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill_dir = repository_root / ".agents" / "skills" / "devconcord-gap-analysis"
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        report_text = (skill_dir / "references" / "report-format.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(validate_skill_directory(skill_dir), [])
        for expected in (
            "name: devconcord-gap-analysis",
            "full or incremental quality gap assessments",
            "Full Assessment",
            "Incremental Assessment",
            "Finding identity and lifecycle",
            "Same**, **Different**, or **Uncertain",
            "Mark a finding **Resolved** only when evidence",
            "relationships need not be one-to-one",
            "criteria revision change can require",
            "Requirements, domain, and architecture",
            "Performance:",
            "Robustness:",
            "Replaceability:",
            "Security:",
            "User experience and function:",
            "Documentation:",
            "Development and assurance:",
            "Conforms",
            "Partially conforms",
            "Not applicable",
            "Not assessed",
            "confirmed defect",
            "verification gap",
            "Do not edit the target",
            "Do not silently switch revisions",
            "--skill devconcord-gap-analysis",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, skill_text)
        for expected in (
            "## 1. Assessment overview",
            "## 3. Area assessment",
            "## 4. Prioritized findings",
            "Acceptance conditions:",
            "Verification method and evidence still needed:",
            "ten-axis weighted system",
            "do not replace formal issue IDs",
            "Previous target commit and working-tree state",
            "Previous and current DevConcord criteria identity/revision",
            "one-to-many or many-to-one",
            "Added tests alone are not proof",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, report_text)

    def test_gap_analysis_is_documented_and_manual_scenarios_cover_contract(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        readme = (repository_root / "README.md").read_text(encoding="utf-8")
        docs_index = (repository_root / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        skills_guide = (repository_root / "docs" / "agent-skills.md").read_text(
            encoding="utf-8"
        )
        scenarios = (
            repository_root / "tests" / "integration" / "README.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "devconcord-gap-analysis",
            "全体/差分診断",
        ):
            with self.subTest(document="README", expected=expected):
                self.assertIn(expected, readme)
            with self.subTest(document="docs index", expected=expected):
                self.assertIn(expected, docs_index)
        for expected in (
            "devconcord-gap-analysis",
            "devconcord-repository-review",
            "devconcord-documentation-architecture",
            "全体診断",
            "差分診断",
            "特定領域",
            "既存の課題表",
        ):
            with self.subTest(document="Skills guide", expected=expected):
                self.assertIn(expected, skills_guide)

        expected_scenarios = (
            "小規模CLIの全体診断",
            "GUIアプリの全体診断",
            "ネットワークサービスのSecurity分析",
            "ファイル操作アプリのRobustness分析",
            "UI技術交換のReplaceability評価",
            "大量データ処理のPerformance評価",
            "文書構造と情報の正本",
            "前回レポートからの差分診断",
            "DevConcord規約を導入していない対象",
            "`AGENTS.md`と`REVIEWS.md`がない対象",
            "適用不要な原則の判断",
            "証拠不足による未評価",
            "既存課題との重複検出",
            "DevConcord共通参照を取得できない場合",
            "未コミット変更を含む対象",
            "問題のあるファイル移動",
            "関数名変更",
            "同じ場所の別問題",
            "実際の修正",
            "テスト追加のみ",
            "機能の廃止",
            "要求・設計契約の変更",
            "一つの問題が複数へ分割",
            "複数問題が一つへ統合",
            "前回レポートなし",
            "対象commit不明",
            "DevConcord基準のrevision変更",
            "同一性を確定できない",
            "既存課題IDあり",
        )
        for expected in expected_scenarios:
            with self.subTest(scenario=expected):
                self.assertIn(expected, scenarios)

    def test_security_design_skill_is_self_contained_and_covers_security_contract(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill_dir = repository_root / ".agents" / "skills" / "devconcord-design-security"
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        self.assertEqual(validate_skill_directory(skill_dir), [])
        for expected in (
            "name: devconcord-design-security",
            "trust boundaries",
            "least privilege",
            "safe defaults",
            "defense in depth",
            "security invariants",
            "independent verification",
            "residual risks",
            "--skill devconcord-design-security",
            "one reference path per invocation",
            "Do not create a second security ledger or quality score",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, skill_text)

    def test_security_design_is_integrated_without_adding_quality_axes_or_ledgers(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        docs_index = (repository_root / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        skills_index = (repository_root / "docs" / "agent-skills.md").read_text(
            encoding="utf-8"
        )
        requirements = (
            repository_root / "docs" / "application-design" / "templates" / "requirements.md"
        ).read_text(encoding="utf-8")
        issues = (
            repository_root / "docs" / "work-management" / "issue-tracking.md"
        ).read_text(encoding="utf-8")
        reviews = (repository_root / "REVIEWS.md").read_text(encoding="utf-8")
        integration = (
            repository_root / "tests" / "integration" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("devconcord-design-security", docs_index)
        self.assertIn("devconcord-design-security", skills_index)
        for expected in (
            "保護対象の資産",
            "信頼境界",
            "脅威・影響",
            "受け入れ条件",
            "Security by Design",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, requirements)
        self.assertIn("| セキュリティ | 10% |", issues)
        self.assertIn("Security by Design", reviews)
        self.assertIn("外部ファイル取込サービス", integration)
        self.assertIn("AIエージェントを実行しません", integration)

    def test_bootstrap_workflow_reference_preserves_safety_and_scope_contracts(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill = repository_root / ".agents" / "skills" / "devconcord-bootstrap-from-design"
        skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
        workflow_text = (skill / "references" / "workflow.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Required safety checks", skill_text)
        self.assertIn("references/workflow.md", skill_text)
        self.assertIn("unborn HEAD", workflow_text)
        self.assertIn("Git初期化済みで履歴または既存成果物がある", workflow_text)
        self.assertIn("guidance-provenance.md", workflow_text)
        self.assertIn("完成度10軸とSDS", workflow_text)
        self.assertIn("同じ入力・範囲で再実行", workflow_text)

    def test_adoption_workflow_reference_preserves_provenance_and_existing_records(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill = repository_root / ".agents" / "skills" / "devconcord-adopt-guidance"
        skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
        workflow_text = (skill / "references" / "workflow.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Required safety checks", skill_text)
        self.assertIn("適用済み", workflow_text)
        self.assertIn("部分適用", workflow_text)
        self.assertIn("保留", workflow_text)
        self.assertIn("対象外", workflow_text)
        self.assertIn("比較基準コミット", workflow_text)
        self.assertIn("docs/guidance-provenance.md", workflow_text)
        self.assertIn("課題ID・状態・履歴", workflow_text)
        self.assertIn("未実施の確認", workflow_text)

    def test_sync_workflow_reference_separates_document_and_skill_updates(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill = repository_root / ".agents" / "skills" / "devconcord-sync-guidance"
        skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
        workflow_text = (skill / "references" / "workflow.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("does not update the globally installed DevConcord Skills", skill_text)
        self.assertIn("git merge-base --is-ancestor", workflow_text)
        self.assertIn("浅い履歴", workflow_text)
        self.assertIn("比較基準コミット", workflow_text)
        self.assertIn("部分適用・保留", workflow_text)
        self.assertIn("Project Scope", workflow_text)
        self.assertIn("User Scope", workflow_text)
        self.assertIn("Do not run `manage_skills.py` merely because a shared document changed.", workflow_text)

    def test_agent_guidance_generation_modes_and_detailed_contracts(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill = repository_root / ".agents" / "skills" / "devconcord-generate-agent-guidance"
        skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
        agents_text = (skill / "references" / "agents-md.md").read_text(
            encoding="utf-8"
        )
        reviews_text = (skill / "references" / "reviews-md.md").read_text(
            encoding="utf-8"
        )

        for mode in ("`agents`", "`reviews`", "`both`"):
            self.assertIn(mode, skill_text)
        self.assertIn("writing `REVIEWS.md` first", skill_text)
        self.assertIn("## コードレビュー", agents_text)
        self.assertIn("REVIEWS.md", agents_text)
        self.assertIn("レビュー開始前", reviews_text)
        self.assertIn("AGENTS.md", reviews_text)
        self.assertIn("実装済み", agents_text)
        self.assertIn("未確認", reviews_text)

    def test_reader_navigation_connects_quick_start_and_skill_operations(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        readme = (repository_root / "README.md").read_text(encoding="utf-8")
        getting_started = (repository_root / "docs" / "getting-started.md").read_text(
            encoding="utf-8"
        )
        skills_guide = (repository_root / "docs" / "agent-skills.md").read_text(
            encoding="utf-8"
        )
        docs_index = (repository_root / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("(docs/getting-started.md)", readme)
        self.assertIn("(.agents/skills/devconcord-bootstrap-from-design/SKILL.md)", readme)
        self.assertIn("(docs/agent-skills.md#skills)", readme)
        self.assertIn("(docs/agent-skills.md)", readme)
        self.assertIn("## 2. Agent Skillsをユーザー単位でインストールする", getting_started)
        self.assertIn("User Scope", getting_started)
        self.assertIn("(agent-skills.md)", getting_started)
        self.assertIn("devconcord-reference", readme)
        self.assertIn("devconcord-reference", getting_started)
        self.assertIn("devconcord-reference", docs_index)
        self.assertIn("自動呼び出しは保証されない", getting_started)
        self.assertIn("## 中断した操作の回復", skills_guide)
        self.assertIn("## 検証とトラブルシューティング", skills_guide)
        self.assertIn("(agent-skills.md)", docs_index)
        self.assertIn("## Skills", skills_guide)
        self.assertIn("## Skills非対応環境で手動利用", skills_guide)

    def test_business_skills_keep_reference_paths_and_cli_fallback(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skills_root = repository_root / ".agents" / "skills"
        for skill_dir in sorted(
            path
            for path in skills_root.iterdir()
            if path.is_dir()
            and path.name != "devconcord-reference"
        ):
            with self.subTest(skill=skill_dir.name):
                text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("## DevConcord References", text)
                self.assertIn("`devconcord-reference`", text)
                self.assertIn(f"--skill {skill_dir.name}", text)
                self.assertIn("scripts/manage_skills.py reference", text)
                self.assertIn("--revision installed", text)
                self.assertIn("--scope project --target", text)
                self.assertIn("If the common Skill cannot be selected", text)
                self.assertIn("Do not silently switch revisions", text)
                self.assertIn("If a required reference cannot be read, stop", text)
                self.assertIn("if it is optional", text)
                self.assertFalse(
                    (skill_dir / "references" / "local-devconcord.md").exists()
                )

        self.assertFalse(any(skills_root.glob("*/references/local-devconcord.md")))
        for skill_name, reference_name in (
            ("devconcord-adopt-guidance", "workflow.md"),
            ("devconcord-bootstrap-from-design", "workflow.md"),
            ("devconcord-sync-guidance", "workflow.md"),
            ("devconcord-generate-agent-guidance", "agents-md.md"),
            ("devconcord-generate-agent-guidance", "reviews-md.md"),
        ):
            self.assertTrue(
                (skills_root / skill_name / "references" / reference_name).is_file()
            )

    def test_common_reference_skill_uses_requesting_skill_identity(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill_dir = repository_root / ".agents" / "skills" / "devconcord-reference"
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: devconcord-reference", skill_text)
        self.assertIn("scripts/manage_skills.py reference", skill_text)
        self.assertIn("--skill", skill_text)
        self.assertIn("requesting Skill's name", skill_text)
        self.assertIn("Never substitute", skill_text)
        self.assertIn("does not identify which Skill revision", skill_text)
        self.assertIn("not guaranteed across agents or runtimes", skill_text)
        self.assertFalse((skill_dir / "references").exists())

    def test_rejects_invalid_metadata_and_name_mismatch(self) -> None:
        skill_dir = self.make_skill(
            "sample-skill",
            """---
name: Other
description: ""
unexpected-key: value
---
""",
        )

        errors = validate_skill_directory(skill_dir)

        self.assertTrue(any("unsupported/non-portable frontmatter keys" in error for error in errors))
        self.assertTrue(any("name must match" in error for error in errors))
        self.assertTrue(any("description must contain" in error for error in errors))

    def test_rejects_agent_specific_permission_frontmatter(self) -> None:
        skill_dir = self.make_skill(
            "sample-skill",
            """---
name: sample-skill
description: Use this Skill for a focused task.
allowed-tools: Shell
---
""",
        )

        errors = validate_skill_directory(skill_dir)

        self.assertTrue(any("allowed-tools permissions are not allowed" in error for error in errors))

    def test_rejects_malformed_frontmatter_and_broken_relative_links(self) -> None:
        malformed = self.make_skill(
            "malformed-skill",
            """---
name: [unterminated
description: Missing closing YAML
---
""",
        )
        self.assertTrue(
            any("invalid YAML frontmatter" in error for error in validate_skill_directory(malformed))
        )

        broken = self.make_skill("broken-skill")
        broken.joinpath("SKILL.md").write_text(
            """---
name: broken-skill
description: Use this Skill for a focused task.
---
[Missing](references/not-here.md)
""",
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "missing link target" in error
                for error in validate_skill_directory(broken)
            )
        )

    def test_rejects_references_that_escape_the_distributable_skill(self) -> None:
        skill_dir = self.make_skill(
            "escape-skill",
            """---
name: escape-skill
description: Use this Skill for a focused task.
---
[Outside package](../../outside.md)
""",
        )

        errors = validate_skill_directory(skill_dir)

        self.assertTrue(any("link escapes repository" in error for error in errors))

    def test_detects_case_insensitive_duplicate_names_across_roots(self) -> None:
        self.make_skill("sample-skill")
        second_root = self.root / ".claude" / "skills"
        second_skill = second_root / "SAMPLE-SKILL"
        second_skill.mkdir(parents=True)
        second_skill.joinpath("SKILL.md").write_text(
            "---\nname: SAMPLE-SKILL\ndescription: x\n---\n",
            encoding="utf-8",
        )

        errors = validate_repository_skills(self.root)

        self.assertTrue(any("conflicting same-name Skill" in error for error in errors))

    def test_distinguishes_identical_duplicate_copy_from_content_conflict(self) -> None:
        skill = self.make_skill("sample-skill")
        second_root = self.root / ".claude" / "skills"
        second_skill = second_root / "sample-skill"
        second_skill.mkdir(parents=True)
        (second_skill / "SKILL.md").write_bytes((skill / "SKILL.md").read_bytes())

        errors = validate_repository_skills(self.root)

        self.assertTrue(any("identical Skill copy" in error for error in errors))

    def test_identical_copy_is_allowed_only_for_disjoint_agent_exposure(self) -> None:
        skill = self.make_skill("sample-skill")
        second_root = self.root / ".claude" / "skills"
        second_skill = second_root / "sample-skill"
        second_skill.mkdir(parents=True)
        (second_skill / "SKILL.md").write_bytes((skill / "SKILL.md").read_bytes())
        manifest = self.root / ".devconcord" / "skills-manifest.json"
        manifest.parent.mkdir()
        first_record = self.manifest_record(skill)
        second_record = self.manifest_record(second_skill)
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "packages": {
                        ".agents/skills": {
                            "agents": ["codex"],
                            "skills": {"sample-skill": first_record},
                        },
                        ".claude/skills": {
                            "agents": ["claude"],
                            "skills": {"sample-skill": second_record},
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        errors = validate_repository_skills(self.root)
        self.assertFalse(any("duplicate" in error for error in errors))

        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "packages": {
                        ".agents/skills": {
                            "agents": ["codex", "copilot"],
                            "skills": {"sample-skill": first_record},
                        },
                        ".claude/skills": {
                            "agents": ["claude", "copilot"],
                            "skills": {"sample-skill": second_record},
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        errors = validate_repository_skills(self.root)
        self.assertTrue(any("identical Skill copy" in error for error in errors))

        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        manifest_data["duplicate_discovery_allowances"] = [
            {
                "skill": "sample-skill",
                "paths": [".agents/skills", ".claude/skills"],
            }
        ]
        manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
        errors = validate_repository_skills(self.root)
        self.assertFalse(any("identical Skill copy" in error for error in errors))

        unexpected_file = self.root / ".agents" / "skills" / "unexpected.txt"
        unexpected_file.write_text("not a Skill package\n", encoding="utf-8")
        errors = validate_repository_skills(self.root)
        self.assertTrue(any("unexpected non-Skill entry" in error for error in errors))
        unexpected_file.unlink()

        (second_skill / "SKILL.md").write_text(
            (second_skill / "SKILL.md").read_text(encoding="utf-8") + "\nLocal edit.\n",
            encoding="utf-8",
        )
        errors = validate_repository_skills(self.root)
        self.assertTrue(any("conflicting same-name Skill" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
