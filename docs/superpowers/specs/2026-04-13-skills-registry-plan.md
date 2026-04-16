# Plan: Skills Registry SSOT 抽取（Issue #27 / GitLab #11）

复杂度：大 | 通道：完整 | 基线：`095346b` | 分支：`feat/skills-registry-issue-27`

## 设计概要

`skills-registry.json` 作为 34 个 skill 元数据的单一真相源，下游消费方：
- `which-skill.md.tmpl` — 决策树 + 三段式索引
- `lfg.md.tmpl` — 阶段覆盖表
- `test_lfg_coverage.py` — 合约测试 EXPECTED_IN/NOT_IN_LFG
- `harness skills lint` — 一致性检查（CI 强制）

## R-ID → Step 映射

| R-ID | 实施步骤 | 文件 |
|---|---|---|
| R-001 | Step 1, 2 | skills-registry.json |
| R-002 | Step 5 | which-skill.md.tmpl |
| R-003 | Step 6 | lfg.md.tmpl |
| R-004 | Step 7 | test_lfg_coverage.py |
| R-005 | Step 3, 4, 9 | skills_registry.py / skills_lint.py / cli.py / Makefile |
| R-006 | Step 11 | docs/architecture.md / docs/product.md |
| R-007 | Step 12 | .github/PULL_REQUEST_TEMPLATE.md |

## 详细步骤（15 步，每步 2-5 分钟粒度）

### Step 1：起 registry 骨架（R-001 1/2）
**文件**：`src/agent_harness/templates/superpowers/skills-registry.json`（新建）
- 写 schema 头：`{"registry_version": 1, "categories": [...], "skills": [...]}`
- 4 个 category 枚举：`process` / `implementation` / `review` / `meta`
- 添加首个示例 skill `tdd` 完整字段验证 schema
**验证**：`python3 -c "import json; json.load(open('src/agent_harness/templates/superpowers/skills-registry.json'))"`

### Step 2：填充 34 个 skill 元数据（R-001 2/2）
**文件**：`skills-registry.json`（同上）
- 按现有 `which-skill.md.tmpl` 决策树顺序填入
- 字段：`id` / `name` / `category` / `one_line` / `triggers` / `lfg_stage`（数组）/ `expected_in_lfg` / `decision_tree_label` / `exclusion_reason`（仅 false 时）
- 7 个 EXPECTED_NOT_IN_LFG（lfg/which-skill/write-skill/evolve/health/retro/process-notes）填 `exclusion_reason`
**验证**：`python3 -c "d=__import__('json').load(open('src/agent_harness/templates/superpowers/skills-registry.json')); assert len(d['skills'])==34; print('OK', len(d['skills']))"`

### Step 3：写 skills_registry.py 加载器 + 渲染器
**文件**：`src/agent_harness/skills_registry.py`（新建，~80 行）
- `load_registry(template_root: Path) -> dict` — 读 JSON + schema 校验
- `render_decision_tree(registry) -> str` — 生成 which-skill 决策树文本
- `render_skill_index_by_phase(registry) -> str` — 三段式索引（流程类/实现类/收尾类）
- `render_lfg_coverage_table(registry) -> str` — lfg 阶段覆盖表（按 lfg_stage 分组）
- `expected_in_lfg(registry) -> set[str]` / `expected_not_in_lfg(registry) -> dict[str,str]`
**验证**：`python3 -c "from agent_harness.skills_registry import load_registry, render_decision_tree; ..."`

### Step 4：写 skills_lint.py 一致性检查
**文件**：`src/agent_harness/skills_lint.py`（新建，~60 行）
- 检查 1：每个 registry skill 都有对应 `commands/<id>.md.tmpl` 文件
- 检查 2：每个 `.md.tmpl` 文件都在 registry 中（孤儿检查）
- 检查 3：`expected_in_lfg=true` 的 skill 在 lfg.md.tmpl 中真实出现（用现有 EXPECTED_IN_LFG 同款正则）
- 返回 `(ok: bool, errors: list[str])`
**验证**：本地 import 跑通

### Step 5：which-skill.md.tmpl 加占位符（R-002）
**文件**：`src/agent_harness/templates/superpowers/.claude/commands/which-skill.md.tmpl`
- 把"技能调用顺序"三段（流程类/实现类/收尾类）替换为 `<<SKILL_INDEX_BY_PHASE>>`
- 把"决策树"区块替换为 `<<SKILL_DECISION_TREE>>`
- 保留：1% 法则、指令优先级、组合使用示例、常见错误、技能不存在时
**验证**：grep `<<SKILL_` 出现 2 次

### Step 6：lfg.md.tmpl 加占位符（R-003）
**文件**：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`
- 第 856-870 行（"## 技能覆盖清单（自检用）"段）的表格替换为 `<<SKILL_COVERAGE_TABLE>>`
- 保留段落标题和说明文字
**验证**：grep `<<SKILL_COVERAGE_TABLE>>` 出现 1 次

### Step 7：test_lfg_coverage.py 改读 registry（R-004）
**文件**：`tests/test_lfg_coverage.py`
- 删除硬编码的 `EXPECTED_IN_LFG` set 和 `EXPECTED_NOT_IN_LFG` dict
- 改为从 `skills-registry.json` 读取（在 `setUpClass` 里）
- 现有断言逻辑不变（`EXPECTED_IN_LFG <= referenced_skills`、`exclusion_reason` 必填等）
**验证**：跑 `tests.test_lfg_coverage` 全绿（保护现有契约）

### Step 8：渲染钩子接入 initializer / upgrade
**文件**：`src/agent_harness/initializer.py` 和 `src/agent_harness/upgrade.py`
- 在写出 `.claude/commands/which-skill.md` 和 `lfg.md` 后，调用 `skills_registry.render_*` 替换占位符
- 优先级：渲染发生在 jinja 占位符（`{{var}}`）替换之前，避免冲突
**验证**：`make dogfood` 后 `.claude/commands/which-skill.md` 和 `lfg.md` 不含 `<<SKILL_` 残留

### Step 9：harness skills lint 子命令（R-005）
**文件**：`src/agent_harness/cli.py`
- 新增 `skills` 子命令组 + `lint` 子子命令
- `harness skills lint <target>` 调用 `skills_lint.run(target)`，errors 非空时 exit 1
**验证**：`harness skills lint . && echo OK` 退出 0

### Step 10：Makefile 串入 CI
**文件**：`Makefile`
- `ci` target 加 `harness skills lint .` 步骤（在 check 之后、test 之前）
- 本地 `check` target 不加（按用户确认）
**验证**：`make ci` 输出含 "skills lint passed" 之类

### Step 11：合约测试 + 单元测试
**文件**：`tests/test_skills_registry.py`（新建）
- 测试 1：load_registry 解析 OK + skill 数 == 34
- 测试 2：render_decision_tree 输出含所有 expected_in_lfg=true 的 skill
- 测试 3：render_lfg_coverage_table 输出含全部 lfg_stage 分组
- 测试 4：skills_lint.run() 在干净仓库返回 ok=True
- 测试 5：人造一个孤儿 .md.tmpl，验证 lint 报错
- 测试 6：人造一个 registry 缺失文件的 skill，验证 lint 报错
**验证**：`python -m unittest tests.test_skills_registry -v` 全绿

### Step 12：文档同步（R-006）
**文件**：`docs/architecture.md` 和 `docs/product.md`
- architecture.md：新增"Skills Registry SSOT"段，说明 registry → 渲染 → 三处消费方的数据流
- product.md：新增条目 18，记录本次抽取 + skills lint 子命令
- 同步测试计数 438 → 444（新增 6 条测试）
**验证**：`python scripts/check_repo.py` exit 0

### Step 13：PR 模板（R-007）
**文件**：`.github/PULL_REQUEST_TEMPLATE.md`
- 加 checkbox："新增 skill 时只改 `skills-registry.json`，不要直接编辑 which-skill.md.tmpl 或 lfg.md.tmpl"
**验证**：grep "skills-registry" 出现

### Step 14：CHANGELOG
**文件**：`CHANGELOG.md`
- [Unreleased] 顶部新增条目，记录 registry 抽取、3 处消费方改造、harness skills lint
**验证**：grep "skills-registry" 在 [Unreleased] 段内

### Step 15：dogfood + 全量验证
- `make dogfood` 同步 `.claude/commands/{which-skill,lfg}.md`
- `make ci` 全绿（必须）
- `harness skills lint .` 单独跑通
- 抽样人工查 dogfood 产物：`.claude/commands/which-skill.md` 决策树和原版差异要可解释（顺序/排版微调可接受，内容无遗漏）

## 边界情况

| 边界 | 处理 |
|---|---|
| registry skill 数 < 34 | skills lint 报错（`expected: 34, found: N`） |
| `commands/` 出现 registry 没有的 .md.tmpl | lint 报"orphan skill" |
| 一个 skill 的 lfg_stage 是空数组但 expected_in_lfg=true | lint 报"contradiction" |
| 现有 which-skill/lfg 用户已自定义内容 | upgrade 三方合并保留，新占位符冲突时插标记 |

## 历史教训引用

- [架构设计] 单入口技能 ≠ 能力接入完整 — 本任务是该 lessons 的"双核对表"思想落地
- [模板] 模板中的文档占位符语法会被模板引擎吞掉 — 用 `<<SKILL_xxx>>` 而非 `{{}}` 避免和 jinja 冲突
- [架构设计] 兼容层降低迁移成本 — 但本任务**不做**双轨兼容（YAML+JSON），坚持 .json 单一格式（Issue #25 教训）
- [流程] 新增技能时文档散布计数需全量扫描 — 测试计数 438→444 三处同步（CHANGELOG/architecture/release）

## /plan-check 8 维度自检

| 维度 | 检查 | 结果 |
|---|---|---|
| 需求覆盖 | 7 R-ID 全部映射到 step | ✅ |
| 原子性 | 每步 2-5 分钟（15 步总计 ~60-90 分钟） | ✅ |
| 依赖排序 | registry → 渲染器 → templates → 测试 → CLI → 文档 | ✅ |
| 文件作用域 | 每步明确文件路径 | ✅ |
| 可验证性 | 每步有验证命令 | ✅ |
| 上下文适配 | Python stdlib，与项目零依赖原则一致 | ✅ |
| 缺口检测 | 边界情况表已列 | ✅ |
| Nyquist 合规 | 步骤粒度 < 5 分钟，可中断恢复 | ✅ |
