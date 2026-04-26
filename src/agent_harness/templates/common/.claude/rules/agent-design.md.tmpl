---
description: 多 agent 协作的设计硬约束（12-factor-agents 适配）
---

# Agent 设计规则

本规则仅在涉及**多 agent 协作**时适用：`/squad`、`/dispatch-agents`、`/subagent-dev`、以及任何派出子 agent 的场景。单 agent 任务（日常 `/tdd`、`/debug` 等）不受此规则约束。

规则源自 [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)，但**只吸收适用于本项目的 Factor 5/8/10**，详见 `/agent-design-check` 的附录。

## F8（Control Flow）硬约束：worker 内不得自持循环和重试

- **禁止**：在 worker prompt 里写"失败就重试 N 次"、"遍历列表直到完成"、"循环直到 X 为真"
- **正确**：循环 / 重试 / 分支逻辑由**外部调度器**执行
  - `/squad` 场景：`.agent-harness/bin/squad watch` 的 watchdog + advance
  - `/dispatch-agents` 场景：主会话根据子 agent 聚合结果决定是否再派
  - `/subagent-dev` 场景：规划者 agent 在执行者 agent 完成后决定下一步

**理由**：LLM 持有的循环状态对外不可见。失败时无法精确回退到某一次迭代，状态回滚、日志追踪、可观测性全部失效。把控制流外移后，每次 LLM 调用变成一个幂等函数，可审计、可重试、可并行。

**违反检测**：`/agent-design-check` F8 维度 + `/plan-check` 第 9 维度会在 worker prompt 中扫关键词（"重试"、"retry"、"循环"、"loop"、"直到"、"until"、"遍历直到完成"）给出警告。

## F10（Small Focused Agents）硬约束：单 worker ≤ 10 原子步骤

- **禁止**：一个 worker 承担"探索 + 设计 + 实现 + 测试 + 评审"全流程
- **正确**：按角色拆分，每个 worker 3-10 步完成一件事
  - `scout`：读代码、写报告（3-5 步）
  - `builder`：按规格 TDD 实现（5-10 步）
  - `reviewer`：跑 multi-review、输出报告（2-4 步）

**理由**：Agent 任务越大，失败率指数上升；拆小后每步可独立验证、失败易定位、并行度提高。

**违反检测**：`/agent-design-check` F10 维度会估算 worker prompt 的步骤粒度，> 10 步必须拆分。

## F5（Unified State）约束：状态同步点必须显式

- **禁止**：worker 完成后业务状态（`current-task.md`、`task-log.md`）不同步；diary 与 current-task 各记各的
- **正确**：派出 worker 前规划好"谁在什么时刻把哪个信号写回主状态"
  - `/squad`：worker 写 `done` 事件 → 主 `/lfg` 会话读 mailbox → 勾选 current-task checkbox
  - `/dispatch-agents`：主 agent 在收到所有子 agent 聚合结果后统一写回 current-task
  - `/subagent-dev`：执行者 agent 写 diary + status，规划者 agent 在决定下一步前读 aggregate

**理由**：执行状态（"worker 说完成了"）≠ 业务状态（"current-task 勾选了、task-log 归档了"）。两者分裂会导致"Agent 认为做完但业务没更新"，下次恢复状态不一致。

## F11（Artifact Ownership）硬约束：下游不得直接改上游产物

> 来源：腾讯 JK Launcher 团队《Harness Engineering 工程化落地》——下游 agent 觉得上游写得不严谨时，会"顺手改掉"。结果是：谁对哪份产物负责、追责路径、回退边界全部失效。

- **禁止**：worker 直接编辑其他 worker 产出的文件（规格、计划、设计文档、上一阶段 diary 等）
- **正确**：每个 worker **只写自己的产物目录**；发现上游产物有问题时，只能做两件事
  1. 在自己的产物里**提出 blocker**（含具体问题 + 期望的修正方向）
  2. 由 orchestrator / 主会话读到 blocker 后**打回**给上游 worker 重新生成
- **产物目录约定**（以常见场景为例）
  - `/squad`：worker 只写 `squad/<task>/workers/<name>/` 下的文件 + 自己 mailbox 事件
  - `/dispatch-agents`：子 agent 只写 prompt 里 **明示**的输出路径
  - `/subagent-dev`：执行者写 `agents/<id>/diary.md` 和 `status.md`，**不**改规划者产出的 spec / plan

**理由**：如果允许下游私改上游，整条流程就失去"某份产物由谁署名"的契约。出问题后没人能回放"上游当时给的是什么、下游在此之上做了什么"。产物所有权是 F5（Unified State）的前置保障——状态同步的前提是每份状态有明确的唯一作者。

> **代码层面同源**:F11 跟 `simplicity.md` 准则 2「Surgical Changes — 改最少必要」是同一思想的两个层面——agent 层面"下游 agent 不擅改上游 agent 产出",代码层面"AI 不顺手改邻居代码 / 替换现有 style"。两者目标都是**保护署名契约**。Issue #51 吸收 Karpathy 4 原则。

**违反检测**：

- `/agent-design-check` F11 维度（新增）扫 worker prompt：是否出现「必要时直接补充上游文档」「遇到 spec 缺失自行补全后继续」等越权用语
- 执行期的 `audit.jsonl`（见 task-lifecycle）：同一产物文件在单任务里被两个不同 agent 写入 = 违反信号
- 遇到越权时不是默默回滚，而是**打回到违反的 agent**，并在 lessons 里登记一条（进入"脚本化候选"链路，见 knowledge-conflict-resolution.md）

## 搭配规则

- `.claude/rules/task-lifecycle.md` — 分层记忆 + Context Ownership（Factor 3）
- `.claude/rules/autonomy.md` — 操作风险分级
- `/agent-design-check` 技能 — 4 维度体检
- `/plan-check` 第 9 维度 — 计划阶段自动触发 Agent 工程化校验
