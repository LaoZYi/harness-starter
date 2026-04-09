"""Task log statistics and analysis."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from ._shared import require_harness
from .cli_utils import console

_TASK_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) ")
_REWORK_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) 返工")
_LESSON_RE = re.compile(r"^### ")


def _parse_dates(path: Path, pattern: re.Pattern[str]) -> list[datetime]:
    if not path.exists():
        return []
    dates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            try:
                dates.append(datetime.strptime(m.group(1), "%Y-%m-%d"))
            except ValueError:
                pass
    return dates


def run_stats(target: Path) -> None:
    from rich.table import Table
    from rich.panel import Panel

    target = target.resolve()
    require_harness(target)
    tl = target / ".agent-harness" / "task-log.md"
    ll = target / ".agent-harness" / "lessons.md"

    task_dates = _parse_dates(tl, _TASK_RE)
    rework_dates = _parse_dates(tl, _REWORK_RE)
    lesson_count = sum(1 for l in (ll.read_text(encoding="utf-8").splitlines() if ll.exists() else []) if _LESSON_RE.match(l))

    total = len(task_dates)
    reworks = len(rework_dates)

    if total == 0:
        console.print("[dim]task-log.md 中没有记录，暂无统计数据。[/dim]")
        return

    rework_rate = reworks / total * 100 if total else 0
    cutoff = datetime.now() - timedelta(days=30)
    recent = sum(1 for d in task_dates if d >= cutoff)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", min_width=16)
    table.add_column()

    table.add_row("总任务数", str(total))
    table.add_row("返工数", str(reworks))
    rate_color = "green" if rework_rate < 10 else "yellow" if rework_rate < 25 else "red"
    table.add_row("返工率", f"[{rate_color}]{rework_rate:.0f}%[/{rate_color}]")
    table.add_row("近 30 天任务", str(recent))
    table.add_row("教训积累", f"{lesson_count} 条")

    if task_dates:
        first = min(task_dates).strftime("%Y-%m-%d")
        last = max(task_dates).strftime("%Y-%m-%d")
        table.add_row("时间跨度", f"{first} ~ {last}")

    console.print(Panel(table, title="[bold]任务统计[/bold]", border_style="blue"))

    if rework_rate >= 25:
        console.print("\n  [red]![/red] 返工率较高，建议检查 lessons.md 是否充分利用。")
    if lesson_count == 0 and reworks > 0:
        console.print("\n  [yellow]![/yellow] 有返工但没有教训记录，建议返工时归因到 lessons.md。")
