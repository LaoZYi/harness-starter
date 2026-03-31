# agent-harness-demo

这是一个可直接运行的示例仓库，用来演示什么叫“好的 harness”。它不是只放几份 prompt，而是把 agent 的工作环境拆成四层：

1. `AGENTS.md` 只保留短入口和执行规则。
2. `docs/` 承载产品、架构和协作细节。
3. `scripts/check_repo.py` 把关键约束变成机器可校验规则。
4. `Makefile` 和 CI 保证改动能快速自证。

## 快速开始

```bash
cd /Users/bochun/Documents/work/agent-harness-demo
make check
make test
```

## 这个仓库里有什么

- 一个真实的小业务模块：`triage_bot` 会根据工单内容做分流。
- 一套适合 agent 的文档入口。
- 一条最小但完整的验证链。
- 跨工具的轻量适配文件，避免把规则散落在不同产品里。

## 目录

- `AGENTS.md`：仓库级执行入口。
- `CONTRIBUTING.md`：贡献和提交流程。
- `CLAUDE.md`：给 Claude Code 的薄适配层。
- `.cursor/rules/00-repo.mdc`：给 Cursor 的薄适配层。
- `docs/product.md`：业务行为定义。
- `docs/architecture.md`：模块边界和约束。
- `docs/workflow.md`：人类和 agent 的协作流程。
- `docs/release.md`：发布前后检查清单。
- `src/triage_bot/`：示例业务代码。
- `tests/`：回归测试。
- `scripts/check_repo.py`：仓库自检。

## 为什么这算一个好 harness

- 入口短。`AGENTS.md` 只讲怎么开始，不背整本手册。
- 规则实。行为变化要补文档，文档漂移会被脚本拦住。
- 命令少。只保留 `make check`、`make test`、`make ci` 三条主命令。
- 结构清。业务规则、协作规则、验证逻辑分开存放。
- 工具中立。真正的知识在仓库里，不锁死在某个 agent 产品里。

## Starter 级协作入口

- `CONTRIBUTING.md`：给新协作者和新 agent 的统一上手入口。
- `.github/ISSUE_TEMPLATE/`：强制问题和需求都带上下文与验收标准。
- `.github/PULL_REQUEST_TEMPLATE.md`：把验证、文档同步和风险说明变成默认项。
- `docs/release.md`：把发布检查显式化，防止靠记忆发布。
