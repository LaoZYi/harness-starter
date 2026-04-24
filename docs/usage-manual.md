# Agent Harness Framework 使用手册

## 目录

1. [概述](#概述)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [核心概念](#核心概念)
5. [CLI 命令参考](#cli-命令参考)
6. [初始化流程详解](#初始化流程详解)
7. [升级管理](#升级管理)
8. [工作流技能（Superpowers）](#工作流技能superpowers)
9. [分层记忆系统](#分层记忆系统)
10. [多 Agent 协作](#多-agent-协作)
11. [变更审计系统](#变更审计系统)
12. [会话保护 Hooks](#会话保护-hooks)
13. [插件机制](#插件机制)
14. [项目类型详解](#项目类型详解)
15. [Meta 项目管理](#meta-项目管理)
16. [日常运维](#日常运维)
17. [项目内嵌运行时](#项目内嵌运行时)
18. [故障排查](#故障排查)
19. [配置参考](#配置参考)
20. [技能选择决策指南](#技能选择决策指南)
21. [`/lfg` 深度指南](#lfg-深度指南)
22. [框架维护者指南](#框架维护者指南)
23. [常见问题](#常见问题)

---

## 概述

Agent Harness Framework 是一个通用初始化框架，为任意软件项目接入 AI Agent（Claude Code / Codex）提供标准化的协作基础设施。

它不是一个样例项目，而是一个**生产级工具链**，提供四大核心能力：

| 能力 | 说明 |
|------|------|
| **探测** | 自动扫描目标项目，识别语言、包管理器、构建命令、项目类型、外部依赖 |
| **评估** | 根据探测结果打分（0-100），列出接入缺口和建议 |
| **初始化** | 生成完整的 AI 协作骨架（文档、规则、命令、任务追踪、记忆系统） |
| **升级** | 对已接入项目做增量升级，支持三方合并、diff 预览、自动备份 |

### 适用场景

- 新项目接入 AI Agent 协作
- 存量项目标准化 AI 协作流程
- 团队统一 AI 开发规范
- 微服务体系跨仓库知识管理（Meta 项目）

---

## 安装

### 环境要求

- Python >= 3.11
- Git
- tmux >= 3.0（仅多 Agent 协作场景需要）

### 方式一：uv（推荐）

```bash
git clone https://github.com/LaoZYi/harness-starter.git
cd harness-starter
uv sync          # 自动创建 .venv + 安装依赖
make test        # 验证环境
```

### 方式二：pip + venv

```bash
git clone https://github.com/LaoZYi/harness-starter.git
cd harness-starter
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
make test
```

### 方式三：一键初始化

```bash
make setup       # 自动检测 uv/pip，创建环境并安装依赖
```

### 作为全局 CLI 安装

```bash
pip install -e .
# 之后可在任意目录使用 harness 命令
```

> 不安装也可以：`PYTHONPATH=src python -m agent_harness` 等价于 `harness` 命令。

---

## 快速开始

### 5 分钟入门流程

```bash
# 1. 先看看目标项目的探测和评估结果
harness init /path/to/your-project --assess-only

# 2. 正式初始化（交互式，逐步确认）
harness init /path/to/your-project

# 3. 进入项目，打开 Claude Code
cd /path/to/your-project
claude
# AI 会自动读取预填任务，开始分析项目并补全文档
```

### 初始化后的项目结构

```
your-project/
├── AGENTS.md                    # AI 工作入口（简短规则索引）
├── CLAUDE.md                    # AI 项目概览
├── CONTRIBUTING.md              # 协作流程
├── docs/
│   ├── product.md               # 产品规则和功能清单
│   ├── architecture.md          # 架构设计
│   ├── workflow.md              # 协作流程
│   ├── runbook.md               # 运行手册
│   ├── release.md               # 发布检查项
│   ├── decisions/               # 架构决策记录（ADR）
│   └── superpowers/specs/       # 设计文档和计划
├── .claude/
│   ├── settings.json            # Claude Code 配置
│   ├── rules/                   # AI 行为规则（8+ 条）
│   ├── commands/                # 工作流技能命令（36 个）
│   └── hooks/                   # 会话生命周期 hooks（4 个）
├── .agent-harness/
│   ├── project.json             # 项目元数据快照
│   ├── current-task.md          # 当前任务（预填首次分析任务）
│   ├── task-log.md              # 任务归档历史
│   ├── lessons.md               # 经验教训知识库
│   ├── memory-index.md          # L1 热知识索引
│   ├── audit.jsonl              # 变更审计日志
│   ├── init-summary.md          # 初始化评估摘要
│   ├── references/              # L2 专业参考清单
│   │   ├── accessibility.md
│   │   ├── performance.md
│   │   ├── security.md
│   │   └── testing-patterns.md
│   └── bin/                     # 项目内嵌运行时（无需安装 harness CLI）
│       ├── audit
│       ├── memory
│       └── _runtime/
└── .github/                     # PR/Issue 模板
```

---

## 核心概念

### 1. 项目画像（Project Profile）

框架通过 `discovery.py` 自动探测目标项目，生成结构化画像：

| 字段 | 说明 | 示例 |
|------|------|------|
| `language` | 主语言 | `python`、`javascript`、`go` |
| `package_manager` | 包管理器 | `uv`、`npm`、`cargo` |
| `project_type` | 项目类型（9 种） | `backend-service`、`cli-tool` |
| `run_command` | 运行命令 | `uv run python -m app` |
| `test_command` | 测试命令 | `pytest` |
| `check_command` | 静态检查命令 | `ruff check .` |
| `ci_command` | CI 命令 | `make ci` |
| `sensitivity` | 数据敏感级别 | `standard`、`internal`、`high` |
| `external_systems` | 外部依赖 | `postgres`、`redis`、`s3` |

### 2. 评估分数（Assessment Score）

评估模块根据画像打分（0-100），维度包括：

- 是否有测试命令和测试目录
- 是否有 CI 配置
- 是否有文档
- 是否有类型特征文件（如 backend-service 检查 Dockerfile）
- 外部系统集成情况

评估结果分为三档：
- **80-100**：准备就绪
- **50-79**：基本可用，有优化空间
- **0-49**：需要补充基础设施

### 3. 分层记忆架构

框架使用四层记忆体系管理项目知识，避免知识积累挤占 AI 上下文窗口：

| 层 | 文件 | 加载时机 | 用途 |
|---|------|---------|------|
| **L0** | `AGENTS.md`、`.claude/rules/` | 每次会话自动 | 不变的硬规则 |
| **L1** | `current-task.md` + `memory-index.md` | 任务开始时 | 当前任务 + 热知识精华 |
| **L2** | `lessons.md` + `references/*.md` | 按需检索 | 完整教训 + 专业清单 |
| **L3** | `task-log.md` | 显式查询 | 全部历史任务记录 |

### 4. 工作流技能（Superpowers）

36 个结构化 Claude Code 命令，覆盖从构思到沉淀的完整开发生命周期。可通过 `--no-superpowers` 关闭。

---

## CLI 命令参考

### 初始化与评估

```bash
# 交互式初始化（推荐首次使用）
harness init <target>

# 仅评估，不生成文件
harness init <target> --assess-only

# JSON 格式评估输出
harness init <target> --assess-only --json

# 预演模式，不写入文件
harness init <target> --dry-run

# 非交互模式（需提供配置或 CLI 参数）
harness init <target> --non-interactive

# 基于现有技术框架创建
harness init <target> --scaffold ~/frameworks/vue-admin-template

# 不生成 superpowers 技能命令
harness init <target> --no-superpowers

# 覆盖已有文件
harness init <target> --force

# 初始化后自动 git commit
harness init <target> --git-commit

# 完整非交互示例
harness init /path/to/repo \
  --project-name "Acme API" \
  --summary "内部自动化服务" \
  --project-type backend-service \
  --language python \
  --package-manager uv \
  --run-command "uv run python -m acme_api" \
  --test-command "uv run pytest" \
  --check-command "uv run ruff check ." \
  --ci-command "make ci" \
  --deploy-target docker \
  --has-production \
  --sensitivity internal \
  --non-interactive
```

### 升级管理

```bash
# 预览升级计划
harness upgrade plan <target>

# 预览并显示内容差异
harness upgrade plan <target> --show-diff

# 只看特定文件的升级
harness upgrade plan <target> --only AGENTS.md

# JSON 格式升级计划
harness upgrade plan <target> --json

# 执行升级（自动备份被覆盖文件到 .agent-harness/backups/）
harness upgrade apply <target>

# 只升级特定文件
harness upgrade apply <target> --only AGENTS.md

# 预演升级
harness upgrade apply <target> --dry-run
```

### 运维工具

```bash
# 健康检查
harness doctor <target>

# 导出项目画像
harness export <target>
harness export <target> -o snapshot.md
harness export <target> --json

# 任务统计（总数、返工率、活跃度）
harness stats <target>
```

### 记忆管理

```bash
# 从 lessons/task-log 重建记忆索引
harness memory rebuild <target>

# 强制覆盖已有索引
harness memory rebuild <target> --force

# BM25 搜索知识库（纯文本检索，无需 MCP）
harness memory search "关键词"
harness memory search "关键词" --target /path/to/repo
harness memory search "关键词" --scope lessons    # 只搜教训
harness memory search "关键词" --scope history    # 只搜任务历史
harness memory search "关键词" --top 5            # 返回前 5 条
```

### 变更审计

```bash
# 追加审计记录
harness audit append --file current-task.md --op update --summary "标记步骤 3 完成"

# 查看最近审计记录
harness audit tail
harness audit tail --limit 50
harness audit tail --json

# 审计统计（按文件/操作/Agent 聚合）
harness audit stats
harness audit stats --json

# 清理旧记录
harness audit truncate --before 2026-01-01
```

> `--op` 可选值：`create`（首次创建）/ `update`（修改）/ `append`（追加）/ `delete`（删除）

### 多 Agent 日志隔离

```bash
# 创建 Agent 日志目录
harness agent init <agent-id>

# 追加过程日志
harness agent diary <agent-id> "开始扫描 src/utils"

# 设置当前状态
harness agent status <agent-id> "等待依赖 X 完成"

# 列出所有 Agent（按活动时间排序）
harness agent list

# 汇总 Agent 日志
harness agent aggregate
harness agent aggregate agent-1 agent-2

# 记录结构化知识制品
harness agent artifact <agent-id> \
  --type finding \
  --summary "发现 auth 模块存在 N+1 查询" \
  --content "详细描述..." \
  --refs src/auth/queries.py,docs/performance.md
```

> Agent ID 规范：`^[a-z0-9][a-z0-9-]{0,30}$`

### 多 Agent 常驻协作（Squad）

```bash
# 创建 Squad（按 JSON 规格启动 tmux 多 worker）
harness squad create spec.json

# 查看 Squad 状态
harness squad status

# 附着到 worker 终端
harness squad attach <worker-name>

# 标记 worker 完成
harness squad done <worker-name>

# 自动推进依赖已满足的 worker
harness squad advance

# 常驻监控（自动推进 + watchdog）
harness squad watch
harness squad watch --interval 5

# 停止 worker 或整个 Squad
harness squad stop <worker-name>
harness squad stop all

# 导出事件日志（调试用）
harness squad dump
```

### 技能一致性检查

```bash
# 校验 skills-registry.json 与模板文件的一致性
harness skills lint <target>
```

### 跨服务上下文同步（Meta 项目）

```bash
# 同步单个服务
harness sync /path/to/service --meta /path/to/meta-repo

# 再次同步（meta 路径已记住）
harness sync /path/to/service

# 批量同步所有已注册服务
harness sync --all
```

---

## 初始化流程详解

### 交互式初始化

运行 `harness init <target>` 后，框架按以下步骤执行：

**第 1 步：自动探测**
- 扫描项目文件，识别语言、包管理器、构建命令
- 检测项目类型（9 种之一）
- 发现外部依赖（数据库、缓存、消息队列等）

**第 2 步：交互问答（5 个核心问题）**

| 序号 | 问题 | 说明 |
|------|------|------|
| 1 | 项目名称 | 默认取目录名 |
| 2 | 项目目标 | 一句话描述项目做什么 |
| 3 | 项目类型 | 从 9 种中选择，默认取探测结果 |
| 4 | 数据敏感级别 | `standard` / `internal` / `high` |
| 5 | 是否有生产环境 | 影响安全规则的严格程度 |

支持**返回上一步**修改答案，最终确认后才生成文件。

**第 3 步：评估打分**
- 根据探测结果和用户输入，给出 0-100 接入评分
- 列出优势、缺口和建议

**第 4 步：生成文件**
- 渲染 common 模板（通用文档、规则、hooks）
- 渲染 superpowers 模板（33 个技能命令）
- 渲染类型专属模板（如 `backend-service` 的 API/数据库规则）
- 渲染插件（`.harness-plugins/` 下的自定义内容）
- 安装项目内嵌运行时（`.agent-harness/bin/`）

**第 5 步：预填首次任务**
- `current-task.md` 自动填入"分析项目并补全文档"任务
- AI 打开项目后自动执行，补全 `docs/` 中的占位符

### 非交互式初始化

适合 CI/CD 或团队标准化场景：

```bash
# 通过 CLI 参数
harness init /path/to/repo \
  --project-name "My App" \
  --project-type backend-service \
  --non-interactive

# 通过配置文件
harness init /path/to/repo \
  --config my-config.json \
  --non-interactive
```

### 配置自动发现

在目标仓库根目录放置 `.harness.json`，后续命令自动读取：

```json
{
  "project_name": "My App",
  "summary": "内部自动化服务",
  "project_type": "backend-service",
  "language": "python",
  "package_manager": "uv",
  "sensitivity": "internal",
  "has_production": true
}
```

配置优先级：CLI 参数 > `--config` 文件 > `.harness.json` > 自动探测值

---

## 升级管理

当框架版本更新后，对已初始化的项目做增量升级。

### 升级策略

框架对不同文件采用不同的合并策略：

| 策略 | 适用文件 | 行为 |
|------|---------|------|
| `three_way` | `AGENTS.md`、`docs/*.md`、`rules/*.md` | 三方合并，保留用户修改，冲突时插入标记 |
| `overwrite` | `.agent-harness/project.json`、`bin/_runtime/` | 直接覆盖（运行时数据，无用户内容） |
| `skip` | `memory-index.md`、`current-task.md` | 跳过，保留用户编辑 |
| `json_merge` | `settings.json` | JSON 结构化合并 |

### 升级流程

```bash
# 1. 预览升级计划
harness upgrade plan /path/to/repo --show-diff

# 2. 确认无误后执行
harness upgrade apply /path/to/repo
# 被覆盖文件自动备份到 .agent-harness/backups/<timestamp>/

# 3. 如有冲突标记，手动解决
# 在文件中搜索 <<<<<<< 标记，选择保留内容
```

### 找回被覆盖的文件

```bash
ls .agent-harness/backups/
# 按时间戳排列的备份目录
```

---

## 工作流技能（Superpowers）

### 技能总览

33 个技能命令（superpowers）+ 4 个通用命令（common），按开发生命周期分为 8 个阶段：

#### 构思与设计阶段

| 命令 | 用途 |
|------|------|
| `/ideate` | 多角度结构化构思，批量生成候选方案并严格筛选 |
| `/brainstorm` | 深度设计对话，产出结构化设计文档 |
| `/spec` | 规格驱动开发——先定义验收标准和需求 ID，再动手写代码 |
| `/adr` | 架构决策记录——记录技术选型的理由、备选方案和取舍 |

#### 计划阶段

| 命令 | 用途 |
|------|------|
| `/write-plan` | 编写 2-5 分钟粒度的实现计划 |
| `/plan-check` | 8+1 维度计划校验 + 最多 3 轮修订循环 |
| `/agent-design-check` | 多 Agent 计划体检（F3/F5/F8/F10 四维度，涉及 squad/dispatch/subagent 时触发） |
| `/todo` | 结构化任务拆分和进度管理 |

#### 执行阶段

| 命令 | 用途 |
|------|------|
| `/tdd` | 测试驱动开发（RED → GREEN → REFACTOR） |
| `/execute-plan` | 按计划逐步执行，每步 checkpoint |
| `/debug` | 4 阶段系统性排障（症状 → 假设 → 验证 → 结论） |

#### 验证与评审阶段

| 命令 | 用途 |
|------|------|
| `/verify` | 完成前全面验证（功能、非功能、边界情况） |
| `/multi-review` | 多人格并行代码评审 |
| `/request-review` | 准备评审请求（上下文摘要） |
| `/receive-review` | 处理评审反馈并逐条修复 |

#### 协作与委派阶段

| 命令 | 用途 |
|------|------|
| `/dispatch-agents` | 一次性并行分发独立子任务（短任务） |
| `/subagent-dev` | 子代理驱动开发（规划者 + 执行者分离） |
| `/squad` | 多 Agent 常驻协作（tmux + worktree + 角色分权） |

#### 安全与质量阶段

| 命令 | 用途 |
|------|------|
| `/cso` | 安全审计（OWASP + STRIDE + 供应链） |
| `/careful` | 危险命令安全拦截 |
| `/health` | 代码质量仪表盘（0-10 综合评分） |

#### 收尾与沉淀阶段

| 命令 | 用途 |
|------|------|
| `/git-commit` | 结构化 Git 提交（变更分类 + 语义化消息） |
| `/finish-branch` | 分支收尾（测试 → 合并 → 清理） |
| `/compound` | 提炼经验写入知识库（lessons + memory-index） |
| `/doc-release` | 发布后文档同步 |

#### 知识与进化阶段

| 命令 | 用途 |
|------|------|
| `/recall` | 按需检索历史教训/任务/参考清单（Grep + BM25 双链路） |
| `/source-verify` | 从官方文档验证框架 API，防止凭记忆编造 |
| `/lint-lessons` | 知识库健康检查（去重、矛盾检测、过时标记） |
| `/retro` | 工程回顾（基于 Git 历史分析） |
| `/evolve` | 自我进化（搜索新项目 → 评估 → 创建 Issue 提案） |
| `/pressure-test` | 压力测试（Skill TDD，7 类压力 × 6 场景，快手 sec-audit-pipeline 吸收） |

#### 通用命令（不受 `--no-superpowers` 影响）

| 命令 | 用途 |
|------|------|
| `/process-notes` | 把产品需求笔记解析为结构化格式 |
| `/digest-meeting` | 把语音转文字记录转为 current-task 或 task-log 条目 |
| `/recall` | 二级检索（Grep → BM25 兜底） |
| `/source-verify` | 验证框架/库 API 真实性 |

#### 元命令

| 命令 | 用途 |
|------|------|
| `/lfg` | 全自主流水线——一键串联从构思到沉淀的全部阶段 |
| `/which-skill` | 技能选择决策树（不确定用哪个技能时运行） |
| `/use-worktrees` | Git worktree 隔离开发指导 |
| `/write-skill` | 编写新的技能文档 |

### 推荐工作流

**标准流程**（适合中大型任务）：

```
/ideate → /spec → /adr → /write-plan → /plan-check → /tdd → /verify → /multi-review → /compound
```

**快速流程**（适合小任务）：

```
/tdd → /verify → /git-commit
```

**全自动流程**：

```
/lfg    # 一键从需求到交付
```

### 技能选择指南

| 场景 | 推荐技能 |
|------|---------|
| 需要探索方向和创意 | `/ideate` |
| 不确定从哪里开始 | `/which-skill` 或 `/brainstorm` |
| 需求模糊需要明确规格 | `/spec` |
| 面临架构决策 | `/adr` |
| 任务复杂需要规划 | `/write-plan` → `/plan-check` → `/execute-plan` |
| 想全自动完成 | `/lfg` |
| 需要写新功能 | `/tdd` |
| 遇到 bug | `/debug` |
| 多个独立子任务 | `/dispatch-agents` |
| 长任务需要多 Agent | `/squad` |
| 实现完成 | `/verify` → `/multi-review` |
| 需要提交代码 | `/git-commit` |
| 任务完成想沉淀经验 | `/compound` |
| 需要安全审计 | `/cso` |
| 收到会议讨论记录 | `/digest-meeting` |
| 需要检索历史教训 | `/recall` |
| 写框架代码前防 API 幻觉 | `/source-verify` |

---

## 分层记忆系统

### 工作原理

记忆系统将项目知识分为四层，按"热度"分级加载，避免全量读取挤占 AI 上下文窗口。

```
L0（规则）   ← 每次会话自动加载
L1（热索引） ← 任务开始时加载
L2（可检索） ← 按需用 /recall 检索
L3（冷归档） ← 显式查询时才读
```

### memory-index.md 格式

```markdown
# 分层记忆索引

## 最近任务（最多 5 条）
- 2026-04-15 接口重构
- 2026-04-14 安全审计修复
...

## 最近教训（最多 10 条）
- 2026-04-15 [测试] mock 数据库导致漏测实际迁移问题
- 2026-04-14 [流程] Code review 超过 400 行应分批
...

## 参考清单
- `accessibility.md` — 无障碍检查清单
- `performance.md` — 性能优化清单
- `security.md` — 安全审查清单
- `testing-patterns.md` — 测试最佳实践
```

### 维护流程

| 操作 | 命令/时机 |
|------|----------|
| 首次建索引 | `harness memory rebuild . --force` |
| 日常更新 | `/compound` 技能自动同步 |
| 关键词检索 | `/recall <关键词>` 或 `harness memory search "关键词"` |
| 参考清单检索 | `/recall --refs <关键词>` |
| 索引不一致修复 | `harness memory rebuild . --force` |

### Lessons 分类体系

教训按 6 个分类组织，条目标题格式为 `## YYYY-MM-DD [分类] 标题`：

| 分类 | 适用内容 |
|------|---------|
| 测试 | 测试策略、覆盖率、mock 陷阱 |
| 模板 | 模板渲染、占位符、文件结构 |
| 流程 | 工作流程、评审、协作 |
| 工具脚本 | CLI、脚本、自动化 |
| 架构设计 | 模块设计、接口、数据流 |
| 集成 API | 外部 API、SDK、协议 |

---

## 多 Agent 协作

框架提供三种多 Agent 协作模式：

### 模式一：dispatch-agents（一次性并行）

适合**短小独立**的子任务，一次分发、一次收回。

```bash
# AI 对话中使用
/dispatch-agents

# 每个子 Agent 有独立日志空间
harness agent init scout-1
harness agent diary scout-1 "开始扫描 src/auth"
harness agent status scout-1 "扫描中，已发现 3 处问题"

# 主 Agent 汇总
harness agent aggregate
```

### 模式二：subagent-dev（规划 + 执行分离）

适合需要**规划者和执行者**角色分离的场景。

### 模式三：squad（常驻多 Agent 协作）

适合**长时间运行**、需要角色分权和实时观察的复杂任务。

#### 前置依赖

- tmux >= 3.0（`brew install tmux` / `apt install tmux`）
- claude CLI 已登录
- Windows 用户需要 WSL

#### 编写 Squad 规格文件

```json
{
  "task_id": "auth-rewrite",
  "base_branch": "master",
  "workers": [
    {
      "name": "scout",
      "capability": "scout",
      "prompt": "探索 src/auth/ 目录，输出架构分析报告"
    },
    {
      "name": "builder",
      "capability": "builder",
      "depends_on": ["scout"],
      "prompt": "等 scout 报告就绪后，按 specs/auth.md 实现重构"
    },
    {
      "name": "reviewer",
      "capability": "reviewer",
      "depends_on": ["builder"],
      "prompt": "对 builder 的代码做 /multi-review"
    }
  ]
}
```

#### 四种角色

| 角色 | 权限 | 适用场景 |
|------|------|---------|
| **orchestrator** | 只读 + 任务派发（禁止 Edit/Write） | 战略协调，不碰代码 |
| **scout** | 只读（禁止 Edit/Write/Bash） | 代码探索、架构分析 |
| **builder** | 读写（完整权限） | 功能实现、TDD |
| **reviewer** | 只读（禁止 Edit/Write/Bash） | 代码评审、质量检查 |

#### 典型操作流程

```bash
# 1. 创建 Squad
harness squad create spec.json

# 2. 监控状态
harness squad status
# ✅ scout (done)
# 🟢 builder (running)
# ⏳ reviewer (pending, blocked by: builder)

# 3. 实时观察 worker 终端
tmux attach -t squad-auth-rewrite

# 4. 启动常驻监控（自动推进 + watchdog）
harness squad watch

# 5. 完成后停止
harness squad stop all
```

#### 依赖触发机制

- 有 `depends_on` 的 worker 创建时写 `pending` 事件，不启动 tmux 窗口
- `harness squad done <worker>` 标记完成
- `harness squad advance` 检查依赖，自动启动可执行的 worker
- `harness squad watch` 常驻轮询，自动完成 advance + watchdog

#### Watchdog 机制

- 检测 tmux session 整体是否存活
- 检测单个 worker 窗口是否消失
- 异常写入 `session_lost` / `worker_crashed` 事件
- 可通过 `touch .agent-harness/.watchdog-skip` 关闭

---

## 变更审计系统

对 `current-task.md`、`task-log.md`、`lessons.md` 三个关键文件的每次修改，记录 WAL 审计日志。

### 审计记录格式

```json
{
  "ts": "2026-04-16T10:30:00",
  "file": "current-task.md",
  "op": "update",
  "agent": "main",
  "summary": "标记步骤 3 完成"
}
```

### 使用场景

| 场景 | 命令 |
|------|------|
| 任务进度更新后 | `audit append --file current-task.md --op update --summary "..."` |
| 归档任务后 | `audit append --file task-log.md --op append --summary "..."` |
| 写入新教训后 | `audit append --file lessons.md --op append --summary "..."` |
| 查看最近变更 | `audit tail` |
| 统计分布 | `audit stats` |
| 清理旧数据 | `audit truncate --before 2026-01-01` |

> Agent 身份从环境变量 `HARNESS_AGENT` 读取，也可通过 `--agent` 参数显式指定。

---

## 会话保护 Hooks

框架提供 4 个 Claude Code 生命周期 hooks，保护任务进度不丢失。

### session-start.sh

**触发时机**：Claude Code 打开项目时

**行为**：
- 显示 `current-task.md` 中未完成的任务
- 重置 context-monitor 工具调用计数器

### stop.sh

**触发时机**：Claude Code 停止时（Ctrl+C）

**行为**：
- 检查 `current-task.md` 是否有未勾选的 `[ ]` checkbox
- 有则阻止停止，提示先更新进度
- 放行方式：`touch .agent-harness/.stop-hook-skip`

### pre-compact.sh

**触发时机**：执行 `/compact` 命令前

**行为**：
- 追加审计检查点到 `audit.jsonl`
- 提醒 AI 把关键决策持久化

### context-monitor.sh

**触发时机**：每次工具调用后（PostToolUse）

**行为**：
- 计数工具调用次数
- 50 次时：提醒考虑 `/compact`
- 100 次时：强烈建议 `/compact`
- 150 次时：警告即将耗尽上下文
- 关闭方式：`touch .agent-harness/.context-monitor-skip`

---

## 插件机制

在目标项目中创建 `.harness-plugins/` 目录，添加团队自定义内容：

```
.harness-plugins/
├── rules/
│   ├── team-security.md      # → .claude/rules/team-security.md
│   └── code-style.md         # → .claude/rules/code-style.md
└── templates/
    └── docs/
        └── team-guide.md     # → docs/team-guide.md
```

### 特性

- 插件文件支持 `{{project_name}}` 等 63 个模板变量
- `rules/` 下的文件合并到 `.claude/rules/`
- `templates/` 下的文件保持目录结构渲染到项目根
- init 和 upgrade 时自动处理

---

## 项目类型详解

### 9 种项目类型

| 类型 | 检测信号 | 专属规则 |
|------|---------|---------|
| **backend-service** | Dockerfile、API 框架 | API 设计、数据库、错误处理 |
| **web-app** | vite/next/webpack 配置 | 无障碍、组件模式 |
| **cli-tool** | `bin` 字段、cli.py | 退出码、管道约定 |
| **library** | VERSION 文件、Cargo.toml | API 契约、语义化版本 |
| **worker** | worker.toml、celery.py | 队列模式、并发控制 |
| **mobile-app** | React Native、pubspec.yaml | 平台差异 |
| **monorepo** | pnpm-workspace、turbo.json | workspace 依赖 |
| **data-pipeline** | dbt_project.yml、dags/ | 数据血缘、转换模式 |
| **meta** | services/registry.yaml + 无源码 | 跨服务协调（见下节） |

### 类型如何影响初始化

1. **生成的规则文件**：每种类型有专属规则模板
2. **评估加分项**：根据类型检查特征文件
3. **交互流程**：meta 类型跳过敏感级别和生产环境问题
4. **预设配置**：`presets/` 下每种类型有独立的行为定义、架构关注点和发布检查项

---

## Meta 项目管理

Meta 项目是微服务系统的**中央大脑**，不含业务代码，管理三件事：

- **服务在哪**：注册表 + 本地路径
- **谁调谁**：依赖关系图
- **业务规则是什么**：领域知识 + 产品需求

### 初始化

```bash
harness init /path/to/meta-repo
# 项目类型选择：meta
```

### 生成的目录结构

```
meta-repo/
├── services/
│   ├── registry.yaml            # 服务注册表
│   └── dependency-graph.yaml    # 依赖关系图
├── business/
│   ├── domains/                 # 领域知识（术语、规则、流程）
│   ├── products/                # 产品需求
│   └── roadmap.md               # 版本规划
├── shared-plugins/              # 分发到各服务的共享规则
├── tasks/                       # 跨服务任务文件
└── BEST-PRACTICES.md            # 最佳实践指南
```

### Meta 专属命令

| 命令 | 用途 |
|------|------|
| `/meta-sync` | 将 meta 信息同步到各服务仓库 |
| `/meta-populate` | 从已注册仓库扫描推理，填充 meta 空缺 |
| `/meta-create-task` | 从会议纪要生成跨服务任务草稿 |
| `/meta-activate-task` | 激活任务，创建 worktree + 注入 current-task |

### 同步机制

```bash
# 同步后各服务仓库生成：
# docs/service-context.md    — 上下游关系和接口影响范围
# .claude/rules/microservice.md — 微服务协作规则
```

---

## 日常运维

### 健康检查

```bash
harness doctor /path/to/repo
```

检查项：
- task-log 使用率（是否有任务记录）
- 教训积累（lessons.md 条目数）
- 占位符检测（docs/ 中的「待补充」）
- 文件长度合理性

### 项目画像导出

```bash
# Markdown 格式（默认）
harness export /path/to/repo

# 保存到文件
harness export /path/to/repo -o snapshot.md

# JSON 格式
harness export /path/to/repo --json
```

适用场景：新人入职、更换 AI 工具、跨团队共享项目信息。

### 任务统计

```bash
harness stats /path/to/repo
```

输出：任务总数、返工率、活跃度趋势、教训积累量。

---

## 项目内嵌运行时

**核心理念**：clone 项目的人无需安装 harness CLI，AI 工作流所需的所有命令从 `.agent-harness/bin/` 调用。

### 两类用户的分工

| 角色 | 工具 | 职责 |
|------|------|------|
| **项目维护者** | `harness` CLI（`pip install -e .`） | init / upgrade / doctor / export / stats / sync |
| **项目使用者** | `.agent-harness/bin/*`（clone 即用） | audit / memory / squad（AI 工作流内使用） |

### 可用命令

```bash
# 等价于 harness audit
.agent-harness/bin/audit append --file lessons.md --op append --summary "..."
.agent-harness/bin/audit tail
.agent-harness/bin/audit stats

# 等价于 harness memory
.agent-harness/bin/memory rebuild . --force
```

### 升级

`.agent-harness/bin/_runtime/` 在 `harness upgrade apply` 时强制覆盖，无需手动维护。

---

## 故障排查

### 初始化问题

| 现象 | 解决方案 |
|------|---------|
| 很多文件被跳过 | 默认不覆盖已有文件，加 `--force` 覆盖 |
| 探测结果不准确 | 正常现象，交互阶段人工确认关键字段 |
| 新项目类型不适配 | 先补 `presets/`，再补模板和测试 |

### 升级问题

| 现象 | 解决方案 |
|------|---------|
| 出现合并冲突标记 | 搜索 `<<<<<<<`，手动选择保留内容 |
| 覆盖了自定义内容 | 从 `.agent-harness/backups/<timestamp>/` 找回 |
| make check 报产物未同步 | 运行 `make dogfood` 同步后重新提交 |

### Squad 问题

| 现象 | 解决方案 |
|------|---------|
| 未找到 tmux | `brew install tmux` / `apt install tmux` |
| worker 启动即退出 | `tmux attach` 看错误；检查 `settings.local.json` |
| capability 没生效 | 检查 Claude Code 版本是否支持 `permissions.deny` |
| watch 立即退出 | tmux session 不存在；先 `tmux ls` 确认 |
| 频繁打印"worker 失联" | tmux 窗口被 kill；`harness squad dump` 查时间点 |
| 想暂时关闭 watchdog | `touch .agent-harness/.watchdog-skip` |

### 记忆系统问题

| 现象 | 解决方案 |
|------|---------|
| memory-index 和 lessons 不一致 | `harness memory rebuild . --force` |
| 索引中缺少某条教训 | 可能是引入分层加载前写的，运行 rebuild |
| /recall 搜不到 | 尝试换同义词，或用 `harness memory search` 做 BM25 检索 |

---

## 配置参考

### 模板变量清单（63 个）

#### 项目元数据

| 变量 | 说明 |
|------|------|
| `project_name` | 项目名称 |
| `project_slug` | 项目名称的 slug 形式 |
| `project_summary` | 项目目标描述 |
| `project_type` | 项目类型 |
| `language` | 主语言 |
| `package_manager` | 包管理器 |
| `sensitivity` | 数据敏感级别 |
| `deploy_target` | 部署目标 |
| `has_production` | 是否有生产环境 |

#### 命令

| 变量 | 说明 |
|------|------|
| `run_command` | 运行命令 |
| `test_command` | 测试命令 |
| `check_command` | 静态检查命令 |
| `ci_command` | CI 命令 |

#### 路径（bullet list 和 inline 两种格式）

| 变量 | 说明 |
|------|------|
| `source_paths_bullets` / `source_paths_inline` | 源码路径 |
| `test_paths_bullets` / `test_paths_inline` | 测试路径 |
| `docs_paths_bullets` / `docs_paths_inline` | 文档路径 |
| `ci_paths_bullets` / `ci_paths_inline` | CI 配置路径 |

#### 评估结果

| 变量 | 说明 |
|------|------|
| `assessment_score` | 评分 (0-100) |
| `assessment_readiness` | 就绪程度描述 |
| `assessment_confidence` | 置信度 |
| `assessment_strengths_bullets` | 优势列表 |
| `assessment_gaps_bullets` | 缺口列表 |
| `assessment_recommendations_bullets` | 建议列表 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `HARNESS_AGENT` | 审计日志中的 Agent 身份标识 |

### Makefile 目标

| 目标 | 说明 |
|------|------|
| `make setup` | 首次 clone 后初始化环境 |
| `make test` | 运行回归测试 |
| `make check` | 仓库健康检查 |
| `make ci` | check + skills-lint + test（提交前运行） |
| `make dogfood` | 同步框架自身的技能/规则文件 |
| `make sync-superpowers` | 从上游拉取最新 skills 变更 |
| `make init TARGET=<path>` | 初始化目标项目 |
| `make assess TARGET=<path>` | 仅评估 |
| `make upgrade-plan TARGET=<path>` | 预览升级 |
| `make upgrade-apply TARGET=<path>` | 执行升级 |
| `make skills-lint` | 技能注册一致性检查 |

---

## 技能选择决策指南

### 按开发阶段选技能

每个阶段看起来有多个命令，但它们不是「二选一」的关系——有的解决不同问题，有的是上下游串联。

#### 第一步：想清楚做什么

> **类比**：`/ideate` 是头脑风暴白板，`/brainstorm` 是设计评审会议。

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| 老板说了个模糊方向，不知道具体做什么 | `/ideate` | 多角度发散，从 32 个想法里筛出 5-7 个靠谱的 |
| 知道要做什么，但不确定怎么设计 | `/brainstorm` | 深入探讨方案细节，产出设计文档 |
| 需求很明确 | 跳过 | |

#### 第一步半：明确需求规格

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| 需求来自非技术人员，比较模糊 | `/spec` | 将模糊描述转为可测试的验收标准 |
| 跨模块改动，涉及 3+ 个文件 | `/spec` | 先明确目标、边界和测试策略 |
| 需求很清楚，已有明确验收标准 | 跳过 | |

#### 第二步：制定计划

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| 需要把设计拆成可执行的步骤 | `/write-plan` | 产出 2-5 分钟粒度的实施计划 |
| 计划写好了，子任务需要排优先级 | `/todo` | 标 P1/P2/P3，管理阻塞关系 |
| 就改一个小文件 | 跳过 | |

#### 第三步：写代码

| 情况 | 用什么 | 为什么 |
|------|--------|--------|
| 写新功能或改现有行为 | **`/tdd`**（最常用） | 先写测试再写实现，质量最高 |
| 有现成计划，想按步骤走 | `/execute-plan` | 逐步执行，每步验证 |
| 任务太大，想拆给子 agent | `/subagent-dev` | 规划+执行分离 |
| 多个互不相关的子任务 | `/dispatch-agents` | 并行做 |
| 遇到 bug 了 | `/debug` | 根因优先，不要猜 |

**80% 的情况用 `/tdd` 就够了。**

#### 第四步：验证和评审

这四个命令是**顺序关系**，不是选择关系：

```
代码写完 → /verify（自检）→ /multi-review（AI 6 角色评审）
        → /request-review（给人看）→ /receive-review（处理反馈）
```

快速模式：只用 `/verify` + `/multi-review`（占 90% 场景）。

#### 第五步：安全和质量

| 情况 | 用什么 |
|------|--------|
| 发布前确认没有安全漏洞 | `/cso` |
| 想知道代码整体质量如何 | `/health` |
| 要执行危险操作 | `/careful`（自动生效） |

这三个**随时可用**，不需要等到特定阶段。

#### 第六步：收尾

```
功能完成 → /git-commit → /compound（沉淀经验）→ /finish-branch
        → /doc-release（同步文档）→ /retro（每周回顾）
```

### 一图看懂完整流程

```
 ┌─────────── 不确定用什么？ → /which-skill ───────────┐
 │                                                      │
 │  ┌──────────── 想全自动？ → /lfg ──────────────┐    │
 │  │                                              │    │
 │  │   构思 → 规格 → 计划 → 执行 → 验证 → 收尾   │    │
 │  │                                              │    │
 │  │  随时可用：/cso  /health  /careful            │    │
 │  └──────────────────────────────────────────────┘    │
 └──────────────────────────────────────────────────────┘
```

### 按任务规模速查

| 规模 | 推荐路径 |
|------|---------|
| **微小** — 改一行配置、修个 typo | 直接改 → `/git-commit` |
| **小** — 修一个 bug、加一个字段 | `/tdd` → `/verify` → `/git-commit` |
| **中** — 新增一个功能模块 | `/spec` → `/write-plan` → `/tdd` → `/verify` → `/multi-review` → `/compound` |
| **大** — 重构、多模块联动 | `/ideate` → `/spec` → `/write-plan` → `/lfg` |
| **不确定** | `/which-skill` 让 AI 推荐 |

---

## `/lfg` 深度指南

`/lfg`（Let's Go）是框架的核心能力——输入一句话需求，AI 自动完成从计划到交付的全部流程。

### 基本用法

```
/lfg 你的任务描述
```

任务描述写得越具体，效果越好：

```
❌ /lfg 加个搜索
✅ /lfg 给用户列表页增加搜索功能，支持按姓名和邮箱模糊搜索，搜索结果实时更新
```

### 完整生命周期（10 个阶段）

| 阶段 | 做什么 | 需要人工参与？ |
|------|--------|--------------|
| 0 理解任务 | 复述任务、定义验收标准、读历史教训 | 任务不清时会问 |
| 1 环境准备 | 记录基线 commit、创建工作分支、跑基线测试 | 否 |
| 2 构思 | 多角度生成候选方案（仅大型任务） | 选方向 |
| 3 计划 | 生成实施计划 + 质量检查 | 确认计划 |
| 4 实施 | TDD 逐步执行，每步提交 | 否 |
| 5 评审 | 6 角色并行评审 | 否 |
| 6 修复 | 根因分析 + 修复，最多 3 轮 | 3 轮不过时介入 |
| 7 验证 | 全量测试 + 逐条核验验收标准 | 否 |
| 8 质量对比 | 与基线对比测试数/警告数 | 否 |
| 9 沉淀 | 提炼经验写入 lessons.md + lint 去重 | 否 |
| 10 收尾 | 合并/PR/保留/丢弃 + 文档同步 | 选择收尾方式 |

### 四条通道（自动选择）

| 通道 | 适用场景 | 走哪些阶段 | 举例 |
|------|---------|-----------|------|
| **快速** | 改一行、修 typo | 直接改 → 测试 → 提交 | `把 v1.0 改成 v1.1` |
| **轻量** | 小 bug、加个字段 | 简要计划 → TDD → 验证 | `修复密码错误返回 500` |
| **标准** | 新功能、新接口 | 完整 10 阶段（跳过构思） | `给订单 API 增加日期筛选` |
| **完整** | 跨模块、架构级 | 完整 10 阶段 + 构思 | `把 session 迁移到 JWT` |

AI 会告诉你它选了哪条通道和原因，你可以随时覆盖。

### 知识驱动：越用越快

```
lessons.md ──读取──→ /lfg 计划阶段（避开已知陷阱）
                          ↓
                     /lfg 沉淀阶段（记录新教训）──写入──→ lessons.md
```

- **第一次**做某件事：需要研究，可能走弯路
- **第 N 次**做类似的事：AI 从 lessons.md 读到之前的记录，越来越快、越来越少出错

### 中断和恢复

随时可以中断（关闭终端、网络断了），不会丢进度。重新打开 Claude Code，AI 自动从 `current-task.md` 中的进度记录恢复，接着干而不是从头来。

### 什么任务最适合 `/lfg`

| 最适合 | 也行但不是最优 | 不适合 |
|--------|-------------|--------|
| 需求明确的新功能 | 大范围重构（建议先 `/ideate`） | 纯粹的探索/调研 |
| 已知的 bug 修复 | 涉及大量人工决策的工作 | 需要频繁与产品确认的功能 |
| API 端点增改 | 第一次搭建项目骨架 | 学习性质的尝试 |

**经验法则**：如果能用 1-2 句话说清楚「做什么」和「做到什么程度算完」，就适合 `/lfg`。

---

## 框架维护者指南

以下内容面向 harness-starter 框架本身的维护者，不适用于使用 harness 初始化后的目标项目。

### 上游同步

框架的技能模板改编自 3 个上游项目。当上游更新时：

```bash
make sync-superpowers          # 拉取上游最新变更报告
python scripts/sync_superpowers.py --check  # 查看缓存状态（不访问网络）
```

上游源：obra/superpowers（14 个基础技能）、EveryInc/compound-engineering-plugin（6 个增强技能）、garrytan/gstack（5 个运维技能）。同步只产出报告，不自动修改模板。

### 自举（Dogfooding）

框架对自身运行了 `harness init`。修改模板后需同步框架自身的产物：

```bash
make dogfood     # 同步 .claude/commands/ 和 .claude/rules/
make ci          # 自动检测漂移，未同步会报错
```

### 自我进化（/evolve）

`/evolve` 自动搜索 AI 编码领域的新项目 → 评估独特价值 → 创建 Issue 提案。审批通过后用 `/lfg` 实施集成。

### 外部工具集成

[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — 安装后可用 `/codex:review` 获取 Codex 的独立代码评审，与 `/multi-review` 互补。

---

## 常见问题

### 初始化

| 问题 | 解决 |
|------|------|
| 初始化后 AI 会自动做什么？ | 读取 `current-task.md` 中预填的分析任务，自动补全 docs/ |
| 如何关闭工作流技能？ | `harness init --no-superpowers` 或 `.harness.json` 中 `"superpowers": false` |
| 项目类型选错了？ | `harness init --force` 重选，或直接改 `project.json` 的 `project_type` |
| 探测结果不准确？ | 用 `--config` 或 `.harness.json` 显式指定，优先级高于自动探测 |

### 升级

| 问题 | 解决 |
|------|------|
| 升级后自定义内容会丢失吗？ | 不会。自动备份到 `.agent-harness/backups/`，先用 `--show-diff` 预览 |
| 出现合并冲突标记 | 搜索 `<<<<<<<`，手动选择保留内容 |

### Meta 项目

| 问题 | 解决 |
|------|------|
| 如何起步？ | `harness init` 选 `meta` → 填 `registry.yaml` → `/meta-populate` → `/meta-sync` |
| 改了 `service-context.md` 没生效？ | 该文件由 `harness sync` 生成，每次覆盖。改源头（registry/dependency-graph/domains） |

### CI 集成

```bash
harness init /path/to/project --assess-only --json          # 评估（JSON 输出）
harness init /path/to/project --config .harness.json --non-interactive  # 非交互初始化
```
