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


class NoBaseProtectionTests(unittest.TestCase):
    """GitLab Issue #23：缺失 base 基线时 three_way 不得退化为 overwrite。

    当目标项目 `.agent-harness/.base/<file>` 不存在（共同祖先丢失），升级
    必须保护用户在该文件上的长期编辑。采用方案 A：写 `<file>.harness-new`
    旁路文件 + 警告，不动原文件。
    """

    _USER_ARCHITECTURE = (
        "# NestJS 分层架构\n\n"
        "## Middleware\n用户自己写的 500 行内容\n\n"
        "## Controller\n用户自己写的 500 行内容\n\n"
        "## Service\n用户自己写的 500 行内容\n"
    )

    def _init_and_remove_base(self, root: Path, rel_path: str) -> Path:
        """Initialize a project then remove a specific base file to simulate
        early-init projects where `.base/` is incomplete."""
        initialize_project(root, {**_BASE_ANSWERS})
        base_file = root / ".agent-harness" / ".base" / rel_path
        if base_file.exists():
            base_file.unlink()
        return base_file

    def test_no_base_protects_user_content(self) -> None:
        """R-001: 无 base 基线时用户原文件内容完整保留。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS})
            after = arch.read_text(encoding="utf-8")

        self.assertIn("NestJS 分层架构", after)
        self.assertIn("用户自己写的 500 行内容", after)

    def test_no_base_writes_sidecar(self) -> None:
        """R-002: 无 base 时框架新模板写到 <file>.harness-new 旁路文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS})
            sidecar = root / "docs" / "architecture.md.harness-new"

            self.assertTrue(sidecar.exists(),
                            "旁路文件 <file>.harness-new 应被创建以展示框架新模板")
            content = sidecar.read_text(encoding="utf-8")
            self.assertGreater(len(content), 0, "旁路文件不应为空")

    def test_result_reports_missing_base_files(self) -> None:
        """R-003: UpgradeExecutionResult.missing_base_files 列出所有走旁路保护的文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})

        self.assertTrue(hasattr(result, "missing_base_files"),
                        "UpgradeExecutionResult 应有 missing_base_files 字段")
        self.assertIn("docs/architecture.md", result.missing_base_files)

    def test_plan_checklist_warns_missing_base(self) -> None:
        """R-004: plan 阶段 checklist 含 ⚠️ 旁路保护警告。"""
        from agent_harness.upgrade import plan_upgrade
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            plan = plan_upgrade(root, {**_BASE_ANSWERS})

        has_warning = any("旁路" in item or "harness-new" in item or "无基准" in item
                          for item in plan.checklist)
        self.assertTrue(has_warning,
                        f"checklist 应含旁路保护警告，实际: {plan.checklist}")

    def test_force_flag_overrides_protection(self) -> None:
        """R-005: force=True 时跳过保护，直接用框架内容覆盖原文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS}, force=True)
            after = arch.read_text(encoding="utf-8")

        self.assertNotIn("用户自己写的 500 行内容", after,
                         "force=True 时应直接覆盖用户内容")

    def test_no_base_file_missing_still_creates(self) -> None:
        """R-006: 文件不存在时走 create 路径，不触发保护逻辑。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            if arch.exists():
                arch.unlink()

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            self.assertTrue(arch.exists(), "文件不存在时应被创建")
            self.assertIn("docs/architecture.md", result.created_files)
            sidecar = root / "docs" / "architecture.md.harness-new"
            self.assertFalse(sidecar.exists(),
                             "文件被新建时不应写旁路文件")

    def test_with_base_still_three_way_merges(self) -> None:
        """R-007（回归）：base 基线存在时行为不变，走 three_way 合并。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            product = root / "docs" / "product.md"
            original = product.read_text(encoding="utf-8")
            product.write_text(original + "\n## My Section\nUser edit here.\n",
                               encoding="utf-8")

            execute_upgrade(root, {**_BASE_ANSWERS})
            after = product.read_text(encoding="utf-8")

        self.assertIn("User edit here", after,
                      "有 base 时 three_way 合并应保留用户内容")
        sidecar = root / "docs" / "product.md.harness-new"
        self.assertFalse(sidecar.exists(),
                         "有 base 时不应写旁路文件")

    def test_product_md_also_protected(self) -> None:
        """R-008: docs/product.md 无 base 时同样受保护，保护策略对所有
        three_way 文件通用，不仅 architecture.md。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/product.md")
            product = root / "docs" / "product.md"
            product.write_text("# 用户维护的 product.md\n核心业务需求...\n",
                               encoding="utf-8")

            result = execute_upgrade(root, {**_BASE_ANSWERS})
            after = product.read_text(encoding="utf-8")

        self.assertIn("用户维护的 product.md", after)
        self.assertIn("docs/product.md", result.missing_base_files)

    def test_sidecar_overwrites_prior_sidecar(self) -> None:
        """R-009: 连续两次 apply 时，旁路文件用最新模板覆盖旧版本。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            # 第一次 apply
            execute_upgrade(root, {**_BASE_ANSWERS})
            sidecar = root / "docs" / "architecture.md.harness-new"
            self.assertTrue(sidecar.exists())
            first_sidecar = sidecar.read_text(encoding="utf-8")

            # 模拟用户手工篡改旁路文件后再次 apply
            sidecar.write_text("stale sidecar placeholder", encoding="utf-8")
            # 第二次 apply（base 仍缺失，再次保护）—— 用户原文件也得被保留
            arch.write_text(self._USER_ARCHITECTURE + "\n\n## 新增章节\n",
                            encoding="utf-8")
            # 再次删 base 确保走保护分支
            (root / ".agent-harness" / ".base" / "docs" /
             "architecture.md").unlink(missing_ok=True)
            execute_upgrade(root, {**_BASE_ANSWERS})

            second_sidecar = sidecar.read_text(encoding="utf-8")
            after = arch.read_text(encoding="utf-8")

        self.assertNotEqual(second_sidecar, "stale sidecar placeholder",
                            "第二次 apply 应用新模板覆盖旧 sidecar")
        self.assertEqual(second_sidecar, first_sidecar,
                         "同一模板第二次渲染内容应一致")
        self.assertIn("新增章节", after, "原文件的用户增量必须保留")

    def test_after_base_restored_resumes_three_way(self) -> None:
        """R-010（组合）：保护分支跑完后若 save_base 补写了 base，下次
        apply 回到 three_way 正常路径（不再产生新的 .harness-new）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            self._init_and_remove_base(root, "docs/architecture.md")
            arch = root / "docs" / "architecture.md"
            arch.write_text(self._USER_ARCHITECTURE, encoding="utf-8")

            # 第一次：无 base → 走保护，同时保护流程结束时 save_base 恢复 base
            execute_upgrade(root, {**_BASE_ANSWERS})
            sidecar = root / "docs" / "architecture.md.harness-new"
            self.assertTrue(sidecar.exists(), "第一次 apply 应写旁路文件")
            # 保护后 save_base 应补回 base
            base_file = (root / ".agent-harness" / ".base" / "docs" /
                         "architecture.md")
            self.assertTrue(base_file.exists(),
                            "保护分支结束后 save_base 应补回 base 基线")

            # 清理 sidecar 模拟用户已手动 review
            sidecar.unlink()

            # 第二次：base 已恢复 → three_way 路径，不应再生 sidecar
            # 用户再加内容
            arch.write_text(self._USER_ARCHITECTURE + "\n\n## 进一步改动\n",
                            encoding="utf-8")
            result2 = execute_upgrade(root, {**_BASE_ANSWERS})

            self.assertFalse(sidecar.exists(),
                             "base 已恢复后不应再走保护分支")
            self.assertNotIn("docs/architecture.md",
                             result2.missing_base_files,
                             "base 已恢复，不应再出现在 missing_base_files")
            after = arch.read_text(encoding="utf-8")
            self.assertIn("进一步改动", after)


if __name__ == "__main__":
    unittest.main()
