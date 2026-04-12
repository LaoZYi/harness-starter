"""Tests for tmux command construction and environment checks (mocked subprocess)."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from agent_harness.squad.tmux import (
    TmuxError,
    build_new_session_cmd,
    build_new_window_cmd,
    ensure_tmux_available,
)


class TmuxCommandConstructionTests(unittest.TestCase):
    def test_new_session_cmd_is_detached_and_named(self) -> None:
        cmd = build_new_session_cmd(session="squad-abc")
        self.assertEqual(cmd[0], "tmux")
        self.assertIn("new-session", cmd)
        self.assertIn("-d", cmd)
        self.assertIn("-s", cmd)
        self.assertIn("squad-abc", cmd)

    def test_new_window_cmd_includes_worktree_and_prompt(self) -> None:
        cmd = build_new_window_cmd(
            session="squad-abc",
            window="builder-1",
            cwd="/tmp/wt/builder-1",
            system_prompt_file="/tmp/wt/builder-1/.claude/squad-context.md",
            task_prompt_file="/tmp/wt/builder-1/task-prompt.md",
        )
        joined = " ".join(cmd)
        self.assertIn("new-window", cmd)
        self.assertIn("squad-abc", joined)
        self.assertIn("builder-1", joined)
        self.assertIn("/tmp/wt/builder-1", joined)
        self.assertIn("--append-system-prompt", joined)
        self.assertIn("squad-context.md", joined)
        self.assertIn("task-prompt.md", joined)

    def test_session_name_rejects_shell_metacharacters(self) -> None:
        with self.assertRaises(TmuxError):
            build_new_session_cmd(session="bad; rm -rf /")

    def test_window_name_rejects_shell_metacharacters(self) -> None:
        with self.assertRaises(TmuxError):
            build_new_window_cmd(
                session="squad-ok",
                window="bad`cmd`",
                cwd="/tmp",
                system_prompt_file="/tmp/a.md",
                task_prompt_file="/tmp/b.md",
            )

    def test_path_with_spaces_is_quoted(self) -> None:
        """P0-1: cwd / prompt file paths containing spaces must not break the subshell."""
        cmd = build_new_window_cmd(
            session="squad-ok",
            window="w1",
            cwd="/Users/alice/my projects/repo",
            system_prompt_file="/Users/alice/my projects/repo/.claude/ctx.md",
            task_prompt_file="/Users/alice/my projects/repo/task.md",
        )
        shell_cmd = cmd[-1]
        # shlex.quote wraps paths-with-spaces in single quotes.
        self.assertIn("'/Users/alice/my projects/repo'", shell_cmd)
        self.assertIn("'/Users/alice/my projects/repo/.claude/ctx.md'", shell_cmd)

    def test_path_with_backtick_cannot_inject(self) -> None:
        """P0-1: backtick in path must not be interpreted by the shell."""
        cmd = build_new_window_cmd(
            session="squad-ok",
            window="w1",
            cwd="/tmp/good",
            system_prompt_file="/tmp/evil`rm -rf /`.md",
            task_prompt_file="/tmp/t.md",
        )
        shell_cmd = cmd[-1]
        # shlex.quote escapes backticks inside single quotes (single quotes are
        # split and re-joined), so the raw `rm -rf /` sequence must appear wrapped.
        self.assertNotIn("$(rm", shell_cmd)
        # It should appear inside quoted form
        self.assertIn("rm -rf", shell_cmd)


class TmuxAvailabilityTests(unittest.TestCase):
    @patch("agent_harness.squad.tmux.shutil.which")
    def test_missing_tmux_raises_friendly_error(self, m_which: MagicMock) -> None:
        m_which.return_value = None
        with self.assertRaises(TmuxError) as ctx:
            ensure_tmux_available()
        msg = str(ctx.exception)
        self.assertIn("tmux", msg.lower())
        # Should hint installation
        self.assertTrue("brew" in msg.lower() or "apt" in msg.lower() or "安装" in msg)

    @patch("agent_harness.squad.tmux.subprocess.run")
    @patch("agent_harness.squad.tmux.shutil.which")
    def test_tmux_present_returns_version_string(self, m_which: MagicMock, m_run: MagicMock) -> None:
        m_which.return_value = "/usr/bin/tmux"
        m_run.return_value = MagicMock(stdout="tmux 3.6a\n", returncode=0)
        version = ensure_tmux_available()
        self.assertIn("3.", version)


if __name__ == "__main__":
    unittest.main()
