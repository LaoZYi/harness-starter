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

