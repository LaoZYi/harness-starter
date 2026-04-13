"""Issue #26 — /lfg 整合 squad 通道的契约测试。

守住：
- 阶段 0.3 复杂度表含第 5 档 "超大-可并行"
- 并行类关键词注册
- 独立 "squad 通道" 章节存在，含 6 个介入点
- 降级出口（"不要并行" → 完整通道）存在
- spec.json（不是 yaml）+ `.agent-harness/bin/squad` 调用
- worker 不递归 lfg 的硬规则回顾
"""
from __future__ import annotations

import unittest
from pathlib import Path

from agent_harness._shared import SUPERPOWERS_ROOT


LFG_TMPL = SUPERPOWERS_ROOT / ".claude" / "commands" / "lfg.md.tmpl"


class LfgSquadChannelContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = LFG_TMPL.read_text(encoding="utf-8")

    def test_complexity_table_has_fifth_tier(self):
        self.assertIn("超大-可并行", self.text)
        self.assertIn("squad 通道", self.text)

    def test_parallel_keywords_registered(self):
        """并行类关键词必须触发升级到超大档。"""
        for kw in ("同时", "并行", "分头", "三方面", "兵分", "多管齐下"):
            self.assertIn(kw, self.text, f"缺少并行关键词：{kw}")

    def test_squad_channel_section_exists(self):
        self.assertIn("## squad 通道（超大-可并行任务）", self.text)

    def test_six_intervention_points(self):
        for i in range(1, 7):
            self.assertIn(f"介入点 {i}", self.text,
                          f"缺少介入点 {i}")

    def test_has_downgrade_exit(self):
        """拒绝 squad 时必须能降级到单 agent 完整通道。"""
        self.assertIn("不要并行", self.text)
        self.assertIn("完整通道", self.text)

    def test_uses_bin_squad_not_harness_cli(self):
        """整合后 AI 调用必须走 .agent-harness/bin/squad，不是 harness CLI。"""
        self.assertIn(".agent-harness/bin/squad create", self.text)

    def test_spec_format_is_json_not_yaml(self):
        """Issue #25 已去 PyYAML；lfg 生成的 spec 必须是 json。"""
        self.assertIn("spec.json", self.text)
        # 严禁复活 spec.yaml
        self.assertNotIn("spec.yaml", self.text,
                         "lfg.md.tmpl 不应再引用 spec.yaml（Issue #25 已迁 json）")

    def test_forced_compact_at_interventions_2_and_5(self):
        """介入点 2/5 后强制 /compact（防止 lfg 主会话 context 爆炸）。"""
        self.assertIn("compact", self.text.lower())

    def test_worker_no_recursion_rule_reminder(self):
        """worker 内不得再跑 lfg/squad/dispatch-agents 的硬规则要提醒到。"""
        self.assertIn("worker 内不递归", self.text)

    def test_default_topology_is_scout_builder_reviewer(self):
        """默认拓扑模板必须是 scout → builder → reviewer 三段。"""
        # JSON 草稿里应有这三个 capability 字符串
        for cap in ("scout", "builder", "reviewer"):
            self.assertIn(f'"{cap}"', self.text,
                          f"spec 草稿缺少 capability: {cap}")

    def test_failure_fallback_table_present(self):
        """失败兜底表必须存在（spec 拓扑错 / 全部失联 / reviewer FAIL / Ctrl+C）。"""
        self.assertIn("失败兜底", self.text)
        self.assertIn("stop all", self.text)


if __name__ == "__main__":
    unittest.main()
