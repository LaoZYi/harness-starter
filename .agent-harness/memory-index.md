# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-27 [测试] 检查「不调用 X」的契约测试要识别 invocation pattern 而非纯字符串 grep
- 2026-04-27 [工具脚本] `.claude/rules/` 和 `.claude/commands/` 都是 dogfood 生成产物，源在 `templates/superpowers/`
- 2026-04-27 [架构设计] 上层 skill 多场景化先走 D 方案（先抄 + 留位置），不要一上来 B 方案抽象
- 质量快照 — 2026-04-25
- 质量快照 — 2026-04-23
- 2026-04-23 [架构设计] 交付链路和治理链路必须并行，只做交付会导致 lessons 堆矛盾和 skills 老化
- 2026-04-23 [流程] 程序化调用 LLM 必须设硬限（--max-turns + timeout），否则异常情况烧尽配额
- 2026-04-23 [架构设计] 安全规则要补代码反例免疫，仅文字约束模型容易"知道但做不到"
- 2026-04-23 [架构设计] 吸收外部案例库优先做成 L2 references 而非改已有规则
- 2026-04-23 [架构设计] `.claude/commands/` 下任何 .md 都会被 Claude Code 注册为 slash command

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-27 通用文档场景脚手架（D 方案：先抄 + 留 B 位置）
- 2026-04-26 stop hook 范式革命: 行为信号取代内容形式识别(反模式 1 第 6 案例)
- 2026-04-26 补吸 mksglu/context-mode BENCHMARK 增量(Issue #54)
- 2026-04-26 补吸 Karpathy Think Before Coding 缺口(Issue #53)
- 2026-04-26 吸收 forrestchang/andrej-karpathy-skills(Issue #51)

## 参考资料（.agent-harness/references/）

<!-- L2 温知识层。按需通过 `/recall --refs 关键词` 加载。-->

- `ABSTRACT.md` — ABSTRACT
- `OVERVIEW.md` — References 导航
- `accessibility-checklist.md` — 无障碍检查清单（Accessibility）
- `context-degradation-patterns.md` — Context Degradation 5 类诊断模式
- `performance-checklist.md` — 性能检查清单（Performance）
- `requirement-mapping-checklist.md` — 需求 ↔ 测试 ↔ Plan Step 三元映射检查清单
- `security-checklist.md` — 安全检查清单
- `squad-channel.md` — squad-channel
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
