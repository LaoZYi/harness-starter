"""Issue gl#21：测试必须对用户的全局 git 配置免疫。

有些开发者会在全局 `gitconfig` 里启用 pre-commit hook / `core.hooksPath` /
`commit.gpgsign` 等约束，导致跑 `make test` 时那些设置泄漏到测试里临时仓库的
`git commit` 子进程，让无关的 setUp / `harness init --git-commit` 全挂。

这里用一个「拒绝一切 commit 的全局 hook」作为红军，验证：

- `_git_helper.init_git_repo` 不再被 hostile 全局配置干扰（修掉原 27 个 ERROR 的同
  源风险）
- `tests.test_cli._run_harness` 传给 harness 子进程的 env 也会隔离全局配置，让
  `test_git_commit_flag` 在 hostile 环境下依然通过（修掉原 1 个 FAIL）
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from _git_helper import init_git_repo  # noqa: E402
from test_cli import _TEST_CONFIG, _run_harness  # noqa: E402


def _write_hostile_global_gitconfig(root: Path) -> Path:
    """造一份「拒绝所有 commit」的 gitconfig。返回 gitconfig 路径。

    调用方把 `GIT_CONFIG_GLOBAL` 指向它，即可模拟「全局 git 配置带强制 hook」的
    用户环境。
    """
    hooks_dir = root / "hostile-hooks"
    hooks_dir.mkdir()
    pre_commit = hooks_dir / "pre-commit"
    pre_commit.write_text(
        "#!/bin/sh\necho 'blocked by hostile pre-commit' >&2\nexit 1\n",
        encoding="utf-8",
    )
    pre_commit.chmod(0o755)
    gitconfig = root / "hostile-gitconfig"
    gitconfig.write_text(f"[core]\n\thooksPath = {hooks_dir}\n", encoding="utf-8")
    return gitconfig


def _git_log_oneline(repo: Path) -> str:
    """读 repo 的 git log（本身也用隔离 env 读，避免被 hostile 配置影响）。"""
    result = subprocess.run(
        ["git", "-C", str(repo), "log", "--oneline"],
        capture_output=True, text=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
    )
    return result.stdout


class HelperIgnoresHostileGlobalConfigTests(unittest.TestCase):
    """`_git_helper.init_git_repo` 必须屏蔽用户全局 git 配置。"""

    def test_init_git_repo_survives_hostile_global_hookspath(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hostile = _write_hostile_global_gitconfig(root)
            target = root / "repo"
            target.mkdir()

            with patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(hostile)}):
                # 未加 env 隔离前：helper 里的 `git commit --allow-empty` 会被
                # hostile pre-commit 拦截，setUp 直接崩
                init_git_repo(target)

            self.assertIn("init", _git_log_oneline(target))


class RunHarnessIgnoresHostileGlobalConfigTests(unittest.TestCase):
    """`_run_harness` 必须在传给 harness 的 env 里隔离全局 git 配置。"""

    def test_run_harness_init_git_commit_survives_hostile_hookspath(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hostile = _write_hostile_global_gitconfig(root)
            target = root / "repo"
            target.mkdir()

            # 构造最小化的「用户仓库」：git init + 本地 identity
            subprocess.run(["git", "init", str(target)], capture_output=True)
            subprocess.run(
                ["git", "-C", str(target), "config", "user.email", "t@t.com"],
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(target), "config", "user.name", "T"],
                capture_output=True,
            )

            cfg_path = target / "_test_config.json"
            cfg_path.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")

            with patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(hostile)}):
                result = _run_harness(
                    "init", str(target), "--config", str(cfg_path),
                    "--non-interactive", "--git-commit",
                )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("initialize agent harness", _git_log_oneline(target))


if __name__ == "__main__":
    unittest.main()
