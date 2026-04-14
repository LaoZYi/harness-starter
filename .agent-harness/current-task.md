# Current Task

## 任务目标

吸收 mksglu/context-mode（7152⭐）的 3 层方法论——**Think in Code** + **BM25 兜底检索** + **Context Budget** 约束。Issue #29 / GitLab #13。

## 状态：进行中（LFG 完整通道）

## LFG 进度

### Context
复杂度：大 | 通道：完整（evolution）| 基线 commit：5625e48 | 工作分支：feat/context-mode-issue-29 | Issue：#29 / gl#13

### Assumptions
- 假设：3 项全部吸收，不裁剪 | 依据：每项纯方法论/零依赖 Python，MCP server 本体已被 Issue 提案排除
- 假设：Think in Code + 输出预算合并到一个规则 `common/rules/context-budget.md` | 依据：同属"控制上下文流入"主题
- 假设：BM25 实现放 `src/agent_harness/memory.py` 增强，新增 `memory search` 子命令 | 依据：memory 脚本已负责索引维护
- 假设：纯 stdlib BM25，无外部依赖；分词按 re（英文 \w+ + 中文字符独立 token）| 依据：项目零依赖约束
- 假设：Top-K 默认 5，BM25 参数 k1=1.5 b=0.75（Okapi 标准）| 依据：可在 CLI 参数覆盖

### Acceptance
1. `common/rules/context-budget.md.tmpl` 含 Think in Code + 工具输出预算双约束
2. `memory search <query>` CLI 工作，纯 stdlib BM25，输出 Top-K 相关段落
3. `/recall` 技能文档说明二级兜底链路（手工索引未命中 → BM25 兜底）
4. skills-registry + `superpowers-workflow.md` 清单更新
5. 新增单元测试：`tests/test_memory_search.py` 覆盖 tokenize/BM25/CLI 三层
6. `make ci` 通过（451 → ≥ 451 tests OK）+ `harness skills lint` OK
7. `make dogfood` 无漂移（_runtime/memory.py 同步）
8. Issue #29 + GitLab #13 双端关闭

### Files
- 新增：`templates/common/.claude/rules/context-budget.md.tmpl`
- 新增：`docs/superpowers/specs/2026-04-14-context-mode-{spec,plan}.md`
- 新增：`tests/test_memory_search.py`
- 修改：`src/agent_harness/memory.py`（新增 tokenize + bm25_score + search_lessons）
- 修改：`.agent-harness/bin/_runtime/memory.py`（dogfood 同步）
- 修改：`templates/common/.claude/commands/recall.md.tmpl`（添加 BM25 兜底说明）
- 修改：`templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`（新规则 + recall 更新）
- 修改：`templates/superpowers/.claude/commands/lfg.md.tmpl`（0.2 阶段 recall 兜底链路）
- 修改：`docs/product.md`、`docs/usage-guide.md`、`CHANGELOG.md`

### Quality Baseline
- 测试：451 全通过
- Lint：check 通过

### Testing Scenarios
- **正常**：BM25 对已知查询返回相关段落 + score 排序；完全匹配 score > 部分匹配
- **边界**：空查询返回空；超短查询（1 字符）不崩溃；中英混合 token；lessons.md 为空时优雅返回
- **错误路径**：文件不存在报错；无匹配时返回"未命中"提示而非空数组

### Progress
- [x] 理解与评估 — 复杂度大，完整通道
- [x] 环境准备 — 分支 feat/context-mode-issue-29，基线 451 tests OK
- [x] 规格 + 计划 — docs/superpowers/specs/2026-04-14-context-mode-{spec,plan}.md
- [ ] 实施 step 1 — 新增 context-budget 规则
- [ ] 实施 step 2 — memory.py 新增 tokenize + bm25 + search_lessons
- [ ] 实施 step 3 — memory CLI 新增 search 子命令
- [ ] 实施 step 4 — 单元测试 tests/test_memory_search.py
- [ ] 实施 step 5 — recall 技能模板升级 + workflow 清单
- [ ] 实施 step 6 — lfg 阶段 0.2 串入 memory search 兜底
- [ ] 实施 step 7 — dogfood + docs + CHANGELOG 同步
- [ ] 自检
- [ ] 验证 make ci
- [ ] 质量对比
- [ ] 沉淀 compound
- [ ] 完成报告
- [ ] 待验证
- [ ] 归档与关闭 Issue #29 / gl#13
