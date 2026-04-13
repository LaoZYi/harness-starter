# Task Log

每次完成一个任务后，在文件末尾追加一条记录。

任务记录格式：

```
## YYYY-MM-DD 任务简述

- 需求：用户原话或一句话概括
- 做了什么：具体改动摘要
- 关键决策：为什么选了这个方案（如有取舍）
- 改了：涉及的文件列表
- 完成标准：本次新通过的 checkbox
```

返工/反馈记录格式：

```
## YYYY-MM-DD 返工：xxx

- 用户反馈：原话
- 调整了什么：具体改动
- 改了：涉及的文件列表
```

---

## 2026-04-08 进化集成：addyosmani/agent-skills（Issue #6）

- 需求：从 addyosmani/agent-skills 吸收反合理化机制和 spec-driven-development 到框架
- 做了什么：
  - 新建 `/spec` 技能模板（四阶段门控流程：规格→计划→任务→实施）
  - 为 `/tdd`、`/verify`、`/multi-review` 各添加 6 条反合理化表
  - LFG 流水线插入阶段 2.5（规格定义）
  - 更新决策树、工作流规则、evolve 对比表
  - 技能数 27 → 28，12+ 处文档数字同步
- 关键决策：
  - 渐进式披露（第三个吸收项）标记为后续工作，因为涉及现有技能文件结构重构，工作量大且风险高
  - 反合理化表每个技能统一 6 条，格式为"你想说的 | 为什么不行"
  - `/spec` 阶段在 LFG 中设为可选（需求已明确时可跳过），避免过度流程化
- 改了：spec.md.tmpl(新建), tdd.md.tmpl, verify.md.tmpl, multi-review.md.tmpl, lfg.md.tmpl, use-superpowers.md.tmpl, superpowers-workflow.md.tmpl, evolve.md.tmpl, test_superpowers.py, CHANGELOG.md, README.md, docs/architecture.md, docs/product.md, docs/usage-guide.md, project.json, current-task.md
- 完成标准：
  - [x] 3 个技能有反合理化表
  - [x] /spec 模板存在且占位符完整
  - [x] LFG 有规格定义阶段
  - [x] 82 测试通过，make ci 全绿
  - [x] 27→28 数字全部同步
  - [x] dogfood 同步完成
  - [x] GitHub Issue #6 已关闭

## 2026-04-08 Issue #6 后续修复（深度检查 + 用户反馈）

- 需求：用户提出已吸收项目重复提案问题 + 深度检查发现 8 个问题 + dogfood 命令不一致
- 做了什么：
  - evolve 去重：检查 open + closed 的 evolution Issue
  - evolve 更新监控：新增 evolution-update 标签通道，已吸收项目有新特性时单独提案
  - evolve 5 处修复：URL 正则剥离 .git、30 天过期防死锁、补 update Issue 模板、报告加已吸收段、limit 100→500
  - spec.md.tmpl：硬编码 `...` 改为 `{{run_command}}`
  - usage-guide.md：4 处工作流图/表补 /spec
  - dogfood.py + check_repo.py：展平 project.json 嵌套 commands 字典
- 关键决策：dogfood 修复放在脚本层（展平 dict），不改 initializer（保持其接口契约）
- 改了：evolve.md.tmpl, spec.md.tmpl, docs/usage-guide.md, scripts/dogfood.py, scripts/check_repo.py
- 完成标准：
  - [x] make ci 全绿
  - [x] 25 个技能文件命令从 auto-discovery 切换为 project.json 配置
  - [x] 3 条教训写入 lessons.md

## 2026-04-08 进化集成：joelparkerhenderson/architecture-decision-record（Issue #7）

- 需求：从 architecture-decision-record 吸收 ADR 方法论到框架，创建 `/adr` 技能
- 做了什么：
  - 新建 `/adr` 技能模板（MADR 格式，3 种模式：创建/查看/更新，含反合理化表）
  - 新建 `docs/decisions/.gitkeep.tmpl` 目录占位符
  - LFG 流水线 3 处集成：Phase 0 读 ADR、Phase 3 创建 ADR、Phase 9 更新状态
  - 更新决策树、工作流规则、evolve 对比表
  - 技能数 28 → 29，15+ 处文档数字同步
  - 评审后补充 2 个测试断言（disabled 时 decisions 不存在、workflow rule 含 /adr）
- 关键决策：
  - ADR 目录放在 superpowers 模板下而非 common，保持 `--no-superpowers` 能完全关闭
  - MADR 模板简化（去掉 Links 段），聚焦决策核心四要素
  - LFG 集成点选择 Phase 0/3/9 而非单独阶段，避免流程膨胀
- 改了：adr.md.tmpl(新建), .gitkeep.tmpl(新建), lfg.md.tmpl, superpowers-workflow.md.tmpl, use-superpowers.md.tmpl, evolve.md.tmpl, test_superpowers.py, README.md, CHANGELOG.md, docs/product.md, docs/architecture.md, docs/usage-guide.md, .agent-harness/project.json
- 完成标准：
  - [x] adr.md.tmpl 存在且占位符完整
  - [x] LFG 阶段 0/3/9 含 ADR 集成点
  - [x] 技能数 29 全部同步
  - [x] 83 测试通过，make ci 全绿
  - [x] dogfood 同步完成
  - [x] GitHub Issue #7 待关闭

## 2026-04-09 升级三方合并策略 — 让 harness upgrade 保留用户内容

- 需求：升级时保留用户编辑的内容，不要粗暴覆盖
- 做了什么：
  - 文件分类策略：overwrite/skip/three_way/json_merge 四种升级方式
  - 三方合并算法（_merge3.py）：merge3() 行级文本合并 + json_merge() 结构化合并
  - 冲突标记（<<<<<<< 当前内容）+ CLI 醒目红色提示
  - init 时存储基线到 .agent-harness/.base/
  - 老项目（无 .base/）退化为备份+覆盖
  - verify_upgrade() 验证升级结果
- 关键决策：
  - 基线存储在 .agent-harness/.base/ 而非 .git，避免对版本控制的侵入
  - 冲突标记使用中文（"当前内容"/"新内容"）便于理解
  - 老项目无基线时优雅退化，不阻塞升级
- 改了：upgrade.py, _merge3.py(新建), initializer.py, cli.py, tests/test_upgrade.py 等
- 完成标准：
  - [x] skip 文件升级时不被覆盖
  - [x] three_way 文件用户编辑在升级后保留
  - [x] json_merge 文件用户自定义 key 不丢失
  - [x] 冲突时 CLI 醒目红色提示
  - [x] init 时存储基线到 .agent-harness/.base/
  - [x] 老项目（无 .base/）升级时退化为备份+覆盖
  - [x] make ci 全绿（104 tests）

> 注：此记录为补录。原任务在"待验证"状态时被 /lfg #9 覆盖，收尾步骤遗漏。

## 2026-04-12 agent-skills 增量吸收（Issue #16，续 Issue #6）

- 需求：对已吸收项目 addyosmani/agent-skills 做增量分析，吸收新价值点
- 做了什么：
  - 新技能 `/source-verify`（193 行）—— `DETECT → FETCH → IMPLEMENT → CITE` 四阶段，防止 AI 凭记忆编框架 API
  - `.agent-harness/references/` 四个 L2 checklist（a11y / perf / security / testing-patterns），688 行，序言汉化 + 术语保留英文
  - `task-lifecycle.md` 顶部新增"上下文分层原则"理论章节（5 级 Context Hierarchy + L0-L4 映射）
  - `/recall` 扩展 `--refs` flag，默认搜索范围扩到 `lessons + task-log + references`
  - `memory.py` 加 `_scan_references()`，`rebuild_index` 输出新"## 参考资料"段
  - backend-service / web-app 类型规则分别追加 security+perf / a11y+perf 清单引用
  - upgrade 分类：`references/*` → `three_way`（允许用户定制 + 保留上游更新）
  - 决策树 + superpowers-workflow 登记 /source-verify 和 /recall
  - 新增 11 测试：192 → 203
  - check_repo.py 守卫 5 个新文件
- 关键决策：
  - `/source-verify` 独立技能（非融入 /tdd）— 语义独立，融入会让 /tdd 臃肿
  - references 放 `.agent-harness/`（非 `.claude/`）— 与 lessons/task-log 同层，L2 定位
  - checklist 序言汉化、术语保留英文（LCP/TTFB/WCAG/OWASP） — 兼顾可读性和精准
  - 默认 /recall 范围扩到 references，新增 --refs flag 做收窄（非破坏性）
  - context-engineering 做理论章节不做技能 — 它是元规则不是操作步骤
  - Issue 标签 evolution-update + absorbed 双标签，区分首次吸收（evolution）
  - 不吸收 3 个 subagent、hook 增强、code-simplification 等（已有覆盖或延后）
- 改了（commit 范围 327873c..55a6ea7，共 12 commit）：
  - 新建：source-verify.md.tmpl、4 个 references/*.md.tmpl、test_references.py、spec、plan
  - 修改：upgrade.py、cli.py 无改动但 memory.py +60 行、recall.md.tmpl、compound.md.tmpl（已在 #10 改）、task-lifecycle.md.tmpl、use-superpowers.md.tmpl、superpowers-workflow.md.tmpl、backend-service.md.tmpl、web-app.md.tmpl、check_repo.py、test_memory.py、test_superpowers.py、memory-index.md.tmpl
  - 文档：product.md、architecture.md、runbook.md、AGENTS.md、CHANGELOG.md、workflow.md、release.md、CONTRIBUTING.md、lessons.md
- 完成标准：
  - [x] /source-verify 技能存在，反合理化表 6 条
  - [x] references/ 4 文件，init 时自动生成
  - [x] task-lifecycle 含 Context Hierarchy 章节
  - [x] /recall --refs 生效
  - [x] 类型规则引用 references
  - [x] 203 测试全过
  - [x] make ci 全绿
  - [x] dogfood 同步
  - [x] 文档全量同步
  - [x] 用户验证通过


## 2026-04-09 进化集成：spencermarx/open-code-review（Issue #9）

- 需求：从 open-code-review 吸收评审辩论（Discourse）方法论到 /multi-review 技能
- 做了什么：
  - /multi-review 新增 Step 3.5（大变更集导航地图，20+ 文件时触发）
  - /multi-review 新增 Step 4（Discourse Round），定义 AGREE/CHALLENGE/CONNECT/SURFACE 四种辩论操作
  - 评审报告增加辩论轮摘要行
  - evolve 对比表中 /multi-review 更新描述
  - session-start.sh 模板移除 evolution cron 检查（用户要求改为手动触发 /evolve）
  - 测试数 104→105，文档计数同步
- 关键决策：
  - 辩论轮设为智能简化：P0/P1 不超过 2 个时自动简化为快速确认，避免小 PR 过度流程化
  - 不新增技能数量，作为 /multi-review 内部增强
  - 导航地图阈值设为 20 文件，参考 open-code-review 的设计
- 改了：multi-review.md.tmpl, evolve.md.tmpl, session-start.sh.tmpl, test_superpowers.py, docs/architecture.md, CHANGELOG.md, docs/release.md
- 完成标准：
  - [x] Discourse Round 含 AGREE/CHALLENGE/CONNECT/SURFACE
  - [x] 大变更集导航地图（20+ 文件）
  - [x] 105 测试通过，make ci 全绿
  - [x] dogfood 同步完成
  - [x] GitHub Issue #9 已关闭
  - [x] GitLab Issue #4 已关闭

## 2026-04-09 深度审计 + meta 项目类型 + harness sync 命令

- 需求：深度分析项目潜在问题并全部修复，然后支持微服务 30 仓库架构的接入
- 做了什么：
  - **深度审计修复（16 项）**：CRLF 合并静默丢数据、shell 注入、symlink 路径穿越、git add -A 过宽、循环导入、_slugify 行为不一致 x3、升级事务标记、verify 扫描范围、插件 .tmpl 后缀、模板缺 key 警告、输出路径防护、类型标注、stats 双重 resolve、预存在冲突标记检测
  - **新建 `_shared.py`**：提取共享常量，打破 initializer↔upgrade 循环导入
  - **新增 `meta` 项目类型**：preset + 探测 + 专属模板（registry、dependency-graph、conventions、shared-plugins 骨架）
  - **新增 `harness sync` 命令**：一条命令完成跨服务上下文同步 + 共享插件分发
  - **测试 105 → 134**（29 个新测试）
  - **文档全量同步**
- 关键决策：sync 合并 sync-context + distribute-plugins 为一步；meta init 跳过无关问题；添加 pyyaml 依赖
- 改了：41 个文件（12 新建 + 29 修改）
- 完成标准：
  - [x] 16 项审计问题全部修复
  - [x] meta 项目类型可用
  - [x] harness sync --all 端到端 41 项验证全过
  - [x] 134 测试通过，make check 全绿
  - [x] 文档全部一致

## 2026-04-10 深度完善项目类型功能差异化

- 需求：9 种项目类型只有 preset 文本差异，工具行为几乎无差异化，需要深入完善
- 做了什么：
  - 为 7 种类型创建专属规则模板（backend-service、web-app、cli-tool、worker、mobile-app、monorepo、data-pipeline），每种含 5-6 个可操作的开发约束
  - assessment 新增 `_score_type_specific()` 函数，9 种类型各检测特征文件（Dockerfile、vite.config、cli.py、worker.toml、ios/android 等），检测到 +3 分/项，未检测到给出具体建议
  - 新增 22 个测试（11 个规则存在性 + 11 个 assessment 类型感知），总数 154 → 176
  - 另外修复了上次会话未提交的遗留问题：upgrade.py 行数超限（合并重复代码 -3 行）、dogfood 不同步、文档测试计数过时
- 关键决策：
  - 每种类型只需 1 个专属规则文件，不需要大量模板（参考 library-api.md 模式）
  - assessment 用加分机制（每个特征信号 +3 分），不改变基础评分框架
  - 不在 init 流程新增交互问题，避免增加用户摩擦
- 改了：assessment.py, test_assessment.py, test_project_type_rules.py, upgrade.py, docs/product.md, docs/architecture.md, docs/release.md, CHANGELOG.md, AGENTS.md, + 7 个新建 templates/<type>/.claude/rules/<type>.md.tmpl
- 完成标准：
  - [x] 9 种类型都有专属规则模板
  - [x] assessment 对 9 种类型都有类型感知评分
  - [x] 176 测试全过
  - [x] make check / make dogfood 全绿
  - [x] 文档计数和结构同步

## 2026-04-12 分层记忆加载（Issue #10，吸收自 MemPalace）

- 需求：引入分层记忆加载（L0-L3），解决 `.agent-harness/` 下 lessons/task-log 随增长挤占 AI 上下文窗口的问题
- 做了什么：
  - **方案 C：Index + 按需展开**——新增 `memory-index.md` 作为 L1 热索引，task-lifecycle 默认只读它；`lessons.md` / `task-log.md` 为 L2/L3 按需展开
  - 新建 `/recall <关键词>` 技能，支持 `--lessons` / `--history` / `--all` 参数
  - 新建 `memory.py` 模块（162 行）和 `harness memory rebuild` CLI（老项目 bootstrap + 索引重置）
  - `upgrade.py` 将 memory-index.md 列为 skip 策略
  - `/compound` 技能新增 Step 5：写新教训时原子同步 memory-index.md
  - 16 个新测试覆盖 rebuild、升级 skip、技能文档、规则措辞、CJK 标题
  - 穷举 E2E 17/17：正常/边界/错误/升级四类路径
  - ADR 0001 记录选 C 而非 B/D 的决策
  - 文档全量同步：product/architecture/runbook/AGENTS/CHANGELOG/lessons/workflow/release/CONTRIBUTING
- 关键决策：
  - 选方案 C 而非目录分层（B）或 Python 抽象层（D）：脚手架是生成器不是运行时，痛点是"约束 AI 读什么"，不是"运行时 rotate"
  - memory-index 容量 10 教训 + 5 任务（用户敲定）
  - `/recall` 放 common 模板而非 superpowers（基础能力，--no-superpowers 不应关闭）
  - 原子性约束写入 /compound 规则：lessons 新条目 + index 必须同一 commit，打破双写漂移
- 改了：
  - 新建：`memory.py`、`memory-index.md.tmpl`、`recall.md.tmpl`、`test_memory.py`、`docs/decisions/0001-layered-memory-loading.md`
  - 修改：`upgrade.py`、`cli.py`、`check_repo.py`、`compound.md.tmpl`、`task-lifecycle.md.tmpl`、`test_superpowers.py`、`test_apply_upgrade.py`、`product.md`、`architecture.md`、`runbook.md`、`AGENTS.md`、`CHANGELOG.md`、`CONTRIBUTING.md`、`workflow.md`、`release.md`、`lessons.md`
  - 规划：`docs/superpowers/specs/2026-04-12-layered-memory-spec.md`、`2026-04-12-layered-memory-plan.md`
  - 14 个原子 commit（49a1054..5db4833），每步打 tag `lfg/step-N`
- 完成标准：
  - [x] 分层结构存在，task-lifecycle 默认只读索引
  - [x] /recall 技能 + harness memory rebuild CLI 可用
  - [x] upgrade 保留用户编辑
  - [x] 9 种项目类型自动适配
  - [x] 176 → 192 测试全过
  - [x] 穷举 E2E 17/17 通过
  - [x] 文档全量同步
  - [x] ADR 0001 已落地
  - [x] 用户验证通过

## 2026-04-12 lessons.md 结构化分区（Issue #11，灵感自 MemPalace）

- 需求：给 `.agent-harness/lessons.md` 加领域分区，提升 AI 按话题检索教训的效率；灵感来自 MemPalace 的 Wing/Hall/Room 结构化过滤
- 做了什么：
  - **方案 A：单文件内分区 + `[分类]` 前缀 + 顶部索引**（从 4 个候选方案中选最轻）
  - 条目 heading 统一格式：`## YYYY-MM-DD [分类] 一句话标题`
  - `lessons.md` 顶部新增"按分类索引"段，6 类（测试/模板/流程/工具脚本/架构设计/集成API）
  - 迁移现有 10 条教训到新格式，按分类聚类（流程 4 / 工具脚本 2 / 模板 2 / 架构设计 1 / 集成API 1 / 测试 0）
  - `compound.md.tmpl`：第 4 步条目格式改新规范；可用分类表替换为 6 类并说明"可扩展"；新增第 4.5 步"维护顶部索引"，锁死 lessons+index+memory-index 三处一致性
  - `lessons.md.tmpl`：加顶部索引占位 + 条目格式说明
  - dogfood 同步 `.claude/commands/compound.md`
  - `harness memory rebuild . --force` 验证兼容：memory-index 最近教训自然带 `[分类]` 前缀
  - 新增 3 个测试 `RebuildIndexCategoryPrefixTests` 锁死 memory.py 对分类前缀的透明契约（正常/边界/不规范三类）
  - 全量同步文档计数 203→206：AGENTS / CONTRIBUTING / CHANGELOG / docs/{product,architecture,runbook,release,workflow}.md
- 关键决策：
  - **最小实现原则**：拒绝多文件拆分（方案 B）和 Python 抽象层（方案 D）——脚手架痛点是"约束 AI 读什么"，不是运行时 rotate
  - **不改 memory.py**：新格式 `## YYYY-MM-DD [分类] 标题` 对 `^##` 正则透明，新增 3 测试锁死契约防未来回归
  - **分类前缀放日期后**：保证 memory-index 按时间排序 + 索引一眼见归属
  - **不加 `/recall --category`**：grep `[测试]` 已够用，遵循最小实现
  - 评审由 code-reviewer 子代理独立做（单次），非 6 人格 multi-review——纯 markdown 改动无业务逻辑
- 改了：
  - 修改：`compound.md.tmpl`、`lessons.md.tmpl`、`.claude/commands/compound.md`、`.agent-harness/lessons.md`、`.agent-harness/memory-index.md`、`tests/test_memory.py`、`docs/product.md`、`CHANGELOG.md`、`AGENTS.md`、`CONTRIBUTING.md`、`docs/runbook.md`、`docs/release.md`、`docs/workflow.md`、`docs/architecture.md`
  - 新建：`docs/superpowers/specs/2026-04-12-lessons-partition-plan.md`
- 完成标准：
  - [x] lessons.md 10 条全部带 `[分类]` 前缀 + 顶部 6 类索引完整
  - [x] 模板（lessons.md.tmpl + compound.md.tmpl）同步更新；dogfood 同步
  - [x] `harness memory rebuild` 成功，memory-index 含分类前缀
  - [x] 203 → 206 测试全过；新增 3 个契约锁定测试
  - [x] `docs/product.md` 第 12 条 + `CHANGELOG.md` + 8 处计数同步
  - [x] `make ci` 通过；code-reviewer 评审无 P0/P1
  - [x] 用户验证通过


## 2026-04-12 — Issue #18：/squad 多 agent 常驻协作 MVP（阶段 1）

- 需求：给框架加 tmux + git worktree 的多 agent 常驻协作能力，按 capability（scout/builder/reviewer）用 `settings.local.json` 的 `permissions.deny` 运行时强制权限
- 做了什么：
  - `src/agent_harness/squad/` 新模块 5 文件（spec/capability/tmux/state/cli）
  - `harness squad create|status|attach|stop` CLI 子命令 + `--dry-run` flag
  - 渲染产物：`.agent-harness/squad/<task_id>/{manifest.json, status.jsonl, workers/}` + 每个 worker 的 `.claude/{settings.local.json, squad-context.md}` + `task-prompt.md`
  - worker 启动方式：`claude --append-system-prompt "$(cat ctx)" "$(cat task)"` 经 shlex.quote 处理路径
  - 28 个 squad 测试（spec 解析 7 + capability 渲染 7 + tmux mock 8 + integration dry-run 6）
  - `/squad` 进入 use-superpowers 决策树、superpowers-workflow 技能表、lfg 实施阶段、evolve 比较表、usage-guide
  - 全量文档同步：product/architecture/runbook/AGENTS/CHANGELOG/README/usage-guide/release/workflow/CONTRIBUTING/project.json
- 关键决策：
  - 自研 MVP（不包 claude-squad）；JSONL + fcntl（不引入 SQLite）
  - 主 session 即 coordinator（不做常驻守护进程，阶段 1）
  - 改用 `--append-system-prompt` + positional arg（`--prompt-file` 不存在，step 0 source-verify 纠偏）
  - 独立 code-reviewer 发 PASS WITH CONDITIONS；一轮修复 P0x3 + P1x1（shell 注入、flock 顺序、fcntl 软导入、部分失败清理）
  - depends_on 触发 + 自动合并划为阶段 2/3，单独 Issue 追踪
- 改了哪些文件：38 个文件 / +2027 insertions / -41 deletions
  - src/agent_harness/squad/ (6) + src/agent_harness/cli.py
  - src/agent_harness/templates/superpowers/.claude/commands/{squad,lfg,use-superpowers,evolve}.md.tmpl
  - src/agent_harness/templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl
  - tests/test_squad_{spec_parse,capability,tmux_mock,integration}.py
  - dogfood: .claude/commands/{squad,lfg,use-superpowers,evolve}.md + .claude/rules/superpowers-workflow.md
  - docs/ (6) + AGENTS.md + CHANGELOG.md + README.md + CONTRIBUTING.md + .agent-harness/project.json
  - docs/superpowers/specs/2026-04-12-squad-mvp-{spec,plan}.md
  - .agent-harness/lessons.md (+4 条) + memory-index.md
  - .gitignore (.agent-harness/squad/)
- 完成标准（10/10）：
  - [x] tmux 未安装时友好报错（测试 + 代码）
  - [x] 循环依赖被拒绝（DFS 着色法）
  - [x] scout/builder/reviewer 权限字段测试覆盖
  - [x] squad status 无活跃 squad 时友好提示
  - [x] worker worktree 完整独立（double isolation: tmux + worktree）
  - [x] 测试数 ≥ 210，实际 206 → 234（+28）
  - [x] docs/product + architecture + runbook + AGENTS + CHANGELOG 同步
  - [x] dogfood 无漂移（make check 的 drift 检测通过）
  - [x] /squad 出现在 use-superpowers 决策树 + lfg 流水线
  - [x] /dispatch-agents vs /squad 选择标准清晰（多处对比表）
- 用户验证通过


## 2026-04-13 — 代码健康审计：280 行硬规则违反修复 + 守卫自动化

- 需求："深入分析代码发现潜在问题并修复，完后更新文档到最新"（全自动 LFG，用户免询问）
- 做了什么：
  - **P0** `squad/cli.py` 303 → 220 行：`_SQUAD_CONTEXT_TEMPLATE`、worktree provision、settings/prompt 渲染、通用 `run_check` 拆到新模块 `squad/worker_files.py`（95 行）
  - **P1（根因）** `scripts/check_repo.py:check_module_sizes` 从 9 项硬编码白名单改为 `PKG.rglob("*.py")` 自动发现；豁免 `__init__.py` 和 `templates/`
  - **P1** `Makefile` check target 从 `py_compile $(PACKAGE)/*.py`（glob 漏 squad/）改为 `compileall -q $(PACKAGE)` 递归
  - **P2** `squad/tmux.py:ensure_tmux_available` 使用 `shutil.which` 返回的 `path` 调 `tmux -V`
  - 新增 `tests/test_check_repo.py`（4 测试）锁死：新模块自动入检 / squad/ 子包覆盖 / `__init__.py` + `templates/` 豁免 / 端到端 check_repo.py 通过
  - 全量文档同步 234 → 238：AGENTS / CONTRIBUTING / CHANGELOG / docs/{runbook,release,workflow,architecture}.md
  - lessons.md + memory-index.md 同步（新增 1 条工具脚本类教训）
- 关键决策：
  - **自动发现替代白名单**：根源不是"忘记把 squad 加进白名单"，而是白名单本身就是反模式——新增子包永远沉默通过。契约测试锁死防回归
  - **Makefile check 也递归化**：同类问题（glob `*.py` 只在顶层），用 `compileall` 一次解决
  - **拆分粒度**：worker_files.py 承载"worker 材料渲染"职责，cli.py 只做 CLI 调度 + subprocess cleanup，边界清晰
  - 未引入任何新依赖（遵循最小实现原则）
- 改了哪些文件：
  - 新建：`src/agent_harness/squad/worker_files.py`、`tests/test_check_repo.py`
  - 修改：`src/agent_harness/squad/cli.py`、`src/agent_harness/squad/tmux.py`、`scripts/check_repo.py`、`Makefile`
  - 文档：`AGENTS.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`docs/{architecture,runbook,release,workflow}.md`
  - 知识：`.agent-harness/lessons.md`、`memory-index.md`
- 完成标准（6/6）：
  - [x] squad/cli.py ≤ 280 行（220）
  - [x] check_repo.py 自动覆盖所有 .py（含 squad/）
  - [x] 新增 4 个契约测试锁死行为
  - [x] tmux.py 使用 shutil.which 返回路径
  - [x] make ci 通过（234 → 238）
  - [x] 文档全量同步
- 用户要求全自动修复，免询问


## 2026-04-13 — /lfg 技能覆盖完整化（单入口驱动 33 技能）

- 需求：评估 /lfg 是否能发挥框架全部能力，发现 gap 并全部修复
- 做了什么：
  - 发现 11 个覆盖盲区（`/recall` `/use-worktrees` `/careful` `/source-verify` `/todo` `/subagent-dev` `/request-review` `/receive-review` `/verify` `/finish-branch` CLI 入口分流 + references 按需）
  - 阶段 0.1 新增"运维任务分流表"：init/upgrade/doctor/export/stats/sync/memory rebuild/squad/health/retro/lint-lessons/evolve 的走 CLI/元技能，不拉进 /lfg
  - 阶段 0.2 从"全文读 lessons.md"改为"分层加载"：L0 规则 + L1 memory-index 必读；L2/L3 用 `/recall` 和 `/recall --refs`
  - 阶段 1 接入 `/use-worktrees` + `/careful`；阶段 3 接入 `/source-verify` + `/todo`；阶段 4 选型表加 `/subagent-dev`
  - 阶段 5 串 `/request-review` → `/multi-review`；阶段 6 串 `/receive-review`
  - 阶段 7 用 `/verify` 做完整验证；阶段 10 用 `/finish-branch` 做收尾；回滚前 `/careful` 拦截
  - 末尾新增"技能覆盖清单"表（按阶段列接入点，含豁免说明）
  - 新增 `tests/test_lfg_coverage.py`（5 测试）：EXPECTED_IN_LFG (26) + EXPECTED_NOT_IN_LFG (7) 契约、shipped skills 必须被分类、豁免技能不得被 `运行` 命令化、dogfood 同步检查
  - make dogfood 同步 .claude/commands/lfg.md
  - 全量文档计数 238 → 243：AGENTS / CONTRIBUTING / CHANGELOG / docs/{architecture,runbook,release,workflow}.md
  - lessons.md + memory-index.md 新增"统一入口技能必须串起全量能力"（架构设计类）
- 关键决策：
  - **契约测试而非口头约束**：新增技能时，test_every_shipped_skill_is_classified 会失败，强迫开发者做"进 lfg 还是豁免"决策。这是本次修复的根因防御
  - **豁免分两类**：(a) /lfg /use-superpowers 自递归 / 平级；(b) /health /retro /lint-lessons 完整版 /evolve /write-skill /process-notes 是元技能或周期任务，不属单任务流
  - **CLI 入口显式提示**：/lfg 用户经常被误用于"初始化新项目"，新加的分流表直接告诉用户走 harness init。降低用户记忆负担的正确方式是 /lfg 主动指路，不是假装能做一切
  - 未修改 lfg 核心阶段编号（0/1/2/2.5/3-10），只在既有阶段内追加技能调用——保向后兼容
- 改了哪些文件：
  - 新建：`tests/test_lfg_coverage.py`
  - 模板：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`（+85 行）
  - dogfood：`.claude/commands/lfg.md`（make dogfood 自动同步）
  - 文档：`CHANGELOG.md`、`AGENTS.md`、`CONTRIBUTING.md`、`docs/{architecture,runbook,release,workflow}.md`
  - 知识：`.agent-harness/lessons.md`、`memory-index.md`
- 完成标准（6/6）：
  - [x] /lfg 引用 33 个技能中应覆盖的 26 个
  - [x] CLI 入口 + 元技能豁免说明齐全
  - [x] 契约测试锁死未来新技能必须被分类
  - [x] dogfood 无漂移
  - [x] make ci 通过（238 → 243）
  - [x] 文档全量同步 + lessons 沉淀
- 用户要求全自动修复，免询问


## 2026-04-13 — Issue #12：关键文件变更审计（WAL，吸收自 MemPalace）

- 需求：给 .agent-harness/ 下 current-task.md / task-log.md / lessons.md 加 WAL 审计日志，每次写操作记录 ts/file/op/agent/summary 到 audit.jsonl
- 做了什么：
  - `src/agent_harness/audit.py` 新模块（277 行）：append_audit / read_all / tail / stats / truncate_before / init_audit，fcntl LOCK_EX + O_APPEND 并发安全
  - `src/agent_harness/audit_cli.py`（95 行）：`harness audit append/tail/stats/truncate` 四子命令
  - cli.py 瘦身：_register_squad + _register_audit 从 builder 体内挪到顶部 import，通过压缩空行+分号保持 ≤ 280 行硬规则
  - task-lifecycle 规则新增"关键文件变更审计（WAL）"段（告知 AI 写三个关键文件后 append audit）
  - upgrade.py 将 `.agent-harness/audit.jsonl` 列入 skip（保留用户日志）
  - 模板占位：`templates/common/.agent-harness/audit.jsonl.tmpl`（空文件）
  - check_repo.py REQUIRED_FILES 加入 audit.py / audit_cli.py
  - `tests/test_audit.py`（20 测试）：append/tail/stats/truncate 全路径 + UTF-8+emoji + agent 三态 + 反面校验 + 并发 10×20 无丢失 + malformed 容错 + CLI 端到端 + upgrade skip 契约
  - make dogfood 同步 .claude/rules/task-lifecycle.md
  - 全量文档计数 243 → 263：AGENTS/CONTRIBUTING/CHANGELOG/docs/{product,architecture,runbook,release,workflow}.md
- 关键决策：
  - **最小实现**（复用 2026-04-12 教训）：拒绝 WAL 事务系统；采用库函数 + CLI + 规则提示三层，不引入 hook 强制
  - **复用 fcntl 模式**：沿用 squad/state.py 的 LOCK_EX 方案；append-only 比 squad 的 truncate 更简单，不触发"先锁再 truncate"陷阱
  - **agent 身份从 env 读**：`HARNESS_AGENT` 环境变量 + `--agent` 覆盖；不做身份体系，框架是脚手架不是运行时
  - **只监控 3 个文件**：current-task / task-log / lessons，严格按 Issue 原始范围。扩大到 docs/ 或代码是 YAGNI
  - **无自动 rotation**：`truncate --before YYYY-MM-DD` 手动裁剪，审计日志周期由用户决定
  - **malformed 容错**：read_all 跳过坏行不抛异常；审计是追溯用的旁路，不能因一条脏数据失去全部历史
- 改了哪些文件：
  - 新建：src/agent_harness/audit.py、audit_cli.py、templates/common/.agent-harness/audit.jsonl.tmpl、tests/test_audit.py
  - 修改：src/agent_harness/cli.py、upgrade.py、templates/common/.claude/rules/task-lifecycle.md.tmpl、scripts/check_repo.py
  - dogfood：.claude/rules/task-lifecycle.md
  - 文档：AGENTS.md、CONTRIBUTING.md、CHANGELOG.md、docs/{product,architecture,runbook,release,workflow}.md
  - 知识：.agent-harness/memory-index.md
- 完成标准（8/8）：
  - [x] harness audit append 成功写入 JSONL
  - [x] harness audit tail 返回最近 N 条
  - [x] harness audit stats 按 file/agent 聚合
  - [x] harness audit truncate --before DATE 裁剪生效
  - [x] 并发 200 次 append 无丢失（fcntl 锁）
  - [x] upgrade 保留用户已有 audit.jsonl（skip 契约测试锁死）
  - [x] make ci 通过（243 → 263）
  - [x] 文档全量同步


## 2026-04-13 — Issue #13：Stop + PreCompact hook 自动保存进度（吸收自 MemPalace）

- 需求：加 Claude Code 的 Stop hook 和 PreCompact hook，防止会话中断丢进度 + 压缩前持久化关键决策
- 做了什么：
  - 运行 `/source-verify` 查 Claude Code hook API 文档，发现 3 个关键纠偏：
    1. Stop hook **不支持 matcher**（文档明确静默忽略）
    2. `stop_hook_active` 字段仅在 SubagentStop 文档保证，Stop 事件无保证 → 改用 `.stop-hook-skip` sentinel 文件做人工放行
    3. PreCompact **无 decision control**（文档明确），不能 block
  - `.claude/hooks/stop.sh.tmpl`：读 current-task → 若有 `- [ ]` 且无"状态：待验证" → 输出顶级 `{"decision":"block","reason":...}` JSON（reason 经 python3 json.dumps 转义，保证多行 + 中文 + 引号合法）
  - `.claude/hooks/pre-compact.sh.tmpl`：append audit.jsonl 检查点（trigger=manual|auto 从 stdin 提取）+ stderr 输出软提示
  - `settings.json.tmpl` 注册 Stop + PreCompact，严格按 source-verify 结论（Stop 不加 matcher）
  - `scripts/check_repo.py` REQUIRED_FILES 加入两个 hook 模板
  - `tests/test_hooks.py` 16 测试：4 路决策 + sentinel 放行 + JSON 多行合法 + stdin 消费 + audit 副作用 + stderr 内容 + settings 结构契约（含 Stop 不得有 matcher 的 source-verify 锚定）
  - make dogfood 同步后，当前 session 的 current-task 有未完成 checkbox 会被自己拦住 → `touch .agent-harness/.stop-hook-skip` 兜底
  - 全量文档计数 263 → 279：AGENTS/CONTRIBUTING/CHANGELOG/docs/{product,architecture,runbook,release,workflow}.md
- 关键决策：
  - **source-verify 驱动**：直接修掉 3 个凭记忆写的 API 假设，落地 lessons "CLI flag 假设在 plan 阶段必须 source-verify"
  - **人工放行用 sentinel 文件**：比依赖未文档化字段稳；脚手架 dogfood 自身时必须自备逃生舱
  - **PreCompact 只做副作用**：append audit + stderr，不 block；契合 Claude Code 设计
  - **JSON reason 转义用 python3**：bash printf 无法安全转义多行/中文/引号，嵌入 python3 一行做 json.dumps 最稳
  - **与 Issue #12 协作**：PreCompact 直接调 audit.jsonl 格式，不再新增记录源
- 改了哪些文件：
  - 新建：`templates/common/.claude/hooks/{stop,pre-compact}.sh.tmpl`、`tests/test_hooks.py`
  - 修改：`templates/common/.claude/settings.json.tmpl`、`scripts/check_repo.py`
  - dogfood：`.claude/hooks/{stop,pre-compact}.sh`、`.claude/settings.json`
  - 文档：`AGENTS.md`（无改）、`CONTRIBUTING.md`、`CHANGELOG.md`、`docs/{product,architecture,runbook,release,workflow}.md`
  - 知识：`.agent-harness/lessons.md`（+1 条架构设计）、`memory-index.md`
  - 兜底：`.agent-harness/.stop-hook-skip`（本仓库一次性，.gitignore 已含 `.agent-harness/` 子路径？需检查是否应加入 gitignore）
- 完成标准（9/9）：
  - [x] 两个 hook 脚本模板存在
  - [x] Stop 四路决策正确（无文件/待验证/全勾/未勾）
  - [x] skip sentinel 生效
  - [x] PreCompact 写 audit + stderr 提示
  - [x] settings.json 符合 Claude Code 规范（Stop 无 matcher）
  - [x] 16 测试全绿
  - [x] make ci 通过（263 → 279）
  - [x] make dogfood 同步后框架仍可用（sentinel 兜底）
  - [x] 文档全量同步 + lessons 沉淀


## 2026-04-13 — Issue #14：多 agent 日志隔离（吸收自 MemPalace）

- 需求：给 /dispatch-agents 和 /subagent-dev 场景的并行子 agent 提供独立目录，避免并发写共享 current-task 互相覆盖
- 做了什么：
  - `src/agent_harness/agent.py`（233 行）：init_agent / diary_append / status_set / status_read / list_agents / aggregate，fcntl 锁（append 用 LOCK_EX+O_APPEND，status 用 LOCK_EX+truncate，沿 2026-04-12 "先锁再 truncate" 教训）
  - `src/agent_harness/agent_cli.py`：`harness agent init/diary/status/list/aggregate` 五子命令
  - 目录：`.agent-harness/agents/<id>/{diary.md, status.md}`；id 规范 `^[a-z0-9][a-z0-9-]{0,30}$`（与 squad 统一）
  - upgrade 策略：`.agent-harness/agents/*` → skip
  - `/dispatch-agents` + `/subagent-dev` 技能模板加子 agent 日志隔离段
  - `task-lifecycle.md` 规则加"并行子 agent 的日志隔离"段
  - `tests/test_agent.py` 25 测试：init 幂等 + id 规范（大写/shell 元字符/超长）+ diary（UTF-8/自动创建）+ status（覆盖）+ list（排序/过滤非法目录）+ aggregate（全量/子集/空）+ 并发 10x20 + CLI 端到端 + upgrade skip + squad 边界
  - 附带修复：`cli.py:main` 原本丢弃 handler 返回码，测试 "init BAD!" 时暴露 → 改为 `sys.exit(rc)` 透传。cli.py 压缩到 279 行保硬规则
  - 全量文档计数 279 → 304：AGENTS/CONTRIBUTING/CHANGELOG/docs/{product,architecture,runbook,release,workflow}.md
- 关键决策：
  - **最小实现**：没做 MemPalace 的 50 agent 上限、没加 Python 包装层、没 hook 强制；库函数 + CLI + 规则提示三层
  - **复用 fcntl 模式**：与 audit.py 同源，保证并发写安全；lessons "先锁再 truncate" 教训直接套用到 status_set
  - **与 /squad 严格分离**：文档明确边界——/squad 重型（tmux + worktree + capability）走 squad/<task>/workers/；轻型 /dispatch-agents + /subagent-dev 走 agents/<id>/。契约测试 test_agents_and_squad_are_separate_subdirs 锁定
  - **aggregate 只读不合并**：主 agent 基于汇总决定哪些进 task-log，避免自动合并的边界问题
  - **暴露并修复 cli.py:main rc 丢弃**：算本次任务的顺手改进，影响 audit / agent 两个命令族的错误码语义
- 改了哪些文件：
  - 新建：`src/agent_harness/agent.py`、`agent_cli.py`、`templates/common/.agent-harness/agents/.gitkeep.tmpl`、`tests/test_agent.py`
  - 修改：`src/agent_harness/cli.py`、`upgrade.py`、`scripts/check_repo.py`、`templates/common/.claude/rules/task-lifecycle.md.tmpl`、`templates/superpowers/.claude/commands/{dispatch-agents,subagent-dev}.md.tmpl`
  - dogfood：`.claude/commands/{dispatch-agents,subagent-dev}.md`、`.claude/rules/task-lifecycle.md`
  - 文档：`AGENTS.md` (+2 行)、`CONTRIBUTING.md`、`CHANGELOG.md`、`docs/{product,architecture,runbook,release,workflow}.md`
  - 知识：`.agent-harness/memory-index.md`
- 完成标准（11/11）：全部通过 — init 幂等、diary append、status 覆盖、list 排序、aggregate 汇总、id 规范、并发 200 次无丢失、upgrade skip、技能模板引导、make ci 279→304、文档 + 边界说明
