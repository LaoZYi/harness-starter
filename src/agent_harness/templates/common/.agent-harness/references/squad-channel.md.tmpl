## squad 通道（超大-可并行任务）

**进入条件**：阶段 0.3 判定为"超大-可并行"档，用户确认拓扑。

**核心思想**：`/lfg` 主会话扮演**协调员**——起 squad、实时翻译 mailbox 状态、关键节点拉用户介入。worker 在 tmux 后台并行干活。用户可随时 `tmux attach` 介入调试。

### 前置：`/lfg` 自动生成 spec.json 草稿

根据任务描述推断 worker 拓扑。默认模式（经典三段）：

```json
{
  "task_id": "<kebab-case 任务名，<= 31 字符>",
  "base_branch": "<当前 master/main>",
  "workers": [
    {
      "name": "scout",
      "capability": "scout",
      "prompt": "探索 <相关模块路径>，输出现状报告到 report.md（3 段：现有实现/痛点/建议切入点）"
    },
    {
      "name": "builder",
      "capability": "builder",
      "depends_on": ["scout"],
      "prompt": "读 scout 的 report.md + <任务规格>，按 TDD 实现：先写失败测试 → 实现 → 全过"
    },
    {
      "name": "reviewer",
      "capability": "reviewer",
      "depends_on": ["builder"],
      "prompt": "对 builder 的 worktree diff 跑 /multi-review，输出 review.md。所有 P0/P1 问题汇报到 .agent-harness/squad/<task_id>/workers/reviewer/review.md"
    }
  ]
}
```

**其他拓扑模板**（根据任务特征选）：
- **多端点并行实现**：N 个 builder 各做一个端点，1 个 reviewer 统一审查（N+1 worker）
- **重构 + 迁移**：scout 做调研 → 2 个 builder 分头改前端/后端（无强依赖）→ reviewer 审
- **独立模块各自迁移**：N 个 builder，互不依赖
- **四角色重型任务（Issue #30 吸收自 Danau5tin/multi-agent-coding-system）**：orchestrator + scout + builder + reviewer。`orchestrator` capability 在运行时 **完全 deny Edit/Write/MultiEdit/NotebookEdit**——只能用 Read/Grep/Glob/Task/TodoWrite 派工，连代码都不碰，专职战略协调。适用于：跨 3+ 模块且需要持续调度决策的任务（实施过程中 scout 发现新子方向需要动态派新 builder）。`capability.py` 运行时强制，不是软约束

```json
{
  "task_id": "large-refactor",
  "base_branch": "master",
  "workers": [
    { "name": "orchestrator", "capability": "orchestrator", "prompt": "读 spec 和 scout 产出，决定后续派发；发现新子任务时用 Task 派给 builder；自己不写代码" },
    { "name": "scout-a", "capability": "scout", "prompt": "探索模块 A" },
    { "name": "scout-b", "capability": "scout", "prompt": "探索模块 B" },
    { "name": "builder-1", "capability": "builder", "depends_on": ["scout-a"], "prompt": "按 orchestrator 指令实现模块 A" },
    { "name": "reviewer", "capability": "reviewer", "depends_on": ["builder-1"], "prompt": "多视角评审" }
  ]
}
```

### 介入点 1：拓扑确认（🔴 必须）

```
拟用 squad 通道执行，建议拓扑：
- scout（scout capability）：探索 src/auth/ → report.md
- builder（builder capability，depends on scout）：按 spec 实现
- reviewer（reviewer capability，depends on builder）：做 multi-review

预计：3 个 tmux 窗口 + 3 个 worktree，消耗 ~3x token

确认？回复：
- "可以" → 直接起 squad
- "改成 <新拓扑>" → 修改 spec 重问
- "不要并行，走单 agent" → 降级到完整通道
```

### 起 squad + watch

```bash
.agent-harness/bin/squad create spec.json
.agent-harness/bin/squad watch &   # 后台常驻，自动 advance + watchdog
```

`/lfg` 主会话保持运行，轮询 mailbox + 把重要事件翻译给用户。

### 介入点 2：scout 完成，builder 可否继续（🔴 必须 + 强制 compact）

> **PreCompact hook 自动化（Issue #13）**：本节以及介入点 5、阶段 5/9/10 调用 `/compact` 时，`.claude/hooks/pre-compact.sh` 会**自动**写一条 audit 检查点 + stderr 提示 AI 把关键决策持久化。你不需要手动追加审计——hook 已经做了。/lfg 的配合动作：调 `/compact` 前把待存的决策写进 current-task 或 lessons，让 hook 的"持久化提醒"有内容可捞。

scout 写 `done` 事件后：
1. **优先读结构化知识制品（Issue #30）**：运行 `harness agent aggregate scout` 看顶部 `## artifact` 段。`diary_append_artifact` 写入的制品包含 `type/summary/refs/content` 字段，比散落在 diary 里的自由日志更精炼。无 artifact 时再退回读 `report.md` 全文
2. 告知用户："scout 完成。制品要点：<3 条摘要，优先展示 artifacts>。builder 可以照这个实现吗？"
3. 用户确认后 `/compact`（控制 context 爆掉）继续
4. watchdog + advance 会自动启动 builder

### 介入点 3：worker 失联（watchdog 触发）

`squad watch` 报 `session_lost` 或 `worker_crashed` 时：
```
⚠️ worker <name> 失联（<具体原因>）。选择：
- "重启" → kill window → 重新 spawn
- "跳过" → 标记 done，继续下游
- "终止" → stop all + 回归单 agent 完整通道
```

### 介入点 4：worker 自己卡死

通过 `squad dump | grep stuck`（或 tick 里的异常模式）检测：
```
worker <name> 在 <具体问题> 上连续 3 次 RED / 进度停滞 >10min。
- "我 attach 看看" → 输出 `tmux attach -t squad-<task_id> \; select-window -t <name>`
- "调整方向" → 给新 prompt 让 watchdog 重启
- "跳过此 worker，手工接管" → 主会话接收该部分继续
```

### 介入点 5：reviewer PASS → 确认合并（🔴 必须 + 强制 compact）

```
✅ reviewer 结论 PASS（0 P0 / <N> P1）。
各 worker 成果：
- scout：report.md
- builder：<改动摘要 + 关键 commit SHA>
- reviewer：review.md

所有 worker done。准备合并各 worktree 到 <base_branch>？
回复 "合并" / "回退" / "让我先手动检查"
```

用户回 "合并" 后 `/compact`，进入介入点 6。

### 介入点 6：finish-branch 合并 + push（🔴 必须）

对每个 worker 的 worktree 跑 `/finish-branch`。行为与现有阶段 10 相同：选四种去向（直接合并 / 建 PR / 保留 / 丢弃）。

### 失败兜底

| 场景 | 回退策略 |
|---|---|
| spec 生成错（拓扑不合理） | 回介入点 1 重问 |
| watchdog 报全部 worker 失联 | stop all → 降级到完整通道 |
| reviewer FAIL 且连续 3 轮修不完 | stop all → 告知用户"建议人工介入"，保留 worktree |
| 用户中途 Ctrl+C | `.agent-harness/bin/squad stop all` 保留 worktree，告知用户如何人工接管 |

### 为什么 `/lfg` 主会话常驻而非一次性派发

用户心智：**单一入口**。`/lfg` 主会话从头到尾负责协调，用户只在 6 个介入点出现时回答问题，不用记住"去哪看进度"。代价是 token 消耗——用**介入点 2/5 强制 `/compact`** 抵消。

### worker 内不递归 lfg（硬规则回顾）

AGENTS.md 硬规则：worker 内**不得**再调用 `/squad create` 或 `/dispatch-agents`，也**不**跑完整 `/lfg` 流水线。worker 的 prompt 应直接指向其具体工作（scout 探索、builder TDD 实现、reviewer 审查），不要让 worker 自己再起子流程，资源会爆炸且 observability 崩坏。

---
