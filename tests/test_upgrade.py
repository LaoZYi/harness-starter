from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import execute_upgrade, plan_upgrade, verify_upgrade


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
        self.assertIn("AGENTS.md", result.diffs)

    def test_can_limit_upgrade_plan_to_specific_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "upgrade-target"
            answers = {
                "project_name": "Upgrade Target",
                "project_slug": "upgrade-target",
                "summary": "Project to test selective planning",
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

            result = plan_upgrade(root, answers, only_files=["AGENTS.md"])

        self.assertEqual(result.update_files, ["AGENTS.md"])
        self.assertFalse(result.create_files)


_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Sentinel Target",
    "project_slug": "sentinel-target",
    "summary": "A real summary the user has filled in",
    "project_type": "backend-service",
    "language": "python",
    "package_manager": "uv",
    "run_command": "uv run python -m app",
    "test_command": "uv run pytest",
    "check_command": "uv run ruff check .",
    "ci_command": "make ci",
    "deploy_target": "docker",
    "has_production": False,
    "sensitivity": "internal",
}


class VerifyUpgradeSentinelTests(unittest.TestCase):
    """GitLab Issue #20：verify_upgrade 增加 sentinel 扫描作为防御兜底。

    如果 project.json 的字段已填写但渲染产物里仍出现模板 sentinel（说明
    _resolve_answers 读取 project.json 失败或变量替换遗漏），应发出 warning。
    """

    def test_warns_on_summary_sentinel_when_project_json_filled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            # 模拟历史 bug：产物里残留模板 sentinel（实际场景是 _resolve_answers
            # 跳过 project.json 导致 summary 落回 "待补充项目目标"）
            product = root / "docs" / "product.md"
            product.write_text(
                product.read_text(encoding="utf-8") + "\n\n待补充项目目标\n",
                encoding="utf-8",
            )

            warnings = verify_upgrade(root)
            sentinel_warnings = [w for w in warnings if "待补充" in w]
            self.assertTrue(
                sentinel_warnings,
                f"期待 sentinel warning 但未发现。全量 warnings: {warnings}",
            )

    def test_no_warning_when_project_json_field_also_empty(self) -> None:
        # project.json 的 summary 字段本身就是 sentinel（用户还没填）→ 不应 warning
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS, "summary": "待补充项目目标"})

            warnings = verify_upgrade(root)
            sentinel_warnings = [w for w in warnings if "待补充" in w and "summary" in w.lower()]
            self.assertFalse(
                sentinel_warnings,
                f"project.json 的 summary 为空 sentinel 时不应报 summary warning，实际: {sentinel_warnings}",
            )

    def test_no_warning_when_project_json_missing(self) -> None:
        # 极端场景：project.json 不存在（理论上 init 后一定有，但防御性覆盖）
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            pj = root / ".agent-harness" / "project.json"
            pj.unlink()

            warnings = verify_upgrade(root)
            # 不崩溃即可；sentinel 扫描应静默（没有真相源可对比）
            sentinel_warnings = [w for w in warnings if "待补充" in w]
            self.assertFalse(sentinel_warnings)

    def test_end_to_end_upgrade_with_project_json_renders_real_values(self) -> None:
        """端到端：init + 修改 project.json 模拟用户改名 + upgrade + verify 无 sentinel warning"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            initialize_project(root, {**_BASE_ANSWERS})
            # 用户修改 project.json（modeling Issue 的原始场景）
            pj = root / ".agent-harness" / "project.json"
            data = json.loads(pj.read_text(encoding="utf-8"))
            data["project_name"] = "测试管控平台"
            data["summary"] = "后端实际 summary"
            pj.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            # 重新 upgrade（不传 CLI 覆盖，模拟 harness upgrade apply 无参数）
            # answers 只传 project.json 里的核心字段（来自 _resolve_answers 的真实路径）
            answers = {
                k: data[k] for k in _BASE_ANSWERS if k in data
            }
            answers["has_production"] = data.get("has_production", False)
            execute_upgrade(root, answers)

            product = (root / "docs" / "product.md").read_text(encoding="utf-8")
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("测试管控平台", product + agents)
            warnings = verify_upgrade(root)
            sentinel_warnings = [w for w in warnings if "待补充" in w]
            self.assertFalse(
                sentinel_warnings,
                f"用户填好 project.json 后不应触发 sentinel warning。warnings: {warnings}",
            )
