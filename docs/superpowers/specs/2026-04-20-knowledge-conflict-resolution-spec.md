# 知识冲突解析（Knowledge Conflict Resolution）规格

吸收 [ilang-ai/Imprint](https://github.com/ilang-ai/Imprint) v2.1 的 Conflict Resolution 5 型分类，为本项目的 lessons 维护流程增加「解决路径维度」的分型输出。对应 GitHub #43 / GitLab #22。

## 假设清单

- 假设：新规则命名 `knowledge-conflict-resolution.md` 而非 `lessons-conflict.md`——未来可扩展到 rules 间冲突
- 假设：本次不引入 Imprint 的 `confidence` 字段（confirmed / tentative）——单独 Issue 评估
- 假设：5 型中只有 T3 / T4 / T5 适合接入 lessons 域；T1 / T2 在规则文件中保留为参考
- 假设：`/compound` 的冲突预检不 block，发现后提示人工裁决
- 假设：测试覆盖只涉及规则文件结构契约 + `/lint-lessons` 模板分型字段；`/compound` 是交互式 markdown skill，不做端到端单测

## 目标

### 要构建什么

在本项目的 lessons 维护链路上新增一层「解决路径维度」的分型机制：

1. 新规则文件 `.claude/rules/knowledge-conflict-resolution.md`：文案化 Imprint 5 型（T1-T5），明确各型在本项目中的适用性和处理路径
2. `/lint-lessons` 冲突检测输出中为每对冲突标注 resolution-type + 建议动作（聚焦 T3/T4/T5）
3. `/compound` 写入新 lesson 前做冲突预检，命中矛盾时按型分类并提示人工裁决

### 为什么要构建

当前 `/lint-lessons` 的冲突检测仅分症状类型（规则反向 / 根因冲突 / 预防冲突 / 适用边界 / 优先级），输出结论是描述性的，用户仍需自己判断「该怎么办」。引入 Imprint 的 5 型是把**解决路径**也结构化——从"看见冲突"升级到"看见冲突 + 知道该走哪条路径"。

`/compound` 当前只做重叠度判断（高/中/低），**不区分"重复"和"矛盾"**。两条说法相反的 lesson 会各自写入，下次 /lint-lessons 才被动发现。冲突预检把问题挡在写入前。

### 目标用户

- 本项目维护者（主要）
- 通过模板接入 harness 的其他项目（次要——规则文件会被模板化）
- AI agent（消费者）：lessons.md 和规则文件都是它的上下文

### 成功标准

- `/lint-lessons` 在一条「T3 两条 confirmed 相反」的测试 fixture 上输出包含 `Type-3` 或 `resolution:conditional-branch` 的建议
- `/compound` 在预检测试 fixture 上给出「这是矛盾不是重复」的分型提示
- 新增规则通过 `make dogfood` 同步到项目自身 `.claude/rules/` 无漂移
- 529 + N 个测试全绿

## 命令

- 测试命令：`make test`
- 代码检查命令：`make check`（含 check_repo + lint + typecheck + skills-lint + dogfood）
- 启动命令：`harness`

## 项目结构

### 新增文件

| 路径 | 职责 |
|---|---|
| `templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl` | 新元规则模板，文案化 5 型 |
| `.claude/rules/knowledge-conflict-resolution.md` | dogfood 同步产物（由 `make dogfood` 生成） |
| `docs/decisions/0002-knowledge-conflict-resolution.md` | ADR，记录"为什么要新增这层规则"及取舍 |
| `docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-spec.md` | 本文档 |
| `docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-plan.md` | /write-plan 产出 |
| `tests/test_lessons_conflict_resolution.py` | 规则 + `/lint-lessons` 分型输出回归 |

### 修改文件

| 路径 | 改什么 |
|---|---|
| `templates/superpowers/.claude/commands/lint-lessons.md.tmpl` | 步骤 2.2 每对冲突输出增加 resolution-type 字段；新增一段「5 型速查」引用新规则 |
| `templates/superpowers/.claude/commands/compound.md.tmpl` | 步骤 3 增加「3.5 冲突预检」：区分"重复"与"矛盾"，后者按 T3/T4/T5 分型提示 |
| `.claude/commands/lint-lessons.md` + `.claude/commands/compound.md` | dogfood 同步产物 |
| `CHANGELOG.md` | [Unreleased] 追加条目 |
| `docs/architecture.md` | 测试计数 + 描述同步 |

## 代码风格

### Markdown 规则模板风格

现有 `templates/common/.claude/rules/*.md.tmpl` 的标准：

- 以一级标题 + 一句话目的开头
- 分节：适用场景 → 规则条目 → 反例 → 与其他规则的关系
- 规则条目用表格或编号列表，避免散文
- 中文引号用直角引号 `「」`
- 中英文数字之间空格（如 `HTTP 请求`、`版本 2.0`）

参考：`templates/common/.claude/rules/anti-laziness.md.tmpl`、`task-lifecycle.md.tmpl`

### 测试代码风格

现有 `tests/test_*.py` 约定：

- `from __future__ import annotations` 顶部
- 模块顶部 docstring 说明覆盖的契约
- 每个 `TestCase` 聚焦一个功能点，方法名体现断言语义
- 用临时目录隔离副作用；需要模板渲染时走真实的 `initializer.py` 或直接读 `.md.tmpl` 原文断言字段存在

参考：`tests/test_git_env_isolation.py`（刚加的）、`tests/test_memory_search.py`

## 测试策略

### 框架
- Python `unittest`（纯 stdlib，项目约定）
- Fixtures 用临时目录 + 手写 markdown

### 必测场景

| R-ID | 场景 | 类型 |
|---|---|---|
| R-001 | `knowledge-conflict-resolution.md.tmpl` 存在且含 T1-T5 关键锚点（如 `## T1`、`## T3`、`## T5`） | 正常路径 |
| R-001 | 规则文件结构完整（目的 → 5 型 → 本项目适用性 → 与 /lint-lessons 和 /compound 的关系） | 边界 |
| R-002 | `lint-lessons.md.tmpl` 含「resolution-type」关键词和 T3/T4/T5 建议动作示例 | 正常路径 |
| R-003 | `compound.md.tmpl` 步骤 3.5 存在且含「矛盾」「分型」「T3」等关键词 | 正常路径 |
| R-004 | dogfood 产物（`.claude/rules/knowledge-conflict-resolution.md` 等）和模板一致 | 回归 |
| R-005 | T3（两 confirmed 矛盾）示例在规则文件中的处理路径为「转条件分支 + 记录 mismatch」 | 正常路径 |
| R-005 | T4（多 agent 不一致）处理路径为「两条都降级 tentative + 等用户确认」 | 正常路径 |
| R-005 | T5（lesson vs 当前任务）处理路径为「lesson 是警告不是阻断」 | 边界 |
| R-001 | 规则文件明确声明 T1 / T2 **在本项目 lessons 域不直接适用**（避免误用） | 错误路径 |

### 不测

- `/compound` 的交互对话（markdown skill 无法端到端单测）
- `/lint-lessons` 真实对用户 lessons.md 的扫描（Issue 明确本次不改 lint 引擎，只改输出文案契约）

## 边界

### 始终做

- 规则改动 → template 改动 → dogfood 产物改动 → 测试同步（四处必须原子 commit）
- 新规则的结构必须被测试锁定（防后续漂移）
- ADR 起"Proposed"，合并前升到"Accepted"

### 绝不做

- **不**引入 `confidence` 字段到 lessons.md 条目——独立 Issue 评估
- **不**引入 `.dna.md` DSL 格式
- **不**改 `/lint-lessons` 的冲突检测引擎（它是 markdown skill + AI 推理，没"引擎"可改）——只改输出文案和字段
- **不**让 `/compound` 冲突预检变成 blocking check——始终是"提示 + 人工裁决"
- **不**把 T1（用户本轮 vs 历史 gene）放进 lessons 域的处理——它属于 AI 行为准则，与 lessons 无关
- **不**把 T2（全局 vs 项目）放进 lessons 域——它属于 `.claude/rules/` 与 `.harness-plugins/rules/` 之间的层级问题

### 不决定（留给实施阶段）

- 规则文件内部排版细节（5 型各用多少段，是否加示例）——按最清晰易扫读为准
- `/lint-lessons` 的 resolution-type 字段具体格式（`Type-N` / `T-N` / `resolution:xxx`）——/write-plan 时定

## 与现有规则的关系

- **与 `.claude/rules/task-lifecycle.md` 的关系**：task-lifecycle 是任务生命周期的时序约束，知识冲突解析是知识库一致性的结构约束，正交不冲突
- **与 `.claude/rules/anti-laziness.md` 的关系**：anti-laziness 门禁 1（数量门禁）要求每项检查有明确状态——`/lint-lessons` 和 `/compound` 新增的分型输出是"每个冲突必须标 resolution-type"的具体落地，复用门禁 1 的契约精神
- **与 `docs/decisions/0001-layered-memory-loading.md` 的关系**：分层记忆加载把知识分层存储，知识冲突解析补齐「层内冲突如何处理」

## 非目标

- 不设计自动化冲突裁决机制（AI 自己决定）——始终人工确认
- 不修改 `lessons.md` 现有条目格式
- 不影响 `memory-index.md` 重建逻辑
- 不改 `.agent-harness/bin/memory` 工具链
