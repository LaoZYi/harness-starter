# 规格：`harness init --scaffold` 支持远端 git 仓库

## 假设清单

- 假设：单 flag 自动检测 `--scaffold <local_or_url>`——向后兼容 + UI 简洁
- 假设：shallow clone（`git clone --depth 1`）减少网络开销
- 假设：鉴权走用户 git 配置（SSH key / credential helper），不支持 CLI 传 token
- 假设：clone 到 `tempfile.mkdtemp()`，复制到 target 后清理整个 tmpdir
- 假设：失败清晰中文报错，不 fallback 到空项目
- 假设：测试用本地 bare repo 模拟远端——CI 无外网可用

## 目标

### 要构建什么

让 `harness init --scaffold <value>` 的 `<value>` 可以是：

| 形式 | 现状 | 本次 |
|---|---|---|
| 本地绝对 / 相对路径（如 `../my-framework`） | ✅ 支持 | ✅ 保持 |
| HTTPS git URL（如 `https://github.com/foo/bar.git`） | ❌ | ✅ 新增 |
| SSH git URL（如 `git@github.com:foo/bar.git`） | ❌ | ✅ 新增 |
| `git://` / `ssh://` 协议 | ❌ | ✅ 新增 |

同时新增两个辅助 flag（CLI + 交互均支持）：
- `--scaffold-ref <branch|tag|commit>` 钉 git ref（默认 default branch）
- `--scaffold-subdir <relpath>` 只用克隆仓的某子目录作为模板源（默认仓根，适配 monorepo 模板仓）

### 为什么要构建

当前把团队框架托管到 git 后，用户必须先手动 clone 再 `harness init --scaffold ./cloned-path`，三步走。远端拉取后可一步到位：

```
harness init ./new-project --scaffold https://github.com/team/framework.git
```

### 目标用户

- 把项目模板托管在 GitHub / GitLab / 内部 git 服务的团队
- CI 自动化场景（从 git 拉模板 → 一键 init）

### 成功标准

- 传 git URL 给 `--scaffold` → 自动 clone → 复制 → 清理 tmpdir，全流程无 `.git` 残留在 target
- 传本地路径 → 行为不变（回归 2 条现有 `ScaffoldTests`）
- 5 类失败都有清晰中文报错

## 命令

- 测试：`make test`
- 检查：`make check`
- 启动：`harness init <target> --scaffold <value> [--scaffold-ref <ref>] [--scaffold-subdir <path>]`

## 项目结构

### 新增

| 路径 | 职责 |
|---|---|
| `src/agent_harness/_scaffold_git.py` | 新模块：`is_git_url()` / `copy_scaffold_from_git()` / 失败路径 |
| `tests/test_scaffold_git.py` | 新测试：本地 bare repo 模拟远端，覆盖正常 + ref + subdir + 4 类失败 |
| `docs/superpowers/specs/2026-04-21-scaffold-from-git-{spec,plan}.md` | 本文档 + 计划 |
| `docs/decisions/0003-scaffold-from-git.md` | ADR（轻量）：为什么选单 flag 自动检测 + 不支持 token |

### 修改

| 路径 | 改什么 |
|---|---|
| `src/agent_harness/init_flow.py` | `ask_scaffold` 加「是，从远端 git 仓库拉取」分支 + 调用新模块 |
| `src/agent_harness/cli.py` | 加 `--scaffold-ref` + `--scaffold-subdir` + 统一分派 local vs git |
| `CHANGELOG.md` | [Unreleased] 追加 Added 条 |
| `docs/runbook.md` | init 说明补 git URL 示例 |
| `docs/architecture.md` | 测试计数 543 → +N + 模块清单加 `_scaffold_git.py` |
| `docs/product.md` | 功能列表勾选新条目 |

## 代码风格

### 新模块 `_scaffold_git.py` 约定

- 顶部 docstring 说明「为什么单独成模块」
- `from __future__ import annotations`
- 仅用 stdlib（`subprocess` + `tempfile` + `shutil` + `re`）
- 函数签名：
  ```python
  def is_git_url(value: str) -> bool: ...
  def copy_scaffold_from_git(
      url: str, target: Path, *,
      ref: str | None = None,
      subdir: str | None = None,
  ) -> int: ...
  ```
- 失败统一用 `SystemExit("错误：<中文说明>")`——与现有 `copy_scaffold` 一致
- 不在模块顶层 import `questionary` / `rich`（保持纯运行时工具）

### 测试风格

- 用 `git init --bare <path>` 建本地 bare repo 当「远端」
- 用 `git init <path>` + `git add` + `git commit` + `git push <bare>` 推内容
- 所有 `subprocess.run` 带 `env=isolated_git_env()`（Issue gl#21 教训）

## 测试策略

### 必测场景

| R-ID | 场景 | 类型 |
|---|---|---|
| R-001 | `is_git_url("https://github.com/foo/bar.git")` → True | 正常 |
| R-001 | `is_git_url("git@github.com:foo/bar.git")` → True | 正常 |
| R-001 | `is_git_url("/absolute/local/path")` → False | 正常 |
| R-001 | `is_git_url("../relative/path")` → False | 正常 |
| R-001 | `is_git_url("path/ending/in/.git")` → True（以 `.git` 结尾） | 边界 |
| R-002 | 传 `ref="main"` 到本地 bare repo，能 checkout 对应分支 | 正常 |
| R-002 | 传 `ref="nonexistent-branch"` → SystemExit 且消息含 "ref" | 错误 |
| R-003 | 传 `subdir="templates"` 只复制该子目录 | 正常 |
| R-003 | 传 `subdir="nonexistent-dir"` → SystemExit 且消息含 "子目录" | 错误 |
| R-004 | 端到端：clone bare → copy → target 含期望文件、**不含** .git | 正常 |
| R-005 | mock `shutil.which("git")` 返回 None → SystemExit 且消息含 "git" | 错误 |
| R-005 | 传不存在的 URL（如 `https://nonexistent.invalid/x.git`） → SystemExit（`--depth 1` 快速失败） | 错误 |
| 回归 | 现有 `ScaffoldTests` 2 条 | 回归 |
| CLI | `harness init --scaffold <bare_url> --non-interactive ...` 成功 init | 端到端 |

### 不测

- 实际外网 clone（测试用本地 bare repo）
- 鉴权场景（依赖用户 git config，不是本命令的责任）
- questionary 交互路径（现有 `ask_scaffold` 已无端到端测试，保持不变）

## 边界

### 始终做

- 所有 `git` 调用走 `subprocess.run` + 显式 `check=True`，输出 `capture_output=True` 防刷屏
- 失败消息带具体原因（"git 未安装" / "克隆失败" / "ref 不存在" 等）
- clone tmpdir 用 `tempfile.TemporaryDirectory()` 的 context manager 保证清理

### 绝不做

- **不**引入第三方 git 库（如 GitPython）——零依赖原则
- **不**在 target 目录留 `.git`（现有 `SCAFFOLD_SKIP` 已跳 `.git`，且 tmpdir 整体删除）
- **不**缓存克隆结果
- **不**静默 fallback 到空项目
- **不**处理 token / password 这类鉴权——委托给用户 git 配置

## 与现有规则的关系

- **与 `.claude/rules/safety.md`**：输入信任边界——`value` 来自 CLI 参数，`is_git_url` 检测不含路径遍历；subdir 参数要防 `../` 逃逸
- **与 `lessons.md::2026-04-20 测试脚手架起 git subprocess 必须 env 隔离用户全局配置`**：测试里的 git 调用必须用 `isolated_git_env()`
- **与 `lessons.md::2026-04-13 抽 SSOT 时必须清单化所有下游消费方`**：`copy_scaffold` 目前的 2 个下游（CLI / ask_scaffold）都需要接入新逻辑，一处漏就白改

## 非目标

- 不改 `upgrade` / `doctor` 等其他命令
- 不改 bundled templates 的结构
- 不新增配置文件 schema（`config.json` 不加 `scaffold_git` 字段；保持 CLI 驱动）
