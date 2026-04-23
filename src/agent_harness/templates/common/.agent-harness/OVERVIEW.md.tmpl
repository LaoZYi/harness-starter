# .agent-harness/ 导航

## 职责

承载 Agent Harness 的全部持久化状态。每个子项对应分层记忆架构（L0 Rules / L1 热索引 / L2 按需 / L3 冷归档）的一部分或 agent 协作的基础设施。

## 关键文件 / 目录

### L1 热知识（每次进项目默认加载）

- `current-task.md` — 当前任务目标、假设、计划、测试场景、完成标准；任务生命周期核心状态文件
- `memory-index.md` — 最近教训 + 最近任务 + 参考清单 + 主题索引，默认只读本文件代替读全量 lessons/task-log

### L2 温知识（按需检索）

- `references/` — 专业检查清单（accessibility / performance / security / testing / requirement-mapping）；入口看 `references/OVERVIEW.md`
- `lessons.md` — 历史教训沉淀，用 `/recall --lessons <关键词>` 查询

### L3 冷归档

- `task-log.md` — 已完成任务的全量记录，用 `/recall --history <关键词>` 查询

### 协作基础设施

- `agents/<id>/` — `/dispatch-agents`、`/subagent-dev` 派出的子 agent 的独立 diary / status，互不覆盖
- `squad/<task>/` — `/squad` 常驻协作的 mailbox.db、workers/<name>/ 隔离工作区
- `bin/` — 项目内嵌运行时（audit / memory / squad），clone 即用无需装 CLI
- `audit.jsonl` — current-task / task-log / lessons 三个文件的变更 WAL
- `project.json` — 项目画像（语言、包管理器、命令、类型、自定义 answers）

## 推荐阅读顺序

新进 AI：
1. 先扫本文件了解目录语义
2. 读 `current-task.md` 看有无进行中的任务
3. 读 `memory-index.md` 拿热知识
4. 按任务需要用 `/recall` 钻 L2/L3

## 触发场景

| 场景 | 去哪个文件 |
|---|---|
| 刚进项目 / session 启动 | `current-task.md` + `memory-index.md` |
| 怀疑踩过类似坑 | `/recall --lessons <关键词>` |
| 想找某历史任务的决策 | `/recall --history <关键词>` |
| 需要专业 checklist | `references/OVERVIEW.md` 先导航 |
| 多 agent 并行任务状态 | `agents/<id>/` 或 `squad/<task>/mailbox.db` |
| 追溯文件变更时间线 | `.agent-harness/bin/audit tail` |

## 维护约定

- `current-task.md` / `lessons.md` / `task-log.md` 的每次改动都要走 `audit append`（`.claude/rules/task-lifecycle.md` 硬规则）
- `memory-index.md` 由 `/compound` 自动维护，也可 `harness memory rebuild .` 强制重建
- 本文件 + `ABSTRACT.md` 由「动 `.agent-harness/` 下文件结构的 agent」顺手维护（见 `.claude/rules/documentation-sync.md` 目录导航层）
