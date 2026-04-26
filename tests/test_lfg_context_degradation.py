"""Issue #50 — context-degradation 吸收的契约测试。

守住:
- 新 reference context-degradation-patterns.md.tmpl 存在 + 长度 ≥ 130 行
- 5 类 pattern 关键词都在(Lost-in-Middle / Poisoning / Distraction /
  Confusion / Clash)
- lfg.md.tmpl 阶段 0.2 含 /recall --refs context-degradation 加载指针
- lfg.md.tmpl 阶段 4.1 Context 预算守卫含 tokens-per-task 概念
- context-budget.md.tmpl 含 tokens-per-task 节 + 诊断侧入口
- lfg-progress-format.md.tmpl 含 Artifacts touched 字段
- anti-laziness.md.tmpl 反合理化表含"压缩越狠"借口驳斥
- OVERVIEW.md.tmpl 含新 reference 索引行

来源:吸收 muratcankoylan/Agent-Skills-for-Context-Engineering(15.3k stars,
北大 GAI 实验室 2026 论文引用)。
"""
from __future__ import annotations

import unittest

from agent_harness._shared import SUPERPOWERS_ROOT


COMMON_ROOT = SUPERPOWERS_ROOT.parent / "common"
LFG_TMPL = SUPERPOWERS_ROOT / ".claude" / "commands" / "lfg.md.tmpl"
CTX_DEG_REF = (
    COMMON_ROOT / ".agent-harness" / "references"
    / "context-degradation-patterns.md.tmpl"
)
CTX_BUDGET_RULE = COMMON_ROOT / ".claude" / "rules" / "context-budget.md.tmpl"
LFG_PROGRESS_REF = (
    COMMON_ROOT / ".agent-harness" / "references"
    / "lfg-progress-format.md.tmpl"
)
ANTI_LAZ_RULE = COMMON_ROOT / ".claude" / "rules" / "anti-laziness.md.tmpl"
OVERVIEW_REF = (
    COMMON_ROOT / ".agent-harness" / "references" / "OVERVIEW.md.tmpl"
)


class ContextDegradationContractTests(unittest.TestCase):
    """Issue #50 契约——5 类 attention 诊断到位 + 各文件链路完整。"""

    @classmethod
    def setUpClass(cls):
        cls.ctx_deg = CTX_DEG_REF.read_text(encoding="utf-8")
        cls.lfg = LFG_TMPL.read_text(encoding="utf-8")
        cls.ctx_budget = CTX_BUDGET_RULE.read_text(encoding="utf-8")
        cls.progress = LFG_PROGRESS_REF.read_text(encoding="utf-8")
        cls.anti_laz = ANTI_LAZ_RULE.read_text(encoding="utf-8")
        cls.overview = OVERVIEW_REF.read_text(encoding="utf-8")

    def test_new_reference_exists_and_long_enough(self):
        self.assertTrue(CTX_DEG_REF.exists(), "新 reference 必须存在")
        line_count = len(self.ctx_deg.splitlines())
        self.assertGreaterEqual(
            line_count, 130, f"reference 长度 {line_count} 行 < 130 行下限"
        )

    def test_five_degradation_patterns_present(self):
        """5 类 pattern 都必须在 reference 里。"""
        for pat in (
            "Lost-in-Middle",
            "Poisoning",
            "Distraction",
            "Confusion",
            "Clash",
        ):
            self.assertIn(pat, self.ctx_deg, f"缺少 pattern: {pat}")

    def test_lfg_phase_02_loads_new_reference(self):
        """lfg 阶段 0.2 必须有 /recall --refs context-degradation 加载指针。"""
        self.assertIn(
            "/recall --refs context-degradation",
            self.lfg,
            "lfg.md 必须含 /recall --refs context-degradation 加载指针",
        )

    def test_lfg_phase_41_has_tokens_per_task_guard(self):
        """阶段 4.1 Context 预算守卫必须提及 tokens-per-task 概念。"""
        self.assertIn(
            "tokens-per-task",
            self.lfg,
            "lfg.md 阶段 4.1 守卫必须含 tokens-per-task 概念",
        )

    def test_context_budget_has_tokens_per_task_section(self):
        """context-budget 规则 4 必须有 tokens-per-task 优化目标节。"""
        self.assertIn("tokens-per-task", self.ctx_budget)
        self.assertIn("re-fetching", self.ctx_budget)

    def test_context_budget_has_diagnostic_entry(self):
        """context-budget 必须有诊断侧入口指向新 reference。"""
        self.assertIn("context-degradation", self.ctx_budget)
        self.assertIn("诊断侧", self.ctx_budget)

    def test_lfg_progress_format_has_artifacts_touched(self):
        """lfg-progress-format 必须有 Artifacts touched 字段。"""
        self.assertIn("Artifacts touched", self.progress)

    def test_anti_laziness_has_compression_rationalization(self):
        """anti-laziness 反合理化表必须有'压缩越狠越省 token'借口驳斥。"""
        self.assertIn("压缩", self.anti_laz)
        self.assertIn("re-fetching frequency", self.anti_laz)

    def test_overview_indexes_new_reference(self):
        """OVERVIEW 关键文件列表 + 触发场景表必须含新 reference。"""
        self.assertIn("context-degradation-patterns.md", self.overview)
        # 触发场景表里也要有
        self.assertIn("AI 长会话退化", self.overview)


if __name__ == "__main__":
    unittest.main()
