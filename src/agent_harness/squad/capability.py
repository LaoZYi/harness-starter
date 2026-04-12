"""Render Claude Code settings.local.json per squad capability.

三种 capability 的权限模型：
- scout:    只读探索 — 禁 Write/Edit/NotebookEdit
- builder:  读写实现 — 禁危险 Bash（git push / rm -rf / 远端操作）
- reviewer: 只读审查 — 同 scout 禁写
"""
from __future__ import annotations

from typing import Any


class CapabilityError(ValueError):
    """Raised when an unknown capability is requested."""


# Common deny list for read-only roles (scout / reviewer)
_READONLY_WRITE_DENY = ["Write", "Edit", "NotebookEdit"]

# Bash patterns considered destructive or out-of-scope for all capabilities
_COMMON_BASH_DENY = [
    "Bash(git push:*)",
    "Bash(git push --force:*)",
    "Bash(rm -rf:*)",
    "Bash(rm -rf /:*)",
    "Bash(sudo:*)",
]


def render_settings(capability: str) -> dict[str, Any]:
    """Return a settings.local.json dict for the given capability."""
    if capability == "scout":
        return {
            "permissions": {
                "deny": list(_READONLY_WRITE_DENY)
                + [
                    "Bash(git:*)",
                    "Bash(curl:*)",
                ]
                + _COMMON_BASH_DENY,
            }
        }
    if capability == "builder":
        return {
            "permissions": {
                "deny": list(_COMMON_BASH_DENY)
                + [
                    "Bash(git remote:*)",
                    "Bash(git reset --hard:*)",
                ],
            }
        }
    if capability == "reviewer":
        return {
            "permissions": {
                "deny": list(_READONLY_WRITE_DENY)
                + [
                    "Bash(git commit:*)",
                    "Bash(git:*)",
                ]
                + _COMMON_BASH_DENY,
            }
        }
    raise CapabilityError(f"未知 capability：{capability!r}（仅支持 scout/builder/reviewer）")
