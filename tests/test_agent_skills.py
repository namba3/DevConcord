from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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

    def test_accepts_standard_portable_skill_metadata(self) -> None:
        skill_dir = self.make_skill("sample-skill")

        self.assertEqual(validate_skill_directory(skill_dir), [])

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
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "packages": {
                        ".agents/skills": {"agents": ["codex"], "skills": {}},
                        ".claude/skills": {"agents": ["claude"], "skills": {}},
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
                        ".agents/skills": {"agents": ["codex", "copilot"], "skills": {}},
                        ".claude/skills": {"agents": ["claude", "copilot"], "skills": {}},
                    },
                }
            ),
            encoding="utf-8",
        )
        errors = validate_repository_skills(self.root)
        self.assertTrue(any("identical Skill copy" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
