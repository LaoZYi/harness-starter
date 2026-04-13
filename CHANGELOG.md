# Changelog

## [Unreleased]

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
- **技能文档 + 决策树**：`/squad` 进入 use-superpowers 决策树、superpowers-workflow 技能表、lfg 实施阶段选项
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
- **决策树/workflow 更新**：`/source-verify` 和 `/recall` 进入 use-superpowers 决策树和 superpowers-workflow 技能表
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

框架从项目脚手架工具升级为**完整的 AI 工程方法论平台**。集成 30 个工作流技能，实现知识驱动的自我进化闭环。

### Added

- **30 个工作流技能命令**，融合 3 个开源项目 + 2 个吸收项目 + 2 个本地原创：
  - 来自 [obra/superpowers](https://github.com/obra/superpowers)（14 个）：brainstorm, write-plan, tdd, debug, execute-plan, subagent-dev, dispatch-agents, request-review, receive-review, use-worktrees, finish-branch, write-skill, verify, use-superpowers
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

- 304 个回归测试（含技能存在性、占位符、决策树完整性、分层记忆、lessons 分类前缀契约、check_repo 自动发现契约）
- `scripts/dogfood.py`：作用域化的自举同步（只同步 commands/rules/hooks/settings）
- `scripts/sync_superpowers.py`：三上游源同步工具
- `.github/workflows/daily-evolution.yml`：每日自动进化搜索

---

## [0.5.0] - 2026-04-07 (pre-superpowers)

初始版本。提供探测、评估、初始化、升级四种能力。9 种项目类型 preset。插件机制。Doctor/Export/Stats 运维命令。
