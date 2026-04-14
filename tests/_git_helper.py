"""Shared git-init helper for tests.

测试里多处需要在临时目录 `git init` + 首个 empty commit。直接调 `git commit`
会在**没有全局 git config** 的机器上挂掉（git 要求 author identity）。

本 helper 统一处理三件事：
1. git init
2. 写入 **local** user.email / user.name / commit.gpgsign=false（不污染用户
   全局 config，且不依赖全局 config 存在）
3. 首个 empty commit + 强制 master 分支

新增跨平台测试时**请直接调用本 helper**，不要 inline 复制粘贴 git 初始化
逻辑（那样容易漏掉 config 设置，导致同事机器上 setUp 崩溃）。
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def init_git_repo(path: Path, *, branch: str = "master") -> None:
    """Initialize a git repo at `path` with an empty commit on `branch`.

    Sets local (not global) user.email/user.name + disables gpg signing so this
    works on machines without global git config or gpg configured.
    """
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    # 显式 local config，避免依赖全局配置（见本文件顶部说明）
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=path, check=True,
    )
    subprocess.run(["git", "branch", "-M", branch], cwd=path, check=True)
