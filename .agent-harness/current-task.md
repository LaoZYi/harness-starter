# Current Task

## LFG 进度

### Goal（目标）
吸收 Imprint 的 Conflict Resolution 5 型分类（T3/T4/T5 接入 lessons 域），为 `/lint-lessons` 增加解决路径维度的分型输出，为 `/compound` 增加冲突预检步骤，用新元规则 `.claude/rules/knowledge-conflict-resolution.md` 统一表述。对应 GitHub #43 / GitLab #22。

### Context（上下文）
复杂度：中 | 通道：简化完整（evolution 模式跳过 /ideate + /brainstorm）| 基线 commit：0338b84 | 工作分支：feat/lessons-conflict-resolution-20260420

### Assumptions（假设清单）
- 假设：规则命名 `knowledge-conflict-resolution.md` | 依据：未来可扩展到 rules 间冲突，Imprint 原设计针对广义知识条目
- 假设：本次不引入 `confidence` 字段 | 依据：Issue body 明确 confidence + decay 作为 icebox 独立评估
- 假设：只接入 T3 / T4 / T5 到 lessons 域；T1 / T2 在规则文件中保留为参考 | 依据：T1 是 AI 行为准则不是 lessons 问题；T2 是规则层冲突不在本次范围
- 假设：`/compound` 的冲突预检是「警告 + 人工裁决」不 block | 依据：与现有"重叠度判断"一致，不引入强制 checkpoint
- 假设：测试只覆盖规则文件结构 + `/lint-lessons` 分型输出字符串；`/compound` 交互式命令不做端到端单测 | 依据：skill 是 markdown 模板

### Acceptance（验收标准）
- R-001 `.claude/rules/knowledge-conflict-resolution.md` 存在，文案化 5 型（T1-T5，每型含场景 + 处理路径 + 在本项目中的适用性）
- R-002 `/lint-lessons` 步骤 2.2 每对冲突输出包含 resolution-type（T3/T4/T5 之一或 N/A）+ 建议动作
- R-003 `/compound` 步骤 3 扩展：查重命中「非重复而是矛盾」→ 分型 T3/T4/T5 + 预检提示
- R-004 `templates/common/.claude/rules/` 和 `templates/superpowers/.claude/commands/` 同步；`make dogfood` 无漂移
- R-005 新测试覆盖 T3 / T4 / T5 各至少 1 条 + 规则文件结构契约
- R-006 `CHANGELOG.md` 和 `docs/architecture.md` 测试计数 + 描述同步
- R-007 新增 ADR `docs/decisions/0002-knowledge-conflict-resolution.md`（Proposed → Accepted）

### Quality Baseline（质量基线）
- 测试：529 个，100% 通过
- make test：12.8s
- make check / lint / typecheck：全绿

## 状态：等待用户确认进入实施阶段

spec + plan 已完成，展示给用户后等回复「开始」或调整。用户确认后 checkbox 会逐步勾选。这是 /lfg 阶段 3.3 规定的确认点，不是任务结束。

### Progress（阶段进度）
- [x] 理解与评估 — 复杂度：中，通道：简化完整
- [x] 环境准备 — 分支 feat/lessons-conflict-resolution-20260420，基线测试 529/529
- [x] 规格定义 — docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-spec.md
- [x] 计划 — docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-plan.md
- [x] ADR — docs/decisions/0002-knowledge-conflict-resolution.md（Accepted）
- [x] 实施 — 规则 + 2 个 skill 模板 + 14 条契约测试 + 5 个文档计数同步
- [x] 自检 + 验证 — R-ID 7/7 satisfied；make ci 543/543 pass；make check/lint/typecheck 全绿
- [ ] 提交
- [ ] 待用户确认

## 状态：待验证
