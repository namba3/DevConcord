from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import agent_skills
from scripts.agent_skills import validate_repository_skills, validate_skill_directory


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

    def test_documentation_architecture_skill_is_valid_and_discoverable(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill_dir = (
            repository_root
            / ".agents"
            / "skills"
            / "documentation-architecture"
        )
        self.assertEqual(validate_skill_directory(skill_dir), [])
        skills_guide = (repository_root / "docs" / "agent-skills.md").read_text(
            encoding="utf-8"
        )
        docs_index = (repository_root / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("documentation-architecture", skills_guide)
        self.assertIn("documentation-design.md", docs_index)

    def test_bootstrap_workflow_reference_preserves_safety_and_scope_contracts(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skill = repository_root / ".agents" / "skills" / "bootstrap-from-design"
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
        skill = repository_root / ".agents" / "skills" / "adopt-guidance"
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
        skill = repository_root / ".agents" / "skills" / "sync-guidance"
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
        skill = repository_root / ".agents" / "skills" / "generate-agent-guidance"
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
        self.assertIn("(.agents/skills/bootstrap-from-design/SKILL.md)", readme)
        self.assertIn("(docs/agent-skills.md#skills)", readme)
        self.assertIn("(docs/agent-skills.md)", readme)
        self.assertIn("## 2. Agent Skillsをユーザー単位でインストールする", getting_started)
        self.assertIn("User Scope", getting_started)
        self.assertIn("(agent-skills.md)", getting_started)
        self.assertIn("## 中断した操作の回復", skills_guide)
        self.assertIn("## 検証とトラブルシューティング", skills_guide)
        self.assertIn("(agent-skills.md)", docs_index)
        self.assertIn("## Skills", skills_guide)
        self.assertIn("## Skills非対応環境で手動利用", skills_guide)

    def test_local_reference_guidance_is_compact_and_skill_specific(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        skills_root = repository_root / ".agents" / "skills"
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            with self.subTest(skill=skill_dir.name):
                reference = skill_dir / "references" / "local-devconcord.md"
                text = reference.read_text(encoding="utf-8")
                self.assertLessEqual(len(text.splitlines()), 20)
                self.assertIn(f"--skill {skill_dir.name}", text)
                self.assertIn("installed", text)
                self.assertNotIn("prompts/", text)

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
