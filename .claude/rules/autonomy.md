---
description: 操作权限分级和自治边界
---

# 自治规则

操作按风险分为三级，级别越高越需要用户确认：

## 自由操作（无需确认）

- 读取任何项目文件
- 运行 `make test`、`make check`
- 在 `.agent-harness/` 下更新 current-task.md、task-log.md、lessons.md
- 更新 `docs/` 下的 checkbox 打勾状态
- 填充文档中的"待补充"占位符

## 需要谨慎的操作（正常执行，但出错时必须归因）

- 创建新文件
- 修改现有业务代码
- 修改 `AGENTS.md` 或 `docs/` 中的规则和描述
- 安装新依赖
- 修改配置文件

## 需要用户确认的操作（禁止自行执行）

- 删除文件或目录
- 修改 `.env`、credentials 或密钥相关文件
- 执行 git push、git reset --hard、git rebase
- 修改 CI/CD 配置
- 修改数据库 migration 中的 DROP 操作
- 任何影响生产环境的操作
- 修改项目的权限、认证或安全相关逻辑

遇到不确定归属哪一级的操作时，默认按高一级处理。

## Trust Calibration（任务复杂度自适应，Issue #30）

吸收自 [Danau5tin/multi-agent-coding-system](https://github.com/Danau5tin/multi-agent-coding-system)。上面的三级分类是**操作本身的风险基线**，而**任务复杂度**会改变每一级操作需要的确认频次和验证强度。

与 `/lfg` 阶段 0.3 的 5 档复杂度评估对齐：

| 任务复杂度 | 自由操作阈值 | 谨慎操作阈值 | 确认操作阈值 | Explorer 验证 |
|---|---|---|---|---|
| **微小**（改 1-2 文件，无行为变化） | 完全自主 | 完全自主 | 仍需确认 | 不需要 |
| **小**（1-2 文件，明确行为变化） | 完全自主 | 完全自主 | 仍需确认 | 视情况 |
| **中**（3+ 文件，需要设计） | 完全自主 | 完全自主但每步汇报 | 仍需确认 | **必须**（先读后改） |
| **大**（跨模块 / 架构决策） | 完全自主 | 首次改动前汇报方向 | 仍需确认 | **强制**（scout 先探路） |
| **超大-可并行** | 按 /squad capability 强制 | 按 capability 强制 | orchestrator 禁止写代码 | **强制** |

**核心规则**：

1. **简单任务不要被流程绊住脚**：微小/小任务跳过 /spec、/plan-check、多轮评审
2. **复杂任务必须先探路**：中/大任务在改业务代码之前，必须先让 Explorer（`/squad` 的 scout 或 `/dispatch-agents` 派的只读子代理）读相关模块并输出报告
3. **Orchestrator 强约束**：采用 `/squad` 或 `/subagent-dev` 三角色模式时，orchestrator 能力从文档约束升级为运行时强制（`settings.local.json` 的 `permissions.deny` 屏蔽 Write/Edit/MultiEdit）
4. **信任升级条件**：连续 3 次小任务成功后，同类任务的"谨慎操作"阈值可下调到"自由"（只在同一会话有效，不跨会话）

这不是替代上面的三级基线，而是在其上加一层**任务级调节**：操作基线不变，但任务越简单越自主，任务越复杂越要求证据链（Explorer 验证）。
