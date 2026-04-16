"""Contract tests for /lfg coverage of the framework skill surface.

/lfg is the unified entry-point for day-to-day development tasks; users
should not need to remember 30+ individual skills. These tests lock down
that every skill which *should* be reachable via /lfg is actually
referenced in lfg.md.tmpl at the right pipeline stage.

If a new skill is added, decide whether it's part of the single-task flow
(→ must be wired into /lfg) or a meta/periodic skill (→ add to the
EXPECTED_NOT_IN_LFG list with a justification).
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LFG = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands" / "lfg.md.tmpl"
DOGFOOD_LFG = ROOT / ".claude" / "commands" / "lfg.md"
SKILLS_DIR = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands"
COMMON_DIR = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "commands"


# Skills classification is now sourced from skills-registry.json (Issue #27).
# This avoids drift between which-skill.md.tmpl, lfg.md.tmpl, and the contract test.
# To add/remove skills: edit src/agent_harness/templates/superpowers/skills-registry.json
# and run `harness skills lint .`.
import sys as _sys
_sys.path.insert(0, str(ROOT / "src"))
from agent_harness.skills_registry import (  # noqa: E402
    expected_in_lfg as _expected_in_lfg,
    expected_not_in_lfg as _expected_not_in_lfg,
    load_registry as _load_registry,
)
_REGISTRY = _load_registry(ROOT / "src" / "agent_harness" / "templates" / "superpowers")
EXPECTED_IN_LFG = _expected_in_lfg(_REGISTRY)
EXPECTED_NOT_IN_LFG = _expected_not_in_lfg(_REGISTRY)


def _skill_names() -> set[str]:
    """All skill commands shipped in templates (superpowers + common)."""
    names = set()
    for directory in (SKILLS_DIR, COMMON_DIR):
        for path in directory.glob("*.md.tmpl"):
            names.add("/" + path.stem.removesuffix(".md"))
    return names


class LfgCoverageTests(unittest.TestCase):
    def test_lfg_template_exists(self) -> None:
        self.assertTrue(LFG.is_file(), f"missing {LFG}")

    def test_every_expected_skill_is_mentioned(self) -> None:
        """EXPECTED_IN_LFG is an ever-growing contract — each entry must appear
        somewhere in lfg.md.tmpl. Missing references indicate either:
        (a) the skill was added without wiring into /lfg, or
        (b) the skill is meta/periodic and belongs in EXPECTED_NOT_IN_LFG.
        """
        text = LFG.read_text(encoding="utf-8")
        missing = sorted(s for s in EXPECTED_IN_LFG if s not in text)
        self.assertEqual(
            missing, [],
            f"Skills missing from /lfg pipeline: {missing}. "
            "Wire them into the right stage of lfg.md.tmpl or justify in EXPECTED_NOT_IN_LFG."
        )

    def test_every_shipped_skill_is_classified(self) -> None:
        """Every skill in the template tree must be either IN or NOT_IN the
        /lfg contract — no silent additions. This catches the case where a
        new skill ships without anyone deciding whether it should be in /lfg.
        """
        shipped = _skill_names()
        classified = set(EXPECTED_IN_LFG) | set(EXPECTED_NOT_IN_LFG)
        unclassified = sorted(shipped - classified)
        self.assertEqual(
            unclassified, [],
            f"Skills neither in EXPECTED_IN_LFG nor EXPECTED_NOT_IN_LFG: {unclassified}. "
            "Classify each new skill before shipping."
        )

    def test_not_in_lfg_entries_really_absent_from_call_sites(self) -> None:
        """Meta/periodic skills should not be *commanded* (`运行 /xxx`, `→ /xxx`)
        from the /lfg pipeline, even if their names incidentally appear in prose.
        We check they never appear in an action-verb context.
        """
        text = LFG.read_text(encoding="utf-8")
        action_patterns = [
            re.compile(rf"运行 `{re.escape(skill)}`")
            for skill in EXPECTED_NOT_IN_LFG
        ]
        misused = []
        for skill, pattern in zip(EXPECTED_NOT_IN_LFG, action_patterns):
            if pattern.search(text):
                misused.append(skill)
        # /lint-lessons has a documented "fast 2-item subset" call; it's in
        # EXPECTED_IN_LFG, not NOT_IN. /evolve etc. should not be "运行" from /lfg.
        self.assertEqual(
            misused, [],
            f"Skills flagged as NOT_IN_LFG are being actively invoked from /lfg: {misused}. "
            "Either reclassify or remove the invocation."
        )

    def test_dogfood_synced(self) -> None:
        """Generated .claude/commands/lfg.md must match the template after rendering.
        If this fails, run `make dogfood` after editing lfg.md.tmpl.
        """
        if not DOGFOOD_LFG.is_file():
            self.skipTest("dogfood not applied yet")
        # Cheap heuristic: every expected skill must also appear in dogfood output.
        dogfood_text = DOGFOOD_LFG.read_text(encoding="utf-8")
        missing = sorted(s for s in EXPECTED_IN_LFG if s not in dogfood_text)
        self.assertEqual(
            missing, [],
            f"Dogfood lfg.md out of sync — skills missing: {missing}. Run `make dogfood`."
        )


if __name__ == "__main__":
    unittest.main()
