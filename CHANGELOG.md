# Changelog

## [Unreleased]

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

- 228 个回归测试（含技能存在性、占位符、决策树完整性、分层记忆、lessons 分类前缀契约）
- `scripts/dogfood.py`：作用域化的自举同步（只同步 commands/rules/hooks/settings）
- `scripts/sync_superpowers.py`：三上游源同步工具
- `.github/workflows/daily-evolution.yml`：每日自动进化搜索

---

## [0.5.0] - 2026-04-07 (pre-superpowers)

初始版本。提供探测、评估、初始化、升级四种能力。9 种项目类型 preset。插件机制。Doctor/Export/Stats 运维命令。
