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

初始化 harness（交互模式会依次问项目名称、目标、类型等）：

```bash
harness init /path/to/repo
```

如果要基于现有技术框架创建（复制框架代码 + 初始化 harness）：

```bash
harness init /path/to/new-project --scaffold ~/frameworks/vue-admin-template
```

交互模式下也会自动问是否基于框架创建，不需要记参数。

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

## 初始化后的首次使用

初始化完成后，打开 Claude Code（或其他 AI 工具）进入项目目录即可。AI 会自动读取 `.agent-harness/current-task.md` 中预填的"分析项目并补全文档"任务，自动完成：
- 分析项目源码，理解架构和模块划分
- 补全 docs/ 中所有"待补充"占位符
- 验证命令是否可执行

完成后任务自动归档到 task-log.md，不需要任何额外操作。

## 日常运维命令

初始化完成后，可以用以下命令管理 harness：

```bash
# 健康检查：task-log 使用率、教训积累、待补充数
harness doctor /path/to/repo

# 导出项目画像（给新人或换 agent 时用）
harness export /path/to/repo
harness export /path/to/repo -o snapshot.md
harness export /path/to/repo --json

# 任务数据统计：总数、返工率、活跃度
harness stats /path/to/repo
```

## 插件机制

在目标项目中创建 `.harness-plugins/` 目录，可添加自定义规则和模板：

```
.harness-plugins/
  rules/
    team-security.md     # 初始化时合并到 .claude/rules/
  templates/
    docs/custom-guide.md # 初始化时渲染到项目中
```

插件文件支持 `{{project_name}}` 等模板变量。

## 初始化后会生成什么

- `AGENTS.md` / `CLAUDE.md` / `CLAUDE.local.md.example` / `CONTRIBUTING.md`
- `docs/`：product、architecture、workflow、runbook、release
- `.claude/rules/`：safety、database、api、testing、autonomy
- `.agent-harness/`：project.json、current-task、task-log、lessons、init-summary
- `.github/`：PR 模板、Issue 模板

## 配置自动发现

如果目标仓库根目录下有 `.harness.json` 文件，`harness` 命令会自动读取作为默认配置。格式与 `examples/init-config.example.json` 相同。

优先级：CLI 参数 > `--config` 文件 > `.harness.json` > 自动探测值

## 为什么做成框架而不是样例项目

- 避免样例业务代码污染真实项目上下文
- 让新项目和存量项目都能接入
- 让"初始化项目认知"成为显式步骤
- 让后续需求迭代都落在同一套仓库内知识源上
