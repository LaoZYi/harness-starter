"""CLI handlers for `harness audit` subcommand tree.

同时提供 `main(argv=None)` 函数供 `.agent-harness/bin/audit` 独立调用——
项目内嵌运行时无需装 harness CLI。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import audit


def cmd_append(args) -> int:
    root = Path(args.target or ".").resolve()
    try:
        entry = audit.append_from_args(
            root, file=args.file, op=args.op, summary=args.summary,
            agent=args.agent,
        )
    except ValueError as exc:
        print(f"[audit] 参数校验失败：{exc}")
        return 2
    print(f"[audit] 已追加：{audit.format_entry(entry)}")
    return 0


def cmd_tail(args) -> int:
    root = Path(args.target or ".").resolve()
    entries = audit.tail(root, limit=args.limit)
    if not entries:
        print("[audit] 日志为空")
        return 0
    if args.json:
        for e in entries:
            print(e.to_json())
    else:
        for e in entries:
            print(audit.format_entry(e))
    return 0


def cmd_stats(args) -> int:
    root = Path(args.target or ".").resolve()
    s = audit.stats(root)
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0
    print(f"总条数：{s['total']}")
    if s["total"] == 0:
        return 0
    print(f"时间范围：{s['first_ts']} → {s['last_ts']}")
    print("按文件：")
    for k, v in sorted(s["by_file"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<18}  {v}")
    print("按操作：")
    for k, v in sorted(s["by_op"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<8}  {v}")
    print("按 agent：")
    for k, v in sorted(s["by_agent"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20}  {v}")
    return 0


def cmd_truncate(args) -> int:
    root = Path(args.target or ".").resolve()
    cutoff = audit._parse_iso_lenient(args.before)
    removed = audit.truncate_before(root, cutoff)
    print(f"[audit] 已移除 {removed} 条（cutoff={cutoff}）")
    return 0


def _add_audit_subcommands(au_subs) -> None:
    """Shared subcommand builder — used both by `harness audit` and standalone `bin/audit`."""
    ap = au_subs.add_parser("append", help="追加一条审计记录")
    ap.add_argument("--target", default=".", help="项目根目录（默认当前目录）")
    ap.add_argument("--file", required=True, choices=list(audit.TRACKED_FILES), help="被修改的文件")
    ap.add_argument("--op", required=True, choices=list(audit.VALID_OPS), help="操作类型")
    ap.add_argument("--summary", required=True, help="一行摘要")
    ap.add_argument("--agent", help="覆盖 agent 身份（默认读 HARNESS_AGENT env）")
    ap.set_defaults(func=cmd_append)

    tl = au_subs.add_parser("tail", help="查看最近 N 条审计记录")
    tl.add_argument("--target", default=".", help="项目根目录（默认当前目录）")
    tl.add_argument("--limit", type=int, default=20, help="返回条数（默认 20）")
    tl.add_argument("--json", action="store_true", help="按 JSONL 原样输出")
    tl.set_defaults(func=cmd_tail)

    st = au_subs.add_parser("stats", help="按 file/op/agent 聚合统计")
    st.add_argument("--target", default=".", help="项目根目录（默认当前目录）")
    st.add_argument("--json", action="store_true", help="JSON 输出")
    st.set_defaults(func=cmd_stats)

    tr = au_subs.add_parser("truncate", help="裁剪早于指定时间的记录")
    tr.add_argument("--target", default=".", help="项目根目录（默认当前目录）")
    tr.add_argument("--before", required=True, help="ISO 时间（YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SSZ）")
    tr.set_defaults(func=cmd_truncate)


def register_subcommand(subs) -> None:
    au = subs.add_parser("audit", help="关键文件变更审计日志（.agent-harness/audit.jsonl）")
    au_subs = au.add_subparsers(dest="audit_command", required=True)
    _add_audit_subcommands(au_subs)


def main(argv=None) -> int:
    """Standalone entry for `.agent-harness/bin/audit` (no harness CLI needed)."""
    parser = argparse.ArgumentParser(
        prog="audit",
        description="项目内嵌审计日志运行时（等价于 `harness audit`）",
    )
    subs = parser.add_subparsers(dest="audit_command", required=True)
    _add_audit_subcommands(subs)
    args = parser.parse_args(argv)
    return args.func(args)
