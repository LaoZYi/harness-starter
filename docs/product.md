# 产品规则

这个仓库的目标不是承载某个具体业务，而是把"项目认知初始化"和"AI agent 协作入口"产品化。

## 框架提供什么

1. **探测**：扫描目标项目，产出结构化画像（语言、包管理器、命令、目录结构）。
2. **评估**：根据画像产出接入评分、缺口和建议。
3. **初始化**：根据项目类型和探测结果生成文档/配置文件。支持 `--scaffold` 从现有技术框架创建。交互式问答支持返回上一步和确认修改。
4. **工作流技能**：默认生成 30 个结构化开发技能命令（融合 superpowers + compound-engineering + gstack），覆盖构思、设计、计划、执行、评审、安全、沉淀、自我进化全生命周期。可通过 `--no-superpowers` 关闭。外加 3 个 common 层命令（`/process-notes`、`/recall`、`/source-verify`）不受 `--no-superpowers` 影响。
5. **首次分析**：初始化后 current-task.md 预填分析任务，AI 打开项目自动补全文档。
6. **升级**：对已接入的项目做增量升级，支持三方合并（保留用户内容）、diff 预览、选择性升级和自动备份。冲突时插入标记并醒目提示。
7. **运维**：doctor（健康检查）、export（画像导出）、stats（任务统计）。
8. **扩展**：插件机制，用户可在 .harness-plugins/ 下放自定义规则和模板。
9. **上游同步**：`make sync-superpowers` 从上游仓库拉取最新 skills 变更报告。
10. **分层记忆加载**：`.agent-harness/memory-index.md` 作为 L1 热索引，`task-lifecycle` 规则默认只读它；`lessons.md` / `task-log.md` / `references/` 为 L2/L3，通过 `/recall` 技能或 `harness memory rebuild` 按需展开。避免知识积累挤占 AI 上下文窗口。
11. **专业参考清单**：`.agent-harness/references/` 提供 4 个 checklist（accessibility / performance / security / testing-patterns），按需通过 `/recall --refs` 加载，给专业维度补覆盖盲区。
12. **lessons 分类索引**：`.agent-harness/lessons.md` 顶部维护"按分类索引"（测试 / 模板 / 流程 / 工具脚本 / 架构设计 / 集成API 共 6 类），条目标题统一为 `## YYYY-MM-DD [分类] 标题`。`/compound` 技能自动归类并维护索引一致性。memory-index 中的"最近教训"自然带分类前缀，一眼可见归属。
13. **关键文件变更审计（WAL，Issue #12，吸收自 MemPalace）**：`.agent-harness/audit.jsonl` 记录对 `current-task.md` / `task-log.md` / `lessons.md` 的每次写操作（时间戳 + 文件 + op + agent + summary），通过 `harness audit append/tail/stats/truncate` 操作。多 agent 冲突可追溯、误操作可回溯、不替代 git。采用 fcntl 锁保证并发写无丢失；agent 身份从 `HARNESS_AGENT` env 读取。
15. **多 agent 日志隔离（Issue #14，吸收自 MemPalace）**：`harness agent init/diary/status/list/aggregate` 子命令族，给 `/dispatch-agents` 和 `/subagent-dev` 场景的并行子 agent 提供独立目录 `.agent-harness/agents/<id>/{diary.md, status.md}`，避免并发写共享 current-task.md。agent id 规范 `^[a-z0-9][a-z0-9-]{0,30}$`（与 /squad 一致）；fcntl 锁保证并发写无丢失；主 agent 用 `harness agent aggregate` 汇总后决定哪些值得归档进 task-log（不自动 merge）。与 /squad 的 `squad/<task>/workers/<name>/` 目录各管各的场景，互不相干。
14. **会话保护 hooks（Issue #13，吸收自 MemPalace）**：Claude Code 的 Stop hook 和 PreCompact hook 自动触发。Stop hook 在 AI 停止前检查 current-task.md 是否还有未勾选 checkbox，有则 block 要求先更新进度；人工放行通过 `touch .agent-harness/.stop-hook-skip` 开关。PreCompact hook 在 `/compact` 前追加一条 audit 检查点并 stderr 提示 AI 把关键决策持久化。两个 hook 配合分层记忆 + 变更审计形成"读-写-保存"完整生命周期。
16. **输入安全校验代码化（Issue #15，吸收自 MemPalace）**：`src/agent_harness/security.py` 提供 `sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`，把 `.claude/rules/safety.md` 中"输入信任边界"规则从文档约束变为可复用函数。`sanitize_name` 统一了 agent.py 和 squad/spec.py 中重复的标识符正则；`sanitize_path` 防御路径遍历 + 绝对路径 + 符号链接逃逸；`sanitize_content` 对 oversize 抛异常（显式告警），对 null 字节和控制字符静默剥除（保留 `\n\t\r`）。`SecurityError` 继承 `ValueError` 保持向后兼容。
17. **GSD 吸收三件套 + 两条加料（Issue #17，吸收自 gsd-build/get-shit-done + OpenSwarm）**：
    - **StuckDetector 规则**（task-lifecycle.md + /tdd + /debug）：连续 3 次同模式失败强制停下、写卡点记录、输出 3 个候选方向给用户选，避免在沉没成本上继续绕圈
    - **/lint-lessons 矛盾检测增强**：检出 3 种矛盾模式 + 2 种张力模式，输出 4 选 1 裁决建议但**不自动合并**
    - **需求 ID 三元映射**（/spec + /write-plan + /verify）：R-ID 贯穿规格→计划→验证全链路，验证时硬检查每个 R-ID 为 satisfied / out-of-scope / missed，missed 阻断完成。配套 L2 参考清单 `requirement-mapping-checklist.md`
    - **/plan-check 新技能**：8 维度（需求覆盖 / 原子性 / 依赖排序 / 文件作用域 / 可验证性 / 上下文适配 / 缺口检测 / Nyquist 合规）+ 最多 3 轮修订循环，作为 /write-plan 收尾或独立调用；/lfg 阶段 3 已串入
    - **上下文监控 Hook（降级版）**：经 source-verify 后，Claude Code statusline 不暴露 `remaining_percentage`，降级为 PostToolUse 工具调用计数代理指标（50/100/150 三级阈值提醒 /compact），纯 shell 跨平台；`touch .agent-harness/.context-monitor-skip` 可关闭
16. **多 agent 常驻协作（/squad，阶段 1 MVP + 19a 依赖触发 + 21 mailbox/watch + 22 watchdog + 25 项目内嵌）**：通过 `.agent-harness/bin/squad create <spec.json>`（项目自带运行时，无需装 harness CLI，Issue #25）或 `harness squad create <spec.json>`（维护者命令，Issue #25 起去 PyYAML 迁 JSON）在 tmux 中按**拓扑序**启动多个带独立 worktree 的 Claude Code worker，按 capability（scout / builder / reviewer）用 `settings.local.json` 的 `permissions.deny` 运行时强制工具权限。共享状态写 `.agent-harness/squad/<task_id>/mailbox.db`（SQLite WAL 模式）。**阶段 2 依赖触发（Issue #19a）**：有 `depends_on` 的 worker 先渲染产物但不开 tmux 窗口，写 `pending` 事件；`harness squad done <worker>` 标记完成，`harness squad advance` 扫描并启动依赖已满足的 worker（幂等）；`harness squad status` 显示三态（✅ done / 🟢 running / ⏳/🔴 pending）+ 阻塞时长 + 30min 超时警告。**阶段 2 mailbox + watch（Issue #21）**：状态存储从 JSONL 升级为 SQLite（WAL 模式，并发读写友好），支持 `harness squad watch` 常驻进程轮询 mailbox 自动 advance（SIGTERM 优雅退出、所有 worker done 后自动退出），以及 `harness squad dump` 导出调试 JSONL。**阶段 2 Tier 0 Watchdog（Issue #22）**：`harness squad watch` 每个 tick 末尾跑 watchdog——`tmux has-session` 探测整体存活、`list-windows` 比对 worker 窗口；session 整体丢失 → 写 `session_lost` 事件并立即退出 watch（一次性，幂等）；已 spawned + 未 done + 窗口消失 → 写 `worker_crashed` 事件（按 worker 幂等去重）；`touch .agent-harness/.watchdog-skip` 可关闭整个 watchdog（沿用 context-monitor sentinel 模式）。本期不实现 pid 检查（worker 当前不写 pid）和自动重启（capability 切换+worktree 状态判断复杂度过高）。与 `/dispatch-agents`（一次性短任务）并存。硬依赖 tmux 和 POSIX（fcntl / signal），Windows 原生走 WSL。

## 支持的项目类型（9 种）

backend-service、web-app、cli-tool、library、worker、mobile-app、monorepo、data-pipeline、meta

每种类型在 `presets/` 下有独立的 JSON 预设，定义行为变化判定、架构关注点、发布检查项和默认完成标准。每种类型还有专属规则模板（`templates/<type>/.claude/rules/`），为 AI agent 提供类型相关的开发约束。评估（assessment）根据类型检查对应的项目结构信号并给出加分和建议。

### meta 项目类型

meta 项目是微服务系统的中央大脑，不含业务代码，管理三件事：服务在哪、谁调谁、业务规则是什么。

初始化后生成：
- `services/registry.yaml` — 服务注册表（名称、本地路径、领域、负责人）
- `services/dependency-graph.yaml` — 依赖关系图（provides/consumes）
- `business/domains/` — 按领域组织的业务知识（术语表、规则、流程）
- `business/products/` — 产品需求
- `business/roadmap.md` — 版本规划
- `shared-plugins/` — 分发到各服务的共享规则和模板
- `tasks/` — 跨服务任务文件（YAML 格式，含每个服务的目标和依赖关系）
- `BEST-PRACTICES.md` — 最佳实践指南

meta 专属命令（统一 `meta-` 前缀）：
- `/meta-sync` — 将 meta 信息同步到各服务仓库
- `/meta-populate` — 从已注册的代码仓库扫描推理，填充 meta 空缺（三阶段流水线：确定性提取 → LLM 解读 → 交叉验证）
- `/meta-create-task` — 从会议纪要生成跨服务任务草稿（AI 生成 → 人工确认）
- `/meta-activate-task` — 激活任务，创建 worktree 工作空间并注入 current-task.md

## CLI 命令清单

| 命令 | 作用 |
|------|------|
| `harness init <target>` | 交互式初始化（可选框架脚手架 + 5 个问题 + 确认/回退 + 自动探测） |
| `harness init <target> --scaffold <path>` | 基于现有技术框架创建 |
| `harness init <target> --assess-only` | 只看探测评估结果 |
| `harness init <target> --non-interactive` | 全自动初始化 |
| `harness upgrade plan <target>` | 升级预览 |
| `harness upgrade apply <target>` | 执行升级（自动备份） |
| `harness doctor <target>` | 健康检查 |
| `harness export <target>` | 导出项目画像 |
| `harness stats <target>` | 任务数据统计 |
| `harness sync <target> --meta <meta-repo>` | 同步跨服务上下文和共享规则（meta 路径可省略） |
| `harness sync --all` | 批量同步所有服务（在 meta repo 内运行） |
| `harness memory rebuild <target>` | 从 lessons/task-log 重建 `memory-index.md`（`--force` 覆盖已有） |

## 什么算行为变化

- 影响探测结果字段的改动
- 影响评估结果和接入建议的改动
- 影响模板生成内容的改动
- 影响初始化默认值或交互流程的改动
- 影响生成文件列表或目录结构的改动
- 影响 CLI 命令参数或输出格式的改动

## 变更原则

- 改了初始化输出，必须补对应测试。
- 改了探测字段，必须同步更新文档和模板。
- 改了 CLI 命令或参数，必须同步更新 `docs/runbook.md`。
- 改了模板，必须验证生成结果（`harness init /tmp/test --dry-run`）。
