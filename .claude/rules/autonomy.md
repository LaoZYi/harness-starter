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

| 任务复杂度 | 自由操作阈值 | 谨慎操作阈值 | 确认操作阈值 | Explorer 验证 | 建议模型 |
|---|---|---|---|---|---|
| **微小**（改 1-2 文件，无行为变化） | 完全自主 | 完全自主 | 仍需确认 | 不需要 | **Haiku** |
| **小**（1-2 文件，明确行为变化） | 完全自主 | 完全自主 | 仍需确认 | 视情况 | **Haiku / Sonnet** |
| **中**（3+ 文件，需要设计） | 完全自主 | 完全自主但每步汇报 | 仍需确认 | **必须**（先读后改） | **Sonnet** |
| **大**（跨模块 / 架构决策） | 完全自主 | 首次改动前汇报方向 | 仍需确认 | **强制**（scout 先探路） | **Opus**（深度推理） |
| **超大-可并行** | 按 /squad capability 强制 | 按 capability 强制 | orchestrator 禁止写代码 | **强制** | orchestrator = **Opus**；worker 按 capability 分级 |

**核心规则**：

1. **简单任务不要被流程绊住脚**：微小/小任务跳过 /spec、/plan-check、多轮评审
2. **复杂任务必须先探路**：中/大任务在改业务代码之前，必须先让 Explorer（`/squad` 的 scout 或 `/dispatch-agents` 派的只读子代理）读相关模块并输出报告
3. **Orchestrator 强约束**：采用 `/squad` 或 `/subagent-dev` 三角色模式时，orchestrator 能力从文档约束升级为运行时强制（`settings.local.json` 的 `permissions.deny` 屏蔽 Write/Edit/MultiEdit）
   - **3a. 禁越界专业判断**（来自腾讯 JK Launcher 的踩坑经验）：orchestrator **只做路由 / 状态流转 / 打回判断**，不向 worker 输出需求修订、方案建议、代码改法、测试思路等专业结论。理由：orchestrator 站在流程中心，天然知道各阶段产物，很容易"顺手出意见"——但这类意见往往不专业，还会把整个流程带偏，让系统滑回「中央大脑说了算」
   - **orchestrator 拿不准时的正确动作**：① 拉专业 worker（scout/builder/reviewer）来做判断；② 还拿不准就**暂停流程等用户裁决**，不自行决定推进
   - **违反信号**：orchestrator 产出里出现「我觉得这个需求应该……」「这个方案可以改成……」「这段代码其实……」等专业判断用语 → 立即拦下，改为指派对应 worker
   - **3b. orchestrator 疲劳硬门禁**（快手 sec-audit-pipeline 吸收，分类 `defensive-temporary`）：连续派出 **N 个** worker 后（默认 **N=8**）必须 spawn **fresh orchestrator** 接管，旧 orchestrator 在 mailbox 写 `handoff` 事件后退场——不允许「我还撑得住」继续拖下去
     - **事故根因**：长上下文 orchestrator 会无法判断 SKILL.md 中哪些内容可省略——它省略的恰好是它不知道重要的防护层。Yandex Reasoning Shift 论文证明推理能力越强偷懒幅度越深（最强版自检率缩 40%）
     - **与 Context Budget 规则 4 的区别**：规则 4 软限 ~50 轮是对**所有** agent 的通用上限；3b 是 **orchestrator 专属**阈值更低，因为编排角色在长上下文里更易漏判
     - **handoff 流程**：旧 orchestrator 写 mailbox 事件 `type=handoff, reason=fatigue_gate, worker_count=<N>` → 新 orchestrator spawn 时读 mailbox 接管状态 → 旧 orchestrator 退场
     - **阈值可配**：项目可在 `.agent-harness/squad/<task>/spec.json` 或 `.claude/settings.json` 里覆盖默认 N=8
     - **反偷懒联动**：配合 `anti-laziness.md` 门禁 3 新增借口「上下文太长，不想 spawn 新 SubAgent」——3b 是硬门禁，借口清单是文字驳斥，双保险
     - **回归验证**：本门禁由 `/pressure-test` 的默认场景 5「orchestrator 不 spawn fresh」做月度回归——即使 3b 因配置覆盖 / AI 误解 / 文档被精简而失效，压测能把问题抓回来
4. **信任升级条件**：连续 3 次小任务成功后，同类任务的"谨慎操作"阈值可下调到"自由"（只在同一会话有效，不跨会话）

这不是替代上面的三级基线，而是在其上加一层**任务级调节**：操作基线不变，但任务越简单越自主，任务越复杂越要求证据链（Explorer 验证）。

### 模型分级的核心洞察

> 来源：阿里云 Qoder CLI 团队《Harness Engineering 实战》——「便宜模型反而浪费：复杂任务用低成本模型，它会在错误方向上反复尝试，消耗大量 tokens 和时间，最终还是给不出正确答案」。

- **不是「越便宜越省」**：复杂推理（根因定位、架构决策、跨模块重构）硬塞 Haiku → 多轮试错 × 失败率高 → 总 token 反而高于一次 Opus
- **不是「越强越好」**：简单任务（改 typo、renames、批量文本替换）用 Opus → 过度深思熟虑 → 响应慢 + 成本高
- **按需匹配最优**：
  - Haiku 擅长：**高吞吐量确定性任务**（文本分类、格式转换、简单 diff、信息提取）
  - Sonnet 擅长：**常规开发**（单模块实现、测试编写、文档同步、中等规模重构）
  - Opus 擅长：**深度推理**（根因定位、跨模块架构决策、多约束规划、安全评审）

### 如何切换模型

- **Claude Code**：`/model` 命令切换当前会话模型；或在 `.claude/settings.json` 的 `model` 字段配置默认模型
- **编排式场景**（`/squad` / `/dispatch-agents`）：为不同 worker 指定不同模型，orchestrator 走 Opus，scout 走 Haiku，builder 走 Sonnet
- **未显式切换时**：沿用父会话当前模型，由 Trust Calibration 表作为**建议**参照

> **注意**：具体模型 ID（如 `claude-opus-4-7`）会随 Anthropic 发布迭代。本表只给类别（Haiku / Sonnet / Opus），避免随版本过时。
