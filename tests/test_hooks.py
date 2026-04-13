"""Integration tests for the generated .claude/hooks/ shell scripts.

Covers Issue #13 — Stop + PreCompact hooks absorbed from MemPalace.

Approach: spawn the real bash script, feed stdin JSON, inspect stdout +
exit code + side effects. We do NOT mock — hooks must work under Claude
Code's actual invocation contract (verified via /source-verify at plan time).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "hooks" / "stop.sh.tmpl"
PRECOMPACT_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "hooks" / "pre-compact.sh.tmpl"
SETTINGS_TMPL = ROOT / "src" / "agent_harness" / "templates" / "common" / ".claude" / "settings.json.tmpl"


def _prepare_project(tmp: Path, current_task_body: str | None) -> Path:
    """Render hook scripts into a sandbox project and return project root."""
    proj = tmp / "proj"
    (proj / ".agent-harness").mkdir(parents=True)
    (proj / ".claude" / "hooks").mkdir(parents=True)
    # Copy scripts (tmpl content is plain bash — no {{vars}} in hooks).
    (proj / ".claude" / "hooks" / "stop.sh").write_text(
        STOP_TMPL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (proj / ".claude" / "hooks" / "pre-compact.sh").write_text(
        PRECOMPACT_TMPL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    if current_task_body is not None:
        (proj / ".agent-harness" / "current-task.md").write_text(
            current_task_body, encoding="utf-8"
        )
    return proj


def _run_stop(proj: Path, stdin_json: str = "{}") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(proj / ".claude" / "hooks" / "stop.sh")],
        input=stdin_json, capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(proj), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def _run_precompact(proj: Path, stdin_json: str = '{"trigger":"auto"}') -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(proj / ".claude" / "hooks" / "pre-compact.sh")],
        input=stdin_json, capture_output=True, text=True,
        env={"CLAUDE_PROJECT_DIR": str(proj), "PATH": "/usr/bin:/bin:/usr/local/bin",
             "HARNESS_AGENT": "test-runner"},
    )


class StopHookBehaviorTests(unittest.TestCase):
    """Verify the four-way decision logic."""

    def test_no_current_task_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=None)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")  # no JSON → pass

    def test_empty_current_task_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_awaiting_verification_passes(self) -> None:
        body = "# Current Task\n\n## 状态：待验证\n\n- [ ] 归档与收尾\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             f"Expected pass for 待验证 state, got: {r.stdout!r}")

    def test_unchecked_checkbox_blocks(self) -> None:
        body = "# Current Task\n\n- [x] 第1步\n- [ ] 第2步未完成\n- [ ] 第3步\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIn("current-task.md", data["reason"])
            self.assertIn("checkbox", data["reason"])

    def test_all_checked_passes(self) -> None:
        body = "# Current Task\n\n- [x] 第1步\n- [x] 第2步\n- [x] 第3步\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_skip_sentinel_overrides_unchecked(self) -> None:
        """Manual escape hatch: touch .stop-hook-skip to bypass the guard."""
        body = "# Current Task\n\n- [ ] 未完成但我要强制停\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            (proj / ".agent-harness" / ".stop-hook-skip").touch()
            r = _run_stop(proj)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "",
                             "skip sentinel must bypass the block")

    def test_block_reason_is_valid_json_with_multiline(self) -> None:
        """The reason is multi-line + contains quotes and Chinese — must be valid JSON."""
        body = "# Current Task\n- [ ] step one\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            r = _run_stop(proj)
            # Parse must not raise
            data = json.loads(r.stdout)
            self.assertEqual(data["decision"], "block")
            self.assertIsInstance(data["reason"], str)
            # Must contain an actual newline (JSON unescape handles it)
            self.assertIn("\n", data["reason"])

    def test_consumes_stdin_without_hang(self) -> None:
        """Hook must not hang on stdin; Claude Code sends JSON we discard."""
        body = "# Current Task\n- [x] done\n"
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body=body)
            stdin_json = json.dumps({
                "session_id": "abc", "hook_event_name": "Stop",
                "transcript_path": "/tmp/t.jsonl",
            })
            r = _run_stop(proj, stdin_json=stdin_json)
            self.assertEqual(r.returncode, 0)


class PreCompactHookTests(unittest.TestCase):
    def test_appends_audit_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj, stdin_json='{"trigger":"auto"}')
            self.assertEqual(r.returncode, 0, r.stderr)
            audit = proj / ".agent-harness" / "audit.jsonl"
            self.assertTrue(audit.is_file())
            line = audit.read_text(encoding="utf-8").strip()
            data = json.loads(line)
            self.assertEqual(data["op"], "update")
            self.assertEqual(data["file"], "current-task.md")
            self.assertEqual(data["agent"], "test-runner")
            self.assertIn("pre-compact", data["summary"])
            self.assertIn("auto", data["summary"])

    def test_emits_stderr_hint(self) -> None:
        """Claude Code injects stderr into system-message — must contain guidance."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj)
            self.assertIn("压缩", r.stderr)
            self.assertIn("current-task.md", r.stderr)
            self.assertIn("/compound", r.stderr)

    def test_does_not_block_on_malformed_stdin(self) -> None:
        """Even with garbage stdin, PreCompact must not fail (no decision control)."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = _prepare_project(Path(tmp), current_task_body="")
            r = _run_precompact(proj, stdin_json="not-json-at-all")
            self.assertEqual(r.returncode, 0)
            # audit must still be written with trigger=unknown
            audit = proj / ".agent-harness" / "audit.jsonl"
            self.assertTrue(audit.is_file())
            self.assertIn("unknown", audit.read_text(encoding="utf-8"))


class SettingsJsonContractTests(unittest.TestCase):
    """Verify settings.json.tmpl has the right structure per /source-verify findings."""

    def _load(self) -> dict:
        raw = SETTINGS_TMPL.read_text(encoding="utf-8")
        # Template contains {{test_command_shell}} — strip for JSON parse
        stripped = raw.replace("{{test_command_shell}}", "TEST_CMD_PLACEHOLDER")
        return json.loads(stripped)

    def test_has_stop_and_precompact(self) -> None:
        s = self._load()
        self.assertIn("Stop", s["hooks"])
        self.assertIn("PreCompact", s["hooks"])

    def test_stop_has_no_matcher(self) -> None:
        """Per docs: Stop doesn't support matcher, adding it is silently ignored.
        We omit to stay spec-compliant."""
        s = self._load()
        for block in s["hooks"]["Stop"]:
            self.assertNotIn("matcher", block,
                             "Stop hook must not declare a matcher field (spec: not supported)")

    def test_stop_command_invokes_stop_sh(self) -> None:
        s = self._load()
        cmd = s["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("stop.sh", cmd)

    def test_precompact_command_invokes_pre_compact_sh(self) -> None:
        s = self._load()
        cmd = s["hooks"]["PreCompact"][0]["hooks"][0]["command"]
        self.assertIn("pre-compact.sh", cmd)

    def test_preserves_existing_events(self) -> None:
        """Regression guard — adding Stop/PreCompact must not drop SessionStart/PreToolUse."""
        s = self._load()
        self.assertIn("SessionStart", s["hooks"])
        self.assertIn("PreToolUse", s["hooks"])


if __name__ == "__main__":
    unittest.main()
