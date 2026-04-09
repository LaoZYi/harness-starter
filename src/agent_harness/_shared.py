"""Shared constants, utilities, and guards used across the package."""
from __future__ import annotations

import re
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
TEMPLATE_ROOT = PKG_DIR / "templates" / "common"
SUPERPOWERS_ROOT = PKG_DIR / "templates" / "superpowers"
META_ROOT = PKG_DIR / "templates" / "meta"
PRESET_ROOT = PKG_DIR / "presets"
FRAMEWORK_VERSION = (PKG_DIR / "VERSION").read_text(encoding="utf-8").strip()

if not TEMPLATE_ROOT.is_dir():
    raise RuntimeError(
        f"Template directory not found: {TEMPLATE_ROOT}\n"
        "This usually means the package was installed without data files. "
        "Reinstall with: pip install -e ."
    )

PLACEHOLDER_RE = re.compile(r"\{\{\s*[a-z0-9_]+\s*\}\}")


def slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug (canonical implementation)."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "project"


def require_harness(target: Path) -> None:
    """Raise SystemExit if target hasn't been initialized with harness."""
    if not (target / ".agent-harness").is_dir() and not (target / "AGENTS.md").exists():
        raise SystemExit(f"错误：{target} 尚未初始化 harness。请先运行 harness init {target}")


def shell_escape_single(value: str) -> str:
    """Escape value for safe embedding inside single-quoted shell strings."""
    return value.replace("'", "'\\''")
