# Spec：分层记忆加载（方案 C · Index + 按需展开）

> Issue：GitHub #10 | 来源：MemPalace | 日期：2026-04-12 | 分支：feat/layered-memory

## 目标

让 `.agent-harness/` 下的记忆文件在随项目积累增长时，**不再膨胀 AI 任务启动上下文**。

## 非目标

- 不做目录分层（L2 主题分区）——方案 B 的工作量在当前阶段得不偿失
- 不做 Python 侧 `MemoryLayer` 抽象——方案 D 对脚手架过度工程
- 不改变 `lessons.md` / `task-log.md` 的原有单文件结构和写入方式（历史保持不变）

## 层级映射

| 层 | 承载 | 加载时机 | 预算 |
|---|------|---------|------|
| **L0** | `project.json`（项目身份） | Claude 读 AGENTS.md 时顺带 | 既有 |
| **L1** | `current-task.md` + 新增 `memory-index.md` | task-lifecycle 规则明示读取 | ≤ 200 tokens |
| **L2** | `lessons.md` 全文 | 按需（`/recall` 技能或 grep） | 不计 |
| **L3** | `task-log.md` 全文 | 显式（`/recall --history` 或 grep） | 不计 |

## 新增文件

### `.agent-harness/memory-index.md`

**格式**（示例，初始模板为空骨架）：

```markdown
# Memory Index

> 热知识精华索引。详情在 `lessons.md` / `task-log.md`。
> 需要深入某话题 → 使用 `/recall <关键词>` 技能或直接 grep。

## 最近教训（保留最多 10 条）

- YYYY-MM-DD **一句话标题** — 避免什么后果

## 最近任务（保留最多 5 条）

- YYYY-MM-DD 任务简述

## 主题索引（可选，按关键词定位）

- 关键词 → lessons.md 中相关条目标题（供 grep 用）
```

**维护规则**：
- `/compound` 写新教训时，在"最近教训"顶部插一行，超过 10 条时挤出最老的
- 任务归档（task-log 写新记录）时，顶部插一行，超过 5 条挤出最老
- "主题索引"段由人/AI 周期性整理，不强制

## 模板变更

### `src/agent_harness/templates/common/.agent-harness/memory-index.md.tmpl`（新建）

内容即上述骨架。

### `src/agent_harness/upgrade.py`

在 `FILE_POLICIES` 中添加：

```python
".agent-harness/memory-index.md": "skip",
```

老项目升级时：文件不存在 → 从模板创建；已存在 → 跳过（保留用户编辑）。

### `src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`

**第 0 步的读取表**修改：

| 文件 | 读什么 |
|------|--------|
| `.agent-harness/current-task.md` | 有无未完成任务 |
| `docs/product.md` | 已有功能列表 |
| `docs/architecture.md` | 模块边界 |
| `AGENTS.md` | 硬规则约束 |
| `.agent-harness/memory-index.md` | **（新）热知识索引，命中相关话题时再深入** |

**新增说明段**（紧跟表格）：

> **深入搜索**：memory-index.md 提示当前任务可能关联某条教训或历史任务时，使用 `/recall <关键词>` 技能或 `grep` 读取 `lessons.md` / `task-log.md` 的具体节。不要默认读取全量。

### `src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`（新建）

新技能命令，模板内容定义：
- **用途**：在 `lessons.md` / `task-log.md` 中按关键词检索
- **参数**：`<关键词>` 或 `--history <关键词>`（后者只查 task-log）
- **行为**：Grep 对应文件，返回匹配的二级标题（`##`）所在节

### `src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl`

增加一段维护 `memory-index.md` 的步骤（写完新教训后必须同步更新 index）。

### `src/agent_harness/templates/common/.agent-harness/project.json.tmpl`

**可选**：将 memory-index 纳入命令注册（仅当当前 project.json 有 commands/doc 映射时）。检查现状后决定。

## CLI 变更

### `harness memory rebuild <target>`（可选，本次实现）

- **用途**：从现有 `lessons.md` 和 `task-log.md` 扫描生成 `memory-index.md`
- **触发**：老项目首次启用分层时；或 index 需要重置时
- **行为**：取 lessons.md 末尾 10 条 `##` 标题 + task-log.md 末尾 5 条 `##` 标题写入 index
- **模块**：新建 `src/agent_harness/memory.py`（< 100 行），`cli.py` 注册

## 文档同步

- `docs/product.md` — "框架提供什么" 增加一条"分层记忆"；CLI 表加一行
- `docs/architecture.md` — 模块职责加 `memory.py`
- `docs/runbook.md` — 使用示例和故障排查
- `AGENTS.md` — 快速地图、常用命令补充
- `CHANGELOG.md` — 新增条目
- `.agent-harness/lessons.md` — 任务完成后追加一条分层加载设计教训

## 测试

新增测试（在 `tests/` 下合适文件）：

1. `memory-index.md.tmpl` 存在且占位符有效
2. `upgrade.py` FILE_POLICIES 包含 memory-index.md 为 skip
3. 初始化后目标项目存在 `memory-index.md`
4. task-lifecycle 规则模板含 "memory-index" 字样，不再强制读 lessons.md 全量
5. `/recall` 技能模板存在且文档完整
6. `harness memory rebuild` CLI：空 lessons.md → 生成空段；含 3 条 → 正确列出；> 10 条 → 截断到 10 条
7. `harness memory rebuild` 尊重 skip 策略——已存在 index 时不覆盖（或仅在 `--force` 时覆盖）

目标：测试 176 → ≥ 184。

## 验收标准（映射到 Issue）

| 验收 | 如何验证 |
|------|---------|
| 1. `.agent-harness/` 支持分层 | `memory-index.md` 存在，lessons/task-log 仍在 |
| 2. task-lifecycle 默认只读 L0+L1 | rule 模板中读取表已改 |
| 3. 存在显式触发 L2/L3 的方式 | `/recall` 技能 + 直接 grep 提示 |
| 4. upgrade 平滑迁移 | upgrade 测试通过；老项目缺 index 时自动创建 |
| 5. 9 种类型同步 | init 任一类型都生成 memory-index.md（common 模板，天然适配） |
| 6. 测试全绿 | `make ci` 通过，新增测试 ≥ 8 个 |
| 7. 文档同步 | product/architecture/runbook/AGENTS/CHANGELOG/lessons 均更新 |
| 8. Issue 关闭 | LFG Phase 10.6 执行 |

## 风险和缓解

| 风险 | 缓解 |
|------|-----|
| `memory-index.md` 与 `lessons.md` 不同步 | `/compound` 技能文档明示两步都做；`health` 技能加一致性检查（后续） |
| 老项目升级 index 是空的 → 反而丢信息 | 提供 `harness memory rebuild` 一次性 bootstrap |
| "主题索引"难以自动维护 → 长期腐化 | 该段标为"可选"，不是阻塞性 |
| task-lifecycle 规则被 AI 忽视仍读全文 | rule 措辞强化："默认不读 lessons.md 全量，除非命中索引提示" |

## 范围边界

**做**：上文列出的模板、规则、技能、CLI、测试、文档。

**不做**：
- 文件拆分到 `memory/` 子目录
- Python `MemoryLayer` 抽象
- 自动化主题分类（L2 主题分区）
- 对非 `.agent-harness/` 外的记忆源（如 git log 摘要）做分层
