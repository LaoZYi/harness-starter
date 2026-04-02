"""Export project snapshot for sharing or onboarding."""
from __future__ import annotations

import json
from pathlib import Path

from .cli_utils import console


def _read_if_exists(path: Path, max_lines: int = 0) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if max_lines:
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[-max_lines:])
    return text


def _extract_recent_tasks(task_log: str, count: int = 10) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in task_log.splitlines():
        if line.startswith("## ") and current:
            blocks.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks[-count:] if blocks else []


def _build_snapshot(target: Path) -> dict[str, object]:
    pj_path = target / ".agent-harness" / "project.json"
    project = json.loads(pj_path.read_text(encoding="utf-8")) if pj_path.exists() else {}

    task_log_text = _read_if_exists(target / ".agent-harness" / "task-log.md")
    recent_tasks = _extract_recent_tasks(task_log_text)

    lessons_text = _read_if_exists(target / ".agent-harness" / "lessons.md")
    current_task = _read_if_exists(target / ".agent-harness" / "current-task.md")
    has_active_task = bool(current_task.strip()) and any(
        l.strip() and not l.startswith("#") and not l.startswith("<!--")
        for l in current_task.splitlines()
    )

    return {
        "project": project,
        "recent_tasks": recent_tasks,
        "lessons": lessons_text,
        "active_task": current_task.strip() if has_active_task else None,
        "task_count": len(_extract_recent_tasks(task_log_text, count=9999)),
    }


def _render_markdown(snapshot: dict[str, object]) -> str:
    lines = ["# 项目画像\n"]
    p = snapshot["project"]
    if p:
        lines.append(f"- 项目：{p.get('project_name', '未知')}")
        lines.append(f"- 类型：{p.get('project_type', '未知')}")
        lines.append(f"- 语言：{p.get('language', '未知')}")
        lines.append(f"- 目标：{p.get('project_summary', '未知')}")
        lines.append("")

    if snapshot["active_task"]:
        lines.append("## 当前进行中任务\n")
        lines.append(snapshot["active_task"])
        lines.append("")

    lines.append(f"## 历史任务（共 {snapshot['task_count']} 条，显示最近 {len(snapshot['recent_tasks'])} 条）\n")
    for t in snapshot["recent_tasks"]:
        lines.append(t)
        lines.append("")

    if snapshot["lessons"].strip():
        lines.append("## 踩坑教训\n")
        lines.append(snapshot["lessons"].strip())
        lines.append("")

    return "\n".join(lines)


def run_export(target: Path, *, output: str | None = None, as_json: bool = False) -> None:
    target = target.resolve()
    snapshot = _build_snapshot(target)

    if as_json:
        text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    else:
        text = _render_markdown(snapshot)

    if output:
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"[green]已导出到[/green] {output}")
    else:
        console.print(text)
