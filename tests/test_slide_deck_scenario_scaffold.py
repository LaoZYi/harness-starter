"""Contract tests for slide-deck scenario scaffold (D 方案 — 第 2 个非代码场景).

Mirrors test_doc_scenario_scaffold.py. The slide-deck project type reuses
the bottom 5 doc skills (outline-doc / draft-doc / review-doc / finalize-doc),
but exposes a parallel entrypoint /lfg-slide whose behavior is described
strictly in lfg-slide.md.tmpl (not /lfg-doc).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPERPOWERS_CMDS = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / ".claude" / "commands"
LFG_SLIDE_TMPL = SUPERPOWERS_CMDS / "lfg-slide.md.tmpl"
REGISTRY = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / "skills-registry.json"
PROFILE_DIR = ROOT / "src" / "agent_harness" / "templates" / "common" / ".agent-harness" / "lfg-profiles"
SLIDE_PRESET = ROOT / "src" / "agent_harness" / "presets" / "slide-deck.json"
SLIDE_RULES_TMPL = (
    ROOT / "src" / "agent_harness" / "templates" / "slide-deck"
    / ".claude" / "rules" / "slide-conventions.md.tmpl"
)

# Code-flavored skills that must NOT appear in /lfg-slide.md.tmpl main body
# (mirror of FORBIDDEN_IN_LFG_DOC; slide reuses doc bottom skills, not code skills).
FORBIDDEN_IN_LFG_SLIDE = [
    "/tdd", "/git-commit", "/finish-branch", "/multi-review",
    "/verify", "/debug", "/health", "/cso", "/squad",
]

# Underlying doc skills that /lfg-slide is expected to call (strict parallel
# to /lfg-doc — slide reuses them rather than opening /outline-slide etc).
EXPECTED_DOC_SKILLS_IN_LFG_SLIDE = [
    "/outline-doc", "/draft-doc", "/review-doc", "/finalize-doc",
]

_INVOKE_PATTERNS = [
    re.compile(r"^\s*\d+\.\s*[`*]*(/[\w-]+)"),
    re.compile(r"(?:运行|调用|跑|执行|串)\s*[`*]*(/[\w-]+)"),
    re.compile(r"^\s*-\s*`?(/[\w-]+)`?\s+——"),
]
_NEGATION_MARKERS = ("不调", "不做", "不用", "替代", "代替", "→ 改", "禁止", "**不**", "不**", "不直接", "不自动")


def _strip_negation_sections(text: str) -> str:
    out: list[str] = []
    skip = False
    skip_keywords = ("不做", "不调", "禁止", "与 /lfg 的关系", "与 /lfg-doc 的区别", "与 /lfg-doc 的关系")
    for line in text.splitlines():
        if line.startswith("## "):
            skip = any(k in line for k in skip_keywords)
        if not skip:
            out.append(line)
    return "\n".join(out)


def _invoked_skills(text: str) -> set[str]:
    body = _strip_negation_sections(text)
    invoked: set[str] = set()
    for line in body.splitlines():
        if any(neg in line for neg in _NEGATION_MARKERS):
            continue
        if line.strip().startswith("|"):
            continue
        if line.strip().startswith(">"):
            continue
        for pat in _INVOKE_PATTERNS:
            for m in pat.finditer(line):
                invoked.add(m.group(1))
    return invoked


class SlideDeckScenarioTests(unittest.TestCase):
    # --- R1: project_type registered ---
    def test_project_type_registered_in_discovery(self) -> None:
        from agent_harness.discovery import PROJECT_TYPES
        self.assertIn("slide-deck", PROJECT_TYPES)

    def test_project_type_registered_in_init_flow(self) -> None:
        from agent_harness.init_flow import PROJECT_TYPE_CHOICES
        self.assertIn("slide-deck", PROJECT_TYPE_CHOICES)

    # --- R2: conventions tmpl exists ---
    def test_slide_conventions_tmpl_exists(self) -> None:
        self.assertTrue(SLIDE_RULES_TMPL.is_file(), f"missing {SLIDE_RULES_TMPL}")
        self.assertGreater(SLIDE_RULES_TMPL.stat().st_size, 100,
                           f"{SLIDE_RULES_TMPL} suspiciously small")

    # --- R3: lfg-profile tmpl exists with required fields ---
    def test_slide_profile_yaml_has_required_fields(self) -> None:
        p = PROFILE_DIR / "slide-deck.yaml.tmpl"
        self.assertTrue(p.is_file(), f"missing {p}")
        text = p.read_text(encoding="utf-8")
        self.assertIn("schema_version: 1", text)
        self.assertIn("name:", text)
        self.assertIn("description:", text)
        self.assertIn("stages:", text)

    # --- R4: preset exists with required fields ---
    def test_slide_preset_exists(self) -> None:
        self.assertTrue(SLIDE_PRESET.is_file(), f"missing {SLIDE_PRESET}")
        d = json.loads(SLIDE_PRESET.read_text(encoding="utf-8"))
        for k in (
            "behavior_change_definition", "architecture_focus", "release_checks",
            "default_done_criteria", "workflow_skills_summary", "exclude_rules",
        ):
            self.assertIn(k, d, f"slide-deck.json missing field {k}")

    # --- R5: profile stages map to /lfg-slide.md.tmpl ---
    def test_slide_profile_matches_lfg_slide(self) -> None:
        text = (PROFILE_DIR / "slide-deck.yaml.tmpl").read_text(encoding="utf-8")
        skills_in_yaml = set(re.findall(r"^\s*skill:\s*([\w-]+)", text, re.MULTILINE))
        lfg_slide_text = LFG_SLIDE_TMPL.read_text(encoding="utf-8")
        for skill in skills_in_yaml:
            self.assertIn(
                f"/{skill}", lfg_slide_text,
                f"slide-deck.yaml lists /{skill} but /lfg-slide.md.tmpl does not call it",
            )

    # --- R6: lfg-slide registered in skills-registry ---
    def test_lfg_slide_in_registry(self) -> None:
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        ids = {s["id"] for s in reg["skills"]}
        self.assertIn("lfg-slide", ids, "skill lfg-slide not registered")
        entry = next(s for s in reg["skills"] if s["id"] == "lfg-slide")
        self.assertFalse(
            entry["expected_in_lfg"],
            "lfg-slide should be expected_in_lfg=false (走 /lfg-slide 不走 /lfg)",
        )

    # --- R7: lfg-slide.md.tmpl exists ---
    def test_lfg_slide_template_exists(self) -> None:
        self.assertTrue(LFG_SLIDE_TMPL.is_file(), f"missing {LFG_SLIDE_TMPL}")
        self.assertGreater(LFG_SLIDE_TMPL.stat().st_size, 100,
                           f"{LFG_SLIDE_TMPL} suspiciously small")

    # --- R8: lfg-slide does NOT invoke forbidden code skills ---
    def test_lfg_slide_does_not_call_code_skills(self) -> None:
        text = LFG_SLIDE_TMPL.read_text(encoding="utf-8")
        invoked = _invoked_skills(text)
        for forbidden in FORBIDDEN_IN_LFG_SLIDE:
            self.assertNotIn(
                forbidden, invoked,
                f"/lfg-slide.md.tmpl positively invokes forbidden code-skill {forbidden}",
            )

    def test_lfg_slide_invokes_doc_skills(self) -> None:
        """slide reuses doc bottom skills strictly parallel to /lfg-doc."""
        text = LFG_SLIDE_TMPL.read_text(encoding="utf-8")
        invoked = _invoked_skills(text)
        for skill in EXPECTED_DOC_SKILLS_IN_LFG_SLIDE:
            self.assertIn(
                skill, invoked,
                f"/lfg-slide.md.tmpl missing expected doc skill {skill}",
            )

    def test_lfg_slide_does_not_call_git_or_finish_branch(self) -> None:
        """Secondary guard mirroring doc test: /git-commit and /finish-branch
        must not be invoked positively (negation/comparison sections stripped)."""
        text = LFG_SLIDE_TMPL.read_text(encoding="utf-8")
        invoked = _invoked_skills(text)
        self.assertNotIn("/git-commit", invoked)
        self.assertNotIn("/finish-branch", invoked)

    def test_underlying_doc_skills_available_for_slide(self) -> None:
        """slide-deck depends on 4 doc bottom skills being registered.
        Asserted from slide's perspective so regressions surface independently
        from doc-scenario tests."""
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        ids = {s["id"] for s in reg["skills"]}
        for skill in ("outline-doc", "draft-doc", "review-doc", "finalize-doc"):
            self.assertIn(
                skill, ids,
                f"slide-deck depends on {skill} but it is not registered",
            )

    # --- R9: harness init --project-type slide-deck renders full scaffold ---
    def _run_init(self, type_arg: str, target_dir: Path, no_superpowers: bool = False) -> None:
        cmd = [
            sys.executable, "-m", "agent_harness", "init",
            "--project-type", type_arg, str(target_dir), "--non-interactive",
        ]
        if no_superpowers:
            cmd.append("--no-superpowers")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            self.fail(f"harness init failed: stdout={result.stdout}\nstderr={result.stderr}")

    def test_init_slide_deck_renders_full_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "slide-proj"
            self._run_init("slide-deck", target)
            # Conventions rule rendered
            self.assertTrue(
                (target / ".claude/rules/slide-conventions.md").is_file(),
                "missing rendered slide-conventions.md",
            )
            # /lfg-slide command rendered
            self.assertTrue(
                (target / ".claude/commands/lfg-slide.md").is_file(),
                "missing rendered lfg-slide.md",
            )
            # Bottom 4 doc skills also rendered (slide reuses them)
            for skill in ("outline-doc", "draft-doc", "review-doc", "finalize-doc"):
                self.assertTrue(
                    (target / ".claude/commands" / f"{skill}.md").is_file(),
                    f"missing rendered command {skill}.md",
                )
            # lfg-profile yaml rendered
            self.assertTrue(
                (target / ".agent-harness/lfg-profiles/slide-deck.yaml").is_file(),
                "missing rendered lfg-profile slide-deck.yaml",
            )

    # --- R10: --no-superpowers still renders conventions + lfg-profiles ---
    def test_no_superpowers_skips_slide_skills(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "no-sp-slide"
            self._run_init("slide-deck", target, no_superpowers=True)
            # /lfg-slide command should NOT be rendered
            self.assertFalse(
                (target / ".claude/commands/lfg-slide.md").is_file(),
                "lfg-slide.md should not be rendered with --no-superpowers",
            )
            # But conventions and lfg-profiles still render (they're outside superpowers/)
            self.assertTrue(
                (target / ".claude/rules/slide-conventions.md").is_file(),
                "conventions rule should render even with --no-superpowers",
            )
            self.assertTrue(
                (target / ".agent-harness/lfg-profiles/slide-deck.yaml").is_file(),
                "lfg-profile should render even with --no-superpowers",
            )

    # --- R11: lfg audit not regressed ---
    def test_lfg_audit_score_not_regressed(self) -> None:
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [sys.executable, "-m", "agent_harness", "lfg", "audit", "--json"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"harness lfg audit failed: stderr={result.stderr}",
        )
        data = json.loads(result.stdout)
        self.assertGreaterEqual(
            data["total"], 7.0,
            f"lfg audit total {data.get('total')} < 7.0 baseline",
        )


if __name__ == "__main__":
    unittest.main()
