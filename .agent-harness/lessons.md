# Lessons Learned

从错误和返工中提炼的教训。每条教训对应一个曾经犯过的错，包含根因和防止再犯的规则。

agent 开始任务前应快速浏览本文件，避免重蹈覆辙。

---

## 2026-04-08 dogfood 命令展平

- 错误：dogfood 生成的技能文件中显示 `python -m unittest discover` 而非 `make test`，所有 25 个文件都用了 auto-discovery 的命令而非 project.json 配置的
- 根因：`project.json` 用嵌套结构存命令（`"commands": {"test": "make test"}`），但 `dogfood.py` 和 `check_repo.py` 直接透传给 `prepare_initialization()`，后者期望扁平 key（`"test_command"`）。嵌套 key 查不到就 fallback 到 auto-discovery
- 规则：凡是读 `project.json` 后调用 `prepare_initialization()` 的地方（目前有 dogfood.py 和 check_repo.py），都必须先展平 `commands` 字典。新增类似调用时同理

## 2026-04-08 进化去重必须覆盖已关闭 Issue

- 错误：`/evolve` 只检查 open Issue 去重，已吸收（closed）的项目会在下次搜索中被重新提案
- 根因：`gh issue list` 默认只返回 open 状态，需要显式传 `--state all`
- 规则：进化去重必须检查 open + closed 两种状态。同时需要区分"新发现"（evolution 标签）和"已吸收项目有更新"（evolution-update 标签）两条通道

## 2026-04-08 GitLab Issue 搜索禁用 search 参数

- 错误：LFG 收尾关闭 GitLab Issue 时用 `search=architecture-decision-record` 查找对应 Issue，返回空结果，导致 GitLab Issue 未同步关闭
- 根因：GitLab API 的 `search` 参数对中文标题和混合语言内容匹配不可靠，无法可靠找到目标 Issue
- 规则：查找 GitLab Issue 时必须用 `labels` 过滤缩小范围，再在本地用 Python 做标题子串匹配。禁止依赖 GitLab API 的 `search` 参数

## 2026-04-08 新增技能时文档散布计数需全量扫描

- 错误：新增 `/spec` 技能后，技能数从 27 变 28，但 12+ 处散布的计数引用容易遗漏
- 根因：技能计数硬编码在 CHANGELOG、README、docs/、templates/ 等多个文件中，没有单一来源
- 规则：新增技能后必须 `grep "N 个"` 全量扫描确认无遗漏。长期可考虑在 check_repo.py 中加计数一致性校验

## 2026-04-09 新任务覆盖前必须先关闭旧任务

- 错误：用户触发 `/lfg #9` 时，current-task.md 中有"待验证"状态的三方合并任务，直接覆盖导致旧任务的 task-log 记录丢失
- 根因：没有遵守 task-lifecycle 规则中的"如果有未完成任务，先询问用户：继续还是替换"。即使用户明确要做新任务，也应该先对旧任务做收尾（写 task-log）再替换
- 规则：覆盖 current-task.md 前，如果旧任务状态为"待验证"且所有 checkbox 已完成，必须先补写 task-log 记录再替换。绝不能静默丢弃已完成的工作记录

## 2026-04-09 重复工具函数提取后必须删除原始定义

- 错误：将 `_slugify` 提取到 `_shared.py` 后，三个模块各自保留了一个 `def _slugify(v): return slugify(v)` 的无用包装函数
- 根因：提取时只添加了新导入和替换了实现体，没有检查调用点是否还在用旧的私有名称
- 规则：提取公共函数后，必须 grep 确认旧定义全部删除、调用点全部改为直接调用新函数。不要留包装函数

## 2026-04-09 模板中的文档占位符语法会被模板引擎吞掉

- 错误：shared-plugins/README.md.tmpl 里写了 `{{variable}}` 作为文档示例，但模板引擎把它替换成了空串
- 根因：模板引擎对所有 `{{ }}` 做替换，没有转义机制区分"真占位符"和"文档中的示例"
- 规则：模板文件中不要用 `{{xxx}}` 作为文档示例文本，改用文字描述或反引号内放不匹配正则的变体

## 2026-04-09 命令重命名后模板文件也要全量扫描

- 错误：将 `sync-context` 重命名为 `sync` 后，docs/ 和 AGENTS.md 更新了，但 templates/meta/ 下的 4 处引用未更新
- 根因：只搜索了 docs/ 和项目根的 .md 文件，遗漏了 src/agent_harness/templates/ 目录
- 规则：重命名 CLI 命令后，必须对整个仓库（含 templates/）执行 `grep -r "旧命令名"` 确认零残留

## 2026-04-12 同一项目的增量吸收用 evolution-update 标签

- 场景：addyosmani/agent-skills 在 Issue #6（2026-04-08）已首次吸收；2026-04-12 对其增量更新做二次吸收，创建 Issue #16
- 根因：已关闭的 evolution Issue 不应重复提案（evolve 去重规则），但"同一项目有新价值"这条通道需要独立标识
- 规则：增量吸收用 `evolution-update` + `absorbed` 双标签（Issue #16 已使用），避免与首次吸收的 `evolution` 通道混淆。`/evolve` 搜索时分别查两个通道

## 2026-04-12 脚手架项目吸收外部思想要选最小实现

- 场景：吸收 MemPalace 的四层记忆栈时，候选方案从"目录分层+Python 抽象层"（完整移植）到"单索引文件"（最小方案）
- 决策：选方案 C（memory-index.md 精华索引 + `/recall` 按需展开），而非方案 B（目录分层）或方案 D（MemPalace layers.py 移植）
- 根因：本项目是**脚手架生成器**，不是运行时系统；运行时系统用分层是为了动态 rotate，脚手架用分层是为了约束 AI 读什么——两者的痛点不同，"完整移植"反而是过度工程
- 规则：从外部项目吸收思想前，先问"对方的痛点是否和我们一致？" 脚手架项目倾向选最轻的实现（单文件 > 目录结构 > Python 抽象层）。迁移成本低 + 与现有数据结构兼容 > 理论上的完备性

