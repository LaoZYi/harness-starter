# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-13 [架构设计] 统一入口技能必须串起全量能力
- 2026-04-13 [工具脚本] 守卫禁用白名单改自动发现
- 2026-04-12 [测试] 文件锁顺序必须先锁再 truncate
- 2026-04-12 [架构设计] POSIX-only 模块要 try-except 软导入
- 2026-04-12 [工具脚本] shell 命令构造必须 shlex.quote 所有路径
- 2026-04-12 [流程] CLI flag 假设在 plan 阶段必须 source-verify
- 2026-04-12 [架构设计] 脚手架项目吸收外部思想要选最小实现
- 2026-04-12 [流程] 同一项目的增量吸收用 evolution-update 标签
- 2026-04-09 [模板] 命令重命名后模板文件也要全量扫描
- 2026-04-09 [模板] 模板中的文档占位符语法会被模板引擎吞掉

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-13 变更审计 WAL（Issue #12，吸收自 MemPalace）
- 2026-04-13 /lfg 技能覆盖完整化：33 个技能全员接入 + 契约测试锁死
- 2026-04-13 代码健康审计：280 行硬规则违反修复 + 守卫自动化
- 2026-04-12 lessons.md 结构化分区（Issue #11，灵感自 MemPalace）
- 2026-04-12 分层记忆加载（Issue #10，吸收自 MemPalace）

## 参考资料（.agent-harness/references/）

<!-- L2 温知识层。按需通过 `/recall --refs 关键词` 加载。-->

- `accessibility-checklist.md` — 无障碍检查清单（Accessibility）
- `performance-checklist.md` — 性能检查清单（Performance）
- `security-checklist.md` — 安全检查清单
- `testing-patterns.md` — 测试模式参考（Testing Patterns）

## 主题索引（可选，按关键词定位历史）

<!-- 人工或 AI 周期性整理。格式：`- 关键词 → lessons.md "条目标题"` -->

（尚未建立。当 lessons.md 条目较多时可整理此段方便定位。）

---

## 使用说明

- **task-lifecycle 规则**指示 AI 在开始新任务时默认读取本文件（而非 lessons.md / task-log.md 全量），避免上下文膨胀。
- 索引命中某话题 → 用 `/recall <关键词>` 技能或 `grep` 读取对应节。
- references/ 为 L2 温知识（a11y / perf / security / testing）— 用 `/recall --refs` 按需查询。
- 索引由 `/compound` 技能维护；也可运行 `harness memory rebuild .` 从现有 lessons/task-log/references 重建一次。
