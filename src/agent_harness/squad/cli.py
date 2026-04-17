"""CLI commands for squad: create / status / attach / stop."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .coordinator import cmd_advance, cmd_done, cmd_dump, cmd_watch, derive_worker_state
from .spec import parse_spec
from .state import (
    Manifest,
    WorkerRecord,
    append_status,
    list_active_squads,
    read_manifest,
    squad_dir,
    write_manifest,
)
from .tmux import (
    build_new_session_cmd,
    build_new_window_cmd,
    ensure_tmux_available,
)
from .worker_files import (
    provision_worker_worktree,
    run_check,
    write_worker_files,
)


def cmd_create(args) -> int:
    spec_path = Path(args.spec).resolve()
    root = Path(args.project or ".").resolve()
    dry_run = bool(getattr(args, "dry_run", False))

    if not dry_run:
        try:
            ensure_tmux_available()
        except Exception as exc:
            print(f"[squad] 环境检查失败：{exc}")
            return 2

    try:
        spec = parse_spec(spec_path)
    except Exception as exc:
        print(f"[squad] spec 解析失败：{exc}")
        return 2

    session_name = f"squad-{spec.task_id}"
    sdir = squad_dir(root, spec.task_id)
    sdir.mkdir(parents=True, exist_ok=True)

    # 1. start tmux session (detached) — skipped in dry-run
    if not dry_run:
        run_check(build_new_session_cmd(session_name), f"启动 tmux session {session_name}")

    # 2. provision each worker — on failure, tear down session + worktrees.
    #
    # Wave-0 启动策略（Issue #19 阶段 2 依赖触发）：
    # - 渲染所有 worker 的产物（worktree + settings + prompt）
    # - 只对**无 depends_on 的 worker** 真正创建 tmux 窗口（wave 0）
    # - 有依赖的 worker 写 pending 事件；等 `harness squad advance` 在依赖 done 后触发启动
    # - Dry-run 不区分 wave，全部只渲染不开窗口
    worker_records: list[WorkerRecord] = []
    try:
        for w in spec.workers:
            wt_path = provision_worker_worktree(root, spec, w, dry_run=dry_run)
            write_worker_files(root, spec, w, wt_path)
            is_wave0 = not w.depends_on
            if not dry_run and is_wave0:
                run_check(
                    build_new_window_cmd(
                        session=session_name,
                        window=w.name,
                        cwd=str(wt_path),
                        system_prompt_file=str(wt_path / ".claude" / "squad-context.md"),
                        task_prompt_file=str(wt_path / "task-prompt.md"),
                    ),
                    f"启动 worker 窗口 {w.name}",
                )
            worker_records.append(
                WorkerRecord(
                    name=w.name,
                    capability=w.capability,
                    worktree=str(wt_path),
                    depends_on=list(w.depends_on),
                )
            )
            if dry_run:
                event = "dry-run-rendered"
            elif is_wave0:
                event = "spawned"
            else:
                event = "pending"
            msg = f"worktree={wt_path}"
            if not is_wave0 and not dry_run:
                msg += f"; blocked_by={','.join(w.depends_on)}"
            append_status(
                root, spec.task_id,
                {"worker": w.name, "event": event, "message": msg},
            )
    except RuntimeError as exc:
        print(f"[squad] 创建失败，清理中：{exc}")
        if not dry_run:
            subprocess.run(["tmux", "kill-session", "-t", session_name], check=False)
            for wr in worker_records:
                subprocess.run(
                    ["git", "-C", str(root), "worktree", "remove", "--force", wr.worktree],
                    check=False,
                )
        return 2

    # 3. write manifest
    manifest = Manifest(
        task_id=spec.task_id,
        base_branch=spec.base_branch,
        tmux_session=session_name,
        created_at=time.time(),
        workers=worker_records,
    )
    write_manifest(root, manifest)

    wave0 = [w for w in worker_records if not w.depends_on]
    pending = [w for w in worker_records if w.depends_on]

    if dry_run:
        print(f"[squad] dry-run 完成：{len(worker_records)} 个 worker 的产物已渲染（未启动 tmux/worker）")
        print(f"[squad] 检查：ls {sdir} / cat {worker_records[0].worktree}/.claude/settings.local.json")
    else:
        print(f"[squad] 已创建 squad '{spec.task_id}'，{len(worker_records)} 个 worker")
        print(f"[squad] wave 0 已启动 ({len(wave0)})：{', '.join(w.name for w in wave0) or '（无 — 所有 worker 都有依赖？检查 spec）'}")
        if pending:
            print(f"[squad] pending ({len(pending)})：{', '.join(w.name + '←[' + ','.join(w.depends_on) + ']' for w in pending)}")
            print("[squad] 依赖完成后运行：harness squad done <worker>  然后  harness squad advance")
        print(f"[squad] 观察：tmux attach -t {session_name}")
        print("[squad] 状态：harness squad status")
    return 0


def cmd_status(args) -> int:
    root = Path(args.project or ".").resolve()
    active = list_active_squads(root)
    if not active:
        print("[squad] 当前没有活跃的 squad。")
        return 0

    now = time.time()
    for task_id in active:
        m = read_manifest(root, task_id)
        if m is None:
            continue
        print(f"\nSquad: {m.task_id} (tmux session: {m.tmux_session})")
        print(f"  base_branch: {m.base_branch}")
        print("  workers:")
        for w in m.workers:
            state = derive_worker_state(
                root, task_id, m.tmux_session, w.name, w.depends_on, now,
            )
            print(f"    - {w.name} [{w.capability}] {state} → {w.worktree}")
    return 0


def cmd_attach(args) -> int:
    root = Path(args.project or ".").resolve()
    target = args.worker
    active = list_active_squads(root)
    if not active:
        print("[squad] 没有活跃的 squad。")
        return 1

    for task_id in active:
        m = read_manifest(root, task_id)
        if m is None:
            continue
        if any(w.name == target for w in m.workers):
            print(
                f"请在另一个终端执行："
                f"tmux attach -t {m.tmux_session} \\; select-window -t {target}"
            )
            return 0

    print(f"[squad] 未找到 worker：{target}")
    return 1


def cmd_stop(args) -> int:
    root = Path(args.project or ".").resolve()
    target = args.target
    active = list_active_squads(root)
    if not active:
        print("[squad] 没有活跃的 squad。")
        return 0

    stopped = 0
    for task_id in active:
        m = read_manifest(root, task_id)
        if m is None:
            continue
        if target in ("all", task_id):
            subprocess.run(["tmux", "kill-session", "-t", m.tmux_session], check=False)
            append_status(root, task_id, {"event": "squad_stopped", "message": target})
            stopped += 1
        else:
            for w in m.workers:
                if w.name == target:
                    subprocess.run(
                        ["tmux", "kill-window", "-t", f"{m.tmux_session}:{w.name}"],
                        check=False,
                    )
                    append_status(
                        root, task_id,
                        {"worker": w.name, "event": "worker_stopped", "message": ""},
                    )
                    stopped += 1

    print(f"[squad] 已停止 {stopped} 项（target={target}）。worktree 保留，请用 /finish-branch 处理合并。")
    return 0 if stopped else 1


def _add_squad_subcommands(sq_subs) -> None:
    """Shared subcommand builder — used by `harness squad` and standalone `bin/squad`."""
    c = sq_subs.add_parser("create", help="按 JSON spec 创建 squad 并启动 workers")
    c.add_argument("spec", help="JSON spec 文件路径（Issue #25 起从 yaml 迁 json）")
    c.add_argument("--project", help="项目根目录（默认当前目录）")
    c.add_argument(
        "--dry-run",
        action="store_true",
        help="只渲染产物（settings/prompt/manifest），不启动 tmux 或建 worktree。用于测试和端到端验证",
    )
    c.set_defaults(func=cmd_create)

    s = sq_subs.add_parser("status", help="列出活跃 squad 和 workers")
    s.add_argument("--project", help="项目根目录（默认当前目录）")
    s.set_defaults(func=cmd_status)

    a = sq_subs.add_parser("attach", help="查看某个 worker 的 tmux 窗口（提示命令）")
    a.add_argument("worker", help="worker 名")
    a.add_argument("--project", help="项目根目录（默认当前目录）")
    a.set_defaults(func=cmd_attach)

    stp = sq_subs.add_parser("stop", help="停止指定 worker 或整个 squad（target=all 或 worker 名）")
    stp.add_argument("target", help="worker 名 / task_id / 'all'")
    stp.add_argument("--project", help="项目根目录（默认当前目录）")
    stp.set_defaults(func=cmd_stop)

    def _add_coord(name, help_, func, extra=None):
        p = sq_subs.add_parser(name, help=help_)
        p.add_argument("--task-id", help="squad task id（默认自动选择唯一活跃 squad）")
        p.add_argument("--project", help="项目根目录（默认当前目录）")
        if extra:
            extra(p)
        p.set_defaults(func=func)
        return p

    _add_coord("advance", "推动 squad：启动依赖已满足的 pending worker", cmd_advance,
               lambda p: p.add_argument("--dry-run", action="store_true", help="只打印将启动哪些 worker"))
    dn = _add_coord("done", "标记某 worker 完成（写 done 事件）", cmd_done,
                    lambda p: p.add_argument("-m", "--message", help="done 事件附带消息"))
    dn.add_argument("worker", help="worker 名")
    _add_coord("watch", "常驻进程：轮询 mailbox 自动 advance（Issue #21）", cmd_watch,
               lambda p: p.add_argument("--interval", type=int, default=3, help="轮询间隔秒数（默认 3s）"))
    _add_coord("dump", "导出 mailbox 为 JSONL（调试用）", cmd_dump)


def register_subcommand(subs) -> None:
    sq = subs.add_parser("squad", help="多 agent 常驻协作（tmux + worktree）")
    _add_squad_subcommands(sq.add_subparsers(dest="squad_command", required=True))


def main(argv=None) -> int:
    """Standalone entry for `.agent-harness/bin/squad` (Issue #25)."""
    import argparse
    p = argparse.ArgumentParser(prog="squad", description="项目内嵌 squad 运行时")
    _add_squad_subcommands(p.add_subparsers(dest="squad_command", required=True))
    args = p.parse_args(argv)
    return args.func(args) or 0
