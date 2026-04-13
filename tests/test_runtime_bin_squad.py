"""Issue #25 — .agent-harness/bin/squad 端到端契约。

核心验收：无 harness CLI + 无 PyYAML 环境下 bin/squad 可跑 create/status。
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


_BASE_ANSWERS: dict[str, object] = {
    "project_name": "Squad Bin Target",
    "project_slug": "squad-bin-target",
    "summary": "Test project for squad embedding",
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


def _run_bin(bin_path: Path, *args: str, cwd: Path):
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"  # 清掉 harness CLI 可能所在的 venv
    return subprocess.run(
        [sys.executable, str(bin_path), *args],
        cwd=str(cwd), capture_output=True, text=True, env=env,
    )


class SquadBinInstallTests(unittest.TestCase):

    def test_init_creates_squad_entry_and_runtime_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            self.assertTrue((root / ".agent-harness" / "bin" / "squad").is_file())
            squad_pkg = root / ".agent-harness" / "bin" / "_runtime" / "squad"
            self.assertTrue(squad_pkg.is_dir())
            for mod in ("cli.py", "spec.py", "coordinator.py", "mailbox.py",
                        "state.py", "tmux.py", "watchdog.py", "capability.py",
                        "worker_files.py", "__init__.py"):
                self.assertTrue((squad_pkg / mod).is_file(), f"缺模块：{mod}")

    def test_spec_py_rewrites_security_import_to_absolute(self):
        """_runtime/squad/spec.py 的 security import 必须从相对改为
        `from _runtime.security import`（_runtime 是顶级 package）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            spec_py = root / ".agent-harness" / "bin" / "_runtime" / "squad" / "spec.py"
            src = spec_py.read_text(encoding="utf-8")
            self.assertNotIn("from ..security", src)
            self.assertIn("from _runtime.security import", src)


class SquadBinStdlibOnlyTests(unittest.TestCase):
    """squad + security 运行时必须纯 stdlib（无 PyYAML 等第三方）。"""

    _STDLIB_ALLOW = {
        "__future__", "argparse", "collections", "contextlib", "dataclasses",
        "datetime", "json", "os", "pathlib", "re", "sys", "time", "typing",
        "fcntl", "shutil", "subprocess", "tempfile", "uuid", "hashlib",
        "textwrap", "string", "itertools", "functools", "enum", "copy",
        "sqlite3", "signal", "shlex",
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
                    continue
                if node.module:
                    mods.add(node.module.split(".")[0])
        return mods

    def test_squad_and_security_stdlib_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            runtime = root / ".agent-harness" / "bin" / "_runtime"
            targets = [runtime / "security.py"] + sorted(
                (runtime / "squad").glob("*.py")
            )
            # `_runtime` 是 squad.spec 重写后的绝对导入前缀（指向自身 sibling 包）
            allowed = self._STDLIB_ALLOW | {"_runtime"}
            for py in targets:
                imports = self._collect_imports(py)
                non_stdlib = imports - allowed
                self.assertEqual(
                    non_stdlib, set(),
                    f"{py.name} 引入非 stdlib 依赖 {non_stdlib}"
                )


class SquadBinEndToEndTests(unittest.TestCase):
    """bin/squad 在无 harness CLI 环境下 create/status 全流程通。"""

    def _init_git(self, path: Path):
        subprocess.run(["git", "init", "-q"], cwd=path, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"],
                       cwd=path, check=True)
        subprocess.run(["git", "branch", "-M", "master"], cwd=path, check=True)

    def test_bin_squad_create_dry_run(self):
        """无 harness + 无 PyYAML 环境 bin/squad create --dry-run 成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            self._init_git(root)
            spec = root / "spec.json"
            spec.write_text(json.dumps({
                "task_id": "sq-e2e",
                "base_branch": "master",
                "workers": [
                    {"name": "scout", "capability": "scout", "prompt": "探索"},
                    {"name": "builder", "capability": "builder",
                     "depends_on": ["scout"], "prompt": "实现"},
                ],
            }, ensure_ascii=False), encoding="utf-8")

            bin_squad = root / ".agent-harness" / "bin" / "squad"
            r = _run_bin(bin_squad, "create", str(spec), "--dry-run",
                         "--project", str(root), cwd=root)
            self.assertEqual(r.returncode, 0,
                             f"exit {r.returncode}\nstderr={r.stderr}\nstdout={r.stdout}")
            # manifest.json 生成
            mf = root / ".agent-harness" / "squad" / "sq-e2e" / "manifest.json"
            self.assertTrue(mf.is_file())
            data = json.loads(mf.read_text(encoding="utf-8"))
            self.assertEqual(data["task_id"], "sq-e2e")
            self.assertEqual(len(data["workers"]), 2)

    def test_bin_squad_status_lists_squad(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            self._init_git(root)
            spec = root / "spec.json"
            spec.write_text(json.dumps({
                "task_id": "st-e2e", "base_branch": "master",
                "workers": [{"name": "a", "capability": "scout", "prompt": "x"}],
            }, ensure_ascii=False), encoding="utf-8")
            bin_squad = root / ".agent-harness" / "bin" / "squad"
            _run_bin(bin_squad, "create", str(spec), "--dry-run",
                     "--project", str(root), cwd=root)
            r = _run_bin(bin_squad, "status", "--project", str(root), cwd=root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("st-e2e", r.stdout)

    def test_bin_squad_rejects_yaml_with_migration_hint(self):
        """.yaml spec → bin/squad 应给迁移提示（回归保护 Issue #25 破坏性变更）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "target"
            initialize_project(root, {**_BASE_ANSWERS})
            self._init_git(root)
            yaml_spec = root / "spec.yaml"
            yaml_spec.write_text("task_id: x\nbase_branch: main\n", encoding="utf-8")
            bin_squad = root / ".agent-harness" / "bin" / "squad"
            r = _run_bin(bin_squad, "create", str(yaml_spec), "--dry-run",
                         "--project", str(root), cwd=root)
            self.assertNotEqual(r.returncode, 0)
            combined = r.stderr + r.stdout
            self.assertIn("JSON", combined, combined[:300])


if __name__ == "__main__":
    unittest.main()
