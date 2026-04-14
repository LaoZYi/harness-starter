# Current Task

## 任务目标

吸收 humanlayer/12-factor-agents 方法论，裁剪为本项目真正适用的 4 条 Factor（3/5/8/10），落地为 1 个新技能 + 1 个新规则 + 2 处增量修改。Issue #28 / GitLab #12。

## 状态：进行中（LFG 标准通道）

## LFG 进度

### Context
复杂度：大 | 通道：完整（evolution 自动）| 基线 commit：bf7bcd0 | 工作分支：feat/agent-design-12factor-issue-28 | Issue：#28 / gl#12

### Assumptions
- 假设：只吸收 Factor 3/5/8/10（Context Window / Unified State / Control Flow / Small Focused Agents） | 依据：本项目是模板库非 LLM 运行时，其他 8 条 Factor 不适用
- 假设：新技能名 `/agent-design-check`（非 `/12-factor-check`）| 依据：聚焦能落地的 4 条，避免"为吸收而吸收"
- 假设：规则放 `templates/common/.claude/rules/agent-design.md`（所有项目类型） | 依据：squad/dispatch-agents 在所有项目类型通用
- 假设：`plan-check` 从 8 维度扩到 9 维度（Agent 维度条件触发），不新造技能 | 依据：避免技能数量膨胀

### Acceptance
1. 新技能 `agent-design-check.md.tmpl` 存在并含 4 Factor checklist
2. 新规则 `agent-design.md.tmpl` 在 common/rules（Factor 8/10 硬约束）
3. `task-lifecycle.md.tmpl` 追加 Context Ownership 段（Factor 3）
4. `plan-check.md.tmpl` 含第 9 维度（Agent 工程化，条件触发）
5. skills-registry.json 注册新技能；lfg.md.tmpl 覆盖清单自动渲染
6. `make test` 通过（含新测试）+ `make check` 通过
7. `make dogfood` 无漂移
8. Issue #28 + GitLab #12 关闭

### Files
- 新增：`templates/superpowers/.claude/commands/agent-design-check.md.tmpl`
- 新增：`templates/common/.claude/rules/agent-design.md.tmpl`
- 新增：`docs/superpowers/specs/2026-04-14-12factor-agent-design-spec.md`
- 新增：`docs/superpowers/specs/2026-04-14-12factor-agent-design-plan.md`
- 修改：`templates/common/.claude/rules/task-lifecycle.md.tmpl`（Context Ownership 段）
- 修改：`templates/superpowers/.claude/commands/plan-check.md.tmpl`（第 9 维度）
- 修改：`templates/superpowers/.claude/commands/lfg.md.tmpl`（阶段 3 引用）
- 修改：`templates/superpowers/skills-registry.json`（注册新技能）
- 修改：`docs/product.md`、`docs/architecture.md`（技能清单）
- 修改：`tests/test_skills_registry.py`（断言新技能）

### Quality Baseline
- 测试：451 全通过
- Lint：check 通过

### Testing Scenarios
- **正常**：渲染模板包含新技能 + 规则；registry 注册正确
- **边界**：agent-design-check 在非 agent 场景提示"不适用跳过"；plan-check 第 9 维度条件触发
- **错误路径**：skills-registry 遗漏 → lint 报 orphan；模板占位符未替换 → dogfood 漂移

### Progress
- [x] 理解与评估 — 复杂度大，完整通道
- [x] 环境准备 — 分支 feat/agent-design-12factor-issue-28，基线 451 tests OK
- [x] 规格定义 — 2026-04-14-12factor-agent-design-spec.md
- [x] 计划 — 2026-04-14-12factor-agent-design-plan.md
- [ ] 实施 step 1 — 新建 agent-design-check 技能模板
- [ ] 实施 step 2 — 新建 agent-design 规则模板
- [ ] 实施 step 3 — task-lifecycle 追加 Context Ownership 段
- [ ] 实施 step 4 — plan-check 加第 9 维度
- [ ] 实施 step 5 — skills-registry 注册 + lfg 覆盖清单校验
- [ ] 实施 step 6 — 测试 + dogfood 同步
- [ ] 实施 step 7 — docs/product.md + docs/architecture.md 同步
- [ ] 自检
- [ ] 评审 multi-review
- [ ] 验证 verify
- [ ] 质量对比
- [ ] 沉淀 compound
- [ ] 完成报告
- [ ] 待验证 — 用户确认
- [ ] 归档与关闭 Issue #28 / gl#12
