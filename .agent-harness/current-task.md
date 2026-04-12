# Current Task

## LFG 进度

### Goal（目标）
引入分层记忆加载（L0-L3 冷热分层），解决 `.agent-harness/` 下 lessons.md / task-log.md 随增长挤占上下文窗口的问题（Issue #10，吸收自 MemPalace）

### Context（上下文）
- 复杂度：大 | 通道：完整
- 基线 commit：49d48244
- 工作分支：feat/layered-memory
- Issue：GitHub #10（标签 absorbed，来源 MemPalace）

### Assumptions（假设清单）
- 假设：L0 = `project.json`（已存在，项目身份） | 依据：当前 project.json 承载身份信息
- 假设：L1 = current-task + lessons 最近 N 条 + task-log 最近 N 条 | 依据：MemPalace 设计 + ~200 tokens 预算
- 假设：L2 = 按主题分区的历史教训 | 依据：Issue 方案
- 假设：L3 = 完整 task-log 历史 | 依据：Issue 方案
- 假设：新增技能/CLI 让 AI 按需查询 L2/L3 | 依据：**待阶段 2 敲定**
- 假设：老项目升级时自动迁移单文件 → 分层结构 | 依据：项目有完整 upgrade 测试
- 假设：不改 AGENTS.md 硬规则，仅调整 task-lifecycle rule 中"读什么" | 依据：最小化范围

### Acceptance（验收标准）
1. `.agent-harness/` 支持 L0/L1/L2/L3 分层结构
2. Claude task-lifecycle 默认只加载 L0+L1（上下文 ≤ 200 tokens 稳定）
3. 存在显式触发方式加载 L2 / L3
4. `harness upgrade apply` 能平滑迁移单文件 → 分层
5. 模板同步到 9 种项目类型
6. 新增分层加载的测试，`make ci` 全绿
7. 文档全量同步
8. GitHub Issue #10（及 GitLab 对应）同步关闭

### Decisions（关键决策）
- 待阶段 2 构思 + 阶段 2.5 规格后敲定

### Quality Baseline（质量基线）
- 测试：176 个，100% 通过
- make check：通过
- 基线时间：2026-04-12

### Progress（阶段进度）
- [x] 理解与评估 — 复杂度大，通道完整，用户确认
- [x] 环境准备 — 分支 feat/layered-memory，基线测试 176/176
- [ ] 构思（/ideate + /brainstorm）
- [ ] 规格定义（/spec）
- [ ] 架构决策（/adr）
- [ ] 计划（/write-plan）
- [ ] 实施
- [ ] 自检
- [ ] 评审（/multi-review）
- [ ] 验证
- [ ] 质量对比
- [ ] 沉淀
- [ ] 完成报告
- [ ] 待验证
- [ ] 归档与收尾
