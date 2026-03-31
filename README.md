# agent-harness-starter

这是一个面向生产项目的 starter，用来给 Codex 和 Claude Code 提供一套可直接工作的仓库骨架。它不是 prompt 集合，而是把 agent 的工作环境拆成四层：

1. `AGENTS.md` 只保留短入口和执行规则。
2. `docs/` 承载产品、架构和协作细节。
3. `scripts/check_repo.py` 把关键约束变成机器可校验规则。
4. `Makefile` 和 CI 保证改动能快速自证。

## 快速开始

```bash
cd /Users/bochun/Documents/work/agent-harness-starter
make check
make test
```

本地跑一个真实输入：

```bash
printf '{"title":"service down","description":"api is unavailable","customer_tier":"enterprise","channel":"email"}' | make run
```

## 这个仓库里有什么

- 一个可扩展的服务骨架：`ticket_router` 会根据工单内容做路由决策。
- 一套适合 Codex 和 Claude Code 的文档入口。
- 一条最小但完整的验证链。
- 一组能直接进入团队协作的模板文件。

## 目录

- `AGENTS.md`：仓库级执行入口。
- `CONTRIBUTING.md`：贡献和提交流程。
- `CLAUDE.md`：给 Claude Code 的薄适配层。
- `docs/product.md`：业务行为定义。
- `docs/architecture.md`：模块边界和约束。
- `docs/workflow.md`：人类和 agent 的协作流程。
- `docs/release.md`：发布前后检查清单。
- `docs/runbook.md`：本地运行和排障手册。
- `src/ticket_router/`：服务代码。
- `tests/`：回归测试。
- `scripts/check_repo.py`：仓库自检。

## 适合拿去起什么项目

- 内部工具服务
- 后台自动化任务
- 规则引擎类 Python 服务
- 需要 agent 长期协作维护的中小型仓库

## 为什么这算一个可生产化 starter

- 入口短。`AGENTS.md` 只讲怎么开始，不背整本手册。
- 规则实。行为变化要补文档，文档漂移会被脚本拦住。
- 命令少。只保留 `make check`、`make test`、`make ci` 三条主命令。
- 结构清。业务规则、协作规则、验证逻辑分开存放。
- 工具中立。真正的知识在仓库里，不锁死在某个 agent 产品里。
- 工具范围清晰。当前只维护 Codex 和 Claude Code 两条入口，不额外兼容 Cursor。
- 入口可跑。`make run` 接受真实 JSON 输入，而不是只能运行固定样例。

## Starter 级协作入口

- `CONTRIBUTING.md`：给新协作者和新 agent 的统一上手入口。
- `.github/ISSUE_TEMPLATE/`：强制问题和需求都带上下文与验收标准。
- `.github/PULL_REQUEST_TEMPLATE.md`：把验证、文档同步和风险说明变成默认项。
- `docs/release.md`：把发布检查显式化，防止靠记忆发布。
- `docs/runbook.md`：把运行命令和常见排障显式化，减少口头传承。
