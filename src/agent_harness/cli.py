"""Unified CLI for agent-harness-framework."""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import asdict
from pathlib import Path

from .assessment import assess_project
from .cli_utils import (
    console, maybe_git_commit, print_assessment, print_init_result, print_profile,
    print_upgrade_apply, print_upgrade_plan, print_verify_warnings,
)
from .discovery import discover_project
from .init_flow import (
    PROJECT_TYPE_CHOICES, SENSITIVITY_CHOICES, ask_scaffold, copy_scaffold,
    interactive_init, non_interactive_init,
)
from .initializer import initialize_project
from .models import ProjectProfile
from .upgrade import plan_upgrade as _plan_upgrade, execute_upgrade as _execute_upgrade, verify_upgrade as _verify
from .audit_cli import register_subcommand as _reg_audit
from .agent_cli import register_subcommand as _reg_agent
from .squad.cli import register_subcommand as _reg_squad

PROJECT_FIELDS = (
    "project_name", "project_slug", "summary", "project_type",
    "language", "package_manager", "run_command", "test_command",
    "check_command", "ci_command", "deploy_target", "sensitivity",
)

_FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]

def _guard_self_init(target: Path) -> None:
    if target.resolve() == _FRAMEWORK_ROOT:
        raise SystemExit("错误：目标目录是框架仓库自身。请指定目标项目：harness init /path/to/your-project")

def _load_config(path: Path) -> dict[str, object]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise SystemExit("配置文件仅支持 .json 或 .toml")

def _auto_discover_config(target: Path) -> dict[str, object]:
    p = target / ".harness.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

def _add_common_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-name")
    parser.add_argument("--project-slug")
    parser.add_argument("--summary")
    parser.add_argument("--project-type", choices=PROJECT_TYPE_CHOICES)
    parser.add_argument("--language")
    parser.add_argument("--package-manager")
    parser.add_argument("--run-command")
    parser.add_argument("--test-command")
    parser.add_argument("--check-command")
    parser.add_argument("--ci-command")
    parser.add_argument("--deploy-target")
    parser.add_argument("--sensitivity", choices=SENSITIVITY_CHOICES)
    parser.add_argument("--has-production", action="store_true")
    parser.add_argument("--no-production", action="store_true")

def _resolve_answers(args: argparse.Namespace, profile: ProjectProfile, config: dict[str, object]) -> dict[str, object]:
    answers: dict[str, object] = {}
    for key in PROJECT_FIELDS:
        cli_value = getattr(args, key.replace("-", "_"), None)
        if cli_value is not None:
            answers[key] = cli_value
        elif key in config:
            answers[key] = config[key]
        else:
            answers[key] = getattr(profile, key, None)
    if args.has_production:
        answers["has_production"] = True
    elif args.no_production:
        answers["has_production"] = False
    elif "has_production" in config:
        answers["has_production"] = bool(config["has_production"])
    else:
        answers["has_production"] = profile.has_production
    return answers

def _merged_config(target: Path, args: argparse.Namespace) -> dict[str, object]:
    explicit = _load_config(Path(args.config).resolve()) if args.config else {}
    return {**_auto_discover_config(target), **explicit}

# ── command handlers ──
def _cmd_init(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    if not args.assess_only:
        _guard_self_init(target)
    if args.assess_only:
        profile = discover_project(target)
        result = assess_project(profile, root=target)
        if args.json:
            print(json.dumps({"profile": asdict(profile), "assessment": asdict(result)}, ensure_ascii=False, indent=2))
            return
        print_profile(profile)
        print_assessment(result)
        return
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    is_interactive = not (args.non_interactive or args.config or _auto_discover_config(target))
    scaffold_src = getattr(args, "scaffold", None)
    if scaffold_src:
        copy_scaffold(Path(scaffold_src).expanduser(), target)
        console.print(f"  [green]已复制框架代码[/green]：{Path(scaffold_src).name}")
    elif is_interactive:
        ask_scaffold(target)
    profile = discover_project(target)
    config = _merged_config(target, args)
    if is_interactive:
        answers = interactive_init(target, profile, config)
    else:
        answers = non_interactive_init(args, profile, config, _resolve_answers)
    if getattr(args, "no_superpowers", False):
        answers["superpowers"] = False
    result = initialize_project(target, answers, force=args.force, dry_run=args.dry_run)
    print_init_result(result)
    if not result.dry_run:
        print_verify_warnings(_verify(target))
        maybe_git_commit(target, args, result.written_files)

def _cmd_upgrade_plan(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    _guard_self_init(target)
    profile = discover_project(target)
    config = _merged_config(target, args)
    answers = _resolve_answers(args, profile, config)
    result = _plan_upgrade(target, answers, only_files=args.only or None)
    if args.json:
        print(json.dumps({
            "target_root": result.target_root, "create_files": result.create_files,
            "update_files": result.update_files, "unchanged_files": result.unchanged_files,
            "checklist": result.checklist, "diffs": result.diffs,
        }, ensure_ascii=False, indent=2))
        return
    print_upgrade_plan(result, show_diff=args.show_diff)

def _cmd_upgrade_apply(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    _guard_self_init(target)
    profile = discover_project(target)
    config = _merged_config(target, args)
    answers = _resolve_answers(args, profile, config)
    result = _execute_upgrade(target, answers, only_files=args.only or None, dry_run=args.dry_run)
    print_upgrade_apply(result)
    if not result.dry_run:
        print_verify_warnings(_verify(target))

def _cmd_doctor(args: argparse.Namespace) -> None:
    from .doctor import run_doctor
    run_doctor(Path(args.target).resolve())

def _cmd_export(args: argparse.Namespace) -> None:
    from .export import run_export
    run_export(Path(args.target).resolve(), output=args.output, as_json=args.json)

def _cmd_stats(args: argparse.Namespace) -> None:
    from .stats import run_stats
    run_stats(Path(args.target).resolve())

def _cmd_sync(args: argparse.Namespace) -> None:
    from .sync_context import resolve_meta, run_sync, run_sync_all
    target = Path(args.target).resolve() if not args.all else None
    meta = resolve_meta(args.meta, target)
    if args.all:
        run_sync_all(meta, dry_run=args.dry_run)
    else:
        run_sync(target, meta, dry_run=args.dry_run)

def _cmd_memory_rebuild(args: argparse.Namespace) -> None:
    from .memory import run_rebuild_cli
    run_rebuild_cli(Path(args.target).resolve(), force=args.force)


# ── parser ──

def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="harness", description="Agent harness framework CLI.")
    subs = root.add_subparsers(dest="command")

    init_p = subs.add_parser("init", help="初始化 harness")
    init_p.add_argument("target", help="目标项目路径")
    init_p.add_argument("--config", help="JSON/TOML 配置文件")
    init_p.add_argument("--scaffold", help="基于现有框架创建（复制框架代码到目标目录）")
    _add_common_project_args(init_p)
    init_p.add_argument("--assess-only", action="store_true", help="只做探测评估")
    init_p.add_argument("--force", action="store_true", help="覆盖已有文件")
    init_p.add_argument("--dry-run", action="store_true", help="预演不写文件")
    init_p.add_argument("--non-interactive", action="store_true", help="不交互")
    init_p.add_argument("--json", action="store_true", help="JSON 输出")
    init_p.add_argument("--git-commit", action="store_true", default=None, help="初始化后自动 git commit")
    init_p.add_argument("--no-git-commit", action="store_false", dest="git_commit", help="不自动 git commit")
    init_p.add_argument("--description")
    init_p.add_argument("--features")
    init_p.add_argument("--constraints")
    init_p.add_argument("--done-criteria")
    init_p.add_argument("--no-superpowers", action="store_true", help="不生成 superpowers 工作流文件")
    init_p.set_defaults(func=_cmd_init)

    upgrade_p = subs.add_parser("upgrade", help="升级 harness 文件")
    upgrade_subs = upgrade_p.add_subparsers(dest="upgrade_command")
    plan_p = upgrade_subs.add_parser("plan", help="预览升级")
    plan_p.add_argument("target", help="目标项目路径")
    plan_p.add_argument("--config")
    _add_common_project_args(plan_p)
    plan_p.add_argument("--only", action="append", default=[], help="限定文件")
    plan_p.add_argument("--show-diff", action="store_true", help="显示 diff")
    plan_p.add_argument("--json", action="store_true")
    plan_p.set_defaults(func=_cmd_upgrade_plan)
    apply_p = upgrade_subs.add_parser("apply", help="执行升级")
    apply_p.add_argument("target", help="目标项目路径")
    apply_p.add_argument("--config")
    _add_common_project_args(apply_p)
    apply_p.add_argument("--only", action="append", default=[], help="限定文件")
    apply_p.add_argument("--dry-run", action="store_true")
    apply_p.set_defaults(func=_cmd_upgrade_apply)

    doc_p = subs.add_parser("doctor", help="检查 harness 健康状态")
    doc_p.add_argument("target", help="目标项目路径")
    doc_p.set_defaults(func=_cmd_doctor)

    exp_p = subs.add_parser("export", help="导出项目画像")
    exp_p.add_argument("target", help="目标项目路径")
    exp_p.add_argument("-o", "--output", help="输出文件路径")
    exp_p.add_argument("--json", action="store_true", help="JSON 格式")
    exp_p.set_defaults(func=_cmd_export)

    sta_p = subs.add_parser("stats", help="任务数据统计")
    sta_p.add_argument("target", help="目标项目路径")
    sta_p.set_defaults(func=_cmd_stats)

    sync_p = subs.add_parser("sync", help="从 meta repo 同步跨服务上下文和共享规则")
    sync_p.add_argument("target", nargs="?", default=".", help="服务仓库路径")
    sync_p.add_argument("--meta", default=None, help="meta 仓库路径（可省略，自动检测）")
    sync_p.add_argument("--all", action="store_true", help="同步 registry 中所有服务")
    sync_p.add_argument("--dry-run", action="store_true", help="预演不写文件")
    sync_p.set_defaults(func=_cmd_sync)

    mem_p = subs.add_parser("memory", help="分层记忆管理（memory-index.md 维护）")
    rebuild_p = mem_p.add_subparsers(dest="memory_command").add_parser("rebuild", help="从 lessons/task-log 重建 memory-index.md")
    rebuild_p.add_argument("target", nargs="?", default=".", help="项目根目录（默认当前目录）")
    rebuild_p.add_argument("--force", action="store_true", help="覆盖已存在的 memory-index.md")
    rebuild_p.set_defaults(func=_cmd_memory_rebuild)
    from .skills_lint import register_subcommand as _reg_skills
    _reg_squad(subs); _reg_audit(subs); _reg_agent(subs); _reg_skills(subs)
    return root

def main() -> None:
    args = build_parser().parse_args()
    if not hasattr(args, "func"): sys.exit(1)
    rc = args.func(args)
    if isinstance(rc, int) and rc != 0: sys.exit(rc)

if __name__ == "__main__":
    main()
