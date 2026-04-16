# /digest-meeting 技能 — Plan

**基于**：`docs/superpowers/specs/2026-04-16-digest-meeting-spec.md`
**分支**：`feat/digest-meeting`
**基线**：master c7679f3 / 487 测试全绿 / check 通过

## 执行顺序（11 步，依赖排序）

每步≈2-5 分钟粒度，均带验证命令。

---

### 步骤 1 — 写新测试 `tests/test_digest_meeting.py`（RED 先行）

**R-ID**：R8
**文件**：`tests/test_digest_meeting.py`（新建）

**包含 6 个测试类（covers 7 cases）**：

```python
class DigestMeetingTemplateTests(unittest.TestCase):
    def test_template_file_exists(self):
        # tmpl 文件存在
    def test_template_contains_seven_steps(self):
        # 模板中包含 7 步指令关键词：读取 / 模式检测 / 提取 / meta 检测 / 展示 / 写入 / 标记
    def test_template_declares_six_signal_types(self):
        # 6 类信号：决策 / 需求 / 约束 / 待办 / 开放问题 / 参与者
    def test_template_declares_format_compat(self):
        # 4 种格式：飞书 / 说话人 / 时间戳 / 纯文本
    def test_template_has_placeholders(self):
        # {{project_name}}、{{project_type}}、{{check_command}} 都存在

class DigestMeetingInitTests(unittest.TestCase):
    def test_init_generates_digest_meeting_command(self):
        # harness init 后 .claude/commands/digest-meeting.md 存在且占位符已替换

class DigestMeetingRegistryTests(unittest.TestCase):
    def test_registry_contains_entry(self):
        # skills-registry.json 有 digest-meeting 条目
    def test_registry_entry_is_meta_category_excluded_from_lfg(self):
        # category=meta, expected_in_lfg=false, 有 exclusion_reason
```

**验证**：`pytest tests/test_digest_meeting.py -v` → **全部失败**（红灯确认测试真有效）

---

### 步骤 2 — 创建命令模板 `digest-meeting.md.tmpl`

**R-ID**：R1
**文件**：`src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl`（新建）

**结构**（7 个顶级段落）：

```
# 处理需求讨论记录

## 背景 / 定位
  - 说明差异：与 /process-notes 的分工
  - 适用场景：idea 讨论 / 迭代评审

## 输入格式兼容（4 种启发式检测）
  - 纯文本 / 带说话人 / 带时间戳 / 飞书妙记
  - 原则：宽进严出，不确定就展示解析结果让用户校对

## 第 1 步：读取 notes/ 下的原始讨论记录
  - 扫描 .md/.txt，跳过 notes/digested/ 和已标记 <!-- processed --> 的文件
  - 空目录 → 报错退出

## 第 2 步：检测模式（init / iterate）
  - 读 docs/product.md，看"功能列表"段是否有实质内容（非 checkbox 占位 / 非待补充）
  - 空 → init 模式；有 → iterate 模式

## 第 3 步：提取 6 类信号
  | 决策 | 需求 | 约束 | 待办 | 开放问题 | 参与者 |
  - 每项标注来源：讨论第 N 段原话 / AI 综合推断
  - 合并同类项 / 忽略噪音 / 存疑标注

## 第 4 步：meta 项目检测
  - 检查 services/registry.yaml 存在 → 自动提示委托 /meta-create-task

## 第 5 步：展示摘要（🔴 用户确认）
  - 结构化展示 6 类信号，询问用户是否写入

## 第 6 步：写入（按模式分叉）
  - init：写 notes/digested/meeting-YYYY-MM-DD.md（process-notes 兼容格式）→ 提示用户跑 /process-notes
  - iterate：写 current-task.md（任务目标 + 假设 + 验收标准）→ 提示用户跑 /lfg
  - 架构决策类：建议先跑 /adr

## 第 7 步：标记已处理
  - 原始文件头部插 <!-- processed: YYYY-MM-DD -->

## 注意事项
  - 原始文件永不动（只加 processed 标记）
  - 运行 {{check_command}} 验证项目状态
```

**占位符**：`{{project_name}}`、`{{project_type}}`、`{{check_command}}`

**验证**：
- `cat src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl | wc -l` → 大致 100-180 行
- `pytest tests/test_digest_meeting.py::DigestMeetingTemplateTests -v` → 5/5 PASS

---

### 步骤 3 — 更新 `skills-registry.json`

**R-ID**：R2
**文件**：`src/agent_harness/templates/superpowers/skills-registry.json`

在文件末尾 `process-notes` 条目**之后**（保持末尾是"meta"归类的 skill）插入：

```json
    ,{
      "id": "digest-meeting",
      "name": "需求讨论摘要",
      "category": "meta",
      "one_line": "把多人讨论的原始语音转文字记录转为结构化产物",
      "triggers": ["讨论记录转任务", "会议纪要处理", "语音转文字后续处理"],
      "decision_tree_label": null,
      "lfg_stage": [],
      "expected_in_lfg": false,
      "exclusion_reason": "meeting-transcript processing, upstream of /lfg (produces current-task.md as input, not a pipeline stage)"
    }
```

> 注意：category=meta（对标 process-notes），不是 process。

**验证**：
- `python -c "import json; d=json.load(open('src/agent_harness/templates/superpowers/skills-registry.json')); assert 'digest-meeting' in {s['id'] for s in d['skills']}"` → 无输出（成功）
- `.venv/bin/python -m agent_harness.cli skills lint .` → OK
- `pytest tests/test_digest_meeting.py::DigestMeetingRegistryTests -v` → 2/2 PASS

---

### 步骤 4 — 更新 `superpowers-workflow.md.tmpl`（技能清单 + 使用场景）

**R-ID**：R3
**文件**：`src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md.tmpl`

修改两处（用 Edit 工具精确插入）：

1. "所有可用技能"表格中找合适位置插入：
   ```
   | `/digest-meeting` | 把多人讨论的原始语音转文字记录转为结构化产物（/lfg 前置源头） |
   ```

2. "何时使用哪个技能"列表插入：
   ```
   - 收到多人讨论的原始语音转文字记录 → `/digest-meeting`
   ```

**验证**：`grep digest-meeting src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md.tmpl` → 2 命中

---

### 步骤 5 — 更新 `/lfg` 阶段 0.1（notes/ 原始文件输入检测）

**R-ID**：R5
**文件**：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`

在阶段 0.1 "**如果输入是普通文本描述**" 段之前，插入一个新分支：

```markdown
**如果输入是文件路径且指向 `notes/` 下的原始讨论记录**（路径以 `notes/` 开头，以 `.md` 或 `.txt` 结尾，且不在 `notes/digested/` 下）：

→ **🔴 停下来提示用户**：这看起来是未处理的原始讨论记录。建议先跑 `/digest-meeting <文件路径>` 做结构化摘要，它会根据项目状态自动产出 `notes/digested/` 下的笔记（init 模式）或 `current-task.md`（iterate 模式），然后再来 `/lfg`。
```

**验证**：`grep -c "digest-meeting" src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` → ≥1

---

### 步骤 6 — 更新 `/process-notes` 加引导

**R-ID**：R4
**文件**：`src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl`

在"背景"段末尾加一段 callout：

```markdown
> **注意**：如果 `notes/` 下是**多人讨论的原始语音转文字记录**（有对话、分歧、决策过程），建议先用 `/digest-meeting` 做结构化摘要，产出 `notes/digested/` 下的结构化笔记，再用本命令。本命令处理**单人已整理**的笔记，对多人原始讨论记录的噪音过滤能力不足。
```

**验证**：`grep "/digest-meeting" src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl` → 1 命中

---

### 步骤 7 — 更新 `docs/product.md`

**R-ID**：R6
**文件**：`docs/product.md`

修改两处：

1. 第 10 行"工作流技能"描述，把"3 个 common 层命令（`/process-notes`、`/recall`、`/source-verify`）"改为"4 个 common 层命令（`/process-notes`、`/digest-meeting`、`/recall`、`/source-verify`）"
2. 在"框架提供什么"段添加一项说明 `/digest-meeting` 的价值定位（"研发源头入口：讨论记录→结构化产物"）

**验证**：`grep "/digest-meeting" docs/product.md` → ≥2 命中

---

### 步骤 8 — 更新 `docs/architecture.md`

**R-ID**：R7
**文件**：`docs/architecture.md`

修改第 40 行资源层 common 模板段：把"3 个 common 命令（`/process-notes`、`/recall`、`/source-verify`）"改为"4 个 common 命令（`/process-notes`、`/digest-meeting`、`/recall`、`/source-verify`）"。

**验证**：`grep "/digest-meeting" docs/architecture.md` → ≥1 命中

---

### 步骤 9 — 更新 `AGENTS.md`（common 命令计数同步）

**R-ID**：R6 的配套
**文件**：`AGENTS.md`

第 76 行 "3 个 common 命令" → "4 个 common 命令"（列表描述也补充 digest-meeting）。

**验证**：`grep "/digest-meeting\|4 个 common" AGENTS.md` → ≥1 命中

---

### 步骤 10 — make dogfood 同步

**验证**：
```bash
make dogfood
ls .claude/commands/digest-meeting.md  # 应存在
grep -c "{{" .claude/commands/digest-meeting.md  # 应为 0（占位符都已替换）
```

---

### 步骤 11 — make ci 全量验证 + WAL 审计

**验证**：
```bash
make ci   # 全绿
.agent-harness/bin/audit tail --limit 10  # 看到本次关键变更记录
```

每个破坏性修改前记得：`.agent-harness/bin/audit append --file current-task.md --op update --summary "plan step N 完成"`

---

## 文件作用域（原子性：每步只改列表里的文件）

| 步骤 | 文件 | 行为 |
|---|---|---|
| 1 | `tests/test_digest_meeting.py` | 新建 |
| 2 | `src/.../common/.claude/commands/digest-meeting.md.tmpl` | 新建 |
| 3 | `src/.../superpowers/skills-registry.json` | 追加条目 |
| 4 | `src/.../common/.claude/rules/superpowers-workflow.md.tmpl` | 两处插入 |
| 5 | `src/.../superpowers/.claude/commands/lfg.md.tmpl` | 阶段 0.1 插入 |
| 6 | `src/.../common/.claude/commands/process-notes.md.tmpl` | 背景段补充 |
| 7 | `docs/product.md` | 两处更新 |
| 8 | `docs/architecture.md` | 一处更新 |
| 9 | `AGENTS.md` | 一处更新 |
| 10 | 多文件（dogfood 触发） | `.claude/commands/` 下同步 |
| 11 | — | 只做验证，不改代码 |

## R-ID 覆盖矩阵

| R-ID | 步骤 | 状态 |
|---|---|---|
| R1 | 步骤 2 | → satisfied |
| R2 | 步骤 3 | → satisfied |
| R3 | 步骤 4 | → satisfied |
| R4 | 步骤 6 | → satisfied |
| R5 | 步骤 5 | → satisfied |
| R6 | 步骤 7 + 步骤 9 | → satisfied |
| R7 | 步骤 8 | → satisfied |
| R8 | 步骤 1 | → satisfied |
| R9 | — | → **out-of-scope**（调研确认 `test_lfg_coverage.py` 用 glob 扫描，不硬编码 common 数；无需更新现有测试契约） |
| R10 | 步骤 10 + 步骤 11 | → satisfied |
| R11 | 每步提交前后 | → satisfied（贯穿） |

> **R9 降级说明**：原 spec 假设有"common 命令计数契约测试"需要更新，调研后确认没有（`test_lfg_coverage.py` 用 `glob("*.md.tmpl")` 动态扫描，`test_superpowers.py` 只测具体 skill 不数总数）。唯一硬编码"3 个"的是文档（product.md / architecture.md / AGENTS.md），已在步骤 7-9 覆盖。

## 历史教训引用

- **"抽 SSOT 时必须清单化所有下游消费方"**（memory-index 2026-04-13 架构设计）
  → 本计划显式列出 skills-registry.json 的下游：步骤 5（lfg.md.tmpl 的 `<<SKILL_COVERAGE_TABLE>>` 自动渲染不需手改）、步骤 4（workflow 规则手改）、步骤 1（测试契约）。没有遗漏。

- **"占位符层次必须显式区分"**（memory-index 2026-04-13 模板）
  → common 层模板只用 `{{var}}` 不用 `<<SKILL_*>>`，步骤 2 的新模板恪守此规。

## 回滚点

每步完成后打 `lfg/step-N` tag，便于精确回滚。

## 边界情况清单（实施中遇到就按此处理）

- 步骤 3 插入 JSON 时语法错（尾逗号等）→ `python -c "import json; json.load(open(...))"` 校验，坏了回退 tag
- 步骤 5 插入 lfg.md.tmpl 位置选错 → 用 grep 定位"如果输入是普通文本描述"前一行做锚点
- 步骤 10 dogfood 失败 → 看报错，大概率是 registry.json 格式坏（回溯步骤 3）
- 步骤 11 CI 失败且不是本次相关 → 停下来告知用户，不盲目修
