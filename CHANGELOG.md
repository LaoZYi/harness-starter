# Changelog

## [Unreleased]

### Changed — `/use-superpowers` 更名为 `/which-skill`（2026-04-16）

消除与上游 obra/superpowers 开源项目的命名歧义。`/use-superpowers` 容易让用户误以为在调用 superpowers 项目本身，实际功能是「技能选择引导」。

**改动范围**：
- 重命名模板 `use-superpowers.md.tmpl` → `which-skill.md.tmpl`
- 重命名生成产物 `.claude/commands/use-superpowers.md` → `which-skill.md`
- `skills-registry.json` 中 id 和 name 同步更新（`"技能选择引导"`）
- 模板/生成文件标题从「使用 Superpowers 技能系统」改为「技能选择引导」
- 全量替换 30 个文件中的引用（源码、测试、文档、历史归档）
- 3 处测试函数名从 `test_use_superpowers_*` 改为 `test_which_skill_*`

### Added — 使用手册（2026-04-16）

新增 `docs/usage-manual.md`（完整版，19 章节）和 `docs/quickstart.md`（速查版，一页纸）。

### Added — Context-Mode 方法论吸收（Issue #29 / GitLab #13，2026-04-14）

吸收 [mksglu/context-mode](https://github.com/mksglu/context-mode)（7k+ ⭐，HN #1）的 3 层方法论——**Think in Code** + **BM25 兜底检索** + **Context Budget** 约束。**不吸收**其 MCP server 本体（Node/SQLite 违反零依赖原则），只吸收方法论为规则 + 纯 stdlib Python 工具。

**新文件**：
- `templates/common/.claude/rules/context-budget.md.tmpl`：Think in Code + 工具输出预算双约束（2k tokens 阈值触发 pipe 预处理）
- `src/agent_harness/memory_search.py`：纯 stdlib Okapi BM25（k1=1.5, b=0.75）、中英混合分词（`\w+` + CJK 1-gram）
- `tests/test_memory_search.py`：25 条契约（tokenize/segment/BM25/CLI E2E）

**改动**：
- `src/agent_harness/memory.py`：新增 `memory search` 子命令；BM25 拆到独立模块避免触发 280 行硬限
- `src/agent_harness/runtime_install.py`：`memory_search.py` 加入 `_RUNTIME_MODULES`，`.agent-harness/bin/memory search` 项目内嵌即可用
- `templates/common/.claude/commands/recall.md.tmpl`：Grep 未命中时自动串 BM25 兜底（第 5 步）
- `templates/superpowers/.claude/commands/lfg.md.tmpl`：阶段 0.2 加入 Context Budget 约束 + BM25 兜底链路
- `templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`：`/recall` 描述补充"含 BM25 兜底"
- `tests/test_runtime_bin.py`：stdlib allow-list 新增 `math`（BM25 需要）

**测试**：499 tests OK（+12）；`make check` 无警告；`harness skills lint` OK；`make dogfood` 无漂移。

### Added — 12-Factor Agent Design 集成（Issue #28 / GitLab #12，2026-04-14）

吸收 [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)（19k+ ⭐）的方法论，裁剪为本项目真正适用的 4 条 Factor（F3/F5/F8/F10），落地为 1 个新技能 + 1 个新规则 + 2 处增量修改。技能总数 31 → 32 个工作流技能命令。

**新文件**：
- `templates/superpowers/.claude/commands/agent-design-check.md.tmpl`：4 维度 Agent 设计体检（F3 Context Ownership / F5 State Unification / F8 Control Flow / F10 Small Focused Agents）
- `templates/common/.claude/rules/agent-design.md.tmpl`：F8/F10 硬约束 + F5 同步点约束
- `docs/superpowers/specs/2026-04-14-12factor-agent-design-{spec,plan}.md`

**改动**：
- `templates/common/.claude/rules/task-lifecycle.md.tmpl`：追加"Context Ownership"段（F3）
- `templates/superpowers/.claude/commands/plan-check.md.tmpl`：新增第 9 维度"Agent 工程化"（条件触发）
- `templates/superpowers/.claude/commands/lfg.md.tmpl`：阶段 3 引入 `/agent-design-check` 条件调用
- `templates/superpowers/skills-registry.json`：注册 `agent-design-check`（第 35 个 skill；其中 expected_in_lfg=true 的技能从 31 升到 32 个）

**裁剪策略**：
- 本项目是 Claude Code 模板库，非自建 LLM 运行时。12-factor 中 F1/F2/F4/F6/F7/F9/F11/F12 预设"拥有 prompt/tool schema/状态机代码控制权"不适用，只在新技能附录中列出作参考
- F8（Control Flow）硬约束：worker prompt 禁止自持 retry/loop
- F10（Small Focused）硬约束：单 worker ≤ 10 原子步骤
- F3（Context Ownership）加入 task-lifecycle L0-L3 分层之外的"子 agent prompt 必须显式设计"原则
- F5（Unified State）约束同步点，防止 agent 完成但业务状态不同步

### Added — Skills Registry SSOT（Issue #27 / GitLab #11，2026-04-13）

把 34 个 skill 的元数据抽到 `templates/superpowers/skills-registry.json` 单一真相源，消除三处文档（which-skill.md.tmpl / lfg.md.tmpl / test_lfg_coverage.py）的同步漂移风险。

**新文件**：
- `src/agent_harness/templates/superpowers/skills-registry.json`：34 skill 元数据（id / category / one_line / triggers / lfg_stage / expected_in_lfg / exclusion_reason / decision_tree_label）
- `src/agent_harness/skills_registry.py`：渲染器（load_registry / render_decision_tree / render_skill_index_by_phase / render_lfg_coverage_table / apply_to_target）
- `src/agent_harness/skills_lint.py`：三检查（孤儿 .md.tmpl / 注册但缺文件 / expected_in_lfg=true 但 lfg 未引用）
- `tests/test_skills_registry.py`：13 条契约（registry 加载 / 渲染 / lint）

**改造**：
- `which-skill.md.tmpl`：手写决策树和三段索引替换为 `<<SKILL_DECISION_TREE>>` 和 `<<SKILL_INDEX_BY_PHASE>>` 占位符
- `lfg.md.tmpl`：手写阶段覆盖表替换为 `<<SKILL_COVERAGE_TABLE>>` 占位符
- `tests/test_lfg_coverage.py`：EXPECTED_IN_LFG / EXPECTED_NOT_IN_LFG 改为从 registry 读取（消除硬编码 set）
- `initializer.py` / `upgrade.py` / `scripts/dogfood.py`：材化 superpowers 模板后调用 `apply_to_target` 替换 `<<SKILL_*>>`
- `cli.py`：新增 `harness skills lint <target>` 子命令
- `Makefile`：`make ci` 串入 `make skills-lint` 守卫

**占位符设计**：使用 `<<SKILL_xxx>>` 双尖括号，与 `{{var}}` jinja 占位符隔离，避免双重替换冲突。

**约束**：
- 加新 skill 只改 `skills-registry.json`，不直接编辑两个 .md.tmpl 的 skill 段落（PR 模板已加 checkbox）
- 不引入 PyYAML（沿用 .json，符合 Issue #25 运行时无依赖承诺）
- 渲染发生在模板时（init / upgrade / dogfood），非运行时

**评分**：/lfg 单一入口完整性进一步加固，新增 `skills lint` 把"反向合约"自动化，杜绝未来 skill 漂移。

### Added — /lfg 能力发挥度复评 + 4 Gap 修复 + 3 润色（2026-04-13，评估驱动）

基于"用户只需记 /lfg 一条命令"目标，对 /lfg 做系统性能力发挥度评估并修复所有发现的接合缝隙。

**第一轮：4 Gap + meta 路由修复**
- **阶段 0.1 meta 项目类型路由**：读 `.agent-harness/project.json.project_type == meta` 时劝退到 `/meta-*` 命令集
- **阶段 0.2 插件规则必读**：扫描 `.harness-plugins/rules/*.md` 进入 L0/L1 必读，团队自定义规则不再被忽视
- **阶段 4.1 并行子 agent 硬隔离**：选 `/dispatch-agents` 或 `/subagent-dev` 时强制跑 `.agent-harness/bin/agent init/diary/aggregate`，防止并发写共享 current-task.md
- **阶段 4.1 / 9.1 / 10.5 WAL 显式化**：每次改 current-task / lessons / task-log 都显式 `.agent-harness/bin/audit append`，落实 task-lifecycle 硬规则
- **阶段 9.1 L1 索引自刷新**：`/compound` 后跑 `.agent-harness/bin/memory rebuild . --force`，memory-index 不再过时

**第二轮：复评后润色**
- **阶段 7.3 穷举验证**：新增步骤 0 `/recall --refs testing` 加载 `testing-patterns.md` L2 清单
- **阶段 0.1 evolution 分支**：标注自动走完整通道（含 /ideate + /brainstorm + /spec + /plan-check）
- **阶段 3.2 计划质量检查**："历史教训" 扩为 "历史教训 + 团队规则（含 plugins/rules）"

**合约测试**
- 新增 `tests/test_lfg_gap_fixes.py`，9 条宽松正则合约锁定所有修复点
- 撤回原评估中"Gap 1 /health 未集成"结论——经查 `test_lfg_coverage.py:64` 是明文设计排除项，并沉淀为 lessons

**两条跨会话教训**
- `[流程] 评估报告前必须先查合约测试` — `EXPECTED_NOT_IN_*` 是项目对"不做某事"的显式承诺
- `[架构设计] 单入口技能 ≠ 能力接入完整` — 要用双核对表：skill 链 + 运行时元能力

**/lfg 评分：从 87 → 100**。Skill 链、运行时胶水、规则合规、分层记忆全部接通并由 15 条合约（`test_lfg_coverage.py` 6 + `test_lfg_gap_fixes.py` 9）锁死。

### Added — /lfg 整合 squad 通道：5 档复杂度 + 6 介入点（Issue #26，#23 子任务 3 / 收官）

- **阶段 0.3 复杂度判定新增第 5 档"超大-可并行"**：信号含「同时/并行/分头/兵分/scout-builder-reviewer」关键词、可拆 3+ 互不强依赖子任务、经典「调研→实现→评审」、单 agent 估时 > 4 小时
- **新章节 `## squad 通道（超大-可并行任务）`**：/lfg 主会话扮演协调员，自动生成 spec.json 拓扑草稿（默认 scout-builder-reviewer 三段，另有"多端点并行""重构+迁移""独立模块"三种模板）
- **6 个用户介入点**：拓扑确认（可降级到完整通道）/ scout done 强制 compact / watchdog 失联处置 / worker 卡死处置 / reviewer PASS 强制 compact / finish-branch 合并
- **失败兜底表 + 硬规则回顾**：worker 内**不**递归 lfg（AGENTS.md 第 7 条）
- **所有 bin/squad 调用走 Issue #25 的项目内嵌 runtime**
- **新测试 `tests/test_lfg_squad_channel.py`**（11 条契约）：第 5 档、并行关键词、6 介入点、降级出口、bin/squad 调用、spec 必为 json、/compact 强制、默认拓扑、失败兜底

**Issue #23 meta tracker 三子任务全部完成**（#24 + #25 + #26）：用户 clone init 过的项目 + 开 Claude Code，`/lfg` 任意需求——AI 自动判定复杂度，普通走单 agent，复杂可并行自动起 squad 多 worker + 6 介入点，全程**无需装 harness CLI + 无需装 PyYAML**。

### Added — squad 项目内嵌 + 破坏性变更 spec.yaml → spec.json（Issue #25，#23 子任务 2）

- **去 PyYAML 依赖**：`src/agent_harness/squad/spec.py` 从 yaml.safe_load 迁到 json.loads；spec 文件必须是 `.json` 后缀，`.yaml` / `.yml` 会拒绝并给出精确迁移命令
- **扩展 `runtime_install.py`**：复制 squad 整包（10 个 .py）+ security.py 到 `.agent-harness/bin/_runtime/`；自动把 squad.spec 里的 `from ..security import` 改写成 `from _runtime.security import`（_runtime 作为顶级 package）
- **新 entry 脚本 `bin/squad`**：Python shebang，加 bin/ 到 sys.path，调用 `_runtime.squad.cli.main`
- **squad/cli.py 新增 `main(argv=None)`**：抽 `_add_squad_subcommands` 共享给 `register_subcommand`（harness CLI 路径）和 `main`（bin 路径）
- **模板替换**：3 个 .tmpl（lfg / squad / task-lifecycle）+ AGENTS.md + docs/runbook + docs/product 里 `harness squad create <spec.yaml>` 全部改 `.agent-harness/bin/squad create <spec.json>`
- **新测试 `tests/test_runtime_bin_squad.py`**（6 条端到端契约）：
  - init 创建完整 bin/squad + _runtime/squad/ 结构；spec.py 的 security import 改写为绝对路径
  - 纯 stdlib AST 守卫扩展到 squad 所有文件 + security.py
  - bin/squad create / status 在无 harness + 无 PyYAML 环境跑通
  - bin/squad 对 .yaml spec 给精确迁移提示（破坏性变更的回归保护）
- **现有 squad 测试全部迁 yaml→json**（test_squad_spec_parse / dependency / integration / mailbox）

### Added — 项目内嵌运行时：audit / memory 脱离 harness CLI 依赖（Issue #24，#23 子任务 1）

- **新模块 `src/agent_harness/runtime_install.py`**：`install_runtime(target_root)` 把
  audit/audit_cli/memory 源码复制到目标项目 `.agent-harness/bin/_runtime/`，生成精简
  `_shared.py`（去除原文件顶层读取 VERSION / 检查 templates/ 的副作用），写两个可执行
  entry 脚本（`audit` / `memory`，Python shebang）
- **initializer.initialize_project** 末尾自动调用 `install_runtime`
- **upgrade.execute_upgrade** 末尾自动调用 `install_runtime` — 覆盖式刷新 _runtime 模块
  和 entry 脚本（视为框架资产，无用户数据）
- **audit_cli.py + memory.py** 新增 `main(argv=None)` 函数，供 bin entry 独立调用；
  `harness audit` / `harness memory` 通过 cli.py 的路径不受影响
- **scripts/dogfood.py** 增加 `install_runtime(ROOT)` 步骤——本仓库每次 dogfood 自动
  刷新 bin/_runtime
- **模板调用替换**：3 个 .tmpl（task-lifecycle / memory-index / lfg）里的
  `harness audit/memory` 换成 `.agent-harness/bin/audit/memory`
- **新测试 `tests/test_runtime_bin.py`**（10 条端到端契约）：
  - init 创建 bin 目录 + entry 脚本 + _runtime 模块
  - `_runtime/*.py` 必须纯 stdlib（ast 层面强制）
  - bin/audit append/tail/rejects-invalid 在无 harness CLI 环境下跑通
  - bin/memory rebuild 在无 harness CLI 环境下跑通
  - upgrade 覆盖式刷新 _runtime 和 entry 脚本
- **原则确立**：`harness` CLI 面向**项目维护者**（init/upgrade/doctor/...）；
  `.agent-harness/bin/` 面向**项目使用者**（AI 工作流调的所有命令）

### Added — squad Tier 0 Watchdog（Issue #22，#19 拆分阶段 2 收官）

- **新模块 `src/agent_harness/squad/watchdog.py`**（199 行）：纯函数 + 依赖注入设计
  - `detect_failures` / `run_watchdog_tick` / `watch_tick_with_report` / `is_skipped`
  - 失联状态从 mailbox 事件流反查（沿用"三源对账推导状态"原则），不引入外挂状态文件
  - 依赖注入（`session_exists_fn` / `list_windows_fn`）便于测试替换 + 真实 tmux 调用解耦
- **`tmux.session_exists` + `build_has_session_cmd`**：基于 `tmux has-session -t <X>` 的存活探测
- **mailbox `KNOWN_TYPES` 扩展**：`session_lost` / `worker_crashed` / `watch_exited`
- **`coordinator.cmd_watch` 集成**：每 tick 末尾跑 watchdog；done 检查优先于 watchdog 退出（避免任务完成时 kill session 被误判）
- **sentinel 关闭机制**：`touch .agent-harness/.watchdog-skip` 完全静默 watchdog（沿用 context-monitor 模式）；watch 主循环不受影响
- **本期范围声明**：不实现 pid 检查（worker 当前不写 pid）、不实现自动重启（capability 切换+worktree 状态判断复杂度过高）；留给后续 Issue
- **新测试 `tests/test_squad_watchdog.py`**（19 条）：sentinel skip / session_lost 一次性 / worker_crashed 幂等 / done & 未 spawned 不误报 / 多 worker 同 tick crash / KNOWN_TYPES 注册 / 重启场景退出独立 / 异常隔离

### Fixed — squad watchdog 深度评审两处潜在 bug

- **session_lost 幂等去重导致重启 watch 死循环**：旧实现把"是否写新事件"和"是否退出 watch"耦合在 `detect_failures` 的返回值上。session 暂死 → 报 session_lost → watch 退出 → 用户重启 cmd_watch → 旧记录让 `_session_lost_already_reported=True` → detect 返回空 → cmd_watch 误以为 session 还在 → 空转死循环。修复：`watch_tick_with_report` 退出判定独立于事件去重，每次直接探测 `session_exists`
- **watchdog 内部异常会让 cmd_watch 整个崩溃**：`mb.append_event` / subprocess 抛异常会冒泡到主调度循环。修复：`watch_tick_with_report` 整体 try/except 兜底，故障打印警告 + 保守返回 False，不传播
- **新增 5 条契约测试**保护回归：`test_exits_when_session_dead_even_if_already_reported`、`test_no_exit_when_session_alive_and_no_failures`、`test_sentinel_skip_does_not_force_exit`、`test_exception_in_session_probe_is_swallowed`、`test_exception_in_list_windows_is_swallowed`
- **新沉淀 2 条教训到 `lessons.md`**：`[架构设计] 幂等去重和退出判定不能共用同一个返回值`、`[流程] 辅助监控模块必须有异常隔离边界`

### Added — 多 agent 日志隔离（Issue #14，吸收自 MemPalace）

- **新模块 `src/agent_harness/agent.py`**（233 行）：`init_agent / diary_append / status_set / status_read / list_agents / aggregate`，fcntl LOCK_EX + O_APPEND 并发 append 安全；status 用 LOCK_EX + truncate 原子覆盖；agent id 规范 `^[a-z0-9][a-z0-9-]{0,30}$`（与 /squad 一致）
- **新 CLI `harness agent`**（`agent_cli.py`）：`init / diary / status / list / aggregate` 五个子命令
- **目录结构**：`.agent-harness/agents/<id>/{diary.md, status.md}`，每个子 agent 独立空间避免并发覆盖
- **技能模板更新**：`/dispatch-agents` 和 `/subagent-dev` 末尾新增"子 agent 日志隔离"段，指导 id 规范 + 禁止直接写 current-task
- **task-lifecycle 规则新增"并行子 agent 的日志隔离"**，与 WAL 段配套
- **upgrade 策略**：`.agent-harness/agents/*` 列入 `skip`（用户数据保留）
- **附带修复**：`cli.py:main` 原先丢弃 handler 返回码，改为 `sys.exit(rc)` 透传；agent CLI 的 `init BAD!` 现在正确返回 exit 2
- **新测试 `tests/test_agent.py`**（25 测试）：init 幂等 + id 规范（拒绝大写/shell 元字符/超长）+ diary 追加/UTF-8/自动创建 + status set/read/overwrite + list 排序/过滤非法目录 + aggregate 全量/子集/空 + 并发 10×20 无丢失 + CLI 端到端 + upgrade skip 契约 + squad 边界不相交
- **与 /squad 的边界**：文档明确——`/squad` 重型（tmux + worktree + capability）仍用 `squad/<task>/workers/`；轻型 `/dispatch-agents` 和 `/subagent-dev` 用 `agents/<id>/`

### Added — 会话保护 hooks（Issue #13，吸收自 MemPalace）

- **Stop hook** (`.claude/hooks/stop.sh`)：AI 即将停止时检查 `.agent-harness/current-task.md`，若有 `- [ ]` 未勾选 且 无"状态：待验证" 则 block（顶级 JSON `{"decision":"block","reason":...}`），要求 AI 先把进度写到 current-task.md
- **人工放行机制**：`touch .agent-harness/.stop-hook-skip` → 下次 Stop 跳过检查。替代 MemPalace 原方案中的 `stop_hook_active` 字段（经 `/source-verify` 确认 Claude Code 文档仅 SubagentStop 保证该字段，Stop 事件无保证）
- **PreCompact hook** (`.claude/hooks/pre-compact.sh`)：压缩前自动 append 一条 audit 检查点（复用 Issue #12 的 `audit.jsonl`），并 stderr 输出软提示要求 AI 把关键决策持久化。Claude Code 文档明确 PreCompact 无 decision control，本实现不尝试 block
- **`settings.json.tmpl` 新增两个 event 注册**：Stop 不带 matcher（文档明确静默忽略），PreCompact 也不带 matcher（捕获 manual + auto）
- **新测试 `tests/test_hooks.py`**（16 测试）：正常/边界/错误/skip sentinel/JSON 多行 reason 合法性/stdin 消费/audit 副作用/stderr 注入/settings 结构契约（含 Stop 不得有 matcher 的 source-verify 锚定）
- **自我保护测试**：框架 dogfood 自身后，当前 session 有未完成 checkbox 会被自己的 hook 拦住 → 引入 `.stop-hook-skip` sentinel 兜底
- **与 Issue #12 协作**：PreCompact 直接复用 audit.jsonl 基础设施形成"变更审计 + 压缩 checkpoint"闭环

### Added — 关键文件变更审计（WAL，Issue #12，吸收自 MemPalace）

- **新模块 `src/agent_harness/audit.py`**（277 行）：`append_audit / read_all / tail / stats / truncate_before`，fcntl LOCK_EX + O_APPEND 保证并发安全；agent 身份从 `HARNESS_AGENT` env 读取，默认 `unknown`；op 四选一（create / update / append / delete）；只追踪 `current-task.md` / `task-log.md` / `lessons.md`
- **新 CLI `harness audit`**（audit_cli.py，95 行）：`append / tail / stats / truncate` 四个子命令，JSON 输出选项，中文 + emoji summary 不转义
- **task-lifecycle 规则新增"关键文件变更审计（WAL）"段**：告知 AI 修改三个关键文件后追加审计记录
- **upgrade 策略**：`.agent-harness/audit.jsonl` 列为 `skip`，保留用户日志
- **init 模板**：`.agent-harness/audit.jsonl.tmpl`（空文件）作为初始化占位
- **新测试 tests/test_audit.py**（20 个）：append/tail/stats/truncate 全路径、UTF-8 + emoji、agent 来源三态、反面校验（非法 file/op）、并发 10×20 无丢失、malformed 行容错、CLI 端到端、upgrade skip 契约
- **最小实现原则**：沿用 `/squad/state.py` 的 fcntl 锁模式，复用 2026-04-12 "文件锁顺序必须先锁再 truncate" 教训；不做自动 rotation（手动 `truncate --before`），不 hook 强制（agent 自觉调用，降低绑定）

### Changed — /lfg 技能覆盖完整化（2026-04-13）

- **/lfg 流水线串起全部 33 条命令**（30 superpowers + 3 common）：补接入 `/recall`（阶段 0.2 分层加载）、`/use-worktrees` + `/careful`（阶段 1 + 回滚点）、`/source-verify` + `/todo`（阶段 3 API 验证 + 任务拆分）、`/subagent-dev`（阶段 4 选型）、`/request-review` + `/receive-review`（阶段 5/6 结构化评审循环）、`/verify`（阶段 7 验证）、`/finish-branch`（阶段 10 收尾）
- **阶段 0.1 新增运维任务分流表**：用户问"初始化项目 / 升级 / doctor / export / stats / sync / memory rebuild / squad / health / retro / lint-lessons / evolve" 时 /lfg 会告知对应 CLI 或元技能入口，而非错误地拉进开发流水线
- **阶段 0.2 从全文加载改为分层加载**：默认读 `memory-index.md`（L1）+ L0 规则；L2/L3 通过 `/recall` 和 `/recall --refs` 按需检索。与 `task-lifecycle` 规则和 ADR 0001 对齐
- **回滚机制加 /careful 拦截**：`git reset --hard` 前强制走一轮确认，展示将丢弃的 commit 和未推送改动
- **lfg.md.tmpl 末尾新增"技能覆盖清单"**：按阶段列出每个技能的接入点，未来新增技能有自检锚点
- **新增 tests/test_lfg_coverage.py**（5 测试）：锁死 EXPECTED_IN_LFG（26 个必须接入）和 EXPECTED_NOT_IN_LFG（7 个明确豁免）契约，每个技能都必须被分类——防止新技能被沉默遗漏

### Fixed — 代码健康审计（2026-04-13）

- **squad/cli.py 模块拆分**：303 → 220 行，辅助函数（`_SQUAD_CONTEXT_TEMPLATE`、worktree provision、settings/prompt 渲染、通用 `run_check`）抽到新模块 `squad/worker_files.py`。修复 AGENTS.md 280 行硬规则违反
- **check_repo.py 守卫根因修复**：`check_module_sizes` 从白名单改为 `PKG.rglob("*.py")` 自动发现，覆盖 `src/agent_harness/` 下所有 `.py`（含 `squad/` 及未来新增子包）。白名单曾漏掉 `squad/` 整个包，导致 303 行违规悄悄通过
- **Makefile check 递归化**：`py_compile $(PACKAGE)/*.py` 改为 `compileall -q $(PACKAGE)`，修复 glob 漏扫 `squad/` 子目录
- **tmux.py 一致性修复**：`ensure_tmux_available` 从 `shutil.which` 拿到的 `path` 实际用于 `subprocess.run`，不再与探测结果脱节
- **新增 tests/test_check_repo.py**（4 测试）锁死：新模块自动进入 280 检查 / squad/ 子包被覆盖 / `__init__.py` 与 `templates/` 被豁免 / check_repo.py 端到端干净通过

### Added — /squad 多 agent 常驻协作 MVP（Issue #18，阶段 1）

- **`harness squad create|status|attach|stop` CLI**：按 YAML spec 在 tmux 中启动 N 个带独立 worktree 的 Claude Code worker
- **Capability 分权**：scout（只读探索）/ builder（读写实现）/ reviewer（只读审查），通过 `.claude/settings.local.json` 的 `permissions.deny` 运行时强制
- **双隔离**：tmux session（每 worker 一 window）+ git worktree（每 worker 一 worktree），互不污染
- **共享状态**：`.agent-harness/squad/<task_id>/{manifest.json, status.jsonl, workers/<name>/}`，fcntl 文件锁保证并发写安全
- **Worker 启动方式**：`claude --append-system-prompt "$(cat squad-context.md)" "$(cat task-prompt.md)"` — system prompt 装 squad 约束（含 5 条硬规则），positional arg 装任务
- **安全约束**：worker 名 / task_id 强制 `^[a-z0-9][a-z0-9-]{0,30}$` 防 shell 注入；禁止嵌套 squad；禁止写共享 lessons.md
- **与 `/dispatch-agents` 并存**：dispatch 适合 3+ 短独立子任务（一次性 map-reduce）；squad 适合长任务、需实时观察、需角色分权
- **技能文档 + 决策树**：`/squad` 进入 which-skill 决策树、superpowers-workflow 技能表、lfg 实施阶段选项
- **阶段 1 限制**：tmux 硬依赖（Windows 用 WSL）；无依赖触发（`depends_on` 仅做循环校验，所有 worker 同时启动）；无自动合并（走 `/finish-branch`）；SQLite mailbox/FIFO 合并队列等留给阶段 2/3
- **测试**：206 → 226（+20）覆盖 YAML 解析 / 依赖环检测 / 名称注入防护 / 3 种 capability 权限渲染 / JSON 可序列化 / tmux 命令构造 / shell 元字符防护 / tmux 可用性探测
- **源验证纠偏**：`/source-verify` 发现 Claude Code CLI **没有** `--prompt-file` flag，改用 `--append-system-prompt` + positional argument（plan 原假设已纠正，附录记录）

### Changed — lessons.md 分类分区（Issue #11, inspired by MemPalace）

- **lessons.md 顶部分类索引**：6 类（测试 / 模板 / 流程 / 工具脚本 / 架构设计 / 集成API），每类列 anchor 链接
- **条目 heading 统一格式**：`## YYYY-MM-DD [分类] 一句话标题`。分类前缀不破坏 `memory.py` 扫描（对正则透明），memory-index "最近教训" 自然带分类
- **`/compound` 更新**：第 4 步条目格式改为新规范；可用分类表替换为 6 类；新增第 4.5 步"维护分类索引"，建立 lessons + index + memory-index 三处一致性铁律
- **现有 10 条教训迁移**：全部加上分类前缀，顶部索引填充完毕
- **测试**：203 → 206（+3）覆盖分类前缀保留、多分类混合、不规范格式不崩溃（锁死 memory.py 对 body 内容的透明契约）
- **最小实现原则**：不拆多文件、不改 memory.py、不加 `/recall --category`（grep 已够用）。遵循 2026-04-12 "脚手架项目吸收外部思想要选最小实现" 教训

### Added — agent-skills 增量吸收（Issue #16，续 Issue #6）

- **`/source-verify` 新技能**：`DETECT → FETCH → IMPLEMENT → CITE` 四阶段流程。防止 AI 凭训练数据编框架 API，要求代码附上官方文档 URL。含 6 条反合理化表
- **`.agent-harness/references/` L2 参考清单**：4 个 checklist（accessibility / performance / security / testing-patterns）。序言汉化，行业术语（LCP/TTFB/WCAG/OWASP 等）保留英文。通过 `/recall --refs <关键词>` 定向检索
- **Context Hierarchy 理论章节**：`task-lifecycle.md` 顶部新增 5 级上下文层级（Rules / Specs+Hot / Warm / Cold / Conversation），对应本项目 L0-L4 映射和操作准则
- **/recall 扩展**：默认范围扩到 `lessons + task-log + references`；新增 `--refs` flag 只搜参考清单
- **memory-index 升级**：自动扫描 references/ 输出"## 参考资料"段
- **类型规则引用清单**：backend-service → security + performance（Backend 段）；web-app → accessibility + performance
- **upgrade 策略**：references/* 列为 `three_way`（允许用户定制 + 保留上游更新）
- **决策树/workflow 更新**：`/source-verify` 和 `/recall` 进入 which-skill 决策树和 superpowers-workflow 技能表
- **测试**：192 → 203（+11）覆盖 references 生成/升级保留/英文术语、/source-verify 存在性+反合理化表、memory rebuild 扫描 references、Context Hierarchy 章节、/recall --refs 文档

## [1.1.1] - 2026-04-12

### Added — 分层记忆加载（Issue #10, absorbed from MemPalace）

- **L0-L3 分层记忆**：`.agent-harness/memory-index.md` 作为 L1 热索引；`task-lifecycle` 规则默认只读索引（~200 tokens 预算稳定），不再全量读 lessons.md / task-log.md
- **新技能 `/recall`**：按关键词检索 lessons.md + task-log.md，支持 `--lessons` / `--history` / `--all` 参数
- **新 CLI `harness memory rebuild`**：从现有 lessons/task-log 扫描重建 memory-index.md（老项目 bootstrap 或索引重置）
- **`/compound` 增强**：写新教训时自动同步 memory-index.md（原子 commit 要求）
- **升级策略**：memory-index.md 列为 skip，保留用户编辑
- **测试**：176 → 192（新增 16 个覆盖 rebuild、升级 skip、技能文档、规则措辞）
- **ADR 0001**：记录方案 C（Index + 按需展开）决策及替代方案

## [1.1.0] - 2026-04-09

### Added

- **三方合并升级**：`harness upgrade apply` 现在使用存储基线 + 三方合并，自动保留用户在 `AGENTS.md`、`docs/*.md` 等文件中的手动编辑。冲突时插入 `<<<<<<< 当前内容` 标记并醒目提示
- **文件四级分类**：overwrite（纯模板）、skip（用户数据）、three_way（混合文件）、json_merge（配置文件）
- **基线存储**：init/upgrade 时自动存储渲染结果到 `.agent-harness/.base/`，为后续三方合并提供基准
- **冲突检测**：`verify_upgrade` 自动扫描未解决的冲突标记并警告
- **自动计数守卫**：`make check` 自动校验文档中的测试数和技能数与实际一致
- **技能文档覆盖守卫**：`make check` 自动校验每个技能在 workflow/决策树/evolve/usage-guide 中都有条目

## [1.0.0] - 2026-04-08

### Highlights

框架从项目脚手架工具升级为**完整的 AI 工程方法论平台**。集成 31 项工作流技能，实现知识驱动的自我进化闭环（当时基线；当前技能数以最新条目为准）。

### Added

- **31 项工作流技能命令**（当时基线，后续增量见顶部条目），融合 3 个开源项目 + 2 个吸收项目 + 2 个本地原创：
  - 来自 [obra/superpowers](https://github.com/obra/superpowers)（14 个）：brainstorm, write-plan, tdd, debug, execute-plan, subagent-dev, dispatch-agents, request-review, receive-review, use-worktrees, finish-branch, write-skill, verify, which-skill
  - 来自 [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)（6 个）：ideate, compound, multi-review, lfg, git-commit, todo
  - 来自 [garrytan/gstack](https://github.com/garrytan/gstack)（5 个）：cso, health, retro, doc-release, careful
  - 吸收自 [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)（1 个）：spec（规格驱动开发）+ 反合理化机制增强
  - 吸收自 [joelparkerhenderson/architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record)（1 个）：adr（架构决策记录）
  - 本地原创（2 个）：lint-lessons（灵感来自 Karpathy 的 LLM Wiki 模式）、evolve
- **`/lfg` 全自主流水线**：知识驱动的 10 阶段自动化流水线（理解→环境→构思→计划→实施→评审→修复→验证→沉淀→收尾），支持 4 条复杂度通道（快速/轻量/标准/完整），支持 Issue ID 输入
- **`/evolve` 自我进化系统**：自动搜索 GitHub + Web 上的新 AI 编码工具项目，评估独特性，创建 Issue 提案
- **每日进化 GitHub Actions**：`.github/workflows/daily-evolution.yml`，每天自动搜索并创建进化报告 Issue
- **SessionStart hook 自动重建进化定时任务**：打开 Claude Code 时自动检测并重建 `/evolve` cron
- **`/lint-lessons` 知识库健康检查**：6 项检查（去重/矛盾/过时/孤立/覆盖度/交叉引用），0-10 评分
- **`/multi-review` 多人格评审**：6 角色并行（正确性/测试/可维护性/规范/安全/性能），P0-P3 分级
- **`/cso` 安全审计**：14 阶段安全分析（OWASP + STRIDE + secrets 考古 + 供应链）
- **Dogfood 机制**：框架对自身运行 init，`make dogfood` 同步模板产物，`make check` 自动检测漂移
- **上游同步工具**：`make sync-superpowers` 支持 3 个上游源的变更检测
- **`--no-superpowers` 选项**：可关闭工作流技能，只生成基础文档和规则
- **外部工具集成**：codex-plugin-cc 作为可选交叉评审

### Changed

- 预设系统增加 `workflow_skills_summary` 字段，按项目类型推荐重点技能
- AGENTS.md 模板新增"快速开始"段落，突出 `/lfg` 入口
- 升级流程支持 superpowers 模板的增量更新

### Infrastructure

- 516 个回归测试（含技能存在性、占位符、决策树完整性、分层记忆、lessons 分类前缀契约、check_repo 自动发现契约、security 输入校验、Issue #22 squad watchdog 19 条契约：14 基础场景 + 5 评审修复回归保护、Issue #24 项目内嵌运行时 10 条端到端契约、/digest-meeting 12 条）
- `scripts/dogfood.py`：作用域化的自举同步（只同步 commands/rules/hooks/settings）
- `scripts/sync_superpowers.py`：三上游源同步工具
- `.github/workflows/daily-evolution.yml`：每日自动进化搜索

---

## [0.5.0] - 2026-04-07 (pre-superpowers)

初始版本。提供探测、评估、初始化、升级四种能力。9 种项目类型 preset。插件机制。Doctor/Export/Stats 运维命令。
