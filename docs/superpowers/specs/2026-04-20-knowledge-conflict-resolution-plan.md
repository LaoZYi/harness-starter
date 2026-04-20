# 实施计划：知识冲突解析（Knowledge Conflict Resolution）

对应规格：`docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-spec.md`
对应 Issue：GitHub #43 / GitLab #22
分支：`feat/lessons-conflict-resolution-20260420`
基线：`0338b84`

## R-ID 映射

| R-ID | 内容 | 对应 Step |
|---|---|---|
| R-001 | 规则文件存在 + 结构完整 | Step 3, Step 5 |
| R-002 | `/lint-lessons` 分型字段 | Step 6 |
| R-003 | `/compound` 冲突预检 | Step 7 |
| R-004 | dogfood 无漂移 | Step 8 |
| R-005 | T3/T4/T5 处理路径文案 | Step 5（规则文件内） |
| R-006 | CHANGELOG + architecture.md 同步 | Step 9 |
| R-007 | ADR 存在且状态升到 Accepted | Step 2（Proposed）、Step 10（Accepted） |

## 步骤清单

### Step 1：写测试（RED 全部）

**文件**：`tests/test_lessons_conflict_resolution.py`（新）

**覆盖**：

```python
class KnowledgeConflictResolutionRuleStructureTests(unittest.TestCase):
    # R-001, R-005
    - test_rule_template_exists
    - test_rule_contains_all_five_types
    - test_t3_processing_path_is_conditional_branch
    - test_t4_processing_path_is_downgrade_to_tentative
    - test_t5_processing_path_is_warning_not_block
    - test_t1_and_t2_marked_out_of_scope_for_lessons

class LintLessonsTemplateTests(unittest.TestCase):
    # R-002
    - test_lint_lessons_template_has_resolution_type_field
    - test_lint_lessons_references_new_rule

class CompoundTemplateTests(unittest.TestCase):
    # R-003
    - test_compound_template_has_conflict_precheck_step
    - test_compound_precheck_classifies_by_type

class ADRStateTests(unittest.TestCase):
    # R-007
    - test_adr_file_exists
    - test_adr_has_valid_status_field
```

**验证命令**：`PYTHONPATH=src .venv/bin/python -m unittest tests.test_lessons_conflict_resolution -v`
**预期**：全部 RED（至少 `test_rule_template_exists` 等文件存在类断言失败）

### Step 2：写 ADR（Proposed）

**文件**：`docs/decisions/0002-knowledge-conflict-resolution.md`（新）

**内容骨架**：
- Status: Proposed
- Context: `/lint-lessons` 现仅分症状类型；`/compound` 不区分"重复"与"矛盾"；Imprint 5 型提供解决路径维度
- Decision: 新增元规则 `.claude/rules/knowledge-conflict-resolution.md`；lint-lessons + compound 消费该规则；只接入 T3/T4/T5
- Consequences: +1 规则文件，+2 skill 模板修改，+1 测试文件，+1 ADR；新约束是"冲突输出必须标 resolution-type"
- Alternatives considered: 合并进 anti-laziness.md（否，正交关注点）；全接入 T1-T5（否，T1/T2 不属 lessons 域）

**验证命令**：`test -f docs/decisions/0002-knowledge-conflict-resolution.md`

### Step 3：创建规则模板（R-001 GREEN）

**文件**：`templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl`（新）

**结构**：
1. 一句话目的
2. 5 型速查表（T1-T5 的场景 + 判定信号 + 处理路径）
3. 在本项目 lessons 域的适用性（T3/T4/T5 接入，T1/T2 保留参考）
4. 与 `/lint-lessons` 和 `/compound` 的接入点
5. 示例：3 个真实冲突场景（T3/T4/T5 各一）

**验证命令**：`.venv/bin/python -m unittest tests.test_lessons_conflict_resolution.KnowledgeConflictResolutionRuleStructureTests -v` → 全 GREEN

### Step 4：规则模板通过 dogfood 同步到项目

**命令**：`make dogfood`
**验证**：`test -f .claude/rules/knowledge-conflict-resolution.md && diff <(sed 's|{{project_name}}.*||' templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl) <(cat .claude/rules/knowledge-conflict-resolution.md) | head`
**预期**：dogfood 产物存在且内容一致（除模板变量替换）

### Step 5：规则模板完善（含 T3/T4/T5 示例与处理路径）

基于 Step 3 的骨架，把处理路径文案对齐 R-005 的具体字符串断言：
- T3 → 「转条件分支（`when:` 语义）+ 记录 mismatch，不删任一」
- T4 → 「两条都降级为 tentative，等用户确认」
- T5 → 「lesson 是警告，不是阻断；自然提醒风险不拒绝任务」

**验证命令**：跑 Step 1 里的 R-005 测试

### Step 6：`/lint-lessons` 模板改造（R-002 GREEN）

**文件**：`templates/superpowers/.claude/commands/lint-lessons.md.tmpl`

**改动**：
- 步骤 2.2 现有 5 类症状分类保留不动
- 在 2.2 输出格式后追加一段「2.2.1 标注 resolution-type（T3/T4/T5 或 N/A）」
- 在步骤 2.2 顶部加一句「本步骤参考 `.claude/rules/knowledge-conflict-resolution.md`」
- 输出示例从 `建议裁决：A 新且针对并发场景，B 可能过时` 扩展为 `resolution-type: T3（两 confirmed 相反）→ 建议：转条件分支`

**验证命令**：Step 1 里的 `LintLessonsTemplateTests`

### Step 7：`/compound` 模板改造（R-003 GREEN）

**文件**：`templates/superpowers/.claude/commands/compound.md.tmpl`

**改动**：
- 步骤 3 现有「重叠度判断」表格保留
- 新增「第 3.5 步：冲突预检（非重复而是矛盾）」：查重时若发现根因/解决方案相反而非相似 → 按 T3/T4/T5 分型 + 提示人工裁决
- 明确「预检是警告性，不 block」

**验证命令**：Step 1 里的 `CompoundTemplateTests`

### Step 8：dogfood 同步 commands（R-004 GREEN）

**命令**：`make dogfood`
**验证**：`make check`（含 dogfood 漂移检测）
**预期**：`.claude/commands/lint-lessons.md` + `.claude/commands/compound.md` 与模板一致

### Step 9：文档同步（R-006 GREEN）

**文件**：
- `CHANGELOG.md` — [Unreleased] 新增 `### Added — 知识冲突解析规则（GitHub #43 / GitLab #22，2026-04-20）`
- `docs/architecture.md` — 测试数 `529 个回归测试` → `(529 + N) 个回归测试`，描述段追加「知识冲突解析 N 条：规则结构 + lint-lessons 分型 + compound 预检 + ADR 状态」
- 其他 5 处 `527/529` 引用全量 grep 更新

**验证命令**：`.venv/bin/python scripts/check_repo.py`（count_consistency 全绿）

### Step 10：ADR 升级到 Accepted（R-007 最终）

**文件**：`docs/decisions/0002-knowledge-conflict-resolution.md`
**改动**：`Status: Proposed` → `Status: Accepted`；追加 `Accepted date: 2026-04-20`

### Step 11：全量验证 + 自检

**命令**：`make ci`（check + lint + typecheck + skills-lint + test）
**预期**：全绿

### Step 12：快速评审 + 提交

- 自审：验收标准 7/7 对照；规则合规 5/5
- `/multi-review` 2 审查员（正确性 + 测试完整性）
- `git commit` 结构化 conventional commit

## 依赖关系

```
Step 1 (RED tests)
  ↓
Step 2 (ADR Proposed)
  ↓
Step 3 → Step 4 → Step 5 (Rule file)
  ↓
Step 6 (lint-lessons) ⟂ Step 7 (compound)  [可并行]
  ↓
Step 8 (dogfood sync)
  ↓
Step 9 (docs sync)
  ↓
Step 10 (ADR Accepted)
  ↓
Step 11 (verify) → Step 12 (commit)
```

## 风险与回滚

- **风险 1**：规则文件文案写得太抽象，T3/T4/T5 在真实 lessons 上难以应用 → 通过 R-005 的具体字符串断言防止；补 3 个具体示例
- **风险 2**：dogfood 漂移（模板改了但 `.claude/` 没同步）→ `make check` 的 dogfood 检测会拦
- **风险 3**：更新 `docs/architecture.md` 的测试计数时漏一个引用点 → `scripts/check_repo.py::check_count_consistency` 自动扫全仓
- **回滚**：每步独立 commit + `lfg/step-N` tag；异常时 `git reset --hard lfg/step-N` 到前一步

## 历史教训引用

- `lessons.md` 2026-04-13 「抽 SSOT 时必须清单化所有下游消费方」→ 本次规则文件的下游消费方是 `/lint-lessons` 和 `/compound`，已在 Step 6/7 明确接入
- `lessons.md` 2026-04-20 「优先级契约测试必须覆盖所有优先级等级」→ 本次 5 型虽只接入 3 型，但规则文件要文案化全 5 型避免将来扩展时漏漆
- `lessons.md` 2026-04-08 「新增技能时文档散布计数需全量扫描」→ Step 9 的 grep 全仓防漏

## 不在本次范围（明确记录）

- Imprint 的 `confidence` 字段（confirmed / tentative）→ 单独 Issue
- Imprint 的 `.dna.md` DSL 格式 → 永不吸收
- Imprint 的用户级跨项目 profile → 单独 Issue
- T1 / T2 接入 lessons 域 → 规则文件中标记为 out-of-scope

## 计划校验（/plan-check 8 维度）

### 1. 需求覆盖
- 7 条 R-ID 全覆盖（见映射表）
- Issue body 的 4 项「落地方案」全映射到 Step（方案 1 → Step 3-5，方案 2 → Step 6，方案 3 → Step 7，方案 4 → Step 1）

### 2. 原子性
- 每 Step 2-5 分钟粒度；Step 6 和 Step 7 可并行
- 每 Step 都有明确的验证命令

### 3. 依赖排序
- 拓扑序：RED → 骨架 → 细节 → dogfood → docs → ADR final → verify
- 无循环依赖

### 4. 文件作用域
- 所有改动文件在结构段明确列出
- 新增 6 个文件、修改 4 个文件，共 10 处

### 5. 可验证性
- 每 Step 有具体的 shell 或测试命令作为验证
- 最终有 `make ci` 作为总闸

### 6. 上下文适配
- 已引用 lessons.md 3 条相关教训
- 遵循项目约定：`.md.tmpl` 放 templates/，dogfood 同步 .claude/，测试放 tests/

### 7. 缺口检测
- 不需要 /source-verify（本次不依赖外部框架 API）
- 不需要 /agent-design-check（本次不涉及多 agent 协作）
- 不需要 /cso（knowledge base 维护不触发生产安全）

### 8. Nyquist 合规
- 采样点：7 个 R-ID × 至少 1 条测试 + ADR 状态扫描 + dogfood 检测 = ≥ 9 个验证信号
- 覆盖频率够高，不会漏检
