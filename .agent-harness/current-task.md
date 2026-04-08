# Current Task

## 状态：待验证

## LFG 进度

任务：Issue #6 — 进化集成 addyosmani/agent-skills（反合理化表 + spec-driven-development）
复杂度：中
通道：标准
基线 commit：a13b2a8
工作分支：master（直接工作）
Issue 来源：gh#6（evolution 标签）

### 验收标准
1. [x] `/tdd`、`/verify`、`/multi-review` 技能末尾新增反合理化表（各 6 条）
2. [x] 新建 `/spec` 技能模板，实现规格驱动开发流程
3. [x] `/lfg` 流水线在阶段 2 和阶段 3 之间插入规格定义步骤（阶段 2.5）
4. [x] `superpowers-workflow.md.tmpl` 技能列表包含 `/spec`
5. [x] 测试通过（82/82，含新技能的存在性 + 占位符 + 决策树完整性测试）
6. [x] 文档数字同步（技能数 27 → 28，12+ 处全部更新）
7. [x] `make dogfood && make ci` 通过

### 质量基线
- 测试：82 个，100% 通过
- 检查：passed

### 阶段进度
- [x] 理解与评估 — 复杂度：中，通道：标准
- [x] 环境准备 — 82 测试通过，repo check passed
- [x] 计划 — 12 个文件，7 条验收标准
- [x] 实施 — 4 步全部完成
- [x] 自检 — 验收标准 7/7 通过
- [x] 质量对比 — 测试 82→82，技能 27→28
- [ ] 收尾 — 待用户验证后提交

## 已做的改动

### 新增文件
- `src/agent_harness/templates/superpowers/.claude/commands/spec.md.tmpl` — 规格驱动开发技能

### 修改的模板文件（反合理化表）
- `tdd.md.tmpl` — 6 条反合理化表
- `verify.md.tmpl` — 6 条反合理化表
- `multi-review.md.tmpl` — 6 条反合理化表

### 修改的集成文件
- `superpowers-workflow.md.tmpl` — 技能表 + 推荐流程 + 决策指南
- `use-superpowers.md.tmpl` — 决策树 + 流程技能列表
- `lfg.md.tmpl` — 阶段 2.5 + 进度追踪 + 确认点汇总
- `evolve.md.tmpl` — 对比表加 /spec + 数字 27→28

### 修改的测试
- `tests/test_superpowers.py` — _EXPECTED_COMMANDS 加 spec.md

### 修改的文档（27→28 同步）
- CHANGELOG.md, README.md, docs/product.md, docs/architecture.md, docs/usage-guide.md, .agent-harness/project.json

### dogfood 同步
- `.claude/commands/spec.md` (新增)
- 7 个已有文件更新
