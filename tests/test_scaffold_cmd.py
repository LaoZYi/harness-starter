"""`harness init --scaffold-cmd <cmd>` 契约测试。

所有脚手架命令用 POSIX shell 内建模拟（`sh -c '...'`），CI 和开发机都不
依赖外部生态（node / cargo / django）。端到端 CLI 测试走 `isolated_git_env()`
避免 harness auto git commit 被用户全局 gitconfig 污染（lessons 2026-04-20）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from _git_helper import isolated_git_env  # noqa: E402


class RunScaffoldCommandTests(unittest.TestCase):
    """R-001 + R-004 + R-005 + R-006：核心行为 + 失败路径。"""

    def test_runs_command_in_target_and_creates_files(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            count = run_scaffold_command(
                "sh -c 'echo hello > README.md && mkdir -p src && echo code > src/main.py'",
                target,
            )
            self.assertGreaterEqual(count, 2)
            self.assertTrue((target / "README.md").is_file())
            self.assertTrue((target / "src" / "main.py").is_file())
            self.assertIn("hello", (target / "README.md").read_text())

    def test_target_created_if_missing(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "a" / "b" / "c"
            self.assertFalse(target.exists())
            run_scaffold_command("sh -c 'echo x > out.txt'", target)
            self.assertTrue((target / "out.txt").is_file())

    def test_dash_dash_separator_preserved(self) -> None:
        """vite 风格：`... -- --template react` 的 `--` 后续参数完整传到脚手架。"""
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "p"
            # sh -c 'echo "$@" > args.txt' _ -- --template react
            # $@ 从 $1 开始展开：-- --template react
            run_scaffold_command(
                'sh -c \'echo "$@" > args.txt\' _ -- --template react',
                target,
            )
            content = (target / "args.txt").read_text().strip()
            self.assertEqual(content, "-- --template react")

    def test_quoted_arg_with_spaces(self) -> None:
        """带空格的参数在 shlex.split 后保留为一个 argv 项。"""
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "p"
            run_scaffold_command(
                'sh -c \'echo "$1" > out.txt\' _ "my app name"',
                target,
            )
            self.assertEqual((target / "out.txt").read_text().strip(), "my app name")

    def test_nonzero_exit_raises_systemexit(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command("sh -c 'exit 3'", Path(tmpdir) / "t")
            msg = str(ctx.exception)
            self.assertIn("3", msg)  # returncode

    def test_unknown_command_raises_systemexit(self) -> None:
        """shutil.which 预检：程序不存在时清晰报错。"""
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command(
                    "this-cmd-does-not-exist-xyz-42 arg",
                    Path(tmpdir) / "t",
                )
            self.assertIn("未找到", str(ctx.exception))

    def test_empty_command_raises(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command("   ", Path(tmpdir) / "t")
            self.assertIn("不能为空", str(ctx.exception))

    def test_shlex_parse_error_raises_clearly(self) -> None:
        """引号不闭合时 shlex 抛 ValueError，我们转 SystemExit。"""
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command('echo "unterminated', Path(tmpdir) / "t")
            self.assertIn("解析", str(ctx.exception))


class ShellMetacharSafetyTests(unittest.TestCase):
    """R-005 安全契约：shell 元字符被当字面参数，不解释。"""

    def test_semicolon_does_not_chain_commands(self) -> None:
        """`sh -c 'echo ok' ; rm -rf <sentinel>` —— 分号后部分是 argv，不执行 rm。

        关键证据：sentinel 文件跑完后仍存在。
        """
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            sentinel = Path(tmpdir) / "sentinel.txt"
            sentinel.write_text("I MUST NOT BE DELETED", encoding="utf-8")
            target = Path(tmpdir) / "project"

            # 若走 shell=True，`; rm -rf <sentinel>` 会执行导致 sentinel 消失
            # 我们走 argv：sh 收到多余参数视为 $0/$1/...，不解释，sentinel 不动
            cmd = f"sh -c 'echo ok > out.txt' _ ; rm -rf {sentinel}"
            run_scaffold_command(cmd, target)

            self.assertTrue(sentinel.is_file(), "sentinel 被删除 — shell 元字符被解释了！")
            self.assertEqual(sentinel.read_text(), "I MUST NOT BE DELETED")
            self.assertTrue((target / "out.txt").is_file())

    def test_dollar_paren_not_evaluated(self) -> None:
        """`$(cmd)` 不被当 command substitution 求值。"""
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "p"
            # 若被求值，$(echo pwned) 会替换为 pwned
            # 我们走 argv，$(echo pwned) 是字面参数传给 sh 的 $1
            run_scaffold_command(
                'sh -c \'echo "$1" > out.txt\' _ "$(echo pwned)"',
                target,
            )
            content = (target / "out.txt").read_text().strip()
            # sh 的 $1 拿到的是字面量 "$(echo pwned)"
            self.assertEqual(content, "$(echo pwned)")


class CliMutualExclusionTests(unittest.TestCase):
    """R-002：--scaffold 与 --scaffold-cmd 互斥。"""

    def test_both_flags_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {**isolated_git_env(), "PYTHONPATH": str(REPO_ROOT / "src")}
            result = subprocess.run(
                [sys.executable, "-m", "agent_harness", "init",
                 str(Path(tmpdir) / "t"),
                 "--scaffold", "/some/path",
                 "--scaffold-cmd", "echo x",
                 "--non-interactive", "--no-git-commit"],
                capture_output=True, text=True, env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            combined = (result.stderr + result.stdout).lower()
            # argparse 互斥组标准错误消息
            self.assertIn("not allowed with argument", combined)


class InteractiveChoiceTests(unittest.TestCase):
    """R-003：ask_scaffold 新增「脚手架命令」选项。"""

    def test_ask_scaffold_source_includes_cmd_option(self) -> None:
        """源码契约：ask_scaffold 中包含「脚手架命令」字样。"""
        import inspect

        from agent_harness import init_flow
        src = inspect.getsource(init_flow.ask_scaffold)
        self.assertIn("脚手架命令", src)


class CliEndToEndTests(unittest.TestCase):
    """R-007：harness init --scaffold-cmd 端到端 init。"""

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

    def test_init_with_scaffold_cmd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            cfg = Path(tmpdir) / "cfg.json"
            cfg.write_text(json.dumps(self._TEST_CONFIG), encoding="utf-8")

            env = {**isolated_git_env(), "PYTHONPATH": str(REPO_ROOT / "src")}
            result = subprocess.run(
                [sys.executable, "-m", "agent_harness", "init",
                 str(target),
                 "--scaffold-cmd",
                 "sh -c 'echo hello > README.md && mkdir src && echo code > src/main.py'",
                 "--config", str(cfg),
                 "--non-interactive", "--no-git-commit"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # 脚手架命令产物
            self.assertTrue((target / "README.md").is_file())
            self.assertTrue((target / "src" / "main.py").is_file())
            # harness 注入
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / ".agent-harness").is_dir())


class ShutilWhichMockTests(unittest.TestCase):
    """R-004：shutil.which 返回 None → 不走 subprocess。"""

    def test_which_none_short_circuits(self) -> None:
        from agent_harness import _scaffold_cmd
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(_scaffold_cmd.shutil, "which", return_value=None):
                with patch.object(_scaffold_cmd.subprocess, "run") as mock_run:
                    with self.assertRaises(SystemExit):
                        _scaffold_cmd.run_scaffold_command(
                            "some-cmd arg", Path(tmpdir) / "t",
                        )
                    mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
