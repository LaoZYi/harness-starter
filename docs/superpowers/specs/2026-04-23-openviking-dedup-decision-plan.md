# Plan：吸收 OpenViking Memory dedup 4 决策

日期：2026-04-23
Issue：GitHub #45 / `evolution` + `absorbed` 标签
复杂度：大（evolution 模式 → 完整通道）
基线 commit：a85ce2e（feat/openviking-dedup-decision）
基线测试：614 tests pass
基线检查：All checks passed

---

## R-ID 需求映射

| R-ID | 验收标准 | 对应步骤 |
|---|---|---|
| R-001 | `/compound` 新增 dedup 决策步骤（3.6），4 分支 skip/create/merge/delete 完整 | step 1, 3 |
| R-002 | `/lint-lessons` 每对矛盾输出 `resolution-type` + `dedup decision` 双标签 | step 1, 4 |
| R-003 | `knowledge-conflict-resolution.md` T3 章节升级为 4 决策 SOP | step 1, 2 |
| R-004 | 新增 3+ 单测覆盖 skip / create / merge / delete 4 种分支 | step 1 |
| R-005 | `make dogfood` 同步；`make ci` 全绿 | step 5, 7 |
| R-006 | `docs/product.md` 持续演进段新增条目 9.1 | step 6 |
| R-007 | 不破坏 `assertIn("保留 A")` 锚点，`test_rule_contains_all_five_types` 等现有契约绿 | step 4 约束 + step 7 兜底 |

---

## 步骤

### 步骤 1（RED）：写 5 条契约测试

文件：`tests/test_lessons_conflict_resolution.py`（现有文件扩展）

追加测试类 `OpenVikingDedupDecisionTests`，覆盖：

**正常路径（3 条）**：
- `test_t3_has_four_decision_sop`：读 `knowledge-conflict-resolution.md.tmpl`，断言 T3 段落含 4 个决策关键词 `skip` / `create` / `merge` / `delete`
- `test_compound_has_dedup_step_36_with_memory_search`：读 `compound.md.tmpl`，断言含 `3.6` + `memory search` + `--top` 字样
- `test_lint_lessons_has_dedup_decision_label`：读 `lint-lessons.md.tmpl`，断言矛盾输出段同时含 `resolution-type:` 和 `dedup decision:` 字面

**边界/回归（2 条）**：
- `test_lint_lessons_preserves_keep_a_anchor`：保留 `保留 A` 文本锚点（回归保护，锁定 `lessons.md:67` 教训）
- `test_compound_dedup_not_auto_execute`：断言 compound 3.6 步含 `不自动执行` 或 `不 block 写入` 字样（铁律回归）

**验证命令**：
```bash
.venv/bin/python -m pytest tests/test_lessons_conflict_resolution.py -v 2>&1 | tail -30
```

**期望**：5 条全 FAIL（RED）。

### 步骤 2：扩 knowledge-conflict-resolution.md.tmpl T3 章节

文件：`src/agent_harness/templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl`

T3 段「处理路径」段之后、T4 段之前**新增子段**「T3 的 4 决策 SOP（dedup decision，OpenViking 吸收）」：

- 前置：先跑 `.agent-harness/bin/memory search "<关键词>" --top 3 --scope lessons` 拿 top-3 相似条目
- 4 决策表格：skip / create / merge / delete，每行含「触发信号」+「标准动作」
- 硬约束 3 条：不自动执行；merge/delete 须刷 memory-index；delete 不物理删（保留 deprecated 标注）

同时更新「与 `/compound` 的接入点」章节末段，承接 dedup 决策入 3.6 步；「铁律」段追加 `dedup decision` 必须与 `resolution-type` 双标签叠加。

**保留不动**：
- 「处理路径」段的现有 4 条（条件分支 / 不擅自二选一 / 等用户确认 / 确认后固化）
- T3 段原「条件分支 + 不删任一」语义关键词（给 `test_t3_processing_path_is_conditional_branch` 兜底）

**验证命令**：
```bash
grep -A 5 "T3 的 4 决策 SOP" src/agent_harness/templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl | head -20
```

**期望**：4 决策表格渲染完整。

### 步骤 3：/compound 新增步骤 3.6（Dedup 决策）

文件：`src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl`

在第 3.5 步末尾追加承接句「冲突分型完成后，进入第 3.6 步做 dedup 决策」；在第 4 步之前**新增第 3.6 步**：

- 跑 `.agent-harness/bin/memory search "<关键词>" --top 3 --scope lessons`
- 基于返回结果做 skip / create / merge / delete 4 选 1
- 输出决策建议格式示例（5 行，含 A/B/C 分支回复选项）
- 铁律 3 条：引用 T3 章节完整 SOP；**不自动执行**；merge/delete 必须刷 memory-index

**验证命令**：
```bash
grep -n "第 3.6 步\|memory search --top\|skip\|create\|merge\|delete" src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl | head -20
```

**期望**：第 3.6 步结构完整，4 决策关键词齐全。

### 步骤 4：扩 /lint-lessons 输出双标签（含「保留 A」锚点保护）

文件：`src/agent_harness/templates/superpowers/.claude/commands/lint-lessons.md.tmpl`

在 2.2.1 子段之后**新增 2.2.2**「标注 dedup decision（OpenViking 吸收）」：

- 4 决策在 lint-lessons 语义的表格（skip=维持现状 / create=补 when: / merge=合并 / delete=删一条）
- 说明「4 决策与现有 4 模板（保留 A 删 B / 保留 B 删 A / 合并为一条 / 都保留补充适用条件）是元分类 vs 具体裁决文字的双标签关系」

更新**矛盾输出格式示例**，每个示例条目追加 `· dedup decision: <value>` 标签。

更新**铁律段**：
```
- 每对候选必须同时给出：症状分类 + resolution-type（T3/T4/T5/N/A）+ dedup decision（skip/create/merge/delete/N/A）+ 建议动作
```

**保留不动**：
- 第 99 行「保留 A 删 B / 保留 B 删 A / 合并为一条 / 都保留但补充适用条件」4 模板原文案

**验证命令**：
```bash
# 新增
grep -n "2.2.2\|dedup decision" src/agent_harness/templates/superpowers/.claude/commands/lint-lessons.md.tmpl | head -10
# 回归
grep -c "保留 A" src/agent_harness/templates/superpowers/.claude/commands/lint-lessons.md.tmpl
```

**期望**：2.2.2 + dedup decision 出现；「保留 A」至少 1 次出现。

### 步骤 5：make dogfood 同步 .claude/ 副本

```bash
make dogfood 2>&1 | tail -10
```

**期望**：无漂移 warning。同步后 `.claude/commands/compound.md`、`.claude/commands/lint-lessons.md`、`.claude/rules/knowledge-conflict-resolution.md` 与 tmpl 一致。

### 步骤 6：docs/product.md 新增持续演进条目 9.1

文件：`docs/product.md`

在 9.2 条目**之前**（时间倒序顶部）追加 9.1 条目：

- 标题：**OpenViking Memory dedup 4 决策（2026-04-23，吸收自 volcengine/OpenViking）**
- 内容 200-300 字，说明：吸收机制（BM25 预过滤 + 4 决策）、落地位置（/compound 3.6 + /lint-lessons 2.2.2 + KCR T3 SOP）、零依赖原则（复用 memory search 不引入 embedding）、参考来源（OpenViking 设计思想不拷代码）

**验证命令**：
```bash
grep -n "^9\.1\. " docs/product.md | head -2
```

### 步骤 7：make ci 全绿（含 dogfood 守卫 + skills-lint）

```bash
make ci 2>&1 | tail -20
```

**期望**：
- 5 条新测试绿
- 总数 614 → 619
- `test_lint_lessons_has_contradiction_detection` 等现有契约全绿
- `test_t3_processing_path_is_conditional_branch` 绿（T3 原语义保留）
- `check_repo.py` 无新增警告
- `harness skills lint` 无漂移

### 步骤 8：memory rebuild --force 刷新 L1 索引

```bash
.agent-harness/bin/memory rebuild . --force
```

**期望**：`memory-index.md` 的「参考资料」段不变（本次未增 references），最近教训保持同步。

---

## 完成标准

- [ ] 步骤 1 5 条测试先 RED
- [ ] 步骤 2-4 实施后 GREEN（5/5）
- [ ] 步骤 5 dogfood 无漂移
- [ ] 步骤 6 docs/product.md 9.1 条目存在
- [ ] 步骤 7 `make ci` 全绿（619 tests）
- [ ] R-007 验证：`grep -c "保留 A" lint-lessons.md.tmpl` >= 1
- [ ] 步骤 8 memory rebuild 成功

---

## plan-check 8 维度自检

1. **需求覆盖**：R-001..R-007 全部映射到具体步骤 ✅
2. **原子性**：每步独立可验证（grep / pytest / make） ✅
3. **依赖排序**：1 (RED) → 2/3/4 (实施) → 5 (dogfood) → 6 (docs) → 7 (ci) → 8 (index) ✅
4. **文件作用域**：每步点明绝对路径，无"相关文件"模糊词 ✅
5. **可验证性**：每步含 `验证命令` + `期望` 两行 ✅
6. **上下文适配**：零依赖铁律 + `保留 A` 锚点保护 + 不改 Python 模块，对齐 lessons.md:67 / :133 / :428 三条历史教训 ✅
7. **缺口检测**：
   - ADR：本次吸收机制不是架构决策（只是 SOP 扩展），无须新增 ADR ✅
   - memory-index 刷新：step 8 ✅
   - audit WAL：每次改关键文件后在执行阶段追加 ✅
8. **Nyquist 合规**：8 步粒度（每步 2-5 分钟），既不碎也不大 ✅

第 9 维度（Agent 工程化）：不涉及多 agent 协作（单 agent 模板编辑），跳过。
