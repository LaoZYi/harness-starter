"""Contract tests for doc scenario scaffold (D 方案 — 通用文档场景骨架).

See: docs/superpowers/specs/2026-04-27-doc-scenario-skeleton-spec.md (18 R-IDs)
     docs/superpowers/specs/2026-04-27-doc-scenario-skeleton-plan.md (25 tasks)
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
LFG_TMPL = SUPERPOWERS_CMDS / "lfg.md.tmpl"
LFG_DOC_TMPL = SUPERPOWERS_CMDS / "lfg-doc.md.tmpl"
REGISTRY = ROOT / "src" / "agent_harness" / "templates" / "superpowers" / "skills-registry.json"
PROFILE_DIR = ROOT / "src" / "agent_harness" / "templates" / "common" / ".agent-harness" / "lfg-profiles"
DOC_PRESET = ROOT / "src" / "agent_harness" / "presets" / "document.json"

# Baseline: skill calls in /lfg.md.tmpl at task A.1 lock-in time. R5 contract:
# behavior preserved means this set must remain a subset of /lfg.md.tmpl going forward.
EXPECTED_LFG_SKILL_CALLS = {
    "/ideate", "/brainstorm", "/spec", "/write-plan", "/plan-check",
    "/agent-design-check", "/tdd", "/source-verify", "/execute-plan",
    "/use-worktrees", "/careful", "/debug", "/multi-review", "/verify",
    "/git-commit", "/finish-branch", "/compound", "/lint-lessons",
    "/health", "/retro", "/cso", "/doc-release", "/squad",
    "/dispatch-agents", "/subagent-dev", "/recall",
}

# Code-flavored skills that must NOT appear in /lfg-doc.md.tmpl main body
# (they may be mentioned in a "不做" section explaining what's deliberately skipped).
FORBIDDEN_IN_LFG_DOC = [
    "/tdd", "/git-commit", "/finish-branch", "/multi-review",
    "/verify", "/debug", "/health", "/cso", "/squad",
]

NEW_DOC_SKILLS = ["lfg-doc", "outline-doc", "draft-doc", "review-doc", "finalize-doc"]


# Patterns that indicate "this line invokes the skill" (positive call site).
# Mentions in negation contexts ("不调", "替代", header callouts, comparison tables)
# are descriptive references, not invocations, and must not trip R4.
_INVOKE_PATTERNS = [
    re.compile(r"^\s*\d+\.\s*[`*]*(/[\w-]+)"),     # "1. /tdd ..."
    re.compile(r"(?:运行|调用|跑|执行|串)\s*[`*]*(/[\w-]+)"),  # "运行 /tdd"
    re.compile(r"^\s*-\s*`?(/[\w-]+)`?\s+——"),     # "- /tdd —— description"
]
_NEGATION_MARKERS = ("不调", "不做", "不用", "替代", "代替", "→ 改", "禁止", "**不**", "不**", "不直接", "不自动")


def _strip_negation_sections(text: str) -> str:
    """Strip h2 sections whose heading contains negation keywords.

    Handles '## 不做的事', '## 不调用', '## 禁止', and comparison sections like
    '## 与 /lfg 的关系' (which lists what /lfg-doc deliberately differs from)."""
    out: list[str] = []
    skip = False
    skip_keywords = ("不做", "不调", "禁止", "与 /lfg 的关系", "与 /lfg-doc 的区别")
    for line in text.splitlines():
        if line.startswith("## "):
            skip = any(k in line for k in skip_keywords)
        if not skip:
            out.append(line)
    return "\n".join(out)


def _invoked_skills(text: str) -> set[str]:
    """Extract skills that appear in invocation positions (excluding negation lines).

    Two-layer filter: (1) drop entire negation/comparison sections, (2) drop
    inline negation lines within remaining body."""
    body = _strip_negation_sections(text)
    invoked: set[str] = set()
    for line in body.splitlines():
        # Skip lines that explicitly negate or describe absence
        if any(neg in line for neg in _NEGATION_MARKERS):
            continue
        # Skip table rows (comparison tables list skills descriptively)
        if line.strip().startswith("|"):
            continue
        # Skip block-quote callouts (header summaries)
        if line.strip().startswith(">"):
            continue
        for pat in _INVOKE_PATTERNS:
            for m in pat.finditer(line):
                invoked.add(m.group(1))
    return invoked


class DocScenarioTests(unittest.TestCase):
    # --- A.1 baseline (R5) ---
    def test_lfg_skill_calls_unchanged(self) -> None:
        """R5: /lfg.md.tmpl behavior preserved — every baseline skill still invoked."""
        text = LFG_TMPL.read_text(encoding="utf-8")
        for skill in EXPECTED_LFG_SKILL_CALLS:
            self.assertIn(skill, text, f"/lfg.md.tmpl missing baseline skill {skill}")

    # --- R3 ---
    def test_doc_skills_in_registry(self) -> None:
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        ids = {s["id"] for s in reg["skills"]}
        for skill in NEW_DOC_SKILLS:
            self.assertIn(skill, ids, f"skill {skill} not registered")
            entry = next(s for s in reg["skills"] if s["id"] == skill)
            self.assertFalse(
                entry["expected_in_lfg"],
                f"{skill} should be expected_in_lfg=false (走 /lfg-doc 不走 /lfg)",
            )

    # --- R1, R2 ---
    def test_doc_skill_templates_exist(self) -> None:
        for skill in NEW_DOC_SKILLS:
            p = SUPERPOWERS_CMDS / f"{skill}.md.tmpl"
            self.assertTrue(p.is_file(), f"missing {p}")
            self.assertGreater(p.stat().st_size, 100, f"{p} suspiciously small")

    # --- R4 ---
    def test_lfg_doc_does_not_call_code_skills(self) -> None:
        text = LFG_DOC_TMPL.read_text(encoding="utf-8")
        invoked = _invoked_skills(text)
        for forbidden in FORBIDDEN_IN_LFG_DOC:
            self.assertNotIn(
                forbidden, invoked,
                f"/lfg-doc.md.tmpl positively invokes forbidden code-skill {forbidden}",
            )

    def test_lfg_doc_does_not_call_git_or_finish_branch(self) -> None:
        """Secondary guard: /git-commit and /finish-branch must not be invoked
        positively (negation/comparison sections are stripped by _invoked_skills)."""
        text = LFG_DOC_TMPL.read_text(encoding="utf-8")
        invoked = _invoked_skills(text)
        self.assertNotIn("/git-commit", invoked)
        self.assertNotIn("/finish-branch", invoked)

    # --- R6 ---
    def test_lfg_profiles_skeleton_files_exist(self) -> None:
        for fname in ["code.yaml.tmpl", "doc.yaml.tmpl", "README.md.tmpl"]:
            p = PROFILE_DIR / fname
            self.assertTrue(p.is_file(), f"missing {p}")

    # --- R7 ---
    def test_profile_yaml_has_required_fields(self) -> None:
        for yaml_name in ["code.yaml.tmpl", "doc.yaml.tmpl"]:
            text = (PROFILE_DIR / yaml_name).read_text(encoding="utf-8")
            self.assertIn("schema_version: 1", text)
            self.assertIn("name:", text)
            self.assertIn("description:", text)
            self.assertIn("stages:", text)

    # --- R8 ---
    def test_code_profile_matches_lfg(self) -> None:
        text = (PROFILE_DIR / "code.yaml.tmpl").read_text(encoding="utf-8")
        skills_in_yaml = set(re.findall(r"^\s*skill:\s*([\w-]+)", text, re.MULTILINE))
        lfg_text = LFG_TMPL.read_text(encoding="utf-8")
        for skill in skills_in_yaml:
            self.assertIn(
                f"/{skill}", lfg_text,
                f"code.yaml lists /{skill} but /lfg.md.tmpl does not call it",
            )

    # --- R9 ---
    def test_doc_profile_matches_lfg_doc(self) -> None:
        text = (PROFILE_DIR / "doc.yaml.tmpl").read_text(encoding="utf-8")
        skills_in_yaml = set(re.findall(r"^\s*skill:\s*([\w-]+)", text, re.MULTILINE))
        lfg_doc_text = LFG_DOC_TMPL.read_text(encoding="utf-8")
        for skill in skills_in_yaml:
            self.assertIn(
                f"/{skill}", lfg_doc_text,
                f"doc.yaml lists /{skill} but /lfg-doc.md.tmpl does not call it",
            )

    # --- R10 ---
    def test_document_preset_exists(self) -> None:
        self.assertTrue(DOC_PRESET.is_file())
        d = json.loads(DOC_PRESET.read_text(encoding="utf-8"))
        for k in (
            "behavior_change_definition", "architecture_focus", "release_checks",
            "default_done_criteria", "workflow_skills_summary", "exclude_rules",
        ):
            self.assertIn(k, d)

    # --- R11, R12, R13 ---
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

    def test_init_document_renders_full_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "doc-proj"
            self._run_init("document", target)
            for skill in NEW_DOC_SKILLS:
                self.assertTrue(
                    (target / ".claude/commands" / f"{skill}.md").is_file(),
                    f"missing rendered command {skill}.md",
                )
            for f in ["code.yaml", "doc.yaml", "README.md"]:
                self.assertTrue(
                    (target / ".agent-harness/lfg-profiles" / f).is_file(),
                    f"missing rendered profile {f}",
                )

    def test_init_other_types_get_lfg_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "code-proj"
            self._run_init("backend-service", target)
            self.assertTrue((target / ".claude/commands/lfg.md").is_file())
            self.assertTrue((target / ".agent-harness/lfg-profiles/code.yaml").is_file())
            self.assertTrue((target / ".agent-harness/lfg-profiles/doc.yaml").is_file())

    def test_no_superpowers_skips_doc_skills(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "no-sp-doc"
            self._run_init("document", target, no_superpowers=True)
            self.assertFalse((target / ".claude/commands/lfg-doc.md").is_file())
            # lfg-profiles 在 common/ 下，应仍渲染
            self.assertTrue((target / ".agent-harness/lfg-profiles/doc.yaml").is_file())

    # --- R14 ---
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
        # audit JSON: {"total": <float>, "max_total": <float>, ...}
        self.assertGreaterEqual(data["total"], 7.0,
            f"lfg audit total {data.get('total')} < 7.0 baseline")


if __name__ == "__main__":
    unittest.main()
