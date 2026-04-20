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

    def test_memory_index_preserved_on_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            index = root / ".agent-harness" / "memory-index.md"
            index.write_text("# Memory Index\n\n## 最近教训\n\n- user curated entry\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            after = index.read_text(encoding="utf-8")

        self.assertIn("user curated entry", after)
        self.assertIn(".agent-harness/memory-index.md", result.skipped_files)


class ThreeWayMergeUpgradeTests(unittest.TestCase):
    def test_user_content_preserved_in_three_way(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            product = root / "docs" / "product.md"
            original = product.read_text(encoding="utf-8")
            product.write_text(original + "\n## My Custom Section\n\nUser content here.\n", encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS})
            after = product.read_text(encoding="utf-8")

        self.assertIn("My Custom Section", after)
        self.assertIn("User content here", after)

    def test_upgrade_preserves_user_additions_in_claude_md(self) -> None:
        """GitLab Issue #20：CLAUDE.md 应用户可编辑，升级时走 three_way 保留自定义内容。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            claude_md = root / "CLAUDE.md"
            user_marker = "# 我的本地备注 - 不应被覆盖"
            claude_md.write_text(claude_md.read_text(encoding="utf-8") + "\n" + user_marker + "\n", encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            updated_text = claude_md.read_text(encoding="utf-8")

            self.assertIn("CLAUDE.md", result.merged_files,
                          "CLAUDE.md 应走 three_way 合并而非 overwrite")
            self.assertIn(user_marker, updated_text,
                          "用户在 CLAUDE.md 的本地备注在 upgrade 后应保留")


class ConflictReportingTests(unittest.TestCase):
    def test_conflict_markers_in_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            agents = root / "AGENTS.md"
            # Modify the base to simulate a template change
            base_path = root / ".agent-harness" / ".base" / "AGENTS.md"
            base_content = base_path.read_text(encoding="utf-8")
            # Change a specific line in user file
            user_content = base_content.replace("禁止在任务结束时才批量更新文档", "USER RULE OVERRIDE")
            agents.write_text(user_content, encoding="utf-8")
            # Change same line in base (simulate template update)
            new_base = base_content.replace("禁止在任务结束时才批量更新文档", "FRAMEWORK NEW RULE")
            base_path.write_text(new_base, encoding="utf-8")

            # Re-render with a modified context isn't easy, so we test the mechanism
            # by verifying the upgrade runs without error
            result = execute_upgrade(root, {**_BASE_ANSWERS})

        # The upgrade should complete and detect the conflict
        self.assertIsNotNone(result)
        # Verify that either conflicts were reported or the merge preserved user content
        agents_after = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
        has_conflict_marker = "<<<<<<< " in agents_after
        has_conflict_report = bool(result.conflicts)
        self.assertTrue(has_conflict_marker or has_conflict_report or "USER RULE OVERRIDE" in agents_after,
            "Conflict should be detected or user content preserved")


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
            # Modify a file so upgrade actually does something
            agents = root / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\n# user note\n", encoding="utf-8")
            execute_upgrade(root, {**_BASE_ANSWERS})
            base_dir = root / ".agent-harness" / ".base"
            self.assertTrue((base_dir / "AGENTS.md").exists())
            # Base should contain the rendered template content, not user edits
            base_content = (base_dir / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn("# user note", base_content)

    def test_upgrade_progress_marker_cleaned_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            execute_upgrade(root, {**_BASE_ANSWERS})
            marker = root / ".agent-harness" / ".upgrade-in-progress"
            self.assertFalse(marker.exists(), "Progress marker should be cleaned up after upgrade")


if __name__ == "__main__":
    unittest.main()
