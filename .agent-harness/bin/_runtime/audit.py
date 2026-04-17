"""Change-audit log (WAL) for .agent-harness/ key files.

Append-only JSONL log at `.agent-harness/audit.jsonl` recording every
write to current-task.md, task-log.md, and lessons.md. Purpose:
- Trace who changed what and when (multi-agent scenarios)
- Detect concurrent writes before they conflict
- Support future rollback mechanics

Minimal implementation: library function + CLI subcommands. Agents are
expected to call `append_audit()` via `harness audit append` after
editing a tracked file. Not enforced by hooks — framework is a scaffold,
not a runtime.

Absorbed from MemPalace's `mcp_server.py` WAL (github.com/milla-jovovich/mempalace).
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl as _fcntl
    _HAS_FCNTL = True
except ImportError:  # Windows native (non-WSL)
    _fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


TRACKED_FILES = ("current-task.md", "task-log.md", "lessons.md")
VALID_OPS = ("create", "update", "append", "delete")
DEFAULT_AGENT = "unknown"


@dataclass
class AuditEntry:
    ts: str
    file: str
    op: str
    agent: str
    summary: str

    def to_json(self) -> str:
        return json.dumps(
            {"ts": self.ts, "file": self.file, "op": self.op, "agent": self.agent, "summary": self.summary},
            ensure_ascii=False,
        )


def audit_path(project_root: Path) -> Path:
    return project_root / ".agent-harness" / "audit.jsonl"


def _require_fcntl() -> None:
    if not _HAS_FCNTL:
        raise OSError(
            "audit 需要 fcntl（Unix / macOS / WSL）。"
            "Windows 原生环境不支持文件锁，请在 WSL 下运行。"
        )


def _agent_identity() -> str:
    """Read agent identity from HARNESS_AGENT env var, fall back to DEFAULT_AGENT."""
    return os.environ.get("HARNESS_AGENT", DEFAULT_AGENT) or DEFAULT_AGENT


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate(file: str, op: str) -> None:
    if file not in TRACKED_FILES:
        raise ValueError(
            f"audit 只追踪 {TRACKED_FILES}，收到：{file!r}"
        )
    if op not in VALID_OPS:
        raise ValueError(
            f"op 必须是 {VALID_OPS} 之一，收到：{op!r}"
        )


@contextlib.contextmanager
def _locked_append(path: Path) -> Iterator[Any]:
    """Exclusive lock + O_APPEND. Safe under concurrent writes.

    Follows 2026-04-12 lesson "文件锁顺序必须先锁再 truncate" — here we
    don't truncate (append-only), but keep the lock-first discipline.
    """
    _require_fcntl()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
        with os.fdopen(fd, "a", encoding="utf-8", closefd=False) as f:
            yield f
            f.flush()
            os.fsync(fd)
    finally:
        try:
            _fcntl.flock(fd, _fcntl.LOCK_UN)
        finally:
            os.close(fd)


def append_audit(
    project_root: Path,
    file: str,
    op: str,
    summary: str,
    *,
    agent: str | None = None,
    ts: str | None = None,
) -> AuditEntry:
    """Append one JSONL record to .agent-harness/audit.jsonl.

    Args:
        project_root: Target project containing `.agent-harness/`.
        file: Tracked filename (see TRACKED_FILES).
        op: Operation type (see VALID_OPS).
        summary: One-line human-readable description.
        agent: Override agent identity (default: HARNESS_AGENT env or "unknown").
        ts: Override timestamp (default: now, ISO 8601 UTC).

    Returns:
        The AuditEntry that was written.
    """
    _validate(file, op)
    entry = AuditEntry(
        ts=ts or _now_iso(),
        file=file,
        op=op,
        agent=agent or _agent_identity(),
        summary=summary,
    )
    with _locked_append(audit_path(project_root)) as f:
        f.write(entry.to_json() + "\n")
    return entry


def read_all(project_root: Path) -> list[AuditEntry]:
    """Parse every JSONL line into AuditEntry. Skips malformed lines silently
    (audit log is advisory, not authoritative — tolerate partial corruption)."""
    path = audit_path(project_root)
    if not path.is_file():
        return []
    entries: list[AuditEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            entries.append(AuditEntry(
                ts=str(data.get("ts", "")),
                file=str(data.get("file", "")),
                op=str(data.get("op", "")),
                agent=str(data.get("agent", "")),
                summary=str(data.get("summary", "")),
            ))
        except (json.JSONDecodeError, TypeError):
            continue
    return entries


def tail(project_root: Path, limit: int = 20) -> list[AuditEntry]:
    """Return the most recent `limit` entries (newest first)."""
    entries = read_all(project_root)
    if limit <= 0:
        return []
    return list(reversed(entries[-limit:]))


def stats(project_root: Path) -> dict[str, Any]:
    """Aggregate counts by file, op, and agent."""
    entries = read_all(project_root)
    by_file = Counter(e.file for e in entries)
    by_op = Counter(e.op for e in entries)
    by_agent = Counter(e.agent for e in entries)
    first = entries[0].ts if entries else None
    last = entries[-1].ts if entries else None
    return {
        "total": len(entries),
        "by_file": dict(by_file),
        "by_op": dict(by_op),
        "by_agent": dict(by_agent),
        "first_ts": first,
        "last_ts": last,
    }


def truncate_before(project_root: Path, cutoff_iso: str) -> int:
    """Remove entries with ts < cutoff_iso (lexicographic compare works for ISO 8601).

    Returns the number of entries removed. Atomic via tempfile + rename.
    """
    path = audit_path(project_root)
    if not path.is_file():
        return 0
    entries = read_all(project_root)
    kept = [e for e in entries if e.ts >= cutoff_iso]
    removed = len(entries) - len(kept)
    if removed == 0:
        return 0
    # Atomic rewrite under lock: truncate + rewrite full content.
    _require_fcntl()
    tmp = path.with_suffix(".jsonl.tmp")
    with _locked_append(path):
        # Hold parent-level lock on path; tmp write can proceed safely.
        tmp.write_text(
            "\n".join(e.to_json() for e in kept) + ("\n" if kept else ""),
            encoding="utf-8",
        )
        os.replace(tmp, path)
    return removed


def init_audit(project_root: Path) -> AuditEntry | None:
    """Create audit.jsonl with a bootstrap entry if it doesn't exist.

    Idempotent — if file already exists, returns None without writing.
    """
    if audit_path(project_root).is_file():
        return None
    return append_audit(
        project_root,
        file="current-task.md",
        op="create",
        summary="audit log initialized",
        agent="harness-init",
    )


def append_from_args(
    project_root: Path, file: str, op: str, summary: str, agent: str | None = None
) -> AuditEntry:
    """CLI-facing wrapper with explicit param order — keeps argparse handler small."""
    return append_audit(project_root, file, op, summary, agent=agent)


def format_entry(entry: AuditEntry) -> str:
    """Human-readable one-line format for CLI output."""
    return f"{entry.ts}  {entry.file:<18}  {entry.op:<7}  [{entry.agent}]  {entry.summary}"


def _parse_iso_lenient(value: str) -> str:
    """Accept both `YYYY-MM-DD` and full `YYYY-MM-DDTHH:MM:SSZ`; normalize to full form."""
    if "T" not in value:
        return f"{value}T00:00:00Z"
    return value


def touch_if_missing(project_root: Path) -> Path:
    """Ensure .agent-harness/audit.jsonl exists (empty file is valid)."""
    path = audit_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


# Public API surface
__all__ = [
    "TRACKED_FILES", "VALID_OPS", "DEFAULT_AGENT",
    "AuditEntry", "audit_path",
    "append_audit", "read_all", "tail", "stats", "truncate_before",
    "init_audit", "append_from_args", "format_entry",
    "touch_if_missing",
]


# Time injection for tests (monkeypatched if needed)
_time = time
