# 计划校验（Plan Check）

在实施计划进入执行前，对 plan 做 8 维度结构化校验 + 最多 3 轮修订循环。防止"计划看起来合理但遗漏关键点"导致中途返工。

灵感自 [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) 的 `/plan-check` 机制。

当前项目：`Agent Harness Framework`（cli-tool / python）

## 适用时机

- **作为 `/write-plan` 的收尾步骤**：计划生成后立即跑一遍 plan-check，捕捉低级漏项
- **作为独立调用**：对已存在的 `docs/superpowers/specs/*-plan.md` 做审查
- **作为 `/lfg` 阶段 3 的质量门**：计划通过 check 才进入实施

**跳过场景**：快速通道的微小任务无需 plan-check，因为计划只有 1-2 行，8 维度校验是冗余开销。

## 输入

- 计划文件路径（优先 `docs/superpowers/specs/*-plan.md`，其次 `.agent-harness/current-task.md`）
- 规格文件（如有 `/spec` 产物，用于 R-ID 覆盖校验）

如果都没有，告诉用户先运行 `/write-plan`。

## 8 维度校验

### 1. 需求覆盖（Requirement Coverage）

**检查**：spec 的每条 R-ID 是否都映射到至少一个 plan task，或明确标 `out-of-scope` 并附理由？

**通过标准**：
- 每个 R-ID 都有归属
- 无"悬空 R-ID"（既不实施也不标 out-of-scope）
- out-of-scope 条目注明了追踪 Issue / follow-up task

**常见失败**：Scope Reduction — spec 写了 R4 但 plan 里没出现。

### 2. 任务原子性（Task Atomicity）

**检查**：每个 task 是否真的是 2-5 分钟粒度？有没有被描述得"原子"但实际跨越多个逻辑单元？

**通过标准**：
- 每个 task 有明确的"做完/没做完"二元判定
- 每个 task 最多改 2 个文件（超过就拆）
- 每个 task 有独立的验证命令

**常见失败**：一个 task 写着"实现用户管理模块"——这不是 task，是 epic。

### 3. 依赖排序（Dependency Ordering）

**检查**：task 之间的依赖关系是否显式？能不能按 plan 的顺序一步步往下执行？

**通过标准**：
- 前置任务都在被依赖的任务之前
- 互不依赖的 task 标注为可并行
- 无循环依赖

**常见失败**：task 5 用了 task 8 才创建的函数——执行到 5 就 broken。

### 4. 文件作用域（File Scope）

**检查**：每个 task 声明了改哪些文件吗？文件路径是绝对还是相对？不同 task 是否改了同一个文件（冲突风险）？

**通过标准**：
- 文件路径具体（不是"相关文件"）
- 同一文件在多个 task 出现时，task 顺序决定了改动的叠加顺序
- 新增文件和修改文件分开列

**常见失败**：task 3 和 task 7 都改 `service.py`，顺序不清 → 合并风险。

### 5. 可验证性（Verifiability）

**检查**：每个 task 有没有"验证此 task 完成"的命令？验证失败时能直接定位问题吗？

**通过标准**：
- 有验证命令（`make test` / `make check` / 具体命令）
- 验证命令的预期输出明确
- 不写"应该能工作"这种不可验证的描述

**常见失败**：task 说"实现完成后运行测试"——运行哪个测试？怎么算通过？

### 6. 上下文适配（Context Fit）

**检查**：plan 的技术选型是否匹配项目现有约定？有没有引入与既有架构冲突的模式？

**通过标准**：
- 使用的库/框架是项目 `AGENTS.md` 或 `docs/architecture.md` 列出的
- 如果需要新依赖，有 ADR 记录理由
- 新增文件位置符合 `docs/architecture.md` 模块边界

**常见失败**：plan 里用 Redis 但项目从来没装过 Redis，且没 ADR 说明为什么引入。

### 7. 缺口检测（Gap Detection）

**检查**：plan 描述的改动以外，是否有"必须但被忽略"的配套改动？

**通过标准**：
- 改了 API → 更新了调用方
- 改了数据库 schema → 有 migration 步骤
- 改了规则文件 → 同步更新了 dogfood 版本
- 改了模板 → 同步了测试数
- 改了现有功能 → 回归了依赖该功能的代码

**常见失败**：改了 `/tdd` 技能但忘了跑 `make dogfood` 同步到本仓库。

### 8. Nyquist 合规（Nyquist Compliance）

**检查**：写任何代码前，每条需求是否有对应的自动化测试信号？

**通过标准**：
- 每条 R-ID 对应至少一个"可被 CI 识别"的测试 / 断言
- 不允许"集成测试整体通过"作为某 R-ID 的唯一证据
- 测试名或断言的位置在 plan 中可定位

**常见失败**：R3 说"空结果有提示"，plan 里没写 `test_empty_state` 或类似测试名。

## 修订循环

### 第 1 轮 — 初次校验

对 8 维度逐一打分：

| 维度 | 评分 | 发现的问题 |
|---|---|---|
| 需求覆盖 | 🔴 FAIL | R3 和 R5 悬空 |
| 任务原子性 | ✅ PASS | |
| 依赖排序 | 🟡 WARN | task 4 可能依赖 task 6 |
| ... | ... | ... |

**结论**：
- **所有 8 维度 PASS** → 输出"计划通过校验，可进入实施"
- **任何维度 FAIL 或多个 WARN** → 列出修订项，请 `/write-plan` 作者修订

### 第 2 轮 — 修订后复检

- 对第 1 轮的所有 FAIL/WARN 项逐条复查
- 新 PASS 的项标 ✅，仍 FAIL 的项保持 🔴

### 第 3 轮 — 最后机会

- 若仍有 FAIL → **🔴 升级到用户**

```
⚠️ plan-check 未收敛（已执行 3 轮）

仍 FAIL 的维度：
- 需求覆盖：R3 在第 2 轮被标 out-of-scope，但没追踪 Issue
- 缺口检测：改动涉及模板但未同步 dogfood

用户决策：
1. "强制通过" — 接受当前状态，带已知缺口进入实施
2. "回到规格" — 重新跑 /spec 调整 R-ID 或缩小范围
3. "放弃计划" — 重新 /write-plan
```

## 输出格式

```
## 计划校验报告

计划：docs/superpowers/specs/2026-04-13-user-search-plan.md
规格：docs/superpowers/specs/2026-04-13-user-search-spec.md

### 评分：6/8（🟡 需修订）

| 维度 | 评分 | 发现 |
|---|---|---|
| 1. 需求覆盖 | ✅ PASS | 5/5 R-ID 全部覆盖 |
| 2. 任务原子性 | ✅ PASS | 12 个 task 粒度合理 |
| 3. 依赖排序 | 🟡 WARN | task 7 可能需要在 task 5 之前 |
| 4. 文件作用域 | ✅ PASS | 无跨 task 同文件冲突 |
| 5. 可验证性 | ✅ PASS | 所有 task 有验证命令 |
| 6. 上下文适配 | 🔴 FAIL | 引入了 Redis 但无 ADR |
| 7. 缺口检测 | 🔴 FAIL | 改了 /tdd 模板但缺 dogfood 步骤 |
| 8. Nyquist 合规 | ✅ PASS | 所有 R-ID 有具体测试名 |

### 修订建议

P0（阻断）：
- 维度 6：运行 `/adr` 记录引入 Redis 的理由，或改用项目已有的缓存方案
- 维度 7：在 plan 末尾新增一步"运行 `make dogfood` 同步模板到本仓库"

P1（建议）：
- 维度 3：验证 task 5 和 task 7 的依赖，必要时调整顺序

### 下一步

修订 plan 后运行 `/plan-check` 第 2 轮复检，或直接进入 `/execute-plan` 如果 P0 能一次性解决。
```

## 集成

- `/lfg` 阶段 3 的"计划质量检查"可替换为运行本技能
- `.claude/rules/superpowers-workflow.md` 的推荐流程中将 plan-check 放在 /write-plan 之后、/execute-plan 之前
