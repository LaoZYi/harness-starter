from __future__ import annotations

import sys

_COLOR = sys.stdout.isatty()

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"


def _wrap(code: str, text: str) -> str:
    return f"{code}{text}{_RESET}" if _COLOR else text


def green(text: str) -> str:
    return _wrap(_GREEN, text)


def yellow(text: str) -> str:
    return _wrap(_YELLOW, text)


def red(text: str) -> str:
    return _wrap(_RED, text)


def cyan(text: str) -> str:
    return _wrap(_CYAN, text)


def bold(text: str) -> str:
    return _wrap(_BOLD, text)


def dim(text: str) -> str:
    return _wrap(_DIM, text)


def step(current: int, total: int, label: str) -> None:
    prefix = f"[{current}/{total}]"
    print(f"{cyan(prefix)} {label}")


LANGUAGE_DEFAULTS: dict[str, dict[str, str]] = {
    "python": {"package_manager": "pip", "run_command": "python -m {slug}", "test_command": "pytest", "check_command": "ruff check .", "ci_command": "make ci"},
    "typescript": {"package_manager": "npm", "run_command": "npm start", "test_command": "npm test", "check_command": "npm run lint", "ci_command": "npm run ci"},
    "javascript": {"package_manager": "npm", "run_command": "npm start", "test_command": "npm test", "check_command": "npm run lint", "ci_command": "npm run ci"},
    "go": {"package_manager": "go", "run_command": "go run .", "test_command": "go test ./...", "check_command": "golangci-lint run", "ci_command": "make ci"},
    "rust": {"package_manager": "cargo", "run_command": "cargo run", "test_command": "cargo test", "check_command": "cargo clippy", "ci_command": "cargo test"},
    "java": {"package_manager": "gradle", "run_command": "./gradlew run", "test_command": "./gradlew test", "check_command": "./gradlew check", "ci_command": "./gradlew build"},
    "ruby": {"package_manager": "bundler", "run_command": "bundle exec ruby main.rb", "test_command": "bundle exec rspec", "check_command": "bundle exec rubocop", "ci_command": "bundle exec rake ci"},
    "php": {"package_manager": "composer", "run_command": "php artisan serve", "test_command": "vendor/bin/phpunit", "check_command": "vendor/bin/phpstan", "ci_command": "composer run ci"},
}


def prompt_choice(label: str, options: list[str], default: str) -> str:
    print(f"{label}:")
    default_idx = 0
    for i, opt in enumerate(options, 1):
        marker = cyan("*") if opt == default else " "
        print(f"  {marker} {i}) {opt}")
    hint = f" [默认: {default}]" if default in options else ""
    answer = input(f"输入编号或名称{hint}: ").strip()
    if not answer:
        return default
    if answer.isdigit():
        idx = int(answer) - 1
        if 0 <= idx < len(options):
            return options[idx]
    if answer in options:
        return answer
    return answer


def print_init_result(result: object) -> None:
    label = "previewed" if result.dry_run else "initialized"
    print(bold(f"{label}: {result.target_root}"))
    print(f"written: {len(result.written_files)}")
    for path in result.written_files:
        print(f"{green('+')} {path}")
    if result.skipped_files:
        print(f"skipped: {len(result.skipped_files)}")
        for path in result.skipped_files:
            print(f"{dim('=')} {path}")
    if result.summary_path:
        print(f"summary: {yellow(result.summary_path)}")


def print_upgrade_plan(result: object, show_diff: bool = False) -> None:
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
    if show_diff and result.diffs:
        print("diffs:")
        for path, diff_text in result.diffs.items():
            print(f"--- {path} ---")
            print(diff_text.rstrip())


def print_upgrade_apply(result: object) -> None:
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


def print_profile(profile: object) -> None:
    print(bold("== 探测结果 =="))
    for field in ("project_name", "project_type", "language", "package_manager",
                   "run_command", "test_command", "check_command", "ci_command",
                   "deploy_target", "has_production", "sensitivity"):
        print(f"{field}: {getattr(profile, field)}")
    print(f"source_paths: {', '.join(profile.source_paths) or '无'}")
    print(f"external_systems: {', '.join(profile.external_systems) or '无'}")
    if profile.notes:
        print("notes:")
        for note in profile.notes:
            print(f"  - {note}")


def print_assessment(result: object) -> None:
    color = green if result.readiness == "high" else yellow if result.readiness == "medium" else red
    print(f"\n{bold('== 评估结果 ==')}")
    print(f"readiness: {color(result.readiness)}")
    print(f"score: {bold(str(result.score))}")
    print(f"confidence: {result.confidence}")
    if result.dimensions:
        print("dimensions:")
        for k, v in result.dimensions.items():
            print(f"  {k}: {v}")
    if result.strengths:
        print("strengths:")
        for s in result.strengths:
            print(f"  {green('+')} {s}")
    if result.gaps:
        print("gaps:")
        for g in result.gaps:
            print(f"  {red('-')} {g}")
    if result.recommendations:
        print("recommendations:")
        for r in result.recommendations:
            print(f"  {yellow('>')} {r}")
