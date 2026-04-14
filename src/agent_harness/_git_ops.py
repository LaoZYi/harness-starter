"""Shared git operation helpers with friendly error handling.

Why separate module: `harness init` 会尝试帮用户创建首个 commit，但若用户机器没
配 git user.email/user.name，原先的 `subprocess.run(..., check=True)` 会直接
抛 CalledProcessError（实际 stderr 是英文 "Please tell me who you are"），
新手看了一脸懵。这里集中处理"预检 + 友好降级"。

保持最小依赖（只用 stdlib subprocess），避免耦合 CLI 交互层。
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def git_identity_configured(target: Path) -> bool:
    """Return True iff both user.email and user.name are readable.

    Uses `git config --get` which consults the full precedence chain
    (local → global → system → defaults). Works regardless of whether the
    identity is set locally in `target` or globally for the current user.
    """
    for key in ("user.email", "user.name"):
        result = subprocess.run(
            ["git", "-C", str(target), "config", "--get", key],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return False
    return True


def format_missing_identity_hint(target: Path) -> str:
    """Multi-line hint printed when commit is skipped due to missing identity.

    Shown to the user by the caller (keeps this module free of console/UI deps).
    """
    target_s = str(target)
    return (
        "跳过 git 提交：当前仓库未配置 git user.email / user.name。\n"
        "    改动已 staged。请配置后手动 commit：\n"
        f"      git -C {target_s} config user.email \"you@example.com\"\n"
        f"      git -C {target_s} config user.name \"Your Name\"\n"
        f"      git -C {target_s} commit -m \"chore: initialize agent harness\""
    )
