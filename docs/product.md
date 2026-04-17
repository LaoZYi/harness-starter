# 产品规则

这个仓库的目标不是承载某个具体业务，而是把"项目认知初始化"和"AI agent 协作入口"产品化。

## 核心能力

1. **探测**：扫描目标项目，产出结构化画像（语言、包管理器、命令、目录结构）。
2. **评估**：根据画像产出接入评分、缺口和建议。
3. **初始化**：根据项目类型和探测结果生成文档/配置文件。支持 `--scaffold` 从现有技术框架创建。交互式问答支持返回上一步和确认修改。
4. **工作流技能**：默认生成 32 个结构化开发技能命令（融合 superpowers + compound-engineering + gstack + 12-factor-agents），覆盖构思、设计、计划、执行、评审、安全、沉淀、自我进化全生命周期。可通过 `--no-superpowers` 关闭。外加 4 个 common 层命令（`/process-notes`、`/digest-meeting`、`/recall`、`/source-verify`）不受 `--no-superpowers` 影响。其中 `/digest-meeting` 是研发流程的源头入口——把多人讨论的语音转文字原始记录转为框架可消费的结构化产物（init 模式填文档 / iterate 模式写 current-task）。
5. **首次分析**：初始化后 current-task.md 预填分析任务，AI 打开项目自动补全文档。
6. **升级**：对已接入的项目做增量升级，支持三方合并（保留用户内容）、diff 预览、选择性升级和自动备份。冲突时插入标记并醒目提示。
7. **运维**：doctor（健康检查）、export（画像导出）、stats（任务统计）。
8. **扩展**：插件机制，用户可在 .harness-plugins/ 下放自定义规则和模板。
9. **上游同步**：`make sync-superpowers` 从上游仓库拉取最新 skills 变更报告。

## 持续演进（按时间倒序，最新在顶）

10. **Environment Engineering 设计哲学（Issue #34，2026-04-16，参考 holaboss-ai/holaOS）**：在 `docs/architecture.md` 顶部新增「设计哲学：Environment Engineering」段——明确本项目的方法论根基（优化 Agent 运行环境而非 prompt），对比 holaOS 的技术路径差异，消歧义 "Agent Harness" 一词在两个项目中的不同含义。纯文档增补，无代码变化。
11. **Claude Code 内部机制对齐（Issue #33，2026-04-16，吸收自 Windy3f3f3f3f/how-claude-code-works）**：从 Claude Code 50 万行源码分析中提炼关键洞察，深化本项目规则。（1）`context-budget.md` 新增"5 级渐进式压缩"对照段——说明规则 2 的 ≤ 2k tokens 阈值是 L1 Tool Result Budget 之前的前置防线，`/compact` 对应 L5 Autocompact 是最后手段；（2）`task-lifecycle.md` StuckDetector 前新增"L0 静默恢复"层——区分可重试的瞬时失败（命令超时、工具截断、临时文件冲突、git 锁）vs 同根因 3 次才停，对齐 Claude Code 7 个 continue site 的分级恢复理念；（3）新增 L2 参考文件 `references/claude-code-internals.md`（5 级压缩 + 7 continue site + 工具预执行 + 参考链接）。**不吸收**：agent-design.md 的"工具预执行"增强（F8 Control Flow 已覆盖），具体代码实现（逆向分析可能因版本差异过时）。
12. **git-cliff changelog 自动化（Issue #32，2026-04-16，吸收自 orhun/git-cliff）**：`/doc-release` 技能第 5 步新增 git-cliff 自动草稿生成——检测 `command -v git-cliff`，有则调用 `git-cliff --unreleased --strip header` 按 conventional commit 类型分组生成草稿供 AI 润色，无则提示安装并降级到手动整理。设计为**软依赖**（不违反零依赖原则），`docs/runbook.md` 新增安装说明和可选 `cliff.toml` 自定义配置示例。**不吸收**：不在 `harness init` 时自动生成 cliff.toml（内置配置足够用，用户需要自定义时自行创建）。
13. **Anthropic Agent Skills spec 对齐（Issue #31，2026-04-16，吸收自 anthropics/skills）**：在 `docs/architecture.md` 明确本项目技能（standalone commands）与 Anthropic Agent Skills 三种形态（standalone commands / model-invoked SKILL.md / plugin marketplace）的关系。`/write-skill` 模板新增 SKILL.md 格式选项（遵循 [agentskills.io/specification](https://agentskills.io/specification)），开发者创建新技能时可选择 model-invoked 模式。**不吸收**：不把现有 32 个 command 改为 SKILL.md（它们是用户主动触发的工作流步骤，model-invoked 会导致 Claude 在不该用时误调用）；不创建 `.claude-plugin/plugin.json`（commands 经 `harness init` 渲染含项目特定内容，无法跨项目原样分发）。
14. **Multi-Agent 角色分权 + Context Store 吸收（Issue #30，2026-04-14，吸收自 Danau5tin/multi-agent-coding-system）**：TerminalBench #13 水平的"能力/权限分层 + 知识复利"方法论落地——（1）`squad/capability.py` 新增 `orchestrator` capability，运行时 `settings.local.json` 强制 deny Edit/Write/MultiEdit/NotebookEdit，对齐源项目"编排者连代码都不碰"的强约束；（2）`agent.py` 新增 `diary_append_artifact` / `extract_artifacts` API + `agent artifact` CLI 子命令，把 sub-agent 的发现从自由日志升级为结构化知识制品，`aggregate` 顶部集中展示供后续任务 refs 复用；（3）`common/rules/autonomy.md` 追加 Trust Calibration 段，把静态三级操作分类升级为"任务复杂度 × 操作基线"二维模型；（4）`squad.md.tmpl` 文档 4 种角色 + 三标准角色卡，`subagent-dev.md.tmpl` 追加三角色模式段。**不吸收**：源项目的 Python 运行时代码（独立 LLM 编排框架，与 Claude Code 脚手架架构不兼容）。
15. **Context-Mode 方法论吸收（Issue #29，2026-04-14，吸收自 mksglu/context-mode）**：新增 `common/rules/context-budget.md` 规则（Think in Code 范式 + 工具输出预算双约束——搜索/统计/过滤任务优先脚本化、单次工具输出 > 2k tokens 必须先 pipe 处理）。新增 `memory_search.py` 模块 + `memory search <query>` CLI 子命令（纯 stdlib Okapi BM25，中英混合分词：英文 `\w+` 按词切、CJK 按字符 1-gram）。`/recall` 技能升级为二级兜底链路（Grep → BM25 兜底），解决"关键词写错或同义词"时 Grep 漏召的问题。`/lfg` 阶段 0.2 明确 Context Budget 约束 + BM25 兜底链路。**不吸收**：MCP server 本体（Node/SQLite 违反零依赖原则）。
16. **12-Factor Agent Design 集成（Issue #28，2026-04-14，吸收自 humanlayer/12-factor-agents）**：新增 `/agent-design-check` 技能（4 维度：F3 Context Ownership / F5 State Unification / F8 Control Flow / F10 Small Focused Agents），针对涉及 `/squad` / `/dispatch-agents` / `/subagent-dev` 的计划做 Agent 工程化体检。配套 `common/rules/agent-design.md` 规则（F8/F10 硬约束：worker 不得自持 retry/loop、单 worker ≤ 10 原子步骤）；`common/rules/task-lifecycle.md` 追加"Context Ownership"段（Factor 3）；`/plan-check` 扩到 8+1 维度（第 9 维度 Agent 工程化条件触发）；`/lfg` 阶段 3 在 `/plan-check` 后自动串联 `/agent-design-check`。**裁剪策略**：12-factor 中 F1/F2/F4/F6/F7/F9/F11/F12 预设自建 LLM 运行时不适用，只在新技能附录中作参考。
17. **skills-registry.json SSOT（Issue #27，2026-04-13）**：把 36 个 skill 的元数据（id / category / triggers / lfg_stage / expected_in_lfg / exclusion_reason）抽到单一 JSON 真相源。下游消费方：`which-skill.md.tmpl` 渲染决策树和三段索引；`lfg.md.tmpl` 渲染阶段覆盖表；`tests/test_lfg_coverage.py` 读取 EXPECTED_IN/NOT_IN_LFG；`harness skills lint` CLI 子命令在 CI 中强制三处一致性（孤儿 .md.tmpl / 注册但缺文件 / expected_in_lfg=true 但 lfg 未引用）。`<<SKILL_*>>` 双尖括号占位符避免与 `{{var}}` jinja 占位符冲突。`make ci` 串入 `make skills-lint` 守卫。
18. **/lfg gap 修复（2026-04-13，评估驱动）**：对单入口 `/lfg` 做 5 处接合补强，把运行时能力真正嵌进流水线：
    - **阶段 0.1 meta 类型路由**：读 `.agent-harness/project.json.project_type == meta` 时劝退到 `/meta-*` 命令集
    - **阶段 0.2 plugins 必读扩展**：把 `.harness-plugins/rules/*.md` 加入 L0/L1 必读，不再忽视团队自定义规则
    - **阶段 4.1 并行子 agent 硬隔离**：选 `/dispatch-agents`/`/subagent-dev` 时强制跑 `.agent-harness/bin/agent init/diary/aggregate`，防止并发写共享 current-task
    - **阶段 4.1 / 9.1 / 10.5 WAL 显式化**：每次改 current-task/lessons/task-log 都写 `.agent-harness/bin/audit append`，落实 task-lifecycle 硬规则
    - **阶段 9.1 L1 索引自刷新**：`/compound` 后跑 `.agent-harness/bin/memory rebuild . --force`，memory-index 不再过时
    - 由 `tests/test_lfg_gap_fixes.py` 6 条合约测试锁定。原评估中的"Gap 1 /health 未集成"经查 `test_lfg_coverage.py` 是明文设计排除项，撤回
19. **多 agent 常驻协作（/squad，阶段 1 MVP + 19a 依赖触发 + 21 mailbox/watch + 22 watchdog + 25 项目内嵌）**：通过 `.agent-harness/bin/squad create <spec.json>`（项目自带运行时，无需装 harness CLI，Issue #25）或 `harness squad create <spec.json>`（维护者命令，Issue #25 起去 PyYAML 迁 JSON）在 tmux 中按**拓扑序**启动多个带独立 worktree 的 Claude Code worker，按 capability（scout / builder / reviewer）用 `settings.local.json` 的 `permissions.deny` 运行时强制工具权限。共享状态写 `.agent-harness/squad/<task_id>/mailbox.db`（SQLite WAL 模式）。**阶段 2 依赖触发（Issue #19a）**：有 `depends_on` 的 worker 先渲染产物但不开 tmux 窗口，写 `pending` 事件；`harness squad done <worker>` 标记完成，`harness squad advance` 扫描并启动依赖已满足的 worker（幂等）；`harness squad status` 显示三态（✅ done / 🟢 running / ⏳/🔴 pending）+ 阻塞时长 + 30min 超时警告。**阶段 2 mailbox + watch（Issue #21）**：状态存储从 JSONL 升级为 SQLite（WAL 模式，并发读写友好），支持 `harness squad watch` 常驻进程轮询 mailbox 自动 advance（SIGTERM 优雅退出、所有 worker done 后自动退出），以及 `harness squad dump` 导出调试 JSONL。**阶段 2 Tier 0 Watchdog（Issue #22）**：`harness squad watch` 每个 tick 末尾跑 watchdog——`tmux has-session` 探测整体存活、`list-windows` 比对 worker 窗口；session 整体丢失 → 写 `session_lost` 事件并立即退出 watch（一次性，幂等）；已 spawned + 未 done + 窗口消失 → 写 `worker_crashed` 事件（按 worker 幂等去重）；`touch .agent-harness/.watchdog-skip` 可关闭整个 watchdog（沿用 context-monitor sentinel 模式）。本期不实现 pid 检查（worker 当前不写 pid）和自动重启（capability 切换+worktree 状态判断复杂度过高）。与 `/dispatch-agents`（一次性短任务）并存。硬依赖 tmux 和 POSIX（fcntl / signal），Windows 原生走 WSL。
20. **GSD 吸收三件套 + 两条加料（Issue #17，吸收自 gsd-build/get-shit-done + OpenSwarm）**：
    - **StuckDetector 规则**（task-lifecycle.md + /tdd + /debug）：连续 3 次同模式失败强制停下、写卡点记录、输出 3 个候选方向给用户选，避免在沉没成本上继续绕圈
    - **/lint-lessons 矛盾检测增强**：检出 3 种矛盾模式 + 2 种张力模式，输出 4 选 1 裁决建议但**不自动合并**
    - **需求 ID 三元映射**（/spec + /write-plan + /verify）：R-ID 贯穿规格→计划→验证全链路，验证时硬检查每个 R-ID 为 satisfied / out-of-scope / missed，missed 阻断完成。配套 L2 参考清单 `requirement-mapping-checklist.md`
    - **/plan-check 新技能**：8 维度（需求覆盖 / 原子性 / 依赖排序 / 文件作用域 / 可验证性 / 上下文适配 / 缺口检测 / Nyquist 合规）+ 最多 3 轮修订循环，作为 /write-plan 收尾或独立调用；/lfg 阶段 3 已串入
    - **上下文监控 Hook（降级版）**：经 source-verify 后，Claude Code statusline 不暴露 `remaining_percentage`，降级为 PostToolUse 工具调用计数代理指标（50/100/150 三级阈值提醒 /compact），纯 shell 跨平台；`touch .agent-harness/.context-monitor-skip` 可关闭
21. **输入安全校验代码化（Issue #15，吸收自 MemPalace）**：`src/agent_harness/security.py` 提供 `sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`，把 `.claude/rules/safety.md` 中"输入信任边界"规则从文档约束变为可复用函数。`sanitize_name` 统一了 agent.py 和 squad/spec.py 中重复的标识符正则；`sanitize_path` 防御路径遍历 + 绝对路径 + 符号链接逃逸；`sanitize_content` 对 oversize 抛异常（显式告警），对 null 字节和控制字符静默剥除（保留 `\n\t\r`）。`SecurityError` 继承 `ValueError` 保持向后兼容。
22. **多 agent 日志隔离（Issue #14，吸收自 MemPalace）**：`harness agent init/diary/status/list/aggregate` 子命令族，给 `/dispatch-agents` 和 `/subagent-dev` 场景的并行子 agent 提供独立目录 `.agent-harness/agents/<id>/{diary.md, status.md}`，避免并发写共享 current-task.md。agent id 规范 `^[a-z0-9][a-z0-9-]{0,30}$`（与 /squad 一致）；fcntl 锁保证并发写无丢失；主 agent 用 `harness agent aggregate` 汇总后决定哪些值得归档进 task-log（不自动 merge）。与 /squad 的 `squad/<task>/workers/<name>/` 目录各管各的场景，互不相干。
23. **会话保护 hooks（Issue #13，吸收自 MemPalace）**：Claude Code 的 Stop hook 和 PreCompact hook 自动触发。Stop hook 在 AI 停止前检查 current-task.md 是否还有未勾选 checkbox，有则 block 要求先更新进度；人工放行通过 `touch .agent-harness/.stop-hook-skip` 开关。PreCompact hook 在 `/compact` 前追加一条 audit 检查点并 stderr 提示 AI 把关键决策持久化。两个 hook 配合分层记忆 + 变更审计形成"读-写-保存"完整生命周期。
24. **关键文件变更审计（WAL，Issue #12，吸收自 MemPalace）**：`.agent-harness/audit.jsonl` 记录对 `current-task.md` / `task-log.md` / `lessons.md` 的每次写操作（时间戳 + 文件 + op + agent + summary），通过 `harness audit append/tail/stats/truncate` 操作。多 agent 冲突可追溯、误操作可回溯、不替代 git。采用 fcntl 锁保证并发写无丢失；agent 身份从 `HARNESS_AGENT` env 读取。
25. **lessons 分类索引**：`.agent-harness/lessons.md` 顶部维护"按分类索引"（测试 / 模板 / 流程 / 工具脚本 / 架构设计 / 集成API 共 6 类），条目标题统一为 `## YYYY-MM-DD [分类] 标题`。`/compound` 技能自动归类并维护索引一致性。memory-index 中的"最近教训"自然带分类前缀，一眼可见归属。
26. **专业参考清单**：`.agent-harness/references/` 提供 4 个 checklist（accessibility / performance / security / testing-patterns），按需通过 `/recall --refs` 加载，给专业维度补覆盖盲区。
27. **分层记忆加载**：`.agent-harness/memory-index.md` 作为 L1 热索引，`task-lifecycle` 规则默认只读它；`lessons.md` / `task-log.md` / `references/` 为 L2/L3，通过 `/recall` 技能或 `harness memory rebuild` 按需展开。避免知识积累挤占 AI 上下文窗口。

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
