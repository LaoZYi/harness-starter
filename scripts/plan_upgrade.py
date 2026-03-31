from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_harness import discover_project, plan_upgrade


def _load_config(path: Path) -> dict[str, object]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise SystemExit("配置文件仅支持 .json 或 .toml")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan how harness files would upgrade in an existing repository.")
    parser.add_argument("--target", default=".", help="Target repository path")
    parser.add_argument("--config", help="Path to a JSON or TOML config file")
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
    parser.add_argument("--has-production", action="store_true")
    parser.add_argument("--no-production", action="store_true")
    parser.add_argument("--only", action="append", default=[], help="Only plan specific managed files")
    parser.add_argument("--show-diff", action="store_true", help="Print unified diffs for files that would update")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
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

    result = plan_upgrade(target, answers, only_files=args.only or None)

    if args.json:
        print(
            json.dumps(
                {
                    "target_root": result.target_root,
                    "create_files": result.create_files,
                    "update_files": result.update_files,
                    "unchanged_files": result.unchanged_files,
                    "checklist": result.checklist,
                    "diffs": result.diffs,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print(f"target: {result.target_root}")
    print(f"create: {len(result.create_files)}")
    for path in result.create_files:
        print(f"+ {path}")
    print(f"update: {len(result.update_files)}")
    for path in result.update_files:
        print(f"~ {path}")
    print(f"unchanged: {len(result.unchanged_files)}")
    for path in result.unchanged_files:
        print(f"= {path}")
    print("checklist:")
    for item in result.checklist:
        print(f"- {item}")
    if args.show_diff and result.diffs:
        print("diffs:")
        for path, diff_text in result.diffs.items():
            print(f"--- {path} ---")
            print(diff_text.rstrip())


if __name__ == "__main__":
    main()
