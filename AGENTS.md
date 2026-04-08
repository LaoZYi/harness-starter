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
```

## 快速地图

- `src/agent_harness/cli.py`：统一 CLI 入口。
- `src/agent_harness/init_flow.py`：交互/非交互初始化流程。
- `src/agent_harness/doctor.py`：健康检查。
- `src/agent_harness/export.py`：项目画像导出。
- `src/agent_harness/stats.py`：任务统计。
- `src/agent_harness/discovery.py`：项目探测。
- `src/agent_harness/assessment.py`：接入评估。
- `src/agent_harness/upgrade.py`：升级规划和验证。
- `src/agent_harness/initializer.py`：初始化主流程（含插件渲染）。
- `src/agent_harness/templates/common/`：生成到目标项目的骨架文件（含 .claude/rules/）。
- `src/agent_harness/presets/`：8 种项目类型预设。
- `tests/test_cli.py`：CLI 集成回归（82 个测试）。
- `scripts/check_repo.py`：框架仓库守卫。
