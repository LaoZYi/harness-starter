"""Squad 依赖触发与状态推进（Issue #19 阶段 2 的 19a 子范围）。

核心职责：
- `cmd_advance`：扫 status.jsonl 的 done 事件 + tmux 已启动窗口，找出依赖已满足但未启动的 worker，启动它们（幂等）
- `cmd_done`：便捷写 done 事件，等价于 worker 自己追加到 status.jsonl

这个模块未来会扩展为 19c 的"持久 coordinator"——`harness squad watch` 常驻进程
消费 mailbox 事件自动 advance；现在 19a 是"命令驱动"版本（用户手动 advance）。
"""
from __future__ import annotations

from pathlib import Path

from .state import (
    Manifest,
    append_status,
    done_workers,
    list_active_squads,
    pending_worker_info,
    read_manifest,
)
from .tmux import build_new_window_cmd, list_windows
from .worker_files import run_check


STUCK_THRESHOLD_SECONDS = 30 * 60  # 阻塞 >30min 警告


def derive_worker_state(
    root: Path, task_id: str, tmux_session: str, worker_name: str,
    depends_on: list[str], now: float,
) -> str:
    """纯状态推导：done / running / pending / unknown。"""
    done = done_workers(root, task_id)
    live = set(list_windows(tmux_session))
    pending_ts = pending_worker_info(root, task_id)

    if worker_name in done:
        return "✅ done"
    if worker_name in live:
        return "🟢 running"
    if worker_name in pending_ts:
        age = int(now - pending_ts[worker_name])
        mins = age // 60
        if age > STUCK_THRESHOLD_SECONDS:
            return f"🔴 pending {mins}min (blocked >30min — 检查依赖：{','.join(depends_on)})"
        return f"⏳ pending {mins}min (blocked_by: {','.join(depends_on)})"
    return "⚪ unknown"


def find_squad(root: Path, task_id: str | None) -> tuple[str, Manifest] | None:
    """Locate a manifest by task_id, or the only active squad if task_id is None.

    Returns (task_id, manifest) or None（已打印错误）.
    """
    active = list_active_squads(root)
    if not active:
        print("[squad] 当前没有活跃的 squad。")
        return None
    if task_id is None:
        if len(active) > 1:
            print(f"[squad] 存在多个活跃 squad：{active}，请用 --task-id 指定")
            return None
        task_id = active[0]
    elif task_id not in active:
        print(f"[squad] 未找到 squad：{task_id}（活跃：{active}）")
        return None
    m = read_manifest(root, task_id)
    if m is None:
        return None
    return task_id, m


def cmd_advance(args) -> int:
    """推动 squad 前进：检查所有 pending worker 的依赖是否已 done，是则启动 tmux 窗口。

    幂等：若 worker 对应的 tmux 窗口已存在则跳过。
    """
    root = Path(args.project or ".").resolve()
    found = find_squad(root, getattr(args, "task_id", None))
    if found is None:
        return 1
    task_id, m = found

    done = done_workers(root, task_id)
    live_windows = set(list_windows(m.tmux_session))
    dry_run = bool(getattr(args, "dry_run", False))

    started: list[str] = []
    still_pending: list[str] = []
    for w in m.workers:
        if w.name in live_windows or w.name in done:
            continue  # 已启动或已完成
        if not set(w.depends_on).issubset(done):
            still_pending.append(w.name)
            continue

        # 依赖都 done，启动它
        if dry_run:
            print(f"[squad] (dry-run) 将启动：{w.name}")
            started.append(w.name)
            continue
        try:
            run_check(
                build_new_window_cmd(
                    session=m.tmux_session,
                    window=w.name,
                    cwd=w.worktree,
                    system_prompt_file=str(Path(w.worktree) / ".claude" / "squad-context.md"),
                    task_prompt_file=str(Path(w.worktree) / "task-prompt.md"),
                ),
                f"启动 worker 窗口 {w.name}",
            )
        except RuntimeError as exc:
            print(f"[squad] 启动 {w.name} 失败：{exc}")
            append_status(
                root, task_id,
                {"worker": w.name, "event": "spawn_failed", "message": str(exc)},
            )
            continue
        append_status(
            root, task_id,
            {"worker": w.name, "event": "spawned",
             "message": f"advance triggered; deps={','.join(w.depends_on)}"},
        )
        started.append(w.name)

    if started:
        print(f"[squad] 已启动 {len(started)} 个 worker：{', '.join(started)}")
    else:
        print("[squad] 无可启动的 worker（依赖未满足或全部已启动/完成）")
    if still_pending:
        print(f"[squad] 仍 pending：{', '.join(still_pending)}")
    return 0


def cmd_done(args) -> int:
    """便捷标记某 worker 完成（等价于 worker 自己写 done 事件）。"""
    root = Path(args.project or ".").resolve()
    found = find_squad(root, getattr(args, "task_id", None))
    if found is None:
        return 1
    task_id, m = found

    if not any(w.name == args.worker for w in m.workers):
        print(
            f"[squad] worker 不存在：{args.worker}"
            f"（spec 里的 worker: {[w.name for w in m.workers]}）"
        )
        return 1

    append_status(
        root, task_id,
        {"worker": args.worker, "event": "done",
         "message": args.message or "manual done via harness squad done"},
    )
    print(f"[squad] 已标记 {args.worker} 为 done。下一步：harness squad advance")
    return 0
