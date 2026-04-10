"""Tests for project-type-specific rule inclusion/exclusion."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project

_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Type Test",
    "project_slug": "type-test",
    "summary": "Test project type differentiation.",
    "language": "python",
    "package_manager": "pip",
    "run_command": "make run",
    "test_command": "make test",
    "check_command": "make check",
    "ci_command": "make ci",
    "deploy_target": "docker",
    "has_production": False,
    "sensitivity": "standard",
}


def _init(project_type: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "target"
        result = initialize_project(root, {**_BASE_ANSWERS, "project_type": project_type}, force=True)
        return result.written_files


class ExcludeRulesTests(unittest.TestCase):
    """Phase 1: Verify exclude_rules in presets filters out irrelevant rules."""

    def test_backend_service_gets_all_rules(self) -> None:
        files = _init("backend-service")
        self.assertIn(".claude/rules/api.md", files)
        self.assertIn(".claude/rules/database.md", files)

    def test_library_excludes_api_and_database(self) -> None:
        files = _init("library")
        self.assertNotIn(".claude/rules/api.md", files)
        self.assertNotIn(".claude/rules/database.md", files)

    def test_cli_tool_excludes_api_and_database(self) -> None:
        files = _init("cli-tool")
        self.assertNotIn(".claude/rules/api.md", files)
        self.assertNotIn(".claude/rules/database.md", files)

    def test_data_pipeline_excludes_api(self) -> None:
        files = _init("data-pipeline")
        self.assertNotIn(".claude/rules/api.md", files)
        # data-pipeline keeps database rule (pipelines often touch DBs)
        self.assertIn(".claude/rules/database.md", files)

    def test_web_app_excludes_database(self) -> None:
        files = _init("web-app")
        self.assertNotIn(".claude/rules/database.md", files)
        # web-app keeps api rule (frontend calls APIs)
        self.assertIn(".claude/rules/api.md", files)

    def test_mobile_app_excludes_database(self) -> None:
        files = _init("mobile-app")
        self.assertNotIn(".claude/rules/database.md", files)

    def test_meta_excludes_api_and_database(self) -> None:
        files = _init("meta")
        self.assertNotIn(".claude/rules/api.md", files)
        self.assertNotIn(".claude/rules/database.md", files)

    def test_worker_keeps_all_rules(self) -> None:
        files = _init("worker")
        self.assertIn(".claude/rules/api.md", files)
        self.assertIn(".claude/rules/database.md", files)

    def test_universal_rules_always_present(self) -> None:
        """Rules that apply to ALL project types should always be generated."""
        for ptype in ("backend-service", "library", "cli-tool", "meta", "web-app"):
            files = _init(ptype)
            for rule in ("safety.md", "testing.md", "autonomy.md", "task-lifecycle.md",
                         "documentation-sync.md", "error-attribution.md"):
                self.assertIn(f".claude/rules/{rule}", files, f"{ptype} missing universal rule {rule}")


class TypeSpecificRulesTests(unittest.TestCase):
    """Phase 2: Verify each project type gets its own type-specific rule file."""

    def test_backend_service_gets_own_rule(self) -> None:
        files = _init("backend-service")
        self.assertIn(".claude/rules/backend-service.md", files)

    def test_web_app_gets_own_rule(self) -> None:
        files = _init("web-app")
        self.assertIn(".claude/rules/web-app.md", files)

    def test_cli_tool_gets_own_rule(self) -> None:
        files = _init("cli-tool")
        self.assertIn(".claude/rules/cli-tool.md", files)

    def test_worker_gets_own_rule(self) -> None:
        files = _init("worker")
        self.assertIn(".claude/rules/worker.md", files)

    def test_mobile_app_gets_own_rule(self) -> None:
        files = _init("mobile-app")
        self.assertIn(".claude/rules/mobile-app.md", files)

    def test_monorepo_gets_own_rule(self) -> None:
        files = _init("monorepo")
        self.assertIn(".claude/rules/monorepo.md", files)

    def test_data_pipeline_gets_own_rule(self) -> None:
        files = _init("data-pipeline")
        self.assertIn(".claude/rules/data-pipeline.md", files)

    def test_library_gets_own_rule(self) -> None:
        files = _init("library")
        self.assertIn(".claude/rules/library-api.md", files)

    def test_type_specific_rules_have_no_unfilled_placeholders(self) -> None:
        """Type-specific rules should have all placeholders replaced."""
        import re
        placeholder_re = re.compile(r"\{\{\s*[a-z_]+\s*\}\}")
        type_rule_map = {
            "backend-service": "backend-service.md",
            "web-app": "web-app.md",
            "cli-tool": "cli-tool.md",
            "worker": "worker.md",
            "mobile-app": "mobile-app.md",
            "monorepo": "monorepo.md",
            "data-pipeline": "data-pipeline.md",
            "library": "library-api.md",
        }
        for ptype, rule_file in type_rule_map.items():
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir) / "target"
                initialize_project(root, {**_BASE_ANSWERS, "project_type": ptype}, force=True)
                rule_path = root / ".claude" / "rules" / rule_file
                self.assertTrue(rule_path.exists(), f"{ptype} missing {rule_file}")
                content = rule_path.read_text(encoding="utf-8")
                unfilled = placeholder_re.findall(content)
                self.assertEqual(unfilled, [], f"{ptype}/{rule_file} has unfilled placeholders: {unfilled}")

    def test_type_specific_rule_not_generated_for_other_types(self) -> None:
        """backend-service rule should NOT appear in cli-tool output."""
        files = _init("cli-tool")
        self.assertNotIn(".claude/rules/backend-service.md", files)

    def test_backend_service_does_not_get_cli_tool_rule(self) -> None:
        files = _init("backend-service")
        self.assertNotIn(".claude/rules/cli-tool.md", files)


if __name__ == "__main__":
    unittest.main()
