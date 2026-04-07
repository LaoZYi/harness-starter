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

## 25 个工作流技能命令

初始化后，项目中会生成 25 个 Claude Code 斜杠命令，覆盖完整开发生命周期。

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
| `/git-commit` | 结构化提交（规范检测、逻辑分组、安全检查、智能暂存） | compound |
| `/finish-branch` | 4 个选项：合并/PR/保留/丢弃，测试门禁 | superpowers |
| `/doc-release` | 9 步发布后文档同步（diff 分析 → 逐文件审计 → 跨文档一致性） | gstack |
| `/retro` | 工程回顾（git 历史分析、会话检测、热点分析、具体表扬和建议） | gstack |

### 自主模式与元技能

| 命令 | 用途 | 来源 |
|------|------|------|
| `/lfg` | 全自主流水线：plan → implement → review → fix → verify → compound | compound |
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

### 按场景选择

| 场景 | 推荐命令 |
|------|---------|
| 不知道从哪开始 | `/use-superpowers` 或 `/brainstorm` |
| 需要探索多个方向 | `/ideate` |
| 任务复杂需要拆解 | `/write-plan` → `/execute-plan` |
| 想全自动完成 | `/lfg` |
| 需要写新功能 | `/tdd` |
| 遇到 bug | `/debug` |
| 多个独立子任务 | `/dispatch-agents` |
| 实现完成了 | `/verify` → `/multi-review` |
| 需要提交代码 | `/git-commit` |
| 想沉淀经验 | `/compound` |
| 需要安全审计 | `/cso` |
| 需要质量评估 | `/health` |
| 发布后更新文档 | `/doc-release` |
| 想做工程回顾 | `/retro` |

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
