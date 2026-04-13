"""Embedded runtime _shared — only utilities audit/memory need (no framework deps)."""
from pathlib import Path


def require_harness(target: Path) -> None:
    """Raise SystemExit if target hasn't been initialized with harness."""
    if not (target / ".agent-harness").is_dir() and not (target / "AGENTS.md").exists():
        raise SystemExit(
            f"错误：{target} 尚未初始化 harness。请先运行 harness init {target}"
        )
