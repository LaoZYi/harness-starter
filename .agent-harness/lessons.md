# Lessons Learned

从错误和返工中提炼的教训。每条教训对应一个曾经犯过的错，包含根因和防止再犯的规则。

agent 开始任务前应快速浏览本文件，避免重蹈覆辙。

## 按分类索引

> 新增条目时在对应分类追加 anchor 链接。若出现新分类，在此表新增一行并同步 `/compound` 指令。anchor 规则见 `/compound` 指令第 4.5 步。

- **测试**: [文件锁顺序必须先锁再 truncate](#2026-04-12-测试-文件锁顺序必须先锁再-truncate)
- **模板**: [模板中的文档占位符语法会被模板引擎吞掉](#2026-04-09-模板-模板中的文档占位符语法会被模板引擎吞掉), [命令重命名后模板文件也要全量扫描](#2026-04-09-模板-命令重命名后模板文件也要全量扫描)
- **流程**: [进化去重必须覆盖已关闭 Issue](#2026-04-08-流程-进化去重必须覆盖已关闭-issue), [新增技能时文档散布计数需全量扫描](#2026-04-08-流程-新增技能时文档散布计数需全量扫描), [新任务覆盖前必须先关闭旧任务](#2026-04-09-流程-新任务覆盖前必须先关闭旧任务), [同一项目的增量吸收用 evolution-update 标签](#2026-04-12-流程-同一项目的增量吸收用-evolution-update-标签), [CLI flag 假设在 plan 阶段必须 source-verify](#2026-04-12-流程-cli-flag-假设在-plan-阶段必须-source-verify)
- **工具脚本**: [dogfood 命令展平](#2026-04-08-工具脚本-dogfood-命令展平), [重复工具函数提取后必须删除原始定义](#2026-04-09-工具脚本-重复工具函数提取后必须删除原始定义), [shell 命令构造必须-shlex-quote-所有路径](#2026-04-12-工具脚本-shell-命令构造必须-shlex-quote-所有路径), [守卫禁用白名单改自动发现](#2026-04-13-工具脚本-守卫禁用白名单改自动发现)
- **架构设计**: [脚手架项目吸收外部思想要选最小实现](#2026-04-12-架构设计-脚手架项目吸收外部思想要选最小实现), [POSIX-only 模块要 try-except 软导入](#2026-04-12-架构设计-posix-only-模块要-try-except-软导入), [统一入口技能必须串起全量能力](#2026-04-13-架构设计-统一入口技能必须串起全量能力), [自回环 hook 必须有人工放行开关](#2026-04-13-架构设计-自回环-hook-必须有人工放行开关)
- **集成API**: [GitLab Issue 搜索禁用 search 参数](#2026-04-08-集成api-gitlab-issue-搜索禁用-search-参数)

## 条目格式

```
## YYYY-MM-DD [分类] 一句话标题

- 错误：发生了什么
- 根因：为什么会发生
- 规则：以后怎么避免
```

---

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
