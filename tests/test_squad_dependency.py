"""Issue #19 阶段 2 — 依赖触发 + 拓扑序启动测试（19a 子范围）。

核心不变量：
- cmd_create 的 dry-run 渲染全部 worker 产物但不开 tmux 窗口，且对有 depends_on 的
  worker 写 "dry-run-rendered" 事件
- 非 dry-run 会把 wave 0 写 "spawned"，其他写 "pending"（本测试用 dry-run 绕开 tmux）
- done_workers / pending_worker_info 纯文件计算，可在 dry-run 数据上验证
- advance 的 dry-run 在不接触 tmux 的情况下能正确算出"下一步该启动谁"

测试不接触真实 tmux：所有 advance 都走 --dry-run 路径，通过 append_status 注入 done 事件。
"""
from __future__ import annotations

import argparse
import io
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_harness.squad import cli as squad_cli
from agent_harness.squad.coordinator import (
    cmd_advance, cmd_done, derive_worker_state, find_squad,
)
from agent_harness.squad.state import (
    append_status, done_workers, pending_worker_info,
    read_all_status, read_manifest,
)


def _make_create_args(spec_path: Path, project: Path) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.spec = str(spec_path)
    ns.project = str(project)
    ns.dry_run = True
    return ns


def _make_coord_args(
    project: Path, task_id: str | None = None, dry_run: bool = True,
    worker: str | None = None, message: str | None = None,
) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.project = str(project)
    ns.task_id = task_id
    ns.dry_run = dry_run
    if worker is not None:
        ns.worker = worker
    ns.message = message
    return ns


def _write_linear_spec(tmp: Path) -> Path:
    """scout → builder → reviewer linear chain."""
    import json
    spec = tmp / "spec.json"
    spec.write_text(json.dumps({
        "task_id": "linear", "base_branch": "master",
        "workers": [
            {"name": "scout", "capability": "scout", "prompt": "探索"},
            {"name": "builder", "capability": "builder",
             "depends_on": ["scout"], "prompt": "实现"},
            {"name": "reviewer", "capability": "reviewer",
             "depends_on": ["builder"], "prompt": "评审"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return spec


def _write_diamond_spec(tmp: Path) -> Path:
    """scout → {builder, linter} → reviewer (diamond)."""
    import json
    spec = tmp / "spec.json"
    spec.write_text(json.dumps({
        "task_id": "diamond", "base_branch": "master",
        "workers": [
            {"name": "scout", "capability": "scout", "prompt": "探索"},
            {"name": "builder", "capability": "builder",
             "depends_on": ["scout"], "prompt": "实现"},
            {"name": "linter", "capability": "builder",
             "depends_on": ["scout"], "prompt": "代码检查"},
            {"name": "reviewer", "capability": "reviewer",
             "depends_on": ["builder", "linter"], "prompt": "评审"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return spec


class _BaseDependencyTest(unittest.TestCase):
    """Common setup：init git repo，生成 spec，跑 cmd_create dry-run。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        # 初始化 git 仓库（worktree provision 需要）
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"],
                       cwd=self.tmp, check=True)
        subprocess.run(["git", "branch", "-M", "master"], cwd=self.tmp, check=True)

    def _create_linear(self) -> None:
        spec = _write_linear_spec(self.tmp)
        rc = squad_cli.cmd_create(_make_create_args(spec, self.tmp))
        self.assertEqual(rc, 0)

    def _create_diamond(self) -> None:
        spec = _write_diamond_spec(self.tmp)
        rc = squad_cli.cmd_create(_make_create_args(spec, self.tmp))
        self.assertEqual(rc, 0)


class CreateWavesTests(_BaseDependencyTest):
    """cmd_create 的 wave 0 识别在 dry-run 下也应正确分组事件。"""

    def test_linear_dry_run_records_all_workers(self):
        self._create_linear()
        m = read_manifest(self.tmp, "linear")
        self.assertIsNotNone(m)
        self.assertEqual([w.name for w in m.workers], ["scout", "builder", "reviewer"])

    def test_create_prints_wave0_and_pending_hints(self):
        """非 dry-run 路径下 cmd_create 会提示 wave 0 + pending；dry-run 路径也能渲染
        manifest。这里验证 manifest depends_on 保留。"""
        self._create_linear()
        m = read_manifest(self.tmp, "linear")
        self.assertEqual(m.workers[0].depends_on, [])
        self.assertEqual(m.workers[1].depends_on, ["scout"])
        self.assertEqual(m.workers[2].depends_on, ["builder"])


class DoneAndPendingInfoTests(_BaseDependencyTest):
    def test_done_workers_empty_when_no_events(self):
        self._create_linear()
        self.assertEqual(done_workers(self.tmp, "linear"), set())

    def test_cmd_done_writes_done_event(self):
        self._create_linear()
        rc = cmd_done(_make_coord_args(self.tmp, worker="scout"))
        self.assertEqual(rc, 0)
        self.assertEqual(done_workers(self.tmp, "linear"), {"scout"})

    def test_cmd_done_rejects_unknown_worker(self):
        self._create_linear()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_done(_make_coord_args(self.tmp, worker="ghost"))
        self.assertEqual(rc, 1)
        self.assertIn("worker 不存在", buf.getvalue())

    def test_pending_worker_info_tracks_blocked_workers(self):
        """注入 pending 事件后 pending_worker_info 应返回对应 worker 名 + 时间戳。"""
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "builder", "event": "pending", "message": "x"})
        info = pending_worker_info(self.tmp, "linear")
        self.assertIn("builder", info)
        self.assertGreater(info["builder"], 0)

    def test_pending_cleared_once_spawned(self):
        """spawned 事件应清除 pending 状态。"""
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "builder", "event": "pending", "message": "x"})
        append_status(self.tmp, "linear",
                      {"worker": "builder", "event": "spawned", "message": "y"})
        self.assertNotIn("builder", pending_worker_info(self.tmp, "linear"))


class AdvanceDryRunTests(_BaseDependencyTest):
    """advance --dry-run 不接触 tmux，只计算应启动 worker。"""

    def test_advance_with_no_done_keeps_downstream_pending(self):
        """wave 0 已 running，但没 done 事件 → 下游应仍 pending，advance 不启动任何 worker。"""
        self._create_linear()
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["scout"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cmd_advance(_make_coord_args(self.tmp, dry_run=True))
        self.assertEqual(rc, 0)
        self.assertIn("无可启动的 worker", buf.getvalue())

    def test_advance_starts_builder_after_scout_done(self):
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "scout", "event": "done", "message": ""})
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["scout"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_advance(_make_coord_args(self.tmp, dry_run=True))
        out = buf.getvalue()
        self.assertIn("将启动：builder", out)
        self.assertNotIn("将启动：reviewer", out)

    def test_diamond_reviewer_needs_both_builder_and_linter(self):
        self._create_diamond()
        # scout done → builder, linter 可启动（scout 已 running）
        append_status(self.tmp, "diamond",
                      {"worker": "scout", "event": "done", "message": ""})
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["scout"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_advance(_make_coord_args(self.tmp, dry_run=True))
        out = buf.getvalue()
        self.assertIn("将启动：builder", out)
        self.assertIn("将启动：linter", out)
        self.assertNotIn("将启动：reviewer", out)

        # builder, linter 都 running 了；只 builder done，reviewer 仍不能启动
        append_status(self.tmp, "diamond",
                      {"worker": "builder", "event": "done", "message": ""})
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["scout", "builder", "linter"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_advance(_make_coord_args(self.tmp, dry_run=True))
            self.assertNotIn("将启动：reviewer", buf.getvalue())

            # linter 也 done 后，reviewer 可启动
            append_status(self.tmp, "diamond",
                          {"worker": "linter", "event": "done", "message": ""})
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_advance(_make_coord_args(self.tmp, dry_run=True))
            self.assertIn("将启动：reviewer", buf.getvalue())

    def test_advance_idempotent_under_live_window(self):
        """若 tmux 已有对应窗口，advance 不应重复启动。"""
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "scout", "event": "done", "message": ""})
        # 模拟 tmux 返回 builder 已在 live windows 中
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["builder"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_advance(_make_coord_args(self.tmp, dry_run=True))
            self.assertNotIn("将启动：builder", buf.getvalue())


class FindSquadTests(_BaseDependencyTest):
    def test_auto_select_single_squad(self):
        self._create_linear()
        found = find_squad(self.tmp, None)
        self.assertIsNotNone(found)
        task_id, m = found
        self.assertEqual(task_id, "linear")

    def test_reports_when_no_squads(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            found = find_squad(self.tmp, None)
        self.assertIsNone(found)
        self.assertIn("没有活跃的 squad", buf.getvalue())


class WorkerStateDerivationTests(_BaseDependencyTest):
    """derive_worker_state 是 status 命令的核心推导逻辑，纯函数可直测。"""

    def test_done_worker_shows_done(self):
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "scout", "event": "done", "message": ""})
        now = time.time()
        with patch("agent_harness.squad.coordinator.list_windows", return_value=[]):
            state = derive_worker_state(
                self.tmp, "linear", "squad-linear", "scout", [], now,
            )
        self.assertIn("done", state)

    def test_running_worker_shows_running(self):
        self._create_linear()
        with patch("agent_harness.squad.coordinator.list_windows",
                   return_value=["scout"]):
            state = derive_worker_state(
                self.tmp, "linear", "squad-linear", "scout", [], time.time(),
            )
        self.assertIn("running", state)

    def test_pending_under_30min_shows_waiting(self):
        self._create_linear()
        append_status(self.tmp, "linear",
                      {"worker": "builder", "event": "pending", "message": "x"})
        with patch("agent_harness.squad.coordinator.list_windows", return_value=[]):
            state = derive_worker_state(
                self.tmp, "linear", "squad-linear", "builder", ["scout"], time.time(),
            )
        self.assertIn("pending", state)
        self.assertNotIn("blocked >30min", state)

    def test_pending_over_30min_triggers_stuck_warning(self):
        self._create_linear()
        # 注入一个 31 分钟前的 pending 事件：直接操作 mailbox db 的 ts 字段
        import sqlite3
        from agent_harness.squad.state import squad_dir
        from agent_harness.squad.mailbox import db_path
        sd = squad_dir(self.tmp, "linear")
        # 先 append 一条 pending，再改 ts 到 31 分钟前
        append_status(self.tmp, "linear",
                      {"worker": "builder", "event": "pending", "message": "x"})
        conn = sqlite3.connect(str(db_path(sd)))
        old_ts = time.time() - 31 * 60
        conn.execute(
            "UPDATE events SET ts = ? WHERE worker = 'builder' AND event_type = 'pending'",
            (old_ts,),
        )
        conn.commit()
        conn.close()

        with patch("agent_harness.squad.coordinator.list_windows", return_value=[]):
            state = derive_worker_state(
                self.tmp, "linear", "squad-linear", "builder", ["scout"], time.time(),
            )
        self.assertIn("blocked >30min", state)


if __name__ == "__main__":
    unittest.main()
