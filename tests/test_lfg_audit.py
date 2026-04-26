"""Tests for `harness lfg audit` — 15-dimension /lfg scorecard.

2026-04-26: 扩展 10 → 15 维(加引用深度 / 主模板长度 / 确认点密度 / 关键守卫多点 / 通道层级化)。

Three categories required by `.claude/rules/testing.md`:
- Normal: healthy repo scores near the top
- Boundary: mutating the template deducts the right dimension
- Error: missing or corrupted inputs fail cleanly
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_harness.lfg_audit import audit  # noqa: E402
from agent_harness.lfg_audit_checks import DIMENSION_CHECKS  # noqa: E402
from agent_harness.lfg_audit_cli import main  # noqa: E402

SUPERPOWERS_REL = Path("src/agent_harness/templates/superpowers")
LFG_TMPL_REL = SUPERPOWERS_REL / ".claude/commands/lfg.md.tmpl"


def _clone_repo(dst: Path) -> Path:
    """Mirror the bits of the repo the auditor reads (rules, lfg, registry, presets)."""
    for rel in (
        SUPERPOWERS_REL / ".claude/commands/lfg.md.tmpl",
        SUPERPOWERS_REL / "skills-registry.json",
    ):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    common_rules = Path("src/agent_harness/templates/common/.claude/rules")
    (dst / common_rules).mkdir(parents=True, exist_ok=True)
    for f in (ROOT / common_rules).glob("*.md.tmpl"):
        shutil.copy2(f, dst / common_rules / f.name)
    presets = Path("src/agent_harness/presets")
    (dst / presets).mkdir(parents=True, exist_ok=True)
    for f in (ROOT / presets).glob("*.json"):
        shutil.copy2(f, dst / presets / f.name)
    return dst


class NormalPathTests(unittest.TestCase):
    """正常路径：健康仓库跑出高分。"""

    def test_healthy_repo_scores_at_least_baseline(self) -> None:
        card = audit(ROOT)
        # 15 维基线: ≥ 10.5(70%);新增 5 维(11-15)是质量层,健康仓库应 >= 12
        self.assertGreaterEqual(
            card.total, 10.5,
            f"baseline score too low: {card.total}/{card.max_total}. "
            f"Dims: {[(d.id, d.score) for d in card.dimensions]}",
        )

    def test_has_exactly_fifteen_dimensions(self) -> None:
        card = audit(ROOT)
        self.assertEqual(len(card.dimensions), 15)
        self.assertEqual(len(DIMENSION_CHECKS), 15)

    def test_json_output_is_parseable(self) -> None:
        card = audit(ROOT)
        payload = card.to_json()
        # Roundtrip via json serialization
        text = json.dumps(payload, ensure_ascii=False)
        reloaded = json.loads(text)
        self.assertEqual(reloaded["max_total"], 15)
        self.assertEqual(len(reloaded["dimensions"]), 15)
        for d in reloaded["dimensions"]:
            self.assertIn("score", d)
            self.assertIn("checks", d)

    def test_console_output_mentions_total(self) -> None:
        card = audit(ROOT)
        text = card.to_console()
        self.assertIn("威力释放度", text)
        self.assertIn(f"{card.total}/{card.max_total}", text)


class BoundaryTests(unittest.TestCase):
    """边界情况：定点扰动模板应扣对应维度分。"""

    def test_removing_audit_keyword_zeros_dim_7(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _clone_repo(Path(td))
            lfg_path = repo / LFG_TMPL_REL
            text = lfg_path.read_text(encoding="utf-8")
            # 删掉 audit append 让 Dim 7 失分
            mutated = text.replace("audit append", "XXXX")
            lfg_path.write_text(mutated, encoding="utf-8")
            card = audit(repo)
            dim7 = next(d for d in card.dimensions if d.id == 7)
            self.assertEqual(
                dim7.score, 0.0,
                f"Dim 7 应归零，实际 {dim7.score}; checks={dim7.checks}",
            )

    def test_removing_compound_deducts_dim_9(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _clone_repo(Path(td))
            lfg_path = repo / LFG_TMPL_REL
            text = lfg_path.read_text(encoding="utf-8")
            mutated = text.replace("/compound", "/xxxxxxxx")
            lfg_path.write_text(mutated, encoding="utf-8")
            card = audit(repo)
            dim9 = next(d for d in card.dimensions if d.id == 9)
            self.assertLess(dim9.score, 1.0)

    def test_empty_template_tanks_total(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _clone_repo(Path(td))
            lfg_path = repo / LFG_TMPL_REL
            lfg_path.write_text("# empty\n", encoding="utf-8")
            card = audit(repo)
            # 空模板:维度 1-10 全 0;维度 12 长度因为短给 1.0;维度 13 密度因 0 个 🔴 给 1.0
            # 总分约 2.0 左右,应远低于 5.0
            self.assertLess(
                card.total, 5.0,
                f"空模板总分应 < 5，实际 {card.total}",
            )

    def test_opt_in_rules_not_counted_in_dim_1(self) -> None:
        """api.md/database.md 不在基线中，删除 api.md 关键词不扣 Dim 1。"""
        card = audit(ROOT)
        dim1 = next(d for d in card.dimensions if d.id == 1)
        check_names = [name for name, _ in dim1.checks]
        self.assertNotIn("api.md 被引用", check_names)
        self.assertNotIn("database.md 被引用", check_names)

    def test_threshold_gate_fails_below(self) -> None:
        # 设阈值高于满分(15.5)必然 exit 1——表达"门禁失败路径"语义,
        # 不绑定当前总分(随模板优化会变,绑定具体值会让回归测试随分数漂移)
        rc = main(["--repo", str(ROOT), "--threshold", "15.5"])
        self.assertEqual(rc, 1)

    def test_threshold_gate_passes_at_or_above(self) -> None:
        rc = main(["--repo", str(ROOT), "--threshold", "5"])
        self.assertEqual(rc, 0)


class ErrorPathTests(unittest.TestCase):
    """错误路径：缺失或损坏的输入要返回非 0 退出码，不崩溃。"""

    def test_missing_template_returns_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rc = main(["--repo", td, "--threshold", "7"])
            self.assertEqual(rc, 2)

    def test_missing_template_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                audit(Path(td))

    def test_corrupt_registry_returns_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _clone_repo(Path(td))
            (repo / SUPERPOWERS_REL / "skills-registry.json").write_text(
                "{ this is not json", encoding="utf-8"
            )
            rc = main(["--repo", str(repo), "--threshold", "7"])
            self.assertEqual(rc, 2)

    def test_missing_rules_dir_degrades_dim_1_gracefully(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _clone_repo(Path(td))
            # 删除 rules 目录
            shutil.rmtree(repo / "src/agent_harness/templates/common/.claude/rules")
            card = audit(repo)
            dim1 = next(d for d in card.dimensions if d.id == 1)
            # Dim 1 should be 0 with a diagnostic note, not crash
            self.assertEqual(dim1.score, 0.0)
            self.assertTrue(any("规则目录缺失" in n for n in dim1.notes))


if __name__ == "__main__":
    unittest.main()
