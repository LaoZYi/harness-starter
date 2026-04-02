from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness import discover_project, execute_upgrade
from agent_harness.cli_utils import bold, dim, green, yellow


def _load_config(path: Path) -> dict[str, object]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise SystemExit("配置文件仅支持 .json 或 .toml")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a planned harness upgrade to an existing repository.")
    parser.add_argument("--target", default=".", help="Target repository path")
    parser.add_argument("--config", help="Path to a JSON or TOML config file")
    parser.add_argument("--project-name")
    parser.add_argument("--project-slug")
    parser.add_argument("--summary")
    parser.add_argument("--project-type", choices=["backend-service", "web-app", "cli-tool", "library", "worker", "mobile-app", "monorepo", "data-pipeline"])
    parser.add_argument("--language")
    parser.add_argument("--package-manager")
    parser.add_argument("--run-command")
    parser.add_argument("--test-command")
    parser.add_argument("--check-command")
    parser.add_argument("--ci-command")
    parser.add_argument("--deploy-target")
    parser.add_argument("--sensitivity", choices=["standard", "internal", "high"])
    parser.add_argument("--has-production", action="store_true")
    parser.add_argument("--no-production", action="store_true")
    parser.add_argument("--only", action="append", default=[], help="Only upgrade specific managed files")
    parser.add_argument("--dry-run", action="store_true", help="Preview upgrade without writing files")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    profile = discover_project(target)
    config = _load_config(Path(args.config).resolve()) if args.config else {}

    answers: dict[str, object] = {}
    for key in (
        "project_name",
        "project_slug",
        "summary",
        "project_type",
        "language",
        "package_manager",
        "run_command",
        "test_command",
        "check_command",
        "ci_command",
        "deploy_target",
        "sensitivity",
    ):
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

    result = execute_upgrade(target, answers, only_files=args.only or None, dry_run=args.dry_run)
    label = "previewed" if result.dry_run else "upgraded"
    print(bold(f"{label}: {result.target_root}"))
    print(f"created: {len(result.created_files)}")
    for path in result.created_files:
        print(f"  {green('+')} {path}")
    print(f"updated: {len(result.updated_files)}")
    for path in result.updated_files:
        print(f"  {yellow('~')} {path}")
    print(f"unchanged: {len(result.unchanged_files)}")
    for path in result.unchanged_files:
        print(f"  {dim('=')} {path}")
    if result.backup_root:
        print(f"backup: {yellow(result.backup_root)}")
    if result.selected_files:
        print(f"selected: {', '.join(result.selected_files)}")


if __name__ == "__main__":
    main()
