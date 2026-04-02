"""Health check for an initialized harness project."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .cli_utils import console

_PLACEHOLDER_RE = re.compile(r"\{\{\s*[a-z0-9_]+\s*\}\}")
_TASK_HEADING_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} ")
_REWORK_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} 返工")
_LESSON_RE = re.compile(r"^### ")
_TODO_RE = re.compile(r"待补充")


def _count_headings(path: Path, pattern: re.Pattern[str]) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if pattern.match(line))


def _count_pattern_in_dir(root: Path, pattern: re.Pattern[str], glob: str = "*.md") -> int:
    count = 0
    for p in root.rglob(glob):
        count += len(pattern.findall(p.read_text(encoding="utf-8")))
    return count


def run_doctor(target: Path) -> None:
    from rich.table import Table

    target = target.resolve()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", min_width=20)
    table.add_column()

    issues: list[str] = []

    # AGENTS.md
    agents = target / "AGENTS.md"
    if agents.exists():
        lines = len(agents.read_text(encoding="utf-8").splitlines())
        status = f"[green]✓[/green] {lines} 行" if lines <= 80 else f"[yellow]![/yellow] {lines} 行（超过 80）"
        if lines > 80:
            issues.append("AGENTS.md 超过 80 行，建议拆分到 docs/")
        table.add_row("AGENTS.md", status)
    else:
        table.add_row("AGENTS.md", "[red]✗ 不存在[/red]")
        issues.append("AGENTS.md 不存在")

    # project.json
    pj = target / ".agent-harness" / "project.json"
    if pj.exists():
        try:
            json.loads(pj.read_text(encoding="utf-8"))
            table.add_row("project.json", "[green]✓[/green] 合法")
        except json.JSONDecodeError:
            table.add_row("project.json", "[red]✗ JSON 格式错误[/red]")
            issues.append("project.json JSON 格式错误")
    else:
        table.add_row("project.json", "[red]✗ 不存在[/red]")
        issues.append("project.json 不存在")

    # task-log.md
    tl = target / ".agent-harness" / "task-log.md"
    task_count = _count_headings(tl, _TASK_HEADING_RE)
    rework_count = _count_headings(tl, _REWORK_RE)
    if task_count > 0:
        table.add_row("task-log.md", f"{task_count} 条记录（返工 {rework_count} 条）")
    else:
        table.add_row("task-log.md", "[dim]空（尚未使用）[/dim]")

    # lessons.md
    ll = target / ".agent-harness" / "lessons.md"
    lesson_count = _count_headings(ll, _LESSON_RE)
    table.add_row("lessons.md", f"{lesson_count} 条教训" if lesson_count else "[dim]空[/dim]")

    # current-task.md
    ct = target / ".agent-harness" / "current-task.md"
    if ct.exists():
        content = ct.read_text(encoding="utf-8").strip()
        has_content = any(line.strip() and not line.startswith("#") and not line.startswith("<!--") for line in content.splitlines())
        table.add_row("current-task.md", "[yellow]有进行中任务[/yellow]" if has_content else "[green]空闲[/green]")
    else:
        table.add_row("current-task.md", "[dim]不存在[/dim]")

    # docs/ 待补充
    docs_dir = target / "docs"
    todo_count = _count_pattern_in_dir(docs_dir, _TODO_RE) if docs_dir.is_dir() else 0
    table.add_row("docs/ 待补充", f"[yellow]{todo_count} 处[/yellow]" if todo_count else "[green]0 处[/green]")

    # 占位符
    placeholder_count = 0
    for md in (target / "AGENTS.md", target / "CLAUDE.md"):
        if md.exists():
            placeholder_count += len(_PLACEHOLDER_RE.findall(md.read_text(encoding="utf-8")))
    table.add_row("未填充占位符", f"[red]{placeholder_count} 处[/red]" if placeholder_count else "[green]0 处[/green]")
    if placeholder_count:
        issues.append(f"AGENTS.md/CLAUDE.md 中有 {placeholder_count} 处未填充占位符")

    from rich.panel import Panel
    console.print(Panel(table, title="[bold]健康检查[/bold]", border_style="blue"))

    if issues:
        console.print("\n[bold yellow]建议[/bold yellow]")
        for i in issues:
            console.print(f"  [yellow]![/yellow] {i}")
    else:
        console.print("\n[bold green]一切正常[/bold green]")
