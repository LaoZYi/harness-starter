# Current Task

## 任务目标

补吸 Karpathy 原则 1「Think Before Coding」的 3 条缺口，扩展现有规则集对 **Pre-coding 阶段**的覆盖。来源：Issue #53 / `/evolve` 步骤 1.5（#51 已 CLOSED 增量）。

## 范围（已 push back 缩窄）

| 项 | 状态 |
|---|---|
| 新特性 1：Think Before Coding 缺口 3 条 → R-001~R-005 | **本次实施** |
| 新特性 2：EXAMPLES.md 范例（选项 B 新建 references/simplicity-examples.md） | **out-of-scope**（推迟，独立 issue） |
| 新特性 3：skills/ 拆分结构 | 跳过（已对齐） |

理由：选项 B 违反 simplicity.md 准则 2 Surgical Changes（不是用户主动要求的扩展），按本任务自身要新增的 Push Back 规则现场演示——push back 后用户授权按推荐方案做。

## 假设清单

- 假设：rules SSOT 是 `src/agent_harness/templates/common/.claude/rules/*.tmpl`，主仓库 `.claude/rules/` 由 `make dogfood` 同步 | 依据：`scripts/dogfood.py` 第 24 行 `SYNC_PREFIXES`
- 假设：本次纯 Markdown 文档变更，不需要新增测试 | 依据：testing.md 测试三类场景针对代码行为
- 假设：门禁 5 内插入 Push Back 子节最自然 | 依据：门禁 5 主旨「AI 主动 surface 判断而非隐藏」与 Push Back 同源
- 假设：master 直接工作，每步打 `lfg/step-N` tag | 依据：项目惯例（recent commits 都有 `[plan step N]` 在 master）

## 验收标准（R-IDs）

- [ ] **R-001** `task-lifecycle.md.tmpl` 第 1 步「假设清单」扩为「假设 + 依据 + 若需求模糊**列多解读**」+ 触发条件锚定
  - 硬检查：grep `多解读` ≥ 1 次 + grep `触发条件` 在该段 ≥ 1 次
- [ ] **R-002** `task-lifecycle.md.tmpl` 第 2 步「展示并等待用户确认」加「Name what's confusing」+「主动提出更简单方案」
  - 硬检查：grep `哪里不清楚\|Name what` ≥ 1 次 + grep `更简单\|simpler` ≥ 1 次
- [ ] **R-003** `anti-laziness.md.tmpl` 门禁 5 加 Push Back 子节 + 边界 + 反合理化新借口
  - 硬检查：grep `Push back\|push back` ≥ 1 次 + grep `不该 push back\|边界` ≥ 1 次 + 反合理化表新增 ≥ 1 行
- [ ] **R-004** `make dogfood` 同步成功，`.claude/rules/` 中 task-lifecycle/anti-laziness 同步更新
  - 硬检查：dogfood 输出含 `~ .claude/rules/task-lifecycle.md` 和 `~ .claude/rules/anti-laziness.md`
- [ ] **R-005** `make ci` 全绿（658 tests + ruff + mypy + skills-lint + deadcode + shellcheck）
  - 硬检查：`Ran 658+ tests` + `OK` + 无 ruff/mypy 报错
- [—] **R-006** EXAMPLES.md 范本/选项 B/C — out-of-scope（独立 issue 候选）

## 计划步骤

- [ ] step 1: 编辑 `task-lifecycle.md.tmpl` 第 1 步加多解读 (R-001)
- [ ] step 2: 编辑 `task-lifecycle.md.tmpl` 第 2 步加 Name confusing + simpler approach (R-002)
- [ ] step 3: 编辑 `anti-laziness.md.tmpl` 门禁 5 加 Push Back 子节 (R-003)
- [ ] step 4: `make dogfood` 同步 (R-004)
- [ ] step 5: grep 硬检查（R-001/R-002/R-003 关键词命中）
- [ ] step 6: `make ci` 全绿 (R-005)
- [ ] step 7: `/multi-review` 轻量评审（2 角色：正确性 + 测试完整性）
- [ ] step 8: 完成报告 + audit + 进入待验证

## 质量基线

- 测试：658 pass, 25.625s
- 起始 HEAD: 977dbf4
- 起始分支: master

## Progress

| Step | 描述 | 状态 |
|---|---|---|
| 1 | task-lifecycle 第 1 步 | [ ] |
| 2 | task-lifecycle 第 2 步 | [ ] |
| 3 | anti-laziness 门禁 5 Push Back | [ ] |
| 4 | make dogfood | [ ] |
| 5 | grep 验证 R-001/002/003 | [ ] |
| 6 | make ci | [ ] |
| 7 | multi-review 轻量 | [ ] |
| 8 | 完成报告 | [ ] |
