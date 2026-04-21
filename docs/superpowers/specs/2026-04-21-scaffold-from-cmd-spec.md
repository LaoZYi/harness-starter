# 规格：`harness init --scaffold-cmd` 支持脚手架命令

## 假设清单

- 假设：独立新 flag `--scaffold-cmd "<完整命令>"`——不复用 `--scaffold` 自动检测（命令字符串与本地路径/URL 无法可靠区分）
- 假设：用 `shlex.split` + `subprocess.run(argv, shell=False)`——防注入 + 对绝大多数脚手架够用
- 假设：stdio 透传到父终端（`stdin/stdout/stderr = None`）——让用户自己应付脚手架的交互式问答，避免捕获导致死锁
- 假设：命令的 cwd = target 目录；用户自己负责把脚手架的 target 参数写成 `.`（例：`npm create vite@latest . -- --template react`）
- 假设：`--scaffold` 与 `--scaffold-cmd` 由 argparse 互斥组强制互斥
- 假设：交互 `ask_scaffold` 加「是，通过脚手架命令创建」为第 4 选项
- 假设：**不**引入预设清单（vite-react / next-ts 等）——维护成本高、易过时
- 假设：测试里的脚手架命令用 shell 内建（`sh -c 'echo > file'`）和便携 POSIX 工具（`mkdir`、`touch`）模拟，CI 不依赖外网或 node/cargo 等

## 目标

### 要构建什么

给 `harness init` 新增第三种脚手架来源：

| 来源 | flag | 现状 | 本次 |
|---|---|---|---|
| 本地路径 | `--scaffold <path>` | ✅ 支持 | ✅ 保持 |
| 远端 git URL | `--scaffold <git_url>` + `--scaffold-ref/subdir` | ✅ 支持（ADR 0003）| ✅ 保持 |
| 脚手架命令 | `--scaffold-cmd "<cmd>"` | ❌ | ✅ **新增** |

### 为什么要构建

JavaScript / Python / Rust / Ruby 等生态的主流初始化方式是一条官方/社区脚手架命令，如：

```bash
npm create vite@latest my-app -- --template react
npx create-next-app@latest my-app
pnpm create svelte my-app
django-admin startproject mysite
rails new myapp --database=postgresql
cargo new my-app
poetry new my-app
```

现状下用户必须先手工在别处跑脚手架生成目录，再 `harness init <生成目录>`，两步走。扩展后：

```bash
harness init ./my-app --scaffold-cmd "npm create vite@latest . -- --template react"
```

一步到位——脚手架在 target 下生成文件，harness 接手后续 `init`。

### 目标用户

- 使用主流前端/后端脚手架（vite / next / remix / nuxt / django / rails / cargo / poetry / dotnet 等）的开发者
- 在团队约定的脚手架命令上叠加 harness agent 协作基础设施的场景

### 成功标准

- 传合法命令 → 在 target 下执行 → 脚手架文件生成 → 继续 harness init 后续流程（AGENTS.md、.claude/、.agent-harness/ 等注入）
- 命令不存在 / 命令失败 / 空命令 / 解析失败 均有清晰中文报错
- 现有 `--scaffold <path>` / `--scaffold <git_url>` 行为无回归

## 命令

- 测试：`make test`
- 检查：`make check`
- 启动：`harness init <target> --scaffold-cmd "<cmd>"`
- 配套：`--scaffold` 与 `--scaffold-cmd` 互斥

## 项目结构

### 新增

| 路径 | 职责 |
|---|---|
| `src/agent_harness/_scaffold_cmd.py` | 新模块：`run_scaffold_command()` + `ask_cmd_scaffold()` + 失败路径 |
| `tests/test_scaffold_cmd.py` | 新测试：单元 + 端到端 CLI，覆盖正常 / 边界 / 错误 / 互斥 / 回归 |
| `docs/superpowers/specs/2026-04-21-scaffold-from-cmd-{spec,plan}.md` | 本文档 + 计划 |
| `docs/decisions/0004-scaffold-from-cmd.md` | ADR（轻量）：为什么独立 flag + 为什么 argv 不 shell=True |

### 修改

| 路径 | 改什么 |
|---|---|
| `src/agent_harness/cli.py` | 加 `--scaffold-cmd`、与 `--scaffold` 组成互斥组；在 `_cmd_init` 加 `scaffold_cmd` 分支 |
| `src/agent_harness/init_flow.py` | `ask_scaffold` 加第 4 选项（跳 `_scaffold_cmd.ask_cmd_scaffold`），**尽量控制在 280 行以内** |
| `docs/product.md` | 核心能力 #3 扩写，加 `--scaffold-cmd` 说明；CLI 命令清单加新行；「持续演进」追加一条 |
| `docs/runbook.md` | init 章节补 `--scaffold-cmd` 示例和常见脚手架 |
| `docs/architecture.md` | 模块清单加 `_scaffold_cmd.py`；测试计数从 560 加上本次新增 |
| `AGENTS.md` | 「常用命令」段补 `harness init ... --scaffold-cmd "..."` 示例（不超过 120 行硬规则） |

## 代码风格

### 新模块 `_scaffold_cmd.py` 约定

- 顶部 docstring 说明「为什么单独成模块」（参照 `_scaffold_git.py` 风格）
- `from __future__ import annotations`
- 仅用 stdlib（`shlex` + `subprocess` + `shutil` + `pathlib`）
- 函数签名：
  ```python
  def run_scaffold_command(command: str, target: Path) -> int: ...
  def ask_cmd_scaffold(target: Path) -> int: ...  # 交互入口
  ```
  `run_scaffold_command` 返回 target 下新生成的文件计数（便于 console 展示），参照 `copy_scaffold` 的契约。
- 失败统一用 `SystemExit("错误：<中文说明>")`——与现有 `copy_scaffold` / `_scaffold_git` 一致
- 不在模块顶层 import `questionary` / `rich`（延迟 import，与 `_scaffold_git` 一致）
- `subprocess.run` 参数：`shell=False`、`stdin=None`、`stdout=None`、`stderr=None`（即继承父进程）——不捕获，让交互式脚手架正常跑；只读 `returncode`

### 测试风格

- 脚手架命令用可控 shell 指令模拟，避免依赖 node / cargo：
  - 正常路径：`sh -c 'echo hello > README.md && mkdir -p src && echo code > src/main.py'`
  - 失败路径：`sh -c 'echo boom >&2; exit 1'` → `returncode != 0`
  - 不存在：`this-cmd-does-not-exist`
- 互斥测试走 `subprocess.run([sys.executable, "-m", "agent_harness", "init", ..., "--scaffold", "x", "--scaffold-cmd", "y"])`，断言 returncode != 0 且 stderr 含互斥提示
- 引用 `_git_helper.isolated_git_env()` 仅在端到端 init 时需要（避免全局 gitconfig 污染 harness 的自动 git commit）

## 测试策略

### 必测场景（R-ID 三元映射）

| R-ID | 场景 | 类型 | 映射到 |
|---|---|---|---|
| R-001 | `run_scaffold_command("sh -c 'echo x > README.md'", <target>)` 创建 target 且内含 README.md | 正常 | 实施 step A |
| R-001 | 命令含 `--` 分隔符（vite 风格）能被 shlex 正确拆分 | 正常 | 实施 step A |
| R-001 | 命令含带引号的参数（`"my app"`）能正确保留空格 | 正常 | 实施 step A |
| R-002 | CLI 同时传 `--scaffold` 和 `--scaffold-cmd` → argparse 报错 returncode != 0 | 错误 | 实施 step C（cli.py 互斥组）|
| R-003 | `ask_scaffold` 交互逻辑存在「脚手架命令」选项字符串（用 unittest mock 断言） | 正常 | 实施 step D |
| R-004 | `run_scaffold_command("sh -c 'exit 1'", <target>)` → `SystemExit` 且消息含 `returncode` 和命令 | 错误 | 实施 step B |
| R-004 | `run_scaffold_command("this-cmd-does-not-exist", <target>)` → `SystemExit` 且消息含 "未找到" 或 "command not found" | 错误 | 实施 step B（shutil.which 预检）|
| R-005 | `run_scaffold_command("sh -c 'echo ok'; rm -rf /", <target>)` ——整个字符串走 shlex，分号后部分成**字面参数**传给 sh（即 sh 会被当成程序名跟一堆字面参数），`rm -rf /` **不会执行** | 错误/安全 | 实施 step B |
| R-006 | 空字符串 / 只含空白 → `SystemExit` 且消息含 "命令不能为空" | 边界 | 实施 step B |
| R-006 | 引号不闭合（`"unterminated`）→ shlex 抛 `ValueError`，我们捕获并 `SystemExit` | 边界 | 实施 step B |
| R-007 | CLI 端到端：`harness init <target> --scaffold-cmd "sh -c 'echo > README.md'" --non-interactive --config ...` 成功 init，AGENTS.md + README.md 并存 | 集成 | 实施 step E |
| R-009 | 现有 `test_scaffold_git.py` / `test_cli.py::ScaffoldTests` 继续通过 | 回归 | 全局 |

### 不测

- 真实 `npm create` / `django-admin` 等外部命令（CI 不能保证 node/django 存在，用 sh 模拟）
- questionary 的终端 UI 交互（沿用现有 `ask_scaffold` 未做端到端 UI 测的惯例）
- Windows 原生行为（项目硬依赖 POSIX / WSL）

## 边界

### 始终做

- shlex 解析失败 / 空命令 / 命令不存在 / 命令返回非 0 — 四类失败都清晰中文报错
- 子进程继承 stdio（让 npm init 等交互式脚手架正常跑）
- target 不存在时 `mkdir(parents=True, exist_ok=True)`（与 `copy_scaffold_from_git` 一致）
- 命令执行前日志行 `▶ 执行脚手架命令：<cmd>`（便于用户追踪）

### 绝不做

- **不**用 `shell=True`（防注入 + 可预测的参数切分语义）
- **不**改写用户命令的参数（不自动插 `.` 等 target 参数）
- **不**捕获子进程 stdout/stderr（避免交互式死锁）
- **不**引入预设清单 / 模板注册表（`--scaffold-preset` 这类扩展留给未来需求驱动）
- **不**在 `--scaffold` 自动检测里加命令识别（独立 flag 更明确）
- **不**对命令做白名单（用户的机器、用户的命令，harness 不做防用户自伤）

## 与现有规则的关系

- **与 `.claude/rules/safety.md`**：输入信任边界——`command` 来自 CLI 参数，用 argv 执行而非 shell，天然消解命令注入担忧；文档里显式说明 shell 元字符被当字面量
- **与 `lessons.md::2026-04-20 测试脚手架起 git subprocess 必须 env 隔离用户全局配置`**：端到端 CLI 测试中 harness 的 auto git commit 也要走 `isolated_git_env()`
- **与 AGENTS.md「每个 Python 模块不超过 280 行」**：`init_flow.py` 当前 278 行——本次只加 1 行分支字符串 + 1 个 import + 1 处调用；超过时拆到 `_scaffold_cmd.ask_cmd_scaffold` 承载（已按此规划）
- **与 `lessons.md::2026-04-13 抽 SSOT 时必须清单化所有下游消费方`**：`--scaffold` 逻辑有 2 个下游（`_cmd_init` 和 `ask_scaffold`）——新逻辑也必须两处都接入

## 非目标

- 不改 `upgrade` / `doctor` / `sync` / `doctor` / `stats` 等其他命令
- 不改现有 `_scaffold_git.py` / `copy_scaffold` 行为（只在 CLI 路由层并列）
- 不添加 config 文件 schema 字段（保持 CLI 驱动，和 `--scaffold` 对齐）
- 不实现 `--scaffold-cmd-cwd` 等参数（cwd = target 是唯一合理选择）
- 不做「脚手架生成后自动把产物移到 target 根」的智能整理（用户命令应写 `.` 作 target 参数）
