# Changelog

## [1.0.0] - 2026-04-08

### Highlights

框架从项目脚手架工具升级为**完整的 AI 工程方法论平台**。集成 29 个工作流技能，实现知识驱动的自我进化闭环。

### Added

- **29 个工作流技能命令**，融合 3 个开源项目 + 2 个吸收项目 + 2 个本地原创：
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

- 87 个回归测试（含技能存在性、占位符、决策树完整性）
- `scripts/dogfood.py`：作用域化的自举同步（只同步 commands/rules/hooks/settings）
- `scripts/sync_superpowers.py`：三上游源同步工具
- `.github/workflows/daily-evolution.yml`：每日自动进化搜索

---

## [0.5.0] - 2026-04-07 (pre-superpowers)

初始版本。提供探测、评估、初始化、升级四种能力。8 种项目类型 preset。插件机制。Doctor/Export/Stats 运维命令。
