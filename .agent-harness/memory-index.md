# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-12 脚手架项目吸收外部思想要选最小实现
- 2026-04-12 同一项目的增量吸收用 evolution-update 标签
- 2026-04-09 命令重命名后模板文件也要全量扫描
- 2026-04-09 模板中的文档占位符语法会被模板引擎吞掉
- 2026-04-09 重复工具函数提取后必须删除原始定义
- 2026-04-09 新任务覆盖前必须先关闭旧任务
- 2026-04-08 新增技能时文档散布计数需全量扫描
- 2026-04-08 GitLab Issue 搜索禁用 search 参数
- 2026-04-08 进化去重必须覆盖已关闭 Issue
- 2026-04-08 dogfood 命令展平

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-12 分层记忆加载（Issue #10，吸收自 MemPalace）
- 2026-04-10 深度完善项目类型功能差异化
- 2026-04-09 深度审计 + meta 项目类型 + harness sync 命令
- 2026-04-09 进化集成：spencermarx/open-code-review（Issue #9）
- 2026-04-09 升级三方合并策略 — 让 harness upgrade 保留用户内容

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
