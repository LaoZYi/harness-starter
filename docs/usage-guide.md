# Agent Harness Framework 完整使用指南

## 目录

- [概述](#概述)
- [安装](#安装)
- [快速开始](#快速开始)
- [初始化项目](#初始化项目)
- [生成的文件结构](#生成的文件结构)
- [25 个工作流技能命令](#25-个工作流技能命令)
- [推荐工作流](#推荐工作流)
- [日常运维](#日常运维)
- [升级已有项目](#升级已有项目)
- [配置参考](#配置参考)
- [插件机制](#插件机制)
- [上游同步](#上游同步)
- [外部工具集成](#外部工具集成)
- [常见问题](#常见问题)

---

## 概述

Agent Harness Framework 是一个通用初始化框架，用来给 AI agent（Claude Code、Codex 等）在任意项目里落一套稳定的协作基础设施。它不自带业务代码，而是提供：

1. **探测** — 扫描目标项目，产出结构化画像（语言、包管理器、命令、目录结构）
2. **评估** — 根据画像产出接入评分、缺口和建议
3. **初始化** — 生成文档、规则、任务追踪和 25 个工作流技能命令
4. **升级** — 对已接入的项目做增量升级，支持 diff 预览和自动备份

工作流技能融合了 3 个开源项目的精华：
- [obra/superpowers](https://github.com/obra/superpowers)（14 个基础技能）
- [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)（6 个增强技能）
- [garrytan/gstack](https://github.com/garrytan/gstack)（5 个运维技能）

---

## 安装

```bash
cd agent-harness-starter
pip install -e .
```

`-e` 是 editable mode（开发模式），安装一次即可。后续框架代码更新后无需重新安装。

安装后即可在任意位置使用 `harness` 命令。

> 不想安装？也可以通过 `PYTHONPATH=src python -m agent_harness` 来使用。

---

## 快速开始

```bash
# 1. 先看看项目现状
harness init /path/to/your-project --assess-only

# 2. 交互式初始化（会问 5 个问题）
harness init /path/to/your-project

# 3. 打开 Claude Code 进入项目目录，AI 自动开始工作
cd /path/to/your-project
# Claude Code 会读取 .agent-harness/current-task.md 中的预填任务
```

---

## 初始化项目

### 交互模式（推荐）

```bash
harness init /path/to/project
```

会依次问 5 个问题（支持返回上一步）：

1. **项目名称** — 例如 "Acme API"
2. **一句话目标** — 例如 "Handle internal automation requests"
3. **项目类型** — 从 8 种类型中选择（见下表）
4. **敏感级别** — standard / internal / high
5. **是否已有生产环境** — 是 / 否

### 支持的项目类型

| 类型 | 适用场景 |
|------|---------|
| `backend-service` | API 服务、微服务 |
| `web-app` | 前端应用、SPA（React、Vue、Next.js） |
| `cli-tool` | 命令行工具 |
| `library` | 可复用的包/库 |
| `worker` | 后台任务、Serverless |
| `mobile-app` | iOS/Android、React Native、Flutter |
| `monorepo` | 多包工作空间 |
| `data-pipeline` | ETL、dbt、Airflow |

每种类型有独立的 preset，定义该类型的行为变化判定、架构关注点、发布检查项和推荐技能。

### 非交互模式

```bash
# 方式一：通过配置文件
harness init /path/to/project --config config.json --non-interactive

# 方式二：通过命令行参数
harness init /path/to/project \
  --project-name "Acme API" \
  --summary "Handle internal automation requests." \
  --project-type backend-service \
  --language python \
  --package-manager uv \
  --test-command "uv run pytest" \
  --check-command "uv run ruff check ." \
  --non-interactive

# 方式三：在项目根目录放 .harness.json，自动读取
harness init /path/to/project --non-interactive
```

### 配置文件示例（`.harness.json`）

```json
{
  "project_name": "Acme API",
  "project_slug": "acme-api",
  "summary": "Handle internal automation requests.",
  "project_type": "backend-service",
  "language": "python",
  "package_manager": "uv",
  "run_command": "uv run python -m acme_api",
  "test_command": "uv run pytest",
  "check_command": "uv run ruff check .",
  "ci_command": "make ci",
  "deploy_target": "docker",
  "has_production": true,
  "sensitivity": "internal"
}
```

### 其他初始化选项

```bash
# 预演模式（不写文件）
harness init /path/to/project --dry-run

# 基于现有框架创建（先复制框架代码，再初始化）
harness init /path/to/new-project --scaffold ~/frameworks/vue-admin-template

# 覆盖已有文件
harness init /path/to/project --force

# 不生成工作流技能命令
harness init /path/to/project --no-superpowers

# 初始化后自动 git commit
harness init /path/to/project --git-commit
```

---

## 生成的文件结构

初始化后，目标项目会新增以下文件：

```
project/
├── AGENTS.md                              # AI agent 快速入口（≤80 行）
├── CLAUDE.md                              # Claude Code 上下文
├── CLAUDE.local.md.example                # 本地覆盖模板
├── CONTRIBUTING.md                        # 贡献指南
│
├── docs/
│   ├── product.md                         # 功能定义和完成标准
│   ├── architecture.md                    # 架构和模块划分
│   ├── workflow.md                        # 协作流程和评审要点
│   ├── runbook.md                         # 运行、测试、排障手册
│   ├── release.md                         # 发布检查清单
│   └── superpowers/
│       └── specs/                         # 设计文档和实现计划存放目录
│
├── .agent-harness/
│   ├── project.json                       # 结构化项目元数据
│   ├── current-task.md                    # 当前进行中的任务
│   ├── task-log.md                        # 历史任务记录
│   ├── lessons.md                         # 经验教训知识库
│   └── init-summary.md                   # 初始化摘要
│
├── .claude/
│   ├── settings.json                      # SessionStart + PreToolUse hooks
│   ├── commands/
│   │   ├── process-notes.md               # 语音笔记处理
│   │   ├── brainstorm.md                  # 结构化头脑风暴
│   │   ├── write-plan.md                  # 编写实现计划
│   │   ├── tdd.md                         # 测试驱动开发
│   │   ├── debug.md                       # 系统性排障
│   │   ├── ... (共 25 个技能命令)
│   │   └── use-superpowers.md             # 技能选择引导
│   └── rules/
│       ├── safety.md                      # 安全规则
│       ├── testing.md                     # 测试要求
│       ├── task-lifecycle.md              # 任务生命周期
│       ├── autonomy.md                    # 权限级别
│       ├── api.md                         # API 设计规范
│       ├── database.md                    # 数据库安全
│       ├── documentation-sync.md          # 文档同步规则
│       ├── error-attribution.md           # 错误归因规则
│       └── superpowers-workflow.md        # 工作流技能引导
│
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── feature_request.md
│       └── config.yml
│
└── notes/                                 # 语音笔记存放目录
```

---

## 27 个工作流技能命令

初始化后，项目中会生成 27 个 Claude Code 斜杠命令，覆盖完整开发生命周期。

### 构思与设计

| 命令 | 用途 | 来源 |
|------|------|------|
| `/ideate` | 多角度结构化构思，3-4 个子代理用不同视角生成候选方案，筛选出 5-7 个存活方案 | compound |
| `/brainstorm` | 结构化设计对话，9 步流程产出设计文档到 `docs/superpowers/specs/` | superpowers |

### 计划与任务管理

| 命令 | 用途 | 来源 |
|------|------|------|
| `/write-plan` | 创建 2-5 分钟粒度的实现计划，含完整代码和验证步骤 | superpowers |
| `/todo` | 结构化任务拆分（P1/P2/P3 优先级），依赖追踪，与 `current-task.md` 集成 | compound |

### 开发与执行

| 命令 | 用途 | 来源 |
|------|------|------|
| `/tdd` | 测试驱动开发（RED-GREEN-REFACTOR 铁律） | superpowers |
| `/execute-plan` | 按计划逐步执行，遇阻即停 | superpowers |
| `/debug` | 4 阶段系统性排障：根因调查 → 模式分析 → 假设验证 → 修复 | superpowers |
| `/subagent-dev` | 子代理协作开发，两阶段评审（spec + quality） | superpowers |
| `/dispatch-agents` | 并行分发独立任务给多个 agent | superpowers |
| `/use-worktrees` | Git worktree 创建隔离开发环境 | superpowers |

### 验证与评审

| 命令 | 用途 | 来源 |
|------|------|------|
| `/verify` | 5 步验证门：识别命令 → 执行 → 读输出 → 核实 → 声明 | superpowers |
| `/multi-review` | 6 角色并行评审（正确性/测试/可维护性/规范/安全/性能），P0-P3 分级 | compound |
| `/request-review` | 准备评审请求，含 commit SHA、实现描述、需求引用 | superpowers |
| `/receive-review` | 6 步处理评审反馈：阅读 → 复述 → 验证 → 评估 → 回应 → 实施 | superpowers |

### 安全与质量

| 命令 | 用途 | 来源 |
|------|------|------|
| `/cso` | 14 阶段安全审计（OWASP Top 10 + STRIDE + secrets 考古 + 供应链） | gstack |
| `/health` | 代码质量仪表盘，加权 0-10 分（类型检查/lint/测试/死代码/shell） | gstack |
| `/careful` | 8 类危险命令拦截（rm -rf、DROP TABLE、force push 等） | gstack |

### 知识沉淀与收尾

| 命令 | 用途 | 来源 |
|------|------|------|
| `/compound` | 任务完成后提炼经验，写入 `.agent-harness/lessons.md`，自动去重 | compound |
| `/lint-lessons` | 知识库健康检查：去重、矛盾检测、过时检测、覆盖度分析（0-10 评分） | karpathy |
| `/git-commit` | 结构化提交（规范检测、逻辑分组、安全检查、智能暂存） | compound |
| `/finish-branch` | 4 个选项：合并/PR/保留/丢弃，测试门禁 | superpowers |
| `/doc-release` | 9 步发布后文档同步（diff 分析 → 逐文件审计 → 跨文档一致性） | gstack |
| `/retro` | 工程回顾（git 历史分析、会话检测、热点分析、具体表扬和建议） | gstack |

### 自主模式与元技能

| 命令 | 用途 | 来源 |
|------|------|------|
| `/lfg` | 全自主流水线：plan → implement → review → fix → verify → compound → lint | compound |
| `/evolve` | 自动搜索新项目 → 评估独特性 → 创建 Issue 提案 | 本地原创 |
| `/use-superpowers` | 技能选择引导，1% 法则决策树 | superpowers |
| `/write-skill` | 用 TDD 方法论编写新技能 | superpowers |

---

## 推荐工作流

### 标准工作流（手动串联）

```
/ideate          → 多角度探索方向，产出候选方案
    ↓
/brainstorm      → 深入设计对话，产出设计文档
    ↓
/write-plan      → 编写实现计划（2-5 分钟粒度）
    ↓
/tdd             → 测试驱动开发（先写测试，再写实现）
    ↓
/execute-plan    → 按计划逐步实施
    ↓
/verify          → 运行测试和检查，全面验证
    ↓
/multi-review    → 6 角色并行代码评审
    ↓
/compound        → 提炼经验到知识库
    ↓
/finish-branch   → 合并或推送分支
```

### 全自主模式（一键完成）

```bash
# 输入任务描述，agent 自动走完全部流程
/lfg 实现用户登录功能，包含邮箱密码验证和 JWT token 生成
```

`/lfg` 会自动串联：计划 → 实施 → 评审 → 修复 → 验证 → 知识沉淀 → 收尾。

### 懒人入口

如果你不想记 25 个命令，**只记两个**：

- **`/use-superpowers`** — 告诉 AI 你要做什么，它会自动推荐合适的技能
- **`/lfg`** — 一键全自动完成（plan → implement → review → fix → verify → compound）

下面的决策指南帮你理解每个阶段多个命令之间的关系，但日常使用不需要背诵。

### 技能选择决策指南

每个阶段看起来有多个命令，但它们不是"二选一"的关系——有的解决不同问题，有的是上下游串联。以下按开发阶段逐个说清楚。

#### 第一步：想清楚做什么

> **类比**：`/ideate` 是头脑风暴白板，`/brainstorm` 是设计评审会议。

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| "老板说了个模糊方向，我不知道具体做什么" | `/ideate` | 多角度发散，从 30 个想法里筛出 5-7 个靠谱的 |
| "我知道要做什么，但不确定怎么设计" | `/brainstorm` | 深入探讨方案细节，产出设计文档 |
| "需求很明确，不需要讨论" | 跳过，直接下一步 | |

典型组合：先 `/ideate` 选方向 → 再 `/brainstorm` 做设计。小任务可以直接 `/brainstorm` 或跳过。

#### 第二步：制定计划

> **类比**：`/write-plan` 是写施工图纸，`/todo` 是在图纸上标工序和优先级。

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| "需要把设计拆成可执行的步骤" | `/write-plan` | 产出 2-5 分钟粒度的实施计划 |
| "计划写好了，子任务需要排优先级和追踪依赖" | `/todo` | 给子任务标 P1/P2/P3，管理阻塞关系 |
| "就改一个小文件" | 跳过，直接写代码 | |

典型组合：`/write-plan` 写计划 → `/todo` 管理子任务。简单任务只需 `/write-plan` 或直接跳过。

#### 第三步：写代码

> **类比**：`/tdd` 是工匠手工打造，`/execute-plan` 是按图纸施工，`/subagent-dev` 是派工头带队干，`/dispatch-agents` 是多支队伍同时开工。

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| "写新功能或改现有行为" | **`/tdd`**（最常用） | 先写测试，再写实现。质量最高 |
| "有现成计划，想按步骤走" | `/execute-plan` | 逐步执行计划，每步都验证 |
| "任务太大，想拆给子 agent" | `/subagent-dev` | 一个一个分配，每个任务做完有评审 |
| "多个互不相关的子任务" | `/dispatch-agents` | 同时分发给多个 agent 并行做 |
| "遇到 bug 了" | `/debug` | 根因优先！不要猜，先调查 |
| "想在隔离环境开发" | `/use-worktrees` | 创建 git worktree，不影响主分支 |

**80% 的情况用 `/tdd` 就够了**。`/execute-plan` 是 `/tdd` 的"按计划版"，两者经常配合：计划里每一步用 TDD 方式执行。

#### 第四步：验证和评审

> **类比**：`/verify` 是自检清单，`/multi-review` 是请 6 个专家会诊，`/request-review` 是写评审申请表，`/receive-review` 是处理专家意见。

这四个命令是**顺序关系**，不是选择关系：

```
代码写完了
    ↓
/verify              ← 自己先验证（跑测试、跑 lint、确认结果）
    ↓
/multi-review        ← AI 6 角色评审（正确性/测试/安全/性能/规范/可维护性）
    ↓ 如果需要人工评审
/request-review      ← 准备给人看的评审材料
    ↓ 收到反馈后
/receive-review      ← 逐条处理反馈（阅读→复述→验证→回应→实施）
```

**快速模式**：只用 `/verify` + `/multi-review` 就够了（占 90% 场景）。`/request-review` 和 `/receive-review` 在团队协作、提 PR 时才需要。

#### 第五步：安全和质量

> **类比**：`/cso` 是请安保专家扫一遍，`/health` 是年度体检报告，`/careful` 是操作前的安全带。

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| "发布前想确认没有安全漏洞" | `/cso` | 14 阶段安全审计（OWASP + STRIDE + secrets） |
| "想知道代码整体质量如何" | `/health` | 0-10 综合评分，告诉你哪里最需要改进 |
| "要执行危险操作（删数据、force push）" | `/careful` | 自动拦截提醒，防止手滑 |

这三个**随时可用**，不需要等到特定阶段。`/careful` 在初始化后自动生效（作为规则文件），不需要手动调用。

#### 第六步：收尾

> **类比**：`/git-commit` 是签收一批货，`/finish-branch` 是关闭整条产线，`/compound` 是写工作日志，`/doc-release` 是更新产品手册。

```
一个功能做完了
    ↓
/git-commit          ← 提交代码（可能提交多次）
    ↓
/compound            ← 把这次学到的经验写入知识库
    ↓
/lint-lessons        ← 检查知识库有没有重复或过时条目（可选，建议定期）
    ↓
/finish-branch       ← 合并分支 / 创建 PR / 保留 / 丢弃
    ↓ 合并后
/doc-release         ← 同步更新 README、CHANGELOG 等文档
    ↓ 每周一次
/retro               ← 工程回顾，分析这周的 git 历史
```

**最常用**：`/git-commit` → `/finish-branch`。`/compound` 强烈建议每次任务完成都用，积累知识库后续会越来越快。

### 一图看懂完整流程

```
 ┌─────────── 不确定用什么？ → /use-superpowers ───────────┐
 │                                                          │
 │  ┌──────────── 想全自动？ → /lfg ──────────────────┐    │
 │  │                                                  │    │
 │  │   构思 ──→ 计划 ──→ 执行 ──→ 验证 ──→ 收尾      │    │
 │  │    │        │        │        │        │         │    │
 │  │  ideate   write-   tdd     verify   git-commit   │    │
 │  │  brain-   plan     debug   multi-   compound     │    │
 │  │  storm    todo     exec-   review   finish-      │    │
 │  │                    plan             branch       │    │
 │  │                    sub-             doc-release   │    │
 │  │                    agent            retro        │    │
 │  │                    dispatch                      │    │
 │  │                    worktrees                     │    │
 │  │                                                  │    │
 │  │  随时可用：/cso  /health  /careful               │    │
 │  └──────────────────────────────────────────────────┘    │
 └──────────────────────────────────────────────────────────┘
```

### 按任务规模速查

| 规模 | 典型耗时 | 推荐路径 |
|------|---------|---------|
| **微小** — 改一行配置、修个 typo | < 5 分钟 | 直接改 → `/git-commit` |
| **小** — 修一个 bug、加一个字段 | 5-30 分钟 | `/tdd` → `/verify` → `/git-commit` |
| **中** — 新增一个功能模块 | 30 分钟-2 小时 | `/brainstorm` → `/write-plan` → `/tdd` → `/verify` → `/multi-review` → `/compound` → `/finish-branch` |
| **大** — 重构、新系统、多模块联动 | 半天以上 | `/ideate` → `/brainstorm` → `/write-plan` → `/lfg`（或手动走全流程） |
| **不确定** | ? | `/use-superpowers` 让 AI 推荐 |

---

## `/lfg` 深度指南

`/lfg`（Let's F\*\*\*ing Go）是框架的核心能力——输入一句话需求，AI 自动完成从计划到交付的全部流程。

### 基本用法

```
/lfg 你的任务描述
```

任务描述写得越具体，效果越好。对比：

```
❌ /lfg 加个搜索
✅ /lfg 给用户列表页增加搜索功能，支持按姓名和邮箱模糊搜索，搜索结果实时更新
```

### 它做了什么（完整生命周期）

```
你输入任务 ──→ AI 自动执行以下全部阶段：

┌──────────────────────────────────────────────────────────┐
│ 阶段 0  理解任务                                          │
│   · 复述任务确认理解正确                                    │
│   · 定义 3-5 条可验证的验收标准                             │
│   · 读取 lessons.md 搜索相关历史教训                        │
│   · 读取 architecture.md 了解模块边界                      │
│   · 判断复杂度 → 选择通道                                  │
├──────────────────────────────────────────────────────────┤
│ 阶段 1  环境准备                                          │
│   · 记录基线 commit（用于回滚）                             │
│   · 创建工作分支隔离开发                                    │
│   · 跑一遍测试确认基线没问题                                │
│   · 记录质量快照（测试数、lint 警告数）                       │
├──────────────────────────────────────────────────────────┤
│ 阶段 2  构思（仅大型任务）                                  │
│   · 多角度生成候选方案                                      │
│   · 🔴 等你选方向                                         │
│   · 深入设计选定方案                                        │
├──────────────────────────────────────────────────────────┤
│ 阶段 3  计划                                              │
│   · 生成实施计划（2-5 分钟粒度的步骤）                       │
│   · 7 项质量检查（覆盖度/具体性/历史教训引用等）              │
│   · 🔴 展示计划摘要等你确认                                 │
├──────────────────────────────────────────────────────────┤
│ 阶段 4  实施                                              │
│   · 逐步执行计划（TDD：先写测试再写实现）                    │
│   · 每步完成后跑测试 + 提交 commit + 更新进度                │
│   · 遇到问题自动用 /debug 排查                              │
│   · 实施完自查：验收标准每条都满足了吗？                      │
├──────────────────────────────────────────────────────────┤
│ 阶段 5  评审                                              │
│   · 6 角色并行评审（正确性/测试/安全/性能/规范/可维护性）      │
│   · 发现分 P0-P3 四级                                      │
├──────────────────────────────────────────────────────────┤
│ 阶段 6  修复（如果评审发现问题）                             │
│   · 先分析根因，再修复                                      │
│   · 修复后重新评审，最多 3 轮                                │
│   · 3 轮不过 → 🔴 停下来让你决定                            │
├──────────────────────────────────────────────────────────┤
│ 阶段 7  验证                                              │
│   · 跑全部测试 + lint 检查                                  │
│   · 逐条核验验收标准（附证据）                               │
│   · 生产项目自动跑安全审计                                   │
├──────────────────────────────────────────────────────────┤
│ 阶段 8  质量对比                                           │
│   · 与阶段 1 的基线对比：测试多了还是少了？警告变化？          │
├──────────────────────────────────────────────────────────┤
│ 阶段 9  沉淀与知识维护                                      │
│   · 提炼经验教训写入 lessons.md                             │
│   · 重点记录：评审发现的问题、走过的弯路、反复出现的模式       │
│   · 快速 lint：检查新条目有没有和已有条目重复或过时            │
├──────────────────────────────────────────────────────────┤
│ 阶段 10  收尾                                             │
│   · 🔴 让你选择：合并/创建 PR/保留/丢弃                     │
│   · 自动同步项目文档                                        │
│   · 输出完成报告                                            │
└──────────────────────────────────────────────────────────┘
```

### 四条通道（自动选择）

`/lfg` 不会用同样的仪式感对待所有任务。它先判断复杂度，然后走对应的通道：

| 通道 | 适用场景 | 走哪些阶段 | 举例 |
|------|---------|-----------|------|
| **快速** | 改一行、修 typo | 直接改 → 测试 → 提交 | `/lfg 把 README 里的 v1.0 改成 v1.1` |
| **轻量** | 小 bug、加个字段 | 简要计划 → TDD → 验证 → 提交 | `/lfg 修复登录接口密码错误返回 500 的 bug` |
| **标准** | 新功能、新接口 | 完整 10 阶段（跳过构思） | `/lfg 给订单 API 增加按日期范围筛选` |
| **完整** | 跨模块、架构级 | 完整 10 阶段 + 构思 + worktree | `/lfg 把认证系统从 session 迁移到 JWT` |

AI 会告诉你它选了哪条通道和原因，你可以随时覆盖（比如"走完整通道"）。

### 什么时候会停下来问你

大部分阶段是自动的，只有这些时刻需要你参与：

| 时刻 | AI 会问你什么 |
|------|-------------|
| 任务不清晰 | "你说的 XX 具体是指...？验收标准是...？" |
| 构思完成（大任务） | "这 5 个方案，你倾向哪个方向？" |
| 计划写好 | "计划共 12 步，涉及 5 个文件，确认开始？" |
| 修复 3 轮没过 | "这两个问题修不过去，要继续/回退/跳过？" |
| 安全审计发现高危 | "发现 1 个 Critical 安全问题，请审查" |
| 收尾 | "代码完成，选择：合并/PR/保留/丢弃？" |

其他时候它就默默干活，你可以去做别的事。

### 知识驱动：越用越聪明

`/lfg` 的一个核心设计是**知识闭环**：

```
           ┌─────────────────────────────┐
           │     .agent-harness/         │
           │     lessons.md              │
           │     (项目知识库)             │
           └──────┬──────────────┬───────┘
                  │              │
         开始前读取           结束后写入 + lint
                  │              │
                  ↓              ↑
           ┌──────┴──────────────┴───────┐
           │         /lfg 流水线          │
           │                             │
           │  计划阶段：引用相关教训       │
           │  实施阶段：避免已知陷阱       │
           │  沉淀阶段：记录新教训         │
           │  lint阶段：去重 + 清理过时    │
           └─────────────────────────────┘
```

- **第一次**做某件事：需要研究，可能走弯路
- **第二次**做类似的事：AI 读到 lessons.md 里的记录，在计划阶段就避开上次的坑
- **第 N 次**：知识库越来越厚，AI 在同类任务上越来越快、越来越少出错

这就是为什么每次 `/lfg` 结束都会运行 `/compound` — 它不只是在完成当前任务，它在为未来的任务积累知识。

### 中断和恢复

`/lfg` 随时可以中断（关闭终端、网络断了、你去开会了），不会丢进度。

**恢复方式**：重新打开 Claude Code，AI 会自动读取 `.agent-harness/current-task.md` 中的进度记录，从上次停下的地方继续。

进度记录包含完整上下文：
- 任务描述和验收标准
- 当前走到哪个阶段
- 基线 commit（用于回滚）
- 质量基线（用于对比）
- 引用的历史教训

所以恢复不是"从头再来"，而是"接着干"。

### 回滚

任何阶段都可以说"回退"：

- **在工作分支上**：`git reset --hard` 回到基线 commit，干干净净
- **在主分支上**：用 `git revert` 逐个撤销（安全操作）
- 进度记录自动清理

### 完成报告

每次 `/lfg` 结束会输出一份结构化报告：

```
✅ LFG 完成报告

任务：给订单 API 增加按日期范围筛选
复杂度：中 | 通道：标准

验收标准：
- [x] /api/orders 支持 start_date 和 end_date 参数
- [x] 日期格式为 ISO 8601
- [x] 缺少日期参数时返回全部订单
- [x] 日期范围无效时返回 400

执行摘要：
  计划：docs/superpowers/specs/2026-04-07-order-date-filter-plan.md
  提交：8 个 commit（a1b2c3d..e4f5g6h）
  评审：PASS（第 1 轮）
  安全：通过（0 个 High/Critical）

质量变化：
  测试：42 → 50（+8）
  Lint：3 → 2（-1）

沉淀：
  - "日期范围查询需注意时区处理" 写入 lessons.md

文档更新：
  - docs/product.md（新增日期筛选功能描述）
```

### 什么任务最适合 `/lfg`

| 最适合 | 也行但不是最优 | 不适合 |
|--------|-------------|--------|
| 需求明确的新功能 | 大范围重构（建议先 `/ideate`） | 纯粹的探索/调研 |
| 已知的 bug 修复 | 涉及大量人工决策的工作 | 需要频繁与产品确认的功能 |
| API 端点增改 | 第一次搭建项目骨架 | 学习性质的尝试 |
| 数据模型变更 | 性能优化（需要先 profiling） | |
| 配置和迁移 | | |

**经验法则**：如果你能用 1-2 句话说清楚"做什么"和"做到什么程度算完"，就适合 `/lfg`。

---

## 日常运维

### 健康检查

```bash
harness doctor /path/to/project
```

检查 task-log 使用率、教训积累数、待补充占位符数量。

### 导出项目画像

```bash
# Markdown 格式（给新人或换 agent 时用）
harness export /path/to/project

# 输出到文件
harness export /path/to/project -o snapshot.md

# JSON 格式（给 CI/CD 用）
harness export /path/to/project --json
```

### 任务数据统计

```bash
harness stats /path/to/project
```

输出任务总数、返工率、活跃度、教训数量。

---

## 升级已有项目

当框架版本更新后，已初始化的项目可以增量升级：

```bash
# 1. 预览升级会影响哪些文件
harness upgrade plan /path/to/project

# 2. 查看具体 diff
harness upgrade plan /path/to/project --show-diff

# 3. 只看某些文件
harness upgrade plan /path/to/project --only AGENTS.md --only .agent-harness/project.json

# 4. 执行升级（自动备份到 .agent-harness/backups/）
harness upgrade apply /path/to/project

# 5. 选择性升级
harness upgrade apply /path/to/project --only AGENTS.md

# 6. 预演升级
harness upgrade apply /path/to/project --dry-run
```

升级会自动备份变化的文件到 `.agent-harness/backups/<timestamp>/`。

---

## 配置参考

### 配置优先级

```
CLI 参数 > --config 文件 > .harness.json > 自动探测值
```

### 完整配置字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_name` | string | 项目名称 |
| `project_slug` | string | URL 友好的项目标识（自动生成） |
| `summary` | string | 一句话目标 |
| `description` | string | 详细描述（可选） |
| `features` | string | 功能列表，逗号或换行分隔（可选） |
| `constraints` | string | 约束条件（可选） |
| `done_criteria` | string | 完成标准（可选，不填则从 preset 生成） |
| `project_type` | string | 项目类型（8 种之一） |
| `language` | string | 编程语言 |
| `package_manager` | string | 包管理器 |
| `run_command` | string | 运行命令 |
| `test_command` | string | 测试命令 |
| `check_command` | string | 检查/lint 命令 |
| `ci_command` | string | CI 命令 |
| `deploy_target` | string | 部署目标 |
| `has_production` | bool | 是否有生产环境 |
| `sensitivity` | string | 敏感级别：standard/internal/high |
| `superpowers` | bool | 是否生成工作流技能（默认 true） |

### 自动探测

框架会自动探测以下信息：

- **语言**：通过 package.json、pyproject.toml、go.mod、Cargo.toml 等
- **框架**：React、Django、FastAPI、Rails 等
- **包管理器**：npm、pnpm、uv、pip、cargo 等
- **命令**：从 Makefile、package.json scripts、pyproject.toml 提取
- **目录结构**：源码、测试、文档、CI 目录
- **外部系统**：postgres、redis、stripe、openai 等依赖
- **ORM**：SQLAlchemy、Prisma 等
- **测试框架**：pytest、jest、go test 等
- **项目类型**：monorepo、mobile-app、data-pipeline 等

---

## 插件机制

在目标项目中创建 `.harness-plugins/` 目录，可添加自定义规则和模板：

```
.harness-plugins/
  rules/
    team-security.md           # 初始化时合并到 .claude/rules/
    code-style.md              # 团队编码规范
  templates/
    docs/onboarding-guide.md   # 初始化时渲染到项目中
    .github/CODEOWNERS         # 自定义文件
```

插件文件支持 `{{project_name}}`、`{{test_command}}` 等模板变量。

---

## 上游同步

框架的 25 个技能模板改编自 3 个上游项目。当上游更新时，可以检查变更：

```bash
# 拉取上游最新 skills 并生成变更报告
make sync-superpowers

# 只查看当前缓存状态（不访问网络）
python scripts/sync_superpowers.py --check

# 查看某个 skill 的详细 diff
python scripts/sync_superpowers.py --diff brainstorming
```

缓存存在 `.superpowers-upstream/`（已 gitignore）。同步只产出报告，不自动修改模板——需要人工审核后手动更新。

支持的上游源：
- `obra/superpowers` — 14 个基础技能
- `EveryInc/compound-engineering-plugin` — 6 个增强技能
- `garrytan/gstack` — 5 个运维技能

---

## 自举（Dogfooding）

框架对自身运行了 `harness init`，生成了完整的 `.agent-harness/` 和 `.claude/` 结构。开发框架本身时也可以使用 `/lfg`、`/tdd`、`/debug` 等技能。

### 模板和产物同步

当你修改了 `src/agent_harness/templates/` 下的模板文件后，框架自身的 `.claude/commands/` 和 `.claude/rules/` 需要同步更新：

```bash
# 同步（只更新 commands/rules/settings，不碰手写文档）
make dogfood
```

不需要记住——`make ci` 会自动检测漂移。如果模板改了但没同步，CI 会报错并提示你运行 `make dogfood`。

---

## 自我进化

框架通过 `/evolve` 命令实现自我迭代：每天自动搜索 AI 编码工具领域的新项目，评估是否值得吸收，合格的创建 GitHub Issue 提案。

### 工作流

```
每天自动触发 /evolve
    ↓
搜索 GitHub + Web（AI coding tools 关键词）
    ↓
初筛（star≥50、近30天更新、非fork）
    ↓
深度评估（vs 已有 27 个技能，找独特能力）
    ↓
创建 Issue 提案（标签 evolution）
    ↓
你审批 approve / reject
    ↓ (approved)
/lfg 实施集成
```

### 手动运行

```
/evolve
```

### 自动触发

通过 Claude Code remote trigger 每天自动执行。查看当前触发器：

```
查看 Claude Code 中的 scheduled triggers
```

### 提案 Issue 格式

每个提案包含：项目链接、Star 数、核心能力、独特价值、建议吸收的技能、可行性评估、风险分析。

你只需要在 Issue 里回复 approve 或 reject。approve 后用 `/lfg` 实施集成。

---

## 外部工具集成

以下外部插件安装后可与本框架生成的项目配合使用：

### codex-plugin-cc

[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — 安装后可用 `/codex:review` 获取 OpenAI Codex 的独立代码评审，与框架的 `/multi-review` 互补，提供跨 AI 交叉验证。

---

## 常见问题

### 初始化后 AI 会自动做什么？

打开 Claude Code 进入项目目录后，AI 会自动读取 `.agent-harness/current-task.md` 中预填的"分析项目并补全文档"任务，自动完成源码分析、文档补全和命令验证。

### 如何关闭工作流技能？

```bash
harness init /path/to/project --no-superpowers
```

或在 `.harness.json` 中设置 `"superpowers": false`。

### 升级后自定义内容会丢失吗？

不会。升级前会自动备份到 `.agent-harness/backups/<timestamp>/`。建议先用 `--show-diff` 预览变更。

### 如何给团队添加自定义规则？

在项目中创建 `.harness-plugins/rules/your-rule.md`，下次 init 或 upgrade 时自动合并到 `.claude/rules/`。

### 项目类型选错了怎么办？

重新运行 `harness init /path/to/project --force`，选择正确的类型。或者直接修改 `.agent-harness/project.json` 中的 `project_type` 字段。

### 探测结果不准确怎么办？

框架的探测是启发式的，可以通过 `--config` 或 `.harness.json` 显式指定正确的值，优先级高于自动探测。

### 如何在 CI 中使用？

```bash
# 评估项目（JSON 输出）
harness init /path/to/project --assess-only --json

# 非交互初始化
harness init /path/to/project --config .harness.json --non-interactive --no-git-commit
```
