# AGENTS

把这个文件当成入口，不要把它写成百科全书。详细信息放到 `docs/` 和 `src/agent_harness/`。

## 开始前先看什么

1. 先读 `README.md` 了解仓库目标和主命令。
2. 改初始化逻辑前，读 `docs/product.md`。
3. 改模板或目录结构前，读 `docs/architecture.md`。
4. 准备提交改动前，读 `docs/workflow.md`。
5. 运行脚本或排障前，读 `docs/runbook.md`。
6. 准备提 PR 或发版本前，读 `CONTRIBUTING.md` 和 `docs/release.md`。

## 默认工作流

1. 先用一句话重述你要改什么。
2. 只打开和任务相关的文件，不要全仓乱扫。
3. 先做最小改动，再补测试，再补文档。
4. 用 `make check` 做静态自检。
5. 用 `make test` 跑行为回归。
6. 如果改了行为或约束，必须同步更新 `docs/`。

## 硬规则

- `AGENTS.md` 保持简短，超过 120 行就该拆分。
- 框架行为变化必须更新 `docs/product.md`。
- 模板结构变化必须更新 `docs/architecture.md`。
- 初始化或探测命令变化必须更新 `docs/runbook.md`。
- 新脚本要接入 `Makefile`，不要发明隐藏命令。
- 新规则优先写成可执行校验，不要只写成口头提醒。
- `/squad` worker **禁止递归**：worker 内不得再调用 `/squad create` 或 `/dispatch-agents`（防止无限派生）。
- `/squad` worker **禁止写共享 lessons**：不得写 `.agent-harness/lessons.md`；有教训只能写到 `.agent-harness/squad/<task_id>/workers/<name>/lessons.pending.md`，由 coordinator 合并。

## 常用命令

```bash
make check
make test
make ci
harness init /path/to/repo
harness init /path/to/repo --assess-only
harness upgrade plan /path/to/repo
harness upgrade apply /path/to/repo
harness doctor /path/to/repo
harness export /path/to/repo
harness stats /path/to/repo
harness sync /path/to/service --meta /path/to/meta
harness sync --all
harness memory rebuild .
harness squad create spec.json  # 或项目自带：.agent-harness/bin/squad create spec.json
harness squad status
harness audit append --file lessons.md --op append --summary "..."
harness audit tail
harness agent init agent-1
harness agent diary agent-1 "开始子任务"
harness agent aggregate
```

## 快速地图

- `src/agent_harness/cli.py`：统一 CLI 入口。
- `src/agent_harness/init_flow.py`：交互/非交互初始化流程。
- `src/agent_harness/doctor.py`：健康检查。
- `src/agent_harness/export.py`：项目画像导出。
- `src/agent_harness/stats.py`：任务统计。
- `src/agent_harness/sync_context.py`：跨服务上下文同步。
- `src/agent_harness/sync_render.py`：服务上下文 Markdown 渲染。
- `src/agent_harness/_shared.py`：共享常量、工具函数和守卫。
- `src/agent_harness/memory.py`：分层记忆索引维护（`harness memory rebuild`）。
- `src/agent_harness/audit.py` + `audit_cli.py`：关键文件变更审计（`harness audit append/tail/stats/truncate`）。
- `src/agent_harness/agent.py` + `agent_cli.py`：多 agent 日志隔离（`harness agent init/diary/status/list/aggregate`）。
- `src/agent_harness/discovery.py`：项目探测。
- `src/agent_harness/assessment.py`：接入评估。
- `src/agent_harness/upgrade.py`：升级规划和验证。
- `src/agent_harness/initializer.py`：初始化主流程（含插件渲染）。
- `src/agent_harness/templates/common/`：生成到目标项目的骨架文件（含 .claude/rules/、4 个 common 命令、L2 参考清单 references/）。
- `src/agent_harness/presets/`：9 种项目类型预设。
- `tests/`：框架回归测试（516 个，覆盖探测、评估、初始化、升级、CLI、技能、meta sync、类型差异化、分层记忆、L2 参考清单、/source-verify、lessons 分类前缀、squad、watchdog、security、GSD 吸收契约）。
- `scripts/check_repo.py`：框架仓库守卫。
