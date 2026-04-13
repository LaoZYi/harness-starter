"""CLI handlers for `harness agent` subcommand tree (Issue #14)."""
from __future__ import annotations

from pathlib import Path

from . import agent


def cmd_init(args) -> int:
    root = Path(args.target or ".").resolve()
    try:
        d = agent.init_agent(root, args.id)
    except agent.AgentError as exc:
        print(f"[agent] {exc}")
        return 2
    print(f"[agent] 已初始化：{d}")
    return 0


def cmd_diary(args) -> int:
    root = Path(args.target or ".").resolve()
    try:
        line = agent.diary_append(root, args.id, args.message)
    except agent.AgentError as exc:
        print(f"[agent] {exc}")
        return 2
    print(f"[agent] 已记录：{line.rstrip()}")
    return 0


def cmd_status(args) -> int:
    root = Path(args.target or ".").resolve()
    try:
        agent.status_set(root, args.id, args.state)
    except agent.AgentError as exc:
        print(f"[agent] {exc}")
        return 2
    print(f"[agent] {args.id} 状态已更新")
    return 0


def cmd_list(args) -> int:
    root = Path(args.target or ".").resolve()
    records = agent.list_agents(root)
    if not records:
        print("[agent] 当前没有活跃 agent。使用 `harness agent init <id>` 创建。")
        return 0
    print(f"{'agent':<20}  {'last_activity':<22}  {'lines':<6}  status")
    for r in records:
        status = (r.status[:50] + "...") if len(r.status) > 50 else r.status
        print(f"{r.id:<20}  {r.last_activity or '—':<22}  {r.diary_lines:<6}  {status}")
    return 0


def cmd_aggregate(args) -> int:
    root = Path(args.target or ".").resolve()
    try:
        text = agent.aggregate(root, args.ids if args.ids else None)
    except agent.AgentError as exc:
        print(f"[agent] {exc}")
        return 2
    print(text)
    return 0


def register_subcommand(subs) -> None:
    ag = subs.add_parser("agent", help="多 agent 日志隔离（agents/<id>/{diary,status}.md）")
    ag_subs = ag.add_subparsers(dest="agent_command", required=True)

    i = ag_subs.add_parser("init", help="创建 agent 目录（幂等）")
    i.add_argument("id", help="agent id（^[a-z0-9][a-z0-9-]{0,30}$）")
    i.add_argument("--target", default=".", help="项目根目录")
    i.set_defaults(func=cmd_init)

    d = ag_subs.add_parser("diary", help="向 agent diary.md 追加一行")
    d.add_argument("id", help="agent id")
    d.add_argument("message", help="日记内容（一行）")
    d.add_argument("--target", default=".", help="项目根目录")
    d.set_defaults(func=cmd_diary)

    s = ag_subs.add_parser("status", help="覆盖 agent status.md 为当前状态")
    s.add_argument("id", help="agent id")
    s.add_argument("state", help="状态描述")
    s.add_argument("--target", default=".", help="项目根目录")
    s.set_defaults(func=cmd_status)

    l = ag_subs.add_parser("list", help="列出活跃 agent（按最近活动排序）")
    l.add_argument("--target", default=".", help="项目根目录")
    l.set_defaults(func=cmd_list)

    a = ag_subs.add_parser("aggregate", help="汇总 diary 供主 agent 回读")
    a.add_argument("ids", nargs="*", help="只汇总这些 id（留空=全部）")
    a.add_argument("--target", default=".", help="项目根目录")
    a.set_defaults(func=cmd_aggregate)
