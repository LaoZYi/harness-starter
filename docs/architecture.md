# 架构约束

## 模块职责

### CLI 层
- `src/agent_harness/cli.py`：统一入口，argparse 子命令注册和路由，不超过 280 行。
- `src/agent_harness/init_flow.py`：交互式和非交互式初始化流程（从 cli.py 拆出）。

### 核心功能层
- `src/agent_harness/discovery.py`：扫描目标项目并给出结构化画像。
- `src/agent_harness/assessment.py`：根据画像给出接入评分、缺口和建议。
- `src/agent_harness/initializer.py`：整合探测结果、预设和用户输入，渲染模板并生成文件。含插件渲染逻辑。
- `src/agent_harness/upgrade.py`：比较模板生成结果与现有文件，给出升级计划并执行。含文件分类（overwrite/skip/three_way/json_merge）、基线存储和 verify_upgrade 验证。
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
- `src/agent_harness/security.py`：统一输入安全校验（`sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`）。将 `.claude/rules/safety.md` 的信任边界从文档约束代码化为强制函数。agent.py 和 squad/spec.py 复用其 `NAME_PATTERN` 和 `sanitize_name`，消除重复正则。吸收自 MemPalace（Issue #15）。
- `src/agent_harness/audit.py`：关键文件变更审计 WAL（`append_audit / tail / stats / truncate_before`），fcntl 锁保证并发安全，只追踪 current-task / task-log / lessons 三个文件。
- `src/agent_harness/agent.py` + `agent_cli.py`：多 agent 日志隔离（`init_agent / diary_append / status_set / list_agents / aggregate`），fcntl 锁保证并发 append 无丢失；专为 `/dispatch-agents` 和 `/subagent-dev` 场景服务，与 /squad 的 workers/ 目录并列但互不相交。
- `src/agent_harness/templates/common/.claude/hooks/`：Claude Code 会话保护 hooks — `session-start.sh`（打开项目时展示未完成任务）、`stop.sh`（停止前检查 current-task 未勾选 checkbox，可通过 `.stop-hook-skip` sentinel 放行）、`pre-compact.sh`（压缩前追加 audit 检查点 + stderr 提示）。
- `src/agent_harness/audit_cli.py`：`harness audit` 子命令的 argparse handler（append/tail/stats/truncate）。
- `src/agent_harness/squad/`：多 agent 常驻协作（阶段 1 MVP）— `spec.py`（YAML 解析/循环检测）、`capability.py`（scout/builder/reviewer 权限渲染）、`tmux.py`（tmux 命令构造 + 可用性检查）、`state.py`（manifest + status.jsonl，fcntl 文件锁）、`worker_files.py`（worktree provision + settings/prompt 渲染 + 通用 run_check）、`cli.py`（`harness squad create|status|attach|stop` 子命令，只做 CLI 调度）。运行时状态写目标项目的 `.agent-harness/squad/<task_id>/`。

### 资源层
- `src/agent_harness/templates/common/`：生成到目标项目的通用模板。含规则、3 个 common 命令（`/process-notes`、`/recall`、`/source-verify`）、文档、任务追踪、L2 参考清单目录（`.agent-harness/references/`）等。
- `src/agent_harness/templates/superpowers/`：结构化工作流技能模板（30 个命令 + 1 个规则），默认启用，可通过 `--no-superpowers` 关闭。融合了 obra/superpowers（14 个基础技能）、EveryInc/compound-engineering-plugin（6 个增强技能）、garrytan/gstack（5 个运维技能）、addyosmani/agent-skills（1 个吸收技能 + 反合理化增强）、joelparkerhenderson/architecture-decision-record（1 个吸收技能）、spencermarx/open-code-review（评审辩论方法论增强）和 3 个本地原创技能（lint-lessons、evolve、squad）。
- `src/agent_harness/templates/meta/`：meta 项目类型专属模板（services/registry、dependency-graph、conventions、shared-plugins、business 领域知识骨架、BEST-PRACTICES 指南、/sync-meta 和 /populate-meta 命令）。
- `src/agent_harness/templates/<type>/`：各项目类型的专属规则模板（backend-service、web-app、cli-tool、worker、mobile-app、monorepo、data-pipeline、library 各有 1 个专属规则文件）。
- `src/agent_harness/presets/`：9 种项目类型的 JSON 预设，含 `workflow_skills_summary` 指定项目类型重点技能。
- `scripts/check_repo.py`：框架仓库守卫脚本。
- `scripts/sync_superpowers.py`：上游 skills 同步工具，支持三个上游源（superpowers + compound + gstack）。
- `scripts/dogfood.py`：框架自身生成产物同步工具。

### 测试层
- `tests/`：329 个回归测试，覆盖探测、评估（含类型感知评分）、初始化、升级、CLI 集成、superpowers/compound/gstack 技能、决策树完整性、meta sync（领域分发、相对路径、安全校验、git 仓库验证、大文件跳过）、项目类型规则排除、类型专属规则生成、分层记忆加载（memory.py + /recall + memory-index）、L2 参考清单生成与升级保留（references/）、/source-verify 技能、lessons 分类前缀契约、squad 规格解析 / capability 渲染 / tmux 命令构造（28 个 squad 测试：spec/capability/tmux 单元 + 集成 dry-run 端到端，含 shell 注入防护回归）、check_repo 守卫自动发现契约（4 条，回归保护 280 行硬规则不再依赖白名单）、security 输入校验（25 条：sanitize_name/path/content 覆盖正常、边界、路径遍历、符号链接逃逸、null 字节、控制字符、oversize）。

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

## 推荐扩展方式

- 想增加新项目类型：先加 `src/agent_harness/presets/*.json`，再补模板、评估逻辑和测试。
- 想增加新生成文件：先加模板，再补初始化测试和仓库自检。
- 想增加新 CLI 命令：新建模块放 handler，cli.py 只注册子命令，更新 runbook。
- 想增加新规则模板：放到 `src/agent_harness/templates/common/.claude/rules/`，加 paths frontmatter。
- 想增加新 Claude Code 命令：放到 `src/agent_harness/templates/common/.claude/commands/`（通用）或 `src/agent_harness/templates/superpowers/.claude/commands/`（工作流技能），文件名即命令名。
