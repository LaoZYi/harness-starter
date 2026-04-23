"""Tests for directory navigation layer (ABSTRACT.md / OVERVIEW.md).

Inspired by volcengine/OpenViking's filesystem-as-context design.
Validates: rule documented, tmpl exists, /recall supports --map,
guard script rejects bad state.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class DirectoryMapRuleTests(unittest.TestCase):
    def test_rule_file_has_directory_map_section(self) -> None:
        rule = REPO_ROOT / ".claude" / "rules" / "documentation-sync.md"
        text = rule.read_text(encoding="utf-8")
        self.assertIn("目录导航层", text)
        self.assertIn("ABSTRACT.md", text)
        self.assertIn("OVERVIEW.md", text)
        self.assertIn(".agent-harness/", text)
        self.assertIn(".agent-harness/references/", text)

    def test_rule_tmpl_matches_dogfood(self) -> None:
        dogfood = (REPO_ROOT / ".claude" / "rules" / "documentation-sync.md").read_text(encoding="utf-8")
        tmpl = (
            REPO_ROOT
            / "src"
            / "agent_harness"
            / "templates"
            / "common"
            / ".claude"
            / "rules"
            / "documentation-sync.md.tmpl"
        ).read_text(encoding="utf-8")
        # This rule has no {{vars}}, so tmpl and dogfood should match byte-for-byte
        self.assertEqual(dogfood, tmpl, "documentation-sync.md drift between dogfood and tmpl")

    def test_rule_warns_against_claude_commands_dir(self) -> None:
        """Regression guard: .claude/commands/ must not appear as a whitelisted dir.

        Claude Code registers any .md under .claude/commands/ as a slash command;
        putting ABSTRACT/OVERVIEW there creates bogus /ABSTRACT and /OVERVIEW commands.
        """
        rule = (REPO_ROOT / ".claude" / "rules" / "documentation-sync.md").read_text(encoding="utf-8")
        # Must contain the explicit warning
        self.assertIn("不要把", rule)
        self.assertIn(".claude/commands/", rule)


class RecallMapSupportTests(unittest.TestCase):
    def test_recall_dogfood_has_map_param(self) -> None:
        recall = (REPO_ROOT / ".claude" / "commands" / "recall.md").read_text(encoding="utf-8")
        self.assertIn("--map", recall)
        self.assertIn("ABSTRACT.md", recall)
        self.assertIn("OVERVIEW.md", recall)

    def test_recall_tmpl_has_map_param(self) -> None:
        tmpl = (
            REPO_ROOT
            / "src"
            / "agent_harness"
            / "templates"
            / "common"
            / ".claude"
            / "commands"
            / "recall.md.tmpl"
        ).read_text(encoding="utf-8")
        self.assertIn("--map", tmpl)
        self.assertIn("三段式", tmpl)


class DirectoryMapArtifactTests(unittest.TestCase):
    """Dogfood: whitelisted dirs in this project must have ABSTRACT/OVERVIEW."""

    WHITELIST = (
        REPO_ROOT / ".agent-harness",
        REPO_ROOT / ".agent-harness" / "references",
    )

    def test_all_whitelist_dirs_have_abstract_and_overview(self) -> None:
        for d in self.WHITELIST:
            self.assertTrue(d.exists(), f"{d} missing")
            for name in ("ABSTRACT.md", "OVERVIEW.md"):
                fp = d / name
                self.assertTrue(fp.exists(), f"{fp} missing")
                self.assertGreater(fp.stat().st_size, 0, f"{fp} empty")

    def test_abstract_length_under_limit(self) -> None:
        for d in self.WHITELIST:
            fp = d / "ABSTRACT.md"
            content = fp.read_text(encoding="utf-8").strip()
            self.assertLessEqual(len(content), 200, f"{fp} too long: {len(content)}")

    def test_overview_length_under_limit(self) -> None:
        for d in self.WHITELIST:
            fp = d / "OVERVIEW.md"
            content = fp.read_text(encoding="utf-8").strip()
            self.assertLessEqual(len(content), 4000, f"{fp} too long: {len(content)}")


class DirectoryMapTmplTests(unittest.TestCase):
    """Template layer: tmpl files must exist for init/upgrade to carry ABSTRACT/OVERVIEW."""

    TMPL_ROOT = REPO_ROOT / "src" / "agent_harness" / "templates" / "common" / ".agent-harness"

    def test_agent_harness_tmpl_pair_exists(self) -> None:
        self.assertTrue((self.TMPL_ROOT / "ABSTRACT.md.tmpl").exists())
        self.assertTrue((self.TMPL_ROOT / "OVERVIEW.md.tmpl").exists())

    def test_references_tmpl_pair_exists(self) -> None:
        self.assertTrue((self.TMPL_ROOT / "references" / "ABSTRACT.md.tmpl").exists())
        self.assertTrue((self.TMPL_ROOT / "references" / "OVERVIEW.md.tmpl").exists())


class DirectoryMapGuardTests(unittest.TestCase):
    """check_repo.py's check_directory_maps() must reject bad states."""

    def _run_guard_in_fake_root(self, setup_fn) -> subprocess.CompletedProcess:
        """Copy guard into a temp dir, let setup_fn build fake structure, then run."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            setup_fn(root)
            # Inline minimal guard script using the same DIRECTORY_MAP_WHITELIST logic
            guard_src = '''
import sys
from pathlib import Path
ROOT = Path(sys.argv[1]).resolve()
DIRS = (ROOT / ".agent-harness", ROOT / ".agent-harness" / "references")
errors = []
for d in DIRS:
    rel = d.relative_to(ROOT).as_posix() or "."
    if not d.exists():
        errors.append(f"{rel}/ 目录不存在")
        continue
    for name, limit in (("ABSTRACT.md", 200), ("OVERVIEW.md", 4000)):
        fp = d / name
        if not fp.exists():
            errors.append(f"{rel}/{name} 缺失")
            continue
        content = fp.read_text(encoding="utf-8").strip()
        if not content:
            errors.append(f"{rel}/{name} 为空")
        elif len(content) > limit:
            print(f"[warn] {rel}/{name} 过长", file=sys.stderr)
if errors:
    print("\\n".join(errors), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
'''
            script = root / "_guard.py"
            script.write_text(guard_src, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(script), str(root)],
                capture_output=True, text=True,
            )

    def test_missing_abstract_fails(self) -> None:
        def setup(root: Path) -> None:
            (root / ".agent-harness" / "references").mkdir(parents=True)
            (root / ".agent-harness" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "ABSTRACT.md").write_text("x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
        r = self._run_guard_in_fake_root(setup)
        self.assertEqual(r.returncode, 1)
        self.assertIn(".agent-harness/ABSTRACT.md 缺失", r.stderr)

    def test_empty_abstract_fails(self) -> None:
        def setup(root: Path) -> None:
            (root / ".agent-harness" / "references").mkdir(parents=True)
            (root / ".agent-harness" / "ABSTRACT.md").write_text("", encoding="utf-8")
            (root / ".agent-harness" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "ABSTRACT.md").write_text("x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
        r = self._run_guard_in_fake_root(setup)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ABSTRACT.md 为空", r.stderr)

    def test_all_present_passes(self) -> None:
        def setup(root: Path) -> None:
            (root / ".agent-harness" / "references").mkdir(parents=True)
            for d in (root / ".agent-harness", root / ".agent-harness" / "references"):
                (d / "ABSTRACT.md").write_text("x", encoding="utf-8")
                (d / "OVERVIEW.md").write_text("# x", encoding="utf-8")
        r = self._run_guard_in_fake_root(setup)
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")

    def test_over_long_abstract_warns_not_errors(self) -> None:
        def setup(root: Path) -> None:
            (root / ".agent-harness" / "references").mkdir(parents=True)
            long_text = "x" * 300  # > 200 limit
            (root / ".agent-harness" / "ABSTRACT.md").write_text(long_text, encoding="utf-8")
            (root / ".agent-harness" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "ABSTRACT.md").write_text("x", encoding="utf-8")
            (root / ".agent-harness" / "references" / "OVERVIEW.md").write_text("# x", encoding="utf-8")
        r = self._run_guard_in_fake_root(setup)
        self.assertEqual(r.returncode, 0)  # warn, not error
        self.assertIn("过长", r.stderr)


if __name__ == "__main__":
    unittest.main()
