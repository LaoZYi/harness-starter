# Current Task

## 状态：待验证

## LFG 进度

### Goal
修复 GitLab Issue #23 — `harness upgrade apply` 在 base 基线缺失时把用户长期维护的 `docs/architecture.md` 整体覆盖为 40 行模板骨架。

### Context
- 复杂度:中 | 通道:标准 | 基线 commit:317977e | 工作分支:fix/issue-23-three-way-base-missing-protect
- 方案 A:缺 base 时写 `<file>.harness-new` 旁路文件 + 警告,保留原文件 + `--force` 逃生口
- 保护策略**对所有 three_way 文件通用**,不维护白名单

### Acceptance(R-ID 三元映射,10 个全 satisfied)
- [x] R-001 无 base 基线的 three_way 文件不再被无声覆盖 — ✅ `test_no_base_protects_user_content`
- [x] R-002 框架新模板写到 `<file>.harness-new` 旁路文件 — ✅ `test_no_base_writes_sidecar`
- [x] R-003 `UpgradeExecutionResult.missing_base_files` 字段 — ✅ `test_result_reports_missing_base_files`
- [x] R-004 plan 阶段 checklist 含旁路警告 — ✅ `test_plan_checklist_warns_missing_base`
- [x] R-005 `--force` 逃生口强制覆盖 — ✅ `test_force_flag_overrides_protection`
- [x] R-006 文件不存在时走 create,不触发保护 — ✅ `test_no_base_file_missing_still_creates`
- [x] R-007(回归) 有 base 时 three_way 合并行为不变 — ✅ `test_with_base_still_three_way_merges`
- [x] R-008 `docs/product.md` 同样受保护(策略通用)— ✅ `test_product_md_also_protected`
- [x] R-009 连续 apply 时 sidecar 被刷新 — ✅ `test_sidecar_overwrites_prior_sidecar`
- [x] R-010 base 恢复后回到 three_way — ✅ `test_after_base_restored_resumes_three_way`

### Progress
- [x] 0.1 理解任务:读 Issue #23、复述根因、列假设
- [x] 0.2 加载历史:memory-index、BM25 检索、task-log 2026-04-09
- [x] 0.3 复杂度判断:中 → 标准通道,用户确认方案 A
- [x] 1 环境准备:工作分支 + 基线 588 tests 全绿
- [x] 2.5 规格:R-001..R-010 + 五类场景覆盖
- [x] 3 计划:本文件 Progress(7 步)
- [x] 4 实施:
  - [x] 4a 写失败测试(RED):10/10 FAIL
  - [x] 4b 改 upgrade.py 实现(GREEN):10/10 PASS
  - [x] 4c CLI 新增 `--force` + checklist 警告文案
  - [x] 4d make ci 全绿(598 tests)
- [x] 5 自检:验收 R-ID 10/10 satisfied,规则合规 5/5
- [x] 6 验证:/verify R-ID 核验 + 穷举端到端 19 check(5 场景)
- [x] 7 质量对比:测试 588 → 598(+10),无新增警告
- [x] 8 文档同步:product/architecture/runbook/CHANGELOG/release 全量更新
- [x] 9 沉淀:2 条教训(策略默认值边界 + 用户数据保护测试覆盖),memory-index 已刷新,WAL 已写
- [ ] 10 收尾:待用户验证通过后 commit + 关闭 GitLab Issue #23

### Files(实际涉及)
- `src/agent_harness/upgrade.py` — 保护分支 + force 参数 + SIDECAR_SUFFIX + checklist 文案
- `src/agent_harness/models.py` — `UpgradeExecutionResult.missing_base_files`
- `src/agent_harness/cli.py` — `--force` flag 注册 + 透传
- `tests/test_apply_upgrade.py` — `NoBaseProtectionTests` 10 条(+212 行)
- `docs/product.md` / `docs/architecture.md` / `docs/runbook.md` — 行为说明
- `CHANGELOG.md` / `docs/release.md` — 测试计数 588→598
- `.agent-harness/lessons.md` — 2 条新教训
- `.agent-harness/memory-index.md` — 自动刷新
- `.agent-harness/task-log.md` — 归档记录

### Quality Baseline → Final
- 测试:588 → 598(+10),100% 通过,14.416s
- Lint:通过(make ci 全绿)
- 端到端:5 场景 19 check 全过

### 给用户验证的要点
1. Bug 是否真的修复?看 `/tmp/issue23_e2e_verify.py` 的场景 1——用户 500 行 NestJS 架构在缺 base 时被完整保留
2. 策略是否太严(误保护)?看场景 2——有 base 时行为不变,三方合并正常
3. 逃生口是否工作?场景 3 `--force` 能强制覆盖
4. 连续操作是否稳?场景 4/5 覆盖
5. 回归是否破坏?`test_user_content_preserved_in_three_way` + `CLAUDE.md three_way` 等历史测试全绿

### 完成报告(Issue #23)
- 发现:用户文档(architecture.md 508 行 NestJS)在 harness upgrade 时被整体覆盖为 40 行模板骨架
- 根因:`three_way` 策略默认值在 base 缺失的边界场景静默退化为 overwrite,违反了"保护用户内容"的核心目的
- 修复:缺 base 时改写 `<file>.harness-new` 旁路文件 + 警告,原文件零修改;`--force` 作为显式逃生口;保护对所有 three_way 文件通用
- 质量保证:10 条 R-ID 单元测试 + 5 场景 19 check 端到端穷举 + 全量 598 tests 回归 + make ci 全绿
- 沉淀:2 条新教训(策略默认值边界处理 + 用户数据保护测试覆盖的五类场景铁律)
