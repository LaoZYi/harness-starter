# agent-harness-framework

这是一个通用初始化框架，用来给 Codex 和 Claude Code 在任意项目里落一套稳定的 agent harness。它不自带业务案例，而是提供四种能力：

1. 探测项目现状
2. 评估接入缺口和风险
3. 生成第一版项目知识骨架
4. 把协作约束落成文档和模板

## 安装

```bash
cd agent-harness-starter
pip install -e .
```

`-e` 是 editable mode（开发模式），安装一次即可。后续框架代码更新后**无需重新安装**，因为它直接指向源码目录，改了代码立刻生效。

安装后即可在任意位置使用 `harness` 命令。

> 不想安装？也可以通过 `PYTHONPATH=src python -m agent_harness` 或 `make` 目标来使用，功能完全一样。

## 典型使用方式

先看项目探测和接入评估结果：

```bash
harness init /path/to/repo --assess-only
```

如果需要 JSON 格式输出：

```bash
harness init /path/to/repo --assess-only --json
```

如果这个项目已经接入过旧版本 harness，先看升级会影响哪些文件：

```bash
harness upgrade plan /path/to/repo
```

如果想直接看会改什么内容：

```bash
harness upgrade plan /path/to/repo --show-diff
```

如果只想升级某几个托管文件：

```bash
harness upgrade plan /path/to/repo --only AGENTS.md --only .agent-harness/project.json
```

确认没问题后，可以直接执行升级：

```bash
harness upgrade apply /path/to/repo
```

也可以只执行部分升级：

```bash
harness upgrade apply /path/to/repo --only AGENTS.md
```

再初始化 harness：

```bash
harness init /path/to/repo
```

如果想先预演、不直接写文件：

```bash
harness init /path/to/repo --dry-run
```

如果你希望把初始化参数固化到配置文件：

```bash
harness init /path/to/repo --config examples/init-config.example.json --non-interactive
```

如果目标仓库中有 `.harness.json`，参数会自动读取，无需每次传 `--config`：

```bash
harness init /path/to/repo --non-interactive
```

如果你希望一次性无交互初始化：

```bash
harness init /path/to/repo \
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

- `src/agent_harness/cli.py`：统一 CLI 入口（`harness` 命令）
- `src/agent_harness/`：探测、初始化和模板渲染逻辑
- `templates/common/`：生成到目标项目中的模板文件
- `presets/`：按项目类型给出默认文案和检查重点
- `scripts/check_repo.py`：框架仓库自检
- `examples/init-config.example.json`：配置文件初始化示例

## 配置自动发现

如果目标仓库根目录下有 `.harness.json` 文件，`harness` 命令会自动读取作为默认配置。格式与 `examples/init-config.example.json` 相同。

优先级：CLI 参数 > `--config` 文件 > `.harness.json` > 自动探测值

## 为什么做成框架而不是样例项目

- 避免样例业务代码污染真实项目上下文
- 让新项目和存量项目都能接入
- 让"初始化项目认知"成为显式步骤
- 让后续需求迭代都落在同一套仓库内知识源上
