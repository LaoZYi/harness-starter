# Lessons Learned

从错误和返工中提炼的教训。每条教训对应一个曾经犯过的错，包含根因和防止再犯的规则。

agent 开始任务前应快速浏览本文件，避免重蹈覆辙。

## 按分类索引

> 新增条目时在对应分类追加 anchor 链接。若出现新分类，在此表新增一行并同步 `/compound` 指令。anchor 规则见 `/compound` 指令第 4.5 步。

- **测试**: [文件锁顺序必须先锁再 truncate](#2026-04-12-测试-文件锁顺序必须先锁再-truncate), [优先级契约测试必须覆盖所有优先级等级](#2026-04-20-测试-优先级契约测试必须覆盖所有优先级等级), [测试脚手架起 git subprocess 必须 env 隔离用户全局配置](#2026-04-20-测试-测试脚手架起-git-subprocess-必须-env-隔离用户全局配置), [改模板文本前必须 grep 现有测试是否锁定具体字符串](#2026-04-20-测试-改模板文本前必须-grep-现有测试是否锁定具体字符串), [涉及外部系统的功能单测 + 本地 mock ≠ 真实验证](#2026-04-21-测试-涉及外部系统的功能单测--本地-mock--真实验证), [用户命令执行的 shell 元字符安全必须用 sentinel 文件证明](#2026-04-21-测试-用户命令执行的-shell-元字符安全必须用-sentinel-文件证明), [用户数据保护类 bug 修复必须覆盖五类场景不是单点复现](#2026-04-21-测试-用户数据保护类-bug-修复必须覆盖五类场景不是单点复现)
- **模板**: [模板中的文档占位符语法会被模板引擎吞掉](#2026-04-09-模板-模板中的文档占位符语法会被模板引擎吞掉), [命令重命名后模板文件也要全量扫描](#2026-04-09-模板-命令重命名后模板文件也要全量扫描), [lfg 模板引用 NOT_IN_LFG 技能要避开 "运行 /xxx" 措辞](#2026-04-16-模板-lfg-模板引用-not_in_lfg-技能要避开-运行-xxx-措辞)
- **流程**: [进化去重必须覆盖已关闭 Issue](#2026-04-08-流程-进化去重必须覆盖已关闭-issue), [新增技能时文档散布计数需全量扫描](#2026-04-08-流程-新增技能时文档散布计数需全量扫描), [新任务覆盖前必须先关闭旧任务](#2026-04-09-流程-新任务覆盖前必须先关闭旧任务), [同一项目的增量吸收用 evolution-update 标签](#2026-04-12-流程-同一项目的增量吸收用-evolution-update-标签), [CLI flag 假设在 plan 阶段必须 source-verify](#2026-04-12-流程-cli-flag-假设在-plan-阶段必须-source-verify), [评估报告前必须先查合约测试](#2026-04-13-流程-评估报告前必须先查合约测试), [plan 阶段判 out-of-scope 前必须 grep 硬编码数字](#2026-04-16-流程-plan-阶段判-out-of-scope-前必须-grep-硬编码数字), [能力集成度评估必须用量化扫描而非主观判断](#2026-04-17-流程-能力集成度评估必须用量化扫描而非主观判断), [补强任务按 ROI 递减主动收手](#2026-04-17-流程-补强任务按-roi-递减主动收手)
- **工具脚本**: [_runtime 模块清单是 dogfood 的一部分](#2026-04-14-工具脚本-runtime-模块清单是-dogfood-的一部分), [dogfood 产物在 .claude 下默认 gitignore 需 force-add](#2026-04-14-工具脚本-dogfood-产物在-claude-下默认-gitignore-需-force-add), [dogfood 命令展平](#2026-04-08-工具脚本-dogfood-命令展平), [重复工具函数提取后必须删除原始定义](#2026-04-09-工具脚本-重复工具函数提取后必须删除原始定义), [shell 命令构造必须-shlex-quote-所有路径](#2026-04-12-工具脚本-shell-命令构造必须-shlex-quote-所有路径), [守卫禁用白名单改自动发现](#2026-04-13-工具脚本-守卫禁用白名单改自动发现)
- **架构设计**: [.claude/commands 下任何 .md 会被注册为 slash command](#2026-04-23-架构设计-claudecommands-下任何-md-都会被-claude-code-注册为-slash-command), [策略默认值在边界场景必须显式处理不得静默退化](#2026-04-21-架构设计-策略默认值在边界场景必须显式处理不得静默退化), [角色权限分层要从文档约束升级到运行时强制](#2026-04-14-架构设计-角色权限分层要从文档约束升级到运行时强制), [子 agent 产出要从自由日志升级到结构化制品](#2026-04-14-架构设计-子-agent-产出要从自由日志升级到结构化制品), [外部方法论吸收前必须做适用性裁剪](#2026-04-14-架构设计-外部方法论吸收前必须做适用性裁剪), [脚手架项目吸收外部思想要选最小实现](#2026-04-12-架构设计-脚手架项目吸收外部思想要选最小实现), [POSIX-only 模块要 try-except 软导入](#2026-04-12-架构设计-posix-only-模块要-try-except-软导入), [统一入口技能必须串起全量能力](#2026-04-13-架构设计-统一入口技能必须串起全量能力), [自回环 hook 必须有人工放行开关](#2026-04-13-架构设计-自回环-hook-必须有人工放行开关), [新异常类继承 ValueError 保向后兼容](#2026-04-13-架构设计-新异常类继承-valueerror-保向后兼容), [hook 依赖未公开 API 必须 source-verify 再决定降级](#2026-04-13-架构设计-hook-依赖未公开-api-必须-source-verify-再决定降级), [大 Issue 吸收要拆阶段 + atomic commit + step tag](#2026-04-13-流程-大-issue-吸收要拆阶段-atomic-commit-step-tag), [模块拆分前留好未来模块位置](#2026-04-13-架构设计-模块拆分前留好未来模块位置), [三源对账推导状态而非持久化 worker 状态](#2026-04-13-架构设计-三源对账推导状态而非持久化-worker-状态), [没 consumer 的基础设施重构是空转](#2026-04-13-流程-没-consumer-的基础设施重构是空转), [兼容层降低迁移成本](#2026-04-13-架构设计-兼容层降低迁移成本), [单入口技能能力接入完整](#2026-04-13-架构设计-单入口技能--能力接入完整), [Harness 反偷懒与协作记忆要解耦](#2026-04-13-架构设计-harness-中反偷懒与协作记忆模块要解耦), [抽 SSOT 时必须清单化所有下游消费方](#2026-04-13-架构设计-抽-ssot-时必须清单化所有下游消费方), [占位符层次必须显式区分](#2026-04-13-模板-占位符层次必须显式区分避免双重替换), [280 行硬限触发时连环效应](#2026-04-13-流程-280-行硬限触发时连环效应3-个文件同时超), [生产项目安全审计采用预防+兜底双重保障](#2026-04-17-架构设计-生产项目安全审计采用预防--兜底双重保障), [answers 与持久化 schema 分裂必须显式桥接](#2026-04-20-架构设计-answers-与持久化-schema-分裂必须显式桥接), [入口技能 gap 先用工具量化再动手](#2026-04-21-架构设计-入口技能-gap-先用工具量化再动手)
- **集成API**: [GitLab Issue 搜索禁用 search 参数](#2026-04-08-集成api-gitlab-issue-搜索禁用-search-参数)

## 条目格式

```
## YYYY-MM-DD [分类] 一句话标题

- 错误：发生了什么
- 根因：为什么会发生
- 规则：以后怎么避免
```

---

## 2026-04-21 [架构设计] 策略默认值在边界场景必须显式处理不得静默退化

- 错误：`harness upgrade apply` 的 `three_way` 分支，遇到 `.agent-harness/.base/<file>` 基线缺失时，代码直接 `output_path.write_text(new_content)` 把用户长期维护的 `docs/architecture.md`（用户写了 500 行 NestJS 架构图）整体覆盖为 40 行模板骨架。策略表和文档都声明该文件走 `three_way`（保留用户内容），但代码在缺 base 的边界条件下退化成了 `overwrite` 语义——而且没有任何警告，只是在 `backups/<ts>/` 留了备份（事后补救，用户发现时已经覆盖）
- 根因：**策略的"声明语义" ≠ "所有路径都实现这个语义"**。`three_way` = "保留用户内容 + 合并模板更新" 的声明，依赖 base 存在这个隐含前提。当前提破产时，代码没有显式处理"保护用户内容"这个根本目标，只是按"容易的出路"走了 overwrite。而 `_build_checklist` 里已经有 `nb = sum(... three_way and not base exists)` 在**统计**这种文件——说明开发者**意识到了这种情况存在**，但没把"意识到" 转化成"保护"
- 规则：改任何**有默认值的策略分支**前，对照三问：
  1. 默认策略的**核心目的**是什么？（`three_way` 是"保护用户内容"，不是"合并"——"合并"只是手段）
  2. 默认策略的**前提条件**有哪些？（`three_way` 的前提是 base 存在）
  3. 前提破产时，回到**核心目的**还是回到**最简单出路**？
  代码必须选 1。"最简单出路" 背后藏着用户数据损失。具体到 harness upgrade：缺 base 时不能用 overwrite 兜底，应改写旁路文件（`<file>.harness-new`）+ 警告，把决策权还给用户。策略通用化——不是维护"用户文档白名单"（列表永远不全），而是对所有 `three_way` 文件一视同仁。逃生口通过 `--force` 显式给出（用户明确知道"我要覆盖"）

## 2026-04-21 [测试] 用户数据保护类 bug 修复必须覆盖五类场景不是单点复现

- 错误：最初倾向于写 1-2 条测试复现 Issue #23 原始场景（500 行 NestJS 架构 + 缺 base → 被覆盖）就收工。但"保护用户内容"是**策略级**修复，不是单点 bug——如果只测一个场景，后续重构里任何路径回归都难发现
- 根因：用户反馈 bug 时给出的是**一个症状**，bug 背后的策略漏洞可能以多种形态出现（不同文件、不同操作序列、不同 base 状态）。单点测试只能锁住症状，锁不住策略
- 规则：涉及**用户数据保护**（覆盖/删除/迁移）的 bug 修复，测试必须覆盖五类场景：
  - **正常路径**：策略前提满足时行为不变（回归保护）
  - **边界**：策略前提破产时的"新保护行为"（本 bug 的核心）
  - **边界**：数据不存在时（应走 create，不触发保护）
  - **错误/逃生**：用户明确要覆盖时（`--force` 等逃生口工作正常）
  - **冲突/竞争**：连续操作、中间状态被篡改
  - **组合**：多文件、多次操作、状态恢复后的路径切换
  本次 10 条 R-ID（R-001..R-010） + 5 场景 19 check 端到端穷举是最低标准。用户数据一次丢失 = 失去信任，测试密度必须匹配风险密度


- 错误：给 `harness init --scaffold-cmd "<命令>"` 设计时，只在文档和注释里写「我们用 `shlex.split` + `subprocess.run(argv, shell=False)`，所以 shell 元字符不会被解释」。一旦未来有人手误改成 `shell=True`，或换到某个包装 shell 的库，文档描述就悄悄失效，用户的 `; rm -rf <path>` 就真的能被执行。
- 根因：「我们用 argv 所以安全」是**实现细节级**的承诺，看代码才能验证。没有**行为级**断言时，任何重构都可能静默破坏安全属性。
- 规则：凡是「用户输入的字符串最终要 exec」的场景，测试里必须放一个**sentinel 文件**——先在文件系统上创建一个具名文件，构造一个「如果 shell 解释元字符就会删除/修改它」的命令（如 `sh -c 'echo ok' _ ; rm -rf <sentinel>`），执行后断言 sentinel 仍存在、内容不变。这把安全契约从文档承诺锁定为运行时行为。扩展到：任何 `subprocess` / `os.system` / `exec*` 场景，写「如果走 shell 会怎样」的反例测试，比写「我走了 argv」的正例更有效。

## 2026-04-21 [测试] 涉及外部系统的功能单测 + 本地 mock ≠ 真实验证

- 错误：做 `harness init --scaffold <git_url>` 时，我跑了 17 条单元测试全绿（含 1 条 CLI subprocess 端到端），就向用户报了「实施完成，待验证」。用户反问「你自己测试过吗？」——我才意识到 17 条都是**本地 bare repo 模拟远端**，从未在真实 GitHub 仓库上跑过。结果跑真实 `https://github.com/LaoZYi/harness-starter.git` 时倒是通过了，但我**没法提前保证**——如果真实网络层 + GitHub smart protocol 有差异（比如重定向 / redirect-auth / 特定 CA），模拟就会骗我
- 根因：本地 `git init --bare` + `file://` 路径的 clone 走 local transport，和 `https://` 的 smart transport 是**不同代码路径**。单元测试只验证了程序在 local transport 下的正确性，没验证在真实 transport 下的行为。虽然 `git clone` 在项目层对这俩透明，但"透明"不等于"等价"——任何透明层都可能有 bug 或边界行为
- 规则：**任何涉及外部系统（网络 / 进程 / API / 文件系统外部路径）的功能，完成条件不是「单测 + 本地 mock 全绿」，而是「单测 + 本地 mock 全绿 + 至少一次真实外部源跑通」**。流程加一步：实现完成 → 单测全绿 → **真实 smoke test**（挑一个真实可访问的外部目标跑一次关键路径）→ 才能 claim「待验证」。若真实源不可访问（CI 等），在完成报告里显式声明「未做真实外部验证，仅本地模拟」让用户知情
- 适用场景：网络类（git clone / HTTP API / WebSocket）、外部进程（调用第三方 CLI）、外部文件系统（跨主机挂载、云存储）、外部服务（数据库、消息队列、缓存）

## 2026-04-20 [测试] 改模板文本前必须 grep 现有测试是否锁定具体字符串

- 错误：给 `/lint-lessons` 模板加 resolution-type 字段时，把「铁律」段的原文案「每对候选必须给出裁决建议（4 选 1）：保留 A 删 B / ...」改写成了「每对候选必须同时给出：症状分类 + resolution-type + 建议动作」，导致 `tests/test_gsd_absorb.py::test_lint_lessons_has_contradiction_detection` 失败——它通过 `assertIn("保留 A", text)` 锁定了原文案。自己的 14 条新测试全绿，但 make test 全跑时被全局回归抓出
- 根因：同仓多个测试文件对同一 template 有**互不知情的字符串锁定**。TDD 写新测试时只看到自己的契约，看不到别处对"这段 template 某字符串"的隐式依赖；普通 grep 又因为字符串可能散落在多个测试文件，要专门搜 `assertIn.*<某短语>` 才能暴露
- 规则：改任何 template / rule 文件的**具体字符串**（不是结构性重构）前，必做两步：
  1. `grep -r 'assertIn.*<目标文件名stem>' tests/` 找出所有对该文件做字符串断言的测试
  2. 列出被锁定的字符串清单，改动时保留（或同步更新对应测试）
  这比"改完再跑全量测试靠回归抓"成本低——全量测试跑 12 秒，但期间如果 dogfood 已同步，`.claude/` 产物已经被污染，还得 revert dogfood 产物。预防比事后修复便宜
- 适用场景：改任何 `templates/**/*.md.tmpl`、`.claude/rules/*.md`、`AGENTS.md`、`docs/*.md` 的文本内容时；改 CLI 输出字符串时；改用户可见的错误消息时

## 2026-04-20 [测试] 测试脚手架起 git subprocess 必须 env 隔离用户全局配置

- 错误：`make test` 在某开发者机器上批量失败（GitLab #21：27 ERROR + 1 FAIL），全部是临时仓库里的 `git commit`。根因是该用户本地全局 gitconfig 带了 pre-commit hook / `core.hooksPath` 指向强制校验目录（他们自己的协作流程要求"必须走 worktree 分支"）。原 `tests/_git_helper.init_git_repo` 只设了 local `user.email/name` 和 `commit.gpgsign=false`，没屏蔽全局配置，hook 继承下去直接 `exit 1`；同一问题也让 `tests/test_cli.py::_run_harness` 调的 `harness init --git-commit` 内部 commit 被拦，`cli_utils.maybe_git_commit` 捕获后降级为 warning，`git log` 为空，`test_git_commit_flag` 断言失败
- 根因：`subprocess.run(["git", ...])` 默认继承整个 `os.environ`，git 会读 `~/.gitconfig`、`/etc/gitconfig`、以及 `GIT_*` 环境变量指向的配置。local repo config 只能覆盖**同名键**，没法阻止全局 `core.hooksPath` 或 pre-commit 这类带副作用的指令生效
- 规则：任何测试脚手架起 git 子进程时，env 必须同时带 `GIT_CONFIG_GLOBAL=/dev/null` 和 `GIT_CONFIG_SYSTEM=/dev/null`（git 官方支持的完全隔离入口，不依赖 local config 能否"反向覆盖"）。封装成 `isolated_git_env()` 公共 helper，所有 git 子进程走它；不允许各测试自己 inline `subprocess.run(["git", ...])` 绕开。新增跨边界测试（测试→subprocess 工具→其内部 git）时，工具的 env 也要透传这套隔离
- 适用场景：任何需要在临时目录 `git init` + commit 的测试；调用 CLI 工具（工具内部会跑 git）的集成测试；CI 机器和开发者机器 git 配置差异大的跨平台项目；类似的"子进程继承父 env"踩坑（SSH agent、npm rc、pip config、shell rc 等）

## 2026-04-20 [架构设计] answers 与持久化 schema 分裂必须显式桥接

- 错误：`harness upgrade apply` 把用户 project.json 里的 `项目名 / 类型 / 包管理器` 全部渲染成了启发式默认值，因为 `_resolve_answers` 只查 CLI / `.harness.json` / discover profile，**跳过了 `.agent-harness/project.json`**。即便后续补了读取，还踩了第二坑——project.json 的 schema 用 `project_summary` / `commands.run` 嵌套结构，`_resolve_answers` 用扁平键 `summary` / `run_command`，直接 `key in project_json` 对不上。`verify_upgrade` 的 sentinel 检查也栽在同一处
- 根因：init 时 `initializer.py` 用扁平 answers 渲染成嵌套 project.json（rendered schema 优化给人读），但 upgrade 时又要把嵌套结构反向映射回扁平 answers——两个命名空间没有 SSOT 桥接层，任何读 project.json 的地方都得自己重写映射逻辑，最容易忘
- 规则：任何「持久化到磁盘的结构」和「in-memory 使用的扁平键」不一致时，必须写一个 **归一化函数** 作为唯一入口（本项目是 `cli_answers.load_project_json`）。所有消费者——`_resolve_answers` / `verify_upgrade` / 未来新增读取方——都走这个函数，禁止各自解包。测试要覆盖「只填部分字段」「schema 字段缺失」「schema 损坏」三类边界
- 适用场景：任何 init→write→read-back 循环的 CLI 工具；rendered template 与 source-of-truth 双存储；configuration-driven 框架

## 2026-04-20 [测试] 优先级契约测试必须覆盖所有优先级等级

- 错误：写 `_resolve_answers` 的优先级契约测试时，只写了"CLI > project.json"和"config > project.json"，没写"project.json > profile(discover)"的 fallthrough 链。结果 schema 映射错误的 bug 没被这组测试抓到，跑全量 E2E 才发现
- 根因：优先级链是"N 级偏序关系"，相邻两级契约不能互相推导出全局正确性（例：CLI > profile 和 config > profile 都通过，不代表 config > project_json > profile 链路正确）
- 规则：N 级优先级链要写 N-1 条 "A 赢 B" 测试 + 1 条 "全无 A/B/C 时 fallthrough 到 D" 测试，**外加**一个端到端测试走完整链路。不要相信"相邻契约 + fallthrough 自证"——它不自证
- 适用场景：config 合并、环境变量覆盖、feature flag 层级、insurance policy fallback

## 2026-04-17 [流程] 能力集成度评估必须用量化扫描而非主观判断

- 错误：评估 /lfg 是否"充分发挥项目威力"时，第一反应是通读 lfg.md.tmpl 凭感觉打分。结果漏掉了 Issue #34 Environment Engineering（0 次引用）、Issue #33 claude-code-internals（0 次）、Issue #30 Trust Calibration / orchestrator / knowledge artifacts（0 次）、4 个 hooks（都是 0 次）等大量"已吸收但未显式声明"的能力
- 根因：主观评估会把"能力存在"与"能力被主动使用"混为一谈。吸收一个 Issue 时改了吸收产物（规则/命令/参考文件），但统一入口技能的引用没同步更新——主观通读时看见"有相关段落"就以为覆盖了，实际没落到引用计数上
- 规则：评估任何"统一入口 / 能力聚合器"技能的集成度时，先写扫描脚本用 `grep -c <关键词>` 统计每个能力被引用的次数，0 次的能力打补丁说明；然后按"技能覆盖 / 阶段流程 / 运行时能力集成 / 新特性集成度 / hooks 协作"等维度加权评分。数据驱动的打分比"通读后感觉"可靠 10 倍
- 适用场景：/lfg 威力评估、/which-skill 决策树完整性、/compound lessons 分类覆盖度，以及任何 "入口 × N 种能力" 的矩阵问题

## 2026-04-17 [架构设计] 生产项目安全审计采用"预防 + 兜底"双重保障

- 错误：最初 /lfg 的 /cso 安全审计只在阶段 7.4（验证期）执行一次。对生产项目而言，如果 /cso 发现 Critical/High 问题，已经实施完代码才被打回阶段 4 重做，成本很高
- 根因：事后审计是"兜底"模式——问题发生了才发现；但生产项目的风险识别应该前置为"预防"模式——在计划期就把风险作为约束内化进计划，让实施阶段直接绕开高风险路径
- 规则：对"有兜底机制的风险识别能力"（安全/性能/兼容性审计类），考虑前置一次到**计划期**形成双重保障：计划期用快速扫识别风险区并写进计划的 Non-goals 或"约束"段，兜底期用完整审计防漏网。生产项目（has_production=true 或 sensitivity=high）强制启用双重保障，非生产项目可只保留兜底
- 代价：预防期会增加 5-10 min 审计时间，但省掉潜在的返工。ROI 明显为正

## 2026-04-17 [流程] 补强任务按 ROI 递减主动收手

- 错误：/lfg 威力补强从 7.5 → 8.75（+1.25）又到 9.56（+0.81），计划继续推到 9.75，但最后 0.19 分缺口要动大量跨仓库细节（git-cliff 直通、Environment Engineering 深度嵌入等），ROI 极低
- 根因：补强任务有天然递减规律——前几项弥补"明显缺口"ROI 很高，后几项需要"完美主义"动改动扩散，ROI 接近 0。不识别拐点就会无限加码
- 规则：补强任务每轮结束后**重新跑一次量化评估**（复用"能力集成度评估"扫描脚本），对比"新增引用数 vs 代码改动量"。一旦 ROI（加分/工作量）低于 1:1 就主动收手，诚实报告当前分数而非硬追承诺值。本次承诺 9.75 实际 9.56，差 0.19，诚实报告并说明原因比"强撑到 9.75"有价值
- 预防：任何"从 N 推到 M"的补强任务，开头就列出"ROI 递减识别信号"——比如"改动扩散 > 3 个仓库、或单项加分 < 0.3、或工作量 > 1h / 0.1 分"。到信号后自动收手

## 2026-04-16 [流程] plan 阶段判 out-of-scope 前必须 grep 硬编码数字

- 错误：/digest-meeting 规划阶段把"既有测试更新"(R9) 判为 out-of-scope，理由是 `test_lfg_coverage.py` 用 glob 扫描不数数字。但 `test_skills_registry.py` 硬编码了 `skill_count == 35` 和 `len(in_lfg) + len(not_in) == 35`。实施到 CI 阶段才发现，打回修改。
- 根因：调研阶段只看了 `test_lfg_coverage.py`（最明显的候选），没 grep 所有测试文件里的 magic number 对 skill 总数的引用。"SSOT 下游清单化"原则落到实处不彻底。
- 规则：新增/删除 skill 前，**必须**在 `tests/` 下 grep 所有涉及 skill 计数的硬编码数字（`grep -n "\\b35\\b\\|len.*skills.*==" tests/test_skills*.py`），把所有需要同步的地方列到 plan 里，而不是假设"一个契约测试能覆盖所有"。同类规则适用于任何 SSOT 变更：不只看最明显的下游，要 grep 到所有消费方。

## 2026-04-16 [模板] lfg 模板引用 NOT_IN_LFG 技能要避开 "运行 /xxx" 措辞

- 错误：在 lfg.md.tmpl 里加"然后你可以再次**运行** `/lfg`"，被 `test_not_in_lfg_entries_really_absent_from_call_sites` 捕获报错——该测试防止 NOT_IN_LFG 分类的 skill（包括 /lfg 自己作为 self-reference）被 LFG 主动调用。
- 根因：`/lfg` 自己在 `expected_in_lfg=false`（避免无限递归），但 lfg.md.tmpl 里其他段落引用自己是正常的 self-reference。测试用 `运行 \`{skill}\`` 正则简单粗暴卡主动调用，无法区分"self-reference 提示语"和"lfg 真的要调用自己"。
- 规则：在 lfg.md.tmpl 里提到 `/lfg` 自己或其他 NOT_IN_LFG 技能（/evolve / /health / /retro / /process-notes / /digest-meeting 等）时，避开"**运行** `/xxx`"措辞，改用"调用 `/xxx`"、"跑 `/xxx`"、"用 `/xxx`" 等。

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
- 规则：凡是宣称为"统一入口"的技能（/lfg、/which-skill 这类），必须有契约测试：EXPECTED_IN + EXPECTED_NOT_IN 两个集合，并集等于当前全部技能清单；新增技能时测试失败强制做分类决策。模板末尾应有"覆盖清单"表作为自检锚点
- **补充（2026-04-17）**：不只是技能，**非技能能力**（hooks / 运行时 bin 脚本 / references checklist / Trust Calibration 规则段）同样适用——它们在 harness 框架层面已经在工作，但入口技能若 0 引用 → AI 无法主动配合。补救办法：每吸收一个新 Issue 后扫 `grep -c <关键词> lfg.md.tmpl`，引用次数为 0 的能力必须在 lfg 对应阶段显式声明协作方式

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

## 2026-04-21 [架构设计] 入口技能 gap 先用工具量化再动手

- 错误：过去评估 /lfg 是否"发挥全部威力"靠主观阅读模板 + grep——要么漏掉维度（如 rules 覆盖、audit WAL 命令、hook 隔离），要么夸大了实际落地
- 根因：单入口技能的完整性是个**多维问题**（rules + skills + memory + 反偷懒门禁 + stuck + agent + audit + docs + compound + context budget），人脑同时跟踪 10 个维度易漏；加新能力时惯性只看"技能编排"一个维度
- 规则：新加能力前后都跑 `harness lfg audit`——总分退步或某维度分下降就是信号；绝不在「直觉上觉得 /lfg 已经全面」时跳过。配套：维护 10 维 scorecard（`src/agent_harness/lfg_audit_checks.py`），每加一类新能力就加一维检查。本次用 audit 10 分钟内定位 `knowledge-conflict-resolution.md` 未反哺 gap → 3 行精准接入 → 工具验证 9.9→10.0，全流程闭环可复现

## 2026-04-23 [架构设计] `.claude/commands/` 下任何 .md 都会被 Claude Code 注册为 slash command

- 错误：吸收 OpenViking 目录分层摘要时，第一版把 `.claude/commands/` 放进 ABSTRACT/OVERVIEW 白名单。`make dogfood` 生成两个文件后，session 下一条 system-reminder 立刻显示新增了 `/ABSTRACT` 和 `/OVERVIEW` 两个无意义的 slash command，污染 skill 列表
- 根因：Claude Code 对 `.claude/commands/` 下任何 `.md` 文件**无差别注册**为 slash command——不看文件名约定（全大写 / 下划线前缀 / 非 skill 形态都无效），也不看是否有 frontmatter。这是 Claude Code 的平台硬约束，不受项目自身规则控制
- 规则：
  1. 任何"目录导航 / 索引 / 元数据 / README / 分类导航"类文件**禁止**放 `.claude/commands/`，即便命名非常规
  2. 技能的分类导航由 `.claude/rules/<workflow>.md`（如 `superpowers-workflow.md`）承担，或放在 `.claude/` 根下的非 commands 子目录
  3. `.claude/commands/` 下只放**用户主动触发的 slash command 定义文件**，文件名即命令名
  4. 涉及 `.claude/commands/` 新增文件的改动，dogfood 后**必须看一眼** system-reminder 的 skill 列表有无异常新增
  5. 本规则已固化到 `.claude/rules/documentation-sync.md` 反模式段 + `tests/test_directory_maps.py::DirectoryMapRuleTests::test_rule_warns_against_claude_commands_dir` 回归锁定
