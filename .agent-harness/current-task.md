# Current Task

## 状态：待用户确认（评审路径选择）

## LFG 进度

### Goal（目标）

吸收快手 sec-audit-pipeline 反偷懒工程学到本框架（Issue #46），核心落地 3 点：
1. 新增 `/pressure-test` skill（7 类压力 × 6 场景，给关键 skill 做 TDD）
2. `anti-laziness.md` 新增门禁 7（压力测试）+ 门禁 3 表新增 3 条反合理化借口 + 门禁 4 增强字段级必填
3. `autonomy.md` Trust Calibration 新增 **3b. orchestrator 疲劳硬门禁**

### Context（上下文）

- Issue：GitHub #46（`evolution` 标签 → 完整通道）
- 复杂度：**大** | 通道：**完整**（不起 squad）
- 基线 commit：`3441671`（master HEAD 合并 #45 后）
- 工作分支：`feat/kuaishou-pressure-test`
- 来源：微信公众号「快手安全应急响应中心」2026-04-23 文章，作者赵海洋；项目 `sec-audit-pipeline` 与本框架同名同源独立演化

### Assumptions（7 条）

- 假设 1：evolution 完整通道跳过 /spec/ideate/brainstorm（Issue body 已含完整规格和验收）
- 假设 2：`/pressure-test` 归类 `meta` / `expected_in_lfg: false`（与 /health / /retro / /lint-lessons 同类，不入 lfg 主流程）
- 假设 3：门禁 7 默认触发频次「每月 + 新反合理化条目添加时」（Issue 明示）
- 假设 4：3 条新反合理化借口逐字抄 Issue 描述（保留原事故句式）
- 假设 5：anti-laziness.md 顶部声明「4 道」过期（实际 6 道），本次改成 7 道趁机修
- 假设 6：不引入 Z3 / 跨模型对抗 / 黑盒白盒（Issue 明示不吸收）
- 假设 7：三处「待核实 ⚠️」条目（三层架构 / Controller 5 件事 / 方法论溯源）暂不阻断本次实施，必要时 follow-up Issue

### Non-goals

- 不引入 Z3/SMT 依赖
- 不 OCR 文章图片找 Controller 5 件事具体清单
- 不改 /multi-review / /cso / /lfg 实现（压力测试只引用）
- 不改 Python 模块（规避 _runtime 同步风险）

### Acceptance（R-ID）

| R-ID | 验收标准 |
|---|---|
| R-001 | `/pressure-test.md.tmpl` 新增,含 7 类压力 + 6 默认场景 + 作用域清单 |
| R-002 | `skills-registry.json` 注册 pressure-test(category=meta, expected_in_lfg=false) |
| R-003 | `anti-laziness.md.tmpl` 门禁 7 压力测试定义 + 顶部声明改 7 道 |
| R-004 | `anti-laziness.md.tmpl` 门禁 3 表新增 3 条反合理化借口(Agent 写入失败手动接管 / 上下文太长不想 spawn / SKILL 太长精简传给 sub) |
| R-005 | `anti-laziness.md.tmpl` 门禁 4 增强「字段级必填」声明 |
| R-006 | `autonomy.md.tmpl` Trust Calibration 新增 3b orchestrator 疲劳硬门禁 |
| R-007 | 新门禁机制均标记 `defensive-temporary`(遵循 lessons.md `反偷懒与协作记忆要解耦` 规则) |
| R-008 | 新增契约测试覆盖 skill / 门禁 / 3b |
| R-009 | `make ci` 全绿 + `make dogfood` 无漂移 + `harness skills lint` 通过 |
| R-010 | `docs/product.md` 9.1 之前新增吸收条目 + 测试计数同步 |

### Progress

- [x] 阶段 0 理解与评估
- [x] 阶段 1 环境准备 — 分支 feat/kuaishou-pressure-test, HEAD 3441671, 基线 620 tests
- [x] 阶段 2 构思(跳过,evolution 完整通道但方案已在 Issue body 明示)
- [x] 阶段 2.5 规格(跳过,Issue body 已是规格)
- [x] 阶段 3 计划 — docs/superpowers/specs/2026-04-23-kuaishou-pressure-test-plan.md, 8 维度自检通过
- [x] 阶段 4 实施 — 632/632 tests pass
  - [x] 步骤 1 RED: 12 条契约测试(9 fail + 3 error, 全部预期)
  - [x] 步骤 2 新增 pressure-test.md.tmpl(7 类压力 + 6 场景 + 4 默认作用域 + defensive-temporary 标记)
  - [x] 步骤 3 skills-registry.json 注册(meta / expected_in_lfg=false / decision_tree_label)
  - [x] 步骤 4 anti-laziness.md.tmpl 4 处改动(顶部 4→7 / 门禁 3 +3 借口 / 门禁 4 字段必填 / 门禁 7)
  - [x] 步骤 5 autonomy.md.tmpl 3b orchestrator 疲劳硬门禁
  - [x] 步骤 6 make dogfood(+1 新增 pressure-test.md,3 更新)
  - [x] 步骤 7 docs/product.md 9.0 + 计数 32→33 技能 / 620→632 测试(7 文件)
  - [x] 步骤 8 make ci 632/632 全绿 + skills lint 通过
  - [x] 步骤 9 memory rebuild --force
- [ ] 阶段 5 评审 — 待用户选路径 A 完整 / B 轻量 / C 跳过
- [ ] 阶段 6-10 修复/验证/沉淀/收尾
