# Current Task

## 状态：进行中

## LFG 进度

### Goal
Issue #22 — 在 squad coordinator 中加 Tier 0 Watchdog：定时 ping tmux session + worker 窗口，发现失联写 mailbox 事件 + 提示用户。

### Context
复杂度：中 | 通道：标准 | 基线 commit：686fb6a | 工作分支：feat/squad-watchdog-issue-22 | 基线测试：382 个，OK

### Assumptions
- 假设：watchdog 复用 cmd_watch 进程，**不**起独立循环 | 依据：单进程更简单；watch 已是常驻
- 假设：检查频率 = watch interval（每个 tick 后跑一次） | 依据：减少状态机复杂度
- 假设：本期实现场景 A（session 丢失）+ 场景 B（worker 窗口丢失），场景 C（pid 检查）留 TODO | 依据：worker 当前不写 pid，跨文件改动太多
- 假设：不实现自动重启（haiku→sonnet）只上报 | 依据：Issue 标注"可选"
- 假设：失联事件幂等去重——已写过 worker_crashed 不重写 | 依据：每 3s 跑一次，否则刷屏

### Acceptance
1. 新建 `src/agent_harness/squad/watchdog.py`（纯函数 + sentinel 检查）
2. `cmd_watch` 每个 tick 末尾调用 watchdog
3. tmux session 不存在 → mailbox 写 `session_lost` 事件 + stdout 提示
4. 已 spawned + 未 done + 窗口消失 → mailbox 写 `worker_crashed` 事件（幂等）
5. `touch .agent-harness/.watchdog-skip` 可完全关闭 watchdog
6. 测试覆盖：场景 A、场景 B、sentinel 关闭、幂等去重 ≥ 4 个 case
7. 同步更新 `docs/architecture.md`、`docs/product.md`

### Decisions
- watchdog 是纯函数，所有"已上报"判定从 mailbox 事件流推导（沿用 lessons "三源对账推导状态"）
- 沿用 context-monitor sentinel 模式（`.agent-harness/.watchdog-skip`）
- KNOWN_TYPES 加 `session_lost` / `worker_crashed`

### Files
- 新增：`src/agent_harness/squad/watchdog.py`
- 修改：`src/agent_harness/squad/coordinator.py`（cmd_watch 集成）
- 修改：`src/agent_harness/squad/mailbox.py`（KNOWN_TYPES 扩展）
- 新增：`tests/test_squad_watchdog.py`
- 修改：`docs/product.md`、`docs/architecture.md`

### Quality Baseline
- 测试：382 个，100% 通过

### Progress
- [x] 理解与评估
- [x] 环境准备 — 分支 feat/squad-watchdog-issue-22, 基线 OK
- [x] 计划
- [ ] 实施 — TDD: watchdog.py 纯函数 → coordinator 集成
- [ ] 自检
- [ ] 评审
- [ ] 验证
- [ ] 质量对比
- [ ] 沉淀
- [ ] 完成报告
- [ ] 待验证
- [ ] 归档与收尾
