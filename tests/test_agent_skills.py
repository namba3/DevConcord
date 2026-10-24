from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.agent_skills import (
    _portable_skill_fingerprint,
    validate_official_skill_names,
    validate_skill_directory,
    validate_skill_roots,
)


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
PACKAGE = SKILLS_ROOT / "devconcord"
MODULES = PACKAGE / "references" / "modules"
EXPECTED_MODULES = {
    "design": {
        "devconcord-design-orchestration",
        "devconcord-ux-functional-design",
    },
    "quality": {
        "devconcord-design-performance",
        "devconcord-design-robustness",
        "devconcord-design-replaceability",
        "devconcord-design-security",
        "devconcord-observability-design",
        "devconcord-documentation-architecture",
    },
    "development": {
        "devconcord-development-orchestration",
        "devconcord-issue-driven-development",
        "devconcord-implementation-planning",
        "devconcord-decision-resolution",
    },
    "verification": {
        "devconcord-test-design",
        "devconcord-repository-review",
        "devconcord-gap-analysis",
        "devconcord-root-cause-analysis",
    },
    "lifecycle": {
        "devconcord-compatibility-migration",
        "devconcord-release-engineering",
        "devconcord-dependency-governance",
    },
    "management": {
        "devconcord-bootstrap-from-design",
        "devconcord-adopt-guidance",
        "devconcord-sync-guidance",
        "devconcord-generate-agent-guidance",
        "devconcord-reference",
    },
    "evaluation": {"devconcord-agent-behavior-evaluation"},
}


def module(category: str, name: str) -> Path:
    return MODULES / category / name / "module.md"


class UnifiedSkillArchitectureTests(unittest.TestCase):
    def test_only_one_public_official_skill_is_discoverable(self) -> None:
        public = sorted(path.name for path in SKILLS_ROOT.iterdir() if (path / "SKILL.md").is_file())
        self.assertEqual(public, ["devconcord"])
        self.assertEqual(validate_official_skill_names(SKILLS_ROOT), [])
        self.assertEqual(validate_skill_directory(PACKAGE), [])
        self.assertEqual(validate_skill_roots([SKILLS_ROOT]), [])

    def test_review_guidance_uses_unified_logical_commands(self) -> None:
        review = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        routing = (PACKAGE / "references" / "routing.md").read_text(encoding="utf-8")
        section = review.split("## 指摘の基準", maxsplit=1)[1]
        guidance = section.split("\n## ", maxsplit=1)[0]
        for command in (
            "review repository",
            "review gap",
            "verify test-design",
            "develop implementation-plan",
            "quality security",
            "lifecycle compatibility",
            "lifecycle release",
            "lifecycle dependencies",
            "decide scan",
            "decide investigate",
            "decide compare",
            "decide recommend",
            "decide resolve",
            "develop unblock",
        ):
            self.assertIn(f"`devconcord {command}`", guidance)
            self.assertIn(f"`{command}`", routing)
        self.assertIn("公式公開Skillは `devconcord` の一つ", guidance)
        self.assertIn("Development Orchestrationの標準品質ゲートに追加せず", guidance)

    def test_reference_cli_uses_public_package_identity_for_all_internal_workflows(self) -> None:
        package_docs = list((PACKAGE / "references" / "modules").rglob("*.md"))
        security = module("quality", "devconcord-design-security").read_text(encoding="utf-8")
        self.assertIn("requesting workflow context", security)
        self.assertIn("--skill devconcord", security)
        self.assertNotIn("this workflow's name as `--skill`", security)
        for path in package_docs:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotRegex(
                text,
                r"(?:workflow|module)\s+name\s+as\s+`?--skill|`--skill`\s+(?:is|should be)\s+the\s+(?:workflow|module)",
                msg=str(path.relative_to(PACKAGE)),
            )

    def test_every_legacy_workflow_is_an_internal_module_without_skill_frontmatter(self) -> None:
        discovered = {
            category: {path.name for path in (MODULES / category).iterdir() if path.is_dir()}
            for category in EXPECTED_MODULES
        }
        self.assertEqual(discovered, EXPECTED_MODULES)
        for category, names in EXPECTED_MODULES.items():
            for name in names:
                with self.subTest(module=name):
                    path = module(category, name)
                    text = path.read_text(encoding="utf-8")
                    self.assertTrue(text.strip())
                    self.assertFalse(text.startswith("---\n"))
                    self.assertFalse((path.parent / "SKILL.md").exists())
        self.assertEqual(sum(map(len, discovered.values())), 25)

    def test_router_covers_explicit_commands_and_risk_proportional_selection(self) -> None:
        router = (PACKAGE / "references" / "routing.md").read_text(encoding="utf-8")
        skill = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        for command in (
            "design explore", "design create", "design evolve",
            "develop plan", "develop issue", "develop batch", "develop iterate", "develop stabilize",
            "decide scan", "decide investigate", "decide compare", "decide recommend",
            "decide resolve", "develop unblock",
            "review repository", "review impact", "review gap", "verify test-design",
            "diagnose root-cause", "quality performance", "quality robustness",
            "quality security", "quality replaceability", "quality observability",
            "quality ux", "quality documentation", "lifecycle compatibility",
            "lifecycle release", "lifecycle dependencies", "manage bootstrap",
            "manage adopt", "manage sync", "manage guidance", "manage reference", "evaluate agent",
        ):
            with self.subTest(command=command):
                self.assertIn(f"`{command}`", router)
        for contract in (
            "Natural-language", "unknown", "ambiguous", "Risk-proportional",
            "module selection never expands permission", "not an operating-system command",
        ):
            self.assertIn(contract.lower(), (router + skill).lower())

    def test_optional_lifecycle_workflows_are_not_standard_quality_gates(self) -> None:
        orchestration = module("development", "devconcord-development-orchestration").read_text(
            encoding="utf-8"
        )
        unified = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "not standard-loop steps", "not a gate", "do not stop unrelated work",
            "does not authorize an automatic handoff",
        ):
            self.assertIn(phrase, orchestration.lower())
        for name in (
            "devconcord-compatibility-migration",
            "devconcord-release-engineering",
            "devconcord-dependency-governance",
        ):
            self.assertIn(name, unified)
        self.assertIn("workflows are optional", unified.lower())

    def test_decision_resolution_contract_keeps_records_authority_and_issue_state_distinct(self) -> None:
        decision = module("development", "devconcord-decision-resolution")
        module_text = decision.read_text(encoding="utf-8")
        workflow_text = (decision.parent / "references" / "workflow.md").read_text(encoding="utf-8")
        issue_guide = (ROOT / "docs" / "work-management" / "issue-tracking.md").read_text(
            encoding="utf-8"
        )
        issue_template = (ROOT / "docs" / "work-management" / "templates" / "issue-register.md").read_text(
            encoding="utf-8"
        )
        for state in ("未整理", "調査中", "判断可能", "承認待ち", "解決済み", "保留"):
            with self.subTest(state=state):
                self.assertIn(state, module_text + workflow_text + issue_guide)
        for contract in (
            "DEC-####", "not another decision record", "recommendation is not approval",
            "does not complete or automatically unblock", "Resolved", "Bypassed Safely",
            "Escalated", "reconsideration", "decision-changing evidence",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract.lower(), (module_text + workflow_text).lower())
        self.assertIn("DEC-0001", issue_template)
        self.assertIn("書式例", issue_template)
        self.assertIn("実在の未決事項として登録しない", issue_template)
        self.assertIn("Related DEC ID", (ROOT / "docs" / "work-management" / "templates" / "handoff.md").read_text(
            encoding="utf-8"
        ))
        self.assertIn("Decision Resolution & Unblocking", issue_guide)

    def test_issue_record_updates_do_not_force_quality_rescoring_and_fixture_is_present(self) -> None:
        issue_guide = (ROOT / "docs" / "work-management" / "issue-tracking.md").read_text(
            encoding="utf-8"
        )
        update_section = issue_guide.split("## 5. 課題表の更新手順", maxsplit=1)[1].split(
            "## 6. ", maxsplit=1
        )[0]
        issue_module = module("development", "devconcord-issue-driven-development").read_text(
            encoding="utf-8"
        )
        self.assertIn("通常のIssue/DEC状態", update_section)
        self.assertIn("全10軸を再採点しない", update_section)
        self.assertIn("明示的な完成度監査・リリース判定", update_section)
        normalized_issue_module = " ".join(issue_module.lower().split())
        self.assertIn("do not change a completion score for routine work", normalized_issue_module)

        fixture = ROOT / "tests" / "integration" / "fixtures" / "decision-resolution"
        for relative in (
            "README.md", "docs/requirements.md", "docs/adr.md", "docs/issues.md",
            "docs/risks.md", "docs/handoff.md", "src/exporter.py", "tests/test_exporter.py",
        ):
            with self.subTest(fixture_file=relative):
                self.assertTrue((fixture / relative).is_file())
        issues = (fixture / "docs" / "issues.md").read_text(encoding="utf-8")
        self.assertIn("DEC-1001", issues)
        self.assertIn("ISS-1003", issues)
        self.assertIn("Product owner", issues)

    def test_development_handoff_is_optional_evidence_context_not_a_parallel_ledger(self) -> None:
        template = ROOT / "docs" / "work-management" / "templates" / "handoff.md"
        issue_guide = (ROOT / "docs" / "work-management" / "issue-tracking.md").read_text(
            encoding="utf-8"
        )
        common = (ROOT / "docs" / "common" / "ai-assisted-development.md").read_text(
            encoding="utf-8"
        )
        issue_module = module("development", "devconcord-issue-driven-development").read_text(
            encoding="utf-8"
        )
        issue_workflow = (
            module("development", "devconcord-issue-driven-development").parent
            / "references" / "workflow.md"
        ).read_text(encoding="utf-8")
        orchestration = module("development", "devconcord-development-orchestration").read_text(
            encoding="utf-8"
        )
        orchestration_workflow = (
            module("development", "devconcord-development-orchestration").parent
            / "references" / "workflow.md"
        ).read_text(encoding="utf-8")
        template_text = template.read_text(encoding="utf-8")
        agents_guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        review_guidance = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        guidance_generation = (
            MODULES / "management" / "devconcord-generate-agent-guidance"
            / "references" / "agents-md.md"
        ).read_text(encoding="utf-8")
        checklist_heading = issue_guide.index("## 7. 運用チェックリスト")
        handoff_heading = issue_guide.index("## 8. 開発引継ぎ（HANDOFF.md）")
        checklist_item = issue_guide.index("- [ ] 冒頭の完成度評価")

        for section in (
            "Baseline", "Current Focus", "Verified Progress", "Pending Verification",
            "Important Findings", "Blockers / Approval Boundaries", "Next Safe Actions",
            "Stop Conditions",
        ):
            with self.subTest(template_section=section):
                self.assertIn(f"## {section}", template_text)
        for phrase in (
            "唯一の正本", "複製しません", "再開時", "競合", "権限", "更新",
        ):
            with self.subTest(issue_contract=phrase):
                self.assertIn(phrase, issue_guide)
        self.assertLess(checklist_heading, checklist_item)
        self.assertLess(checklist_item, handoff_heading)
        for phrase in (
            "optional", "not a required loop artifact", "quality gate",
            "finite budget", "evidence freshness", "current user's",
        ):
            with self.subTest(orchestration_contract=phrase):
                self.assertIn(phrase.lower(), (common + orchestration + orchestration_workflow).lower())
        self.assertIn("Plan mode", (issue_module + issue_workflow))
        self.assertIn("never modify", issue_workflow)
        self.assertIn("concurrent edits", orchestration_workflow)
        self.assertIn("not overwrite", orchestration_workflow)
        self.assertIn("HANDOFF", agents_guidance)
        self.assertIn("検証", agents_guidance)
        self.assertIn("同じディレクトリ", template_text)
        self.assertIn("beside the target's authoritative", issue_module.lower())
        self.assertIn("same directory as the", orchestration_workflow.lower())
        self.assertIn("課題表と同じディレクトリ", issue_guide)
        self.assertIn("課題表と同じディレクトリ", guidance_generation)
        self.assertIn("課題表と同じディレクトリ", review_guidance)

    def test_module_contracts_and_supporting_references_are_retained(self) -> None:
        contracts = {
            ("quality", "devconcord-design-security"): ("trust boundary", "長期秘密"),
            ("design", "devconcord-ux-functional-design"): ("user task", "acceptance"),
            ("development", "devconcord-issue-driven-development"): ("issue register", "verification"),
            ("verification", "devconcord-repository-review"): ("evidence", "severity"),
            ("lifecycle", "devconcord-compatibility-migration"): ("compatibility risk", "rollback"),
            ("management", "devconcord-sync-guidance"): ("baseline", "local edits"),
            ("evaluation", "devconcord-agent-behavior-evaluation"): ("discovery", "execution"),
        }
        for (category, name), phrases in contracts.items():
            text = module(category, name).read_text(encoding="utf-8").lower()
            for phrase in phrases:
                with self.subTest(module=name, phrase=phrase):
                    self.assertIn(phrase, text)
        for path in MODULES.rglob("*.md"):
            if path.name == "module.md":
                continue
            self.assertTrue(path.is_file())

    def test_specialized_workflow_authority_and_evidence_contracts(self) -> None:
        contracts = {
            ("design", "devconcord-design-orchestration"): (
                "explore", "do not edit", "explicit approval", "stop when",
            ),
            ("development", "devconcord-development-orchestration"): (
                "plan", "iterate", "stabilize", "budget", "quality gates", "stop",
            ),
            ("development", "devconcord-issue-driven-development"): (
                "issue register", "priority", "dependencies", "completion", "evidence",
            ),
            ("verification", "devconcord-test-design"): (
                "independent", "oracle", "acceptance", "executed test", "risk",
            ),
            ("verification", "devconcord-repository-review"): (
                "read-only", "evidence", "severity", "regression", "unverified",
            ),
            ("verification", "devconcord-root-cause-analysis"): (
                "symptom", "falsifiable", "hypothesis", "diagnostic", "repair",
            ),
            ("quality", "devconcord-design-security"): (
                "trust boundary", "asset", "threat", "invariant", "verification",
            ),
            ("quality", "devconcord-design-robustness"): (
                "failure", "concurrency", "cancellation", "recovery", "invariant",
            ),
            ("management", "devconcord-bootstrap-from-design"): (
                "source", "provenance", "existing", "do not invent",
            ),
            ("management", "devconcord-adopt-guidance"): (
                "source", "preserve", "provenance", "do not imply",
            ),
            ("management", "devconcord-sync-guidance"): (
                "baseline", "local edits", "do not overwrite", "same commit",
            ),
            ("management", "devconcord-generate-agent-guidance"): (
                "review.md", "agents.md", "availability", "never install",
            ),
            ("lifecycle", "devconcord-compatibility-migration"): (
                "compatibility risk", "migration", "rollback", "irreversible",
            ),
            ("lifecycle", "devconcord-release-engineering"): (
                "explicitly authorized", "rollback", "candidate", "never publish",
            ),
            ("lifecycle", "devconcord-dependency-governance"): (
                "update", "license", "supply-chain", "optional",
            ),
        }
        for (category, name), phrases in contracts.items():
            entry = module(category, name)
            text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(entry.parent.rglob("*.md"))
            ).lower()
            for phrase in phrases:
                with self.subTest(module=name, phrase=phrase):
                    self.assertIn(phrase.lower(), text)

        orchestration = module("development", "devconcord-development-orchestration").read_text(
            encoding="utf-8"
        ).lower()
        for phrase in (
            "not standard-loop steps", "not a gate", "do not stop unrelated work",
            "non-use as a defect", "does not authorize an automatic handoff",
        ):
            self.assertIn(phrase, orchestration)

    def test_official_name_rule_does_not_apply_to_external_skill_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "vendor-example"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: vendor-example\ndescription: External test skill.\n---\n\nBody.\n",
                encoding="utf-8",
            )
            from scripts.agent_skills import validate_skill_directory

            self.assertEqual(validate_skill_directory(skill), [])
            self.assertEqual(validate_skill_roots([root]), [])
            self.assertTrue(validate_official_skill_names(root))

    def test_duplicate_fingerprints_match_management_hash_and_ignore_empty_directories(self) -> None:
        from scripts.manage_skills import _portable_tree_digest

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            first_root = project / ".agents" / "skills"
            second_root = project / ".claude" / "skills"
            first = first_root / "vendor-example"
            second = second_root / "vendor-example"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            content = (
                "---\nname: vendor-example\ndescription: Example external workflow.\n---\n\nBody.\n"
            )
            for skill in (first, second):
                (skill / "SKILL.md").write_text(content, encoding="utf-8")
                (skill / "references").mkdir()
                (skill / "references" / "details.md").write_text("Details.\n", encoding="utf-8")
                localized = skill / "references" / "詳細"
                localized.mkdir()
                (localized / "guide.md").write_text("Localized path.\n", encoding="utf-8")
                executable = skill / "bin" / "tool"
                executable.parent.mkdir()
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (second / "empty" / "nested").mkdir(parents=True)

            executable_files = ("bin/tool",)
            first_digest = _portable_skill_fingerprint(first, executable_files)
            second_digest = _portable_skill_fingerprint(second, executable_files)
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first_digest, _portable_tree_digest(first, executable_files))
            self.assertEqual(second_digest, _portable_tree_digest(second, executable_files))
            self.assertEqual(
                validate_skill_roots(
                    [first_root, second_root],
                    duplicate_allowances={
                        ("vendor-example", (".agents/skills", ".claude/skills"))
                    },
                ),
                [],
            )

    def test_docs_and_cli_refer_to_the_unified_package(self) -> None:
        guide = (ROOT / "docs" / "agent-skills.md").read_text(encoding="utf-8")
        source_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        cli = (ROOT / "scripts" / "manage_skills.py").read_text(encoding="utf-8")
        self.assertIn("--skill devconcord", guide)
        self.assertIn("migrate --scope user", guide)
        self.assertIn("--apply", guide)
        self.assertNotRegex(guide, r"(?m)^\s+--skills\s+devconcord-")
        self.assertIn("Unified Skill", source_index)
        self.assertIn("--skills selection is retired", cli)


if __name__ == "__main__":
    unittest.main()
