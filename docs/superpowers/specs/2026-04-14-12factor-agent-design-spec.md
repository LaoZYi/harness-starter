# 12-Factor Agent Design 集成 — Spec

**Issue**：#28（GitHub）/ #12（GitLab）
**来源**：`/evolve` 提案吸收 humanlayer/12-factor-agents（19255⭐）
**日期**：2026-04-14

## 目标

把 12-factor-agents 的**可适用部分**（4 条 Factor）沉淀为本框架的 Agent 设计体检清单和硬规则，填补"Agent 工程化"维度空白。

## 范围裁剪

### 吸收的 4 条 Factor

| Factor | 本项目如何落地 | 理由 |
|---|---|---|
| F3 Own Context Window | task-lifecycle 追加 Context Ownership 段 | 已有 L0-L3 分层，追加"每个子 Agent prompt 必须显式设计"原则 |
| F5 Unified State | agent-design 规则约束 | current-task.md 是 unified state，但 squad worker mailbox + agent diary 分裂 |
| F8 Own Control Flow | agent-design 硬约束 | worker 内 retry/loop 必须由外部 advance/watchdog 控制，不由 LLM 自行循环 |
| F10 Small Focused Agents | agent-design 硬约束 | 单 worker 任务 ≤ 10 原子步骤 |

### 不吸收的 8 条

F1 NL→Tool、F2 Own Prompts、F4 Tools as Structured Output、F6 Launch/Pause/Resume、F7 Human Contact、F9 Compact Errors、F11 Trigger from Anywhere、F12 Stateless Reducer — 这些都预设"自建 LLM 应用"，本项目（Claude Code 模板库）不控制这些层。在新技能中作为"Reference Only"列出，不做硬约束。

## 需求

- **R1**：提供 `/agent-design-check` 技能，对涉及 squad/dispatch-agents/subagent-dev 的计划做 4 维度体检
- **R2**：体检在非 Agent 场景明确跳过（不制造噪音）
- **R3**：Factor 8/10 写入硬规则，`/write-plan` 和 `/squad` 阶段自动提示
- **R4**：Factor 3 追加到 task-lifecycle 作为"Context Ownership"段
- **R5**：`/plan-check` 第 9 维度"Agent 工程化"（条件触发）
- **R6**：skills-registry.json 注册新技能，lfg 覆盖清单自动渲染
- **R7**：测试保证 registry 完整性 + 模板占位符完整
- **R8**：docs/product.md 技能列表同步更新

## 验收

- 新技能在 `/lfg` 阶段 3 被条件触发（检测 squad/dispatch 关键词）
- `harness init <target>` 渲染出的项目包含 `agent-design-check` + `agent-design.md` 规则
- `make test` 451 → ≥ 451 全通过；`make check` 无警告；`make dogfood` 无漂移

## 不做

- 不新建 `/12-factor-check`（避免技能膨胀）
- 不改现有 L0-L3 分层架构（只增量追加）
- 不吸收 Factor 1/2/4/6/7/9/11/12 的硬约束（只在技能内列出以供参考）
