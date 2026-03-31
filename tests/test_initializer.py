from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project


class InitializeProjectTests(unittest.TestCase):
    def test_generates_harness_files_from_answers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "acme-api"
            result = initialize_project(
                root,
                {
                    "project_name": "Acme API",
                    "project_slug": "acme-api",
                    "summary": "Handle internal automation requests.",
                    "project_type": "backend-service",
                    "language": "python",
                    "package_manager": "uv",
                    "run_command": "uv run python -m acme_api",
                    "test_command": "uv run pytest",
                    "check_command": "uv run ruff check .",
                    "ci_command": "make ci",
                    "deploy_target": "docker",
                    "has_production": True,
                    "sensitivity": "internal",
                },
                force=False,
            )

            agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
            project_json = json.loads((root / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            runbook_exists = (root / "docs" / "runbook.md").exists()
            summary_text = (root / ".agent-harness" / "init-summary.md").read_text(encoding="utf-8")

        self.assertTrue(result.written_files)
        self.assertIn("Acme API", agents_text)
        self.assertEqual(project_json["project_name"], "Acme API")
        self.assertIn("harness_version", project_json)
        self.assertEqual(project_json["commands"]["test"], "uv run pytest")
        self.assertTrue(runbook_exists)
        self.assertIn("初始化摘要", summary_text)
        self.assertIn("Acme API", summary_text)

    def test_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "preview-only"
            result = initialize_project(
                root,
                {
                    "project_name": "Preview Only",
                    "summary": "Preview harness output",
                    "project_type": "backend-service",
                    "language": "python",
                    "package_manager": "pip",
                    "run_command": "TODO",
                    "test_command": "TODO",
                    "check_command": "TODO",
                    "ci_command": "TODO",
                    "deploy_target": "未定",
                    "has_production": False,
                    "sensitivity": "standard",
                },
                dry_run=True,
            )

            root_exists = root.exists()
            agents_exists = (root / "AGENTS.md").exists()

        self.assertTrue(result.dry_run)
        self.assertTrue(result.written_files)
        self.assertFalse(root_exists)
        self.assertFalse(agents_exists)


if __name__ == "__main__":
    unittest.main()
