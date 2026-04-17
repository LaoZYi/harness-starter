"""Issue #21 — SQLite mailbox + coordinator watch 测试。

覆盖：
- mailbox 读写（WAL 模式、多 connection、line-by-line 幂等）
- state.py 签名兼容（append_status / done_workers / pending_worker_info 走 mailbox）
- cmd_watch 循环（限定 max_iterations 避免无限轮询；mock list_windows）
- cmd_watch SIGTERM 优雅退出
- cmd_dump 导出 JSONL
- watch 全部 done 后自动退出
"""
from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from agent_harness.squad import cli as squad_cli
from agent_harness.squad import mailbox as mb
from agent_harness.squad.coordinator import cmd_dump, cmd_watch
from agent_harness.squad.state import (
    append_status, done_workers, pending_worker_info, read_all_status,
)


import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent))
from _git_helper import init_git_repo as _init_git  # noqa: E402


def _make_linear_spec(tmp: Path) -> Path:
    spec = tmp / "spec.json"
    spec.write_text(json.dumps({
        "task_id": "mtest", "base_branch": "master",
        "workers": [
            {"name": "scout", "capability": "scout", "prompt": "x"},
            {"name": "builder", "capability": "builder",
             "depends_on": ["scout"], "prompt": "y"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return spec


def _create_args(spec: Path, project: Path) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.spec, ns.project, ns.dry_run = str(spec), str(project), True
    return ns


class MailboxCoreTests(unittest.TestCase):
    """mailbox.py 基础行为。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sd = self.tmp / "squad" / "t1"

    def test_wal_mode_active(self):
        """append_event 会自动初始化 WAL 模式。"""
        mb.append_event(self.sd, "info", message="hello")
        # 验证 WAL 副文件存在（至少启动过一次）
        import sqlite3
        conn = sqlite3.connect(str(mb.db_path(self.sd)))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        self.assertEqual(mode, "wal")

    def test_empty_before_any_event(self):
        self.assertEqual(mb.read_events(self.sd), [])
        self.assertEqual(mb.done_workers(self.sd), set())
        self.assertEqual(mb.pending_worker_info(self.sd), {})

    def test_append_and_read_order(self):
        for i in range(5):
            mb.append_event(self.sd, "info", worker=f"w{i}", message=str(i))
        events = mb.read_events(self.sd)
        self.assertEqual([e["message"] for e in events], ["0", "1", "2", "3", "4"])

    def test_filter_by_event_type(self):
        mb.append_event(self.sd, "done", worker="scout")
        mb.append_event(self.sd, "pending", worker="builder")
        mb.append_event(self.sd, "done", worker="builder")
        done_events = mb.read_events(self.sd, event_type="done")
        self.assertEqual(len(done_events), 2)
        self.assertEqual({e["worker"] for e in done_events}, {"scout", "builder"})

    def test_filter_by_worker(self):
        mb.append_event(self.sd, "pending", worker="builder", message="x")
        mb.append_event(self.sd, "spawned", worker="builder", message="y")
        mb.append_event(self.sd, "done", worker="scout", message="z")
        builder_events = mb.read_events(self.sd, worker="builder")
        self.assertEqual(len(builder_events), 2)

    def test_done_workers_set(self):
        mb.append_event(self.sd, "done", worker="a")
        mb.append_event(self.sd, "done", worker="b")
        mb.append_event(self.sd, "pending", worker="c")
        self.assertEqual(mb.done_workers(self.sd), {"a", "b"})

    def test_pending_cleared_by_spawn(self):
        mb.append_event(self.sd, "pending", worker="builder", message="x")
        self.assertIn("builder", mb.pending_worker_info(self.sd))
        mb.append_event(self.sd, "spawned", worker="builder", message="y")
        self.assertNotIn("builder", mb.pending_worker_info(self.sd))

    def test_payload_roundtrip(self):
        """非标准字段走 payload 字典。"""
        mb.append_event(self.sd, "info", message="m", payload={"k": "v", "n": 42})
        events = mb.read_events(self.sd)
        self.assertEqual(events[0]["payload"], {"k": "v", "n": 42})

    def test_dump_to_jsonl_is_parseable(self):
        mb.append_event(self.sd, "done", worker="a")
        mb.append_event(self.sd, "info", message="hi")
        lines = list(mb.dump_to_jsonl(self.sd))
        self.assertEqual(len(lines), 2)
        for line in lines:
            json.loads(line)  # 不抛即合法

    def test_reject_empty_event_type(self):
        with self.assertRaises(mb.MailboxError):
            mb.append_event(self.sd, "")


class StateBackwardCompatTests(unittest.TestCase):
    """state.py 的旧签名仍能工作（19a 调用方无感）。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _init_git(self.tmp)
        squad_cli.cmd_create(_create_args(_make_linear_spec(self.tmp), self.tmp))

    def test_append_status_writes_to_mailbox(self):
        append_status(self.tmp, "mtest",
                      {"worker": "scout", "event": "done", "message": "ok"})
        self.assertIn("scout", done_workers(self.tmp, "mtest"))

    def test_pending_worker_info_roundtrip(self):
        append_status(self.tmp, "mtest",
                      {"worker": "builder", "event": "pending", "message": "x"})
        info = pending_worker_info(self.tmp, "mtest")
        self.assertIn("builder", info)

    def test_read_all_status_returns_events(self):
        """cmd_create 本身已写入若干事件，read_all_status 应非空。"""
        events = read_all_status(self.tmp, "mtest")
        self.assertGreater(len(events), 0)


class WatchCommandTests(unittest.TestCase):
    """cmd_watch 常驻进程的关键行为（用 max_iterations 控制循环次数）。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _init_git(self.tmp)
        squad_cli.cmd_create(_create_args(_make_linear_spec(self.tmp), self.tmp))

    def _make_watch_args(self, interval=1, max_iter=2):
        ns = argparse.Namespace()
        ns.project = str(self.tmp)
        ns.task_id = None
        ns.interval = interval
        ns._max_iterations = max_iter
        return ns

    def test_watch_exits_when_all_done(self):
        """所有 worker 都 done → 自动退出，返回 0。"""
        append_status(self.tmp, "mtest", {"worker": "scout", "event": "done"})
        append_status(self.tmp, "mtest", {"worker": "builder", "event": "done"})
        buf = io.StringIO()
        with patch("agent_harness.squad.coordinator.list_windows", return_value=[]):
            with redirect_stdout(buf):
                rc = cmd_watch(self._make_watch_args(interval=1, max_iter=5))
        self.assertEqual(rc, 0)
        self.assertIn("所有 worker 已 done", buf.getvalue())

    def test_watch_respects_max_iterations(self):
        """当没有全部 done 时，max_iterations 终结循环。"""
        with patch("agent_harness.squad.coordinator.list_windows", return_value=["scout"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_watch(self._make_watch_args(interval=1, max_iter=2))
        self.assertEqual(rc, 0)
        self.assertIn("开始监视", buf.getvalue())

    def test_watch_auto_advances_on_done(self):
        """watch 在循环中发现 done 应自动 advance（这里 mock advance）。"""
        append_status(self.tmp, "mtest", {"worker": "scout", "event": "done"})
        called = []
        def fake_run_check(cmd, label):
            called.append(label)
        with patch("agent_harness.squad.coordinator.run_check", side_effect=fake_run_check), \
             patch("agent_harness.squad.coordinator.list_windows", return_value=["scout"]):
            cmd_watch(self._make_watch_args(interval=1, max_iter=2))
        # 应该至少尝试启动 builder 一次
        self.assertTrue(any("builder" in c for c in called),
                        f"watch 没有触发 builder 启动；调用记录：{called}")


class DumpCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        _init_git(self.tmp)
        squad_cli.cmd_create(_create_args(_make_linear_spec(self.tmp), self.tmp))

    def _dump_args(self):
        ns = argparse.Namespace()
        ns.project = str(self.tmp)
        ns.task_id = None
        return ns

    def test_dump_produces_jsonl(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cmd_dump(self._dump_args())
        self.assertEqual(rc, 0)
        self.assertIn("事件", err.getvalue())
        lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
        self.assertGreater(len(lines), 0)
        for line in lines:
            json.loads(line)  # 每行都是合法 JSON


class GitignoreTemplateTests(unittest.TestCase):
    """模板是否包含 WAL 副文件的 .gitignore 规则。"""

    def test_gitignore_template_has_wal_rules(self):
        tmpl = (Path(__file__).resolve().parents[1] / "src" / "agent_harness"
                / "templates" / "common" / ".agent-harness" / ".gitignore.tmpl")
        self.assertTrue(tmpl.is_file(), f"missing {tmpl}")
        text = tmpl.read_text(encoding="utf-8")
        self.assertIn("mailbox.db-wal", text)
        self.assertIn("mailbox.db-shm", text)


if __name__ == "__main__":
    unittest.main()
