"""Issue #51 — Karpathy simplicity / surgical-changes 吸收的契约测试。

守住:
- 新 rule simplicity.md.tmpl 存在 + 长度 ≥ 60 行
- 4 准则关键词都在(Simplicity First / Surgical Changes / 孤儿清理 / 可验证目标)
- 与 anti-laziness 边界声明存在(反偷懒 vs 反过度工程化)
- 与 safety 边界(扩散 vs 越界)在 simplicity.md
- 适用边界(框架级抽象 vs 业务代码)在 simplicity.md
- agent-design.md F11 引用 simplicity 准则 2 同源说明
- requirement-mapping-checklist 末尾含'模糊→可验证'转换模板 + 7 类 pattern
- anti-laziness 顶部含与 simplicity 边界声明
- lfg.md 阶段 0.1 / 4.2 / 4.3 三处引用

来源:Issue #51 吸收 forrestchang/andrej-karpathy-skills(87.8k stars,基于
Karpathy 关于 LLM 编码陷阱观察)。
"""
from __future__ import annotations

import unittest

from agent_harness._shared import SUPERPOWERS_ROOT


COMMON_ROOT = SUPERPOWERS_ROOT.parent / "common"
LFG_TMPL = SUPERPOWERS_ROOT / ".claude" / "commands" / "lfg.md.tmpl"
SIMPLICITY_RULE = COMMON_ROOT / ".claude" / "rules" / "simplicity.md.tmpl"
AGENT_DESIGN_RULE = COMMON_ROOT / ".claude" / "rules" / "agent-design.md.tmpl"
ANTI_LAZ_RULE = COMMON_ROOT / ".claude" / "rules" / "anti-laziness.md.tmpl"
REQ_MAPPING_REF = (
    COMMON_ROOT / ".agent-harness" / "references"
    / "requirement-mapping-checklist.md.tmpl"
)


class SimplicityAbsorptionContractTests(unittest.TestCase):
    """Issue #51 契约——Karpathy 4 原则的项目化吸收链路完整。"""

    @classmethod
    def setUpClass(cls):
        cls.simplicity = SIMPLICITY_RULE.read_text(encoding="utf-8")
        cls.agent_design = AGENT_DESIGN_RULE.read_text(encoding="utf-8")
        cls.anti_laz = ANTI_LAZ_RULE.read_text(encoding="utf-8")
        cls.req_mapping = REQ_MAPPING_REF.read_text(encoding="utf-8")
        cls.lfg = LFG_TMPL.read_text(encoding="utf-8")

    def test_simplicity_rule_exists_and_long_enough(self):
        self.assertTrue(SIMPLICITY_RULE.exists(), "simplicity.md.tmpl 必须存在")
        line_count = len(self.simplicity.splitlines())
        self.assertGreaterEqual(
            line_count, 60, f"simplicity 长度 {line_count} 行 < 60 行下限"
        )

    def test_simplicity_has_four_principles(self):
        """4 准则关键词都必须在 simplicity.md。"""
        for kw in ("Simplicity First", "Surgical Changes", "孤儿清理", "可验证目标"):
            self.assertIn(kw, self.simplicity, f"simplicity 缺准则: {kw}")

    def test_simplicity_has_anti_laziness_boundary(self):
        """simplicity 必须明示与 anti-laziness 反向互补。"""
        self.assertIn("anti-laziness", self.simplicity)
        self.assertIn("反向互补", self.simplicity)

    def test_simplicity_has_safety_boundary(self):
        """simplicity 必须明示与 safety「改一处查所有同类」的边界。"""
        self.assertIn("safety", self.simplicity)

    def test_simplicity_has_scope_boundary(self):
        """simplicity 必须明示框架 vs 业务的适用边界。"""
        self.assertIn("框架", self.simplicity)
        self.assertIn("业务", self.simplicity)
        # 修反模式例外要明示
        self.assertIn("反模式", self.simplicity)

    def test_agent_design_f11_references_simplicity(self):
        """agent-design.md F11 必须引用 simplicity 准则 2 同源说明。"""
        self.assertIn("simplicity.md", self.agent_design)
        self.assertIn("Surgical Changes", self.agent_design)

    def test_anti_laziness_top_has_simplicity_boundary(self):
        """anti-laziness 顶部(在 7 道门禁之前)必须含 simplicity 边界说明。"""
        # 取门禁 1 之前的部分
        idx = self.anti_laz.find("## 门禁 1")
        self.assertGreater(idx, 0, "找不到门禁 1 标题")
        head = self.anti_laz[:idx]
        self.assertIn("simplicity", head,
                      "anti-laziness 顶部(门禁 1 前)必须含 simplicity 边界声明")
        self.assertIn("反向互补", head)

    def test_req_mapping_has_conversion_template(self):
        """requirement-mapping 末尾必须含模糊→可验证转换模板 + 7 类 pattern。"""
        self.assertIn("模糊需求 → 可验证目标转换模板", self.req_mapping)
        # 7 类 pattern 关键词
        for pat in (
            "Add validation",
            "Fix the bug",
            "Refactor X",
            "Optimize Y",
            "Migrate from A to B",
            "Improve UX",
            "Support Z",
        ):
            self.assertIn(pat, self.req_mapping, f"缺转换 pattern: {pat}")

    def test_lfg_phase_01_references_conversion_template(self):
        """lfg 阶段 0.1 第 3 步必须引用转换模板。"""
        self.assertIn("模糊需求 → 可验证目标", self.lfg)

    def test_lfg_phase_42_forbids_neighbor_drift(self):
        """lfg 阶段 4.2 必须含'顺手改进邻居代码'禁止行。"""
        self.assertIn("顺手改进", self.lfg)
        self.assertIn("Surgical Changes", self.lfg)

    def test_lfg_phase_43_self_check_has_simplicity_row(self):
        """lfg 阶段 4.3 自检表必须含 simplicity 检查行。"""
        # 寻找 4.3 段落
        idx = self.lfg.find("公共规则合规检查")
        self.assertGreater(idx, 0)
        # 取 4.3 之后 ~1500 字符
        section = self.lfg[idx:idx + 1500]
        self.assertIn("simplicity", section)
        self.assertIn("追溯", section)


if __name__ == "__main__":
    unittest.main()
