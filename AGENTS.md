# AGENTS

把这个文件当成入口，不要把它写成百科全书。详细信息放到 `docs/`。

## 开始前先看什么

1. 先读 `README.md` 了解仓库目标和主命令。
2. 改业务行为前，读 `docs/product.md`。
3. 改代码结构前，读 `docs/architecture.md`。
4. 准备提交改动前，读 `docs/workflow.md`。
5. 准备提 PR 或发版本前，读 `CONTRIBUTING.md` 和 `docs/release.md`。

## 默认工作流

1. 先用一句话重述你要改什么。
2. 只打开和任务相关的文件，不要全仓乱扫。
3. 先做最小改动，再补测试，再补文档。
4. 用 `make check` 做静态自检。
5. 用 `make test` 跑行为回归。
6. 如果改了行为或约束，必须同步更新 `docs/`。

## 硬规则

- `AGENTS.md` 保持简短，超过 120 行就该拆分。
- 行为变化必须更新 `docs/product.md`。
- 架构变化必须更新 `docs/architecture.md`。
- 新脚本要接入 `Makefile`，不要发明隐藏命令。
- 新规则优先写成可执行校验，不要只写成口头提醒。

## 常用命令

```bash
make check
make test
make ci
make run
```

## 快速地图

- `src/triage_bot/router.py`：分流决策。
- `src/triage_bot/models.py`：领域模型。
- `tests/test_router.py`：核心行为样例。
- `scripts/check_repo.py`：文档和结构守卫。
- `CONTRIBUTING.md`：贡献说明。
- `docs/release.md`：发布清单。
