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
    LANGUAGE_DEFAULTS, print_assessment, print_init_result, print_profile,
    print_upgrade_apply, print_upgrade_plan, prompt_choice,
)
from .discovery import discover_project
from .initializer import initialize_project
from .upgrade import plan_upgrade as _plan_upgrade, execute_upgrade as _execute_upgrade


PROJECT_FIELDS = (
    "project_name", "project_slug", "summary", "project_type",
    "language", "package_manager", "run_command", "test_command",
    "check_command", "ci_command", "deploy_target", "sensitivity",
)

PROJECT_TYPE_CHOICES = [
    "backend-service", "web-app", "cli-tool", "library",
    "worker", "mobile-app", "monorepo", "data-pipeline",
]

SENSITIVITY_CHOICES = ["standard", "internal", "high"]

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


def _resolve_answers(args: argparse.Namespace, profile: object, config: dict[str, object]) -> dict[str, object]:
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


def _prompt(label: str, default: str) -> str:
    answer = input(f"{label} [{default}]: " if default else f"{label}: ").strip()
    return answer or default


def _prompt_bool(label: str, default: bool) -> bool:
    answer = input(f"{label} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    return default if not answer else answer in {"y", "yes"}




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
    profile = discover_project(target)
    config = _merged_config(target, args)

    answers: dict[str, object] = {}
    ni = args.non_interactive

    def _ask(key: str, label: str, cli_val: str | None, default: str, choices: list[str] | None = None) -> None:
        if cli_val is not None:
            answers[key] = cli_val
        elif key in config:
            answers[key] = str(config[key])
        elif ni:
            answers[key] = default
        elif choices:
            answers[key] = prompt_choice(label, choices, default)
        else:
            answers[key] = _prompt(label, default)

    _ask("project_name", "项目名", args.project_name, profile.project_name)
    _ask("project_slug", "项目 slug", args.project_slug, profile.project_slug)
    _ask("summary", "一句话目标", args.summary, profile.summary)
    _ask("project_type", "项目类型", args.project_type, profile.project_type, PROJECT_TYPE_CHOICES)
    _ask("language", "主要语言", args.language, profile.language)

    lang = str(answers.get("language", "unknown"))
    lang_defs = LANGUAGE_DEFAULTS.get(lang, {})
    slug = str(answers.get("project_slug", "project"))

    def _lang_default(key: str, profile_val: str) -> str:
        if profile_val and profile_val not in ("TODO", "unknown", "未定"):
            return profile_val
        tmpl = lang_defs.get(key, profile_val)
        return tmpl.replace("{slug}", slug) if tmpl else profile_val

    _ask("package_manager", "包管理器", args.package_manager, _lang_default("package_manager", profile.package_manager))
    _ask("run_command", "运行命令", args.run_command, _lang_default("run_command", profile.run_command))
    _ask("test_command", "测试命令", args.test_command, _lang_default("test_command", profile.test_command))
    _ask("check_command", "检查命令", args.check_command, _lang_default("check_command", profile.check_command))
    _ask("ci_command", "CI 命令", args.ci_command, _lang_default("ci_command", profile.ci_command))
    _ask("deploy_target", "部署目标", args.deploy_target, profile.deploy_target)
    _ask("sensitivity", "敏感级别", args.sensitivity, profile.sensitivity, SENSITIVITY_CHOICES)

    for ek in ("description", "features", "constraints", "done_criteria"):
        cv = getattr(args, ek, None)
        if cv is not None:
            answers[ek] = cv
        elif ek in config:
            answers[ek] = config[ek]

    if args.has_production:
        answers["has_production"] = True
    elif args.no_production:
        answers["has_production"] = False
    elif "has_production" in config:
        answers["has_production"] = bool(config["has_production"])
    elif ni:
        answers["has_production"] = profile.has_production
    else:
        answers["has_production"] = _prompt_bool("是否已有生产环境", profile.has_production)

    result = initialize_project(target, answers, force=args.force, dry_run=args.dry_run)
    print_init_result(result)


def _cmd_upgrade_plan(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    _guard_self_init(target)
    profile = discover_project(target)
    config = _merged_config(target, args)
    answers = _resolve_answers(args, profile, config)
    result = _plan_upgrade(target, answers, only_files=args.only or None)

    if args.json:
        print(json.dumps({
            "target_root": result.target_root,
            "create_files": result.create_files,
            "update_files": result.update_files,
            "unchanged_files": result.unchanged_files,
            "checklist": result.checklist,
            "diffs": result.diffs,
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


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="harness", description="Agent harness framework CLI.")
    subs = root.add_subparsers(dest="command")

    init_p = subs.add_parser("init", help="Initialize harness files in a repository")
    init_p.add_argument("target", help="目标项目路径")
    init_p.add_argument("--config", help="Path to a JSON or TOML config file")
    _add_common_project_args(init_p)
    init_p.add_argument("--assess-only", action="store_true", help="Only run discovery and assessment")
    init_p.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_p.add_argument("--dry-run", action="store_true", help="Preview without writing")
    init_p.add_argument("--non-interactive", action="store_true", help="Do not prompt")
    init_p.add_argument("--json", action="store_true", help="Print raw JSON (with --assess-only)")
    init_p.add_argument("--description")
    init_p.add_argument("--features")
    init_p.add_argument("--constraints")
    init_p.add_argument("--done-criteria")
    init_p.set_defaults(func=_cmd_init)

    upgrade_p = subs.add_parser("upgrade", help="Upgrade harness files in an existing repository")
    upgrade_subs = upgrade_p.add_subparsers(dest="upgrade_command")

    plan_p = upgrade_subs.add_parser("plan", help="Preview upgrade changes")
    plan_p.add_argument("target", help="目标项目路径")
    plan_p.add_argument("--config")
    _add_common_project_args(plan_p)
    plan_p.add_argument("--only", action="append", default=[], help="Limit to specific files")
    plan_p.add_argument("--show-diff", action="store_true", help="Show unified diffs")
    plan_p.add_argument("--json", action="store_true")
    plan_p.set_defaults(func=_cmd_upgrade_plan)

    apply_p = upgrade_subs.add_parser("apply", help="Execute upgrade")
    apply_p.add_argument("target", help="目标项目路径")
    apply_p.add_argument("--config")
    _add_common_project_args(apply_p)
    apply_p.add_argument("--only", action="append", default=[], help="Limit to specific files")
    apply_p.add_argument("--dry-run", action="store_true")
    apply_p.set_defaults(func=_cmd_upgrade_apply)

    return root


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
