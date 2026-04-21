"""Clone a remote git repo and use it as `harness init --scaffold` source.

为什么单独成模块：`init_flow.py` 已满（交互流程 + 组装 answers），git 拉取逻辑
涉及独立关注点（子进程、临时目录、路径安全校验）。拆出来让 `init_flow` 保持单
责任；也方便测试 mock `shutil.which` 等系统调用。

设计要点（见 `docs/decisions/0003-scaffold-from-git.md`）：

- 纯 stdlib，不引 GitPython
- shallow clone（`--depth 1`）省流量
- 鉴权委托给用户 git 配置（SSH key / credential helper）
- ref 只承诺 branch / tag（`git clone --branch` 能力上限），不接任意 commit SHA
- subdir 双保险校验：拒绝 `..` / 绝对路径 + `commonpath` 检测逃逸
- clone 到 `tempfile.TemporaryDirectory`，复制后整目录删除（不在 target 留 .git）
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_URL_PREFIXES = ("http://", "https://", "git@", "ssh://", "git://")


def is_git_url(value: str) -> bool:
    """Return True iff `value` looks like a git URL.

    规则：
    - 以 `http://` / `https://` / `git@` / `ssh://` / `git://` 开头
    - 或以 `.git` 结尾（本地镜像仓）
    """
    if any(value.startswith(p) for p in _URL_PREFIXES):
        return True
    if value.endswith(".git"):
        return True
    return False


def _assert_safe_subdir(subdir: str) -> None:
    """拒绝路径遍历：`..` 分段 + 绝对路径。"""
    if Path(subdir).is_absolute():
        raise SystemExit(f"错误：--scaffold-subdir 不能是绝对路径：{subdir}")
    parts = subdir.replace("\\", "/").split("/")
    if ".." in parts:
        raise SystemExit(f"错误：--scaffold-subdir 不能含 `..` 分段：{subdir}")


def copy_scaffold_from_git(
    url: str,
    target: Path,
    *,
    ref: str | None = None,
    subdir: str | None = None,
) -> int:
    """从 git URL 拉取并复制为 scaffold。返回复制的文件数。

    Args:
        url: git URL（https / ssh / git@ / 本地 `.git` 路径均可）
        target: 目标项目目录（若不存在由 `copy_scaffold` 创建）
        ref: 可选 branch / tag；None 表示仓库默认分支
        subdir: 可选仓内子目录；None 表示仓根
    """
    if shutil.which("git") is None:
        raise SystemExit("错误：未找到 git 命令。请先安装 git 再使用 --scaffold <git_url>。")

    if subdir:
        _assert_safe_subdir(subdir)

    # 延迟导入，避免 init_flow ↔ _scaffold_git 循环
    from .init_flow import copy_scaffold

    with tempfile.TemporaryDirectory(prefix="harness-scaffold-") as tmp:
        clone_dir = Path(tmp) / "clone"
        cmd = ["git", "clone", "--depth", "1"]
        if ref:
            cmd += ["--branch", ref]
        cmd += [url, str(clone_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            if ref and (
                "Remote branch" in stderr
                or "not found" in stderr
                or "could not find remote ref" in stderr.lower()
            ):
                raise SystemExit(
                    f"错误：git ref `{ref}` 不存在于远端。\n  URL: {url}\n  stderr: {stderr}"
                )
            raise SystemExit(
                f"错误：git clone 失败。\n  URL: {url}\n  ref: {ref or '<default>'}\n  stderr: {stderr}"
            )

        source = clone_dir
        if subdir:
            candidate = (clone_dir / subdir).resolve()
            clone_resolved = clone_dir.resolve()
            try:
                common = os.path.commonpath([str(candidate), str(clone_resolved)])
            except ValueError:
                # 跨盘等极端情况
                common = ""
            if common != str(clone_resolved):
                raise SystemExit(
                    f"错误：--scaffold-subdir 解析后逃逸了 clone 目录：{subdir}"
                )
            if not candidate.is_dir():
                raise SystemExit(f"错误：clone 仓中不存在子目录：{subdir}")
            source = candidate

        return copy_scaffold(source, target)


def ask_git_scaffold(target: Path) -> int:
    """Interactive path：问 URL / ref / subdir，然后 clone + 复制。返回文件数。"""
    import questionary
    url = questionary.text(
        "git 仓库 URL（https / ssh / git@）",
        validate=lambda v: bool(v.strip()) or "不能为空",
    ).ask()
    if url is None:
        raise SystemExit(1)
    ref = questionary.text("git ref（branch / tag，空=默认分支）", default="").ask()
    subdir = questionary.text("仓内子目录（空=仓根）", default="").ask()
    return copy_scaffold_from_git(
        url.strip(),
        target,
        ref=(ref.strip() or None) if ref is not None else None,
        subdir=(subdir.strip() or None) if subdir is not None else None,
    )
