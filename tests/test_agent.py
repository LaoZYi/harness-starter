"""Tests for agent diary/status module (Issue #14, absorbed from MemPalace)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from agent_harness import agent


def _mk_root(tmp: Path) -> Path:
    root = tmp / "proj"
    (root / ".agent-harness").mkdir(parents=True)
    return root


class InitAgentTests(unittest.TestCase):
    def test_init_creates_dir_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            d = agent.init_agent(root, "agent-1")
            self.assertTrue(d.is_dir())
            self.assertTrue((d / "diary.md").is_file())
            self.assertTrue((d / "status.md").is_file())
            self.assertIn("agent-1", (d / "diary.md").read_text(encoding="utf-8"))

    def test_init_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.init_agent(root, "agent-1")
            agent.diary_append(root, "agent-1", "first entry")
            # Re-init must not clobber
            agent.init_agent(root, "agent-1")
            text = (root / ".agent-harness" / "agents" / "agent-1" / "diary.md").read_text(encoding="utf-8")
            self.assertIn("first entry", text)


class IdValidationTests(unittest.TestCase):
    def test_rejects_uppercase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            with self.assertRaises(agent.AgentError):
                agent.init_agent(root, "Agent-1")

    def test_rejects_shell_metachars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            for bad in ["agent/1", "agent;rm", "../evil", "agent 1", "agent$x", "-leading"]:
                with self.assertRaises(agent.AgentError, msg=f"must reject {bad!r}"):
                    agent.init_agent(root, bad)

    def test_rejects_too_long(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            with self.assertRaises(agent.AgentError):
                agent.init_agent(root, "a" * 32)

    def test_accepts_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            for ok in ["a", "agent-1", "a1b2c3", "x" * 31, "worker-001-scout"]:
                agent.init_agent(root, ok)


class DiaryAppendTests(unittest.TestCase):
    def test_append_adds_timestamped_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            line = agent.diary_append(root, "a1", "first message")
            self.assertTrue(line.startswith("- "))
            self.assertIn("first message", line)
            diary = (root / ".agent-harness" / "agents" / "a1" / "diary.md").read_text(encoding="utf-8")
            self.assertIn("first message", diary)
            self.assertIn("- 20", diary)  # year prefix

    def test_empty_message_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            with self.assertRaises(agent.AgentError):
                agent.diary_append(root, "a1", "")

    def test_append_auto_creates_agent(self) -> None:
        """diary_append without prior init_agent must still work."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.diary_append(root, "a2", "auto-create test")
            self.assertTrue((root / ".agent-harness" / "agents" / "a2" / "diary.md").is_file())

    def test_utf8_message_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.diary_append(root, "a1", "开始扫描 🔍 src/utils/")
            text = (root / ".agent-harness" / "agents" / "a1" / "diary.md").read_text(encoding="utf-8")
            self.assertIn("开始扫描 🔍 src/utils/", text)


class StatusTests(unittest.TestCase):
    def test_set_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.status_set(root, "a1", "waiting on X")
            ts, state = agent.status_read(root, "a1")
            self.assertTrue(ts.startswith("20"))
            self.assertEqual(state, "waiting on X")

    def test_set_overwrites_previous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.status_set(root, "a1", "step 1 running")
            agent.status_set(root, "a1", "step 2 running")
            _, state = agent.status_read(root, "a1")
            self.assertEqual(state, "step 2 running")

    def test_read_missing_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            ts, state = agent.status_read(root, "never-set")
            self.assertEqual((ts, state), ("", ""))


class ListAndAggregateTests(unittest.TestCase):
    def test_list_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            self.assertEqual(agent.list_agents(root), [])

    def test_list_sorted_by_activity(self) -> None:
        import time as _t
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.diary_append(root, "old-agent", "long ago")
            _t.sleep(1.05)  # ensure mtime differs (some FS have 1s resolution)
            agent.diary_append(root, "new-agent", "just now")
            records = agent.list_agents(root)
            self.assertEqual([r.id for r in records], ["new-agent", "old-agent"])

    def test_list_skips_invalid_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.init_agent(root, "valid-1")
            (root / ".agent-harness" / "agents" / "INVALID").mkdir()  # violates regex
            records = agent.list_agents(root)
            self.assertEqual([r.id for r in records], ["valid-1"])

    def test_aggregate_all_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.diary_append(root, "a1", "alpha work")
            agent.diary_append(root, "a2", "beta work")
            agent.status_set(root, "a2", "almost done")
            out = agent.aggregate(root)
            self.assertIn("a1", out)
            self.assertIn("a2", out)
            self.assertIn("alpha work", out)
            self.assertIn("beta work", out)
            self.assertIn("almost done", out)

    def test_aggregate_subset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.diary_append(root, "a1", "alpha")
            agent.diary_append(root, "a2", "beta")
            out = agent.aggregate(root, ["a1"])
            self.assertIn("alpha", out)
            self.assertNotIn("beta", out)

    def test_aggregate_empty_returns_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            out = agent.aggregate(root)
            self.assertIn("没有活跃", out)


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_diary_append_no_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            n_threads, per_thread = 10, 20
            errors: list[str] = []

            def worker(tid: int) -> None:
                try:
                    for i in range(per_thread):
                        agent.diary_append(root, "shared", f"t{tid}-i{i}")
                except Exception as e:  # pragma: no cover
                    errors.append(str(e))

            threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertEqual(errors, [])
            diary = (root / ".agent-harness" / "agents" / "shared" / "diary.md").read_text(encoding="utf-8")
            count = sum(1 for ln in diary.splitlines() if ln.startswith("- "))
            self.assertEqual(count, n_threads * per_thread)


class CLITests(unittest.TestCase):
    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
        return subprocess.run(
            [sys.executable, "-m", "agent_harness", "agent", *args],
            cwd=str(root), capture_output=True, text=True, env=env,
        )

    def test_init_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            r = self._run(root, "init", "agent-1")
            self.assertEqual(r.returncode, 0, r.stderr)
            r2 = self._run(root, "list")
            self.assertIn("agent-1", r2.stdout)

    def test_diary_and_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            self._run(root, "diary", "a1", "first")
            self._run(root, "status", "a1", "working")
            r = self._run(root, "aggregate")
            self.assertIn("first", r.stdout)
            self.assertIn("working", r.stdout)

    def test_invalid_id_rejected_with_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            r = self._run(root, "init", "BAD!")
            self.assertEqual(r.returncode, 2)
            self.assertIn("不合法", r.stdout)


class UpgradeSkipTests(unittest.TestCase):
    def test_agents_glob_is_skip(self) -> None:
        from agent_harness.upgrade import get_category
        self.assertEqual(get_category(".agent-harness/agents/foo/diary.md"), "skip")
        self.assertEqual(get_category(".agent-harness/agents/bar/status.md"), "skip")


class SquadBoundaryDocumentation(unittest.TestCase):
    """Sanity: the agent/ tree must NOT intersect squad/ tree paths."""

    def test_agents_and_squad_are_separate_subdirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            agent.init_agent(root, "a1")
            self.assertTrue((root / ".agent-harness" / "agents").is_dir())
            # squad uses its own subdir structure, not agents/
            self.assertFalse((root / ".agent-harness" / "agents" / "squad").exists())


if __name__ == "__main__":
    unittest.main()
