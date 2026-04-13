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
3. **计划步骤**：checkbox 格式
4. **测试场景清单**（三类必须都有，具体见 testing rule）：
   - **正常路径**：核心功能的预期行为
   - **边界情况**：空值、极值、并发、大数据量等
   - **错误路径**：非法输入、权限不足、依赖不可用等
5. **完成标准**：可验证的条件

### 第 2 步：展示并等待用户确认

写完后，**不要立即开始编码**。先向用户展示 current-task.md 的内容摘要，重点突出：
- 假设清单（有没有理解错的）
- 范围边界（做什么、不做什么）
- 完成标准（怎样算完成）

然后明确询问："需求理解是否准确？有没有要调整的？"

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

## 关键文件变更审计（WAL）

每次修改以下三个关键文件后，追加一条审计记录到 `.agent-harness/audit.jsonl`：

- `current-task.md`
- `task-log.md`
- `lessons.md`

用 CLI 追加（推荐）：

```bash
harness audit append --file current-task.md --op update --summary "标记步骤3完成"
harness audit append --file lessons.md --op append --summary "新增测试相关教训"
harness audit append --file task-log.md --op append --summary "归档任务 Issue #42"
```

**op 四选一**：`create`（首次创建）/ `update`（原地修改）/ `append`（尾部追加）/ `delete`（删除）。

**agent 身份**：默认从环境变量 `HARNESS_AGENT` 读取，可用 `--agent` 显式覆盖。

**为什么要写**：
- 多 agent 协作时能看清谁在什么时候改了什么，避免互相覆盖
- 误操作后可以定位到具体时间点回滚
- `harness audit tail` 随时回看最近 N 条变更
- `harness audit stats` 查看按文件/agent 分布

**不做什么**：审计日志是追溯用的旁路，不替代 git；不做自动 rotation（用 `harness audit truncate --before YYYY-MM-DD` 手动清理）。

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
