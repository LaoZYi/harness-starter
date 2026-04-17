"""Agent diary + status — isolation for parallel sub-agents.

Each sub-agent gets its own `.agent-harness/agents/<id>/` directory with:
- `diary.md`: append-only process log (what I'm doing)
- `status.md`: single-state snapshot (what I'm currently doing)

Complements Issue #12's audit.jsonl (which tracks *what files changed*)
with *what each agent is thinking*. Meant for `/dispatch-agents` and
`/subagent-dev` scenarios. `/squad` has its own `squad/<task>/workers/<name>/`
isolation and does NOT use this module.

Absorbed from MemPalace (github.com/milla-jovovich/mempalace) — Issue #14.
"""
from __future__ import annotations

import contextlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .security import NAME_PATTERN, SecurityError, sanitize_name

try:
    import fcntl as _fcntl
    _HAS_FCNTL = True
except ImportError:  # Windows native (non-WSL)
    _fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


class AgentError(ValueError):
    """Raised for invalid agent id or missing agent."""


def _require_fcntl() -> None:
    if not _HAS_FCNTL:
        raise OSError(
            "agent diary 需要 fcntl（Unix / macOS / WSL）。"
            "Windows 原生环境不支持文件锁，请在 WSL 下运行。"
        )


def _validate_id(agent_id: str) -> None:
    try:
        sanitize_name(agent_id)
    except SecurityError as exc:
        raise AgentError(
            f"agent id 不合法（仅允许小写字母/数字/连字符，长度 1-31）：{agent_id!r}"
        ) from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def agents_root(project_root: Path) -> Path:
    return project_root / ".agent-harness" / "agents"


def agent_dir(project_root: Path, agent_id: str) -> Path:
    _validate_id(agent_id)
    return agents_root(project_root) / agent_id


@dataclass
class AgentRecord:
    id: str
    last_activity: str  # ISO 8601, empty if never active
    status: str         # one line or empty
    diary_lines: int


@contextlib.contextmanager
def _locked_append(path: Path, header: str | None = None) -> Iterator[Any]:
    """Append-only write protected by fcntl flock.

    If `header` is given, it's written **inside the lock** when the file is
    empty (first writer wins; subsequent writers see non-zero size and skip).
    This avoids the init_agent check-then-write race that could lose lines
    under concurrent diary_append calls.
    """
    _require_fcntl()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
        if header is not None and os.fstat(fd).st_size == 0:
            os.write(fd, header.encode("utf-8"))
        with os.fdopen(fd, "a", encoding="utf-8", closefd=False) as f:
            yield f
            f.flush()
            os.fsync(fd)
    finally:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN)
        finally:
            os.close(fd)


@contextlib.contextmanager
def _locked_write(path: Path) -> Iterator[Any]:
    """Lock first, then truncate — sequence matters (lessons 2026-04-12)."""
    _require_fcntl()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        with os.fdopen(fd, "w", encoding="utf-8", closefd=False) as f:
            yield f
            f.flush()
            os.fsync(fd)
    finally:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN)
        finally:
            os.close(fd)


def init_agent(project_root: Path, agent_id: str) -> Path:
    """Idempotent: create `.agent-harness/agents/<id>/{diary.md, status.md}`.

    Both diary.md creation and header-writing go through `_locked_append`
    (guarded by fcntl) so concurrent init_agent + diary_append calls can't
    produce a check-then-write race where one writer's header truncates
    another's already-appended line.
    """
    d = agent_dir(project_root, agent_id)
    d.mkdir(parents=True, exist_ok=True)
    status = d / "status.md"
    if not status.exists():
        status.write_text("", encoding="utf-8")
    # Atomically ensure diary.md exists with a header. _locked_append writes
    # the header inside the lock only when st_size == 0, so first caller wins.
    header = f"# Agent Diary — {agent_id}\n\n"
    with _locked_append(d / "diary.md", header=header):
        pass
    return d


def diary_append(project_root: Path, agent_id: str, message: str, *, ts: str | None = None) -> str:
    """Append one timestamped line to the agent's diary.md. Creates agent dir if needed."""
    _validate_id(agent_id)
    if not message or not isinstance(message, str):
        raise AgentError("diary 消息不能为空")
    init_agent(project_root, agent_id)  # idempotent
    line = f"- {ts or _now_iso()}  {message}\n"
    header = f"# Agent Diary — {agent_id}\n\n"
    with _locked_append(agent_dir(project_root, agent_id) / "diary.md", header=header) as f:
        f.write(line)
    return line


def status_set(project_root: Path, agent_id: str, state: str) -> None:
    """Overwrite the agent's status.md with a single-line state (timestamped)."""
    _validate_id(agent_id)
    if not isinstance(state, str):
        raise AgentError("status 必须是字符串")
    init_agent(project_root, agent_id)
    body = f"{_now_iso()}\n{state.strip()}\n"
    with _locked_write(agent_dir(project_root, agent_id) / "status.md") as f:
        f.write(body)


def status_read(project_root: Path, agent_id: str) -> tuple[str, str]:
    """Return (ts, state) or ('', '') if never set."""
    path = agent_dir(project_root, agent_id) / "status.md"
    if not path.is_file():
        return ("", "")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return ("", "")
    lines = text.splitlines()
    if len(lines) < 2:
        # Single line — treat as state without timestamp
        return ("", lines[0])
    return (lines[0], "\n".join(lines[1:]))


def diary_read(project_root: Path, agent_id: str) -> str:
    path = agent_dir(project_root, agent_id) / "diary.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def list_agents(project_root: Path) -> list[AgentRecord]:
    """List agents sorted by most-recent activity (diary mtime, desc)."""
    root = agents_root(project_root)
    if not root.is_dir():
        return []
    records: list[AgentRecord] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or not NAME_PATTERN.match(d.name):
            continue
        diary = d / "diary.md"
        status_ts, status_state = status_read(project_root, d.name)
        if diary.is_file():
            mtime = datetime.fromtimestamp(diary.stat().st_mtime, tz=timezone.utc)
            last_act = mtime.strftime("%Y-%m-%dT%H:%M:%SZ")
            lines = sum(1 for ln in diary.read_text(encoding="utf-8").splitlines() if ln.strip().startswith("- "))
        else:
            last_act = ""
            lines = 0
        records.append(AgentRecord(
            id=d.name, last_activity=last_act, status=status_state, diary_lines=lines
        ))
    records.sort(key=lambda r: r.last_activity, reverse=True)
    return records


def aggregate(project_root: Path, agent_ids: list[str] | None = None) -> str:
    """Return a markdown digest of the given agents' diaries (or all if None).

    Designed for the main agent to read before merging sub-agent output back
    into task-log.md. Does NOT write anywhere — read-only aggregation.
    """
    records = list_agents(project_root)
    if agent_ids:
        for aid in agent_ids:
            _validate_id(aid)
        records = [r for r in records if r.id in agent_ids]
    if not records:
        return "_（当前没有活跃 agent）_\n"
    parts: list[str] = ["# Agent Diary Aggregate\n"]

    # 顶部展示所有 artifacts（知识制品，Issue #30）
    from . import agent_artifacts
    art_section = agent_artifacts.render_artifacts_section(
        project_root, [r.id for r in records]
    )
    if art_section:
        parts.append(art_section)

    for r in records:
        parts.append(f"\n## {r.id}")
        if r.status:
            parts.append(f"\n**当前状态**（{r.last_activity}）：{r.status}\n")
        else:
            parts.append(f"\n**最近活动**：{r.last_activity or '无'}\n")
        body = diary_read(project_root, r.id).strip()
        if body:
            parts.append(body + "\n")
        else:
            parts.append("_（diary 为空）_\n")
    return "\n".join(parts)


def diary_append_artifact(*args, **kwargs):
    """Thin shim to agent_artifacts.diary_append_artifact（向后兼容）。"""
    from . import agent_artifacts
    return agent_artifacts.diary_append_artifact(*args, **kwargs)


def extract_artifacts(*args, **kwargs):
    """Thin shim to agent_artifacts.extract_artifacts（向后兼容）。"""
    from . import agent_artifacts
    return agent_artifacts.extract_artifacts(*args, **kwargs)


__all__ = [
    "AgentError", "AgentRecord",
    "agents_root", "agent_dir",
    "init_agent", "diary_append", "status_set", "status_read",
    "diary_read", "list_agents", "aggregate",
    "diary_append_artifact", "extract_artifacts",
]

_time = time  # tests may monkey-patch
