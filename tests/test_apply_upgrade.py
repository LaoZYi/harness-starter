from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import execute_upgrade


class ApplyUpgradeTests(unittest.TestCase):
    def test_executes_upgrade_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            answers = {
                "project_name": "Upgrade Target",
                "project_slug": "upgrade-target",
                "summary": "Project to test upgrade apply",
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
            original_text = agents_path.read_text(encoding="utf-8")
            agents_path.write_text(original_text + "\n# local change\n", encoding="utf-8")

            result = execute_upgrade(root, answers)
            updated_text = agents_path.read_text(encoding="utf-8")
            backup_root = Path(result.backup_root) if result.backup_root else None
            backup_exists = (backup_root / "AGENTS.md").exists() if backup_root else False

        self.assertIn("AGENTS.md", result.updated_files)
        self.assertNotIn("# local change", updated_text)
        self.assertIsNotNone(backup_root)
        self.assertTrue(backup_exists)

    def test_can_apply_only_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            answers = {
                "project_name": "Upgrade Target",
                "project_slug": "upgrade-target",
                "summary": "Project to test selective upgrade apply",
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
            product_path = root / "docs" / "product.md"
            agents_path.write_text(agents_path.read_text(encoding="utf-8") + "\n# local change\n", encoding="utf-8")
            product_path.write_text(product_path.read_text(encoding="utf-8") + "\n# product change\n", encoding="utf-8")

            result = execute_upgrade(root, answers, only_files=["AGENTS.md"])
            agents_text = agents_path.read_text(encoding="utf-8")
            product_text = product_path.read_text(encoding="utf-8")

        self.assertEqual(result.updated_files, ["AGENTS.md"])
        self.assertNotIn("# local change", agents_text)
        self.assertIn("# product change", product_text)


if __name__ == "__main__":
    unittest.main()
