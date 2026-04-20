"""Shared git-init helper for tests.

测试里多处需要在临时目录 `git init` + 首个 empty commit。直接调 `git commit`
会在**没有全局 git config** 的机器上挂掉（git 要求 author identity），而在
**有「自定义全局 gitconfig / core.hooksPath / 强制 pre-commit」** 的机器上同样
会挂（用户的全局 hook 会拦截测试里的 empty commit）。见 Issue gl#21。

本 helper 统一处理四件事：
1. 用 `isolated_git_env()` 屏蔽用户全局 / 系统级 gitconfig，确保子进程看到的是
   一套干净的配置上下文（避免 pre-commit hook、`core.hooksPath`、`commit.gpgsign`
   等外部设置污染测试）
2. git init
3. 写入 **local** user.email / user.name / commit.gpgsign=false（双保险，即使
   env 隔离失效也不依赖全局 identity）
4. 首个 empty commit + 强制 master 分支

新增跨平台测试时**请直接调用本 helper**，不要 inline 复制粘贴 git 初始化
逻辑（那样容易漏掉 env 隔离或 config 设置，导致同事机器上 setUp 崩溃）。
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def isolated_git_env() -> dict[str, str]:
    """返回一个把用户全局 / 系统级 gitconfig 屏蔽掉的 env。

    `GIT_CONFIG_GLOBAL=/dev/null` + `GIT_CONFIG_SYSTEM=/dev/null` 是 git 官方
    支持的完全隔离入口：子进程只看 repo 本地 config（以及 env 自带的 Git 变量），
    不再加载用户 ~/.gitconfig 或 /etc/gitconfig。

    其他模块（如 `tests.test_cli._run_harness`）需要把 harness 子进程也与用户
    全局 gitconfig 隔离时，请复用此函数。
    """
    return {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }


def init_git_repo(path: Path, *, branch: str = "master") -> None:
    """Initialize a git repo at `path` with an empty commit on `branch`.

    Sets local (not global) user.email/user.name + disables gpg signing so this
    works on machines without global git config or gpg configured. Uses
    `isolated_git_env()` for all subprocess calls so the user's global gitconfig
    (pre-commit hooks, forced worktree rules, etc.) cannot break setUp.
    """
    env = isolated_git_env()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, env=env)
    # 显式 local config，避免依赖全局配置（见本文件顶部说明）
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, env=env)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True, env=env)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True, env=env)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"],
        cwd=path, check=True, env=env,
    )
    subprocess.run(["git", "branch", "-M", branch], cwd=path, check=True, env=env)
