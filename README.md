# Agent Harness Framework

**让任意软件项目在 5 分钟内具备 AI Agent 协作能力。**

大多数 AI 编码工具打开一个项目后，对这个项目一无所知——不知道架构、不知道约定、不知道上次踩过什么坑。Agent Harness 解决的就是这个问题：它扫描项目现状，生成一套结构化的知识骨架，让 AI 从第一秒就像一个了解项目背景的队友。

## 它做了什么

```
你的项目（任意语言、任意框架）
    │
    ▼
harness init /path/to/repo
    │
    ├── 自动探测：语言、包管理器、构建命令、项目类型、外部依赖
    ├── 接入评估：0-100 分，列出缺口和建议
    │
    ▼
生成 AI 协作基础设施
    │
    ├── docs/          产品规则、架构设计、运行手册（AI 自动补全）
    ├── .claude/
    │   ├── rules/     行为约束（安全、测试、自治、上下文预算）
    │   ├── commands/  33 个工作流技能（/tdd /debug /lfg ...）
    │   └── hooks/     会话保护（防丢进度、提醒压缩上下文）
    └── .agent-harness/
        ├── current-task.md   当前任务追踪
        ├── lessons.md        经验教训知识库
        ├── memory-index.md   热知识索引（AI 优先读这个）
        └── bin/              内嵌运行时（clone 即用，无需装 CLI）
```

初始化完成后，AI 打开项目会自动读取预填的首次任务，开始分析源码、补全文档。不需要任何额外操作。

## 核心理念

### 知识分层，不是一股脑全塞给 AI

AI 的上下文窗口是有限的。把所有项目知识都塞进去，结果是什么都看了、什么都记不住。

Agent Harness 用四层记忆架构解决这个问题：

| 层 | 内容 | 何时加载 |
|---|------|---------|
| **L0** | 硬规则（安全、测试、协作约定） | 每次会话自动 |
| **L1** | 当前任务 + 最近 10 条教训 | 任务开始时 |
| **L2** | 完整教训库 + 专业参考清单 | 按需检索 |
| **L3** | 全部历史任务记录 | 显式查询 |

AI 默认只读 L0 + L1（几 KB），需要时用 `/recall` 检索 L2/L3。知识越积越多，但上下文窗口的负担不会增长。

### 越用越快，不是每次从零开始

每次完成任务后，`/compound` 技能自动提炼经验写入教训知识库。下次遇到类似问题，AI 在计划阶段就能避开上次的坑。

```
第 1 次做日期查询 → 踩了时区坑 → lessons.md 记录「日期查询需注意时区」
第 2 次做日期查询 → AI 读到教训 → 计划阶段直接考虑时区处理
第 N 次 → 知识库越来越厚，同类任务越来越快
```

### 结构化工作流，不是自由发挥

33 个技能命令覆盖完整开发生命周期，每个阶段有明确的输入输出：

```
构思 → 规格 → 计划 → 执行 → 验证 → 评审 → 沉淀
```

不确定用哪个？两个入口：
- **`/which-skill`** — 告诉 AI 你要做什么，它推荐合适的技能
- **`/lfg`** — 一键全自动，从需求到交付

## 安装

**环境要求**：Python >= 3.11，Git

```bash
git clone https://github.com/LaoZYi/harness-starter.git
cd harness-starter
make setup    # 自动检测 uv/pip，创建环境并安装依赖
make test     # 验证环境
```

## 使用

### 评估目标项目（不改文件，先看看）

```bash
harness init /path/to/repo --assess-only
```

输出项目探测结果 + 0-100 接入评分 + 缺口和建议。

### 初始化

```bash
harness init /path/to/repo
```

交互式问 5 个问题（项目名、目标、类型、敏感级别、是否有生产环境），确认后生成全套文件。

也支持非交互模式：

```bash
harness init /path/to/repo --config .harness.json --non-interactive
```

### 升级已接入项目

框架版本更新后，对已初始化的项目做增量升级：

```bash
harness upgrade plan /path/to/repo --show-diff   # 先预览
harness upgrade apply /path/to/repo              # 再执行
```

三方合并保留用户修改，被覆盖文件自动备份。

### 日常运维

```bash
harness doctor /path/to/repo    # 健康检查
harness export /path/to/repo    # 导出项目画像（给新人或换 AI 工具时用）
harness stats /path/to/repo     # 任务统计（总数、返工率、活跃度）
```

## 项目类型

框架自动探测项目类型，不同类型生成不同的专属规则：

| 类型 | 检测信号 | 专属规则 |
|------|---------|---------|
| `backend-service` | Dockerfile、API 框架 | API 设计、数据库、错误处理 |
| `web-app` | vite/next/webpack | 无障碍、组件模式 |
| `cli-tool` | bin 字段、cli.py | 退出码、管道约定 |
| `library` | VERSION、Cargo.toml | API 契约、语义化版本 |
| `worker` | worker.toml、celery | 队列模式、并发控制 |
| `mobile-app` | React Native、pubspec | 平台差异 |
| `monorepo` | pnpm-workspace、turbo | workspace 依赖 |
| `data-pipeline` | dbt、dags/ | 数据血缘 |
| `meta` | services/registry.yaml | 跨服务协调 |

## 多 Agent 协作

对于复杂任务，框架支持三种多 Agent 模式：

| 模式 | 适用场景 | 工作方式 |
|------|---------|---------|
| `/dispatch-agents` | 几个独立小任务 | 一次分发，一次收回 |
| `/subagent-dev` | 规划和执行分离 | 规划者想，执行者做 |
| `/squad` | 长任务 + 角色分权 | tmux 多窗口，每人一个 worktree |

Squad 模式支持四种角色（orchestrator / scout / builder / reviewer），通过 `settings.local.json` 的 `permissions.deny` 在运行时强制工具权限——scout 只能读不能写，orchestrator 连代码都不碰。

## 插件机制

在目标项目中创建 `.harness-plugins/` 目录，添加团队自定义规则和模板：

```
.harness-plugins/
├── rules/team-security.md      # → .claude/rules/team-security.md
└── templates/docs/guide.md     # → docs/guide.md
```

支持 `{{project_name}}` 等模板变量，init 和 upgrade 时自动渲染。

## 项目内嵌运行时

初始化后，AI 工作流所需的命令直接内嵌在项目中：

```bash
.agent-harness/bin/audit tail     # 查看变更审计
.agent-harness/bin/memory rebuild . --force  # 重建记忆索引
```

**Clone 项目的人无需安装 harness CLI**，所有日常命令从 `.agent-harness/bin/` 调用。`harness` CLI 只有维护者在 init / upgrade / doctor 时才需要。

## 为什么做成框架而不是样例项目

| 样例项目的问题 | 框架的解决方式 |
|--------------|--------------|
| 样例业务代码污染真实项目上下文 | 不含业务代码，只生成协作基础设施 |
| 新项目能用，存量项目用不了 | 探测 + 增量初始化，新旧项目都能接入 |
| 生成一次就完了，后续靠人维护 | `harness upgrade` 持续增量更新，三方合并保留自定义 |
| 项目认知散落在人脑中 | 教训知识库 + 记忆索引把知识沉淀为文件 |

## 文档

| 文档 | 适合谁 |
|------|--------|
| **[速查手册](docs/quickstart.md)** | 已熟悉的用户，快速查命令 |
| **[完整使用手册](docs/usage-manual.md)** | 首次接触，需要理解每个功能（23 章节） |
| **[运行手册](docs/runbook.md)** | 运维和故障排查 |
| **[产品规则](docs/product.md)** | 框架能力清单和变更原则 |
| **[架构约束](docs/architecture.md)** | 模块职责和数据流 |
