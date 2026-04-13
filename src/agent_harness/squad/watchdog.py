"""Tier 0 Watchdog — Issue #22。

职责：
- 定时 ping tmux session：session 不存在且已 spawn 过 worker → 写 `session_lost` 事件
- 定时比对 worker 窗口：spawned 但未 done 且不在 live windows → 写 `worker_crashed` 事件
- 幂等：已上报的失联事件不重复写（从 mailbox 事件流推导，沿用"三源对账"原则）
- sentinel：`touch .agent-harness/.watchdog-skip` 关闭整个 watchdog（沿用 context-monitor 模式）

设计决策：
- **纯函数 + 依赖注入**：`session_exists_fn` / `list_windows_fn` 参数化便于测试，默认走 tmux 实模块
- **不持久化"已上报"状态**：从 mailbox 反查，少一份状态文件就少一份漂移
- **session_lost 优先于 worker_crashed**：session 都没了不再单独报 worker（避免噪音）
- **本期不实现 pid 检查、不实现自动重启**：worker 当前不写 pid；自动重启涉及 capability 切换和
  worktree 状态判断，复杂度过高，留给后续 Issue
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from . import mailbox as mb
from .state import Manifest, squad_dir

SENTINEL_NAME = ".watchdog-skip"


def is_skipped(project_root: Path) -> bool:
    """`touch .agent-harness/.watchdog-skip` 关闭整个 watchdog。"""
    return (project_root / ".agent-harness" / SENTINEL_NAME).is_file()


def _spawned_workers(sdir: Path) -> set[str]:
    """已 spawn 过的 worker 名集合（从 mailbox 反查）。"""
    return {
        e["worker"] for e in mb.read_events(sdir, event_type="spawned")
        if e.get("worker")
    }


def _done_set(sdir: Path) -> set[str]:
    return mb.done_workers(sdir)


def _crashed_workers(sdir: Path) -> set[str]:
    return {
        e["worker"] for e in mb.read_events(sdir, event_type="worker_crashed")
        if e.get("worker")
    }


def _session_lost_already_reported(sdir: Path) -> bool:
    return bool(mb.read_events(sdir, event_type="session_lost", limit=1))


def detect_failures(
    root: Path,
    task_id: str,
    manifest: Manifest,
    *,
    session_exists_fn: Callable[[str], bool] | None = None,
    list_windows_fn: Callable[[str], list[str]] | None = None,
) -> list[dict[str, Any]]:
    """检测新出现的失联事件（已上报的去重）。

    返回的事件未写入 mailbox——`run_watchdog_tick` 负责写入和打印。
    分离纯探测和副作用，便于测试和将来替换上报通道。
    """
    if session_exists_fn is None or list_windows_fn is None:
        from . import tmux as _tmux
        if session_exists_fn is None:
            session_exists_fn = _tmux.session_exists
        if list_windows_fn is None:
            list_windows_fn = _tmux.list_windows

    sdir = squad_dir(root, task_id)
    spawned = _spawned_workers(sdir)

    if not spawned:
        # squad 还没真正启动任何 worker（比如 dry-run 或 wave-0 全是 pending）
        # → 即使 session 不存在也不报，避免初始化期假阳性
        return []

    new_events: list[dict[str, Any]] = []

    if not session_exists_fn(manifest.tmux_session):
        if not _session_lost_already_reported(sdir):
            new_events.append({
                "event": "session_lost",
                "worker": None,
                "message": (
                    f"tmux session '{manifest.tmux_session}' not found; "
                    f"squad 整体失联，watch 将退出"
                ),
            })
        # session 不存在时不再单独判断 worker 级别（避免噪音）
        return new_events

    live = set(list_windows_fn(manifest.tmux_session))
    done = _done_set(sdir)
    already_crashed = _crashed_workers(sdir)

    for w in sorted(spawned):  # 排序保证多 worker crash 时事件顺序确定
        if w in live or w in done or w in already_crashed:
            continue
        new_events.append({
            "event": "worker_crashed",
            "worker": w,
            "message": (
                f"worker window '{w}' disappeared from session "
                f"'{manifest.tmux_session}'"
            ),
        })

    return new_events


def watch_tick_with_report(
    root: Path,
    task_id: str,
    manifest: Manifest,
    *,
    session_exists_fn: Callable[[str], bool] | None = None,
    list_windows_fn: Callable[[str], list[str]] | None = None,
    printer: Callable[[str], None] = print,
) -> bool:
    """供 cmd_watch 使用：跑一次 tick，打印新失联，返回是否因 session_lost 应退出。"""
    failures = run_watchdog_tick(
        root, task_id, manifest,
        session_exists_fn=session_exists_fn,
        list_windows_fn=list_windows_fn,
    )
    session_lost = False
    for ev in failures:
        if ev["event"] == "session_lost":
            printer(f"[squad watch] ⚠️  {ev['message']}")
            session_lost = True
        else:
            printer(
                f"[squad watch] ⚠️  worker 失联：{ev['worker']} — {ev['message']}"
            )
    return session_lost


def run_watchdog_tick(
    root: Path,
    task_id: str,
    manifest: Manifest,
    *,
    session_exists_fn: Callable[[str], bool] | None = None,
    list_windows_fn: Callable[[str], list[str]] | None = None,
) -> list[dict[str, Any]]:
    """执行一次 watchdog tick：sentinel 检查 → detect → 写 mailbox → 返回新事件。

    返回新写入的事件列表，供调用方（cmd_watch）打印用户提示。
    """
    if is_skipped(root):
        return []

    new_events = detect_failures(
        root, task_id, manifest,
        session_exists_fn=session_exists_fn,
        list_windows_fn=list_windows_fn,
    )
    sdir = squad_dir(root, task_id)
    for e in new_events:
        mb.append_event(
            sdir,
            event_type=e["event"],
            worker=e["worker"],
            message=e["message"],
        )
    return new_events
