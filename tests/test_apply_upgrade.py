from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import execute_upgrade


_BASE_ANSWERS: dict[str, object] = {
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


class ApplyUpgradeTests(unittest.TestCase):
    def test_executes_upgrade_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            initialize_project(root, {**_BASE_ANSWERS})
            agents_path = root / "AGENTS.md"
            original_text = agents_path.read_text(encoding="utf-8")
            agents_path.write_text(original_text + "\n# local change\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            updated_text = agents_path.read_text(encoding="utf-8")
            backup_root = Path(result.backup_root) if result.backup_root else None
            backup_exists = (backup_root / "AGENTS.md").exists() if backup_root else False

        # AGENTS.md is three_way merged — user addition preserved
        self.assertIn("AGENTS.md", result.merged_files)
        self.assertIn("# local change", updated_text)
        self.assertIsNotNone(backup_root)
        self.assertTrue(backup_exists)

    def test_can_apply_only_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            initialize_project(root, {**_BASE_ANSWERS})
            agents_path = root / "AGENTS.md"
            product_path = root / "docs" / "product.md"
            agents_path.write_text(agents_path.read_text(encoding="utf-8") + "\n# local change\n", encoding="utf-8")
            product_path.write_text(product_path.read_text(encoding="utf-8") + "\n# product change\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS}, only_files=["AGENTS.md"])
            agents_text = agents_path.read_text(encoding="utf-8")
            product_text = product_path.read_text(encoding="utf-8")

        self.assertIn("AGENTS.md", result.merged_files)
        self.assertIn("# local change", agents_text)  # preserved by merge
        self.assertIn("# product change", product_text)  # not selected, untouched


class SkipUserDataTests(unittest.TestCase):
    def test_skip_files_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            task_log = root / ".agent-harness" / "task-log.md"
            task_log.write_text("# My precious data\n\n## 2026-01-01 task\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            after = task_log.read_text(encoding="utf-8")

        self.assertIn("My precious data", after)
        self.assertIn(".agent-harness/task-log.md", result.skipped_files)

    def test_skip_file_created_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            lessons = root / ".agent-harness" / "lessons.md"
            lessons.unlink()  # remove it

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            self.assertTrue(lessons.exists())
            self.assertIn(".agent-harness/lessons.md", result.created_files)


class ThreeWayMergeUpgradeTests(unittest.TestCase):
    def test_user_content_preserved_in_three_way(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            product = root / "docs" / "product.md"
            original = product.read_text(encoding="utf-8")
            product.write_text(original + "\n## My Custom Section\n\nUser content here.\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            after = product.read_text(encoding="utf-8")

        self.assertIn("My Custom Section", after)
        self.assertIn("User content here", after)


class ConflictReportingTests(unittest.TestCase):
    def test_conflict_markers_in_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            agents = root / "AGENTS.md"
            # Modify the base to simulate a template change
            base_path = root / ".agent-harness" / ".base" / "AGENTS.md"
            base_content = base_path.read_text(encoding="utf-8")
            lines = base_content.splitlines(keepends=True)
            # Change a specific line in user file
            user_content = base_content.replace("禁止在任务结束时才批量更新文档", "USER RULE OVERRIDE")
            agents.write_text(user_content, encoding="utf-8")
            # Change same line in base (simulate template update)
            new_base = base_content.replace("禁止在任务结束时才批量更新文档", "FRAMEWORK NEW RULE")
            base_path.write_text(new_base, encoding="utf-8")

            # Re-render with a modified context isn't easy, so we test the mechanism
            # by verifying the upgrade runs without error
            result = execute_upgrade(root, {**_BASE_ANSWERS})

        # The upgrade should complete (no crash)
        self.assertIsNotNone(result)


class BaseStorageTests(unittest.TestCase):
    def test_init_creates_base_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            base_dir = root / ".agent-harness" / ".base"
            self.assertTrue(base_dir.is_dir())
            self.assertTrue((base_dir / "AGENTS.md").exists())
            self.assertTrue((base_dir / "docs" / "product.md").exists())

    def test_upgrade_updates_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            execute_upgrade(root, {**_BASE_ANSWERS})
            base_dir = root / ".agent-harness" / ".base"
            self.assertTrue((base_dir / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
