---
description: 任务生命周期管理 — 确保 current-task.md 被使用
---

# 任务生命周期

## 上下文分层原则

上下文是 AI 输出质量的最大杠杆。**太少** → 幻觉 API、违反约定、重复造轮子；**太多** → 失焦、混乱、成本飙升。本规则告诉你"哪些必读、哪些按需、哪些只在显式查询时才看"。

### 五层上下文层级（按持久度从高到低）

| 层 | 承载 | 加载时机 | 在本项目的映射 |
|---|------|---------|---------------|
| **L0 Rules** | 不变的硬规则、项目身份 | 每次会话都加载 | `AGENTS.md`、`CLAUDE.md`、`.claude/rules/` |
| **L1 Specs & Hot Knowledge** | 当前任务 + 最近教训精华 | 任务开始时必读 | `current-task.md` + `memory-index.md` |
| **L2 Warm Knowledge** | 可能相关的历史细节、专业参考 | 按需检索 | `lessons.md` 全文、`references/*.md`（a11y / perf / security / testing） |
| **L3 Cold Archive** | 完整历史、不常查 | 显式查询 | `task-log.md` 全文 |
| **L4 Conversation** | 当前对话已有内容 | 天然积累 | 当前 session 的消息 |

### 操作准则

- **L0、L1 默认读取**——没有这两层的上下文等于闭眼工作
- **L2、L3 按需检索**——用 `/recall <关键词>` 或针对性 grep，禁止默认全量读
- **Rules Files 是高杠杆**：一次写 AGENTS.md 或 `.claude/rules/X.md`，受益所有后续会话；写 memory-index 单条次之；写 `current-task` 只影响本任务
- **冲突消歧优先级**：用户显式指示 > L0 硬规则 > L1 约定 > L2 参考 > L3 历史。高层覆盖低层
- **上下文退化信号**：AI 输出开始违反已知约定、重复建议已实现的功能、幻觉依赖 API —— 说明 L0/L1 没覆盖到，或 AI 没读。立刻补加载

这一分层是 L0-L3 分层记忆架构（见 `docs/decisions/0001-layered-memory-loading.md`）的外部投影。所有下面的"读取表"都遵循它。

## 收到新任务时（最高优先级）

收到用户的新开发任务时，按以下顺序执行：

### 第 0 步：读取项目知识

在写任何内容之前，先读以下文件建立上下文：

| 文件 | 读什么 |
|------|--------|
| `.agent-harness/current-task.md` | 有无未完成任务（有则先问用户：继续还是替换） |
| `docs/product.md` | 已有功能列表，避免重复建设 |
| `docs/architecture.md` | 模块边界和文件结构，知道改哪里 |
| `AGENTS.md` | 硬规则约束，不可违反 |
| `.agent-harness/memory-index.md` | 热知识精华索引（最近教训 + 最近任务 + 主题索引） |

> **注意**：**默认不读 `.agent-harness/lessons.md` 或 `task-log.md` 全量**。当 memory-index 命中相关话题，或你从任务描述判断可能涉及历史踩坑，使用 `/recall <关键词>` 技能做定向检索（或在 lessons.md / task-log.md 上 grep 特定节）。这是分层记忆加载的 L1→L2/L3 上行路径，避免上下文窗口被历史积累挤占。

### 第 1 步：写 current-task.md

写入以下字段，每个都不能留空：

1. **任务目标**：要做什么、为什么做
2. **假设清单**：列出所有隐含假设（技术选型、范围边界、用户意图的理解）。
   格式：`- 假设：... | 依据：...`。没有依据的假设标注"待确认"
3. **多解读列表（仅在以下任一**触发条件**满足时必填，吸收自 [Karpathy 原则 1](https://github.com/forrestchang/andrej-karpathy-skills) "If multiple interpretations exist, present them - don't pick silently"）**：
   - 触发条件：需求含模糊词（"优化"、"改进"、"清理"、"支持"、"更好"）/ 涉及范围边界不清 / 涉及取舍的设计决策（如选用某框架 / 模式 / 数据结构）
   - 不触发：明确的小修复（"把 X 改成 Y"）/ 已有规格的执行 / 用户已经选定方向
   - 格式：列 2-3 条**有意义不同**的解读，每条标注「优势 / 代价 / 适用条件」，等用户在第 2 步选定一种再继续
   - **禁止**：无歧义任务也强行列多解读 → 噪音爆炸（违反 simplicity 准则 1「不要超出用户要求的功能」）
4. **计划步骤**：checkbox 格式
5. **测试场景清单**（三类必须都有，具体见 testing rule）：
   - **正常路径**：核心功能的预期行为
   - **边界情况**：空值、极值、并发、大数据量等
   - **错误路径**：非法输入、权限不足、依赖不可用等
6. **完成标准**：可验证的条件

### 第 2 步：展示并等待用户确认

写完后，**不要立即开始编码**。先向用户展示 current-task.md 的内容摘要，重点突出：
- 假设清单（有没有理解错的）
- 多解读列表（如已触发，等用户选一种）
- 范围边界（做什么、不做什么）
- 完成标准（怎样算完成）

然后明确询问："需求理解是否准确？有没有要调整的？"

**额外要求**（吸收自 Karpathy 原则 1 "Name what's confusing" 和 "If a simpler approach exists, say so"）：

- **显式说明哪里不清楚**（Name what's confusing）：如果对需求某部分仍有疑问，**不要问"对吗？"** 这种笼统问题。直接命名出来：「我不清楚 X 应该是 A 还是 B」「Y 的边界条件没说，我假设是 Z」「Z 部分缺少证据，我会按 W 处理但请确认」。让用户能精确回答而不是猜你在问什么
- **若发现更简单方案主动提出**（push back 入口）：如果对照需求，发现一个明显更简单的实现路径（更少代码 / 更少依赖 / 更少抽象），**必须**在确认前主动提出来，让用户裁决。不要默默走更复杂的路径只因「用户当时是这么说的」——push back 是 simplicity 准则的一部分（详见 `anti-laziness.md` 门禁 5 Push Back 子节）

用户确认后才进入编码阶段。

### 第 3 步：判断是否需要 /spec

满足以下**任一条件**时，必须先运行 `/spec` 再动手：
- 需求描述超过两句话
- 预计涉及 3 个以上文件
- 包含模糊词（"优化"、"改进"、"支持"、"更好"等无明确标准的词）
- 涉及新模块或新架构模式

不满足以上条件的简单任务，跳过 /spec 直接进入执行。

写完之后，**先写测试再写实现**。测试先跑失败（证明测试有效），再写代码让测试通过

## 执行过程中

每完成一个步骤，立即更新 current-task.md 的 checkbox 为 `[x]`。
禁止等全部做完再批量更新，因为会话中断会丢失所有进度。

## 失败分级（静默恢复 → 卡死检测）

失败不全是"卡死"。Claude Code 内部有 7 个 continue site 做静默恢复（PTL 排水、max_output_tokens 升级、反应式压缩等），多数瞬时失败用户根本看不到。本项目对齐这一理念，把失败分为两级：

### L0 静默恢复（自动，不计入卡死次数）

以下失败类型**自动重试 1 次**，不触发 StuckDetector，不需要用户介入：

- **命令超时**：Bash 命令因网络或 I/O 导致超时 → 缩短超时重跑
- **工具输出截断**：结果超过预算被截断 → 加 `| head` 或 `--limit` 重跑
- **临时文件冲突**：写入 /tmp 路径冲突 → 换路径重试
- **git 锁文件**：`.git/index.lock` 残留 → 等 1 秒后重试

**重试 1 次后仍失败** → 升级为 L1 卡死检测，正式计数。

### L1 卡死检测（StuckDetector）

AI 容易在同一个失败模式上绕圈（改 A 坏 B、改 B 又坏 A），浪费上下文且越修越乱。为此设硬性停下规则：

### 触发条件（任一满足就停）

- **TDD 循环**：连续 3 次 RED 未进展（同一测试、同一报错、同一根因假设）
- **调试循环**：同一根因假设连续 3 次被证伪
- **评审修复**：对同一条评审意见连续 3 次修复仍被标 P0/P1
- **命令失败**：同一命令连续 3 次以相同错误失败（不是新错，且已过 L0 静默恢复）

### 触发后必做（不是建议，是强制）

1. **立即停下**，不再继续尝试相同方向
2. 在 current-task.md 中追加一节"卡点记录"：
   - 卡在哪里（具体文件、具体失败）
   - 我已经试过什么（列 3 条尝试）
   - 为什么这些尝试失败（根因分析）
3. **输出 3 个候选方向**给用户选：
   - 候选 A：<换技术路线>
   - 候选 B：<缩小范围标 out-of-scope>
   - 候选 C：<回退到某个 lfg/step-N tag 重做>
4. 🔴 等用户选，禁止自行决定继续

### 为什么 3 次不是 5 次

每次失败消耗 ~500-2000 tokens 上下文。3 次 = 1.5-6k tokens + 心智负担，已足够证明"现在的方向不对"。继续试只是沉没成本谬误。

## 关键文件变更审计（WAL）

每次修改以下三个关键文件后，追加一条审计记录到 `.agent-harness/audit.jsonl`：

- `current-task.md`
- `task-log.md`
- `lessons.md`

用项目自带的运行时追加（推荐，无需装 harness CLI）：

```bash
.agent-harness/bin/audit append --file current-task.md --op update --summary "标记步骤3完成"
.agent-harness/bin/audit append --file lessons.md --op append --summary "新增测试相关教训"
.agent-harness/bin/audit append --file task-log.md --op append --summary "归档任务 Issue #42"
```

> `.agent-harness/bin/audit` 是项目 init 后自带的纯 stdlib 运行时脚本，clone 即用。
> 等价于 `harness audit`（但不需要你机器上装 harness CLI）。

**op 四选一**：`create`（首次创建）/ `update`（原地修改）/ `append`（尾部追加）/ `delete`（删除）。

**agent 身份**：默认从环境变量 `HARNESS_AGENT` 读取，可用 `--agent` 显式覆盖。

**为什么要写**：
- 多 agent 协作时能看清谁在什么时候改了什么，避免互相覆盖
- 误操作后可以定位到具体时间点回滚
- `.agent-harness/bin/audit tail` 随时回看最近 N 条变更
- `.agent-harness/bin/audit stats` 查看按文件/agent 分布

**不做什么**：审计日志是追溯用的旁路，不替代 git；不做自动 rotation（用 `.agent-harness/bin/audit truncate --before YYYY-MM-DD` 手动清理）。

## 并行子 agent 的日志隔离

当通过 `/dispatch-agents` / `/subagent-dev` 并行分发多个子任务时，**每个子 agent 必须使用独立的 diary/status 空间**，不得并发写共享的 current-task.md：

```bash
harness agent init <agent-id>                        # 创建 .agent-harness/agents/<id>/
harness agent diary  <agent-id> "开始扫描 src/utils"  # 追加过程日志
harness agent status <agent-id> "等待依赖 X 完成"      # 覆盖当前状态
harness agent list                                    # 主 agent 查看全部
harness agent aggregate [<id>...]                     # 汇总 diary 供主 agent 合并进 task-log
```

**id 规范**：`^[a-z0-9][a-z0-9-]{0,30}$`（与 /squad worker 命名规范一致）。

**何时用**：
- ✅ `/dispatch-agents` 派出的 2+ 独立子任务 → 每个子任务自取 id 写 diary
- ✅ `/subagent-dev` 执行者 → 执行者写 diary，计划者读 aggregate 汇总
- ❌ `/squad` 已有 `squad/<task>/workers/<name>/` 隔离，**不要**改用 agents/（两套机制会撞）
- ❌ 单 agent 任务不需要，用 current-task.md 即可

**主 agent 收尾时**：读 `harness agent aggregate`，把值得归档的内容写入 `task-log.md`（不自动 merge，主 agent 决定）。

**与 audit.jsonl 的关系**：
- `agents/<id>/diary.md` = "这个 agent 在想什么 / 做什么"（过程）
- `audit.jsonl` = "这个 agent 改了哪个文件 / 何时"（结果）
- 两者互补不重复

## Context Ownership（Agent 上下文所有权）

派出任何子 agent 时（`/squad` worker、`/dispatch-agents` 子任务、`/subagent-dev` 执行者），其 prompt + 初始上下文**必须显式设计**，不得依赖默认拼接。

灵感自 [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) Factor 3 "Own Your Context Window"。

### 显式设计的最小要件

每个子 agent prompt 必须写明：

1. **做什么**（任务边界）：一句话说明这个 agent 的产出物
2. **读哪些**（输入文件清单）：精确路径，不写"相关代码"
3. **写哪里**（输出位置）：具体文件路径 / mailbox event / diary 段落
4. **完成条件**（验收标准）：可机械判定的"完成 vs 未完成"
5. **遇阻如何**（异常路径）：超时 / 依赖缺失 / 测试失败时输出什么，由谁接手

### 反模式

- ❌ "你看着项目情况，做用户搜索功能" —— 缺全部 5 要件
- ❌ "读相关代码" —— 不具体，agent 会自行扩展上下文到整个仓库
- ❌ 多个 worker 默认共享 `current-task.md` 做并发读写 —— 违反"并行子 agent 的日志隔离"

### 与分层记忆的关系

L0（规则）和 L1（热索引）由 Claude Code session 加载规则自动注入，子 agent 不用重复。但子 agent 的**任务级上下文**（输入文件、引用的 references、关联的 lessons 教训）必须在 prompt 里列出——即便是主 agent 刚加载过的内容，子 agent 不一定能继承。

### 违反检测

- 涉及多 agent 的计划由 `/agent-design-check` F3 维度审计
- `.claude/rules/agent-design.md` 定义 F5/F8/F10 配套硬约束

## 实现完成后 → 进入"待验证"状态

agent 自测通过后，**不要**直接写 task-log 和清空 current-task。而是：

1. 在 current-task.md 顶部标记 `## 状态：待验证`
2. 告诉用户"可以验证了"，说明如何验证
3. **保留 current-task.md 不动**，等待用户反馈

## 用户验证通过 → 正式完成

用户确认通过后（明确说"可以"、"没问题"、"通过"等），才执行：

1. 在 `.agent-harness/task-log.md` 末尾追加一条记录，必须包含以下字段：
   - **需求**：用户原话或一句话概括
   - **做了什么**：具体改动摘要
   - **关键决策**：为什么选了这个方案（如有取舍）
   - **改了哪些文件**：文件列表
   - **完成标准**：本次通过的 checkbox
2. 清空 current-task.md（只保留标题和空模板）

## 用户验证不通过 → 返工

用户反馈有问题时，**不是新任务**，在当前 current-task 里继续：

1. 在 current-task.md 中追加返工记录（用户反馈了什么、要修什么）
2. 直接修复，逐步更新 checkbox
3. 修完后重新进入"待验证"状态
4. 同时在 `.agent-harness/task-log.md` 追加一条返工记录（用户反馈、根因、修复内容）
