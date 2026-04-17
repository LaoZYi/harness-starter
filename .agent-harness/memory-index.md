# Memory Index

> 热知识精华索引。详情见 `.agent-harness/lessons.md`、`.agent-harness/task-log.md` 和 `.agent-harness/references/`。
>
> **默认只读本文件**。需要深入某话题时，使用 `/recall <关键词>` 技能或直接 `grep` 完整文件。

## 最近教训（保留最多 10 条）

<!-- 由 /compound 技能或 `harness memory rebuild` 维护。-->

- 2026-04-17 [流程] **能力集成度评估用量化扫描而非主观判断** — 避免漏掉"已吸收但未显式声明"的能力
- 2026-04-17 [架构设计] **生产项目安全审计采用预防+兜底双重保障** — 审计前置到计划期，避免事后返工
- 2026-04-17 [流程] **补强任务按 ROI 递减主动收手** — 承诺 9.75 实际 9.56 诚实报告，避免无限加码
- 2026-04-14 [架构设计] 子 agent 产出要从自由日志升级到结构化制品
- 2026-04-14 [架构设计] 角色权限分层要从文档约束升级到运行时强制
- 2026-04-13 [流程] 280 行硬限触发时连环效应——3 个文件同时超
- 2026-04-13 [模板] 占位符层次必须显式区分（避免双重替换）
- 2026-04-13 [架构设计] 抽 SSOT 时必须清单化所有下游消费方
- 2026-04-13 [架构设计] Harness 中"反偷懒"与"协作记忆"模块要解耦
- 2026-04-13 [架构设计] 单入口技能 ≠ 能力接入完整

## 最近任务（保留最多 5 条）

<!-- 任务归档时顶部插入；超过上限时挤出最老。-->

- 2026-04-17 /lfg 威力补强三轮（7.5 → 8.75 → 9.56）+ ruff/mypy 集成 + 依赖升级 + Python 现代化
- 2026-04-16 新增 /digest-meeting 技能：讨论记录→框架可消费产物
- 2026-04-14 Issue #30 — Multi-Agent 角色分权 + Context Store 吸收
- 2026-04-14 Context-Mode 方法论吸收（Issue #29 / GitLab #13）
- 2026-04-14 12-Factor Agent Design 集成（Issue #28 / GitLab #12）

## 参考资料（.agent-harness/references/）

<!-- L2 温知识层。按需通过 `/recall --refs 关键词` 加载。-->

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
- references/ 为 L2 温知识（a11y / perf / security / testing）— 用 `/recall --refs` 按需查询。
- 索引由 `/compound` 技能维护；也可运行 `harness memory rebuild .` 从现有 lessons/task-log/references 重建一次。
