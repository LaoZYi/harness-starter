# AGENTS

把这个文件当成入口，不要把它写成百科全书。详细信息放到 `docs/`、`templates/` 和 `src/agent_harness/`。

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
make discover TARGET=.
make assess TARGET=.
make upgrade-plan TARGET=/path/to/repo ARGS="--config examples/init-config.example.json"
make upgrade-apply TARGET=/path/to/repo ARGS="--config examples/init-config.example.json"
make init TARGET=/path/to/repo ARGS="--config examples/init-config.example.json --non-interactive"
```

## 快速地图

- `src/agent_harness/discovery.py`：项目探测。
- `src/agent_harness/assessment.py`：接入评估。
- `src/agent_harness/upgrade.py`：升级规划。
- `src/agent_harness/initializer.py`：初始化主流程。
- `templates/common/`：生成到目标项目里的骨架文件。
- `presets/`：项目类型预设。
- `examples/init-config.example.json`：初始化配置示例。
- `tests/test_discovery.py`：探测逻辑回归。
- `tests/test_initializer.py`：初始化逻辑回归。
- `tests/test_init_script.py`：脚本入口回归。
- `tests/test_upgrade.py`：升级规划回归。
- `scripts/check_repo.py`：框架仓库守卫。
- `CONTRIBUTING.md`：贡献说明。
- `docs/release.md`：发布清单。
- `docs/runbook.md`：运行手册。
