"""Shared state files for squad: manifest + status JSONL, with file locks."""
from __future__ import annotations

import contextlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl as _fcntl
    _HAS_FCNTL = True
except ImportError:  # Windows native (non-WSL)
    _fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


def _require_fcntl() -> None:
    if not _HAS_FCNTL:
        raise OSError(
            "squad 需要 fcntl（Unix / macOS / WSL）。"
            "Windows 原生环境不支持文件锁，请在 WSL 下运行。"
        )


@dataclass
class WorkerRecord:
    name: str
    capability: str
    worktree: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Manifest:
    task_id: str
    base_branch: str
    tmux_session: str
    created_at: float
    workers: list[WorkerRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "base_branch": self.base_branch,
            "tmux_session": self.tmux_session,
            "created_at": self.created_at,
            "workers": [asdict(w) for w in self.workers],
        }


def squad_dir(project_root: Path, task_id: str) -> Path:
    return project_root / ".agent-harness" / "squad" / task_id


def write_manifest(root: Path, manifest: Manifest) -> Path:
    d = squad_dir(root, manifest.task_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "manifest.json"
    with _locked_write(path) as f:
        json.dump(manifest.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def read_manifest(root: Path, task_id: str) -> Manifest | None:
    path = squad_dir(root, task_id) / "manifest.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        task_id=data["task_id"],
        base_branch=data["base_branch"],
        tmux_session=data["tmux_session"],
        created_at=data["created_at"],
        workers=[WorkerRecord(**w) for w in data["workers"]],
    )


def list_active_squads(root: Path) -> list[str]:
    base = root / ".agent-harness" / "squad"
    if not base.is_dir():
        return []
    return sorted(
        p.name for p in base.iterdir()
        if p.is_dir() and (p / "manifest.json").is_file()
    )


def append_status(root: Path, task_id: str, record: dict[str, Any]) -> None:
    d = squad_dir(root, task_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "status.jsonl"
    record = {"ts": time.time(), **record}
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _locked_append(path) as f:
        f.write(line)


def read_status_tail(root: Path, task_id: str, limit: int = 50) -> list[dict[str, Any]]:
    path = squad_dir(root, task_id) / "status.jsonl"
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines if line.strip()]


@contextlib.contextmanager
def _locked_write(path: Path) -> Iterator[Any]:
    """Exclusive lock first, truncate second — avoids empty-file race if a
    concurrent writer sees the file mid-operation.
    """
    _require_fcntl()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)  # type: ignore[union-attr]
        # Safe to truncate: exclusive lock held.
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        with os.fdopen(fd, "w", encoding="utf-8", closefd=False) as f:
            yield f
            f.flush()
            os.fsync(fd)
    finally:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN)  # type: ignore[union-attr]
        finally:
            os.close(fd)


@contextlib.contextmanager
def _locked_append(path: Path) -> Iterator[Any]:
    _require_fcntl()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)  # type: ignore[union-attr]
        with os.fdopen(fd, "a", encoding="utf-8", closefd=False) as f:
            yield f
            f.flush()
            os.fsync(fd)
    finally:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN)  # type: ignore[union-attr]
        finally:
            os.close(fd)
