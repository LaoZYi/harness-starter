# Spec：/squad MVP — tmux 常驻多 agent 协作（阶段 1）

> 灵感来源：[overstory](https://github.com/jayminwest/overstory)（AgentRuntime + capability 分级）、[claude-squad](https://github.com/smtg-ai/claude-squad)（tmux + worktree 双隔离 + checkout 模式）
> 日期：2026-04-12 | 基线：`827ed61` | 建议分支：`feat/squad-mvp` | 对应 Issue：待创建

## 背景

现有 `/dispatch-agents` 是**一次性 map-reduce**：主 agent 并行派任务 → 等汇总 → 销毁子 agent。**缺失能力**：
1. 无常驻 agent（无法持续对话、无法追加任务）
2. 无双向通信（子 agent 不能反问、不能互相协调）
3. 无实时观察（用户看不到每个 agent 在做什么）
4. 无角色分权（所有 agent 都是通用工人，容易越权乱改）

**本阶段目标**：用最小改动提供"常驻多 agent + 实时可见 + 角色分权"能力，验证需求是否真实存在。**暂不追求**完整的双向消息总线和 AI 冲突解决。

## 目标（阶段 1 = MVP）

1. 新技能 `/squad`：一键在 tmux 里开 N 个带独立 worktree 的 Claude Code 进程
2. 每个 worker 按 `capability` 获得**运行时强制**的工具权限（scout=RO / builder=RW / reviewer=RO）
3. 共享状态文件（JSONL）让 coordinator 能看到每个 worker 的进度和产出
4. 提供 `squad status` / `squad attach <name>` / `squad stop <name>` 三个子命令
5. worker 完成后走现有 `/finish-branch` 合并回主分支

## 非目标（阶段 1 不做）

- SQLite mailbox + 8 种消息协议 → **阶段 2**
- FIFO merge queue + AI 冲突裁决 → **阶段 3**
- AgentRuntime 抽象（非 Claude Code 兼容）→ **阶段 3**
- 常驻后台 coordinator 守护进程 → 阶段 1 里主 session 就是 coordinator
- tmux 降级方案（无 tmux 环境不可用） → 阶段 2 考虑
- Windows 原生支持 → 建议 WSL

## 架构

```
主 Claude Code session (= coordinator)
  └─ tmux session: squad-<task-id>
       ├─ window 0: coordinator pane（主 session 的镜像日志）
       ├─ window 1: worker "scout-auth"    （worktree: .worktrees/wt/squad-auth-scout）
       ├─ window 2: worker "builder-auth"  （worktree: .worktrees/wt/squad-auth-builder）
       └─ window 3: worker "reviewer-auth" （worktree: .worktrees/wt/squad-auth-reviewer）

共享状态：.agent-harness/squad/<task-id>/
  ├─ manifest.json       # squad 元信息：task-id、创建时间、worker 列表、tmux session 名
  ├─ inbox.jsonl         # coordinator → worker 的消息队列（worker 启动时读，循环轮询）
  ├─ status.jsonl        # worker → coordinator 的状态报告（worker 每次做完动作追加一行）
  └─ workers/<name>/
       ├─ prompt.md      # 注入给这个 worker 的初始 prompt
       ├─ capability     # 单行文本：scout | builder | reviewer
       └─ .claude/settings.local.json  # 按 capability 渲染的工具白名单
```

## 核心流程

### 1. `/squad create <spec-file>`

输入：一个 YAML/Markdown 任务规格，例如：

```yaml
task_id: auth-rewrite
base_branch: master
workers:
  - name: scout-auth
    capability: scout
    prompt: "阅读 src/auth/ 下所有文件，产出现状报告到 .agent-harness/squad/auth-rewrite/workers/scout-auth/report.md"
  - name: builder-auth
    capability: builder
    depends_on: [scout-auth]
    prompt: "读 scout-auth 的报告，按 docs/specs/auth-rewrite.md 实现"
  - name: reviewer-auth
    capability: reviewer
    depends_on: [builder-auth]
    prompt: "对 builder-auth 的 worktree 做 /multi-review，结果写到 review.md"
```

执行：
1. 校验 tmux 已安装（`which tmux`）
2. `tmux new-session -d -s squad-<task-id>`
3. 对每个 worker：调用现有 `/use-worktrees` 逻辑建 worktree
4. 渲染 `.claude/settings.local.json`（见下方 capability 权限表）
5. `tmux new-window -t squad-<task-id> -n <worker-name> -d "cd <worktree> && claude --prompt-file prompt.md"`
6. 写 `manifest.json`
7. 报告给用户：`tmux attach -t squad-<task-id>` 可查看

### 2. `/squad status`

读 `manifest.json` + `status.jsonl`，输出：

```
Squad: auth-rewrite (started 12 min ago)
Worker            | Capability | Status      | Last action        | Worktree
scout-auth        | scout      | ✅ done     | report.md written  | .worktrees/wt/squad-auth-scout
builder-auth      | builder    | 🔄 running  | editing auth.py    | .worktrees/wt/squad-auth-builder
reviewer-auth     | reviewer   | ⏸ waiting  | (depends_on)       | (not created)
```

### 3. `/squad attach <worker-name>`

直接 `tmux attach -t squad-<task-id> \; select-window -t <worker-name>` —— 让用户进到那个 agent 的窗口亲眼看。

### 4. `/squad stop [<worker-name>|all]`

发终止信号 → 清理 tmux window → **不**删 worktree（留给 `/finish-branch` 处理）

### 5. 合并收尾

不新造合并工具，直接让用户对每个 worker 的 worktree 跑 `/finish-branch`。**阶段 1 接受"人工按顺序合"**。

## Capability 权限表（通过 `.claude/settings.local.json` 强制）

| Capability | 允许工具 | 禁止工具 | 用途 |
|---|---|---|---|
| `scout` | Read, Glob, Grep, Bash(read-only 命令白名单) | Write, Edit, Bash(git\|rm\|curl POST...) | 只读探索、输出报告 |
| `builder` | Read, Write, Edit, Bash(开发命令全开), Grep, Glob | Bash(git push, rm -rf, 远端操作) | 常规实现 |
| `reviewer` | Read, Glob, Grep, Bash(test/lint 白名单) | Write, Edit, Bash(git\|写操作) | 审查、产出评审报告 |

> 工具黑名单通过 `settings.local.json` 的 `permissions.deny` 字段实现（已是 Claude Code 原生能力，无需自研）

## 文件清单（新增）

### 模板层
- `src/agent_harness/templates/superpowers/.claude/commands/squad.md.tmpl` — 主技能入口
- `src/agent_harness/templates/common/.agent-harness/squad/README.md.tmpl` — 目录说明
- `src/agent_harness/templates/common/scripts/squad/` — 实现脚本
  - `squad.py` — CLI 入口（create / status / attach / stop 分发）
  - `capability_templates/scout.json.tmpl` — scout settings.local.json 模板
  - `capability_templates/builder.json.tmpl`
  - `capability_templates/reviewer.json.tmpl`

### Dogfood 层（自动同步）
- `.claude/commands/squad.md`
- `scripts/squad/*`
- `.agent-harness/squad/.gitkeep`

### 文档
- `docs/product.md` — 新增"多 agent 协作（/squad）"段
- `docs/architecture.md` — 新增"squad 目录"说明
- `docs/runbook.md` — 新增"tmux 依赖安装 + squad 使用示例"
- `AGENTS.md` — 约束新增：禁止在非 worker 上下文使用 capability 文件
- `CHANGELOG.md` — 记录新能力

### 测试
- `tests/test_squad_capability.py` — capability 模板渲染正确、权限字段符合预期
- `tests/test_squad_spec_parse.py` — YAML/MD 规格解析、`depends_on` 循环检测
- `tests/test_squad_tmux_mock.py` — mock tmux CLI，验证命令构造正确

## 验收标准

1. ✅ `tmux` 未安装时 `/squad create` 明确报错并给出安装命令（不静默失败）
2. ✅ `depends_on` 循环依赖时拒绝创建 squad 并报错
3. ✅ 3 种 capability 的 `settings.local.json` 能阻止越权操作（单元测试验证字段，不需真起 Claude Code）
4. ✅ `/squad status` 在无活跃 squad 时输出友好提示，不崩
5. ✅ worker 的 worktree 完整独立，互相改文件不冲突
6. ✅ 现有 203 测试全通过 + 新增至少 3 个测试
7. ✅ docs/product + runbook + CHANGELOG + AGENTS.md 同步更新
8. ✅ dogfood（项目自身）保持无漂移
9. ✅ `/squad` 在 `which-skill.md.tmpl` 决策树里出现
10. ✅ `/dispatch-agents` 和 `/squad` 各自的适用场景在文档中说清楚

## 关键决策

| 决策 | 方案 | 理由 |
|---|---|---|
| 自研 vs 包 claude-squad | **自研 MVP** | 用户需求还不确定，先用最小 Python 脚本验证；阶段 2 再考虑换成 claude-squad 依赖 |
| 消息存储 | **JSONL 文件** | 阶段 1 不引入 SQLite 依赖，文件锁用 `fcntl.flock` 够用 |
| 协调方式 | **主 session 就是 coordinator** | 阶段 1 不做常驻守护进程，避免进程管理复杂度 |
| worker 启动方式 | **`claude --prompt-file`** | 依赖 Claude Code CLI 的 prompt 注入能力（需 verify 该 flag 存在） |
| tmux 依赖 | **硬依赖** | 阶段 1 用户必须装 tmux，降级方案延后 |
| 与 /dispatch-agents 关系 | **并存** | dispatch 适合短独立子任务、squad 适合长流程/需观察/需分权 |
| Windows 支持 | **WSL** | 阶段 1 不支持原生 Windows，在 runbook 里明确 |

## 风险与预案

| 风险 | 预案 |
|---|---|
| Claude Code `--prompt-file` 不存在或行为变化 | 实施前先 `/source-verify` 验证；备选方案用 `claude < prompt.md` pipe |
| worker 崩溃后僵尸 worktree 堆积 | `/squad stop` 不自动删 worktree，但提供 `squad gc` 清理 stale 条目 |
| 多 worker 同时写 `.agent-harness/lessons.md` | 阶段 1 约定：worker **禁止**直接写 lessons；只能写 `workers/<name>/lessons.pending.md`，coordinator 合并 |
| tmux 版本兼容 | 要求 tmux >= 3.0；runbook 里写明 |
| macOS 用户装 tmux 麻烦 | runbook 提供 `brew install tmux` 一行 |

## 开放问题（等用户决策）

1. **spec 文件格式**：YAML 还是 Markdown frontmatter？倾向 **YAML**（解析简单、工具成熟）
2. **worker prompt 注入机制**：是否在 worker prompt 里强制注入"你是 squad 成员，capability=X，status 文件路径=Y"的前缀？倾向 **是**
3. **/squad create 是否自动跑 `/spec` 校验**：倾向 **否**，spec 校验由用户自己用 `/spec` 跑，/squad 只做编排
4. **是否允许嵌套 squad**（worker 再起 squad）：倾向 **禁止**（对齐 /dispatch-agents 的递归禁令）

## 下一步

用户确认本 spec 后：
1. 创建 Issue #21（同步 GitHub + GitLab）
2. 创建 branch `feat/squad-mvp`
3. 写 `docs/superpowers/specs/2026-04-12-squad-mvp-plan.md`（拆步骤 + TDD 顺序）
4. 进入 `/lfg` 流水线

---

**当前 current-task.md 保持不变**（Issue #11 lessons 分区），本 spec 只是调研产物。
