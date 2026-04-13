# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-13 [架构设计] 三源对账推导状态而非持久化 worker 状态
- 2026-04-13 [架构设计] 模块拆分前留好未来模块位置
- 2026-04-13 [流程] 大 Issue 吸收要拆阶段 + atomic commit + step tag
- 2026-04-13 [架构设计] hook 依赖未公开 API 必须 source-verify 再决定降级
- 2026-04-13 [架构设计] 新异常类继承 ValueError 保向后兼容
- 2026-04-13 [架构设计] 路径遍历校验必须对 resolved 后的路径检查
- 2026-04-13 [架构设计] 自回环 hook 必须有人工放行开关
- 2026-04-13 [架构设计] 统一入口技能必须串起全量能力
- 2026-04-13 [工具脚本] 守卫禁用白名单改自动发现
- 2026-04-12 [测试] 文件锁顺序必须先锁再 truncate

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-13 多 agent 日志隔离（Issue #14，吸收自 MemPalace）
- 2026-04-13 Stop + PreCompact hook（Issue #13，吸收自 MemPalace）
- 2026-04-13 变更审计 WAL（Issue #12，吸收自 MemPalace）
- 2026-04-13 /lfg 技能覆盖完整化：33 个技能全员接入 + 契约测试锁死
- 2026-04-12 lessons.md 结构化分区（Issue #11，灵感自 MemPalace）

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
