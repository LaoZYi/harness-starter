# 实施计划：`harness init --scaffold` 支持远端 git 仓库

对应规格：`docs/superpowers/specs/2026-04-21-scaffold-from-git-spec.md`
分支：`feat/scaffold-from-git-20260421`
基线：`6b37b54`

## R-ID 映射

| R-ID | 内容 | 对应 Step |
|---|---|---|
| R-001 | `is_git_url()` 自动检测 | Step 3, Step 4 |
| R-002 | `--scaffold-ref` 支持 | Step 3, Step 4, Step 5 |
| R-003 | `--scaffold-subdir` 支持 | Step 3, Step 4, Step 5 |
| R-004 | `copy_scaffold_from_git()` | Step 4 |
| R-005 | 5 类失败中文报错 | Step 4 |
| R-006 | `ask_scaffold` 新增分支 | Step 6 |
| R-007 | 测试覆盖 | Step 3（RED） |
| R-008 | 文档 + 计数同步 | Step 8 |

## 步骤清单

### Step 1：/cso 快速扫（生产项目预警）

`has_production=true`，读 `.agent-harness/project.json` 确认，针对本次任务扫：

| 风险点 | 缓解 |
|---|---|
| **任意代码执行**（git URL 被用户控制，clone 过程不执行用户代码——仅落盘） | `git clone` 本身不执行钩子；克隆后**不**运行目标仓的 pre/post-checkout hook（默认行为，不需特殊配置） |
| **路径遍历**（`--scaffold-subdir` 含 `../`）| 在 `copy_scaffold_from_git` 里校验 `subdir` 不含 `..` 和绝对路径字符，`os.path.commonpath` 校验解析后仍在 tmpdir 内 |
| **SSRF**（恶意 URL 指向内网）| 不做——用户本人触发 + 走 `git` 二进制（git 本身会按 URL scheme 处理），不是 server 端接收 URL |
| **命令注入**（URL / ref / subdir 含 shell 特殊字符）| `subprocess.run([list])` 不走 shell，无注入风险；`ref` 参数走 `--branch`，`subdir` 只用作路径拼接 |
| **敏感信息日志**（URL 若含 `user:pass@` 嵌入）| 报错消息不直接回显 URL，只说"克隆失败：<git stderr>"；git 自己可能打印 URL，这个委托给 git 默认行为 |

**结论**：把「subdir 路径遍历」写进计划的**安全约束**段（Step 4 实现时必须加校验）。其他风险当前可控。

### Step 2：写 ADR 0003（Proposed）

**文件**：`docs/decisions/0003-scaffold-from-git.md`

**骨架**：
- Status: Proposed
- Context: 现 `--scaffold` 只接本地路径；团队把模板托管在 git 后多一步手动 clone
- Decision: 扩展单 flag（Option A）+ shallow clone + 委托鉴权给 git config
- Alternatives: Option B 独立 flag / 全量 clone / 引入 GitPython / 自己实现 https 鉴权（都否）
- Consequences: +1 模块 +2 flags +7 测试 +1 ADR

### Step 3：写 RED 测试（tests/test_scaffold_git.py）

覆盖 R-001 / R-002 / R-003 / R-004 / R-005：

```python
class IsGitUrlTests:  # R-001, 5 条
    - https / git@ / ssh:// / git:// / 以 .git 结尾 / 本地路径 / 相对路径

class CopyScaffoldFromGitTests:  # R-004 + R-002 + R-003, 5 条
    - 端到端：bare repo → clone → copy；target 含文件、不含 .git
    - ref=分支名 → checkout 对应分支
    - subdir=子目录 → 只复制该子目录
    - ref=不存在 → SystemExit 含 "ref"
    - subdir=不存在 → SystemExit 含 "子目录"

class GitNotAvailableTests:  # R-005，1 条
    - mock shutil.which("git") → None → SystemExit 含 "git"

class SubdirPathTraversalTests:  # 安全（Step 1 结论），1 条
    - subdir=".." → SystemExit 阻止
```

**验证**：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_scaffold_git -v` → 全 RED

### Step 4：实现 `src/agent_harness/_scaffold_git.py`（R-001 / R-004 / R-005 GREEN）

```python
"""Clone a git repo and use it as scaffold source."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_URL_PREFIXES = ("http://", "https://", "git@", "ssh://", "git://")


def is_git_url(value: str) -> bool:
    if any(value.startswith(p) for p in _URL_PREFIXES):
        return True
    if value.endswith(".git"):
        return True
    return False


def copy_scaffold_from_git(url: str, target: Path, *,
                            ref: str | None = None,
                            subdir: str | None = None) -> int:
    if shutil.which("git") is None:
        raise SystemExit("错误：未找到 git 命令。请先安装 git。")
    if subdir and (".." in subdir.split("/") or Path(subdir).is_absolute()):
        raise SystemExit(f"错误：--scaffold-subdir 不能含 `..` 或绝对路径：{subdir}")

    from .init_flow import copy_scaffold  # 复用本地复制逻辑

    with tempfile.TemporaryDirectory(prefix="harness-scaffold-") as tmp:
        clone_dir = Path(tmp) / "clone"
        cmd = ["git", "clone", "--depth", "1"]
        if ref:
            cmd += ["--branch", ref]
        cmd += [url, str(clone_dir)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            stderr = r.stderr.strip()
            if ref and ("Remote branch" in stderr or "not found" in stderr):
                raise SystemExit(f"错误：git ref `{ref}` 不存在。stderr: {stderr}")
            raise SystemExit(f"错误：git clone 失败。\n  URL: {url}\n  stderr: {stderr}")

        source = clone_dir
        if subdir:
            source = clone_dir / subdir
            source_resolved = source.resolve()
            clone_resolved = clone_dir.resolve()
            # 双保险：路径遍历检测
            if os.path.commonpath([str(source_resolved), str(clone_resolved)]) != str(clone_resolved):
                raise SystemExit(f"错误：--scaffold-subdir 逃逸 clone 目录：{subdir}")
            if not source.is_dir():
                raise SystemExit(f"错误：clone 仓中不存在子目录：{subdir}")

        return copy_scaffold(source, target)
```

**验证**：跑 Step 3 里 RED 测试 → 全 GREEN（除了 `SubdirPathTraversalTests` 确认 pass）

### Step 5：接入 CLI（R-002 / R-003 GREEN）

**文件**：`src/agent_harness/cli.py`

改动：
- `init_p` 新增两 flag：`--scaffold-ref`, `--scaffold-subdir`
- `_cmd_init` 在 `scaffold_src` 处理点：检测是 URL → 调 `copy_scaffold_from_git(...)`；否则保留 `copy_scaffold`

```python
scaffold_src = getattr(args, "scaffold", None)
if scaffold_src:
    from ._scaffold_git import is_git_url, copy_scaffold_from_git
    if is_git_url(scaffold_src):
        copy_scaffold_from_git(
            scaffold_src, target,
            ref=getattr(args, "scaffold_ref", None),
            subdir=getattr(args, "scaffold_subdir", None),
        )
        console.print(f"  [green]已从 git 拉取并复制框架代码[/green]：{scaffold_src}")
    else:
        copy_scaffold(Path(scaffold_src).expanduser(), target)
        console.print(f"  [green]已复制框架代码[/green]：{Path(scaffold_src).name}")
else:
    ask_scaffold(target)
```

**验证**：加一条 CLI 端到端测试（bare repo → `harness init --scaffold <bare_url> ...`）

### Step 6：交互分支（R-006 GREEN）

**文件**：`src/agent_harness/init_flow.py::ask_scaffold`

改动：
- 选项由 2 扩展到 3：「否，空项目」/「是，本地框架路径」/「是，从远端 git 仓库拉取」
- 选「远端 git」→ `questionary.text("git 仓库 URL")` + `questionary.text("ref（空=默认分支）")` + `questionary.text("子目录（空=仓根）")`
- 调 `copy_scaffold_from_git`

**验证**：不加端到端测试（现有 `ask_scaffold` 也没单测），靠 Step 5 的 CLI 覆盖

### Step 7：全量测试 + dogfood

```bash
make test  # 543 + N
make check # dogfood 无漂移（本次不动 template）
```

### Step 8：文档同步（R-008）

- `CHANGELOG.md` [Unreleased] 加 Added 段
- `docs/runbook.md` init 说明加 git URL 示例
- `docs/architecture.md` 测试计数 543 → +N；模块清单加 `_scaffold_git.py`
- `docs/product.md` 功能列表新增一条勾选

### Step 9：ADR 升级 Accepted + make ci

- ADR 0003 改 Status: Accepted
- `make ci` 全绿

### Step 10：快速评审（/multi-review 2 审查员：正确性 + 安全）+ commit

## 依赖关系

```
Step 1 (/cso)
  ↓
Step 2 (ADR Proposed)
  ↓
Step 3 (RED tests)
  ↓
Step 4 (_scaffold_git.py)
  ↓
Step 5 (cli.py) ⟂ Step 6 (ask_scaffold)  [可并行]
  ↓
Step 7 (全测 + check)
  ↓
Step 8 (docs)
  ↓
Step 9 (ADR Accepted + make ci)
  ↓
Step 10 (review + commit)
```

## 风险与回滚

- **风险 1**：网络不可达机器跑测试——全部用本地 bare repo 模拟，无外网依赖
- **风险 2**：`git clone --branch` 对 commit SHA 不生效（`--branch` 只接 branch/tag，不接任意 commit）→ 计划内显式限制：`--scaffold-ref` 文档说明「支持 branch/tag，不支持任意 commit SHA」，避免承诺做不到的事
- **风险 3**：tmpdir 权限问题——用 `tempfile.TemporaryDirectory()` context manager，由 stdlib 保证跨平台
- **回滚**：每步独立 commit + tag `lfg/step-N`

## 历史教训引用

- `lessons.md 2026-04-20 测试脚手架起 git subprocess 必须 env 隔离用户全局配置` → Step 3 测试所有 `subprocess.run git` 必须带 `env=isolated_git_env()`
- `lessons.md 2026-04-20 改模板文本前必须 grep 现有测试是否锁定具体字符串` → Step 8 改文档前 grep `527|529|543` 全仓
- `lessons.md 2026-04-13 抽 SSOT 时必须清单化所有下游消费方` → 已在 spec 列出 `copy_scaffold` 的 2 个下游（CLI / ask_scaffold），Step 5/6 都接

## 计划校验（/plan-check 8 维度自查）

### 1. 需求覆盖
- 8 条 R-ID 全映射到 Step（见顶部映射表）

### 2. 原子性
- 每 Step 2-5 分钟粒度
- Step 5 / Step 6 可并行；其他严格拓扑序

### 3. 依赖排序
- /cso → ADR → RED → 实现 → CLI/交互 → 全测 → 文档 → ADR accepted → review
- 无循环

### 4. 文件作用域
- 新 3 / 改 6（见规格 "项目结构" 段）

### 5. 可验证性
- 每 Step 有具体测试命令或 shell 命令
- 总闸：make ci

### 6. 上下文适配
- 引用 3 条 lessons
- 遵循零依赖原则（不引 GitPython）

### 7. 缺口检测
- /adr 需要（R-007） ✓ Step 2
- /source-verify 不需要（git clone --depth 1 + --branch 是标准用法，不是编 API）
- /agent-design-check 不需要（非多 agent）
- /cso ✓ Step 1（has_production=true）

### 8. Nyquist 合规
- 采样：8 R-ID × 2+ 测试/ID + make ci + dogfood = 20+ 验证信号
