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
        allow = s["permissions"].get("allow", [])
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
        for cap in ("scout", "builder", "reviewer"):
            s = render_settings(cap)
            json.dumps(s)  # must not raise


if __name__ == "__main__":
    unittest.main()
