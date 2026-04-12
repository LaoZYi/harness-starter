# Current Task

## LFG 进度

### Goal（目标）
吸收 addyosmani/agent-skills 增量更新（Issue #16）：新技能 /source-verify、references/ 四 checklist、context-engineering 理论章节。

### Context（上下文）
- 复杂度：中 | 通道：标准
- 基线 commit：9959249
- 工作分支：feat/agent-skills-increment
- Issue：GitHub #16（evolution-update + absorbed）

### Assumptions
- /source-verify 独立新技能，不融入 /tdd
- references/ 放 .agent-harness/（L2 温知识）
- checklist 序言汉化，术语保留英文（LCP/TTFB/INP）
- /recall --refs 扩展非破坏性（默认行为不变）
- context-engineering 作为 task-lifecycle 理论章节，不单独做技能
- 不吸收 subagents、hook 增强、其它延后项

### Acceptance（10 项，见 Issue #16）

### Progress
- [x] Phase 0 评估 — 复杂度中，标准通道，用户确认
- [x] Phase 1 环境准备 — feat/agent-skills-increment 分支，基线 192 测试
- [x] Phase 2.5 规格 — `docs/superpowers/specs/2026-04-12-agent-skills-increment-spec.md`
- [x] Phase 3 计划 — `docs/superpowers/specs/2026-04-12-agent-skills-increment-plan.md`（13 步）
- [ ] Phase 4 实施
- [ ] Phase 4.3 自检
- [ ] Phase 7 验证（E2E smoke + 全量 CI）
- [ ] Phase 8 质量对比
- [ ] Phase 9 沉淀
- [ ] Phase 10 收尾与归档
