"""`harness init --scaffold <git_url>` 契约测试。

所有"远端仓库"用本地 bare repo 模拟（`git init --bare`），CI 和开发机都不依赖
外网。所有 `git` 子进程都走 `isolated_git_env()`（见 `_git_helper.py`），避免
用户全局 gitconfig / hook 污染。
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

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from _git_helper import isolated_git_env  # noqa: E402


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        env=isolated_git_env(),
    )


def _make_remote_with_content(root: Path, *, branch: str = "master") -> Path:
    """搭一个本地 bare repo（扮演远端）并推入一些内容。返回 bare 路径。

    仓库结构：
        README.md
        src/main.py
        templates/skeleton.py
    """
    bare = root / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", branch, str(bare)],
        check=True, capture_output=True, env=isolated_git_env(),
    )
    work = root / "work"
    work.mkdir()
    _git(["init", "-q", "-b", branch], cwd=work)
    _git(["config", "user.email", "t@t.com"], cwd=work)
    _git(["config", "user.name", "T"], cwd=work)
    _git(["config", "commit.gpgsign", "false"], cwd=work)
    (work / "README.md").write_text("hello", encoding="utf-8")
    (work / "src").mkdir()
    (work / "src" / "main.py").write_text("print('main')", encoding="utf-8")
    (work / "templates").mkdir()
    (work / "templates" / "skeleton.py").write_text("# skeleton", encoding="utf-8")
    _git(["add", "-A"], cwd=work)
    _git(["commit", "-m", "init", "-q"], cwd=work)
    _git(["remote", "add", "origin", str(bare)], cwd=work)
    _git(["push", "origin", branch, "-q"], cwd=work)
    return bare


class IsGitUrlTests(unittest.TestCase):
    """R-001：自动检测 git URL vs 本地路径。"""

    def test_https_url_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("https://github.com/foo/bar.git"))

    def test_http_url_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("http://gitlab.example.com/foo/bar.git"))

    def test_ssh_shorthand_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("git@github.com:foo/bar.git"))

    def test_ssh_protocol_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("ssh://git@host/foo/bar.git"))

    def test_git_protocol_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("git://host/foo/bar.git"))

    def test_ends_with_dot_git_is_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertTrue(is_git_url("/local/mirror/foo.git"))

    def test_absolute_local_path_is_not_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertFalse(is_git_url("/home/user/framework"))

    def test_relative_local_path_is_not_git(self) -> None:
        from agent_harness._scaffold_git import is_git_url
        self.assertFalse(is_git_url("../framework"))


class CopyScaffoldFromGitTests(unittest.TestCase):
    """R-002 + R-003 + R-004：clone + ref + subdir + 文件复制。"""

    def test_end_to_end_clone_and_copy(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            target = root / "new-project"
            with patch.dict(os.environ, isolated_git_env()):
                count = copy_scaffold_from_git(str(bare), target)
            self.assertGreater(count, 0)
            self.assertTrue((target / "README.md").exists())
            self.assertTrue((target / "src" / "main.py").exists())
            # .git 目录不应残留（copy_scaffold 已过滤）
            self.assertFalse((target / ".git").exists())

    def test_ref_checks_out_specific_branch(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            # 再推一条 feature 分支，内容不同
            work = root / "work2"
            work.mkdir()
            subprocess.run(["git", "clone", str(bare), str(work)],
                           check=True, capture_output=True, env=isolated_git_env())
            _git(["config", "user.email", "t@t.com"], cwd=work)
            _git(["config", "user.name", "T"], cwd=work)
            _git(["config", "commit.gpgsign", "false"], cwd=work)
            _git(["checkout", "-b", "feature"], cwd=work)
            (work / "README.md").write_text("feature-version", encoding="utf-8")
            _git(["commit", "-am", "feature", "-q"], cwd=work)
            _git(["push", "origin", "feature", "-q"], cwd=work)

            target = root / "new-project"
            with patch.dict(os.environ, isolated_git_env()):
                copy_scaffold_from_git(str(bare), target, ref="feature")
            self.assertEqual(
                (target / "README.md").read_text(encoding="utf-8"),
                "feature-version",
            )

    def test_subdir_only_copies_that_path(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            target = root / "new-project"
            with patch.dict(os.environ, isolated_git_env()):
                copy_scaffold_from_git(str(bare), target, subdir="templates")
            self.assertTrue((target / "skeleton.py").exists())
            # subdir 外的文件不应被复制
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "src").exists())

    def test_nonexistent_ref_raises(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            target = root / "new-project"
            with patch.dict(os.environ, isolated_git_env()):
                with self.assertRaises(SystemExit) as ctx:
                    copy_scaffold_from_git(str(bare), target, ref="no-such-branch")
            # 错误消息应含 ref 或分支
            self.assertIn("ref", str(ctx.exception).lower() + str(ctx.exception))

    def test_nonexistent_subdir_raises(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            target = root / "new-project"
            with patch.dict(os.environ, isolated_git_env()):
                with self.assertRaises(SystemExit) as ctx:
                    copy_scaffold_from_git(str(bare), target, subdir="no-such-dir")
            self.assertIn("子目录", str(ctx.exception))


class GitNotAvailableTests(unittest.TestCase):
    """R-005：git 未装时清晰报错。"""

    def test_git_missing_raises(self) -> None:
        from agent_harness import _scaffold_git
        with patch.object(_scaffold_git.shutil, "which", return_value=None):
            with tempfile.TemporaryDirectory() as tmpdir:
                with self.assertRaises(SystemExit) as ctx:
                    _scaffold_git.copy_scaffold_from_git(
                        "https://example.com/foo.git", Path(tmpdir) / "t"
                    )
            self.assertIn("git", str(ctx.exception).lower() + str(ctx.exception))


class SubdirPathTraversalTests(unittest.TestCase):
    """安全：subdir 不允许路径遍历（/cso 分析结论）。"""

    def test_subdir_with_dotdot_rejected(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                copy_scaffold_from_git(
                    "https://example.com/foo.git",
                    Path(tmpdir) / "t",
                    subdir="../escape",
                )
            self.assertIn("..", str(ctx.exception))

    def test_subdir_absolute_rejected(self) -> None:
        from agent_harness._scaffold_git import copy_scaffold_from_git
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                copy_scaffold_from_git(
                    "https://example.com/foo.git",
                    Path(tmpdir) / "t",
                    subdir="/etc/passwd",
                )
            self.assertIn("绝对路径", str(ctx.exception))


class CliEndToEndTests(unittest.TestCase):
    """CLI 端到端：harness init --scaffold <bare_url> ... 成功 init（R-004 集成）。"""

    def test_init_with_git_scaffold(self) -> None:
        _TEST_CONFIG = {
            "project_name": "Test Project",
            "project_slug": "test-project",
            "summary": "For testing",
            "project_type": "backend-service",
            "language": "python",
            "package_manager": "pip",
            "run_command": "python -m app",
            "test_command": "pytest",
            "check_command": "ruff check .",
            "ci_command": "make ci",
            "deploy_target": "docker",
            "has_production": False,
            "sensitivity": "standard",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bare = _make_remote_with_content(root)
            target = root / "new-project"
            cfg = root / "cfg.json"
            cfg.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")

            env = {**isolated_git_env(), "PYTHONPATH": str(REPO_ROOT / "src")}
            result = subprocess.run(
                [sys.executable, "-m", "agent_harness", "init",
                 str(target), "--scaffold", str(bare),
                 "--config", str(cfg),
                 "--non-interactive", "--no-git-commit"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # scaffold 带入的文件
            self.assertTrue((target / "src" / "main.py").exists())
            # harness 注入的文件
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertFalse((target / ".git").exists())


if __name__ == "__main__":
    unittest.main()
