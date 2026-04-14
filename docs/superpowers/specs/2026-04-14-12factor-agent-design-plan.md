# 12-Factor Agent Design 集成 — Plan

对应 spec：`2026-04-14-12factor-agent-design-spec.md`

## Step 1 — 新建 `agent-design-check` 技能模板

**文件**：`src/agent_harness/templates/superpowers/.claude/commands/agent-design-check.md.tmpl`
**内容**：
- 头部：适用场景（涉及 squad/dispatch-agents/subagent-dev/worker prompt 设计）+ 不适用场景（普通 CRUD，主动跳过）
- 4 维度 checklist（F3/F5/F8/F10），每条含 ✅/⚠️/❌ 标准 + 修复建议
- 附录：其他 8 条 Factor 列表（Reference Only）
- 输出格式：维度评分表 + 修订建议

**验证**：`ls src/agent_harness/templates/superpowers/.claude/commands/agent-design-check.md.tmpl`
**提交**：`feat(skills): add /agent-design-check with 4 factors from 12-factor-agents [plan step 1]`

## Step 2 — 新建 `agent-design` 规则模板

**文件**：`src/agent_harness/templates/common/.claude/rules/agent-design.md.tmpl`
**内容**：
- Factor 8 硬约束：worker 内 retry/loop 由外部 advance/watchdog 控制
- Factor 10 硬约束：单 worker 任务 ≤ 10 原子步骤，超过就拆
- Factor 5 约束：子 Agent 的过程状态（diary）与任务主状态（current-task）保持同步
- 适用范围注明：Agent 协作场景（非 Agent 任务忽略）

**验证**：`ls src/agent_harness/templates/common/.claude/rules/agent-design.md.tmpl`
**提交**：`feat(rules): add agent-design.md with Factor 8/10 hard constraints [plan step 2]`

## Step 3 — task-lifecycle 追加 Context Ownership 段

**文件**：`src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`
**位置**：在"并行子 agent 的日志隔离"章节之后
**内容**：新增"## Context Ownership（Agent 上下文所有权）"段
- 每个子 Agent 的 prompt + 初始上下文必须显式写明
- 禁止依赖默认拼接（如"你知道项目情况，自行决定"）
- 引用 12-factor-agents Factor 3

**验证**：`grep "Context Ownership" src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`
**提交**：`feat(rules): append Context Ownership section to task-lifecycle [plan step 3]`

## Step 4 — plan-check 加第 9 维度

**文件**：`src/agent_harness/templates/superpowers/.claude/commands/plan-check.md.tmpl`
**改动**：
- 在第 8 维度"Nyquist 合规"之后增加 **9. Agent 工程化（条件触发）**
- 通过标准：涉及 squad/dispatch-agents/subagent-dev/多 worker → 必须跑 `/agent-design-check`；不涉及 → 标记"不适用"
- 修订循环保持 3 轮，第 9 维度 FAIL 时引用 `/agent-design-check`

**验证**：`grep -c "Agent 工程化" src/agent_harness/templates/superpowers/.claude/commands/plan-check.md.tmpl` 应 ≥ 1
**提交**：`feat(skills): add 9th dimension "Agent engineering" to plan-check [plan step 4]`

## Step 5 — skills-registry 注册 + lfg 覆盖清单校验

**文件**：`src/agent_harness/templates/superpowers/skills-registry.json`
**改动**：新增 skill entry
```json
{
  "id": "agent-design-check",
  "name": "Agent 设计体检",
  "category": "process",
  "one_line": "4 维度（F3/F5/F8/F10）体检涉及多 agent 的计划",
  "triggers": ["设计 squad worker", "dispatch-agents 前校验", "agent 编排"],
  "decision_tree_label": "计划涉及多 agent？",
  "lfg_stage": ["3 计划"],
  "expected_in_lfg": true
}
```

**同步校验**：运行 `.venv/bin/python -c "from agent_harness.skills_registry import load_registry, render_lfg_coverage_table; from pathlib import Path; r = load_registry(Path('src/agent_harness/templates/superpowers')); print(render_lfg_coverage_table(r))"` 确保"3 计划"阶段出现 `/agent-design-check`
**验证**：`make test -- tests/test_skills_registry.py`
**提交**：`feat(registry): register agent-design-check skill [plan step 5]`

## Step 6 — 测试 + dogfood 同步

**改动**：
- `tests/test_skills_registry.py` 若有硬编码 skill 数量需更新
- 运行 `make dogfood` 同步模板到 `.claude/` + `.agent-harness/`
- 检查 `.claude/commands/agent-design-check.md`、`.claude/rules/agent-design.md` 是否生成

**验证**：`make test && make check && make dogfood`
**提交**：`test(skills): include agent-design-check in registry tests + dogfood sync [plan step 6]`

## Step 7 — docs 同步

**文件**：
- `docs/product.md`：技能清单新增 `/agent-design-check`
- `docs/architecture.md`：如有技能数量字段需更新（31 → 32）

**验证**：`grep "agent-design-check" docs/product.md docs/architecture.md 2>/dev/null | wc -l` ≥ 1
**提交**：`docs: document agent-design-check skill [plan step 7]`

## 依赖与顺序

Step 1 → 2 → 3 → 4 → 5 → 6 → 7（严格顺序，因为 step 5 依赖 step 1 的 tmpl 存在、step 6 的 test 依赖 step 5 的 registry）。

## 风险

- `tests/test_skills_registry.py` 可能硬编码技能数量 31 → 改 32 时要同步所有地方
- `make dogfood` 可能因占位符未替换漂移 → step 6 必须 `--check` 模式验证
