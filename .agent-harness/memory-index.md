# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 质量快照 — 2026-04-23
- 2026-04-23 [架构设计] 交付链路和治理链路必须并行，只做交付会导致 lessons 堆矛盾和 skills 老化
- 2026-04-23 [流程] 程序化调用 LLM 必须设硬限（--max-turns + timeout），否则异常情况烧尽配额
- 2026-04-23 [架构设计] 安全规则要补代码反例免疫，仅文字约束模型容易"知道但做不到"
- 2026-04-23 [架构设计] 吸收外部案例库优先做成 L2 references 而非改已有规则
- 2026-04-23 [架构设计] `.claude/commands/` 下任何 .md 都会被 Claude Code 注册为 slash command
- 2026-04-21 [架构设计] 入口技能 gap 先用工具量化再动手
- 2026-04-14 [架构设计] 子 agent 产出要从自由日志升级到结构化制品
- 2026-04-14 [架构设计] 角色权限分层要从文档约束升级到运行时强制
- 2026-04-13 [流程] 280 行硬限触发时连环效应——3 个文件同时超

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-23 stop hook 认 5 个「等用户」同义字面
- 2026-04-23 吸收 OpenViking 的目录分层摘要（ABSTRACT/OVERVIEW）
- 2026-04-22 feat(workflow): 吸收阿里云 Qoder CLI 文章 3 点
- 2026-04-22 feat(workflow): 吸收腾讯 LEGO Harness Engineering 文章 5 点
- 2026-04-22 feat(workflow): 吸收腾讯 AI 全自动化文章 3 点

## 参考资料（.agent-harness/references/）

<!-- L2 温知识层。按需通过 `/recall --refs 关键词` 加载。-->

- `ABSTRACT.md` — ABSTRACT
- `OVERVIEW.md` — References 导航
- `accessibility-checklist.md` — 无障碍检查清单（Accessibility）
- `performance-checklist.md` — 性能检查清单（Performance）
- `requirement-mapping-checklist.md` — 需求 ↔ 测试 ↔ Plan Step 三元映射检查清单
- `security-checklist.md` — 安全检查清单
- `testing-patterns.md` — 测试模式参考（Testing Patterns）

## 主题索引（可选，按关键词定位历史）

<!-- 人工或 AI 周期性整理。格式：`- 关键词 → lessons.md "条目标题"` -->

（尚未建立。当 lessons.md 条目较多时可整理此段方便定位。）

---

## 使用说明

- **task-lifecycle 规则**指示 AI 在开始新任务时默认读取本文件（而非 lessons.md / task-log.md 全量），避免上下文膨胀。
- 索引命中某话题 → 用 `/recall <关键词>` 技能或 `grep` 读取对应节。
- references/ 为 L2 温知识（a11y / perf / security / testing / pitfalls）— 用 `/recall --refs` 按需查询。
- 索引由 `/compound` 技能维护；也可运行 `harness memory rebuild .` 从现有 lessons/task-log/references 重建一次。
