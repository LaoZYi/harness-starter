"""Tests for the audit log (WAL) — Issue #12, absorbed from MemPalace."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_harness import audit


def _mk_root(tmp: Path) -> Path:
    root = tmp / "proj"
    (root / ".agent-harness").mkdir(parents=True)
    return root


class AppendAuditTests(unittest.TestCase):
    """Normal path + validation."""

    def test_append_creates_file_and_one_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            entry = audit.append_audit(root, "lessons.md", "append", "new test lesson")
            self.assertEqual(entry.file, "lessons.md")
            self.assertEqual(entry.op, "append")
            path = audit.audit_path(root)
            self.assertTrue(path.is_file())
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["file"], "lessons.md")
            self.assertEqual(data["op"], "append")
            self.assertIn("ts", data)
            self.assertIn("summary", data)

    def test_agent_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            old = os.environ.get("HARNESS_AGENT")
            os.environ["HARNESS_AGENT"] = "claude-opus-test"
            try:
                entry = audit.append_audit(root, "current-task.md", "update", "step 1 done")
                self.assertEqual(entry.agent, "claude-opus-test")
            finally:
                if old is None:
                    del os.environ["HARNESS_AGENT"]
                else:
                    os.environ["HARNESS_AGENT"] = old

    def test_agent_override_wins_over_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            os.environ["HARNESS_AGENT"] = "env-agent"
            try:
                entry = audit.append_audit(
                    root, "lessons.md", "append", "x", agent="explicit"
                )
                self.assertEqual(entry.agent, "explicit")
            finally:
                del os.environ["HARNESS_AGENT"]

    def test_agent_default_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            os.environ.pop("HARNESS_AGENT", None)
            entry = audit.append_audit(root, "lessons.md", "append", "x")
            self.assertEqual(entry.agent, "unknown")

    def test_reject_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            with self.assertRaises(ValueError):
                audit.append_audit(root, "random.md", "append", "no")

    def test_reject_invalid_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            with self.assertRaises(ValueError):
                audit.append_audit(root, "lessons.md", "merge", "no")

    def test_append_preserves_utf8_summary(self) -> None:
        """Chinese + emoji must round-trip (no \\u escaping)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "新增 🔒 文件锁教训")
            raw = audit.audit_path(root).read_text(encoding="utf-8")
            self.assertIn("新增 🔒 文件锁教训", raw)


class TailTests(unittest.TestCase):
    def test_empty_log_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            self.assertEqual(audit.tail(root), [])

    def test_returns_newest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            for i in range(5):
                audit.append_audit(
                    root, "lessons.md", "append", f"entry-{i}",
                    ts=f"2026-04-13T10:00:0{i}Z",
                )
            entries = audit.tail(root, limit=3)
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].summary, "entry-4")
            self.assertEqual(entries[-1].summary, "entry-2")

    def test_limit_zero_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "x")
            self.assertEqual(audit.tail(root, limit=0), [])


class StatsTests(unittest.TestCase):
    def test_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            s = audit.stats(root)
            self.assertEqual(s["total"], 0)
            self.assertEqual(s["by_file"], {})

    def test_aggregates_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "a", agent="alice")
            audit.append_audit(root, "lessons.md", "append", "b", agent="alice")
            audit.append_audit(root, "task-log.md", "append", "c", agent="bob")
            s = audit.stats(root)
            self.assertEqual(s["total"], 3)
            self.assertEqual(s["by_file"], {"lessons.md": 2, "task-log.md": 1})
            self.assertEqual(s["by_agent"], {"alice": 2, "bob": 1})
            self.assertEqual(s["by_op"], {"append": 3})


class TruncateTests(unittest.TestCase):
    def test_truncate_before_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "old", ts="2026-01-01T00:00:00Z")
            audit.append_audit(root, "lessons.md", "append", "mid", ts="2026-03-01T00:00:00Z")
            audit.append_audit(root, "lessons.md", "append", "new", ts="2026-04-13T00:00:00Z")
            removed = audit.truncate_before(root, "2026-02-01T00:00:00Z")
            self.assertEqual(removed, 1)
            remaining = audit.read_all(root)
            self.assertEqual(len(remaining), 2)
            self.assertEqual(remaining[0].summary, "mid")

    def test_truncate_missing_file_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            self.assertEqual(audit.truncate_before(root, "2030-01-01T00:00:00Z"), 0)


class ConcurrencyTests(unittest.TestCase):
    """Verify fcntl lock prevents interleaving under concurrent writers."""

    def test_concurrent_appends_no_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            n_threads = 10
            per_thread = 20
            errors: list[str] = []

            def worker(tid: int) -> None:
                try:
                    for i in range(per_thread):
                        audit.append_audit(
                            root, "lessons.md", "append",
                            f"t{tid}-i{i}", agent=f"t{tid}",
                        )
                except Exception as e:  # pragma: no cover
                    errors.append(str(e))

            threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [])
            entries = audit.read_all(root)
            self.assertEqual(len(entries), n_threads * per_thread)
            # Every unique (tid, i) pair must be present.
            seen = {e.summary for e in entries}
            expected = {f"t{t}-i{i}" for t in range(n_threads) for i in range(per_thread)}
            self.assertEqual(seen, expected)


class MalformedLineTolerance(unittest.TestCase):
    def test_read_all_skips_broken_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "ok-1")
            # Inject garbage directly
            with audit.audit_path(root).open("a", encoding="utf-8") as f:
                f.write("not-json-at-all\n")
                f.write("\n")  # empty line
            audit.append_audit(root, "lessons.md", "append", "ok-2")
            entries = audit.read_all(root)
            self.assertEqual([e.summary for e in entries], ["ok-1", "ok-2"])


class CLITests(unittest.TestCase):
    """End-to-end via `python -m agent_harness audit ...`."""

    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
        return subprocess.run(
            [sys.executable, "-m", "agent_harness", "audit", *args],
            cwd=str(root), capture_output=True, text=True, env=env,
        )

    def test_append_and_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            r = self._run(
                root, "append",
                "--file", "lessons.md", "--op", "append", "--summary", "cli test"
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("已追加", r.stdout)

            r2 = self._run(root, "tail", "--limit", "5")
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("cli test", r2.stdout)

    def test_stats_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            self._run(root, "append", "--file", "lessons.md", "--op", "append", "--summary", "x")
            r = self._run(root, "stats", "--json")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["total"], 1)

    def test_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _mk_root(Path(tmp))
            audit.append_audit(root, "lessons.md", "append", "old", ts="2024-01-01T00:00:00Z")
            audit.append_audit(root, "lessons.md", "append", "new", ts="2026-04-13T00:00:00Z")
            r = self._run(root, "truncate", "--before", "2025-01-01")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("已移除 1 条", r.stdout)


class UpgradeSkipTests(unittest.TestCase):
    """audit.jsonl must be classified as `skip` so upgrades preserve user data."""

    def test_audit_jsonl_is_skip(self) -> None:
        from agent_harness.upgrade import get_category
        self.assertEqual(get_category(".agent-harness/audit.jsonl"), "skip")


if __name__ == "__main__":
    unittest.main()
