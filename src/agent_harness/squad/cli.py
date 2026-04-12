"""CLI commands for squad: create / status / attach / stop."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

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

    # 2. provision each worker — on failure, tear down session + worktrees
    worker_records: list[WorkerRecord] = []
    try:
        for w in spec.workers:
            wt_path = provision_worker_worktree(root, spec, w, dry_run=dry_run)
            write_worker_files(root, spec, w, wt_path)
            if not dry_run:
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
            append_status(
                root, spec.task_id,
                {"worker": w.name, "event": "spawned" if not dry_run else "dry-run-rendered",
                 "message": f"worktree={wt_path}"},
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

    if dry_run:
        print(f"[squad] dry-run 完成：{len(worker_records)} 个 worker 的产物已渲染（未启动 tmux/worker）")
        print(f"[squad] 检查：ls {sdir} / cat {worker_records[0].worktree}/.claude/settings.local.json")
    else:
        print(f"[squad] 已创建 squad '{spec.task_id}'，{len(worker_records)} 个 worker")
        print(f"[squad] 观察：tmux attach -t {session_name}")
        print(f"[squad] 状态：harness squad status")
    return 0


def cmd_status(args) -> int:
    root = Path(args.project or ".").resolve()
    active = list_active_squads(root)
    if not active:
        print("[squad] 当前没有活跃的 squad。")
        return 0

    for task_id in active:
        m = read_manifest(root, task_id)
        if m is None:
            continue
        print(f"\nSquad: {m.task_id} (tmux session: {m.tmux_session})")
        print(f"  base_branch: {m.base_branch}")
        print(f"  workers:")
        for w in m.workers:
            print(f"    - {w.name} [{w.capability}] → {w.worktree}")
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


def register_subcommand(subs) -> None:
    """Register `squad` subcommand tree on an argparse subparsers container."""
    sq = subs.add_parser("squad", help="多 agent 常驻协作（tmux + worktree，MVP 阶段 1）")
    sq_subs = sq.add_subparsers(dest="squad_command", required=True)

    c = sq_subs.add_parser("create", help="按 YAML spec 创建 squad 并启动 workers")
    c.add_argument("spec", help="YAML spec 文件路径")
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
