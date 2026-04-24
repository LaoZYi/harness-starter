"""GitHub #46 — 吸收快手 sec-audit-pipeline 反偷懒工程学。

覆盖 R-001 ~ R-006 + R-007（defensive-temporary 分类标记）契约：

- R-001：`/pressure-test.md.tmpl` 含 7 类压力 + 6 默认场景 + 作用域清单
- R-002：`skills-registry.json` 注册 pressure-test (meta / expected_in_lfg=false)
- R-003：`anti-laziness.md.tmpl` 门禁 7 定义 + 顶部声明改 7 道
- R-004：门禁 3 表新增 3 条反合理化借口
- R-005：门禁 4 增强字段级必填
- R-006：`autonomy.md.tmpl` Trust Calibration 新增 3b orchestrator 疲劳门禁
- R-007：新机制均标记 `defensive-temporary`

R-008（dogfood 漂移）/ R-009（make ci）由 `scripts/check_repo.py` 和 `harness skills lint` 兜底。
R-010（文档计数一致）由 `check_count_consistency` 兜底。
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESSURE_TEST_TMPL = (
    REPO_ROOT
    / "src/agent_harness/templates/superpowers/.claude/commands/pressure-test.md.tmpl"
)
SKILLS_REGISTRY = (
    REPO_ROOT / "src/agent_harness/templates/superpowers/skills-registry.json"
)
ANTI_LAZINESS_TMPL = (
    REPO_ROOT / "src/agent_harness/templates/common/.claude/rules/anti-laziness.md.tmpl"
)
AUTONOMY_TMPL = (
    REPO_ROOT / "src/agent_harness/templates/common/.claude/rules/autonomy.md.tmpl"
)

SEVEN_PRESSURE_TYPES = (
    "沉没成本",
    "疲劳",
    "时间压力",
    "权威",
    "经济",
    "务实",
    "复杂度回避",
)


class PressureTestSkillTests(unittest.TestCase):
    """R-001：pressure-test 模板含 7 类压力 + 6 场景 + 作用域。"""

    def test_pressure_test_tmpl_exists(self) -> None:
        self.assertTrue(
            PRESSURE_TEST_TMPL.exists(),
            f"缺少 {PRESSURE_TEST_TMPL.relative_to(REPO_ROOT)}",
        )

    def test_pressure_test_tmpl_has_seven_pressure_types(self) -> None:
        text = PRESSURE_TEST_TMPL.read_text(encoding="utf-8")
        for pressure in SEVEN_PRESSURE_TYPES:
            self.assertIn(
                pressure,
                text,
                f"pressure-test 模板缺少压力类型关键词 `{pressure}`",
            )

    def test_pressure_test_tmpl_has_default_targets(self) -> None:
        """默认作用域必须显式列出 /verify / /multi-review / /cso / /lfg / /squad。"""
        text = PRESSURE_TEST_TMPL.read_text(encoding="utf-8")
        for target in ("/verify", "/multi-review", "/cso", "/lfg", "/squad"):
            self.assertIn(
                target,
                text,
                f"pressure-test 默认作用域缺少 `{target}`",
            )

    def test_pressure_test_tmpl_marks_defensive_temporary(self) -> None:
        """R-007：pressure-test 模板必须标记 defensive-temporary 分类。"""
        text = PRESSURE_TEST_TMPL.read_text(encoding="utf-8")
        self.assertIn(
            "defensive-temporary",
            text,
            "pressure-test 模板必须标记 defensive-temporary 分类"
            "（见 lessons.md 反偷懒与协作记忆要解耦）",
        )


class SkillsRegistryTests(unittest.TestCase):
    """R-002：skills-registry.json 注册 pressure-test。"""

    def test_skills_registry_has_pressure_test_as_meta(self) -> None:
        data = json.loads(SKILLS_REGISTRY.read_text(encoding="utf-8"))
        skills = {s["id"]: s for s in data["skills"]}
        self.assertIn(
            "pressure-test",
            skills,
            "skills-registry.json 必须注册 pressure-test",
        )
        entry = skills["pressure-test"]
        self.assertEqual(
            entry["category"],
            "meta",
            "pressure-test 必须归为 meta 类（周期性,与 /lfg 垂直）",
        )
        self.assertFalse(
            entry["expected_in_lfg"],
            "pressure-test 不入 /lfg 主流程（expected_in_lfg=false）",
        )


class AntiLazinessRuleTests(unittest.TestCase):
    """R-003 + R-004 + R-005 + R-007：anti-laziness 4 处改动。"""

    def test_anti_laziness_header_declares_seven_gates(self) -> None:
        """R-003：顶部不再含『4 道』过期声明，改 7 道。"""
        text = ANTI_LAZINESS_TMPL.read_text(encoding="utf-8")
        # 过时声明必须移除
        self.assertNotIn(
            "本规则定义 4 道硬门禁",
            text,
            "anti-laziness 顶部『本规则定义 4 道硬门禁』是过时声明,必须改为 7 道",
        )
        # 新声明必须存在
        self.assertIn(
            "7 道",
            text,
            "anti-laziness 顶部必须声明『7 道硬门禁』",
        )

    def test_anti_laziness_has_gate_7_pressure_test(self) -> None:
        """R-003：门禁 7 压力测试段存在。"""
        text = ANTI_LAZINESS_TMPL.read_text(encoding="utf-8")
        self.assertIn("门禁 7", text, "anti-laziness 缺少门禁 7 声明")
        self.assertIn(
            "压力测试",
            text,
            "anti-laziness 门禁 7 必须是压力测试主题",
        )

    def test_anti_laziness_gate_3_has_three_new_excuses(self) -> None:
        """R-004：门禁 3 反合理化表新增 3 条借口(逐字抄 Issue #46 原文案)。"""
        text = ANTI_LAZINESS_TMPL.read_text(encoding="utf-8")
        for excuse_keyword in (
            "Agent 写入失败",
            "上下文太长",
            "SKILL.md 太长",
        ):
            self.assertIn(
                excuse_keyword,
                text,
                f"anti-laziness 门禁 3 缺少新借口关键词 `{excuse_keyword}`",
            )

    def test_anti_laziness_gate_4_has_field_level_mandatory(self) -> None:
        """R-005：门禁 4 增强字段级必填声明。"""
        text = ANTI_LAZINESS_TMPL.read_text(encoding="utf-8")
        self.assertIn(
            "字段级必填",
            text,
            "anti-laziness 门禁 4 必须增强『字段级必填』",
        )

    def test_anti_laziness_gate_7_marks_defensive_temporary(self) -> None:
        """R-007:门禁 7 必须标记 defensive-temporary,用下一章节锚点截断防假阳性。"""
        text = ANTI_LAZINESS_TMPL.read_text(encoding="utf-8")
        # 找门禁 7 的"## 门禁 7" 而非全文首个"门禁 7"(避免命中引用)
        gate_7_start = text.find("## 门禁 7")
        self.assertGreater(gate_7_start, 0, "未找到 ## 门禁 7 标题")
        # 用下一章节"## 与现有机制的关系"截断
        next_section = text.find("## 与现有机制", gate_7_start)
        self.assertGreater(next_section, gate_7_start, "未找到门禁 7 终止锚点")
        gate_7_block = text[gate_7_start:next_section]
        self.assertIn(
            "defensive-temporary",
            gate_7_block,
            "门禁 7 段必须显式引用 defensive-temporary 分类(锚点精确截断)",
        )


class AutonomyRuleTests(unittest.TestCase):
    """R-006 + R-007：autonomy Trust Calibration 3b orchestrator 疲劳门禁。"""

    def test_autonomy_has_3b_orchestrator_fatigue_gate(self) -> None:
        text = AUTONOMY_TMPL.read_text(encoding="utf-8")
        self.assertIn("3b", text, "autonomy.md Trust Calibration 必须新增 3b 段")
        self.assertIn(
            "orchestrator 疲劳",
            text,
            "3b 必须是 orchestrator 疲劳硬门禁主题",
        )
        self.assertIn(
            "fresh orchestrator",
            text,
            "3b 必须声明派出 N worker 后 spawn fresh orchestrator 接管",
        )

    def test_autonomy_3b_has_handoff_event_schema(self) -> None:
        """R-006 字段级 schema 契约：3b 定义的 mailbox handoff 事件必须锁字段名。

        下游 squad watchdog / mailbox reader 会按字段名解析。字段改了
        (reason→cause / worker_count→n_workers) 文字契约过但运行时炸。
        """
        text = AUTONOMY_TMPL.read_text(encoding="utf-8")
        for field in ("type=handoff", "reason=fatigue_gate", "worker_count"):
            self.assertIn(
                field,
                text,
                f"3b mailbox 事件 schema 字段 `{field}` 必须原样保留(下游按字段名解析)",
            )

    def test_autonomy_3b_marks_defensive_temporary(self) -> None:
        """R-007: 3b 段必须标记 defensive-temporary，并用下一章节锚点截断防假阳性。"""
        text = AUTONOMY_TMPL.read_text(encoding="utf-8")
        three_b_start = text.find("3b. orchestrator 疲劳")
        self.assertGreater(three_b_start, 0, "未找到 3b 段起始锚点")
        # 用下一个同级标题(4. 信任升级条件 / ## 某节)截断，避免越段捞到别段的关键词
        next_anchor = text.find("4. **信任升级", three_b_start)
        if next_anchor < 0:
            next_anchor = text.find("\n## ", three_b_start)
        self.assertGreater(next_anchor, three_b_start, "未找到 3b 段终止锚点")
        three_b_block = text[three_b_start:next_anchor]
        self.assertIn(
            "defensive-temporary",
            three_b_block,
            "autonomy 3b 段必须显式引用 defensive-temporary 分类(锚点精确截断)",
        )


if __name__ == "__main__":
    unittest.main()
