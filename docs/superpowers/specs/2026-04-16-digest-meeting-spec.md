# /digest-meeting 技能 — Spec

**日期**：2026-04-16
**来源**：用户设计对话（需求讨论→任务输入的源头缺口）
**定位**：common 层新增技能，与 `/process-notes` 并列，补齐"多人讨论原始记录→结构化产物"的翻译环节

## 目标

新增 `/digest-meeting` 通用命令技能，把多人讨论的原始语音转文字记录（以飞书妙记为主，兼容纯文本/带说话人/带时间戳四种格式）转化为框架可消费的结构化产物：

- **init 模式**（项目文档为占位符）：产出结构化笔记到 `notes/digested/`，串 `/process-notes` 填充 `docs/product.md` 等
- **iterate 模式**（项目文档已填充）：产出 `current-task.md`，由用户手动触发 `/lfg` 开始开发
- **meta 项目**：自动提示委托给 `/meta-create-task`（不自行处理）

## 与现有技能的关系

| 现有能力 | 职责 | 与 /digest-meeting 边界 |
|---|---|---|
| `/process-notes` | 处理**单人已整理**的 `notes/` markdown/txt | 只在开头加引导，职责不变 |
| `/meta-create-task` | meta 项目：会议纪要→跨服务任务 YAML | `/digest-meeting` 检测 meta 项目时委托给它 |
| `/spec` | 把需求转为可测试验收标准 | `/digest-meeting` **不直接调用**，由 `/lfg` 阶段 2.5 决定 |
| `/lfg` | 单任务全流水线 | iterate 模式的下游执行者 |

## 需求

### R1 — 新命令模板文件
新建 `src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl`，包含：
- 7 步执行指令（读取 → 模式检测 → 提取 6 类信号 → meta 检测 → 展示摘要 → 写入 → 标记已处理）
- 格式兼容策略（4 种格式启发式检测）
- 6 类信号提取定义（决策/需求/约束/待办/开放问题/参与者）
- 两种模式的产出差异说明
- 占位符：`{{project_name}}`、`{{project_type}}`、`{{check_command}}`

### R2 — skills-registry 注册
在 `src/agent_harness/templates/superpowers/skills-registry.json` 添加条目：
```json
{
  "id": "digest-meeting",
  "name": "需求讨论摘要",
  "category": "process",
  "one_line": "把多人讨论的原始语音转文字记录转为结构化产物",
  "triggers": ["讨论记录转任务", "会议纪要处理", "语音转文字后续处理"],
  "decision_tree_label": null,
  "lfg_stage": [],
  "expected_in_lfg": false
}
```
`expected_in_lfg=false` 理由：`/digest-meeting` 是 `/lfg` 的**前置源头**（生产 current-task.md），不是 `/lfg` 流水线阶段。

### R3 — superpowers-workflow 规则更新
更新 `src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md`：
- "所有可用技能"表增加 `/digest-meeting` 行
- "何时使用哪个技能"段增加"收到原始讨论记录→/digest-meeting"

### R4 — /process-notes 加引导
在 `src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl` 开头"背景"段加一段：
> 如果 `notes/` 下是**多人讨论的原始语音转文字记录**（对话、分歧、决策过程），建议先用 `/digest-meeting` 做结构化摘要，再用本命令。

### R5 — /lfg 阶段 0.1 接合
更新 `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` 阶段 0.1：在"普通文本描述"处理之前加一条：
> **如果用户输入指向 `notes/` 下的原始讨论记录文件**（路径包含 `.md` 或 `.txt`，且在 `notes/` 下但不在 `notes/digested/` 下）→ 建议先跑 `/digest-meeting`，然后再来 `/lfg`

### R6 — docs/product.md 同步
更新 `docs/product.md`：
- "框架提供什么"段，把 common 命令数量从 3 个更新为 4 个
- 说明新增 `/digest-meeting` 的定位

### R7 — docs/architecture.md 同步
更新 `docs/architecture.md` 模板结构段落（或资源层 common 模板说明）：提及 `.claude/commands/digest-meeting.md.tmpl`。

### R8 — 新增测试 test_digest_meeting.py
在 `tests/test_digest_meeting.py` 覆盖：
- 命令模板文件存在且可读
- 模板中包含所需 7 步执行指令的关键词
- `harness init` 后目标项目有 `.claude/commands/digest-meeting.md`
- 占位符 `{{project_name}}` 等已被替换
- skills-registry.json 包含 `digest-meeting` 条目且字段齐全
- `harness skills lint` 不报 orphan 或 missing

### R9 — 既有测试更新
识别并更新：
- 若存在类似"common 命令总数"的契约测试（如 `test_common_commands.py` 或 `test_initializer.py` 中的常量），数字从 3 → 4
- `test_skills_registry.py`（如存在 skill 计数契约）

### R10 — dogfood 同步 + CI 通过
- `make dogfood` 后本仓库 `.claude/commands/digest-meeting.md` 正确生成
- `make ci` 全部通过

### R11 — WAL 审计
每次修改 `current-task.md` / `lessons.md` / `task-log.md` 都追加 audit（task-lifecycle 硬要求）。

## 验收标准

对应上述 R1-R11，每条都要在最终 `/verify` 环节证明 satisfied / out-of-scope / missed：

| R-ID | 验收方式 |
|---|---|
| R1 | `ls src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl` 存在 |
| R2 | `python -c "import json; assert 'digest-meeting' in {s['id'] for s in json.load(open('src/agent_harness/templates/superpowers/skills-registry.json'))['skills']}"` |
| R3 | `grep digest-meeting src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md` 命中 |
| R4 | `grep "/digest-meeting" src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl` 命中 |
| R5 | `grep "/digest-meeting" src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` 命中 |
| R6 | `docs/product.md` 中有 `/digest-meeting` 提及 |
| R7 | `docs/architecture.md` 中有 `digest-meeting` 提及 |
| R8 | `pytest tests/test_digest_meeting.py -v` 全绿 |
| R9 | `make test` 487 → 新基线，无已有测试回归 |
| R10 | `make ci` 通过 + `ls .claude/commands/digest-meeting.md` 存在 |
| R11 | `.agent-harness/bin/audit tail` 能看到关键变更记录 |

## 不做

- **不实现语音转文字**：输入必须是已经转好的文本文件
- **不改 `/process-notes` 的核心逻辑**：只加一条引导句
- **不实现 IDE 集成 / 会议中实时记录**：超出脚手架框架范围
- **不硬编码格式解析**：用启发式判定而非严格 parser，容忍混合/未知格式
- **不在 `/digest-meeting` 中调用 `/spec`**：职责边界——只产出 current-task.md，让 `/lfg` 自决
- **不自动调用 `/lfg`**：iterate 模式写完 current-task 后提示用户手动跑 `/lfg`
- **不引入新 Python 依赖**：纯文本处理在 AI 理解层完成（AI 读模板指令直接执行），不写 Python parser

## 边界与风险

- **风险 1**：格式启发式判定可能误判 → 缓解：模板要求"不确定就展示解析结果让用户校对"
- **风险 2**：iterate 判定依赖"占位符"概念 → 缓解：用"功能列表段是否有非 checkbox 非占位符实质内容"作为判定
- **风险 3**：讨论记录中决策提炼有主观性 → 缓解：所有提取项标注来源（原话引用 vs AI 综合推断）
