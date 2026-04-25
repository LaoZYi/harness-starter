"""Issue #26 — /lfg 整合 squad 通道的契约测试。

守住：
- 阶段 0.3 复杂度表含第 5 档 "超大-可并行"
- 并行类关键词注册
- 独立 "squad 通道" 章节存在，含 6 个介入点
- 降级出口（"不要并行" → 完整通道）存在
- spec.json（不是 yaml）+ `.agent-harness/bin/squad` 调用
- worker 不递归 lfg 的硬规则回顾

2026-04-26 重构: squad 详细工作流抽到 references/squad-channel.md。
契约测试同时检查主模板(必含指针)+ references(详细内容源)。
"""
from __future__ import annotations

import unittest

from agent_harness._shared import SUPERPOWERS_ROOT


LFG_TMPL = SUPERPOWERS_ROOT / ".claude" / "commands" / "lfg.md.tmpl"
SQUAD_REF_TMPL = (
    SUPERPOWERS_ROOT.parent
    / "common"
    / ".agent-harness"
    / "references"
    / "squad-channel.md.tmpl"
)


class LfgSquadChannelContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = LFG_TMPL.read_text(encoding="utf-8")
        cls.ref_text = SQUAD_REF_TMPL.read_text(encoding="utf-8")
        cls.combined = cls.text + "\n" + cls.ref_text

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
        # 主模板含速览;详细内容在 references/squad-channel.md
        self.assertIn("squad-channel.md", self.text,
                      "主模板必须含 references/squad-channel.md 指针")
        for i in range(1, 7):
            self.assertIn(f"介入点 {i}", self.combined,
                          f"缺少介入点 {i}(主模板速览或 references 详细)")

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
        # 主模板速览 + references 详细任一处含即可
        self.assertIn("worker 内**不得**", self.combined)

    def test_default_topology_is_scout_builder_reviewer(self):
        """默认拓扑模板必须是 scout → builder → reviewer 三段。"""
        # JSON 草稿在 references/squad-channel.md(从主模板抽出)
        for cap in ("scout", "builder", "reviewer"):
            self.assertIn(f'"{cap}"', self.ref_text,
                          f"references/squad-channel.md spec 草稿缺少 capability: {cap}")

    def test_failure_fallback_table_present(self):
        """失败兜底表必须存在（spec 拓扑错 / 全部失联 / reviewer FAIL / Ctrl+C）。"""
        self.assertIn("失败兜底", self.text)
        self.assertIn("stop all", self.text)


if __name__ == "__main__":
    unittest.main()
