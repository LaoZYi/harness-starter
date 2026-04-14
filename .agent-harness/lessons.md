# Lessons Learned

从错误和返工中提炼的教训。每条教训对应一个曾经犯过的错，包含根因和防止再犯的规则。

agent 开始任务前应快速浏览本文件，避免重蹈覆辙。

## 按分类索引

> 新增条目时在对应分类追加 anchor 链接。若出现新分类，在此表新增一行并同步 `/compound` 指令。anchor 规则见 `/compound` 指令第 4.5 步。

- **测试**: [文件锁顺序必须先锁再 truncate](#2026-04-12-测试-文件锁顺序必须先锁再-truncate)
- **模板**: [模板中的文档占位符语法会被模板引擎吞掉](#2026-04-09-模板-模板中的文档占位符语法会被模板引擎吞掉), [命令重命名后模板文件也要全量扫描](#2026-04-09-模板-命令重命名后模板文件也要全量扫描)
- **流程**: [进化去重必须覆盖已关闭 Issue](#2026-04-08-流程-进化去重必须覆盖已关闭-issue), [新增技能时文档散布计数需全量扫描](#2026-04-08-流程-新增技能时文档散布计数需全量扫描), [新任务覆盖前必须先关闭旧任务](#2026-04-09-流程-新任务覆盖前必须先关闭旧任务), [同一项目的增量吸收用 evolution-update 标签](#2026-04-12-流程-同一项目的增量吸收用-evolution-update-标签), [CLI flag 假设在 plan 阶段必须 source-verify](#2026-04-12-流程-cli-flag-假设在-plan-阶段必须-source-verify), [评估报告前必须先查合约测试](#2026-04-13-流程-评估报告前必须先查合约测试)
- **工具脚本**: [_runtime 模块清单是 dogfood 的一部分](#2026-04-14-工具脚本-runtime-模块清单是-dogfood-的一部分), [dogfood 产物在 .claude 下默认 gitignore 需 force-add](#2026-04-14-工具脚本-dogfood-产物在-claude-下默认-gitignore-需-force-add), [dogfood 命令展平](#2026-04-08-工具脚本-dogfood-命令展平), [重复工具函数提取后必须删除原始定义](#2026-04-09-工具脚本-重复工具函数提取后必须删除原始定义), [shell 命令构造必须-shlex-quote-所有路径](#2026-04-12-工具脚本-shell-命令构造必须-shlex-quote-所有路径), [守卫禁用白名单改自动发现](#2026-04-13-工具脚本-守卫禁用白名单改自动发现)
- **架构设计**: [角色权限分层要从文档约束升级到运行时强制](#2026-04-14-架构设计-角色权限分层要从文档约束升级到运行时强制), [子 agent 产出要从自由日志升级到结构化制品](#2026-04-14-架构设计-子-agent-产出要从自由日志升级到结构化制品), [外部方法论吸收前必须做适用性裁剪](#2026-04-14-架构设计-外部方法论吸收前必须做适用性裁剪), [脚手架项目吸收外部思想要选最小实现](#2026-04-12-架构设计-脚手架项目吸收外部思想要选最小实现), [POSIX-only 模块要 try-except 软导入](#2026-04-12-架构设计-posix-only-模块要-try-except-软导入), [统一入口技能必须串起全量能力](#2026-04-13-架构设计-统一入口技能必须串起全量能力), [自回环 hook 必须有人工放行开关](#2026-04-13-架构设计-自回环-hook-必须有人工放行开关), [新异常类继承 ValueError 保向后兼容](#2026-04-13-架构设计-新异常类继承-valueerror-保向后兼容), [hook 依赖未公开 API 必须 source-verify 再决定降级](#2026-04-13-架构设计-hook-依赖未公开-api-必须-source-verify-再决定降级), [大 Issue 吸收要拆阶段 + atomic commit + step tag](#2026-04-13-流程-大-issue-吸收要拆阶段-atomic-commit-step-tag), [模块拆分前留好未来模块位置](#2026-04-13-架构设计-模块拆分前留好未来模块位置), [三源对账推导状态而非持久化 worker 状态](#2026-04-13-架构设计-三源对账推导状态而非持久化-worker-状态), [没 consumer 的基础设施重构是空转](#2026-04-13-流程-没-consumer-的基础设施重构是空转), [兼容层降低迁移成本](#2026-04-13-架构设计-兼容层降低迁移成本), [单入口技能能力接入完整](#2026-04-13-架构设计-单入口技能--能力接入完整), [Harness 反偷懒与协作记忆要解耦](#2026-04-13-架构设计-harness-中反偷懒与协作记忆模块要解耦), [抽 SSOT 时必须清单化所有下游消费方](#2026-04-13-架构设计-抽-ssot-时必须清单化所有下游消费方), [占位符层次必须显式区分](#2026-04-13-模板-占位符层次必须显式区分避免双重替换), [280 行硬限触发时连环效应](#2026-04-13-流程-280-行硬限触发时连环效应3-个文件同时超)
- **集成API**: [GitLab Issue 搜索禁用 search 参数](#2026-04-08-集成api-gitlab-issue-搜索禁用-search-参数)

## 条目格式

```
## YYYY-MM-DD [分类] 一句话标题

- 错误：发生了什么
- 根因：为什么会发生
- 规则：以后怎么避免
```

---

## 2026-04-14 [工具脚本] _runtime 模块清单是 dogfood 的一部分

- 错误：新增 `memory_search.py` 后，`src/agent_harness/memory.py` 通过 `from .memory_search import` 引用；dogfood 后 `.agent-harness/bin/_runtime/memory.py` 同步了，但 `_runtime/memory_search.py` 没同步 → 项目内嵌运行时 `.agent-harness/bin/memory search` 报 `ModuleNotFoundError: No module named '_runtime.memory_search'`
- 根因：`src/agent_harness/runtime_install.py` 的 `_RUNTIME_MODULES` 是显式白名单（不是自动扫描），新增的运行时依赖模块必须手动加入
- 规则：新增被 `.agent-harness/bin/*` 入口脚本（audit/memory/squad 等）间接依赖的 `src/agent_harness/*.py` 模块时，**同时**在 `runtime_install.py._RUNTIME_MODULES` 追加一行。检测手段：`test_runtime_only_imports_stdlib` 会捕获 stdlib 以外的导入；`test_memory_rebuild_creates_index` 类的 bin 端到端测试会捕获缺模块。两类测试二选一要过

## 2026-04-14 [架构设计] 外部方法论吸收前必须做适用性裁剪

- 错误：/evolve 提案把 humanlayer/12-factor-agents 全 12 条 Factor 列为吸收清单，但其中 8 条（F1/2/4/6/7/9/11/12）预设"拥有 LLM 运行时 prompt + tool schema + state 代码控制权"。本项目是 Claude Code 模板库，这 8 条在本项目语境下无法落地。如果不做裁剪直接照吸收，会产出一个"看起来全但实际 2/3 是死条款"的技能
- 根因：evolution Issue 的提案阶段只做了"值得吸收"的判断，没做"每条是否都适用本项目"的细审。脚手架项目与 LLM 运行时项目，对同一套方法论的适用面天然不同
- 规则：evolution Issue 进入 `/lfg` 执行阶段后，**第一件事**是在 spec 里做"适用性三分"（高/中/低）—— 对每条 Factor / 每个吸收项标明在本项目语境下的可落地程度。只吸收"高/中"部分，"低"部分在新技能附录里作参考列出，不做硬约束。命名时避免暗示"完整 12 条"（例如 `/agent-design-check` 而非 `/12-factor-check`）

## 2026-04-14 [工具脚本] dogfood 产物在 .claude 下默认 gitignore 需 force-add

- 错误：`make dogfood` 把模板渲染到 `.claude/commands/` 和 `.claude/rules/`，但 `.gitignore` 第 9 行把整个 `.claude/` 目录忽略。新增的 `agent-design-check.md` 和 `agent-design.md` 虽然 dogfood 生成了，但 `git add -A` 并不收录，导致 commit 遗漏。既有文件（evolve.md、lfg.md 等）能 commit 是因为历史上 force-add 过
- 根因：`.gitignore` 用 `.claude/` 忽略整个目录，但历史上用 `git add -f` 显式追加过既有文件，新增文件没有这个"力"，静默失踪
- 规则：dogfood 后新增 `.claude/commands/<new>.md` 或 `.claude/rules/<new>.md` 时，必须显式 `git add -f` 追加。检测手段：dogfood 输出行含 `+ .claude/...` 时，提交前跑 `git status -s .claude/` 对比，缺失项用 `git add -f <path>` 补

## 2026-04-13 [架构设计] 兼容层降低迁移成本

- 错误：Issue #21 把 JSONL 换成 SQLite，最初方案是让 19a 的调用方（cli.py / coordinator.py / 测试）全部改签名接新 API，估算改动面很大。
- 根因：迁移底层存储时，**同时改 API** = 一次做两件事。如果回滚只想回退到 JSONL，还要把 API 改回去。
- 规则：底层存储升级时，**保留旧 API 签名**作为薄兼容层（state.py 的 `append_status / done_workers / pending_worker_info` 签名不变，内部 delegate 到新 mailbox 模块）。让存储升级对调用方完全无感，风险隔离为 mailbox 模块内部。将来若要再升级（比如从 SQLite 到网络化 mailbox），同样改兼容层内部就行。

## 2026-04-13 [流程] 没 consumer 的基础设施重构是空转

- 错误：Issue #19 原计划把阶段 2 拆为 #19a/b/c/d 顺序做，但开始做 #19b（SQLite mailbox）时发现没有 consumer——19a 的 JSONL 完全够用，所谓"mailbox"只是换个数据结构，没有新用户价值。
- 根因：把一个完整 feature（coordinator）按技术层拆分（存储层 vs consumer 层）独立做，会产生"为换而换"的空转阶段。用户永远只看到中间状态的成本（多一个文件）不看到价值（consumer 才用到）。
- 规则：拆 Issue 时按**用户可感知价值**拆，不是按技术层拆。存储层 + 第一个 consumer **合并在同一 Issue** 做（Issue #20 已合并到 #21）。"技术层独立做好了以后再接 consumer"听起来干净但实际会被中途放弃（因为没反馈）。

## 2026-04-13 [架构设计] 三源对账推导状态而非持久化 worker 状态

- 错误：Issue #19a 最初方案想在 manifest 中增加 `worker.status` 字段（pending/running/done），但这会让 19b（SQLite mailbox 替换）和 19c（持久 coordinator）都要再改 schema。
- 根因：状态可以从"已有三个独立源"推导：`spec.workers`（全集）、`status.jsonl` 的 done 事件（完成集）、`tmux list-windows`（已启动集）。持久化会引入同步难题（三源和持久字段何者为准？）。
- 规则：只要状态可**纯函数推导**，就不要持久化。把推导函数（如 `derive_worker_state`）写成 pure 输入→输出，便于测试（mock 三源），也为上游改造（SQLite 替换 JSONL）提供隔离层。只有当推导成本高或推导需要历史全量扫描时才持久化。

## 2026-04-13 [架构设计] 模块拆分前留好未来模块位置

- 错误：Issue #19a 要新增 `cmd_advance` / `cmd_done` 两个 handler，一开始想塞进 `cli.py`。结果 cli.py 从 220→367 超过 280 行硬规则。
- 根因：没提前想清楚"这些新代码的长期归属"——它们是"依赖推进 / 状态协调"的核心逻辑，未来 19c 的持久 coordinator 会在同一模块扩展。塞到 cli.py 里会让后续 19c 又要拆一次。
- 规则：添加新 handler 前先想"它 18 个月后的归属"。如果有明确的未来扩展方向（如 19c 的 watch 进程），就**立即**新建对应模块（这里起名 `coordinator.py`）。宁可新模块一开始只有 2 个函数，也不要为了"不为未知扩展造模块"而把主文件撑爆。宁可空模块，也不可撑爆主文件。

## 2026-04-13 [流程] 大 Issue 吸收要拆阶段 + atomic commit + step tag

- 错误：Issue #17 一次性吸收 5 个独立机制（hook / 新技能 / 模板扩展 / 规则 / 参考清单），最初打算一个 commit 全塞，提交 diff 会达 20+ 文件几百行，难评审且无法精确回滚到某个中间状态。
- 根因：脚手架吸收外部思想的任务常有"机制族"形态——看起来相关，实际彼此独立。单 commit 会丢失机制间的清晰边界。
- 规则：遇到多机制的大 Issue，**按机制拆阶段**（B/C/D/E/F/G+H/I），**每阶段 atomic commit + 轻量 tag**（`lfg/step-X`）。让后续可以 `git reset --hard lfg/step-D` 精准回到任一子阶段。tag 名用阶段字母而不是数字，避免和 /lfg 原有 step-N tag 冲突。

## 2026-04-13 [架构设计] hook 依赖未公开 API 必须 source-verify 再决定降级

- 错误：Issue #17 第 1 项（上下文监控 Hook）原方案依赖 Claude Code statusline 暴露 `remaining_percentage` 字段，差点直接开写。
- 根因：GSD 原项目文档里的字段假设是基于他们自己封装的 statusline，不是官方 schema。训练数据里这种 undocumented 字段很危险——实现能跑但换 Claude Code 版本就崩。
- 规则：凡是 hook / 插件设计依赖"框架暴露的数据"，**编码前必须先 `/source-verify`**（查官方文档 schema）。若官方不支持：要么换代理指标（本次选了工具调用计数）、要么标 out-of-scope 等官方 API。绝不按猜测写然后"看看能不能跑起来"。

## 2026-04-13 [架构设计] 新异常类继承 ValueError 保向后兼容

- 错误：Issue #15 实现 `SecurityError` 时，第一反应是继承 `Exception`，但这样会导致 `agent.py` / `audit.py` / `squad/spec.py` 中现有的 `except ValueError` 全部失效。
- 根因：项目里已有多处用 `ValueError` 作为输入校验的"统一异常族"，新加强类型的异常如果不继承到这个族，等于隐式破坏了公开契约。
- 规则：引入更具体的校验异常类时，**必须继承项目已有的上位异常类**（这里是 `ValueError`）。同时在测试里显式加一条 `assertRaises(ValueError)` 锁死向后兼容。重构老代码改用新异常时用 `raise New() from exc` 保留原因链。

## 2026-04-13 [架构设计] 路径遍历校验必须对 resolved 后的路径检查

- 错误：写 `sanitize_path` 时差点用 `base / path` 后直接 `is_relative_to` 校验，没 resolve。
- 根因：`Path.is_relative_to` 只做字符串前缀比较，不会跟随符号链接。攻击者在 base_dir 内放一个指向外部的符号链接（`base/link -> /etc/passwd`），这种简化检查会误判为安全。
- 规则：凡是路径逃逸防御，**必须**先 `.resolve()` 再 `.relative_to(base.resolve())`。`resolve()` 会跟随符号链接，暴露真实目标位置。测试里必须包含 symlink escape 用例做回归保护。

## 2026-04-13 [架构设计] 自回环 hook 必须有人工放行开关

- 错误：给 dogfood 的框架加 Stop hook 强制 block 未完成 checkbox，AI 自身会被自己的 hook 拦住而无法结束当前响应，造成自锁
- 根因：Stop hook 在脚手架自身 dogfood 时生效，而原始方案（MemPalace）依赖的 `stop_hook_active` 字段经 `/source-verify` 发现 Claude Code 官方文档**仅在 SubagentStop 保证有**，Stop 事件本身无保证。没有短路机制 hook 就会死循环
- 规则：任何会 block AI 继续的自回环 hook 必须提供"人工放行 sentinel"（如 `.agent-harness/.stop-hook-skip` 文件），用户 touch 后下次 Stop 跳过检查。dogfood 本框架时自动 touch 一次避免自锁。不能只依赖 `stop_hook_active` 或 LLM 记住状态——要有持久化的 off switch

## 2026-04-13 [架构设计] 统一入口技能必须串起全量能力

- 错误：声称 /lfg 是"所有使用入口"但它只引用了 33 个技能中的 16 个，`/recall` `/use-worktrees` `/verify` `/finish-branch` `/careful` `/source-verify` `/request-review` `/receive-review` `/subagent-dev` `/todo` 全被遗漏；甚至违反自己项目的 task-lifecycle 分层记忆规则（/lfg 阶段 0.2 直接全文读 lessons.md，绕过 /recall）
- 根因：技能是逐个迭代加入的，每个 PR 只改自己模板，没人系统回过头问"/lfg 还需要更新吗"。没有契约测试锁死"新技能必须被 /lfg 分类（接入 or 豁免）"
- 规则：凡是宣称为"统一入口"的技能（/lfg、/use-superpowers 这类），必须有契约测试：EXPECTED_IN + EXPECTED_NOT_IN 两个集合，并集等于当前全部技能清单；新增技能时测试失败强制做分类决策。模板末尾应有"覆盖清单"表作为自检锚点

## 2026-04-13 [工具脚本] 守卫禁用白名单改自动发现

- 错误：`squad/cli.py` 写到 303 行，超过 AGENTS.md 280 行硬规则，但 `make check` 一直显示 passed
- 根因：`scripts/check_repo.py:check_module_sizes` 用硬编码路径白名单，只列了 9 个模块，新增的 `squad/` 子包（5 个文件）完全没被检查。白名单漂移是沉默的——新文件不进白名单就永远不被检查
- 规则：硬规则守卫应该用自动发现（`rglob` / `walk`）而非白名单。可用豁免机制（跳过 `__init__.py`、`templates/` 等已知非代码目录）代替"只检查这些"。新增契约测试锁死该行为，防未来回归

## 2026-04-08 [工具脚本] dogfood 命令展平

- 错误：dogfood 生成的技能文件中显示 `python -m unittest discover` 而非 `make test`，所有 25 个文件都用了 auto-discovery 的命令而非 project.json 配置的
- 根因：`project.json` 用嵌套结构存命令（`"commands": {"test": "make test"}`），但 `dogfood.py` 和 `check_repo.py` 直接透传给 `prepare_initialization()`，后者期望扁平 key（`"test_command"`）。嵌套 key 查不到就 fallback 到 auto-discovery
- 规则：凡是读 `project.json` 后调用 `prepare_initialization()` 的地方（目前有 dogfood.py 和 check_repo.py），都必须先展平 `commands` 字典。新增类似调用时同理

## 2026-04-08 [流程] 进化去重必须覆盖已关闭 Issue

- 错误：`/evolve` 只检查 open Issue 去重，已吸收（closed）的项目会在下次搜索中被重新提案
- 根因：`gh issue list` 默认只返回 open 状态，需要显式传 `--state all`
- 规则：进化去重必须检查 open + closed 两种状态。同时需要区分"新发现"（evolution 标签）和"已吸收项目有更新"（evolution-update 标签）两条通道

## 2026-04-08 [集成API] GitLab Issue 搜索禁用 search 参数

- 错误：LFG 收尾关闭 GitLab Issue 时用 `search=architecture-decision-record` 查找对应 Issue，返回空结果，导致 GitLab Issue 未同步关闭
- 根因：GitLab API 的 `search` 参数对中文标题和混合语言内容匹配不可靠，无法可靠找到目标 Issue
- 规则：查找 GitLab Issue 时必须用 `labels` 过滤缩小范围，再在本地用 Python 做标题子串匹配。禁止依赖 GitLab API 的 `search` 参数

## 2026-04-08 [流程] 新增技能时文档散布计数需全量扫描

- 错误：新增 `/spec` 技能后，技能数从 27 变 28，但 12+ 处散布的计数引用容易遗漏
- 根因：技能计数硬编码在 CHANGELOG、README、docs/、templates/ 等多个文件中，没有单一来源
- 规则：新增技能后必须 `grep "N 个"` 全量扫描确认无遗漏。长期可考虑在 check_repo.py 中加计数一致性校验

## 2026-04-09 [流程] 新任务覆盖前必须先关闭旧任务

- 错误：用户触发 `/lfg #9` 时，current-task.md 中有"待验证"状态的三方合并任务，直接覆盖导致旧任务的 task-log 记录丢失
- 根因：没有遵守 task-lifecycle 规则中的"如果有未完成任务，先询问用户：继续还是替换"。即使用户明确要做新任务，也应该先对旧任务做收尾（写 task-log）再替换
- 规则：覆盖 current-task.md 前，如果旧任务状态为"待验证"且所有 checkbox 已完成，必须先补写 task-log 记录再替换。绝不能静默丢弃已完成的工作记录

## 2026-04-09 [工具脚本] 重复工具函数提取后必须删除原始定义

- 错误：将 `_slugify` 提取到 `_shared.py` 后，三个模块各自保留了一个 `def _slugify(v): return slugify(v)` 的无用包装函数
- 根因：提取时只添加了新导入和替换了实现体，没有检查调用点是否还在用旧的私有名称
- 规则：提取公共函数后，必须 grep 确认旧定义全部删除、调用点全部改为直接调用新函数。不要留包装函数

## 2026-04-09 [模板] 模板中的文档占位符语法会被模板引擎吞掉

- 错误：shared-plugins/README.md.tmpl 里写了 `{{variable}}` 作为文档示例，但模板引擎把它替换成了空串
- 根因：模板引擎对所有 `{{ }}` 做替换，没有转义机制区分"真占位符"和"文档中的示例"
- 规则：模板文件中不要用 `{{xxx}}` 作为文档示例文本，改用文字描述或反引号内放不匹配正则的变体

## 2026-04-09 [模板] 命令重命名后模板文件也要全量扫描

- 错误：将 `sync-context` 重命名为 `sync` 后，docs/ 和 AGENTS.md 更新了，但 templates/meta/ 下的 4 处引用未更新
- 根因：只搜索了 docs/ 和项目根的 .md 文件，遗漏了 src/agent_harness/templates/ 目录
- 规则：重命名 CLI 命令后，必须对整个仓库（含 templates/）执行 `grep -r "旧命令名"` 确认零残留

## 2026-04-12 [流程] 同一项目的增量吸收用 evolution-update 标签

- 场景：addyosmani/agent-skills 在 Issue #6（2026-04-08）已首次吸收；2026-04-12 对其增量更新做二次吸收，创建 Issue #16
- 根因：已关闭的 evolution Issue 不应重复提案（evolve 去重规则），但"同一项目有新价值"这条通道需要独立标识
- 规则：增量吸收用 `evolution-update` + `absorbed` 双标签（Issue #16 已使用），避免与首次吸收的 `evolution` 通道混淆。`/evolve` 搜索时分别查两个通道

## 2026-04-12 [架构设计] 脚手架项目吸收外部思想要选最小实现

- 场景：吸收 MemPalace 的四层记忆栈时，候选方案从"目录分层+Python 抽象层"（完整移植）到"单索引文件"（最小方案）
- 决策：选方案 C（memory-index.md 精华索引 + `/recall` 按需展开），而非方案 B（目录分层）或方案 D（MemPalace layers.py 移植）
- 根因：本项目是**脚手架生成器**，不是运行时系统；运行时系统用分层是为了动态 rotate，脚手架用分层是为了约束 AI 读什么——两者的痛点不同，"完整移植"反而是过度工程
- 规则：从外部项目吸收思想前，先问"对方的痛点是否和我们一致？" 脚手架项目倾向选最轻的实现（单文件 > 目录结构 > Python 抽象层）。迁移成本低 + 与现有数据结构兼容 > 理论上的完备性

## 2026-04-12 [流程] CLI flag 假设在 plan 阶段必须 source-verify

- 错误：写 /squad MVP plan 时假设 Claude Code 有 `claude --prompt-file <path>` flag，在 plan 的"执行步骤"示例命令中多处使用，如果直接进入实施会整个启动方式失败
- 根因：凭印象假设 CLI 有某个 flag，没先用 `claude --help` 或官方文档验证。大模型训练数据里的 CLI 工具 flag 常有幻觉
- 规则：plan 里任何 CLI flag 假设都必须标记为"待 source-verify"并作为执行计划的第 0 步验证。特别是"prompt 注入""参数传递"这种核心机制，一旦错了后续所有步骤都是坏的。验证方式：`<cli> --help` / 官方 docs / 已存在 repo 的用法。修正：本次实测后改为 `claude --append-system-prompt "$(cat ctx.md)" "$(cat task.md)"` 组合

## 2026-04-12 [工具脚本] shell 命令构造必须 shlex.quote 所有路径

- 错误：`tmux.py` 的 `build_new_window_cmd` 用 f-string 拼接 prompt 文件路径到 `"$(cat {path})"`，cwd 做了手工 `"..."` 引号但两个 prompt 路径没做。含空格路径会破坏 subshell；含反引号或 `$(...)` 的路径会触发命令注入。评审员发现（P0-1）
- 根因：假设"调用者总是传合法路径"。即使当前调用链全部来自内部生成，这种假设不能写进通用工具函数的契约里
- 规则：构造 shell 字符串时，**所有来自参数的片段**必须 `shlex.quote()`，哪怕当前调用者已 sanitize。工具函数防御是责任不是冗余。补回归测试：路径含空格 / 路径含反引号 两种场景各一个

## 2026-04-12 [架构设计] POSIX-only 模块要 try-except 软导入

- 错误：`src/agent_harness/squad/state.py` 顶层 `import fcntl`。Windows 原生环境（非 WSL）`import agent_harness.squad` 就 `ModuleNotFoundError` 崩溃，连 `harness squad --help` 都看不到。评审员发现（P0-3）
- 根因：项目文档说"Windows 用 WSL"，但没在代码层面处理 import 失败。文档级的前置条件不等于代码的优雅降级
- 规则：任何 POSIX-only 依赖（`fcntl`、`termios`、`pwd`、`resource` 等）都必须 `try/except ImportError` 软导入 + 调用时友好报错。让 `--help` 永远能运行，错误推迟到真正需要该功能的调用点再抛

## 2026-04-12 [测试] 文件锁顺序必须先锁再 truncate

- 错误：`_locked_write` 用 `os.open(..., O_TRUNC)` 再 `flock`，在文件打开时就清空了。并发两个 writer 场景下可能导致 A 拿锁前已被 B 清空，数据写到悬空描述符
- 根因：`O_TRUNC` 在 `open()` 时生效，与后续获取锁之间存在窗口。经典 lock-before-mutate 违反
- 规则：flock + truncate 组合必须顺序：`os.open(O_WRONLY|O_CREAT)` → `flock(LOCK_EX)` → `os.ftruncate(0)` → `os.lseek(0)` → 写入。或用"写临时文件 + `os.replace()`"做原子替换（更稳但更复杂）。本次修复采用前者

## 2026-04-13 [架构设计] watchdog 把"已上报"也写进事件流，避免外挂状态文件

- 场景：Issue #22 squad watchdog 要做幂等去重——同一 worker 失联在多个 tick 里只报一次。直觉是开个 set/dict 记录 reported 状态
- 决策：直接把 `worker_crashed` / `session_lost` 写进 mailbox，下次 tick 反查 mailbox 判断是否已上报。**不引入外挂状态文件**
- 根因：sqaud 已经有"三源对账推导状态"原则（lessons/2026-04-13）。再加一份去重状态会破坏单一真相源——重启 / 多进程共享时这份状态会漂移
- 规则：去重/标记状态优先写进现有事件流（mailbox / log / db），让查询替代缓存。代价是每 tick 多一次小查询，收益是少一份漂移源 + 重启自动恢复 + 测试更纯（mailbox 是已有 fixture）
- 副作用：要求新事件类型必须登记 `KNOWN_TYPES`，否则下游过滤会失效——这点恰好已经有契约测试守住

## 2026-04-13 [流程] 280 行硬限触发时不扩规则要拆/瘦模块

- 场景：watchdog 集成 cmd_watch 时 coordinator.py 涨到 299 行触超 280 限
- 决策：拒绝改硬限。先把 watchdog 调用 + 打印 + 退出标志整体抽到 watchdog.py 的 `watch_tick_with_report`（瘦 10 行）；仍超就压平 import + 简化 cmd_dump（再瘦 9 行）压到 280
- 根因：硬限是架构压力测试。一旦放宽就再没有边界，模块会无限膨胀。280 行是经验值，超出说明该模块在做太多事
- 规则：碰到 check_repo 行数失败的处理顺序：① 抽 helper 到合适模块（首选）→ ② 简化代码（去重复 import、压 docstring）→ ③ 拆模块。**不要**改 `check_repo.py` 的限值。这次的代价是 watchdog.py 多了一个 helper 函数 `watch_tick_with_report`，但这个边界本来就该有：watchdog 是检测+决策者，coordinator 只该是调度者


## 2026-04-13 [架构设计] 幂等去重和退出判定不能共用同一个返回值

- 错误：watchdog 的 `watch_tick_with_report` 用 `detect_failures` 返回的事件列表（含 session_lost）来决定 cmd_watch 是否退出。事件去重写在 mailbox 后，重启 watch 时 detect 看见旧 session_lost 直接返回空 → 调用方误以为 session 还在 → 死循环空转 advance 一个死 session
- 根因：把两个不同语义的状态——"该不该写新事件"和"该不该退出"——压到同一个返回值上。事件去重的目的是减噪，退出判定的目的是反映当前真实状态；这两个语义在重启场景下错位
- 规则：去重缓存（mailbox / set / dict）只用于"是否上报"决策；"当前真实状态"必须每次都重新探测。把两者拆成独立判断：`should_report = not already_reported and condition`、`should_exit = condition`。两个谓词共享 `condition` 但不共享缓存
- 适用范围：所有"周期性 ping + 一次性退出"的健康监控模式（watchdog / heartbeat / liveness probe）

## 2026-04-13 [流程] 辅助监控模块必须有异常隔离边界

- 错误：watchdog 直接调 `mb.append_event` 和 `subprocess.run`，任何异常（SQLite 写失败、tmux server 卡住、磁盘满）会冒泡到 cmd_watch 主调度循环让整个常驻进程死掉
- 根因：watchdog 是**辅助**监控，但被当成**关键路径**写——没设计异常边界。心智上"它就是个查询，不会出问题"，但 subprocess + SQLite 都是 I/O 边界
- 规则：辅助/监控/可观测性类模块必须有 try/except 兜底，故障时降级（打印警告 + 返回保守值），不能传播到主调度。判断是否"辅助"的标准：缺了它主流程能不能跑？能 → 必须隔离异常
- 反例：核心数据写入路径**不能**这样做——必须传播让上层处理（safety/error-attribution rule）


## 2026-04-13 [架构设计] AI 运行时调用必须项目内嵌，不能依赖使用者机器的 CLI

- 场景：Issue #24。/lfg 模板里已经在调 `harness audit/memory`；用户 clone 一个 init 过的项目，没装 harness → `command not found`。整合 squad 进 lfg 会更糟（依赖一堆 harness squad 子命令）
- 决策：划清两个角色的命令边界——`harness` CLI（维护者工具：init/upgrade/doctor）vs `.agent-harness/bin/`（使用者工具：AI 工作流调的 audit/memory/squad/...）。后者项目内嵌，clone 即用
- 根因：脚手架框架的"使用者"不一定是"维护者"。接入一次后 clone 项目的人没义务装 harness。把两种用户混为一谈会制造隐性依赖
- 规则：脚手架类框架发到目标项目的任何 AI 工作流脚本/命令，调用的都必须是**项目自带**的运行时（`.agent-harness/bin/...`），不能是**机器 PATH**上的工具。维护者专用命令（脚手架生成/升级）可以例外
- 适用范围：所有"接入一次，之后 AI 自主工作"的脚手架框架

## 2026-04-13 [架构设计] 复制源码做内嵌运行时时，要给宿主模块去掉顶层副作用

- 错误：初版 install_runtime 直接复制 `src/agent_harness/_shared.py` 到 `.agent-harness/bin/_runtime/`。_shared.py 顶层有 `FRAMEWORK_VERSION = (PKG_DIR / "VERSION").read_text()` 和 `if not TEMPLATE_ROOT.is_dir(): raise`——在内嵌运行时场景这两个都不成立，import 就崩
- 根因：原框架模块的顶层副作用（读资源文件、校验目录结构）是面向"装在 site-packages 里有完整发行物"的假设写的。内嵌场景只需模块里的部分函数（`require_harness`）
- 规则：需要复制到"只拿一部分功能"的内嵌运行时时，**不要整文件复制**有顶层副作用的模块。要么改写纯函数版本，要么做一个内嵌专用的精简替身（本次做法：runtime_install.py 内置一个 `_SHARED_EMBEDDED` 字符串，只保留 `require_harness` 函数）。不要为了"单一数据源"而硬拖框架代码进来
- 延伸：设计模块时就让核心函数"纯"（无顶层 I/O），顶层副作用放 `__init__.py` 或明确的 `configure()`——可复用性天然提高


## 2026-04-13 [架构设计] 复制 Python 子包做内嵌运行时时，相对 import 必须重写为绝对前缀

- 场景：Issue #25 squad 项目内嵌。squad/spec.py 用 `from ..security import NAME_PATTERN`（相对 import）。直接复制到目标 `.agent-harness/bin/_runtime/squad/spec.py` 后，Python 按原 `..` 找父包，但目标环境里 _runtime 本身就是顶级 package → 找不到
- 决策：复制时自动把相对 import 重写成绝对前缀 `from _runtime.security import NAME_PATTERN`。`_runtime/` 作为 Python package（有 __init__.py），entry 脚本把 bin/ 加进 sys.path，`_runtime.xxx` 即可正确 import 任何 sibling 模块
- 根因：Python 相对 import 的层级是按运行时 package 深度算的；源码里的 `..` 假设父包存在，内嵌场景里这个假设不成立
- 规则：向内嵌运行时复制 Python 包时，要么（a）保持原包结构并构造同深度的父包，要么（b）改写相对 import 为绝对前缀。本次选 b——简单、一次性、易测
- 反例：想用"拷贝时改包名"（sed `agent_harness` → `_runtime`）看起来也行，但若源码里出现字面字符串 `"agent_harness"`（文档、log 消息）会被错误替换，风险大

## 2026-04-13 [流程] 破坏性变更用后缀自动检测 + 精确迁移提示，比"兼容旧格式"更好

- 场景：Issue #25 把 spec.yaml 迁到 spec.json。能否"继续支持 .yaml"？理论可以（保留 yaml import），但这意味着项目内嵌运行时仍依赖 PyYAML，前期承诺失败
- 决策：硬性拒绝 .yaml / .yml 后缀的 spec 文件，报错里给出具体的 `python -c "import yaml,json; json.dump(yaml.safe_load(...), ..., ensure_ascii=False, indent=2)"` 迁移命令
- 根因：破坏性变更的矫情做法（兼容双轨）会永久锁死依赖，动机是怕用户有轻微迁移成本。但**精确的迁移命令**让用户迁移成本 < 30 秒，比永远背着旧依赖划算得多
- 规则：破坏性变更要"破而彻底"。用文件后缀 / 格式标记来明确拒绝旧格式 + 给出**可直接复制执行**的迁移命令。不要用"temporarily 支持旧格式 + deprecation warning + 计划 N 版本后移除"这种拖泥带水路径——它极少真的到移除那一天，反而成了永久技术债


## 2026-04-13 [流程] 评估报告前必须先查合约测试

- 场景：对 /lfg 做能力发挥度评估，曾主张"Gap 1：/health 未集成是漏洞"，但 `test_lfg_coverage.py:64` 已用 `EXPECTED_NOT_IN_LFG` 字典明文把 /health 列为"periodic code-quality snapshot, not part of single-task flow"的**故意排除项**并注明理由
- 决策：在向用户提交评估报告前，先 grep `test_*coverage*.py` 和任何 EXPECTED_*_NOT_* 类命名的常量，把"系统已明文选择不做什么"纳入视野；有合约测试的设计决策必须先读再评
- 根因：只读了功能文档（lfg.md.tmpl）和能力清单（README / product.md），没读项目自己为 /lfg 设的**反向合约**。评估容易把"有意省略"当"意外漏洞"，产生虚假 gap
- 规则：做能力评估 / gap 分析时，先 glob `tests/test_*coverage*.py` 或搜 `EXPECTED_NOT_IN_` / `EXCLUDED_` 这类反向断言常量；它们是项目对"不做某事"的显式承诺，必须在评估中被正面引用。否则评估会污染后续决策，把设计撤回变成一次次返工

## 2026-04-13 [架构设计] 单入口技能 ≠ 能力接入完整

- 场景：/lfg 作为"用户只需记一条命令"的统一入口，主 skill 链（/ideate → /brainstorm → /spec → /tdd → /multi-review → /compound 等 30 个）接入完整，但**运行时元能力**（`.agent-harness/bin/audit`、`bin/memory`、`bin/agent` 项目内嵌运行时）虽然存在且被 task-lifecycle.md 强制要求，却没在 /lfg 阶段里显式调用，只靠"用户/hook 自觉"兜底，等于形同虚设
- 决策：对"入口技能"的完整性评估要做两遍——第一遍看 skill 链，第二遍看运行时元能力（audit / memory / agent / plugins）是否在相应阶段有**显式命令**。凡是规则文档（task-lifecycle / safety / autonomy）硬要求的动作，入口技能必须有对应调用点
- 根因："技能编排完整 = 能力发挥最大化"是错觉。技能之间的胶水（WAL 审计、索引刷新、子 agent 隔离、插件读取）如果只在 rules 层强制但 skill 层不兜底，就会在每次实际执行时被遗忘
- 规则：设计或评估统一入口技能时，用两张核对表——(1) skill 覆盖表（现有）+ (2) 运行时 hook 表，后者列出 rules/ 目录中所有"MUST / 必须 / 硬规则"动词对应的命令，逐项确认入口技能有调用。遗漏的是胶水，胶水漏了链条散

## 2026-04-13 [架构设计] Harness 中"反偷懒"与"协作记忆"模块要解耦

- 场景：Yandex Rodionov《Reasoning Shift》论文证明长上下文里模型表现差不是"被绕晕"而是**主动选择少想**——找到答案速度不变，但自我检查率从 43% 降到 32%；推理能力越强偷懒幅度越深（OLMo3 最强版缩 40%）。Anthropic 同期论文又证明 desperate 情绪向量直接驱动 reward hacking（30%→100%），未来可能从训练侧用 calm 注入解决，**届时 Harness 中纯属"反偷懒"的部分会变冗余**
- 决策：把 Harness 模块按"治标 vs 治本"显式分两类——
  - **反偷懒补丁类（中期可能被模型内部对齐吞没）**：StuckDetector 3 次失败强停、checkpoint 强制验证、阶段强制 compact、6 介入点等
  - **协作 / 审计 / 记忆类（无论模型多强都需要）**：audit WAL、memory 分层加载、agent diary 隔离、squad 多 worker、docs sync、git worktree
- 根因：Harness Engineering 整体被作者定性为"症状管控"，假设"模型必定退化"并外挂脚手架。但如果退化源是模型内部情绪机制，外部脚手架的护城河会被训练侧迭代摧毁。未做解耦的 Harness 框架会整体过时
- 规则：评估或设计 Harness 时，每个机制问一句"这是在防模型偷懒，还是在解决多 agent 协作 / 审计 / 跨会话记忆问题？"前者标 `defensive-temporary`，后者标 `collaborative-permanent`。前者数量多说明框架抗模型迭代能力弱

## 2026-04-13 [架构设计] 抽 SSOT 时必须清单化所有下游消费方

- 场景：Issue #27 抽取 skills-registry.json 作为 34 个 skill 元数据 SSOT。下游消费方实际有 5 处：initializer.py / upgrade.py / scripts/dogfood.py / scripts/check_repo.py / tests/test_*.py。每漏改一处 CI 就崩一次（漏了 dogfood → 占位符残留；漏了 check_repo → "技能/规则模板已变更但生成产物未同步" 误报；漏了 test_gsd_absorb → /plan-check 找不到）
- 决策：抽 SSOT 之前先全量 grep 所有读这个数据的代码点，列成 consumers 清单写进计划。每个 consumer 一条修复 step，不要靠"等 CI 报错再补"
- 根因：SSOT 抽取的核心矛盾是"加一层间接 → 所有读旧位置的代码必须改读新位置"。盲点在于"读"的形式很多（直接读文件 / 渲染管道 / 测试断言 / lint 检查），grep 单一关键词漏覆盖
- 规则：抽 SSOT 时 grep 三层：(1) 数据的旧位置文件名；(2) 数据中的关键标识符（如 `EXPECTED_IN_LFG`、skill id 列表）；(3) 调用旧 render 函数的地方。三层都列清单后再开工

## 2026-04-13 [模板] 占位符层次必须显式区分（避免双重替换）

- 场景：Issue #27 引入 `<<SKILL_DECISION_TREE>>` 等占位符做 skill 渲染。如果用 `{{SKILL_DECISION_TREE}}`，会和 harness 已有的 `{{var}}` jinja 占位符撞——templating.render_template 看到 SKILL_xxx 找不到 context 值，会替换为空串，skill 块永久消失
- 决策：渲染管道分层时，每层用专属占位符语法。harness 用 `{{var}}`（小写下划线），skills_registry 用 `<<SKILL_xxx>>`（双尖括号大写）。语法上互斥即可保证两个 render_template 调用顺序无关
- 根因：模板替换链条上"前一层吃掉后一层占位符"是常见 footgun，过去 lessons "模板中的文档占位符语法会被模板引擎吞掉" 是同一类问题。本次主动设计避免
- 规则：每加一层渲染管道（jinja → skill → ...），用一个未被任何已有层识别的占位符语法。简单测试：grep 现有所有 render_* 函数的正则，确认新语法不被任何一个匹配

## 2026-04-13 [流程] 280 行硬限触发时连环效应——3 个文件同时超

- 场景：Issue #27 加 SKILL 替换钩子时 cli.py + initializer.py + upgrade.py 同时超 280 行（CI 接连报 3 次）。每次只修一个就跑下一次 CI，再发现下一个文件超
- 决策：触发硬限时**一次性**检查所有相关文件（gather all `wc -l src/agent_harness/*.py | awk '$1 > 270'`），批量修
- 根因：280 行硬限是按文件检查，单次 CI 只报第一个超的文件。但同一次改动如果"复用模式"（每个钩子点都加 5 行 import + 调用），多个文件会同步逼近上限。修一个修不够
- 规则：触发"模块过长"硬限时，立刻 `wc -l src/agent_harness/*.py | sort -rn | head -10` 看全局，然后批量瘦/拆。配合提前抽公共函数（这次抽 `apply_to_rendered_dict` 救了 upgrade.py 和 dogfood.py 两个文件）

## 2026-04-14 [架构设计] 角色权限分层要从文档约束升级到运行时强制

- 错误：Issue #30 前，`/squad` 和 `/subagent-dev` 的 capability 分权只是文档约束（prompt 提示"orchestrator 不改代码"），没有运行时拦截。结果编排者常"顺手"改两行，绕过分工。
- 根因：光写在 prompt 里的约束是 soft rule，LLM 能合理化为"这次只是微调"；只有 `settings.local.json` 的 `permissions.deny` 才能让工具调用在运行时被 Claude Code 直接拒掉。
- 规则：新增 agent 角色时，**同时**要给出（1）文档角色卡 + 能力矩阵，（2）`capability.py` 里对应的 deny 列表 + 测试，（3）对外入口（spec 白名单、CLI 选项）。缺任何一层这个角色都不是"真的"有分权——要么被绕过，要么用不了。

## 2026-04-14 [架构设计] 子 agent 产出要从自由日志升级到结构化制品

- 错误：Issue #30 前，`harness agent diary` 是自由格式 Markdown，`aggregate` 只拼接。结果并行 sub-agent 的发现被埋在日志里，后续任务要重新 grep 才能复用——"并行干活"没升级为"累积智能"。
- 根因：没有结构化 schema 的日志不能被机器解析；人类读 aggregate 也要在几百行日志里挑出"值得复用的发现"——认知负担让知识复利失败。
- 规则：并行子 agent 场景一定要区分**过程日志**（自由写）和**知识制品**（结构化写）。制品至少要有 `type / summary / refs / content` 四个字段，供后续任务按 summary 选择、按 refs 引用。写成 `## artifact` 块在 diary.md 内嵌既保持向后兼容，又能被正则/解析器抽出。
