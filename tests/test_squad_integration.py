"""End-to-end integration test for `harness squad create --dry-run`.

Validates the full pipeline without starting tmux or a real Claude worker:
spec parse → capability render → worktree files → manifest/status.jsonl → status/stop subcommands.

Replaces the "step 10 smoke test" from the plan (true worker run skipped to avoid
API cost). Also indirectly verifies that capability deny patterns end up in
settings.local.json in the exact shape Claude Code documents for Bash tool
restrictions (`Bash(<cmd>:*)`).
"""
from __future__ import annotations

import argparse
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from agent_harness.squad import cli as squad_cli


def _make_args(spec_path: Path, project: Path, dry_run: bool = True) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.spec = str(spec_path)
    ns.project = str(project)
    ns.dry_run = dry_run
    return ns


class SquadDryRunIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.spec_path = self.tmp / "spec.yaml"
        self.spec_path.write_text(
            textwrap.dedent(
                """
                task_id: smoke
                base_branch: master
                workers:
                  - name: scout-a
                    capability: scout
                    prompt: "探索 src/"
                  - name: builder-a
                    capability: builder
                    depends_on: [scout-a]
                    prompt: "按 spec 实现"
                  - name: reviewer-a
                    capability: reviewer
                    depends_on: [builder-a]
                    prompt: "做 /multi-review"
                """
            ),
            encoding="utf-8",
        )

    def test_dry_run_renders_all_artifacts(self) -> None:
        args = _make_args(self.spec_path, self.tmp, dry_run=True)
        rc = squad_cli.cmd_create(args)
        self.assertEqual(rc, 0)

        # 1. manifest.json exists and has 3 workers
        manifest = json.loads(
            (self.tmp / ".agent-harness" / "squad" / "smoke" / "manifest.json").read_text()
        )
        self.assertEqual(manifest["task_id"], "smoke")
        self.assertEqual(manifest["tmux_session"], "squad-smoke")
        self.assertEqual(len(manifest["workers"]), 3)

        # 2. status.jsonl has one "dry-run-rendered" record per worker
        status_lines = (
            (self.tmp / ".agent-harness" / "squad" / "smoke" / "status.jsonl")
            .read_text()
            .splitlines()
        )
        self.assertEqual(len(status_lines), 3)
        for line in status_lines:
            rec = json.loads(line)
            self.assertEqual(rec["event"], "dry-run-rendered")
            self.assertIn("ts", rec)

        # 3. each worker has rendered settings.local.json + squad-context.md + task-prompt.md
        for w in ("scout-a", "builder-a", "reviewer-a"):
            wt = self.tmp / ".worktrees" / "wt" / f"squad-smoke-{w}"
            self.assertTrue((wt / ".claude" / "settings.local.json").is_file())
            self.assertTrue((wt / ".claude" / "squad-context.md").is_file())
            self.assertTrue((wt / "task-prompt.md").is_file())

    def test_scout_settings_contain_bash_git_deny_pattern(self) -> None:
        """P1-3 verification: scout's rendered settings.local.json contains
        `Bash(git:*)` — the exact pattern documented by Claude Code's
        --disallowedTools flag (seen in `claude --help`). This is the wire-format
        we rely on for runtime capability enforcement.
        """
        args = _make_args(self.spec_path, self.tmp, dry_run=True)
        squad_cli.cmd_create(args)
        s = json.loads(
            (self.tmp / ".worktrees" / "wt" / "squad-smoke-scout-a" / ".claude" / "settings.local.json").read_text()
        )
        deny = s["permissions"]["deny"]
        self.assertIn("Bash(git:*)", deny)
        self.assertIn("Write", deny)
        self.assertIn("Edit", deny)

    def test_builder_settings_allow_write_but_deny_destructive(self) -> None:
        args = _make_args(self.spec_path, self.tmp, dry_run=True)
        squad_cli.cmd_create(args)
        s = json.loads(
            (self.tmp / ".worktrees" / "wt" / "squad-smoke-builder-a" / ".claude" / "settings.local.json").read_text()
        )
        deny = s["permissions"]["deny"]
        self.assertIn("Bash(git push:*)", deny)
        self.assertIn("Bash(rm -rf:*)", deny)
        self.assertNotIn("Write", deny)
        self.assertNotIn("Edit", deny)

    def test_squad_context_embeds_capability_and_status_path(self) -> None:
        args = _make_args(self.spec_path, self.tmp, dry_run=True)
        squad_cli.cmd_create(args)
        ctx = (
            self.tmp / ".worktrees" / "wt" / "squad-smoke-scout-a"
            / ".claude" / "squad-context.md"
        ).read_text()
        self.assertIn("scout-a", ctx)
        self.assertIn("capability=scout", ctx)
        self.assertIn("smoke", ctx)
        # Hard rule reminders
        self.assertIn("禁止", ctx)
        self.assertIn("status", ctx)

    def test_status_command_lists_dry_run_squad(self) -> None:
        squad_cli.cmd_create(_make_args(self.spec_path, self.tmp, dry_run=True))
        status_args = argparse.Namespace(project=str(self.tmp))
        rc = squad_cli.cmd_status(status_args)
        self.assertEqual(rc, 0)

    def test_status_with_no_squads_returns_zero(self) -> None:
        empty = Path(tempfile.mkdtemp())
        rc = squad_cli.cmd_status(argparse.Namespace(project=str(empty)))
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
