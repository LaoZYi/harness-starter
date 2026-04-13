# .agent-harness/bin/

项目内嵌运行时脚本。**无需安装 harness CLI** 即可执行——clone 仓库 + 开 Claude Code 立即可用。

- `audit` — 等价于 `harness audit`（关键文件变更审计）
- `memory` — 等价于 `harness memory`（分层记忆索引）
- `_runtime/` — 纯 stdlib 运行时源码副本，由 harness 自动管理。**请勿手工修改**
  （下次 `harness upgrade apply` 会覆盖任何改动）

## 用法

```bash
.agent-harness/bin/audit append --file lessons.md --op append --summary "新沉淀一条教训"
.agent-harness/bin/audit tail --limit 10
.agent-harness/bin/memory rebuild . --force
```

无执行权限时可用 python 直接跑：

```bash
python3 .agent-harness/bin/audit tail
```

## 与 harness CLI 的关系

- **harness CLI**（`pipx install agent-harness-starter`）：**项目维护者**的脚手架工具，
  用于 init / upgrade / doctor / export 等**元命令**
- **.agent-harness/bin/**：**项目使用者**（clone 仓库的人）的运行时，AI 工作流中所有
  需要调用的命令都通过这里，不依赖用户机器装了 harness
