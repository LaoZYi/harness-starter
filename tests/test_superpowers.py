from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project

_BASE_ANSWERS: dict[str, object] = {
    "project_name": "SP Test",
    "project_slug": "sp-test",
    "summary": "Superpowers integration test",
    "project_type": "backend-service",
    "language": "python",
    "package_manager": "pip",
    "run_command": "python -m app",
    "test_command": "pytest",
    "check_command": "ruff check .",
    "ci_command": "make ci",
    "deploy_target": "docker",
    "has_production": False,
    "sensitivity": "standard",
}

_PLACEHOLDER_RE = re.compile(r"\{\{\s*[a-z0-9_]+\s*\}\}")

_EXPECTED_COMMANDS = [
    "brainstorm.md", "write-plan.md", "tdd.md", "debug.md",
    "execute-plan.md", "subagent-dev.md", "dispatch-agents.md",
    "request-review.md", "receive-review.md", "use-worktrees.md",
    "finish-branch.md", "write-skill.md", "verify.md", "use-superpowers.md",
    # compound-engineering additions
    "ideate.md", "compound.md", "multi-review.md", "lfg.md",
    "git-commit.md", "todo.md",
    # agent-skills absorption
    "spec.md",
    # architecture-decision-record absorption
    "adr.md",
    # gstack additions
    "cso.md", "retro.md", "doc-release.md", "health.md", "careful.md",
    # knowledge management
    "lint-lessons.md",
    # self-evolution
    "evolve.md",
]


class SuperpowersDefaultEnabledTests(unittest.TestCase):
    def test_default_init_includes_superpowers_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            result = initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _EXPECTED_COMMANDS:
                self.assertTrue(
                    (commands_dir / cmd).exists(),
                    f"Missing superpowers command: {cmd}",
                )

    def test_default_init_includes_superpowers_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            rule = root / ".claude" / "rules" / "superpowers-workflow.md"
            self.assertTrue(rule.exists(), "Missing superpowers-workflow.md rule")
            content = rule.read_text(encoding="utf-8")
            self.assertIn("/brainstorm", content)
            self.assertIn("/tdd", content)
            self.assertIn("/adr", content)

    def test_default_init_creates_specs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            self.assertTrue((root / "docs" / "superpowers" / "specs").is_dir())

    def test_default_init_creates_decisions_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            self.assertTrue((root / "docs" / "decisions").is_dir())


class SuperpowersDisabledTests(unittest.TestCase):
    def test_disabled_skips_superpowers_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            answers = {**_BASE_ANSWERS, "superpowers": False}
            result = initialize_project(root, answers)
            commands_dir = root / ".claude" / "commands"
            for cmd in _EXPECTED_COMMANDS:
                self.assertFalse(
                    (commands_dir / cmd).exists(),
                    f"Superpowers command should not exist when disabled: {cmd}",
                )
            self.assertFalse(
                (root / ".claude" / "rules" / "superpowers-workflow.md").exists(),
            )
            self.assertFalse(
                (root / "docs" / "decisions").exists(),
                "docs/decisions/ should not exist when superpowers is disabled",
            )

    def test_disabled_still_has_common_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            answers = {**_BASE_ANSWERS, "superpowers": False}
            initialize_project(root, answers)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / ".agent-harness" / "project.json").exists())
            self.assertTrue((root / "docs" / "workflow.md").exists())


class SuperpowersPlaceholderTests(unittest.TestCase):
    def test_no_unfilled_placeholders_in_superpowers_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _EXPECTED_COMMANDS:
                path = commands_dir / cmd
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    unfilled = _PLACEHOLDER_RE.findall(content)
                    self.assertEqual(
                        unfilled, [],
                        f"Unfilled placeholders in {cmd}: {unfilled}",
                    )
            rule = root / ".claude" / "rules" / "superpowers-workflow.md"
            if rule.exists():
                content = rule.read_text(encoding="utf-8")
                unfilled = _PLACEHOLDER_RE.findall(content)
                self.assertEqual(unfilled, [], f"Unfilled placeholders in rule: {unfilled}")


class SuperpowersPresetTests(unittest.TestCase):
    def test_different_presets_produce_different_workflow_summary(self) -> None:
        summaries = {}
        for ptype in ("backend-service", "web-app", "cli-tool"):
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir) / "project"
                answers = {**_BASE_ANSWERS, "project_type": ptype}
                initialize_project(root, answers)
                rule = root / ".claude" / "rules" / "superpowers-workflow.md"
                summaries[ptype] = rule.read_text(encoding="utf-8")
        self.assertNotEqual(summaries["backend-service"], summaries["web-app"])
        self.assertNotEqual(summaries["web-app"], summaries["cli-tool"])


class SuperpowersIdempotentTests(unittest.TestCase):
    def test_double_init_with_force_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            answers = {**_BASE_ANSWERS}
            initialize_project(root, answers, force=True)
            first_content = {}
            for cmd in _EXPECTED_COMMANDS:
                path = root / ".claude" / "commands" / cmd
                first_content[cmd] = path.read_text(encoding="utf-8")

            initialize_project(root, answers, force=True)
            for cmd in _EXPECTED_COMMANDS:
                path = root / ".claude" / "commands" / cmd
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    first_content[cmd],
                    f"Idempotency failed for {cmd}",
                )


class SuperpowersDryRunTests(unittest.TestCase):
    def test_dry_run_lists_superpowers_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            result = initialize_project(root, {**_BASE_ANSWERS}, dry_run=True)
            sp_files = [f for f in result.written_files if "brainstorm" in f or "tdd" in f or "superpowers-workflow" in f]
            self.assertTrue(len(sp_files) >= 3, f"Expected superpowers files in dry run, got: {sp_files}")
            self.assertFalse((root / ".claude" / "commands" / "brainstorm.md").exists())


_COMPOUND_COMMANDS = ["ideate.md", "compound.md", "multi-review.md", "lfg.md", "git-commit.md", "todo.md"]
_GSTACK_COMMANDS = ["cso.md", "retro.md", "doc-release.md", "health.md", "careful.md"]


class CompoundEngineeringTests(unittest.TestCase):
    def test_compound_commands_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _COMPOUND_COMMANDS:
                self.assertTrue(
                    (commands_dir / cmd).exists(),
                    f"Missing compound command: {cmd}",
                )

    def test_workflow_rule_references_compound_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            rule = root / ".claude" / "rules" / "superpowers-workflow.md"
            content = rule.read_text(encoding="utf-8")
            self.assertIn("/ideate", content)
            self.assertIn("/compound", content)
            self.assertIn("/multi-review", content)
            self.assertIn("/lfg", content)

    def test_multi_review_has_discourse_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            content = (root / ".claude" / "commands" / "multi-review.md").read_text(encoding="utf-8")
            self.assertIn("Discourse", content)
            self.assertIn("AGREE", content)
            self.assertIn("CHALLENGE", content)
            self.assertIn("CONNECT", content)
            self.assertIn("SURFACE", content)
            self.assertIn("导航地图", content)

    def test_no_unfilled_placeholders_in_compound_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _COMPOUND_COMMANDS:
                path = commands_dir / cmd
                content = path.read_text(encoding="utf-8")
                unfilled = _PLACEHOLDER_RE.findall(content)
                self.assertEqual(unfilled, [], f"Unfilled placeholders in {cmd}: {unfilled}")


class GstackSkillsTests(unittest.TestCase):
    def test_gstack_commands_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _GSTACK_COMMANDS:
                self.assertTrue(
                    (commands_dir / cmd).exists(),
                    f"Missing gstack command: {cmd}",
                )

    def test_workflow_rule_references_gstack_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            rule = root / ".claude" / "rules" / "superpowers-workflow.md"
            content = rule.read_text(encoding="utf-8")
            self.assertIn("/cso", content)
            self.assertIn("/health", content)
            self.assertIn("/retro", content)

    def test_no_unfilled_placeholders_in_gstack_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _GSTACK_COMMANDS:
                path = commands_dir / cmd
                content = path.read_text(encoding="utf-8")
                unfilled = _PLACEHOLDER_RE.findall(content)
                self.assertEqual(unfilled, [], f"Unfilled placeholders in {cmd}: {unfilled}")


_ADR_COMMANDS = ["adr.md"]


class ArchitectureDecisionRecordTests(unittest.TestCase):
    def test_adr_command_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            commands_dir = root / ".claude" / "commands"
            for cmd in _ADR_COMMANDS:
                self.assertTrue(
                    (commands_dir / cmd).exists(),
                    f"Missing ADR command: {cmd}",
                )

    def test_adr_content_has_madr_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            content = (root / ".claude" / "commands" / "adr.md").read_text(encoding="utf-8")
            self.assertIn("MADR", content)
            self.assertIn("Proposed", content)
            self.assertIn("Accepted", content)
            self.assertIn("Superseded", content)
            self.assertIn("docs/decisions/", content)

    def test_adr_references_collaboration_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            content = (root / ".claude" / "commands" / "adr.md").read_text(encoding="utf-8")
            self.assertIn("/write-plan", content)
            self.assertIn("/compound", content)
            self.assertIn("/brainstorm", content)
            self.assertIn("/lfg", content)

    def test_no_unfilled_placeholders_in_adr_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            content = (root / ".claude" / "commands" / "adr.md").read_text(encoding="utf-8")
            unfilled = _PLACEHOLDER_RE.findall(content)
            self.assertEqual(unfilled, [], f"Unfilled placeholders in adr.md: {unfilled}")


class DecisionTreeCompletenessTests(unittest.TestCase):
    def test_use_superpowers_references_all_commands(self) -> None:
        """Every command (except use-superpowers itself) should appear in the decision tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            content = (root / ".claude" / "commands" / "use-superpowers.md").read_text(encoding="utf-8")
            for cmd in _EXPECTED_COMMANDS:
                skill_name = "/" + cmd.removesuffix(".md")
                if skill_name == "/use-superpowers":
                    continue  # doesn't need to reference itself
                self.assertIn(
                    skill_name, content,
                    f"use-superpowers.md does not reference {skill_name}",
                )


if __name__ == "__main__":
    unittest.main()
