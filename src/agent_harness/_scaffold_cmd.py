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
    """统计 root 下常规文件数（不含目录、不含符号链接目标）。"""
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file())


def run_scaffold_command(command: str, target: Path) -> int:
    """在 target 目录下执行脚手架命令；返回 target 下新增的文件数。

    Args:
        command: 完整脚手架命令字符串（如 `npm create vite@latest . -- --template react`）
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
        raise SystemExit(
            f"错误：--scaffold-cmd 解析失败（引号是否闭合？）：{exc}"
        )

    if not argv:
        raise SystemExit("错误：--scaffold-cmd 命令解析后为空")

    program = argv[0]
    if shutil.which(program) is None:
        raise SystemExit(
            f"错误：未找到命令 `{program}`。请先安装后再使用 --scaffold-cmd。"
        )

    target.mkdir(parents=True, exist_ok=True)
    before = _count_files(target)

    # stdio 继承父进程——交互式脚手架（vite / next 等）需要
    # shell=False（默认）——防 shell 元字符被解释
    result = subprocess.run(argv, cwd=str(target))
    if result.returncode != 0:
        raise SystemExit(
            f"错误：--scaffold-cmd 退出码 {result.returncode}（命令：{stripped}）"
        )

    after = _count_files(target)
    return max(after - before, 0)


def ask_cmd_scaffold(target: Path) -> int:
    """Interactive：问脚手架命令，然后执行。返回新增文件数。"""
    import questionary

    cmd = questionary.text(
        "脚手架命令（例：npm create vite@latest . -- --template react）",
        validate=lambda v: bool(v.strip()) or "不能为空",
    ).ask()
    if cmd is None:
        raise SystemExit(1)
    return run_scaffold_command(cmd.strip(), target)
