# Current Task

## 状态：实施中

## LFG 进度

### Goal（目标）

把 OpenViking（volcengine, AGPL-3.0）的 **Memory dedup 4 决策**机制（skip / create / merge / delete）吸收到本项目的 `/compound` 和 `/lint-lessons` 工作流里，并把 `knowledge-conflict-resolution.md` T3 章节的「转条件分支合并」模糊描述升级成可操作 SOP。

### Context（上下文）

- Issue：GitHub #45（`evolution` + `absorbed` 标签）→ 自动进入进化集成 + 完整通道
- 复杂度：**大**（跨 3 个模板/规则文件 + 新增测试 + 文档同步）
- 基线 commit：`a85ce2e`
- 工作分支：待创建 `feat/openviking-dedup-decision`（阶段 1 处理）
- 来源参考：OpenViking `docs/design/` + `docs/en/concepts/06-extraction.md`（设计思想，不拷代码）

### Assumptions（假设清单）

- 假设 1：**复用 `memory search --top N` BM25**，不引入 embedding / vecdb / faiss | 依据：Issue 硬约束；`.agent-harness/bin/memory search --top 3` 已支持
- 假设 2：**/compound 新增 dedup 决策插在现有"步骤 3 查重与合并"之后，写入之前**（作为步骤 3.6）| 依据：OpenViking extraction 逻辑是"找相似→决策→存储"
- 假设 3：**4 决策输出给用户确认，不自动执行** | 依据：Issue 硬约束 + 现有铁律（knowledge-conflict-resolution.md「不自动合并/删除/降级/晋升」）
- 假设 4：**T3 章节"处理路径"替换为 4 决策 SOP**，T1/T2/T4/T5/T6 语义不变 | 依据：Issue 方案明确只扩 T3
- 假设 5：**`/lint-lessons` 每对矛盾输出双标签**（`resolution-type: T3/T4/T5/T6` + `dedup decision: skip/create/merge/delete`）| 依据：Issue 验收条
- 假设 6：**不改 Python 模块**，只改模板 + 规则 + 测试 + 文档 | 依据：memory_search.py 已完备；本次落地在指令模板层
- 假设 7：**保留 `/lint-lessons` 铁律"保留 A 删 B..."原文案** | 依据：`tests/test_gsd_absorb.py::test_lint_lessons_has_contradiction_detection` 用 `assertIn("保留 A", text)` 锁定，来自 lessons.md:67 教训

### Non-goals（明确不做）

- ❌ 不引入 embedding / 向量索引依赖
- ❌ 不拷贝 OpenViking AGPL-3.0 代码
- ❌ 不改 `memory_search.py` / `memory.py` / 其他 Python 模块
- ❌ 不改 T1 / T2 / T4 / T5 / T6 章节的处理路径
- ❌ 不自动执行 dedup 决策（保持"只给建议"铁律）

### Acceptance（验收标准，与 Issue 对齐）

1. `/compound` 模板新增 dedup 决策流程（步骤 3.6），4 分支 skip/create/merge/delete 完整
2. `/lint-lessons` 每对矛盾条目输出带 **resolution-type + dedup decision** 双标签
3. `knowledge-conflict-resolution.md` T3 章节升级为 4 决策 SOP，替换「转条件分支合并」单一建议
4. 新增 3+ 单测覆盖 skip / create / merge / delete 4 种分支（在 `tests/test_lessons_conflict_resolution.py` 或独立文件）
5. `make dogfood` 同步；`make ci` 全绿
6. `docs/product.md` 持续演进段新增条目（9.1）
7. 不破坏现有契约测试（特别是 `test_lint_lessons_has_contradiction_detection` 的 `assertIn("保留 A")` 锚点）

### Decisions（关键决策）

- **不扩展 memory_search.py CLI**：已有 `--top` 足够；避免改 _runtime 副本同步（lessons.md:133 教训）
- **4 决策定义对齐 OpenViking 但语义本地化**：
  - `skip`：新 lesson 语义与已有高度重合 → 不写入
  - `create`：全新信息 → 正常追加
  - `merge`：与某条 confirmed lesson 部分重合 → 合并升级为 `when:` 条件分支
  - `delete`：新 lesson 证伪了某条 confirmed lesson → 标注后归档旧条（不物理删，保留可追溯）
- **T3 从"单一建议"升级为"4 决策 SOP"**：保留"不自动执行"铁律；输出决策建议交用户确认
- **历史参考**：
  - lessons.md:67 — `/lint-lessons` 铁律原文案"保留 A 删 B..."被测试 assertIn 锁定，本次要**扩展**而非**替换**
  - lessons.md:133 — 改 Python 模块需同步 _runtime，本次仅改模板规避此风险
  - lessons.md:428 — `.claude/commands/` 下任何 .md 会自动注册 slash command，本次不新建文件只改已有

### Files（预计涉及文件）

- `src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl` — 新增步骤 3.6
- `src/agent_harness/templates/superpowers/.claude/commands/lint-lessons.md.tmpl` — 输出格式扩展
- `src/agent_harness/templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl` — T3 章节 + 接入点更新
- `tests/test_lessons_conflict_resolution.py` — 新增 3+ 契约测试
- `docs/product.md` — 持续演进条目（9.1 号位）
- `.claude/commands/compound.md` / `.claude/commands/lint-lessons.md` / `.claude/rules/knowledge-conflict-resolution.md` — dogfood 同步（`make dogfood` 自动）
- `.agent-harness/memory-index.md` — L1 索引刷新（`memory rebuild --force` 自动）

### Quality Baseline（质量基线，阶段 1 记录）

待阶段 1 跑 `make test` + `make check` 记录

### Progress（阶段进度）

- [x] 阶段 0 理解与评估
- [x] 阶段 1 环境准备 — 分支 feat/openviking-dedup-decision, HEAD a85ce2e, 基线 614 tests / check pass
- [x] 阶段 2 构思（跳过，/brainstorm 不适用——本任务方案已明确）
- [x] 阶段 2.5 规格（跳过——Issue body 已含足量验收标准）
- [x] 阶段 3 计划 — docs/superpowers/specs/2026-04-23-openviking-dedup-decision-plan.md, 8 维度自检通过
- [x] 阶段 4 实施（按计划 TDD）— 619/619 tests pass
  - [x] 步骤 1 RED: 扩 5 条契约测试（3 fail + 2 pass 回归）
  - [x] 步骤 2 扩 knowledge-conflict-resolution.md.tmpl T3 章节（新增 4 决策 SOP 子段）
  - [x] 步骤 3 /compound 新增第 3.6 步（dedup 决策 + memory search --top 3）
  - [x] 步骤 4 /lint-lessons 新增 2.2.2 双标签（resolution-type + dedup decision）
  - [x] 步骤 5 make dogfood（3 文件同步）
  - [x] 步骤 6 docs/product.md 9.1 条目
  - [x] 步骤 7 make ci 619/619 绿（原 614 → +5 新测试）
  - [x] 步骤 8 memory rebuild --force（10 教训 / 5 任务刷新）
- [ ] 阶段 4.3 自检
- [ ] 阶段 5 评审（/multi-review）
- [ ] 阶段 6 修复循环
- [ ] 阶段 7 验证（/verify + R-ID 核验 + make ci）
- [ ] 阶段 8 质量对比
- [ ] 阶段 9 沉淀（/compound + memory rebuild + ADR 状态）
- [ ] 阶段 10 收尾（/finish-branch + /doc-release + 关闭 Issue #45）
