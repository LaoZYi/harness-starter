# 架构约束

## 设计哲学：Environment Engineering

本项目的核心论点与 [holaboss-ai/holaOS](https://github.com/holaboss-ai/holaOS) 的 "Environment Engineering" 同源：**与其优化 prompt，不如优化 Agent 运行的环境**（文件系统、工具集、记忆机制、规则约束）。

具体而言：
- **33 个工作流技能** = Agent 的工具集（覆盖构思→设计→实施→评审→沉淀全生命周期）
- **10 层通用规则**（safety / testing / autonomy / context-budget / task-lifecycle / agent-design / documentation-sync / error-attribution / api / database）= Agent 的行为约束，其中 api / database 仅对 backend-service / library 等相关类型生成
- **三层记忆**（memory-index L1 / lessons+references L2 / task-log L3）= Agent 的持久化状态
- **hooks**（session-start / stop / pre-compact / context-monitor）= Agent 的生命周期感知

本项目与 holaOS 的区别：holaOS 自建 Electron 运行时 + workspace 模型，本项目**不自建运行时**，而是为已有的 Coding Agent（Claude Code、Cursor 等）提供 workflow 模板——通过 `harness init` 生成到目标项目的 `.claude/` 配置。两者解决同一问题（让 Agent 从"一次性任务执行"升级为"持续进化的协作者"），但技术路径不同。

> 关于 "Agent Harness" 一词：在 holaOS 中它指 runtime 内的 executor 插入边界；在本项目中它指**生成到目标项目的知识骨架和工作流模板**。两者语义不同，使用时注意上下文区分。

## 模块职责

### CLI 层
- `src/agent_harness/cli.py`：统一入口，argparse 子命令注册和路由，不超过 280 行。
- `src/agent_harness/cli_answers.py`：answer 解析（`resolve_answers` + `load_project_json`）。优先级 `CLI > .harness.json > .agent-harness/project.json > profile(discover) > None`。归一化 project.json 的 rendered schema（`project_summary` / `commands.*`）到 answers 扁平键。见 GitLab Issue #20。
- `src/agent_harness/init_flow.py`：交互式和非交互式初始化流程（从 cli.py 拆出）。
- `src/agent_harness/_scaffold_git.py`：`harness init --scaffold <git_url>` 的远端 git 拉取（shallow clone + `--scaffold-ref` branch/tag + `--scaffold-subdir` 子目录选择 + subdir 路径遍历防护）。
- `src/agent_harness/_scaffold_cmd.py`：`harness init --scaffold-cmd "<命令>"` 的脚手架命令执行（`shlex.split` + argv 列表 + `subprocess.run(shell=False)` + stdio 透传父终端 + `shutil.which` 预检；与 `--scaffold` argparse 互斥）。支持 `npm create vite@latest` / `npx create-next-app` / `cargo init` / `django-admin startproject` / `poetry new` 等主流脚手架。见 ADR 0004。

### 核心功能层
- `src/agent_harness/discovery.py`：扫描目标项目并给出结构化画像。
- `src/agent_harness/assessment.py`：根据画像给出接入评分、缺口和建议。
- `src/agent_harness/initializer.py`：整合探测结果、预设和用户输入，渲染模板并生成文件。含插件渲染逻辑。
- `src/agent_harness/upgrade.py`：比较模板生成结果与现有文件，给出升级计划并执行。含文件分类（overwrite/skip/three_way/json_merge）和基线存储。`CLAUDE.md` 从 overwrite 改为 three_way（GitLab Issue #20），升级时保留用户在 CLAUDE.md 中加的本地备注。`three_way` 分支在 base 基线缺失时**不退化为 overwrite**，改写 `<file>.harness-new` 旁路文件保护用户内容（GitLab Issue #23），通过 `--force` 逃生；`UpgradeExecutionResult.missing_base_files` 列出所有走保护分支的文件。
- `src/agent_harness/upgrade_verify.py`：upgrade 后置校验。检查 AGENTS.md 长度、project.json 合法性、占位符未填、合并冲突残留；以及**sentinel 回落检测**（GitLab Issue #20）——若 project.json 的 `project_summary` 已填写但 `AGENTS.md` / `CLAUDE.md` / `docs/product.md` 里仍出现「待补充项目目标」，说明 answers 解析或变量替换失败，发出 warning。
- `src/agent_harness/_merge3.py`：三方合并算法。merge3() 做行级文本合并，json_merge() 做 JSON 结构化合并。冲突时插入 `<<<<<<< 当前内容` 标记。
- `src/agent_harness/templating.py`：模板发现、占位符替换和落盘。
- `src/agent_harness/sync_context.py`：跨服务上下文同步（读取 meta repo、分发共享插件、分发领域知识）。相对路径基于 meta_root 解析。
- `src/agent_harness/sync_render.py`：服务上下文 Markdown 渲染（generate_service_context_md、generate_microservice_rule）。从 sync_context 拆出的纯函数。

### 运维工具层
- `src/agent_harness/doctor.py`：健康检查（task-log 使用率、教训积累、占位符、长度）。
- `src/agent_harness/export.py`：项目画像导出（Markdown 或 JSON）。
- `src/agent_harness/stats.py`：任务统计分析（返工率、活跃度、教训数）。

### 辅助层
- `src/agent_harness/cli_utils.py`：rich 输出函数、语言默认值映射。
- `src/agent_harness/lang_detect.py`：语言/框架/ORM 检测。
- `src/agent_harness/models.py`：数据模型（ProjectProfile、InitializationResult 等）。
- `src/agent_harness/_shared.py`：共享常量（TEMPLATE_ROOT、META_ROOT 等）、slugify、require_harness。
- `src/agent_harness/memory.py`：分层记忆索引维护（`rebuild_index()` 从 lessons/task-log/references 重建 `memory-index.md`）。
- `src/agent_harness/skills_registry.py` + `skills_lint.py`：Skills Registry SSOT（Issue #27）。`skills-registry.json` 是 36 个 skill 元数据（id/category/triggers/lfg_stage/expected_in_lfg）的单一真相源。`skills_registry.load_registry / render_decision_tree / render_skill_index_by_phase / render_lfg_coverage_table / apply_to_target` 把 `<<SKILL_*>>` 双尖括号占位符（避开 `{{var}}` jinja 冲突）替换为实际内容；initializer 和 upgrade 在材化 superpowers 模板后自动调用 `apply_to_target`。`skills_lint.run` 三检查：孤儿 .md.tmpl / 注册但缺文件 / expected_in_lfg=true 但 lfg 未引用；`harness skills lint <target>` CLI 子命令（`make ci` 串入 `make skills-lint` 守卫），新增 skill 只改 registry。
- `src/agent_harness/security.py`：统一输入安全校验（`sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`）。将 `.claude/rules/safety.md` 的信任边界从文档约束代码化为强制函数。agent.py 和 squad/spec.py 复用其 `NAME_PATTERN` 和 `sanitize_name`，消除重复正则。吸收自 MemPalace（Issue #15）。
- `src/agent_harness/audit.py`：关键文件变更审计 WAL（`append_audit / tail / stats / truncate_before`），fcntl 锁保证并发安全，只追踪 current-task / task-log / lessons 三个文件。
- `src/agent_harness/agent.py` + `agent_cli.py`：多 agent 日志隔离（`init_agent / diary_append / status_set / list_agents / aggregate`），fcntl 锁保证并发 append 无丢失；专为 `/dispatch-agents` 和 `/subagent-dev` 场景服务，与 /squad 的 workers/ 目录并列但互不相交。Issue #30 新增**知识制品（knowledge artifacts）**：`diary_append_artifact(agent_id, artifact_type, summary, content, refs)` 把 sub-agent 的发现写成结构化 Markdown 块（`## artifact` + ts/type/summary/refs/content 字段），`extract_artifacts` 用正则解析回 dict，`aggregate` 顶部集中展示所有 artifacts 供后续任务 refs 复用（compound intelligence）；CLI 入口 `harness agent artifact <id> --type <T> --summary <S> [--content <C> | --content-file <F>] [--refs a,b]`。
- `src/agent_harness/templates/common/.claude/hooks/`：Claude Code 会话保护 + 上下文监控 hooks — `session-start.sh`（打开项目时展示未完成任务 + 重置 context-monitor 计数器）、`stop.sh`（停止前检查 current-task 未勾选 checkbox，可通过 `.stop-hook-skip` sentinel 放行）、`pre-compact.sh`（压缩前追加 audit 检查点 + stderr 提示）、`context-monitor.sh`（PostToolUse 工具调用计数，50/100/150 三级阈值提醒 /compact；可通过 `.context-monitor-skip` sentinel 关闭；Issue #17 GSD 吸收降级方案，因 Claude Code statusline 不暴露 remaining_percentage）。
- `src/agent_harness/audit_cli.py`：`harness audit` 子命令的 argparse handler（append/tail/stats/truncate）。另提供 `main(argv=None)` 供项目内嵌运行时 `.agent-harness/bin/audit` 独立调用（Issue #24）。
- `src/agent_harness/runtime_install.py`：项目内嵌运行时安装器（Issue #24）。`install_runtime(target_root)` 把 `audit.py / audit_cli.py / memory.py` 复制到目标项目 `.agent-harness/bin/_runtime/`，生成精简 `_shared.py`（去除原文件顶层副作用），写 `audit` / `memory` 两个 shebang entry 脚本。让 **clone 项目的人无需装 harness CLI** 就能跑 AI 工作流里所有 audit/memory 命令。init/upgrade 时自动执行；dogfood 时也给本仓库刷新 bin。
- `src/agent_harness/squad/`：多 agent 常驻协作（阶段 1 MVP + 阶段 2 Issue #19a 依赖触发 + Issue #21 mailbox/watch + Issue #22 watchdog + Issue #30 orchestrator 角色）— `spec.py`（YAML 解析/循环检测，allowed capabilities 含 orchestrator/scout/builder/reviewer 四种）、`capability.py`（orchestrator/scout/builder/reviewer 权限渲染；Issue #30 新增 orchestrator 为"战略协调"角色，deny 所有写工具 Edit/Write/MultiEdit/NotebookEdit + 危险 Bash，只允许 Read/Grep/Glob/Task/TodoWrite 派工，对齐 Danau5tin/multi-agent-coding-system 的严格角色分权哲学）、`tmux.py`（tmux 命令构造 + 可用性检查 + `list_windows` + `session_exists`）、`mailbox.py`（SQLite WAL 模式事件存储：`append_event / read_events / done_workers / pending_worker_info / dump_to_jsonl`；索引 event_type 和 worker；KNOWN_TYPES 含 `session_lost` / `worker_crashed`；Issue #21 引入，替代 JSONL）、`state.py`（manifest 持久化 + 旧 `append_status / done_workers / pending_worker_info` 签名兼容层，内部走 mailbox）、`worker_files.py`（worktree provision + settings/prompt 渲染 + 通用 run_check）、`watchdog.py`（Tier 0 watchdog：`detect_failures / run_watchdog_tick / watch_tick_with_report` 纯函数 + 依赖注入；事件去重从 mailbox 反查实现幂等，**但 watch 退出判定独立于事件去重**——直接探测 `session_exists`，避免 session_lost 幂等记录让重启 watch 死循环；`watch_tick_with_report` 整体 try/except 兜底——watchdog 是辅助监控，内部异常（SQLite/tmux）不传播到 cmd_watch 主调度；可通过 `.agent-harness/.watchdog-skip` sentinel 关闭（仅静默失联上报，watch 主循环不受影响），沿用 context-monitor 模式；Issue #22 + 评审两次修复）、`coordinator.py`（依赖推进：`find_squad / cmd_advance / cmd_done / derive_worker_state`；`cmd_watch` 常驻进程轮询 mailbox 自动 advance + done 检查优先于 watchdog 退出 + 每 tick 末尾跑 watchdog + session 失联立即退出 + SIGTERM 优雅退出；`cmd_dump` 导出 JSONL 调试）、`cli.py`（`harness squad create|status|attach|stop|advance|done|watch|dump` 子命令，只做 CLI 调度）。`cmd_create` 按拓扑序启动 wave 0，有 `depends_on` 的 worker 写 `pending` 事件由 `advance` 或 `watch` 触发。运行时状态写目标项目的 `.agent-harness/squad/<task_id>/mailbox.db`（WAL 副文件 `.db-wal` / `.db-shm` 由模板 `.gitignore` 排除）。

### 资源层
- `src/agent_harness/templates/common/`：生成到目标项目的通用模板。含规则、4 个 common 命令（`/process-notes`、`/digest-meeting`、`/recall`、`/source-verify`）、文档、任务追踪、L2 参考清单目录（`.agent-harness/references/`）等。
- `src/agent_harness/templates/superpowers/`：结构化工作流技能模板（32 个命令 + 1 个规则），默认启用，可通过 `--no-superpowers` 关闭。融合了 obra/superpowers（14 个基础技能）、EveryInc/compound-engineering-plugin（6 个增强技能）、garrytan/gstack（5 个运维技能）、addyosmani/agent-skills（1 个吸收技能 + 反合理化增强）、joelparkerhenderson/architecture-decision-record（1 个吸收技能）、spencermarx/open-code-review（评审辩论方法论增强）和 3 个本地原创技能（lint-lessons、evolve、squad）。
- `src/agent_harness/templates/meta/`：meta 项目类型专属模板（services/registry、dependency-graph、conventions、shared-plugins、business 领域知识骨架、BEST-PRACTICES 指南、/sync-meta 和 /populate-meta 命令）。
- `src/agent_harness/templates/<type>/`：各项目类型的专属规则模板（backend-service、web-app、cli-tool、worker、mobile-app、monorepo、data-pipeline、library 各有 1 个专属规则文件）。
- `src/agent_harness/presets/`：9 种项目类型的 JSON 预设，含 `workflow_skills_summary` 指定项目类型重点技能。
- `scripts/check_repo.py`：框架仓库守卫脚本。
- `scripts/sync_superpowers.py`：上游 skills 同步工具，支持三个上游源（superpowers + compound + gstack）。
- `scripts/dogfood.py`：框架自身生成产物同步工具。

### 测试层
- `tests/`：680 个回归测试，覆盖探测、评估（含类型感知评分）、初始化、升级、CLI 集成、superpowers/compound/gstack 技能、决策树完整性、meta sync（领域分发、相对路径、安全校验、git 仓库验证、大文件跳过）、项目类型规则排除、类型专属规则生成、分层记忆加载（memory.py + /recall + memory-index）、L2 参考清单生成与升级保留（references/）、/source-verify 技能、lessons 分类前缀契约、squad 规格解析 / capability 渲染 / tmux 命令构造（82 个 squad 测试：spec/capability/tmux 单元 + 集成 dry-run 端到端，含 shell 注入防护回归 + 17 个 Issue #19a 依赖触发契约 + 18 个 Issue #21 mailbox/watch 契约：WAL 模式验证、事件读写 + 过滤、state.py 签名兼容、cmd_watch 全 done 自动退出 + max_iterations 控制 + 自动 advance、cmd_dump JSONL 导出、gitignore 模板规则 + 19 个 Issue #22 watchdog 契约：sentinel skip、session_lost 一次性、worker_crashed 幂等、done/未 spawned 不误报、多 worker 同 tick crash、KNOWN_TYPES 注册 + 评审 5 条回归保护：重启场景退出独立于事件去重、sentinel 不强制退出 watch、session probe / list_windows 异常隔离）、check_repo 守卫自动发现契约（4 条，回归保护 280 行硬规则不再依赖白名单）、security 输入校验（25 条：sanitize_name/path/content 覆盖正常、边界、路径遍历、符号链接逃逸、null 字节、控制字符、oversize）、GSD 吸收契约（18 条：StuckDetector 规则存在、/lint-lessons 矛盾检测、需求矩阵三元映射、/plan-check 8 维度 + 3 轮修订、context-monitor hook 端到端 + skip 开关、workflow 规则 + /lfg 整合）、目录导航层（14 条：documentation-sync.md 目录导航层章节、tmpl/dogfood 一致性、`/recall --map` 参数、2 个示范目录 ABSTRACT/OVERVIEW 存在性 + 长度、check_directory_maps 守卫正常/边界/错误路径——吸收自 OpenViking 的 filesystem-as-context）。

## 约束

1. 每个 Python 模块不超过 280 行。超过时拆分到新模块。
2. 模板内容必须通用，禁止引入样例业务代码。
3. 脚本逻辑和模板文本分离，禁止把长文案塞进 Python 代码。
4. CLI 新增子命令时，handler 放在独立模块，cli.py 只注册路由。
5. 自检脚本（check_repo.py）优先检查文件存在、模板连通、模块长度。

## 数据流

```
用户输入/配置
     ↓
discover_project() → ProjectProfile
     ↓
assess_project() → AssessmentResult
     ↓
prepare_initialization() → context dict (63 个模板变量)
     ↓
materialize_templates() → 写入目标项目（common 模板）
     ↓
materialize_templates() → 写入 superpowers 模板 (如果启用)
     ↓
materialize_templates() → 写入类型专属模板 (templates/<project_type>/)
     ↓
_materialize_plugins() → 渲染 .harness-plugins/ (如果存在)
     ↓
verify_upgrade() → 验证结果
```

## 插件机制

目标项目中 `.harness-plugins/` 目录的文件在 init/upgrade 时被渲染：
- `rules/*.md` → 合并到 `.claude/rules/`
- `templates/**` → 保持目录结构渲染到项目根

插件文件支持与内置模板相同的 `{{variable}}` 占位符。

## 与 Anthropic Agent Skills 的关系

Claude Code 支持三种技能形态，本项目使用第一种（Standalone Commands）：

| 形态 | 目录 | 调用方式 | 适用场景 |
|------|------|---------|---------|
| **Standalone Commands** | `.claude/commands/<name>.md` | `/<name>`（用户主动触发） | 明确的工作流步骤，需要用户按需调用 |
| **Agent Skills (SKILL.md)** | `.claude/skills/<name>/SKILL.md` | Claude 自动调用（model-invoked） | 后台辅助，模型判断何时激活 |
| **Plugin** | `<plugin>/.claude-plugin/plugin.json` + `skills/` 或 `commands/` | `/<plugin>:<name>`（强制 namespace） | 跨项目分发、marketplace 注册 |

**本项目选择 Standalone Commands 的原因**：

- 33 个工作流技能（`/lfg`、`/tdd`、`/spec` 等）都是**用户主动触发**的——开发者明确知道自己想做什么（"开始全流程"、"测试驱动开发"），不需要模型自行猜测
- 模板渲染时注入项目特定内容（`{{project_name}}`、`{{test_command}}` 等），通过 `harness init` 适配目标项目；这意味着同一技能在不同项目中的渲染结果不同，不适合以固定 plugin 形式跨项目分发
- Standalone Commands 不需要 namespace 前缀，用户直接 `/lfg` 而非 `/harness:lfg`，更简洁

**SKILL.md 规范参考**（[agentskills.io/specification](https://agentskills.io/specification)）：

如果开发者想为目标项目创建 model-invoked 形式的技能（Claude 自动判断何时激活），应遵循 Agent Skills spec：

```yaml
# .claude/skills/<skill-name>/SKILL.md
---
name: <skill-name>          # 必填，1-64 字符，小写字母+数字+连字符，等于目录名
description: <描述>          # 必填，1-1024 字符，说明做什么 + 何时使用
license: <许可证>            # 可选
compatibility: <环境要求>     # 可选
allowed-tools: <工具白名单>   # 可选，实验性
---

<Markdown 正文：技能指引>
```

`/write-skill` 技能在创建新技能时提供 SKILL.md 格式选项。

## 推荐扩展方式

- 想增加新项目类型：先加 `src/agent_harness/presets/*.json`，再补模板、评估逻辑和测试。
- 想增加新生成文件：先加模板，再补初始化测试和仓库自检。
- 想增加新 CLI 命令：新建模块放 handler，cli.py 只注册子命令，更新 runbook。
- 想增加新规则模板：放到 `src/agent_harness/templates/common/.claude/rules/`，加 paths frontmatter。
- 想增加新 Claude Code 命令：放到 `src/agent_harness/templates/common/.claude/commands/`（通用）或 `src/agent_harness/templates/superpowers/.claude/commands/`（工作流技能），文件名即命令名。
