"""Contract tests for skills-registry.json + skills_registry.py + skills_lint.py.

Issue #27: skills-registry.json is the SSOT for all skills; downstream
consumers (which-skill.md.tmpl, lfg.md.tmpl, test_lfg_coverage.py,
harness skills lint) must stay in sync.
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

from agent_harness.skills_registry import (  # noqa: E402
    PLACEHOLDER_COVERAGE_TABLE,
    PLACEHOLDER_DECISION_TREE,
    PLACEHOLDER_INDEX_BY_PHASE,
    apply_to_target,
    expected_in_lfg,
    expected_not_in_lfg,
    load_registry,
    render_all,
    render_decision_tree,
    render_lfg_coverage_table,
    render_skill_index_by_phase,
)
from agent_harness import skills_lint  # noqa: E402

SP_TEMPLATE = ROOT / "src" / "agent_harness" / "templates" / "superpowers"


class RegistryLoadTests(unittest.TestCase):
    """R-001: registry parses + has expected shape."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(SP_TEMPLATE)

    def test_skill_count_is_36(self) -> None:
        # +1 for digest-meeting (2026-04-16)
        self.assertEqual(len(self.registry["skills"]), 36)

    def test_in_lfg_count_matches_excluded(self) -> None:
        in_lfg = expected_in_lfg(self.registry)
        not_in = expected_not_in_lfg(self.registry)
        self.assertEqual(len(in_lfg) + len(not_in), 36)
        self.assertEqual(len(not_in), 8)  # 8 meta-excluded skills (+digest-meeting)

    def test_excluded_skills_have_reason(self) -> None:
        for skill in self.registry["skills"]:
            if not skill["expected_in_lfg"]:
                self.assertIn(
                    "exclusion_reason", skill,
                    f"{skill['id']} excluded but missing exclusion_reason"
                )
                self.assertTrue(skill["exclusion_reason"].strip())

    def test_no_duplicate_ids(self) -> None:
        ids = [s["id"] for s in self.registry["skills"]]
        self.assertEqual(len(ids), len(set(ids)))


class RenderTests(unittest.TestCase):
    """R-002 / R-003: renderers produce expected blocks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(SP_TEMPLATE)

    def test_decision_tree_includes_in_lfg_skills_with_label(self) -> None:
        tree = render_decision_tree(self.registry)
        # Every skill with decision_tree_label must appear
        for skill in self.registry["skills"]:
            if skill.get("decision_tree_label"):
                self.assertIn(f"/{skill['id']}", tree, f"missing /{skill['id']}")

    def test_index_by_phase_has_three_sections(self) -> None:
        idx = render_skill_index_by_phase(self.registry)
        self.assertIn("流程类", idx)
        self.assertIn("实现类", idx)
        self.assertIn("收尾类", idx)
        self.assertNotIn("元任务", idx)  # meta excluded from phase index

    def test_coverage_table_has_all_in_lfg_skills(self) -> None:
        table = render_lfg_coverage_table(self.registry)
        for skill in expected_in_lfg(self.registry):
            self.assertIn(skill, table, f"{skill} missing from coverage table")

    def test_coverage_table_has_excluded_section(self) -> None:
        table = render_lfg_coverage_table(self.registry)
        self.assertIn("元任务", table)
        for skill, reason in expected_not_in_lfg(self.registry).items():
            self.assertIn(skill, table)
            self.assertIn(reason, table)

    def test_render_all_replaces_three_placeholders(self) -> None:
        template = (
            f"head\n{PLACEHOLDER_DECISION_TREE}\n"
            f"middle\n{PLACEHOLDER_INDEX_BY_PHASE}\n"
            f"tail\n{PLACEHOLDER_COVERAGE_TABLE}"
        )
        out = render_all(template, self.registry)
        self.assertNotIn(PLACEHOLDER_DECISION_TREE, out)
        self.assertNotIn(PLACEHOLDER_INDEX_BY_PHASE, out)
        self.assertNotIn(PLACEHOLDER_COVERAGE_TABLE, out)


class LintTests(unittest.TestCase):
    """R-005: harness skills lint correctness."""

    def test_lint_passes_on_clean_repo(self) -> None:
        ok, errors = skills_lint.run(ROOT)
        self.assertTrue(ok, f"unexpected lint errors: {errors}")
        self.assertEqual(errors, [])

    def test_lint_detects_orphan_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            self._mirror_repo(tmp_root)
            # inject an orphan .md.tmpl file
            orphan = (
                tmp_root / "src" / "agent_harness" / "templates"
                / "superpowers" / ".claude" / "commands" / "ghost-skill.md.tmpl"
            )
            orphan.write_text("# Ghost Skill\n", encoding="utf-8")
            ok, errors = skills_lint.run(tmp_root)
            self.assertFalse(ok)
            self.assertTrue(
                any("ghost-skill" in e and "orphan" in e for e in errors),
                f"expected orphan error, got: {errors}"
            )

    def test_lint_detects_registry_skill_without_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            self._mirror_repo(tmp_root)
            registry_path = (
                tmp_root / "src" / "agent_harness" / "templates"
                / "superpowers" / "skills-registry.json"
            )
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data["skills"].append({
                "id": "phantom-skill",
                "name": "Phantom",
                "category": "process",
                "one_line": "x",
                "triggers": [],
                "decision_tree_label": None,
                "lfg_stage": [],
                "expected_in_lfg": False,
                "exclusion_reason": "test fixture",
            })
            registry_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            ok, errors = skills_lint.run(tmp_root)
            self.assertFalse(ok)
            self.assertTrue(
                any("phantom-skill" in e for e in errors),
                f"expected phantom-skill error, got: {errors}"
            )

    def _mirror_repo(self, dest: Path) -> None:
        """Copy minimal subset of repo for lint testing."""
        src_pkg = ROOT / "src" / "agent_harness"
        dst_pkg = dest / "src" / "agent_harness"
        # Only need templates/ for lint
        shutil.copytree(src_pkg / "templates", dst_pkg / "templates")


class ApplyToTargetTests(unittest.TestCase):
    """R-002 / R-003: apply_to_target rewrites materialized files."""

    def test_apply_replaces_placeholders_in_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            cmds = target / ".claude" / "commands"
            cmds.mkdir(parents=True)
            (cmds / "which-skill.md").write_text(
                f"X{PLACEHOLDER_DECISION_TREE}Y", encoding="utf-8"
            )
            (cmds / "lfg.md").write_text(
                f"A{PLACEHOLDER_COVERAGE_TABLE}B", encoding="utf-8"
            )
            written = apply_to_target(SP_TEMPLATE, target)
            self.assertEqual(set(written), {
                ".claude/commands/which-skill.md",
                ".claude/commands/lfg.md",
            })
            usp = (cmds / "which-skill.md").read_text(encoding="utf-8")
            lfg = (cmds / "lfg.md").read_text(encoding="utf-8")
            self.assertNotIn(PLACEHOLDER_DECISION_TREE, usp)
            self.assertNotIn(PLACEHOLDER_COVERAGE_TABLE, lfg)
            self.assertIn("/tdd", usp)  # decision tree should mention /tdd
            self.assertIn("/compound", lfg)  # coverage table mentions /compound


if __name__ == "__main__":
    unittest.main()
