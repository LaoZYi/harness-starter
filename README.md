# agent-harness-framework

给任意项目装一套 AI Agent 协作基础设施，让 Claude Code / Codex 开箱即用。

四种核心能力：**探测**项目现状 → **评估**接入缺口 → **初始化**知识骨架 → **升级**增量更新。

## 30 秒上手

```bash
# 安装
git clone https://github.com/LaoZYi/harness-starter.git && cd harness-starter
make setup && make test

# 评估目标项目
harness init /path/to/repo --assess-only

# 初始化（交互式）
harness init /path/to/repo
```

初始化完成后，进入项目打开 Claude Code，AI 自动开始分析项目并补全文档。

## 文档导航

| 文档 | 定位 | 适合谁 |
|------|------|--------|
| [速查手册](docs/quickstart.md) | 一页纸覆盖全部功能 | 已熟悉的用户，快速查命令 |
| [完整使用手册](docs/usage-manual.md) | 19 章节详细指南 | 首次接触，需要理解每个功能 |
| [运行手册](docs/runbook.md) | CLI 命令和故障排查 | 运维和排障 |
| [产品规则](docs/product.md) | 框架能力清单和变更原则 | 贡献者 |
| [架构约束](docs/architecture.md) | 模块职责和数据流 | 贡献者 |

## 为什么做成框架而不是样例项目

- 避免样例业务代码污染真实项目上下文
- 让新项目和存量项目都能接入
- 让「初始化项目认知」成为显式步骤
- 让后续需求迭代都落在同一套仓库内知识源上
