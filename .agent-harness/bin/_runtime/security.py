"""统一的输入安全校验函数。

将项目中分散的校验规则（agent id 正则、路径遍历检查、内容长度限制）
代码化为可复用的函数，让 `.claude/rules/safety.md` 的约束从"说说而已"
变为"代码强制"。

三个函数的设计姿态：
- sanitize_name   : 严格匹配（失败即抛）。用于 agent id、squad worker 名等标识符。
- sanitize_path   : 严格匹配（失败即抛）。防止路径遍历和符号链接逃逸。
- sanitize_content: 混合 — oversize 抛异常（显式告警），null/控制字符静默剥除。

SecurityError 继承 ValueError，保持与现有 except ValueError 代码的向后兼容。
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "SecurityError",
    "sanitize_name",
    "sanitize_path",
    "sanitize_content",
    "NAME_PATTERN",
    "DEFAULT_MAX_CONTENT_LEN",
]

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")
DEFAULT_MAX_CONTENT_LEN = 100_000

# 允许保留的控制字符：换行、制表符、回车。其他 C0 和 DEL 一律剥除。
_ALLOWED_CTRL = {"\n", "\t", "\r"}


class SecurityError(ValueError):
    """输入校验失败。继承 ValueError 保持向后兼容。"""


def sanitize_name(name: object) -> str:
    """校验标识符名称：长度 1-31、`[a-z0-9-]`、不以 `-` 开头。

    用于 agent id、squad worker 名等面向文件系统的短标识符。
    匹配失败或类型不对时抛 SecurityError。
    """
    if not isinstance(name, str):
        raise SecurityError(
            f"name must be str, got {type(name).__name__}"
        )
    if "\x00" in name:
        raise SecurityError("name contains null byte")
    if not NAME_PATTERN.match(name):
        raise SecurityError(
            f"invalid name {name!r}: must match {NAME_PATTERN.pattern}"
        )
    return name


def sanitize_path(path: object, base_dir: object) -> Path:
    """解析 path 相对 base_dir，确保结果不逃逸 base_dir。

    同时防御路径遍历（`..`）、绝对路径覆盖和符号链接逃逸。
    `base_dir` 必须已存在（用于 resolve 符号链接）；`path` 不需要存在。
    返回 resolved 后的绝对路径。
    """
    if not isinstance(path, (str, Path)):
        raise SecurityError(
            f"path must be str or Path, got {type(path).__name__}"
        )
    if not isinstance(base_dir, (str, Path)):
        raise SecurityError(
            f"base_dir must be str or Path, got {type(base_dir).__name__}"
        )

    path_str = str(path)
    if "\x00" in path_str:
        raise SecurityError("path contains null byte")

    base = Path(base_dir).resolve()
    # strict=False: 允许 path 尚不存在；符号链接仍会被 resolve 跟随
    resolved = (base / path_str).resolve()

    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise SecurityError(
            f"path traversal detected: {path_str!r} escapes {base}"
        ) from exc
    return resolved


def sanitize_content(
    content: object, max_len: int = DEFAULT_MAX_CONTENT_LEN
) -> str:
    """清洗任意来源的字符串内容。

    - 类型非 str → 抛
    - 长度 > max_len → 抛（静默截断会掩盖异常规模）
    - null 字节和非 `\\n\\t\\r` 的 C0/DEL 控制字符 → 剥除（已知无害噪音）
    """
    if not isinstance(content, str):
        raise SecurityError(
            f"content must be str, got {type(content).__name__}"
        )
    if len(content) > max_len:
        raise SecurityError(
            f"content length {len(content)} exceeds max_len {max_len}"
        )
    return "".join(
        ch
        for ch in content
        if ch in _ALLOWED_CTRL or not _is_control(ch)
    )


def _is_control(ch: str) -> bool:
    """C0 (U+0000..U+001F) 或 DEL (U+007F)。"""
    code = ord(ch)
    return code < 0x20 or code == 0x7F
