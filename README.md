# agent-harness-framework

这是一个通用初始化框架，用来给 Codex 和 Claude Code 在任意项目里落一套稳定的 agent harness。它不自带业务案例，而是提供三种能力：

1. 探测项目现状
2. 生成第一版项目知识骨架
3. 把协作约束落成文档和模板

## 典型使用方式

先看现有项目长什么样：

```bash
python scripts/discover_project.py /path/to/repo
```

再初始化 harness：

```bash
python scripts/init_project.py --target /path/to/repo
```

如果你希望一次性无交互初始化：

```bash
python scripts/init_project.py \
  --target /path/to/repo \
  --project-name "Acme API" \
  --summary "Handle internal automation requests." \
  --project-type backend-service \
  --language python \
  --package-manager uv \
  --run-command "uv run python -m acme_api" \
  --test-command "uv run pytest" \
  --check-command "uv run ruff check ." \
  --ci-command "make ci" \
  --deploy-target docker \
  --has-production \
  --sensitivity internal \
  --non-interactive
```

## 初始化后会生成什么

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `docs/product.md`
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/runbook.md`
- `docs/release.md`
- `.agent-harness/project.json`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/*`

## 框架仓库结构

- `templates/common/`：生成到目标项目中的模板文件
- `presets/`：按项目类型给出默认文案和检查重点
- `src/agent_harness/`：探测、初始化和模板渲染逻辑
- `scripts/discover_project.py`：命令行探测入口
- `scripts/init_project.py`：命令行初始化入口
- `scripts/check_repo.py`：框架仓库自检

## 为什么做成框架而不是样例项目

- 避免样例业务代码污染真实项目上下文
- 让新项目和存量项目都能接入
- 让“初始化项目认知”成为显式步骤
- 让后续需求迭代都落在同一套仓库内知识源上
