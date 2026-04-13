"""测试 Issue #17 GSD 吸收的各项模板与契约。

覆盖：
- StuckDetector 规则（task-lifecycle.md + tdd/debug 技能）
- /lint-lessons 矛盾检测节升级
- 需求矩阵三元映射（/spec + /write-plan + /verify）
- requirement-mapping-checklist 参考清单
- /plan-check 新技能 + 8 维度
- context-monitor hook 脚本 + settings.json 注册
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "src" / "agent_harness"
COMMON_RULES = PKG / "templates" / "common" / ".claude" / "rules"
COMMON_HOOKS = PKG / "templates" / "common" / ".claude" / "hooks"
COMMON_SETTINGS = PKG / "templates" / "common" / ".claude" / "settings.json.tmpl"
COMMON_REFS = PKG / "templates" / "common" / ".agent-harness" / "references"
SKILLS = PKG / "templates" / "superpowers" / ".claude" / "commands"


class StuckDetectorTests(unittest.TestCase):
    def test_task_lifecycle_contains_stuck_detector(self):
        text = (COMMON_RULES / "task-lifecycle.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("卡死检测", text)
        self.assertIn("连续 3 次", text)
        self.assertIn("StuckDetector", text)

    def test_tdd_skill_references_stuck_detector(self):
        text = (SKILLS / "tdd.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("StuckDetector", text)
        self.assertIn("连续 3 次 RED", text)

    def test_debug_skill_references_stuck_detector(self):
        text = (SKILLS / "debug.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("StuckDetector", text)
        self.assertIn("连续 3 次", text)


class LintLessonsContradictionTests(unittest.TestCase):
    def test_lint_lessons_has_contradiction_detection(self):
        text = (SKILLS / "lint-lessons.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("矛盾", text)
        self.assertIn("张力", text)
        self.assertIn("保留 A", text)
        self.assertIn("只检出", text)


class RequirementMappingTests(unittest.TestCase):
    def test_spec_has_requirement_matrix(self):
        text = (SKILLS / "spec.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("需求矩阵", text)
        self.assertIn("R-ID", text)
        self.assertIn("测试信号", text)

    def test_write_plan_requires_rid_annotation(self):
        text = (SKILLS / "write-plan.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("R-ID", text)
        self.assertIn("out-of-scope", text)

    def test_verify_has_rid_hard_check(self):
        text = (SKILLS / "verify.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("R-ID 覆盖", text)
        self.assertIn("satisfied", text)
        self.assertIn("out-of-scope", text)
        self.assertIn("missed", text)

    def test_requirement_mapping_checklist_exists(self):
        path = COMMON_REFS / "requirement-mapping-checklist.md.tmpl"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Nyquist", text)
        self.assertIn("Scope Reduction", text)


class PlanCheckSkillTests(unittest.TestCase):
    def test_plan_check_skill_exists(self):
        path = SKILLS / "plan-check.md.tmpl"
        self.assertTrue(path.is_file(), f"missing {path}")

    def test_plan_check_has_eight_dimensions(self):
        text = (SKILLS / "plan-check.md.tmpl").read_text(encoding="utf-8")
        for dim in [
            "需求覆盖", "任务原子性", "依赖排序", "文件作用域",
            "可验证性", "上下文适配", "缺口检测", "Nyquist",
        ]:
            self.assertIn(dim, text, f"plan-check missing dimension: {dim}")

    def test_plan_check_has_three_round_revision(self):
        text = (SKILLS / "plan-check.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("3 轮", text)
        self.assertIn("升级", text)


class ContextMonitorHookTests(unittest.TestCase):
    def test_hook_script_exists(self):
        path = COMMON_HOOKS / "context-monitor.sh.tmpl"
        self.assertTrue(path.is_file())

    def test_settings_registers_post_tool_use_hook(self):
        settings = json.loads(COMMON_SETTINGS.read_text(encoding="utf-8"))
        self.assertIn("PostToolUse", settings["hooks"])
        commands = [
            h["command"]
            for entry in settings["hooks"]["PostToolUse"]
            for h in entry["hooks"]
        ]
        self.assertTrue(
            any("context-monitor" in c for c in commands),
            f"PostToolUse does not include context-monitor, got {commands}",
        )

    def test_session_start_resets_counter(self):
        text = (COMMON_HOOKS / "session-start.sh.tmpl").read_text(encoding="utf-8")
        self.assertIn(".tool-call-count", text)

    def test_hook_counts_and_triggers_at_thresholds(self):
        """端到端：49→50 触发告警；skip 开关生效。"""
        hook = COMMON_HOOKS / "context-monitor.sh.tmpl"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / ".agent-harness").mkdir()
            (td_path / ".agent-harness" / ".tool-call-count").write_text("49")
            result = subprocess.run(
                ["bash", str(hook)], cwd=td, capture_output=True, text=True,
            )
            self.assertIn("50 次", result.stderr)
            count = (td_path / ".agent-harness" / ".tool-call-count").read_text().strip()
            self.assertEqual(count, "50")

            # skip 开关：不累加、不告警
            (td_path / ".agent-harness" / ".context-monitor-skip").touch()
            (td_path / ".agent-harness" / ".tool-call-count").write_text("99")
            result = subprocess.run(
                ["bash", str(hook)], cwd=td, capture_output=True, text=True,
            )
            self.assertNotIn("100", result.stderr)
            count = (td_path / ".agent-harness" / ".tool-call-count").read_text().strip()
            self.assertEqual(count, "99")


class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_rule_mentions_plan_check(self):
        text = (PKG / "templates" / "superpowers" / ".claude" / "rules"
                / "superpowers-workflow.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("/plan-check", text)

    def test_lfg_stage_3_includes_plan_check(self):
        text = (SKILLS / "lfg.md.tmpl").read_text(encoding="utf-8")
        self.assertIn("/plan-check", text)

    def test_use_superpowers_decision_tree_includes_plan_check(self):
        # Issue #27: decision tree + skill index are rendered from skills-registry.json.
        # /plan-check appears in skill index (process category) — that's the canonical
        # location now (decision tree only lists skills with explicit decision_tree_label).
        import sys as _sys
        _sys.path.insert(0, str(PKG.parent))
        from agent_harness.skills_registry import load_registry, render_skill_index_by_phase
        registry = load_registry(PKG / "templates" / "superpowers")
        self.assertIn("/plan-check", render_skill_index_by_phase(registry))


if __name__ == "__main__":
    unittest.main()
