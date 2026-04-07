from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

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


def print_detected(answers: dict[str, object]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="cyan")
    for key in ("language", "package_manager", "run_command", "test_command", "check_command", "ci_command", "deploy_target"):
        table.add_row(key, str(answers.get(key, "")))
    console.print()
    console.print(Panel(table, title="[bold]自动探测结果[/bold]", border_style="green"))


def print_init_result(result: object) -> None:
    label = "[bold green]初始化完成[/bold green]" if not result.dry_run else "[bold yellow]预演完成[/bold yellow]"
    console.print(f"\n{label}  {result.target_root}")
    if result.written_files:
        console.print(f"  写入 [green]{len(result.written_files)}[/green] 个文件")
        for path in result.written_files:
            console.print(f"    [green]+[/green] {path}")
    if result.skipped_files:
        console.print(f"  跳过 [dim]{len(result.skipped_files)}[/dim] 个文件")
        for path in result.skipped_files:
            console.print(f"    [dim]=[/dim] {path}")
    if result.summary_path:
        console.print(f"  摘要: [yellow]{result.summary_path}[/yellow]")


def print_upgrade_plan(result: object, show_diff: bool = False) -> None:
    console.print(f"\n[bold]升级计划[/bold]  {result.target_root}")
    if result.create_files:
        console.print(f"  新增 [green]{len(result.create_files)}[/green] 个文件")
        for path in result.create_files:
            console.print(f"    [green]+[/green] {path}")
    if result.update_files:
        console.print(f"  更新 [yellow]{len(result.update_files)}[/yellow] 个文件")
        for path in result.update_files:
            console.print(f"    [yellow]~[/yellow] {path}")
    if result.unchanged_files:
        console.print(f"  未变 [dim]{len(result.unchanged_files)}[/dim] 个文件")
    if result.checklist:
        console.print("  检查项:")
        for item in result.checklist:
            console.print(f"    - {item}")
    if show_diff and result.diffs:
        for path, diff_text in result.diffs.items():
            console.print(f"\n  [bold]--- {path} ---[/bold]")
            console.print(diff_text.rstrip())


def print_upgrade_apply(result: object) -> None:
    label = "[bold green]升级完成[/bold green]" if not result.dry_run else "[bold yellow]预演完成[/bold yellow]"
    console.print(f"\n{label}  {result.target_root}")
    if result.created_files:
        console.print(f"  新增 [green]{len(result.created_files)}[/green] 个文件")
        for path in result.created_files:
            console.print(f"    [green]+[/green] {path}")
    if result.updated_files:
        console.print(f"  更新 [yellow]{len(result.updated_files)}[/yellow] 个文件")
        for path in result.updated_files:
            console.print(f"    [yellow]~[/yellow] {path}")
    if result.unchanged_files:
        console.print(f"  未变 [dim]{len(result.unchanged_files)}[/dim] 个文件")
    if result.backup_root:
        console.print(f"  备份: [yellow]{result.backup_root}[/yellow]")
    if result.selected_files:
        console.print(f"  选定: {', '.join(result.selected_files)}")


def print_verify_warnings(warnings: list[str]) -> None:
    if warnings:
        console.print("\n[bold yellow]验证警告[/bold yellow]")
        for w in warnings:
            console.print(f"  [yellow]![/yellow] {w}")
    else:
        console.print("\n[bold green]验证通过[/bold green]")


def print_profile(profile: object) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()
    for field in ("project_name", "project_type", "language", "package_manager",
                   "run_command", "test_command", "check_command", "ci_command",
                   "deploy_target", "has_production", "sensitivity"):
        table.add_row(field, str(getattr(profile, field)))
    table.add_row("source_paths", ", ".join(profile.source_paths) or "无")
    table.add_row("external_systems", ", ".join(profile.external_systems) or "无")
    console.print(Panel(table, title="[bold]探测结果[/bold]", border_style="blue"))
    if profile.notes:
        for note in profile.notes:
            console.print(f"  [dim]-[/dim] {note}")


def print_assessment(result: object) -> None:
    color = "green" if result.readiness == "high" else "yellow" if result.readiness == "medium" else "red"
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()
    table.add_row("readiness", f"[{color}]{result.readiness}[/{color}]")
    table.add_row("score", f"[bold]{result.score}[/bold]")
    table.add_row("confidence", result.confidence)
    if result.dimensions:
        for k, v in result.dimensions.items():
            table.add_row(f"  {k}", str(v))
    console.print(Panel(table, title="[bold]评估结果[/bold]", border_style=color))
    if result.strengths:
        for s in result.strengths:
            console.print(f"  [green]+[/green] {s}")
    if result.gaps:
        for g in result.gaps:
            console.print(f"  [red]-[/red] {g}")
    if result.recommendations:
        for r in result.recommendations:
            console.print(f"  [yellow]>[/yellow] {r}")
