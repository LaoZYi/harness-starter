"""CLI entry for `harness lfg audit` — see lfg_audit.py for the core logic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lfg_audit import audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness lfg audit")
    parser.add_argument(
        "--repo",
        default=".",
        help="框架仓库根目录（默认当前目录）",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="机读 JSON 输出",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=7.0,
        help="合格阈值（总分 10）。< 阈值退出码 1（默认 7.0）",
    )
    args = parser.parse_args(argv)

    try:
        card = audit(Path(args.repo))
    except FileNotFoundError as exc:
        print(f"[lfg-audit] FAIL：{exc}")
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[lfg-audit] FAIL：{exc}")
        return 2

    if args.as_json:
        print(json.dumps(card.to_json(), ensure_ascii=False, indent=2))
    else:
        print(card.to_console())

    return 0 if card.total >= args.threshold else 1


def register_subcommand(subs) -> None:
    """Register `harness lfg audit` on argparse subparsers."""
    lfg_p = subs.add_parser("lfg", help="/lfg 体检（威力释放度评分）")
    lfg_subs = lfg_p.add_subparsers(dest="lfg_command")
    audit_p = lfg_subs.add_parser(
        "audit",
        help="对 /lfg 做 10 维 scorecard 静态体检",
    )
    audit_p.add_argument("--repo", default=".", help="框架仓库根目录")
    audit_p.add_argument("--json", dest="as_json", action="store_true")
    audit_p.add_argument("--threshold", type=float, default=7.0)
    audit_p.set_defaults(func=_cli_entry)


def _cli_entry(args) -> int:
    argv: list[str] = ["--repo", args.repo]
    if getattr(args, "as_json", False):
        argv.append("--json")
    argv.extend(["--threshold", str(args.threshold)])
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
