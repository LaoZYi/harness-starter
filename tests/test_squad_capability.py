"""Tests for capability → settings.local.json rendering."""
from __future__ import annotations

import unittest

from agent_harness.squad.capability import (
    CapabilityError,
    render_settings,
)


class RenderSettingsTests(unittest.TestCase):
    def test_scout_denies_write_and_edit(self) -> None:
        s = render_settings("scout")
        deny = s["permissions"]["deny"]
        self.assertIn("Write", deny)
        self.assertIn("Edit", deny)
        self.assertIn("NotebookEdit", deny)

    def test_scout_allows_read_only_tools(self) -> None:
        s = render_settings("scout")
        # At least Read/Glob/Grep should be allowed (or implicit default)
        # We assert that Read is not in deny; allow list is optional
        self.assertNotIn("Read", s["permissions"]["deny"])
        self.assertNotIn("Glob", s["permissions"]["deny"])
        self.assertNotIn("Grep", s["permissions"]["deny"])

    def test_builder_denies_remote_git_and_destructive_bash(self) -> None:
        s = render_settings("builder")
        deny = s["permissions"]["deny"]
        # Should block git push and destructive rm
        deny_flat = " ".join(deny)
        self.assertIn("git push", deny_flat)
        self.assertIn("rm -rf", deny_flat)

    def test_builder_permits_write_edit(self) -> None:
        s = render_settings("builder")
        self.assertNotIn("Write", s["permissions"]["deny"])
        self.assertNotIn("Edit", s["permissions"]["deny"])

    def test_reviewer_denies_write_like_scout(self) -> None:
        s = render_settings("reviewer")
        deny = s["permissions"]["deny"]
        self.assertIn("Write", deny)
        self.assertIn("Edit", deny)

    def test_unknown_capability_raises(self) -> None:
        with self.assertRaises(CapabilityError):
            render_settings("overlord")

    def test_settings_is_json_serializable(self) -> None:
        import json
        for cap in ("scout", "builder", "reviewer", "orchestrator"):
            s = render_settings(cap)
            json.dumps(s)  # must not raise

    # --- Orchestrator capability (Issue #30, 吸收自 multi-agent-coding-system) ---

    def test_orchestrator_denies_all_write_tools(self) -> None:
        """Orchestrator 是战略协调者，禁止直接改代码，只能派工 + 维护 context store。"""
        s = render_settings("orchestrator")
        deny = s["permissions"]["deny"]
        self.assertIn("Write", deny)
        self.assertIn("Edit", deny)
        self.assertIn("MultiEdit", deny)
        self.assertIn("NotebookEdit", deny)

    def test_orchestrator_denies_destructive_bash(self) -> None:
        s = render_settings("orchestrator")
        deny_flat = " ".join(s["permissions"]["deny"])
        self.assertIn("git push", deny_flat)
        self.assertIn("rm -rf", deny_flat)

    def test_orchestrator_allows_read_and_task_tools(self) -> None:
        """允许 Read/Grep/Glob（读上下文）和 Task/TodoWrite（派工）。"""
        deny = render_settings("orchestrator")["permissions"]["deny"]
        self.assertNotIn("Read", deny)
        self.assertNotIn("Grep", deny)
        self.assertNotIn("Glob", deny)
        self.assertNotIn("Task", deny)
        self.assertNotIn("TodoWrite", deny)


if __name__ == "__main__":
    unittest.main()
