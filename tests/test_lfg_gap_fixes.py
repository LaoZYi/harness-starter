"""Contract tests for /lfg gap fixes (2026-04-13).

Background: 评估 /lfg 能力发挥度时识别出 4 个 Gap + 1 个 meta 项目类型路由
缺失。这些测试锁定修复后的关键字必须出现在 lfg.md.tmpl 的对应阶段，
防止后续编辑时回归丢失。

每条测试只断言"关键词出现在预期章节范围内"，用宽松正则而非精确字符串，
避免未来措辞微调误伤。
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LFG = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands" / "lfg.md.tmpl"


def _section(text: str, start_marker: str, end_marker: str | None = None) -> str:
    """Return the slice between two markers (end exclusive). Raises if start missing."""
    start = text.find(start_marker)
    if start < 0:
        raise AssertionError(f"start marker not found: {start_marker!r}")
    if end_marker is None:
        return text[start:]
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise AssertionError(f"end marker not found after start: {end_marker!r}")
    return text[start:end]


class LFGGapFixesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = LFG.read_text(encoding="utf-8")

    # Gap: meta 项目类型路由（阶段 0.1）
    def test_stage_0_1_routes_meta_project_type(self) -> None:
        section = _section(self.text, "### 0.1 理解任务", "### 0.2 加载历史知识")
        self.assertRegex(
            section,
            r"project_type.*meta|meta.*project_type",
            "阶段 0.1 必须检测 project.json 的 project_type == meta 并路由",
        )
        self.assertIn(
            "/meta-sync", section,
            "meta 项目需被引导到 /meta-* 命令集",
        )

    # Gap 4: plugins 自定义规则读取（阶段 0.2 必读）
    def test_stage_0_2_reads_harness_plugins_rules(self) -> None:
        section = _section(self.text, "### 0.2 加载历史知识", "### 0.3 评估复杂度")
        self.assertRegex(
            section,
            r"\.harness-plugins/rules",
            "阶段 0.2 必读列表必须包含 .harness-plugins/rules/ 扫描",
        )

    # Gap 5: 并行子 agent 隔离提示（阶段 4.1）
    def test_stage_4_1_enforces_agent_diary_isolation(self) -> None:
        section = _section(self.text, "#### 4.1 按步执行", "#### 4.2 遇到问题时的处理")
        self.assertRegex(
            section,
            r"agent\s+init",
            "阶段 4.1 必须提示主 agent 为 dispatch-agents/subagent-dev 子 agent 跑 agent init",
        )
        self.assertRegex(
            section,
            r"/dispatch-agents|/subagent-dev",
            "agent init 提示必须与 /dispatch-agents 或 /subagent-dev 配对出现",
        )

    # Gap 2a: 阶段 4 每步 audit WAL
    def test_stage_4_1_writes_audit_on_step_complete(self) -> None:
        section = _section(self.text, "#### 4.1 按步执行", "#### 4.2 遇到问题时的处理")
        self.assertRegex(
            section,
            r"audit\s+append.*current-task\.md|bin/audit append.*current-task",
            "阶段 4.1 每步完成时必须显式 audit append current-task.md",
        )

    # Gap 3: /compound 后的 memory rebuild + Gap 2b: lessons.md audit
    def test_stage_9_1_rebuilds_memory_and_audits_lessons(self) -> None:
        section = _section(self.text, "#### 9.1 提炼经验", "#### 9.2 ADR 状态维护")
        self.assertRegex(
            section,
            r"memory\s+rebuild",
            "阶段 9.1 /compound 后必须跑 memory rebuild 刷新 L1 热索引",
        )
        self.assertRegex(
            section,
            r"audit\s+append.*lessons\.md|bin/audit append.*lessons",
            "阶段 9.1 写入 lessons 后必须 audit append 登记 WAL",
        )

    # Refinement 1: 阶段 7.3 穷举验证先加载 testing-patterns L2 参考清单
    def test_stage_7_3_recalls_testing_patterns_refs(self) -> None:
        section = _section(self.text, "#### 7.3 穷举验证", "#### 7.4 安全审计")
        self.assertRegex(
            section,
            r"/recall\s+--refs\s+testing|testing-patterns\.md",
            "阶段 7.3 穷举验证必须先 /recall --refs testing 加载 testing-patterns 清单",
        )

    # Refinement 2: evolution 模式自动走完整通道
    def test_evolution_mode_routes_to_full_channel(self) -> None:
        section = _section(self.text, "**进化集成模式**", "**如果输入是普通文本描述**")
        self.assertRegex(
            section,
            r"完整通道",
            "evolution 模式必须明确标注走完整通道",
        )

    # Refinement 3: 阶段 3.2 历史教训检查扩到团队规则 (.harness-plugins/rules/)
    def test_stage_3_2_checks_harness_plugins_rules(self) -> None:
        section = _section(self.text, "#### 3.2 计划质量检查", "#### 3.3 用户确认")
        self.assertRegex(
            section,
            r"\.harness-plugins/rules|团队.*规则",
            "阶段 3.2 历史教训检查必须同时涵盖团队 plugins 规则",
        )

    # Gap 2c: 阶段 10.5 归档双 audit
    def test_stage_10_5_audits_archive_and_clear(self) -> None:
        section = _section(self.text, "#### 10.5 归档与关闭", "#### 10.6 关闭源 Issue")
        self.assertRegex(
            section,
            r"audit\s+append.*task-log\.md|bin/audit append.*task-log",
            "阶段 10.5 归档 task-log 时必须 audit append",
        )
        self.assertRegex(
            section,
            r"audit\s+append.*current-task\.md|bin/audit append.*current-task",
            "阶段 10.5 清空 current-task 时必须 audit append",
        )


if __name__ == "__main__":
    unittest.main()
