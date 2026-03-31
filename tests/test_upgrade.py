from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import plan_upgrade


class UpgradePlanTests(unittest.TestCase):
    def test_classifies_updates_and_unchanged_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            answers = {
                "project_name": "Upgrade Target",
                "project_slug": "upgrade-target",
                "summary": "Project to test upgrade planning",
                "project_type": "backend-service",
                "language": "python",
                "package_manager": "uv",
                "run_command": "uv run python -m upgrade_target",
                "test_command": "uv run pytest",
                "check_command": "uv run ruff check .",
                "ci_command": "make ci",
                "deploy_target": "docker",
                "has_production": False,
                "sensitivity": "internal",
            }
            initialize_project(root, answers)
            agents_path = root / "AGENTS.md"
            agents_path.write_text(agents_path.read_text(encoding="utf-8") + "\n# local change\n", encoding="utf-8")

            result = plan_upgrade(root, answers)

        self.assertIn("AGENTS.md", result.update_files)
        self.assertIn("docs/product.md", result.unchanged_files)
        self.assertTrue(result.checklist)
