"""GitHub #43 / GitLab #22 — 吸收 Imprint 5 型 Conflict Resolution 到 lessons 域。

覆盖 R-001 ~ R-007 的契约：

- R-001: `.claude/rules/knowledge-conflict-resolution.md.tmpl` 存在且结构完整
- R-002: `/lint-lessons` 模板含 resolution-type 字段和对新规则的引用
- R-003: `/compound` 模板含冲突预检步骤（3.5）
- R-005: T3/T4/T5 处理路径文案具体到可断言
- R-007: ADR 文件存在且有合法状态字段

R-004（dogfood 漂移）由现有 `scripts/check_repo.py` 的 dogfood 检测兜底。
R-006（文档计数同步）由 `scripts/check_repo.py::check_count_consistency` 兜底。
两者在 `make check` 中执行，这里不再复测。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULE_TEMPLATE = REPO_ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "rules" / "knowledge-conflict-resolution.md.tmpl"
LINT_LESSONS_TEMPLATE = REPO_ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands" / "lint-lessons.md.tmpl"
COMPOUND_TEMPLATE = REPO_ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands" / "compound.md.tmpl"
ADR_FILE = REPO_ROOT / "docs" / "decisions" / "0002-knowledge-conflict-resolution.md"


class KnowledgeConflictResolutionRuleStructureTests(unittest.TestCase):
    """R-001 + R-005：规则模板存在且 5 型处理路径可断言。"""

    def test_rule_template_exists(self) -> None:
        self.assertTrue(RULE_TEMPLATE.exists(), f"缺少 {RULE_TEMPLATE}")

    def test_rule_contains_all_five_types(self) -> None:
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        for marker in ("T1", "T2", "T3", "T4", "T5"):
            self.assertIn(marker, text, f"规则文件缺少 {marker} 标记")

    def test_t3_processing_path_is_conditional_branch(self) -> None:
        """T3（两条 confirmed 相反）处理路径必须提到条件分支 + 不删任一。"""
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        # 锚定在 T3 段落里
        t3_block = _extract_section(text, "T3")
        self.assertTrue(t3_block, "未找到 T3 段落")
        self.assertIn("条件分支", t3_block)
        self.assertTrue(
            "不删" in t3_block or "不废弃" in t3_block or "都保留" in t3_block,
            "T3 段落必须明确『不删任一』",
        )

    def test_t4_processing_path_is_downgrade_to_tentative(self) -> None:
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        t4_block = _extract_section(text, "T4")
        self.assertTrue(t4_block, "未找到 T4 段落")
        self.assertIn("tentative", t4_block)
        self.assertTrue(
            "降级" in t4_block or "等" in t4_block,
            "T4 段落必须明确『降级 + 等用户确认』",
        )

    def test_t5_processing_path_is_warning_not_block(self) -> None:
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        t5_block = _extract_section(text, "T5")
        self.assertTrue(t5_block, "未找到 T5 段落")
        self.assertIn("警告", t5_block)
        self.assertTrue(
            "不" in t5_block and ("阻断" in t5_block or "拒绝" in t5_block or "block" in t5_block.lower()),
            "T5 段落必须明确『警告不阻断』",
        )

    def test_t1_and_t2_marked_out_of_scope_for_lessons(self) -> None:
        """T1 / T2 在本项目 lessons 域不直接适用，规则文件需显式声明。"""
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        # 在文件任意位置声明 T1/T2 不接入 lessons 即可
        self.assertTrue(
            "T1" in text and "T2" in text,
            "规则文件需提到 T1 和 T2",
        )
        # 必须有段落说明本次只接入 T3/T4/T5
        has_scope_note = any(
            keyword in text
            for keyword in ("只接入", "不接入", "out-of-scope", "lessons 域")
        )
        self.assertTrue(has_scope_note, "规则文件必须声明 T1/T2 在 lessons 域不直接适用")


class LintLessonsTemplateTests(unittest.TestCase):
    """R-002：`/lint-lessons` 模板含 resolution-type 字段 + 引用新规则。"""

    def test_lint_lessons_has_resolution_type_field(self) -> None:
        text = LINT_LESSONS_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("resolution-type", text)

    def test_lint_lessons_references_new_rule(self) -> None:
        text = LINT_LESSONS_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("knowledge-conflict-resolution", text)

    def test_lint_lessons_mentions_t3_t4_t5_in_output(self) -> None:
        """输出格式示例应展示如何标注 T3/T4/T5。"""
        text = LINT_LESSONS_TEMPLATE.read_text(encoding="utf-8")
        for t in ("T3", "T4", "T5"):
            self.assertIn(t, text, f"lint-lessons 输出示例缺少 {t}")


class CompoundTemplateTests(unittest.TestCase):
    """R-003：`/compound` 模板含冲突预检步骤。"""

    def test_compound_has_conflict_precheck_step(self) -> None:
        text = COMPOUND_TEMPLATE.read_text(encoding="utf-8")
        # 3.5 或「冲突预检」关键词
        self.assertTrue(
            "3.5" in text or "冲突预检" in text,
            "compound 必须新增『3.5 冲突预检』或等价步骤",
        )

    def test_compound_classifies_by_type(self) -> None:
        text = COMPOUND_TEMPLATE.read_text(encoding="utf-8")
        self.assertTrue(
            "T3" in text and ("T4" in text or "T5" in text),
            "compound 冲突预检必须按 T3/T4/T5 分型",
        )

    def test_compound_precheck_is_warning_not_block(self) -> None:
        """冲突预检应明确是『警告 + 人工裁决』不 block。"""
        text = COMPOUND_TEMPLATE.read_text(encoding="utf-8")
        # 在 compound 文件中出现『预检』周边应带『不 block / 人工裁决 / 警告』字眼
        self.assertTrue(
            "人工裁决" in text or "不 block" in text or "警告" in text or "不阻断" in text,
            "compound 预检段落必须声明非 blocking 性质",
        )


class ADRStateTests(unittest.TestCase):
    """R-007：ADR 文件存在且状态字段合法。"""

    def test_adr_file_exists(self) -> None:
        self.assertTrue(ADR_FILE.exists(), f"缺少 {ADR_FILE}")

    def test_adr_has_valid_status(self) -> None:
        """ADR Status 必须是 Proposed/Accepted/Deprecated/Superseded 之一。"""
        text = ADR_FILE.read_text(encoding="utf-8")
        # 兼容两种格式：`Status: X` 和 `- **状态**：X`（项目 ADR 0001 的格式）
        match = re.search(
            r"(?:Status|状态)\**\s*[:：]\s*(\w+)",
            text,
        )
        self.assertIsNotNone(match, "ADR 缺少 Status/状态 字段")
        assert match is not None  # for mypy
        status = match.group(1)
        self.assertIn(status, {"Proposed", "Accepted", "Deprecated", "Superseded"})


class OpenVikingDedupDecisionTests(unittest.TestCase):
    """GitHub #45：吸收 OpenViking Memory dedup 4 决策（skip/create/merge/delete）。

    覆盖：

    - R-001：`/compound` 新增 dedup 决策步骤（3.6），4 分支完整
    - R-002：`/lint-lessons` 每对矛盾输出 resolution-type + dedup decision 双标签
    - R-003：`knowledge-conflict-resolution.md` T3 章节升级为 4 决策 SOP
    - R-007：`保留 A` 文本锚点保持（lessons.md:67 回归保护）
    """

    def test_t3_has_four_decision_sop(self) -> None:
        """T3 段落必须含 4 决策关键词 skip/create/merge/delete。"""
        text = RULE_TEMPLATE.read_text(encoding="utf-8")
        t3_block = _extract_section(text, "T3")
        self.assertTrue(t3_block, "未找到 T3 段落")
        for keyword in ("skip", "create", "merge", "delete"):
            self.assertIn(
                keyword,
                t3_block,
                f"T3 段落缺少 dedup decision 关键词 `{keyword}`",
            )

    def test_compound_has_dedup_step_36_with_memory_search(self) -> None:
        """`/compound` 必须新增第 3.6 步，调用 memory search --top 拿 top-K 相似条目。"""
        text = COMPOUND_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("3.6", text, "compound 必须新增第 3.6 步")
        self.assertIn(
            "memory search",
            text,
            "compound 3.6 必须调用 memory search 做 BM25 预过滤",
        )
        self.assertIn(
            "--top",
            text,
            "compound 3.6 必须用 --top 控制 top-K",
        )
        for keyword in ("skip", "create", "merge", "delete"):
            self.assertIn(
                keyword,
                text,
                f"compound 3.6 缺少 dedup decision 关键词 `{keyword}`",
            )

    def test_lint_lessons_has_dedup_decision_label(self) -> None:
        """`/lint-lessons` 每对矛盾输出 resolution-type + dedup decision 双标签。"""
        text = LINT_LESSONS_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "resolution-type",
            text,
            "lint-lessons 缺少 resolution-type 标签(现有契约)",
        )
        self.assertIn(
            "dedup decision",
            text,
            "lint-lessons 必须新增 dedup decision 标签",
        )
        # 输出格式示例必须同时出现两种标签
        for keyword in ("skip", "create", "merge", "delete"):
            self.assertIn(
                keyword,
                text,
                f"lint-lessons 2.2.2 缺少 dedup decision 关键词 `{keyword}`",
            )

    def test_lint_lessons_preserves_keep_a_anchor(self) -> None:
        """回归保护：lessons.md:67 教训——`保留 A` 文本锚点受 assertIn 锁定不能动。"""
        text = LINT_LESSONS_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "保留 A",
            text,
            "lint-lessons 4 裁决模板原文案『保留 A 删 B』必须保留"
            "（test_lint_lessons_has_contradiction_detection 通过 assertIn 锁定）",
        )

    def test_compound_dedup_not_auto_execute(self) -> None:
        """`/compound` 3.6 步必须保留『不自动执行』铁律（与现有冲突预检一致）。"""
        text = COMPOUND_TEMPLATE.read_text(encoding="utf-8")
        # 在 compound 全文中出现『不自动执行』或『不 block 写入』即可
        self.assertTrue(
            "不自动执行" in text or "不 block" in text or "人工裁决" in text,
            "compound 3.6 dedup 决策必须声明非自动执行性质"
            "（遵循 knowledge-conflict-resolution.md 铁律）",
        )


def _extract_section(text: str, heading_keyword: str) -> str:
    """截取以 `## <keyword>` 或 `### <keyword>` 开头的段落（到下一个同级标题前）。"""
    lines = text.splitlines()
    start = None
    start_level = None
    pattern = re.compile(rf"^(#{{1,6}})\s+.*\b{re.escape(heading_keyword)}\b")
    for i, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            start = i
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{1,6})\s+", lines[j])
        if m and len(m.group(1)) <= start_level:
            end = j
            break
    return "\n".join(lines[start:end])


if __name__ == "__main__":
    unittest.main()
