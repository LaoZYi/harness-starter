from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness.discovery import discover_project
from agent_harness.initializer import initialize_project


def _prompt(label: str, default: str) -> str:
    prompt = f"{label} [{default}]: " if default else f"{label}: "
    answer = input(prompt).strip()
    return answer or default


def _prompt_bool(label: str, default: bool) -> bool:
    default_label = "Y/n" if default else "y/N"
    answer = input(f"{label} [{default_label}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize Codex/Claude Code harness files in a repository.")
    parser.add_argument("--target", default=".", help="Target repository path")
    parser.add_argument("--project-name")
    parser.add_argument("--project-slug")
    parser.add_argument("--summary")
    parser.add_argument("--project-type", choices=["backend-service", "web-app", "cli-tool", "library", "worker"])
    parser.add_argument("--language")
    parser.add_argument("--package-manager")
    parser.add_argument("--run-command")
    parser.add_argument("--test-command")
    parser.add_argument("--check-command")
    parser.add_argument("--ci-command")
    parser.add_argument("--deploy-target")
    parser.add_argument("--sensitivity", choices=["standard", "internal", "high"])
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files")
    parser.add_argument("--dry-run", action="store_true", help="Preview generated files without writing them")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt for missing values")
    parser.add_argument("--has-production", action="store_true", help="Mark the project as having production")
    parser.add_argument("--no-production", action="store_true", help="Mark the project as not having production")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
    profile = discover_project(target)

    answers: dict[str, object] = {}
    string_fields = [
        ("project_name", "项目名", args.project_name, profile.project_name),
        ("project_slug", "项目 slug", args.project_slug, profile.project_slug),
        ("summary", "一句话目标", args.summary, profile.summary),
        ("project_type", "项目类型", args.project_type, profile.project_type),
        ("language", "主要语言", args.language, profile.language),
        ("package_manager", "包管理器", args.package_manager, profile.package_manager),
        ("run_command", "运行命令", args.run_command, profile.run_command),
        ("test_command", "测试命令", args.test_command, profile.test_command),
        ("check_command", "检查命令", args.check_command, profile.check_command),
        ("ci_command", "CI 命令", args.ci_command, profile.ci_command),
        ("deploy_target", "部署目标", args.deploy_target, profile.deploy_target),
        ("sensitivity", "敏感级别", args.sensitivity, profile.sensitivity),
    ]

    for key, label, current, default in string_fields:
        if current is not None:
            answers[key] = current
        elif args.non_interactive:
            answers[key] = default
        else:
            answers[key] = _prompt(label, default)

    if args.has_production:
        answers["has_production"] = True
    elif args.no_production:
        answers["has_production"] = False
    elif args.non_interactive:
        answers["has_production"] = profile.has_production
    else:
        answers["has_production"] = _prompt_bool("是否已有生产环境", profile.has_production)

    result = initialize_project(target, answers, force=args.force, dry_run=args.dry_run)
    print(f"{'previewed' if result.dry_run else 'initialized'}: {result.target_root}")
    print(f"written: {len(result.written_files)}")
    for path in result.written_files:
        print(f"+ {path}")
    if result.skipped_files:
        print(f"skipped: {len(result.skipped_files)}")
        for path in result.skipped_files:
            print(f"= {path}")


if __name__ == "__main__":
    main()
