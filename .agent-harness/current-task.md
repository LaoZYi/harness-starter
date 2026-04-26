# Current Task

## 任务目标

补吸 mksglu/context-mode BENCHMARK.md 的 2 项增量（Issue #54 / #29 的 12 天后续）：
- Tool Decision Matrix（数据类型 → 处理方式分类学）
- Smart Truncation 头尾保留策略（防丢尾部错误信息）

## 假设清单

- 假设：扩 `context-budget.md.tmpl` 单文件，规则 1 加 Decision Matrix、规则 2 加 Smart Truncation | 依据：Issue #54 评估 ~30 行
- 假设：本项目工具栈对位 = `memory search` / `grep`（精确召回）vs shell 脚本（汇总型） | 依据：现有规则 1 示例都用 grep/find/jq/awk
- 假设：Smart Truncation 用 shell `{ head -N; echo ...; tail -N; }` 模式即可，不引入 60/40 split 算法 | 依据：simplicity 准则
- 假设：master 直接工作，每步打 lfg/step-N tag | 依据：项目惯例

## 验收标准（R-IDs）

- [ ] **R-001** 规则 1 加 Tool Decision Matrix（汇总型 vs 精确召回型分类）
  - 硬检查：grep `精确召回|汇总型` ≥ 各 1 次 + 新增表格 ≥ 5 行
- [ ] **R-002** 规则 2 加 Smart Truncation 头尾保留段 + shell 示例
  - 硬检查：grep `Smart Truncation|头尾保留|head.*tail` ≥ 1 次
- [ ] **R-003** 来源标注引用 BENCHMARK.md 关键洞见
  - 硬检查：grep `BENCHMARK|96%|FATAL` ≥ 1 次
- [ ] **R-004** `make dogfood` 同步成功
  - 硬检查：dogfood 输出含 `~ .claude/rules/context-budget.md`
- [ ] **R-005** `make ci` 全绿（≥ 658 tests + ruff/mypy 0 issue）

## 计划步骤

- [ ] step 1: 规则 1 加 Tool Decision Matrix (R-001 + R-003)
- [ ] step 2: 规则 2 加 Smart Truncation (R-002 + R-003)
- [ ] step 3: `make dogfood` 同步 (R-004)
- [ ] step 4: grep 硬检查 (R-001/R-002/R-003)
- [ ] step 5: `make ci` 全绿 (R-005)
- [ ] step 6: 主会话 2 角色评审（正确性 + 一致性）
- [ ] step 7: 完成报告 + audit + 待验证

## 质量基线

- 测试：658 pass, 25.235s
- 起始 HEAD: 1c434d7
- 起始分支: master

## Progress

| Step | 描述 | 状态 |
|---|---|---|
| 1 | 规则 1 Tool Decision Matrix | [ ] |
| 2 | 规则 2 Smart Truncation | [ ] |
| 3 | make dogfood | [ ] |
| 4 | grep 硬检查 | [ ] |
| 5 | make ci | [ ] |
| 6 | 评审轻量 | [ ] |
| 7 | 完成报告 | [ ] |
