"""Issue #24 — audit / memory 项目内嵌运行时测试。

验收核心：用户 clone 一个 init 过的项目，**没装 harness CLI** 也能跑
`.agent-harness/bin/audit` 和 `.agent-harness/bin/memory`。
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_harness.initializer import initialize_project
from agent_harness.upgrade import execute_upgrade


_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Runtime Bin Target",
    "project_slug": "runtime-bin-target",
    "summary": "Test project for runtime bin embedding",
    "project_type": "backend-service",
    "language": "python",
    "package_manager": "uv",
    "run_command": "uv run python -m app",
    "test_command": "uv run pytest",
    "check_command": "uv run ruff check .",
    "ci_command": "make ci",
    "deploy_target": "docker",
    "has_production": False,
    "sensitivity": "internal",
}


def _run_bin(bin_path: Path, *args: str, cwd: Path, env_override=None):
    """运行项目内 bin 脚本。清空 PATH 中的 harness 模拟无 CLI 环境。"""
    env = os.environ.copy()
    # 清除 PATH 里的 harness 二进制（靠空 PATH 兜底——反正 bin 脚本只需 python3）
    env["PATH"] = "/usr/bin:/bin"  # 保留基础 Unix 工具，去掉 harness 可能所在的 venv
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [sys.executable, str(bin_path), *args],
        cwd=str(cwd), capture_output=True, text=True, env=env,
    )


class RuntimeBinInstallTests(unittest.TestCase):
    """init 后 .agent-harness/bin/ 结构正确。"""

    def test_init_creates_bin_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            bin_dir = root / ".agent-harness" / "bin"
            self.assertTrue(bin_dir.is_dir(), f"bin 目录未创建: {bin_dir}")

    def test_init_creates_audit_and_memory_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            for entry in ("audit", "memory"):
                p = root / ".agent-harness" / "bin" / entry
                self.assertTrue(p.is_file(), f"entry 缺失: {p}")
                content = p.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("#!"),
                                f"{entry} 缺 shebang")

    def test_init_copies_runtime_modules(self):
        """_runtime/ 下必须有 audit.py / audit_cli.py / memory.py / _shared.py。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            runtime = root / ".agent-harness" / "bin" / "_runtime"
            for mod in ("audit.py", "audit_cli.py", "memory.py", "_shared.py",
                        "__init__.py"):
                self.assertTrue((runtime / mod).is_file(),
                                f"runtime 模块缺失: {mod}")


class RuntimeBinStdlibOnlyTests(unittest.TestCase):
    """_runtime 下所有 .py 文件必须纯 stdlib（无第三方依赖）。"""

    # Python 3.11 stdlib 的一部分，加上项目内相对导入
    _STDLIB_ALLOW = {
        "__future__", "argparse", "collections", "contextlib", "dataclasses",
        "datetime", "json", "os", "pathlib", "re", "sys", "time", "typing",
        "fcntl", "shutil", "subprocess", "tempfile", "uuid", "hashlib",
        "textwrap", "string", "itertools", "functools", "enum", "copy",
        "sqlite3", "signal", "shlex", "math",
    }

    def _collect_imports(self, py_file: Path) -> set[str]:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        mods: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    continue  # 相对导入，同包内
                if node.module:
                    mods.add(node.module.split(".")[0])
        return mods

    def test_runtime_only_imports_stdlib(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            runtime = root / ".agent-harness" / "bin" / "_runtime"
            for py in sorted(runtime.glob("*.py")):
                imports = self._collect_imports(py)
                non_stdlib = imports - self._STDLIB_ALLOW
                self.assertEqual(
                    non_stdlib, set(),
                    f"{py.name} 引入了非 stdlib 依赖: {non_stdlib}。"
                    f"运行时必须纯 stdlib。"
                )


class BinAuditEndToEndTests(unittest.TestCase):
    """`.agent-harness/bin/audit` 在无 harness CLI 环境下端到端跑通。"""

    def _init_target(self, root: Path):
        initialize_project(root, {**_BASE_ANSWERS})
        return root / ".agent-harness" / "bin" / "audit"

    def test_audit_append_writes_to_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            bin_audit = self._init_target(root)
            r = _run_bin(
                bin_audit, "append",
                "--file", "lessons.md", "--op", "append",
                "--summary", "e2e-test-entry",
                cwd=root,
            )
            self.assertEqual(r.returncode, 0,
                             f"exit {r.returncode}\nstderr: {r.stderr}\nstdout: {r.stdout}")
            jsonl = root / ".agent-harness" / "audit.jsonl"
            self.assertTrue(jsonl.is_file())
            content = jsonl.read_text(encoding="utf-8").strip()
            self.assertIn("e2e-test-entry", content)

    def test_audit_tail_reads_back(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            bin_audit = self._init_target(root)
            _run_bin(bin_audit, "append", "--file", "task-log.md",
                     "--op", "append", "--summary", "tail-test",
                     cwd=root)
            r = _run_bin(bin_audit, "tail", "--limit", "5", cwd=root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("tail-test", r.stdout)

    def test_audit_rejects_invalid_file(self):
        """--file 只接受 TRACKED_FILES，回归保护。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            bin_audit = self._init_target(root)
            r = _run_bin(bin_audit, "append", "--file", "evil.md",
                         "--op", "append", "--summary", "x", cwd=root)
            self.assertNotEqual(r.returncode, 0)


class BinMemoryEndToEndTests(unittest.TestCase):
    """`.agent-harness/bin/memory rebuild` 在无 harness CLI 环境下跑通。"""

    def test_memory_rebuild_creates_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            bin_memory = root / ".agent-harness" / "bin" / "memory"
            # 预备最小 lessons.md
            lessons = root / ".agent-harness" / "lessons.md"
            lessons.write_text(
                "## 2026-04-13 [测试] 示例教训\n\n- 规则：xxx\n",
                encoding="utf-8",
            )
            r = _run_bin(bin_memory, "rebuild", ".", "--force", cwd=root)
            self.assertEqual(r.returncode, 0,
                             f"exit {r.returncode}\nstderr: {r.stderr}")
            idx = root / ".agent-harness" / "memory-index.md"
            self.assertTrue(idx.is_file())


class RuntimeBinUpgradeTests(unittest.TestCase):
    """upgrade apply 必须同步更新 bin/_runtime/ 和 entry 脚本（视为运行时）。"""

    def test_upgrade_refreshes_runtime_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            # 模拟用户误改了 _runtime/audit.py
            bad = root / ".agent-harness" / "bin" / "_runtime" / "audit.py"
            orig = bad.read_text(encoding="utf-8")
            bad.write_text("# user-corrupted\n", encoding="utf-8")
            # upgrade 应该把它覆盖回源版本
            execute_upgrade(root, {**_BASE_ANSWERS})
            after = bad.read_text(encoding="utf-8")
            self.assertEqual(
                after, orig,
                "upgrade 必须覆盖 _runtime 内容（运行时文件无用户数据）"
            )

    def test_upgrade_refreshes_entry_scripts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            entry = root / ".agent-harness" / "bin" / "audit"
            orig = entry.read_text(encoding="utf-8")
            entry.write_text("#!/usr/bin/env python3\n# broken\n",
                             encoding="utf-8")
            execute_upgrade(root, {**_BASE_ANSWERS})
            after = entry.read_text(encoding="utf-8")
            self.assertEqual(after, orig)


if __name__ == "__main__":
    unittest.main()
