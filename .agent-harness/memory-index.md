# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-13 [架构设计] 复制源码做内嵌运行时时，要给宿主模块去掉顶层副作用
- 2026-04-13 [架构设计] AI 运行时调用必须项目内嵌，不能依赖使用者机器的 CLI
- 2026-04-13 [流程] 辅助监控模块必须有异常隔离边界
- 2026-04-13 [架构设计] 幂等去重和退出判定不能共用同一个返回值
- 2026-04-13 [流程] 280 行硬限触发时不扩规则要拆/瘦模块
- 2026-04-13 [架构设计] watchdog 把"已上报"也写进事件流，避免外挂状态文件
- 2026-04-12 [测试] 文件锁顺序必须先锁再 truncate
- 2026-04-12 [架构设计] POSIX-only 模块要 try-except 软导入
- 2026-04-12 [工具脚本] shell 命令构造必须 shlex.quote 所有路径
- 2026-04-12 [流程] CLI flag 假设在 plan 阶段必须 source-verify

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-13 Issue #24 — audit / memory 项目内嵌（解除 AI 工作流对 harness CLI 的运行时依赖）
- 2026-04-13 Issue #22 — squad Tier 0 Watchdog（最后一块阶段 2 拼图）
- 2026-04-13 /squad SQLite mailbox + watch/dump（Issue #21，合并原 #20）
- 2026-04-13 /squad 依赖触发 + 拓扑序启动（Issue #19a，阶段 2 部分）
- 2026-04-13 GSD 吸收三件套 + OpenSwarm 两条加料（Issue #17）

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
