"""SQLite mailbox (WAL 模式) — Issue #21 阶段 2.cd 的数据层。

职责：
- 事件存储：squad 中所有 worker 状态变更事件（pending / spawned / spawn_failed / done /
  info / error）追加到 `.agent-harness/squad/<task_id>/mailbox.db`
- 并发安全：WAL 模式下允许多 connection 并发读写（一个 cli 子命令 + 一个常驻 watch 进程
  同时访问同一 db 不打架）
- 查询支持：done_workers / pending_worker_info 从 SQL 推导（替代原 JSONL 全扫）

设计决策：
- **只存事件流，不存状态**：符合 lessons.md "三源对账推导状态而非持久化 worker 状态"
- **预留扩展 type 字段**：当前 6 类（4 类 19a 事件 + info/error），schema 支持任何字符串
- **保留 JSONL dump**：`cmd_dump` 命令把 mailbox 导出为可读 JSONL（调试用）
- **per-call connection**：不维护长连接，每次调用开关一次，避免 Python GIL + 跨线程坑

WAL 副文件 `.db-wal` / `.db-shm` 由 SQLite 自动管理，需在 .gitignore 排除。
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL NOT NULL,
    worker      TEXT,               -- null for squad-level events
    event_type  TEXT NOT NULL,      -- pending / spawned / spawn_failed / done / info / error / ... (可扩展)
    message     TEXT NOT NULL DEFAULT '',
    payload     TEXT NOT NULL DEFAULT '{}'  -- JSON blob for future structured fields
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_worker ON events(worker);
"""

# 阶段 2 实际在用的事件类型。其他类型（dispatch / broadcast / ...）等实际 producer 出现时按需加。
KNOWN_TYPES = frozenset({
    "pending", "spawned", "spawn_failed", "done", "info", "error",
    "squad_stopped", "worker_stopped",
    "dry-run-rendered",  # 19a dry-run 路径的事件
    "session_lost", "worker_crashed",  # Issue #22 watchdog
    "watch_exited",  # cmd_watch 退出标记（已在用，补登记）
})


class MailboxError(RuntimeError):
    """Raised for mailbox schema / connection failures."""


def db_path(squad_dir: Path) -> Path:
    """Canonical mailbox db location inside a squad directory."""
    return squad_dir / "mailbox.db"


def _connect(path: Path) -> sqlite3.Connection:
    """Open a WAL-mode connection. Caller closes.

    WAL 模式在每个新 db 上只需设置一次（PRAGMA 是持久化的），但重复设置幂等且便宜。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")  # WAL 下 NORMAL 已足够安全，比 FULL 快
    conn.executescript(_SCHEMA)
    return conn


def append_event(
    squad_dir: Path,
    event_type: str,
    worker: str | None = None,
    message: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    """追加一条事件。幂等——重复调用 append 不同事件是正常的（事件流）。"""
    if not isinstance(event_type, str) or not event_type:
        raise MailboxError(f"event_type must be non-empty str, got {event_type!r}")
    conn = _connect(db_path(squad_dir))
    try:
        conn.execute(
            "INSERT INTO events (ts, worker, event_type, message, payload) VALUES (?, ?, ?, ?, ?)",
            (time.time(), worker, event_type, message,
             json.dumps(payload or {}, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()


def read_events(
    squad_dir: Path,
    event_type: str | None = None,
    worker: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """读事件。可按 type 和/或 worker 过滤。返回按 id 升序（即时间顺序）。"""
    path = db_path(squad_dir)
    if not path.is_file():
        return []
    conn = _connect(path)
    try:
        sql = "SELECT id, ts, worker, event_type, message, payload FROM events"
        clauses: list[str] = []
        params: list[Any] = []
        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type)
        if worker is not None:
            clauses.append("worker = ?")
            params.append(worker)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    payload = json.loads(row["payload"] or "{}")
    return {
        "id": row["id"],
        "ts": row["ts"],
        "worker": row["worker"],
        "event": row["event_type"],   # 对外统一叫 event 保持与 JSONL 兼容
        "message": row["message"],
        **({"payload": payload} if payload else {}),
    }


def done_workers(squad_dir: Path) -> set[str]:
    """Set of worker names that have at least one `done` event."""
    path = db_path(squad_dir)
    if not path.is_file():
        return set()
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT worker FROM events WHERE event_type = 'done' AND worker IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    return {r["worker"] for r in rows}


def pending_worker_info(squad_dir: Path) -> dict[str, float]:
    """Map worker name → earliest `pending` ts，for workers still blocked (no subsequent `spawned`)."""
    path = db_path(squad_dir)
    if not path.is_file():
        return {}
    conn = _connect(path)
    try:
        # 每个 worker 的最早 pending ts
        pending_rows = conn.execute(
            "SELECT worker, MIN(ts) AS first_ts FROM events "
            "WHERE event_type = 'pending' AND worker IS NOT NULL "
            "GROUP BY worker"
        ).fetchall()
        # 已 spawned 的 worker 集合
        spawned_rows = conn.execute(
            "SELECT DISTINCT worker FROM events "
            "WHERE event_type = 'spawned' AND worker IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    spawned = {r["worker"] for r in spawned_rows}
    return {
        r["worker"]: r["first_ts"]
        for r in pending_rows
        if r["worker"] not in spawned
    }


def dump_to_jsonl(squad_dir: Path) -> Iterable[str]:
    """Yield JSONL lines for all events — for `harness squad dump` debugging."""
    for evt in read_events(squad_dir):
        yield json.dumps(evt, ensure_ascii=False)
