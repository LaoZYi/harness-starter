"""Layered memory index maintenance.

Provides `rebuild_index()` which scans `.agent-harness/lessons.md` and
`task-log.md` to (re)generate `.agent-harness/memory-index.md`.

The index is the L1 hot-knowledge layer read by the task-lifecycle rule
on every new task. Keeping it in sync with the full-history files is
the /compound skill's responsibility; this module provides a
deterministic rebuild path for bootstrap and recovery scenarios.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ._shared import require_harness

MAX_LESSONS = 10
MAX_TASKS = 5

_HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")


@dataclass
class RebuildResult:
    status: str  # "created" | "rewritten" | "refused"
    lessons_count: int
    tasks_count: int
    message: str
    path: Path


def _extract_headings(source: Path, limit: int) -> list[str]:
    """Return the last `limit` `##` headings from a markdown file.

    Missing or empty files yield an empty list. Headings are returned
    in the order they appear in the source (oldest→newest), then
    truncated to the most recent `limit` entries.
    """
    if not source.exists():
        return []
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        return []
    headings: list[str] = []
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            headings.append(m.group("title").strip())
    if limit <= 0:
        return []
    return headings[-limit:]


def _render_index(lessons: list[str], tasks: list[str]) -> str:
    """Render memory-index.md content from recent lesson/task titles.

    Lists are rendered newest-first for readability.
    """
    lessons_block = (
        "\n".join(f"- {title}" for title in reversed(lessons))
        if lessons
        else "（暂无。完成任务并运行 `/compound` 后会自动填充。）"
    )
    tasks_block = (
        "\n".join(f"- {title}" for title in reversed(tasks))
        if tasks
        else "（暂无。归档第一个任务后会自动填充。）"
    )

    return (
        "# Memory Index\n\n"
        "> 热知识精华索引。详情见 `.agent-harness/lessons.md` 和 "
        "`.agent-harness/task-log.md`。\n"
        ">\n"
        "> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` "
        "技能或直接 `grep` 完整文件。\n\n"
        f"## 最近教训（保留最多 {MAX_LESSONS} 条）\n\n"
        "<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->\n\n"
        f"{lessons_block}\n\n"
        f"## 最近任务（保留最多 {MAX_TASKS} 条）\n\n"
        "<!-- 任务归档时顶部插入；超过上限时挤出最老。-->\n\n"
        f"{tasks_block}\n\n"
        "## 主题索引（可选，按关键词定位历史）\n\n"
        "<!-- 人工或 AI 周期性整理。格式：`- 关键词 → lessons.md \"条目标题\"` -->\n\n"
        "（尚未建立。当 lessons.md 条目较多时可整理此段方便定位。）\n\n"
        "---\n\n"
        "## 使用说明\n\n"
        "- **task-lifecycle 规则**指示 AI 在开始新任务时默认读取本文件（而非 "
        "lessons.md / task-log.md 全量），避免上下文膨胀。\n"
        "- 索引命中某话题 → 用 `/recall <关键词>` 技能或 `grep` 读取对应节。\n"
        "- 索引由 `/compound` 技能维护；也可运行 "
        "`harness memory rebuild .` 从现有 lessons/task-log 重建一次。\n"
    )


def rebuild_index(
    target_path: Path,
    *,
    force: bool = False,
) -> RebuildResult:
    """Regenerate `.agent-harness/memory-index.md` from lessons/task-log.

    Args:
        target_path: Root of a harness-initialized project.
        force: If True, overwrite an existing memory-index.md; otherwise
            the function refuses and returns `status="refused"`.

    Returns:
        RebuildResult describing the outcome.
    """
    require_harness(target_path)
    harness_dir = target_path / ".agent-harness"
    index_path = harness_dir / "memory-index.md"
    lessons_path = harness_dir / "lessons.md"
    tasks_path = harness_dir / "task-log.md"

    already_exists = index_path.exists()
    if already_exists and not force:
        return RebuildResult(
            status="refused",
            lessons_count=0,
            tasks_count=0,
            message=(
                f"memory-index.md 已存在：{index_path}\n"
                "加 --force 覆盖；否则先用 /compound 逐步维护索引。"
            ),
            path=index_path,
        )

    lessons = _extract_headings(lessons_path, MAX_LESSONS)
    tasks = _extract_headings(tasks_path, MAX_TASKS)
    content = _render_index(lessons, tasks)

    harness_dir.mkdir(parents=True, exist_ok=True)
    index_path.write_text(content, encoding="utf-8")

    status = "rewritten" if already_exists else "created"
    return RebuildResult(
        status=status,
        lessons_count=len(lessons),
        tasks_count=len(tasks),
        message=(
            f"已{('重建' if already_exists else '创建')} "
            f"{index_path}（{len(lessons)} 条教训，{len(tasks)} 条任务）"
        ),
        path=index_path,
    )
