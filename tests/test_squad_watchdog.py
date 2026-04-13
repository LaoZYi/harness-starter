"""Issue #22 — Tier 0 Watchdog 测试。

覆盖三类失联场景 + sentinel 关闭 + 幂等去重 + cmd_watch 集成。
"""
from __future__ import annotations

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_harness.squad import mailbox as mb
from agent_harness.squad.state import (
    Manifest, WorkerRecord, append_status, squad_dir, write_manifest,
)
from agent_harness.squad.watchdog import (
    SENTINEL_NAME, detect_failures, is_skipped, run_watchdog_tick,
)


def _make_manifest(root: Path, task_id: str = "wd", workers=("a", "b")) -> Manifest:
    m = Manifest(
        task_id=task_id,
        base_branch="master",
        tmux_session=f"squad-{task_id}",
        created_at=time.time(),
        workers=[
            WorkerRecord(name=w, capability="builder",
                         worktree=f"/tmp/wt-{w}", depends_on=[])
            for w in workers
        ],
    )
    write_manifest(root, m)
    squad_dir(root, task_id).mkdir(parents=True, exist_ok=True)
    return m


def _spawn(root: Path, task_id: str, name: str) -> None:
    append_status(root, task_id, {"worker": name, "event": "spawned",
                                   "message": "test"})


def _done(root: Path, task_id: str, name: str) -> None:
    append_status(root, task_id, {"worker": name, "event": "done",
                                   "message": "test"})


class SentinelTests(unittest.TestCase):

    def test_is_skipped_false_by_default(self):
        with TemporaryDirectory() as td:
            self.assertFalse(is_skipped(Path(td)))

    def test_is_skipped_true_when_sentinel_present(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / ".agent-harness").mkdir()
            (root / ".agent-harness" / SENTINEL_NAME).touch()
            self.assertTrue(is_skipped(root))

    def test_run_tick_returns_empty_when_skipped(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root)
            _spawn(root, "wd", "a")
            (root / ".agent-harness" / SENTINEL_NAME).touch()

            # 即使 session 不存在，sentinel 启用时也不上报
            events = run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            self.assertEqual(events, [])
            # mailbox 也不应有 session_lost 事件
            self.assertEqual(
                mb.read_events(squad_dir(root, "wd"), event_type="session_lost"),
                [],
            )


class SessionLostTests(unittest.TestCase):

    def test_session_lost_when_session_missing_and_workers_spawned(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root)
            _spawn(root, "wd", "a")

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "session_lost")
            self.assertIsNone(events[0]["worker"])

    def test_no_session_lost_when_no_workers_spawned_yet(self):
        """squad 刚建出来还没启动任何 worker，不报 session_lost（可能只是初始化中）。"""
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root)

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            self.assertEqual(events, [])

    def test_session_lost_idempotent(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root)
            _spawn(root, "wd", "a")

            # 第一次 tick 写入 session_lost
            first = run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            self.assertEqual(len(first), 1)
            # 第二次 tick 不应重复写
            second = run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            self.assertEqual(second, [])
            # mailbox 中只有一条 session_lost
            rows = mb.read_events(squad_dir(root, "wd"), event_type="session_lost")
            self.assertEqual(len(rows), 1)


class WorkerCrashedTests(unittest.TestCase):

    def test_worker_crashed_when_window_disappeared(self):
        """spawn 了 a, b；session 还在但 list_windows=[b] → a crashed。"""
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["b"],
            )
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "worker_crashed")
            self.assertEqual(events[0]["worker"], "a")

    def test_done_worker_not_flagged_as_crashed(self):
        """已 done 的 worker 自然不在 windows 里——不该报 crashed。"""
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")
            _done(root, "wd", "a")

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["b"],
            )
            self.assertEqual(events, [])

    def test_unspawned_worker_not_flagged(self):
        """没启动过的 worker（pending）也不在 windows 里，但不该报 crashed。"""
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            # b 从未 spawn

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["a"],
            )
            self.assertEqual(events, [])

    def test_worker_crashed_idempotent(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")

            first = run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["b"],
            )
            self.assertEqual(len(first), 1)
            second = run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["b"],
            )
            self.assertEqual(second, [])
            rows = mb.read_events(squad_dir(root, "wd"), event_type="worker_crashed")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["worker"], "a")

    def test_multiple_workers_crashed_in_one_tick(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b", "c"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")
            _spawn(root, "wd", "c")

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["c"],
            )
            crashed = sorted(e["worker"] for e in events)
            self.assertEqual(crashed, ["a", "b"])

    def test_session_lost_takes_precedence_over_worker_crashed(self):
        """session 都丢了不再单独报 worker_crashed（避免噪音）。"""
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")

            events = detect_failures(
                root, "wd", m,
                session_exists_fn=lambda s: False,
                list_windows_fn=lambda s: [],
            )
            kinds = [e["event"] for e in events]
            self.assertEqual(kinds, ["session_lost"])


class MailboxIntegrationTests(unittest.TestCase):

    def test_known_types_includes_watchdog_events(self):
        """新事件类型必须在 KNOWN_TYPES 注册，避免漂移。"""
        self.assertIn("session_lost", mb.KNOWN_TYPES)
        self.assertIn("worker_crashed", mb.KNOWN_TYPES)

    def test_events_persisted_to_mailbox(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            m = _make_manifest(root, workers=("a", "b"))
            _spawn(root, "wd", "a")
            _spawn(root, "wd", "b")

            run_watchdog_tick(
                root, "wd", m,
                session_exists_fn=lambda s: True,
                list_windows_fn=lambda s: ["b"],
            )
            crashed = mb.read_events(squad_dir(root, "wd"),
                                     event_type="worker_crashed")
            self.assertEqual(len(crashed), 1)
            self.assertEqual(crashed[0]["worker"], "a")
            self.assertIn("disappeared", crashed[0]["message"])


if __name__ == "__main__":
    unittest.main()
