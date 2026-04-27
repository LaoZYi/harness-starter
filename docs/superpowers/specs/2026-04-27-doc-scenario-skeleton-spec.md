# 通用文档场景脚手架（D 方案）— Spec

**Issue**：（暂未开 issue，本仓库直接迭代）
**日期**：2026-04-27
**对应 current-task**：`.agent-harness/current-task.md`「搭好通用文档场景的骨架」
**类型**：feature（D 方案 = 先抄 + 留 B 的位置）

## 假设清单

- 假设：`/lfg-doc` 是 universally available 技能（放 `templates/superpowers/.claude/commands/`），任何项目类型在 `harness init --no-superpowers=false` 时都能拿到 | 依据：与现有 `/lfg` 同源
- 假设：profile yaml 文件渲染到目标项目的 `.agent-harness/lfg-profiles/`，**仅作描述用**，本期 `/lfg` / `/lfg-doc` 命令本身不读取它 | 依据：D 方案约定，给 B 阶段（AI 推断匹配）留位置
- 假设：新增 `document` 项目类型用于"以文档为主要产物"的项目（标书目录、规范汇编、白皮书项目等），不替代任何现有类型 | 依据：`presets/` 已有 9 类，第 10 类填补 doc 场景
- 假设：本期不实现 `discover_project()` 对 doc 项目的自动检测（用户必须 `--type document` 显式声明），保持探测器纯净 | 依据：D 方案保守原则，自动检测属于"以后再做"的优化
- 假设：`/lfg-doc` 不调 `/git-commit` / `/finish-branch` / `/tdd` / `/multi-review` / `/verify` / `/debug` / `/health` / `/cso` / `/squad` —— 这些含代码假设；改用 doc 版替代或直接省略 | 依据：用户原话"写文档的人用不上 git"
- 假设：`docs/product.md` 第 67-70 行「支持的项目类型」中，`document` 与现有 9 类并列，不影响 `meta` 项目的特殊路由 | 依据：现有 meta 路由独立

## 1. 目标（Objective）

**要构建什么**：一套"写文档"场景的脚手架资产，让 `harness init --type document /path/to/doc-project` 后能拿到一份与现有 `/lfg`（写代码）骨架对齐、但调用文档专用 skill 的 `/lfg-doc` 流水线，配套 4 个 doc 专用 skill（`/outline-doc` / `/draft-doc` / `/review-doc` / `/finalize-doc`）和 2 份场景档案骨架（`lfg-profiles/code.yaml` / `lfg-profiles/doc.yaml`）。

**为什么要构建**：
- 业务：项目最初定位"写代码场景"，扩展到"写文档"是用户验证的第二个真实场景（标书是其中一个具体形态）
- 架构：通过 D 方案（先抄 + 留位置）验证"上层 skill 可以多场景化"，为以后做"AI 猜场景档案 + 用户确认"（B 方案）攒证据，不一上来设计抽象

**目标用户**：
- 投标团队（写标书）
- 内部规范 / 白皮书撰写者
- 任何把"产出文档"当作主要交付物、且希望复用本项目"反偷懒 / 分层记忆 / agent 协作"基础设施的团队

**成功定义**（可量化）：
- `harness init --type document /tmp/doc-test` 在新建空目录中生成完整脚手架（含 `/lfg-doc` 命令、4 个 doc skill、`lfg-profiles/doc.yaml`），无错误
- `harness init --type backend-service /tmp/code-test` 仍生成现有完整代码场景脚手架（多出 `lfg-profiles/code.yaml` 骨架文件），现有行为零退化
- 新增 12-18 条契约测试通过；现有 632 条测试不退化
- `harness lfg audit` ≥ 7.0（不退化）
- `make ci` 全绿
- `docs/product.md` / `docs/architecture.md` / `docs/runbook.md` 同步更新

## 2. 命令（Commands）

- 测试：`make test`
- 检查：`make check`
- CI：`make ci`
- 自检：`scripts/check_repo.py`
- skills lint：`PYTHONPATH=src .venv/bin/python -m agent_harness skills lint .`
- /lfg 体检：`PYTHONPATH=src .venv/bin/python -m agent_harness lfg audit`
- 端到端验证：`PYTHONPATH=src .venv/bin/python -m agent_harness init --type document /tmp/doc-scaffold-test --non-interactive`

## 3. 项目结构（Project Structure）

### 新增文件

| 路径 | 职责 |
|------|------|
| `src/agent_harness/templates/superpowers/.claude/commands/lfg-doc.md.tmpl` | `/lfg-doc` 命令模板，骨架对齐 `/lfg` 但调用 doc 版 skill；不调用 `/tdd` `/git-commit` `/finish-branch` `/multi-review` `/verify` `/debug` `/health` `/cso` |
| `src/agent_harness/templates/superpowers/.claude/commands/outline-doc.md.tmpl` | `/outline-doc` 命令模板：根据 spec 拟章节大纲、字数估算、引用占位 |
| `src/agent_harness/templates/superpowers/.claude/commands/draft-doc.md.tmpl` | `/draft-doc` 命令模板：基于 outline 写草稿；强调先 outline-pass 后 draft-pass 的两段法 |
| `src/agent_harness/templates/superpowers/.claude/commands/review-doc.md.tmpl` | `/review-doc` 命令模板：4 个评审角度（准确性 / 可读性 / 术语统一 / 完整性），多人格并行（与 `/multi-review` 同源思想，角度替换） |
| `src/agent_harness/templates/superpowers/.claude/commands/finalize-doc.md.tmpl` | `/finalize-doc` 命令模板：内嵌定稿前检查（无占位符 / R-ID 全覆盖 / 术语一致 / 拼写）+ 产出最终文件，**不**做 git commit / finish branch |
| `src/agent_harness/templates/common/.agent-harness/lfg-profiles/code.yaml.tmpl` | 描述现有 `/lfg` 流水线的 stage→skill 映射（**仅描述用**，本期无人读取） |
| `src/agent_harness/templates/common/.agent-harness/lfg-profiles/doc.yaml.tmpl` | 描述新建 `/lfg-doc` 流水线的 stage→skill 映射 |
| `src/agent_harness/templates/common/.agent-harness/lfg-profiles/README.md.tmpl` | 说明 lfg-profiles/ 目录的用途、schema、本期约束（暂不被读取）、未来 B 方案的接入位置 |
| `src/agent_harness/presets/document.json` | `document` 项目类型预设（行为变化判定 / 架构关注点 / 默认完成标准 / workflow_skills_summary） |
| `src/agent_harness/templates/document/.claude/rules/document-conventions.md.tmpl` | document 项目类型专属规则（基础格式约定、术语表位置、引用格式等通用文档约束） |
| `tests/test_doc_scenario_scaffold.py` | doc 场景脚手架的契约测试集 |
| `docs/superpowers/specs/2026-04-27-doc-scenario-skeleton-spec.md` | 本文件 |
| `docs/superpowers/specs/2026-04-27-doc-scenario-skeleton-plan.md` | 由 `/write-plan` 阶段产生 |

### 修改文件

| 路径 | 改动 |
|------|------|
| `src/agent_harness/skills_registry.json` | 注册 5 个新 skill：`lfg-doc` / `outline-doc` / `draft-doc` / `review-doc` / `finalize-doc`；分类 `delivery`；触发条件；`expected_in_lfg=false`（doc skill 走 `/lfg-doc` 不走 `/lfg`，避免覆盖检查误报） |
| `src/agent_harness/templates/common/docs/product.md.tmpl` | 项目类型清单加 `document`（如此模板存在） |
| `src/agent_harness/_shared.py` 或 `presets` 加载逻辑 | 注册 `document` 为 valid project type（如硬编码白名单存在） |
| `docs/product.md` | "支持的项目类型" 9 → 10；新增 `document` 段说明 |
| `docs/architecture.md` | 模块职责段加 `lfg-profiles/` 目录 + doc skill；测试层数字更新 |
| `docs/runbook.md` | `harness init --type document` 用法补一行 |
| `scripts/check_repo.py`（如需要） | 守卫新增 lfg-profiles 必有 README + schema_version 字段 |

### 不动的文件（已确认）

- 现有 `/lfg.md.tmpl` —— 行为零退化
- `/tdd.md.tmpl` / `/git-commit.md.tmpl` / `/finish-branch.md.tmpl` / `/multi-review.md.tmpl` —— 代码场景仍用
- `.claude/rules/*.md.tmpl` —— 下面那层不动
- `audit.py` / `memory.py` / `agent.py` / `squad/*` —— 下面那层不动

## 4. 代码风格（Code Style）

### profile yaml 模板（参考）

```yaml
# templates/common/.agent-harness/lfg-profiles/doc.yaml.tmpl
schema_version: 1
name: doc
description: 写文档（标书 / 规范 / 白皮书 / 报告等）的 /lfg-doc 流水线骨架描述

stages:
  - id: ideate
    skill: ideate
    description: 多角度构思文档结构、读者画像、关键论点
    optional: true

  - id: spec
    skill: spec
    description: 把文档需求转为可验收标准（含 R-ID）

  - id: outline
    skill: outline-doc
    description: 拟章节大纲、字数估算、引用占位

  - id: plan
    skill: write-plan
    description: 把 outline 拆为可执行写作步骤

  - id: draft
    skill: draft-doc
    description: 按 plan 写草稿（先 outline-pass 后 draft-pass）

  - id: review
    skill: review-doc
    description: 4 角度并行评审（准确性 / 可读性 / 术语统一 / 完整性）

  - id: finalize
    skill: finalize-doc
    description: 内嵌定稿前检查 + 产出最终文件

  - id: compound
    skill: compound
    description: 沉淀写作教训到 lessons.md
```

```yaml
# templates/common/.agent-harness/lfg-profiles/code.yaml.tmpl
schema_version: 1
name: code
description: 写代码的 /lfg 流水线骨架描述（与 /lfg 现有阶段对齐）

stages:
  - id: ideate
    skill: ideate
    optional: true
  - id: spec
    skill: spec
  - id: plan
    skill: write-plan
  - id: plan-check
    skill: plan-check
  - id: execute
    skill: tdd
  - id: verify
    skill: verify
  - id: review
    skill: multi-review
  - id: commit
    skill: git-commit
  - id: compound
    skill: compound
```

### 命令模板风格

`/lfg-doc.md.tmpl` 复用 `/lfg.md.tmpl` 的所有"反偷懒门禁"、"分层记忆加载"、"context budget"、"agent 设计"段落，**只**替换：

- 阶段名（execute → draft，verify → 内嵌于 finalize，等）
- 调用的 skill（`/tdd` → `/draft-doc`，`/multi-review` → `/review-doc`，`/git-commit` 删除）
- 验证产物（测试退出码 → 文档完整性检查）
- 验收语义（R-ID 测试映射 → R-ID 章节映射）

### 测试风格

```python
# tests/test_doc_scenario_scaffold.py
"""contract tests for doc scenario scaffold (D 方案)."""

def test_doc_skills_registered_in_registry():
    """lfg-doc / outline-doc / draft-doc / review-doc / finalize-doc 都在 skills-registry.json"""

def test_doc_skills_expected_in_lfg_false():
    """5 个 doc skill 的 expected_in_lfg=false（走 /lfg-doc 不走 /lfg）"""

def test_lfg_doc_does_not_call_code_skills():
    """`/lfg-doc.md.tmpl` 不出现 /tdd /git-commit /finish-branch /multi-review /verify /debug /health /cso"""

def test_lfg_unchanged():
    """现有 /lfg.md.tmpl 内容字节级相等于改动前 baseline（用 git show 取 HEAD 版本对比）"""

def test_document_project_type_preset_exists():
    """presets/document.json 存在且 schema 合法"""

def test_init_document_type_renders_doc_assets():
    """harness init --type document 在临时目录生成 /lfg-doc + 4 doc skill + lfg-profiles/{code,doc,README}"""

def test_init_other_types_still_render_lfg_profiles():
    """harness init --type backend-service 也生成 lfg-profiles/ 骨架（universally available）"""

def test_lfg_profiles_yaml_parseable():
    """code.yaml / doc.yaml 是合法 YAML 且含 schema_version / name / stages 字段"""

def test_no_superpowers_skips_doc_skills():
    """harness init --type document --no-superpowers 不渲染 /lfg-doc 等 superpowers skill"""

def test_doc_profile_stages_match_lfg_doc_command():
    """doc.yaml 列出的 stage→skill 映射与 /lfg-doc.md.tmpl 实际调用的 skill 集合一致"""

def test_code_profile_stages_match_lfg_command():
    """code.yaml 列出的 stage→skill 映射与 /lfg.md.tmpl 实际调用的 skill 集合一致"""

def test_lfg_audit_not_regressed():
    """harness lfg audit 总分 ≥ 7.0（基线快照对比）"""
```

## 5. 测试策略（Testing Strategy）

- 框架：`unittest`（本项目沿用）
- 位置：`tests/test_doc_scenario_scaffold.py`
- 覆盖：

  | 类别 | 测试数（预计） |
  |------|----------|
  | 正常路径（注册 / 渲染 / 类型预设） | 5-6 |
  | 边界（--no-superpowers / 升级路径不破坏现有） | 3-4 |
  | 错误（profile yaml 缺字段 / project type 未知） | 2-3 |
  | 一致性（profile yaml 与 lfg-doc 实际 skill 集合对齐） | 2 |
  | 行为零退化（lfg.md.tmpl baseline 对比 + lfg audit 不退化） | 2 |
  | **合计** | **14-17** |

  落入"新增 12-18 条契约测试"区间。

- 端到端：

  ```bash
  PYTHONPATH=src .venv/bin/python -m agent_harness init --type document /tmp/doc-scaffold-test --non-interactive
  # 验证：
  ls /tmp/doc-scaffold-test/.claude/commands/{lfg-doc,outline-doc,draft-doc,review-doc,finalize-doc}.md
  ls /tmp/doc-scaffold-test/.agent-harness/lfg-profiles/{code,doc,README}.{yaml,md}
  python -c "import yaml; yaml.safe_load(open('/tmp/doc-scaffold-test/.agent-harness/lfg-profiles/doc.yaml'))"
  ```

  ⚠️ 此处仅为人工 / 测试中 `subprocess` 调用，零依赖原则下生产代码不引入 PyYAML —— profile yaml 解析（如未来 B 阶段需要）届时再考虑用 stdlib 简易 YAML 或迁 JSON。本期 yaml 文件**仅供阅读**。

## 6. 边界（Boundaries）

| 类别 | 内容 |
|------|------|
| **始终做** | 写契约测试、对比 baseline 验证 `/lfg` 零退化、同步 docs/ 三件套、跑 `harness lfg audit` 验证不退化 |
| **先问再做** | 改 `/lfg.md.tmpl` 哪怕一行（即使是为了对齐 doc 流水线）、改下面那层规则（rules/）、改 audit/memory/squad 等运行时模块、引入新依赖（包括 PyYAML） |
| **绝不做** | 在本任务实现"AI 推断场景档案 + 用户确认"（B 方案职责）；在本任务实现标书业务内容；删除现有 `/tdd` `/git-commit` `/finish-branch` 等代码场景 skill；让 `/lfg-doc` 调用 `/git-commit` |

## 需求矩阵

| R-ID | 需求描述 | 验证方式 | 测试信号 |
|------|---------|---------|---------|
| R1 | `/lfg-doc` 命令模板存在于 `templates/superpowers/.claude/commands/` | 自动化测试 | `test_doc_skills_registered_in_registry` 注册检查 + 文件存在断言 |
| R2 | 4 个 doc 专用 skill (`/outline-doc` / `/draft-doc` / `/review-doc` / `/finalize-doc`) 模板存在 | 自动化测试 | `test_doc_skills_registered_in_registry` |
| R3 | 5 个新 skill 在 `skills-registry.json` 注册（含 id / category / triggers / expected_in_lfg=false） | 自动化测试 | `test_doc_skills_expected_in_lfg_false` |
| R4 | `/lfg-doc` 模板内**不**出现 `/tdd` `/git-commit` `/finish-branch` `/multi-review` `/verify` `/debug` `/health` `/cso` 这 8 个代码场景 skill 的调用 | 自动化测试 | `test_lfg_doc_does_not_call_code_skills`（grep 断言） |
| R5 | 现有 `/lfg.md.tmpl` 内容字节级零退化 | 自动化测试 | `test_lfg_unchanged`（与改动前 baseline / `git show HEAD~N` diff） |
| R6 | `lfg-profiles/code.yaml` + `lfg-profiles/doc.yaml` + `lfg-profiles/README.md` 三个骨架文件存在于 `templates/common/.agent-harness/lfg-profiles/` | 自动化测试 | `test_init_other_types_still_render_lfg_profiles` |
| R7 | profile yaml 是合法 YAML，含 `schema_version: 1`、`name`、`description`、`stages: [{id, skill, description, optional?}]` | 自动化测试 | `test_lfg_profiles_yaml_parseable`（标准库 + 简易解析或允许测试中临时使用 PyYAML） |
| R8 | `code.yaml` 列出的 stage→skill 映射与 `/lfg.md.tmpl` 实际调用 skill 集合一致 | 自动化测试 | `test_code_profile_stages_match_lfg_command`（双向 set 对比） |
| R9 | `doc.yaml` 列出的 stage→skill 映射与 `/lfg-doc.md.tmpl` 实际调用 skill 集合一致 | 自动化测试 | `test_doc_profile_stages_match_lfg_doc_command` |
| R10 | `presets/document.json` 存在并被项目类型白名单接受 | 自动化测试 | `test_document_project_type_preset_exists` |
| R11 | `harness init --type document /tmp/...` 端到端生成完整 doc 场景脚手架（5 个 skill + 3 个 lfg-profiles 文件） | 自动化测试 | `test_init_document_type_renders_doc_assets` |
| R12 | `harness init --type backend-service` 现有行为零退化 + 新增 lfg-profiles 骨架 | 自动化测试 | `test_init_other_types_still_render_lfg_profiles` |
| R13 | `--no-superpowers` 关闭时 `/lfg-doc` 等 5 个 doc skill 不渲染（与 `/lfg` 一致） | 自动化测试 | `test_no_superpowers_skips_doc_skills` |
| R14 | `harness lfg audit` 总分 ≥ 7.0（不退化） | 自动化测试 | `test_lfg_audit_not_regressed`（subprocess 调用 audit + 解析 JSON） |
| R15 | 现有 632 条测试全通过 | 自动化测试 | `make test` exit 0 |
| R16 | `docs/product.md` 项目类型清单更新（9 → 10），新增 `document` 段说明 | 手动 + 自动 | grep `document` in docs/product.md + 评审 |
| R17 | `docs/architecture.md` 模块职责段加 `lfg-profiles/` 与新 skill；测试数更新 | 手动 + 自动 | grep `lfg-profiles` in docs/architecture.md |
| R18 | `docs/runbook.md` 加 `harness init --type document` 命令示例 | 手动 + 自动 | grep `--type document` in docs/runbook.md |

## Out-of-Scope（明确不做）

- AI 推断场景档案 + 用户确认（属 B 方案，后续任务）
- profile yaml 被任何命令运行时读取（本期纯描述）
- discover_project() 自动检测 doc 项目（本期靠 `--type document` 显式指定）
- 标书业务内容（招标方资质规则、技术分项打分等，后续单独任务）
- `/verify-doc` 独立 skill（合并进 `/finalize-doc` 内嵌）
- `/debug` / `/health` / `/cso` / `/retro` / `/squad` 等的 doc 版（本期不需要，按需以后做）
- 文档拼写检查器 / 术语字典工具集成（属 `/finalize-doc` 内嵌的"建议命令"，不是脚手架强依赖）

## 需求评分

| 维度 | 得分 | 扣分理由 |
|------|-----|---------|
| 背景（Background）       | 19 / 20 | 业务动机（用户验证标书场景）+ 架构动机（多场景化验证）双轨清楚；扣 1 分因未引用具体已有 lessons / metrics 作为基线 |
| 价值衡量（Value）        | 17 / 20 | 成功定义有 5 项可量化（端到端命令成功 / 测试不退化 / lfg audit ≥ 7.0 / make ci 全绿 / 三份 docs 同步），扣 3 分因 doc 场景的"用户体验"侧无量化（合理：本期是脚手架不是内容，体验由后续标书任务度量） |
| 解决方案（Solution）     | 19 / 20 | D 方案路径清楚（先抄 + 留位置），与已有 superpowers/ + presets/ + skills-registry.json 架构兼容；扣 1 分因未给出"以后从 D 升 B 时改哪些代码"的迁移 sketch |
| 影响范围（Scope）        | 19 / 20 | 新增 13 个文件 + 修改 5 个文件 + 不动的关键文件全列；out-of-scope 明确 8 项；扣 1 分因 `_shared.py` / preset 加载逻辑改法待 plan 阶段 grep 确认 |
| 正文完整性（Content）    | 20 / 20 | 假设清单 6 条 + 6 个核心区域 + 18 条 R-ID 矩阵 + Out-of-scope + 评分卡，三件套齐全 |
| **合计**   | **94 / 100** | ✅ 通过门禁（≥ 80） |

---

## 5 个开放问题的回答

| 问题 | 回答 | R-ID |
|---|---|---|
| Q1: `/lfg-doc` 阶段顺序 | `ideate (opt) → spec → outline → plan → draft → review → finalize → compound`，与 `/lfg` 共享 ideate / spec / plan / compound 4 阶段；新增 outline / finalize 两阶段；execute 改名 draft；verify 内嵌 finalize；删除 commit 阶段 | R1, R9 |
| Q2: 新增哪些 doc skill | `/outline-doc` / `/draft-doc` / `/review-doc` / `/finalize-doc` 共 4 个（`/finalize-doc` 内嵌 verify+pre-publish 检查，省独立 `/verify-doc`） | R2 |
| Q3: 现有伪通用 skill 的去留 | **真通用复用**：`/ideate` `/brainstorm` `/spec` `/write-plan` `/plan-check` `/agent-design-check` `/compound` `/todo` `/careful` `/recall` `/source-verify` `/lint-lessons` `/digest-meeting` `/process-notes` / **代码绑死，doc 场景不调**：`/tdd` `/git-commit` `/finish-branch` `/multi-review` `/verify` `/debug` `/health` `/cso` `/squad` `/dispatch-agents` `/subagent-dev` `/retro` `/doc-release`（`/doc-release` 名字是 doc 但实际是发布说明，代码场景） | R4 |
| Q4: 是否新建 `document` 类型 | 是，新建 `presets/document.json`；**不**做 discover_project() 自动检测（保守，按需以后做） | R10 |
| Q5: profile yaml schema 最小可行字段 | `schema_version: 1` / `name` / `description` / `stages: [{id, skill, description, optional?}]`；本期不被运行时读取，纯描述 | R6, R7 |
