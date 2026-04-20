# ADR 0002：知识冲突解析（Knowledge Conflict Resolution）

- **状态**：Accepted
- **日期**：2026-04-20
- **接受日期**：2026-04-20
- **决策者**：LFG GitHub #43 / GitLab #22
- **相关 Issue**：GitHub #43 / GitLab #22（吸收自 [ilang-ai/Imprint](https://github.com/ilang-ai/Imprint) v2.1）

## 背景和问题

`.agent-harness/lessons.md` 会随任务推进积累矛盾条目。当前的维护机制有两个缺口：

1. **`/lint-lessons` 只分症状维度**：现有 5 种分类（规则反向 / 根因冲突 / 预防冲突 / 适用边界 / 优先级）告诉用户「是什么类型的冲突」，但没告诉「该怎么办」。用户拿到报告后仍需自己判断解决路径。

2. **`/compound` 不区分『重复』和『矛盾』**：写入新 lesson 前只做重叠度判断（高 / 中 / 低），两条说法相反的教训会各自独立写入，等下次 `/lint-lessons` 才被动发现。

Imprint 项目（v2.1，MIT，2026-04-19）提出 5 型 Conflict Resolution，把知识冲突按**解决路径**分类：

- T1：用户显式指令 vs 历史行为规则 → 跟用户本会话，3 次以上才固化
- T2：全局规则 vs 项目规则 → 项目覆盖全局，记录 mismatch
- T3：两条 confirmed 规则互相矛盾 → 转条件分支（`when:` 语义），都保留
- T4：不同 agent 给出不一致结论 → 两条都降级为 tentative，等用户确认
- T5：lesson 与当前任务冲突 → lesson 是警告不是阻断

**问题**：如何把这个分类最小化吸收到本项目，而不引入 Imprint 的整套 DSL 和 confidence 字段？

## 考虑过的方案

| 方案 | 接入面 | 新增规则 | 新概念 | 评估 |
|------|--------|---------|--------|------|
| A. 全盘吸收 Imprint（DSL + confidence + decay） | lessons 全面改造 | 1 | DSL + confidence + decay | **否**：破坏 lessons 格式，迁移成本高，4 star 方法论未验证 |
| B. 只吸收 5 型分类，lessons 格式不变 | `/lint-lessons` + `/compound` | 1 | 仅 5 型 | **候选** |
| C. 合并进 `anti-laziness.md` | 同 B | 0（扩展现有） | 5 型 | 否：正交关注点，合并会让 anti-laziness 失焦 |
| **D. 5 型中只吸收 T3/T4/T5，T1/T2 标注不适用** | `/lint-lessons` + `/compound` | 1 | 3 型 + 2 型锚点 | **最合** |

## 决策

**采纳方案 D**：新增元规则 `.claude/rules/knowledge-conflict-resolution.md`，文案化 T1-T5 全 5 型但明确只有 T3/T4/T5 适合接入本项目的 lessons 域；T1（用户 vs 历史）属于 AI 行为准则范畴、T2（全局 vs 项目）属于规则层级问题，均不在 lessons 域内直接处理。

### 关键设计点

1. **规则文件作为 SSOT**：`.claude/rules/knowledge-conflict-resolution.md` 是唯一入口；`/lint-lessons` 和 `/compound` 引用它但不内联 5 型定义，避免文案漂移
2. **保留现有症状分类不动**：`/lint-lessons` 2.2 的 5 种症状分类（规则反向 / 根因冲突 等）和 Imprint 5 型是不同轴——症状维度 × 解决维度，可叠加输出
3. **冲突预检是警告性**：`/compound` 新增的 3.5 步是「命中 → 分型 → 提示人工裁决」，不 block 写入，保持现有 UX
4. **T1/T2 保留为参考锚点**：规则文件中明确声明 T1/T2 在 lessons 域 out-of-scope，但保留描述——未来若做用户级 profile（Issue 点 3）或多规则层级协调（Issue 点 2）时可直接复用

### 不决定

- Imprint 的 `confidence` 字段（confirmed / 3/5 / tentative）——单独 Issue 评估
- `.dna.md` DSL 格式——永不吸收，与我们 markdown 分层哲学冲突
- 用户级跨项目 profile——单独 Issue，需设计 L-1 层如何与项目级 L0 协同

## 后果

### 正面

- `/lint-lessons` 输出从"发现矛盾"升级到"发现矛盾 + 该怎么办"，降低用户裁决成本
- `/compound` 把"写入前冲突预检"做成流程的一部分，减少 lessons 负熵
- 规则文件本身是模板化产物，通过 `make dogfood` 同步到项目自身，也会进 `templates/common/` 让下游接入项目受益
- 为将来吸收 confidence + decay（点 2）和用户级 profile（点 3）预留了语义锚点（T1/T2）

### 负面

- 增加一条需要维护的规则文件（~100 行）
- `/lint-lessons` 和 `/compound` 的模板各增加约 20-30 行，提升学习曲线
- 5 型中有 2 型（T1/T2）"仅声明不接入"，对不了解背景的读者可能显得冗余——通过规则文件里的 out-of-scope 说明缓解

### 中性

- 不改 `lessons.md` 现有条目格式和 `memory-index.md` 重建逻辑
- 不影响 `.agent-harness/bin/memory` 工具链
- 现有 529 条测试不变；新增 R-001 ~ R-007 的回归保护

## 参考

- [ilang-ai/Imprint SKILL.md](https://github.com/ilang-ai/Imprint/blob/main/skills/imprint/SKILL.md)（5 型定义源头）
- `docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-spec.md`（本次规格）
- `docs/superpowers/specs/2026-04-20-knowledge-conflict-resolution-plan.md`（本次计划）
- ADR 0001（分层记忆加载策略）——本 ADR 是对 0001 的层内补强
