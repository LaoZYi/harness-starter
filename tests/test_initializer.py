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


    def test_no_unfilled_placeholders_in_output(self) -> None:
        import logging
        import re

        # 捕获 templating 模块的 WARNING —— 未知 key 被静默替换成空字符串，
        # 会让静态扫 `{{xxx}}` 残留的断言漏掉（因为 `{{base_branch}}` 类未知 key
        # 渲染后不留残骸）。捕获 WARNING 能真正锁定"context 与模板 key 匹配"。
        with self.assertNoLogs("agent_harness.templating", level=logging.WARNING):
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir) / "complete-check"
                initialize_project(
                    root,
                    {
                        "project_name": "Complete Check",
                        "project_slug": "complete-check",
                        "summary": "Verify all placeholders are filled.",
                        "project_type": "backend-service",
                        "language": "python",
                        "package_manager": "pip",
                        "run_command": "python -m app",
                        "test_command": "pytest",
                        "check_command": "ruff check .",
                        "ci_command": "make ci",
                        "deploy_target": "docker",
                        "has_production": True,
                        "sensitivity": "internal",
                    },
                    force=True,
                )
                pattern = re.compile(r"{{\s*[a-z0-9_]+\s*}}")
                for path in root.rglob("*"):
                    if path.is_file():
                        content = path.read_text(encoding="utf-8")
                        matches = pattern.findall(content)
                        self.assertFalse(matches, f"{path.relative_to(root)} 包含未填充的占位符: {matches}")

    def test_idempotent_init_with_force(self) -> None:
        answers = {
            "project_name": "Idempotent",
            "project_slug": "idempotent",
            "summary": "Test idempotency.",
            "project_type": "backend-service",
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
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "idem"
            initialize_project(root, answers, force=True)
            # Second init discovers generated dirs, so run twice to stabilize
            initialize_project(root, answers, force=True)
            second = {p.relative_to(root): p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
            initialize_project(root, answers, force=True)
            third = {p.relative_to(root): p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file()}
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
