# 实施计划：`harness init --scaffold-cmd` 支持脚手架命令

对应规格：`docs/superpowers/specs/2026-04-21-scaffold-from-cmd-spec.md`
分支：`feat/scaffold-cmd-20260421`
基线：`22e470f`

## R-ID 映射

| R-ID | 内容 | 对应 Step |
|---|---|---|
| R-001 | `run_scaffold_command()` 正常路径（shlex 拆分、cwd、stdio 透传、target 创建） | Step 3（RED）、Step 4（GREEN） |
| R-002 | `--scaffold` ↔ `--scaffold-cmd` 互斥（argparse group） | Step 3、Step 5 |
| R-003 | `ask_scaffold` 新增「脚手架命令」选项 | Step 3、Step 6 |
| R-004 | 命令失败 / 不存在的中文报错 | Step 3、Step 4 |
| R-005 | shell 元字符被当字面量（argv list 契约） | Step 3、Step 4 |
| R-006 | 空命令 / shlex 解析失败的中文报错 | Step 3、Step 4 |
| R-007 | CLI 端到端 init 流程 | Step 3、Step 7 |
| R-008 | 文档同步（product/runbook/architecture/AGENTS/ADR） | Step 8 |
| R-009 | 现有 `--scaffold` 行为无回归 | Step 7 跑全量 `make test` |

## 步骤清单

### Step 1：/cso 快速扫（生产项目预警）

`has_production=true`（见 `project.json`），针对本次特性扫：

| 风险点 | 缓解 |
|---|---|
| **任意代码执行**（用户自己命令行输入的命令） | 用户自愿 + 命令运行在用户机器上，本身不算漏洞；但 harness 必须用 argv（`shell=False`），避免 shell 元字符被解释为运算符，产生意料之外的执行 |
| **命令注入**（`;` `&` `\|` `$()` 被解释） | `shlex.split` + `subprocess.run(argv, shell=False)`：元字符成为字面参数；R-005 契约测试锁定 |
| **stdin/stdout 捕获导致死锁**（交互式脚手架） | 不捕获，stdio 继承父进程 |
| **target 目录遍历** | target 由 harness 的 argparse 正常处理；命令 cwd 只设为 target；命令自己的参数由用户负责 |
| **信息泄露**（命令失败时回显完整命令） | 可接受——命令是用户自己输入的，不是外部输入 |
| **子进程 signal 处理** | 让 `subprocess.run` 默认语义：Ctrl-C 会传递到子进程（POSIX 默认），harness 只读 `returncode` |

**结论**：把「argv list、shell=False、不捕获 stdio」写进 Step 4 的安全约束。其他风险当前可控。

### Step 2：写 ADR 0004（Proposed）

**文件**：`docs/decisions/0004-scaffold-from-cmd.md`

**骨架**：

- 状态：Proposed（实施完成后改 Accepted）
- 背景：为什么要第三种来源
- 方案对比表：
  - A. 独立 `--scaffold-cmd` flag（**采纳**）
  - B. 复用 `--scaffold`，按启发式判断「命令 vs 路径」（拒绝：不可靠）
  - C. 新增 `--scaffold-preset vite-react` 预设映射（拒绝：维护负担）
  - D. 让用户先手工跑命令再 `harness init <dir>`（拒绝：现状，三步走）
- 关键决策：
  1. 独立 flag + 互斥组，UX 和实现都最简
  2. `shlex.split` + argv list（不用 `shell=True`）
  3. stdio 透传父终端（交互式脚手架才能用）
  4. cwd = target，不改写用户参数（`.` 由用户提供）
- 后果：
  - 正面：UX 清晰、零依赖、交互式脚手架可用
  - 负面：用户需懂脚手架自己的 target 参数写法（文档举例）
  - 中性：新 flag、新模块 ~80 行

### Step 3：写测试（RED 阶段）

**文件**：`tests/test_scaffold_cmd.py`

**骨架**：

```python
"""`harness init --scaffold-cmd <cmd>` 契约测试。

所有脚手架命令用 POSIX shell 内建模拟（`sh -c '...'`），CI 和开发机
都不依赖外部生态（node / cargo / django）。端到端 CLI 测试走
`isolated_git_env()` 避免 harness auto git commit 被用户全局 gitconfig 污染。
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


class RunScaffoldCommandTests(unittest.TestCase):
    """R-001 + R-004 + R-005 + R-006：核心行为 + 失败路径。"""

    def test_runs_command_in_target_and_creates_files(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            count = run_scaffold_command(
                "sh -c \"echo hello > README.md && mkdir -p src && echo code > src/main.py\"",
                target,
            )
        self.assertGreaterEqual(count, 2)
        # 略：断言文件存在、内容匹配

    def test_dash_dash_separator_preserved(self) -> None:
        # `vite` 风格：`npm create vite@latest . -- --template react`
        # 模拟：`sh -c 'echo $@ > args.txt' _ -- --template react`
        # 期望：args.txt 里有 `-- --template react`
        ...

    def test_quoted_arg_with_spaces(self) -> None:
        # `sh -c 'echo "$1" > out' _ "my app"` → out 内容为 "my app"
        ...

    def test_nonzero_exit_raises_systemexit(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command("sh -c 'exit 3'", Path(tmpdir) / "t")
            self.assertIn("3", str(ctx.exception))  # returncode

    def test_unknown_command_raises_systemexit(self) -> None:
        # shutil.which 预检
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit) as ctx:
                run_scaffold_command("this-cmd-does-not-exist-xyz", Path(tmpdir) / "t")
            self.assertIn("未找到", str(ctx.exception) + "")

    def test_empty_command_raises(self) -> None:
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit):
                run_scaffold_command("   ", Path(tmpdir) / "t")

    def test_shlex_parse_error_raises_clearly(self) -> None:
        # 引号不闭合
        from agent_harness._scaffold_cmd import run_scaffold_command
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit):
                run_scaffold_command('echo "unterminated', Path(tmpdir) / "t")

    def test_shell_metachar_treated_as_literal(self) -> None:
        # 安全契约：R-005
        # `sh -c 'echo ok'; rm -rf /` 被 shlex 拆成 ['sh', '-c', 'echo ok', ';',
        # 'rm', '-rf', '/']，整串以 argv 传 sh，sh 看到多余参数会 warn 但不执行 rm
        # 重点：确认 target 兄弟目录不会被删
        ...


class CliMutualExclusionTests(unittest.TestCase):
    """R-002：--scaffold 与 --scaffold-cmd 互斥。"""

    def test_both_flags_fail(self) -> None:
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
            self.assertIn("not allowed", result.stderr.lower() + result.stdout.lower())
            # argparse 互斥组标准错误信息含 "not allowed with argument"


class InteractiveChoiceTests(unittest.TestCase):
    """R-003：ask_scaffold 新增选项字符串契约。"""

    def test_ask_scaffold_includes_cmd_option(self) -> None:
        """模块内存在「脚手架命令」四字选项（字符串契约，用源码扫描）。"""
        import inspect
        from agent_harness import init_flow
        src = inspect.getsource(init_flow.ask_scaffold)
        self.assertIn("脚手架命令", src)


class CliEndToEndTests(unittest.TestCase):
    """R-007：harness init --scaffold-cmd 端到端成功 init。"""

    def test_init_with_scaffold_cmd(self) -> None:
        _TEST_CONFIG = {...}  # 与 test_scaffold_git 同构
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "new-project"
            cfg = Path(tmpdir) / "cfg.json"
            cfg.write_text(json.dumps(_TEST_CONFIG), encoding="utf-8")
            env = {**isolated_git_env(), "PYTHONPATH": str(REPO_ROOT / "src")}
            result = subprocess.run(
                [sys.executable, "-m", "agent_harness", "init",
                 str(target),
                 "--scaffold-cmd", "sh -c 'echo hello > README.md && mkdir src && echo code > src/main.py'",
                 "--config", str(cfg),
                 "--non-interactive", "--no-git-commit"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # scaffold-cmd 产物 + harness 注入
            self.assertTrue((target / "README.md").exists())
            self.assertTrue((target / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
```

**RED 验证**：跑 `python -m pytest tests/test_scaffold_cmd.py -x`，期望全部失败（模块和 flag 尚未实现）。

### Step 4：实现 `_scaffold_cmd.py`（GREEN 核心）

**文件**：`src/agent_harness/_scaffold_cmd.py`（新增）

**骨架**：

```python
"""Run an external scaffold command as `harness init --scaffold-cmd` source.

为什么单独成模块：
- `init_flow.py` 已 278/280 行，不宜继续堆逻辑
- 执行用户命令涉及独立关注点（shlex 拆分、子进程生命周期、stdio 透传）
- 与 `_scaffold_git.py` 并列，构成「三种 scaffold 来源」的三个独立模块

设计要点（见 `docs/decisions/0004-scaffold-from-cmd.md`）：
- shlex + argv 列表，不用 shell=True（防元字符被解释）
- stdio 继承父进程，让交互式脚手架（vite / next 等）正常工作
- cwd = target，不改写用户参数（用户自己写 `.` 作脚手架 target）
- shutil.which 预检给更友好的错误消息
"""
from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path


def _count_files(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and ".git" not in p.parts)


def run_scaffold_command(command: str, target: Path) -> int:
    """在 target 目录下执行脚手架命令；返回 target 下生成的文件数。

    Args:
        command: 完整的脚手架命令字符串（如 `npm create vite@latest . -- --template react`）
        target: 脚手架工作目录；不存在则创建

    Raises:
        SystemExit: 空命令 / shlex 解析失败 / 命令不存在 / 返回非 0
    """
    stripped = command.strip()
    if not stripped:
        raise SystemExit("错误：--scaffold-cmd 命令不能为空")

    try:
        argv = shlex.split(stripped)
    except ValueError as exc:
        raise SystemExit(f"错误：--scaffold-cmd 解析失败（引号不闭合？）：{exc}")

    if not argv:
        raise SystemExit("错误：--scaffold-cmd 命令解析后为空")

    program = argv[0]
    if shutil.which(program) is None:
        raise SystemExit(f"错误：未找到命令 `{program}`。请先安装后再用 --scaffold-cmd。")

    target.mkdir(parents=True, exist_ok=True)
    before = _count_files(target)

    # stdio 继承父进程（交互式脚手架需要）
    result = subprocess.run(argv, cwd=str(target))
    if result.returncode != 0:
        raise SystemExit(
            f"错误：--scaffold-cmd 退出码 {result.returncode}（命令：{stripped}）"
        )

    after = _count_files(target)
    return after - before


def ask_cmd_scaffold(target: Path) -> int:
    """Interactive：问脚手架命令，然后执行。返回文件数。"""
    import questionary
    cmd = questionary.text(
        "脚手架命令（例：npm create vite@latest . -- --template react）",
        validate=lambda v: bool(v.strip()) or "不能为空",
    ).ask()
    if cmd is None:
        raise SystemExit(1)
    return run_scaffold_command(cmd.strip(), target)
```

**安全约束（/cso 结论落地）**：
- ✅ `subprocess.run(argv, ...)` 默认 `shell=False`
- ✅ stdio 不捕获（`stdout/stderr` 不传，继承父进程）
- ✅ 失败时 `SystemExit` 中文消息，不静默 fallback

**关键抉择：`shutil.which` 预检位置**
- 只检查 `argv[0]`（程序名），不检查子命令
- 找不到时直接 `SystemExit`，不跑 `subprocess.run`，给用户更友好的错误

### Step 5：CLI 层接入（cli.py）

**修改**：`src/agent_harness/cli.py`

1. 加互斥组：
   ```python
   init_p = subs.add_parser("init", help="初始化 harness")
   init_p.add_argument("target", help="目标项目路径")
   init_p.add_argument("--config", help="JSON/TOML 配置文件")
   scaffold_group = init_p.add_mutually_exclusive_group()
   scaffold_group.add_argument("--scaffold", help="基于现有框架创建：本地目录路径 或 git URL（https/ssh/git@）")
   scaffold_group.add_argument("--scaffold-cmd", help="执行脚手架命令创建（例：'npm create vite@latest . -- --template react'）")
   init_p.add_argument("--scaffold-ref", help="--scaffold 为 git URL 时，指定 branch 或 tag")
   init_p.add_argument("--scaffold-subdir", help="--scaffold 为 git URL 时，只复制仓内该子目录")
   ```

2. 在 `_cmd_init` 加分支（在现有 `scaffold_src` 分支之前或之后）：
   ```python
   scaffold_cmd_str = getattr(args, "scaffold_cmd", None)
   scaffold_src = getattr(args, "scaffold", None)
   if scaffold_cmd_str:
       from ._scaffold_cmd import run_scaffold_command
       count = run_scaffold_command(scaffold_cmd_str, target)
       console.print(f"  [green]脚手架命令执行完成[/green]：{count} 个新文件")
   elif scaffold_src:
       # existing local / git branch
       ...
   elif is_interactive:
       ask_scaffold(target)
   ```

### Step 6：交互层接入（init_flow.py）

**修改**：`src/agent_harness/init_flow.py`

- `ask_scaffold` 的 `choices` 列表加第 4 项「是，通过脚手架命令创建」
- 加一个 `elif answer.startswith("是，通过脚手架"):` 分支，调 `_scaffold_cmd.ask_cmd_scaffold`
- **严格控制行数**：目标 ≤ 280 行（硬规则）
  - 只加 3-4 行代码
  - 必要时把 `ask_scaffold` 里的两个 if 合并压缩

### Step 7：跑全量测试（绿灯确认）

1. `python -m pytest tests/test_scaffold_cmd.py -v` → 新增测试全过
2. `make test` → 560 + N 条全过，无回归
3. `make check` → lint 无新警告
4. 模块长度检查：`wc -l src/agent_harness/_scaffold_cmd.py src/agent_harness/init_flow.py src/agent_harness/cli.py` → 全部 ≤ 280

### Step 8：文档同步（documentation-sync 规则）

1. **`docs/product.md`**：
   - 核心能力 #3 改成「支持 `--scaffold` 从现有技术框架创建（本地目录或远端 git）和 `--scaffold-cmd` 执行脚手架命令（如 `npm create vite@latest`）」
   - CLI 命令清单加新行：`harness init <target> --scaffold-cmd "<cmd>"`
   - 「持续演进」顶部追加一条，日期 2026-04-21
2. **`docs/runbook.md`**：init 章节补示例三段（本地 / git / cmd），列 5-7 个常见脚手架
3. **`docs/architecture.md`**：
   - 「CLI 层」加 `_scaffold_cmd.py`
   - 测试计数从 560 → 560+N
4. **`AGENTS.md`**：「常用命令」加一行 `harness init /path/to/repo --scaffold-cmd "..."`（注意 120 行硬规则）
5. **`docs/decisions/0004-scaffold-from-cmd.md`**：状态改 Accepted，补「实际实施」段
6. **`CHANGELOG.md`**（如存在）：[Unreleased] 加 Added 条

### Step 9：质量基线对比 + 穷举验证

**穷举验证脚本**（`/tmp/verify_scaffold_cmd.sh`）：
- 5 类场景：正常 / 边界（空命令、空白、引号）/ 错误（不存在、exit 1）/ 组合（与 --non-interactive / --config）/ 回归（`--scaffold <git_url>` 仍可用）
- 每项一行 ✅/❌，末尾汇总

### Step 10：提交 + 打 step tag

- 每步独立 commit：`feat(init): <描述> [plan step N]`
- 每步打 `lfg/step-N` 轻量 tag（回滚用）

## 依赖与顺序

```
Step 1 (/cso) → Step 2 (ADR Proposed) → Step 3 (RED) → Step 4 (_scaffold_cmd)
                                                          ↓
                                     Step 6 (init_flow) ← Step 5 (cli.py)
                                                          ↓
                                                      Step 7 (测试绿)
                                                          ↓
                                                      Step 8 (文档)
                                                          ↓
                                                   Step 9 (穷举验证)
                                                          ↓
                                                   Step 10 (commit)
```

Step 5 与 Step 6 可并行（都依赖 Step 4），但为减轻并发复杂度，按顺序做。

## 验证清单

实施完每步后跑：

| Step | 验证命令 | 预期 |
|---|---|---|
| 3 | `python -m pytest tests/test_scaffold_cmd.py -v` | 全部 FAIL（模块未实现） |
| 4 | `python -m pytest tests/test_scaffold_cmd.py::RunScaffoldCommandTests -v` | 全部 PASS |
| 5 | `python -m pytest tests/test_scaffold_cmd.py::CliMutualExclusionTests -v` | PASS |
| 6 | `python -m pytest tests/test_scaffold_cmd.py::InteractiveChoiceTests -v` | PASS |
| 7 | `make test` | 560 + N 全过 |
| 8 | `grep -r "scaffold-cmd" docs/ AGENTS.md` | 至少出现在 4 处 |
| 9 | 执行穷举脚本 | ✅ ≥ 10 / ❌ 0 |

## 非目标提醒

- 不重构 `_scaffold_git.py` 或 `copy_scaffold`
- 不实现 config 文件字段
- 不实现 `--scaffold-cmd-cwd` / `--scaffold-cmd-preset`
- 不改 `upgrade` / `doctor` / `sync`
