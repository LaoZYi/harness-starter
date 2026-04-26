# Current Task

## 状态:待验证

## LFG 进度

### Goal(目标)
吸收 muratcankoylan/Agent-Skills-for-Context-Engineering 的 5 类 context degradation 诊断 + tokens-per-task 优化目标 + Artifact Trail 字段(GitHub Issue #50 / GitLab #24)。

### Context(上下文)
复杂度:大 | 通道:完整(evolution 模式) | 基线 commit:0f45009 | 工作分支:feat/evolution-50-context-engineering

### Assumptions(假设清单)
- 假设:ai-coding-pitfalls.md vs muratcankoylan 视角正交不冲突 | 依据:已读两份,前者关注 AI 行为,后者关注 attention 机制
- 假设:context-budget.md 净增 ≤ 30 行 | 依据:当前 126 行
- 假设:工作分支足够,不起 worktree | 依据:evolution 历史 pattern
- 假设:Artifact Trail 只改 lfg-progress-format,不改 audit.jsonl | 依据:Issue body 明确

### Acceptance(验收标准)
1. R-001 新 reference 模板存在:context-degradation-patterns.md.tmpl ≥ 130 行,含 5 类 pattern
2. R-002 tokens-per-task 概念引入 context-budget.md.tmpl + 反合理化表
3. R-003 Artifacts touched 字段引入 lfg-progress-format.md.tmpl
4. R-004 make ci 全过
5. R-005 dogfood 后无漂移

### Quality Baseline(质量基线)
- 测试:638 passed in 25s
- mypy:clean (49 source files)
- ruff:clean
- audit Dim 总分基线:14.85/15

### Files(涉及文件)
- 新建:`templates/common/.agent-harness/references/context-degradation-patterns.md.tmpl`
- 改:`templates/common/.claude/rules/context-budget.md.tmpl`
- 改:`templates/common/.claude/rules/anti-laziness.md.tmpl`
- 改:`templates/common/.agent-harness/references/lfg-progress-format.md.tmpl`
- 改:`templates/superpowers/.claude/commands/lfg.md.tmpl`
- 改:`templates/common/.agent-harness/references/OVERVIEW.md.tmpl`
- 加测试:`tests/test_check_repo.py` 或 `tests/test_lfg_audit.py`

### Artifacts touched(本次操作过的产物路径)
- 读: `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`、`src/agent_harness/templates/common/.claude/rules/{context-budget,anti-laziness}.md.tmpl`、`src/agent_harness/templates/common/.agent-harness/references/{lfg-progress-format,OVERVIEW,ai-coding-pitfalls}.md.tmpl`、`tests/test_lfg_squad_channel.py`、`scripts/dogfood.py`
- 改:模板 5 个 + 本仓库 5 个 + 测试 1 个 + 文档 3 个 = 14 文件
  - 新建:`templates/common/.agent-harness/references/context-degradation-patterns.md.tmpl`(190 行)
  - 新建:`tests/test_lfg_context_degradation.py`(114 行,9 条契约)
  - 新建:`.agent-harness/references/context-degradation-patterns.md`(从模板镜像 190 行)
  - 改:`templates/common/.claude/rules/{context-budget,anti-laziness}.md.tmpl`
  - 改:`templates/common/.agent-harness/references/{lfg-progress-format,OVERVIEW}.md.tmpl`
  - 改:`templates/superpowers/.claude/commands/lfg.md.tmpl`
  - 改 dogfood 同步:`.claude/commands/lfg.md`、`.claude/rules/{anti-laziness,context-budget}.md`
  - 改 OVERVIEW:`.agent-harness/references/OVERVIEW.md`
  - 改文档计数:`CHANGELOG.md`、`docs/{architecture,release}.md`
- 删除: 无

### Progress(阶段进度)
- [x] 0.1 任务理解 — evolution 模式自动完整通道
- [x] 0.2 历史加载 — memory-index + AGENTS + ai-coding-pitfalls + claude-code-internals + lfg-progress-format
- [x] 1 环境准备 — 工作分支 feat/evolution-50-context-engineering,基线 638 tests pass
- [—] 2 构思 — 跳过(Issue body 已含设计)
- [—] 2.5 规格 — 跳过(Issue body 等价 spec)
- [x] 3 计划 — 8 步,用户确认"走"
- [x] 4.1 步骤 1:新建 context-degradation-patterns.md.tmpl
- [x] 4.2 步骤 2:改 context-budget.md.tmpl
- [x] 4.3 步骤 3:改 anti-laziness.md.tmpl
- [x] 4.4 步骤 4:改 lfg-progress-format.md.tmpl
- [x] 4.5 步骤 5:改 lfg.md.tmpl 阶段 0.2 + 4.1
- [x] 4.6 步骤 6:改 OVERVIEW.md.tmpl
- [x] 4.7 步骤 7:加契约测试
- [x] 4.8 步骤 8:dogfood + make ci 验证
- [ ] 5 评审 — /multi-review
- [ ] 7 验证 — /verify
- [ ] 9 沉淀 — /compound + memory rebuild
- [ ] 10 收尾 — /finish-branch
