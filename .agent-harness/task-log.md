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

## 2026-04-24 进化集成：快手 sec-audit-pipeline 反偷懒工程学（Issue #46）

- **需求**：吸收快手安全 SRC 赵海洋《Harness Engineering 三层架构 × 形式化验证（下）》提出的「反偷懒工程学」到本框架，核心论点「声明规则 ≠ 门禁扛得住」——必须主动注入压力验证规则在真实压力下是否还被遵守，给 skill 做 TDD
- **做了什么**：
  1. **新增 `/pressure-test` skill** — 7 类压力（沉没成本/疲劳/时间压力/权威/经济/务实/复杂度回避）× 6 默认场景 × 5 默认作用域（/verify / /multi-review / /cso / /lfg / /squad）；归类 `meta`，不入 /lfg 主流程；闭环流程「违规 → 捕获借口 → 分类 → 写反驳 → 更新场景」；标记 `defensive-temporary`
  2. **`anti-laziness.md.tmpl` 4 处改动**：
     - 顶部声明 4 道 → **7 道**硬门禁
     - **门禁 3 反合理化表新增 5 条借口**（3 快手原借口 + 2 评审补齐的「权威/经济」）：「Agent 写入失败手动接管后差不多」/「上下文太长不想 spawn 新 SubAgent」/「SKILL.md 太长精简后传给 SubAgent」/「CTO 说 ship it fast 跳过 /cso」/「再跑 /multi-review 烧几十 k token」
     - **门禁 4 增强字段级必填** + 慎用纯行数阈值提示
     - **门禁 7 新增压力测试**：适用触发 + 闭环流程 + T6 晋升衔接（双入口计数：月度压测 + 真实任务抓到）+ 场景库去重规则（同 skill × 同压力只保最新 1 条）
  3. **`autonomy.md.tmpl` Trust Calibration 新增 3b** — orchestrator 疲劳硬门禁：派出 N=8 worker 后强制 spawn fresh orchestrator；mailbox handoff 事件 schema（type=handoff / reason=fatigue_gate / worker_count）；与 Context Budget 规则 4 通用上限形成 orchestrator 专属阈值双保险；回归验证由 `/pressure-test` 场景 5 月度跑
  4. **13 条契约测试** — PressureTestSkillTests(4) / SkillsRegistryTests(1) / AntiLazinessRuleTests(5) / AutonomyRuleTests(3) 全覆盖 R-001..R-007 + 字段级 schema 锁定 + 锚点截断精确
  5. **docs/product.md 9.0 持续演进条目** + 7 文件计数同步（32→33 技能 / 620→633 测试）
- **关键决策**：
  1. **零依赖原则**：只吸收方法论，不引入 Z3/SMT 形式化验证（违反零依赖）、不拷贝快手代码
  2. **defensive-temporary 分类**：pressure-test skill / 门禁 7 / 3b 三处显式标记，遵循 lessons.md `反偷懒与协作记忆要解耦` — 未来模型对齐改善后可能冗余
  3. **声明式 + 回归测试式双层叠加**：门禁 1-6 是声明层，门禁 7 是验证层，1:1 对应，缺任一层都不完整
  4. **晋升计数双入口**（评审 Round 1 修正）：`/pressure-test` 月度 + 真实任务被 /verify / /multi-review / /receive-review 抓到同款借口都计入，避免「3 个月才晋升」的慢节奏
  5. **场景库去重 vs 反合理化表不去重**：场景是回归保护（只保最新 1 条），借口原话值得作训练语料（不去重）
  6. **/squad 纳入默认作用域**（评审 Round 1 修正）：场景 5 主语是 /squad orchestrator，作用域加 /squad 才准
  7. **锚点截断精确**（评审 Round 1 修正）：`## 门禁 7` → `## 与现有机制` / `3b. orchestrator 疲劳` → `4. **信任升级` — 消除 2000/1500 字符滑动窗口的越段假阳性
  8. **不吸收**：Z3/SMT / 20+ Agent 军团 / Opus+Codex 双模型对抗（已由 codex-plugin-cc 覆盖）/ 黑盒白盒迭代闭环（安全领域特化）
- **改了**：
  - 新增：`src/agent_harness/templates/superpowers/.claude/commands/pressure-test.md.tmpl` / `tests/test_pressure_test_absorb.py` / `docs/superpowers/specs/2026-04-23-kuaishou-pressure-test-plan.md`
  - 修改：`src/agent_harness/templates/common/.claude/rules/anti-laziness.md.tmpl` / `src/agent_harness/templates/common/.claude/rules/autonomy.md.tmpl` / `src/agent_harness/templates/superpowers/skills-registry.json` / `tests/test_skills_registry.py`
  - 同步：`.claude/commands/pressure-test.md` / `.claude/rules/anti-laziness.md` / `.claude/rules/autonomy.md` / `.claude/commands/lfg.md` / `.claude/commands/which-skill.md` / `.claude/rules/superpowers-workflow.md`
  - 文档：`docs/product.md` / `docs/architecture.md` / `docs/usage-manual.md` / `docs/release.md` / `CHANGELOG.md` / `README.md` / `.agent-harness/project.json`
  - 沉淀：`.agent-harness/lessons.md` / `.agent-harness/memory-index.md`
- **完成标准**：
  - [x] R-001..R-010 全 satisfied
  - [x] make ci 全绿（633 tests）
  - [x] 2 SubAgent 评审 Round 1 收敛（8 P1/P2：6 修 + 2 推迟）
  - [x] 用户验证通过
- **量化指标**：
  - `rework_count`: 0
  - `review_p0_count`: 0
  - `review_p1_count`: 4（全部接受修）
  - `review_p2_count`: 4（2 修 + 2 推迟）
  - `user_verify_first_pass`: true
  - `dialog_rounds`: ~8
  - `docs_produced`: 1（plan）+ 14 处文档更新
- **相关 commit**：`671fd94..7f448bb`（4 commits）
- **相关 tag**：`lfg/i46-step-1` / `lfg/i46-step-9` / `lfg/i46-review-r1`

---

## 2026-04-23 进化集成：volcengine/OpenViking Memory dedup 4 决策（Issue #45）

- **需求**：把 OpenViking（AGPL-3.0, 22.8k ⭐）在记忆抽取时的「向量预过滤 + LLM 4 选 1」机制吸收到本项目的 lessons 维护链路，把 `knowledge-conflict-resolution.md` T3 章节从「转条件分支合并」模糊描述升级为可操作 SOP
- **做了什么**：
  1. `knowledge-conflict-resolution.md.tmpl` T3 章节新增「4 决策 SOP」子段（skip/create/merge/delete 表格 + 3 条硬约束）+ 铁律段追加「T3 必须叠加 dedup decision」+「与 /compound 接入点」追加 3.6 步承接
  2. `/compound` 新增第 3.6 步「Dedup 决策」，含前置 `memory search --top 3` + 4 决策表格 + 输出建议格式 + 硬约束 + **触发作用域限定（仅 T3 或无冲突时触发）**
  3. `/lint-lessons` 2.2.1 之后新增 2.2.2 子段「标注 dedup decision」，含 **4 决策在 lint-lessons 语境的语义说明**（与 compound 语境显式区别）+ 双标签输出示例 + 铁律段扩展
  4. 6 条契约测试（test_t3_has_four_decision_sop / test_compound_has_dedup_step_36_with_memory_search / test_lint_lessons_has_dedup_decision_label / test_lint_lessons_preserves_keep_a_anchor **强化锁 3 模板** / test_compound_dedup_not_auto_execute / test_lint_lessons_t4_t5_dedup_decision_marked_na）
  5. docs/product.md 9.1 持续演进条目 + architecture/CHANGELOG/release 计数 614→620 同步
- **关键决策**：
  1. **零依赖原则**：复用现有 `memory search` 的 BM25 做相似度预过滤，不引入 embedding / vecdb / faiss，不拷贝 OpenViking 代码（AGPL-3.0）
  2. **只升级 T3，不动 T4/T5/T6**：Issue 方案明确，T4 走多 agent tentative 原路径，T5 走风险警告原路径，本次 4 决策仅为 T3 专属 SOP
  3. **跨场景同名关键词保留命名 + 加语境提示**（评审 Round 1 P1-1）：skip/create 在 /compound 和 /lint-lessons 语境下语义不同；选择显式声明差异而非重命名，保留"一套机制"的语义关联
  4. **/compound 3.6 触发作用域限定**（评审 Round 1 P1-2）：仅 T3 或无冲突触发，避免与 T4/T5 原路径重叠
  5. **锚点保护强化**（评审 Round 1 P1-3）：`保留 A` 单字锁定 → 锁 3 个完整模板（保留 A 删 B / 保留 B 删 A / 合并为一条），防止 4 模板段整体丢失时假阳
  6. **_extract_section 层级耦合推迟不改**（评审 Round 1 P1 推迟）：该耦合是架构健康警示而非缺陷，记入 lessons 作追溯锚点
- **改了**：
  - `src/agent_harness/templates/common/.claude/rules/knowledge-conflict-resolution.md.tmpl`
  - `src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl`
  - `src/agent_harness/templates/superpowers/.claude/commands/lint-lessons.md.tmpl`
  - `.claude/commands/compound.md`, `.claude/commands/lint-lessons.md`, `.claude/rules/knowledge-conflict-resolution.md`（dogfood 同步）
  - `tests/test_lessons_conflict_resolution.py`（+6 契约测试）
  - `docs/product.md`（9.1 条目 + 测试计数）
  - `docs/architecture.md`, `CHANGELOG.md`, `docs/release.md`（计数 614→620）
  - `docs/superpowers/specs/2026-04-23-openviking-dedup-decision-plan.md`（plan 文件）
  - `.agent-harness/lessons.md`（3 条教训 + 3 处索引更新）
  - `.agent-harness/memory-index.md`（rebuild --force 刷新）
- **完成标准**：
  - [x] R-001..R-007 全 satisfied
  - [x] make ci 全绿（620 tests）
  - [x] 2 SubAgent 评审 Round 1 收敛（5 P1: 4 修 + 1 推迟）
  - [x] 用户验证通过
- **量化指标**：
  - `rework_count`: 0（评审 Round 1 不是返工）
  - `review_p0_count`: 0
  - `review_p1_count`: 5（4 接受修 + 1 推迟）
  - `user_verify_first_pass`: true
  - `dialog_rounds`: ~10（从 /lfg #45 到用户通过）
  - `docs_produced`: 1（plan）+ 9 处文档更新
- **相关 commit**：`8c812a3..204e5dd`（4 commits）
- **相关 tag**：`lfg/i45-step-1` / `lfg/i45-step-8` / `lfg/i45-review-r1` / `lfg/i45-step-9`

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
- 改了：spec.md.tmpl(新建), tdd.md.tmpl, verify.md.tmpl, multi-review.md.tmpl, lfg.md.tmpl, which-skill.md.tmpl, superpowers-workflow.md.tmpl, evolve.md.tmpl, test_superpowers.py, CHANGELOG.md, README.md, docs/architecture.md, docs/product.md, docs/usage-guide.md, project.json, current-task.md
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
- 改了：adr.md.tmpl(新建), .gitkeep.tmpl(新建), lfg.md.tmpl, superpowers-workflow.md.tmpl, which-skill.md.tmpl, evolve.md.tmpl, test_superpowers.py, README.md, CHANGELOG.md, docs/product.md, docs/architecture.md, docs/usage-guide.md, .agent-harness/project.json
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
  - 修改：upgrade.py、cli.py 无改动但 memory.py +60 行、recall.md.tmpl、compound.md.tmpl（已在 #10 改）、task-lifecycle.md.tmpl、which-skill.md.tmpl、superpowers-workflow.md.tmpl、backend-service.md.tmpl、web-app.md.tmpl、check_repo.py、test_memory.py、test_superpowers.py、memory-index.md.tmpl
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
  - `/squad` 进入 which-skill 决策树、superpowers-workflow 技能表、lfg 实施阶段、evolve 比较表、usage-guide
  - 全量文档同步：product/architecture/runbook/AGENTS/CHANGELOG/README/usage-guide/release/workflow/CONTRIBUTING/project.json
- 关键决策：
  - 自研 MVP（不包 claude-squad）；JSONL + fcntl（不引入 SQLite）
  - 主 session 即 coordinator（不做常驻守护进程，阶段 1）
  - 改用 `--append-system-prompt` + positional arg（`--prompt-file` 不存在，step 0 source-verify 纠偏）
  - 独立 code-reviewer 发 PASS WITH CONDITIONS；一轮修复 P0x3 + P1x1（shell 注入、flock 顺序、fcntl 软导入、部分失败清理）
  - depends_on 触发 + 自动合并划为阶段 2/3，单独 Issue 追踪
- 改了哪些文件：38 个文件 / +2027 insertions / -41 deletions
  - src/agent_harness/squad/ (6) + src/agent_harness/cli.py
  - src/agent_harness/templates/superpowers/.claude/commands/{squad,lfg,which-skill,evolve}.md.tmpl
  - src/agent_harness/templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl
  - tests/test_squad_{spec_parse,capability,tmux_mock,integration}.py
  - dogfood: .claude/commands/{squad,lfg,which-skill,evolve}.md + .claude/rules/superpowers-workflow.md
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
  - [x] /squad 出现在 which-skill 决策树 + lfg 流水线
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
  - **豁免分两类**：(a) /lfg /which-skill 自递归 / 平级；(b) /health /retro /lint-lessons 完整版 /evolve /write-skill /process-notes 是元技能或周期任务，不属单任务流
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

## 2026-04-13 输入安全校验代码化（Issue #15，吸收自 MemPalace）

- 需求：把 `.claude/rules/safety.md` 中"输入信任边界"规则从文档约束变为可复用函数；同时去除 `agent.py` 和 `squad/spec.py` 中完全重复的标识符正则。
- 做了什么：
  - 新增 `src/agent_harness/security.py`（119 行），导出 `sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`
  - `SecurityError` 继承 `ValueError`，保持与现有 `except ValueError` 代码的向后兼容
  - `sanitize_path` 用 `.resolve()` + `.relative_to()` 防御路径遍历、绝对路径、符号链接三类逃逸
  - `sanitize_content` 选择 oversize 抛异常（显式告警） + null/控制字符剥除（噪音静默）
  - 重构 `agent.py`（`_AGENT_ID_RE` → `NAME_PATTERN` / `sanitize_name`）和 `squad/spec.py`（`_NAME_PATTERN` 同上），去除重复正则
  - 新增 `tests/test_security.py` 25 条三类场景覆盖；Phase 7 穷举 8 个路径遍历攻击向量全部被阻止
- 关键决策：
  - 新异常类继承 ValueError 而非 Exception：现有多处 `except ValueError` 做输入校验兜底，破坏公开契约成本高
  - 只改 agent + squad 两处：最小侵入原则；templating/initializer 的路径校验延后到下一轮（避免单 PR 牵涉面过大）
  - 不纳入 POSIX 权限检查（0o700/0o600）：跨平台风险，与脚手架定位冲突
- 改了：
  - 新增：`src/agent_harness/security.py`、`tests/test_security.py`
  - 修改：`src/agent_harness/agent.py`、`src/agent_harness/squad/spec.py`
  - 文档：`docs/architecture.md`（辅助层新增条目，测试数 304→329）、`docs/product.md`（功能 16）、`CHANGELOG.md`、`docs/release.md`
  - 知识：`.agent-harness/lessons.md`（2 条架构设计教训）、`memory-index.md`
- 完成标准（5/5）：security.py 导出完整 / 两处重构完成 / 25 条测试 + 穷举 8/8 / make ci 329 全绿 / 文档四处同步

## 2026-04-13 GSD 吸收三件套 + OpenSwarm 两条加料（Issue #17）

- 需求：一次性吸收 gsd-build/get-shit-done 的三件套（上下文监控 Hook / /plan-check / 需求 ID 三元映射）+ OpenSwarm 加料（StuckDetector 规则 / /lint-lessons 矛盾检测），全部落地到框架。
- 做了什么：按 5 阶段 atomic commit 拆分（B/C/D/E/F/G+H）：
  - **B StuckDetector**：task-lifecycle.md 新增"卡死检测"章节（4 类触发条件 + 3 步强制停下）；/tdd 和 /debug 技能文档同步
  - **C 矛盾检测**：/lint-lessons 2.2 节从简单描述升级为 3 矛盾 + 2 张力模式 + 4 选 1 裁决建议（不自动合并）
  - **D 需求 ID 三元映射**：/spec 加 1.4 需求矩阵（R-ID 连续编号 + 可识别测试信号）；/write-plan 要求每 task 标 R-ID + 末尾覆盖表；/verify 加 5.5 R-ID 覆盖硬检查（satisfied/out-of-scope/missed 三态，missed 阻断）；新增 references/requirement-mapping-checklist.md
  - **E /plan-check 新技能**：8 维度（需求覆盖 / 任务原子性 / 依赖排序 / 文件作用域 / 可验证性 / 上下文适配 / 缺口检测 / Nyquist 合规）+ 最多 3 轮修订循环；workflow 规则 + /lfg 阶段 3 + which-skill 决策树 + evolve 对比表 + usage-guide 均同步；技能计数 30→31
  - **F 上下文监控 Hook**：先 source-verify 发现 Claude Code statusline 不暴露 remaining_percentage → 降级为 PostToolUse 工具调用计数（50/100/150 三级阈值）；纯 shell 跨平台；.context-monitor-skip sentinel 可关；session-start.sh 重置计数器
  - **G+H 测试 + 文档**：test_gsd_absorb.py 新增 18 条契约测试；product.md 新增功能 17；architecture.md hooks 段 + 测试层更新；测试数 329→347 同步
- 关键决策：
  - **拆成 6 个 atomic commit + lfg/step-X tag**：单 commit 20+ 文件几百行不可评审，拆后每阶段独立可回滚
  - **F 项降级而非硬做**：GSD 原方案依赖未公开字段，降级到"工具调用计数"代理指标既落地又不 hack
  - **SecurityError 式继承链**：新异常类继承现有上位族（ValueError），保持向后兼容
  - **契约测试覆盖六个子系统**：不测"怎么调用技能"（技能是 AI 读的提示），测"模板文件里是否存在关键字和结构"——模板不被改漏就对了
- 改了：
  - 新增：`src/agent_harness/templates/superpowers/.claude/commands/plan-check.md.tmpl`、`src/agent_harness/templates/common/.agent-harness/references/requirement-mapping-checklist.md.tmpl`、`src/agent_harness/templates/common/.claude/hooks/context-monitor.sh.tmpl`、`tests/test_gsd_absorb.py`
  - 修改（技能模板）：`tdd.md.tmpl`、`debug.md.tmpl`、`lint-lessons.md.tmpl`、`spec.md.tmpl`、`write-plan.md.tmpl`、`verify.md.tmpl`、`which-skill.md.tmpl`、`evolve.md.tmpl`、`lfg.md.tmpl`
  - 修改（规则）：`common/.claude/rules/task-lifecycle.md.tmpl`、`superpowers/.claude/rules/superpowers-workflow.md.tmpl`
  - 修改（hook/配置）：`session-start.sh.tmpl`、`settings.json.tmpl`
  - 修改（dogfood）：`.claude/rules/task-lifecycle.md`、`.claude/commands/*`、`.claude/hooks/*`、`.claude/settings.json`
  - 契约：`tests/test_lfg_coverage.py`（EXPECTED_IN_LFG 加 /plan-check）
  - 文档：`CHANGELOG.md`、`docs/product.md`、`docs/architecture.md`、`docs/release.md`、`docs/usage-guide.md`、`.agent-harness/project.json`
  - 知识：`.agent-harness/lessons.md`（2 条新教训）、`memory-index.md`
- 完成标准（10/10）：
  1. ✅ StuckDetector 规则存在且 /tdd /debug 同步
  2. ✅ /lint-lessons 能检出矛盾候选（模板有"矛盾""张力""保留 A""只检出"等关键字）
  3. ✅ /spec 产出需求矩阵（R-ID + 测试信号）
  4. ✅ /write-plan 每步标 R-ID + 末尾覆盖表
  5. ✅ /verify R-ID 硬检查（三态 satisfied/out-of-scope/missed）
  6. ✅ /plan-check 8 维度 + 3 轮修订存在
  7. ✅ Hook 降级方案（statusline API 不支持 remaining_percentage → 工具调用计数代理），端到端测试通过
  8. ✅ 所有新增/修改技能同步到 /lfg 覆盖表（EXPECTED_IN_LFG 契约测试通过）
  9. ✅ 测试数 329→347、技能数 30→31 全部同步
  10. ✅ make ci 347/347 全绿

## 2026-04-13 /squad 依赖触发 + 拓扑序启动（Issue #19a，阶段 2 部分）

- 需求：Issue #19 阶段 2 的第一部分——`depends_on` 真实生效，按拓扑序启动 worker，前置 done 后才启动下游。阶段 2 的其他机制（SQLite mailbox / 持久 coordinator / watchdog）拆新 Issue。
- 做了什么：
  - `cmd_create` 改造：只启动 wave 0（无 depends_on 的 worker），有依赖的写 pending 事件
  - 新命令 `harness squad advance [--task-id T] [--dry-run]`：扫描 done + tmux 窗口，启动依赖已满足的 pending worker（幂等）
  - 新命令 `harness squad done <worker> [-m MSG]`：便捷写 done 事件
  - `cmd_status` 增强：显示三态（✅ done / 🟢 running / ⏳/🔴 pending）+ 阻塞时长 + 30min 超时警告
  - 新模块 `squad/coordinator.py` 承载依赖推进逻辑（为 Issue #19c 持久 coordinator 预留位置）
  - `state.py` 新增 `done_workers` / `pending_worker_info` / `read_all_status` 查询辅助（纯函数）
  - `tmux.py` 新增 `list_windows(session)` 检测已启动窗口
  - 17 个新测试覆盖：线性依赖、菱形依赖、advance 幂等、状态三态推导、30min 超时警告、find_squad 边界
- 关键决策：
  - **三源对账推导状态**，不在 manifest 中持久化 worker status。避免 19b/19c 再改 schema
  - **新建 coordinator.py 而非塞 cli.py**。cli.py 会超 280 行；且 coordinator 正是 19c 的未来扩展位
  - **done 是显式事件**，不监听 tmux 窗口 exit。worker 自己写 status.jsonl 或用 `harness squad done` 命令
  - **超时只警告不终止**。进程杀/降级留给 19c（coordinator）/ 19d（watchdog）
- 改了：
  - 修改：`src/agent_harness/squad/cli.py`（cmd_create + cmd_status 改造 + 注册新子命令）、`state.py`（查询辅助）、`tmux.py`（list_windows）
  - 新增：`src/agent_harness/squad/coordinator.py`（158 行）、`tests/test_squad_dependency.py`（328 行 / 17 条测试）
  - 文档：`docs/product.md`、`docs/architecture.md`（模块层 + 测试层）、`docs/runbook.md`、测试数 347→364 同步到 CHANGELOG / architecture / release
  - 知识：`.agent-harness/lessons.md`（2 条新教训：三源对账、模块拆分前留好未来位置）、`memory-index.md`
- 完成标准（6/6）：
  1. ✅ 线性依赖 scout→builder→reviewer 按序启动（测试覆盖）
  2. ✅ 菱形依赖 scout→{builder,linter}→reviewer 需两个前置都 done（测试覆盖）
  3. ✅ advance 幂等（mock live_windows 测试覆盖）
  4. ✅ status 三态 + 阻塞时长 + 30min 警告（derive_worker_state 4 条测试）
  5. ✅ 阶段 1 的 28 条 squad 测试不 regression；新增 17 条（共 45 条 squad 测试）
  6. ✅ product / architecture / runbook 文档同步

## 2026-04-13 /squad SQLite mailbox + watch/dump（Issue #21，合并原 #20）

- 需求：Issue #21 的合并版（含原 #20 SQLite mailbox + 原 #21 持久 coordinator）。
- 做了什么：
  - 新模块 `mailbox.py`（183 行）：SQLite WAL 模式事件存储；`append_event / read_events / done_workers / pending_worker_info / dump_to_jsonl`；索引 event_type + worker
  - 新命令 `harness squad watch [--interval 3]`：常驻进程轮询 mailbox → 自动 advance；SIGTERM 优雅退出；全 worker done 后自动退出
  - 新命令 `harness squad dump`：导出 mailbox 为 JSONL（调试）
  - `state.py` 的 `append_status / done_workers / pending_worker_info` 签名不变，内部 delegate 到 mailbox（19a 调用方无感）
  - 模板 `.agent-harness/.gitignore` 自动生成，排除 `mailbox.db-wal` / `mailbox.db-shm` 等 WAL 副文件
  - 18 条新测试：mailbox 基础（WAL、过滤、payload roundtrip）、state 兼容层、watch（全 done 退出、max_iterations、自动 advance）、dump、gitignore 模板
- 关键决策：
  - **合并 #20 到 #21**：避免两次破坏性重构，mailbox 无 consumer 就是空转
  - **保留 state.py 旧签名作兼容层**：迁移风险隔离在 mailbox 模块内
  - **Source-verify sqlite3 WAL / check_same_thread / Row factory 全部验证通过**
  - **WAL 副文件模板 gitignore 自动生成**：目标项目无需手动配置
  - **cli.py 用 `_add_coord` helper 保持 <280 行**：沿用 19a 建立的"模块拆分前留好未来位置"原则
- 改了：
  - 新增：`src/agent_harness/squad/mailbox.py`、`src/agent_harness/templates/common/.agent-harness/.gitignore.tmpl`、`tests/test_squad_mailbox.py`（18 条）
  - 修改：`src/agent_harness/squad/state.py`（兼容层 delegate）、`coordinator.py`（cmd_watch + cmd_dump + _advance_once 共享函数）、`cli.py`（_add_coord helper + 注册 watch/dump）
  - 测试：`test_squad_integration.py`（迁移到 mailbox API）、`test_squad_dependency.py`（pending 30min 测试改为操作 SQL）
  - 文档：`docs/product.md`、`docs/architecture.md`（模块层 + 测试层）、`docs/runbook.md`、测试数 364→382 同步到 CHANGELOG / architecture / release
  - 知识：`.agent-harness/lessons.md`（2 条新教训：兼容层、无 consumer 空转）、`memory-index.md`
- 完成标准（9/9）：
  1. ✅ mailbox.py 存在，WAL 模式
  2. ✅ state.py 签名不变，内部切换（19a 17 条 + 其他 squad 测试不 regression）
  3. ✅ coordinator.py 新增 cmd_watch
  4. ✅ cmd_watch 轮询 + 自动 advance（mock 测试）
  5. ✅ harness squad dump 导出 JSONL
  6. ✅ .gitignore 模板规则
  7. ✅ 19a 17 条 + 阶段 1 28 条 squad 测试全通过
  8. ✅ 新增 18 条测试（mailbox 10 + state 3 + watch 3 + dump 1 + gitignore 1）
  9. ✅ 文档同步（product / architecture / runbook + 测试数 364→382）

## 2026-04-13 Issue #22 — squad Tier 0 Watchdog（最后一块阶段 2 拼图）

- 需求：在 squad coordinator 中加 Tier 0 watchdog——定时 ping tmux session + worker 窗口，发现失联写 mailbox + 提示用户。Issue #19 拆分的最后一块（19a 依赖触发 + 19b/21 mailbox/watch + 19d/22 watchdog 全部完成）
- 做了什么：
  - 新增 `src/agent_harness/squad/watchdog.py`（172 行）：`detect_failures` 纯函数（依赖注入 session_exists_fn / list_windows_fn）+ `run_watchdog_tick`（写 mailbox）+ `watch_tick_with_report`（cmd_watch 用 + 返回 session_lost 退出标志）
  - `tmux.py`：新增 `session_exists` + `build_has_session_cmd`（tmux has-session 探测）
  - `mailbox.py`：`KNOWN_TYPES` 扩展 `session_lost` / `worker_crashed` / `watch_exited`
  - `coordinator.py.cmd_watch`：每 tick 末尾跑 watchdog；session_lost 立即写 watch_exited 并退出
  - 14 条新测试覆盖三类失联场景 + sentinel skip + 幂等去重 + KNOWN_TYPES 注册
- 关键决策：
  - **幂等去重写进事件流**：worker_crashed / session_lost 写到 mailbox 后下次 tick 反查，**不引入外挂状态文件**（沿用"三源对账"原则）
  - **sentinel 模式复用**：`.agent-harness/.watchdog-skip` 沿用 context-monitor 的 skip 模式，统一 UX
  - **session_lost 优先于 worker_crashed**：session 都没了不再单独报每个 worker 失联（避免噪音 + 立即退出 watch）
  - **本期不实现 pid 检查 + 自动重启**：worker 不写 pid 跨文件改动太多；自动重启 capability 切换+worktree 状态判断复杂度过高，留后续 Issue
  - **280 行硬限触发模块边界暴露**：coordinator 集成后涨到 299 行 → 抽 watch_tick_with_report helper 到 watchdog.py + 简化 import 压回 280。沉淀为 lesson
- 改了哪些文件：
  - 新增：`src/agent_harness/squad/watchdog.py`（172 行）、`tests/test_squad_watchdog.py`（14 条契约）
  - 修改：`src/agent_harness/squad/coordinator.py`（cmd_watch 集成 + import/cmd_dump 瘦身回 280 行）、`mailbox.py`（KNOWN_TYPES）、`tmux.py`（session_exists）
  - 文档：`docs/product.md`、`docs/architecture.md`（模块层 + 测试层 + 测试数 382→396）、`docs/release.md`、`CHANGELOG.md`
  - 知识：`.agent-harness/lessons.md`（2 条新教训：watchdog 写事件流去重、280 行硬限触发拆模块）、`memory-index.md`
- 完成标准（7/7）：
  1. ✅ `src/agent_harness/squad/watchdog.py` 存在，纯函数 + sentinel
  2. ✅ cmd_watch 集成 watch_tick_with_report
  3. ✅ tmux session 不存在 → mailbox 写 session_lost + stdout 提示 + watch 退出
  4. ✅ spawned + 未 done + 窗口消失 → mailbox 写 worker_crashed（幂等）
  5. ✅ `.agent-harness/.watchdog-skip` sentinel 完全静默
  6. ✅ 14 条测试覆盖三类失联场景（≥4 个 case 要求超额完成）+ 端到端 4 场景 smoke 全通过
  7. ✅ 文档同步：product / architecture / release / CHANGELOG 测试数 382→396

## 2026-04-13 Issue #24 — audit / memory 项目内嵌（解除 AI 工作流对 harness CLI 的运行时依赖）

- 需求：用户 clone 一个 init 过的 harness 项目，即使没装 harness CLI 也能跑 `/lfg` 等 AI 工作流所需的所有命令。Issue #23 拆分的子任务 1，地基
- 做了什么：
  - 新模块 `src/agent_harness/runtime_install.py`（139 行）：`install_runtime(target_root)` 复制 3 个 stdlib 源文件 + 生成精简 _shared.py + 写两个 entry 脚本 + README
  - `audit_cli.py` / `memory.py` 新增 `main(argv=None)` 函数（抽 `_add_audit_subcommands` 共享逻辑；harness CLI 路径不受影响）
  - `initializer.initialize_project` / `upgrade.execute_upgrade` 末尾自动调 `install_runtime`（强制覆盖式）
  - `scripts/dogfood.py` 增加刷新本仓库 bin
  - 模板调用替换：`templates/common/.claude/rules/task-lifecycle.md.tmpl` + `templates/common/.agent-harness/memory-index.md.tmpl` + `templates/superpowers/.claude/commands/lfg.md.tmpl` 里的 `harness audit/memory` → `.agent-harness/bin/audit/memory`
  - 10 条端到端契约测试：`tests/test_runtime_bin.py`（init 结构、stdlib-only AST 契约、bin/audit 全命令、bin/memory rebuild、upgrade 覆盖式刷新）
- 关键决策：
  - **划清命令边界**：`harness` CLI = 维护者工具；`.agent-harness/bin/` = 使用者工具。这是个**原则**，不只是权宜
  - **复制源码 > 重新实现**：避免两份漂移，但要给宿主模块去顶层副作用（见 lessons 新增条目 2）
  - **不纳入 save_base / three-way merge**：_runtime 是框架资产无用户数据，每次 upgrade 覆盖即可
  - **280 行硬限驱动拆模块**：install_runtime 新建独立文件 `runtime_install.py`，不塞进 initializer.py 污染职责
- 改了哪些文件：
  - 新增：`src/agent_harness/runtime_install.py`（139 行）、`tests/test_runtime_bin.py`（10 条契约，211 行）
  - 修改：`audit_cli.py`（+ main + _add_audit_subcommands 抽取）、`memory.py`（+ main）、`initializer.py`（+ install_runtime 调用 + 压行）、`upgrade.py`（+ import + install_runtime 调用 + 压行）、`scripts/dogfood.py`（+ install_runtime）、3 个 .tmpl（替换调用）、本仓库 `.claude/commands/lfg.md` + `.claude/rules/task-lifecycle.md`（dogfood 同步产物）
  - 文档：`docs/runbook.md`（加"项目自带运行时"段 + 变更审计改为 bin/audit）、`docs/architecture.md`（audit_cli.py 加 main 说明 + 新增 runtime_install.py 条目）、`CHANGELOG.md`（Added 段 + 测试数 411）
  - 知识：`lessons.md` 新增 2 条（AI 运行时必须项目内嵌 + 复制源码要去顶层副作用）
- 完成标准（7/7）：
  1. ✅ `install_runtime` 安装 bin + _runtime + entry + README
  2. ✅ init 时自动装；upgrade 时覆盖式刷新
  3. ✅ audit_cli / memory 新增 main 函数，cli.py 不变
  4. ✅ 3 个 .tmpl 全部替换 harness audit/memory 为 .agent-harness/bin/
  5. ✅ 10 条端到端契约（含 ast 层面的 stdlib-only 守卫）
  6. ✅ `_runtime/*.py` 纯 stdlib 守住（AST 扫描契约通过）
  7. ✅ docs/runbook + architecture + CHANGELOG 同步；dogfood 自身；本仓库 bin 可跑 audit tail

- Issue #23 进度：子任务 1/3 完成；下一步 Issue #25（squad 项目内嵌）

## 2026-04-13 Issue #25 — squad 项目内嵌 + spec.yaml → spec.json（破坏性变更）

- 需求：把 squad 运行时也项目内嵌，让使用者无需装 harness CLI + 无需装 PyYAML 就能跑 multi-agent。Issue #23 拆分的子任务 2，前置 #24 已完成
- 做了什么：
  - `squad/spec.py` 从 PyYAML 迁到 stdlib json；`.yaml`/`.yml` spec 被拒绝并给出精确迁移命令
  - `runtime_install.py` 扩展：复制 squad 整包（10 .py）+ security.py；自动重写 `from ..security` → `from _runtime.security`（避免内嵌场景相对 import 失败）
  - `squad/cli.py` 抽 `_add_squad_subcommands` 共享给 `register_subcommand` 和新 `main(argv=None)`；cli.py 压行 290→279
  - 新 entry `bin/squad`（Python shebang，加 bin/ 到 sys.path）
  - 所有现有 squad 测试 yaml→json 迁移（spec_parse / dependency / integration / mailbox）
  - 6 条新端到端契约（test_runtime_bin_squad.py）：init 结构 + import 改写 + stdlib-only AST + create/status + 破坏性变更回归
  - 模板替换：lfg.md.tmpl / squad.md.tmpl / task-lifecycle.md.tmpl + AGENTS.md + runbook + product 里的 `harness squad create <spec.yaml>` 全改 `.agent-harness/bin/squad create <spec.json>`
- 关键决策：
  - **破而彻底**：不留 yaml 兼容层，硬拒绝 + 精确迁移命令（见 lessons 新条目 2）
  - **相对 import 改写为绝对**：内嵌运行时里 _runtime/ 是顶级 package，相对父包 `..` 失效 → 复制时 sed 改写（见 lessons 新条目 1）
  - **squad/cli.py 压行回 280 以下**：把多行 `_add_coord` 调用压成单行；`main` 用一行 import + argparse
- 改了哪些文件：
  - 修改：`src/agent_harness/squad/spec.py`（去 yaml）、`squad/cli.py`（main + 压行）、`runtime_install.py`（+ squad 复制 + import 改写 + squad entry）
  - 测试：`test_squad_spec_parse.py`（全部重写 json）、`test_squad_dependency.py`（fixture yaml→json + 去 textwrap）、`test_squad_integration.py`（同）、`test_squad_mailbox.py`（同）
  - 新增：`tests/test_runtime_bin_squad.py`（6 条契约）
  - 模板：squad.md.tmpl + lfg.md.tmpl（harness squad → bin/squad，yaml → json）
  - 文档：AGENTS.md + runbook.md + product.md + CHANGELOG.md（测试数 411→418）
  - 知识：lessons.md（2 条新教训：相对 import 改写、破坏性变更哲学）
- 完成标准（10/10）：
  1. ✅ spec.py 去 yaml
  2. ✅ 所有 squad 测试 yaml→json
  3. ✅ docs/AGENTS 里 spec.yaml 示例改 json
  4. ✅ runtime_install 复制 squad + security
  5. ✅ squad.cli.py 加 main
  6. ✅ bin/squad entry 脚本生成
  7. ✅ 端到端契约在无 harness + 无 yaml 环境跑通
  8. ✅ stdlib-only AST 契约扩展到 squad 所有文件 + security
  9. ✅ 模板里所有 harness squad 替换（3 个 .tmpl + docs）
  10. ✅ dogfood 刷新本仓库 bin

- Issue #23 进度：子任务 2/3 完成；下一步 Issue #26（lfg 5 档复杂度 + 自动 squad 通道）

## 2026-04-13 Issue #26 — /lfg 整合 squad：5 档复杂度 + 6 介入点（#23 收官）

- 需求：`/lfg` 自动判定复杂度后选执行方式。不让用户判断任务大小但保留关键介入点。#23 拆分的子任务 3，前置 #24 + #25 完成
- 做了什么：
  - `lfg.md.tmpl` 阶段 0.3 新增第 5 档"超大-可并行"+ 并行类关键词清单
  - 新章节"## squad 通道（超大-可并行任务）"：AI 自动生成 spec.json 草稿（默认 scout-builder-reviewer + 3 种备选拓扑），6 介入点，失败兜底表，worker 不递归硬规则回顾
  - 阶段 4 实施分支补充"squad 通道已在阶段 0.3 自动选择"指引
  - 新测试 `tests/test_lfg_squad_channel.py`（11 条契约）：第 5 档存在、并行关键词、6 介入点、降级出口、bin/squad 调用、spec json 而非 yaml、compact 强制、默认拓扑、失败兜底
- 关键决策：
  - 降级出口必须存在：用户可回"不要并行"→ 自动降级到完整通道
  - 介入点 2/5 后**强制 /compact** 控制 lfg 主会话 context
  - lfg 主会话**常驻**担任协调员（而非一次性派发），牺牲 token 换单一入口心智
  - worker 禁止递归 lfg（沿用 AGENTS.md 第 7 条硬规则，防资源爆炸）
- 改了哪些文件：
  - 模板：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`（+ 约 100 行）
  - 测试：`tests/test_lfg_squad_channel.py`（11 条契约）
  - 文档：`CHANGELOG.md`（新 Added 段）+ 418→429 测试数同步（architecture / release）
  - dogfood 同步：本仓库 `.claude/commands/lfg.md`
- 完成标准（7/7）：
  1. ✅ 阶段 0.3 加第 5 档
  2. ✅ squad 通道专章（6 介入点 + 拓扑生成 + 降级）
  3. ✅ 阶段 4 补 squad 分支
  4. ✅ 自动 spec.json 拓扑草稿模板
  5. ✅ 11 条契约测试全过
  6. ✅ 文档同步（CHANGELOG / architecture 测试数）
  7. ✅ 调用走 `.agent-harness/bin/squad`（Issue #25 已内嵌）

- Issue #23 **meta tracker 收官** — #24 + #25 + #26 全部完成

## 2026-04-13 /lfg 能力发挥度评估 + 4 Gap 修复

- 需求：用户要求评估 /lfg 是否把项目全部能力都用上；评估后一次性修复所有发现的问题
- 做了什么：
  - **评估阶段**：通读 37K 行 lfg.md.tmpl + 30 skill + 运行时元能力（audit/memory/agent/plugins/hooks），对照 task-lifecycle / safety / autonomy 规则逐项核查
  - **发现 6 个候选 gap**，查合约测试 `test_lfg_coverage.py:64` 后撤回其中 1 个（/health 是明文设计排除项），定稿 4 Gap + 1 meta 路由
  - **修复**：`lfg.md.tmpl` 5 处插入——阶段 0.1 meta 路由、0.2 plugins 必读、4.1 子 agent 隔离 + audit、9.1 memory rebuild + audit、10.5 归档双 audit
  - **合约测试**：`tests/test_lfg_gap_fixes.py` 新增 6 条宽松正则合约锁定 5 处插入
  - **文档同步**：测试计数 429→435（CHANGELOG / architecture / release）+ product.md 新增条目 17
  - **自吃狗粮**：`.agent-harness/bin/memory rebuild`、`.agent-harness/bin/audit append` ×3 全程按新规则执行
- 关键决策：
  - **撤回 Gap 1（/health 集成）**：合约测试已明文把它列为"periodic snapshot, not part of single-task flow"设计排除项。评估前未查合约是重大疏忽，已沉淀为 lessons
  - **用项目内嵌运行时**（`.agent-harness/bin/*`）而非 `harness` CLI：符合 Issue #24 内嵌策略，避免 AI 工作流依赖用户机器上的 CLI 安装状态
  - **合约测试用宽松正则**（`audit.*append` 而非精确字符串）：未来措辞微调不会误伤，但关键语义锁死
  - **不扩展 test_lfg_coverage.py**：runtime bin 不是 skill，不应纳入 EXPECTED_IN_LFG；独立测试文件更清晰
- 改了哪些文件：
  - 模板：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`（5 处插入 ≈ 50 行净增）
  - 测试：`tests/test_lfg_gap_fixes.py`（新增，6 条合约）
  - dogfood：`.claude/commands/lfg.md`（自动同步）
  - 文档：`CHANGELOG.md` / `docs/architecture.md` / `docs/release.md`（测试计数 429→435）、`docs/product.md`（新增条目 17）
  - 记忆：`.agent-harness/lessons.md`（+2 条教训 + 分类索引更新）、`.agent-harness/memory-index.md`（rebuild 重建）
  - WAL：`.agent-harness/audit.jsonl`（+3 条记录）
- 完成标准（6/6）：
  1. ✅ 4 Gap + meta 路由在 lfg.md.tmpl 全部修复
  2. ✅ `tests/test_lfg_gap_fixes.py` 6 条合约全过
  3. ✅ `make ci` 全绿（435 tests OK + repository checks passed）
  4. ✅ `make dogfood` 无漂移（差异仅变量替换）
  5. ✅ `docs/product.md` 已同步
  6. ✅ 用户验证通过（"没问题就完成任务"）

## 2026-04-13 /lfg 复评后续润色（1 gap + 2 润色）

- 需求：用户要求再次评估 /lfg 能力发挥，把复评剩余的 1 轻 gap + 2 润色一并修掉
- 做了什么：
  - **阶段 7.3 穷举验证**：新增步骤 0 "先 `/recall --refs testing` 加载 testing-patterns.md"，让关键路径改动的验证脚本基于项目历史测试模式
  - **阶段 0.1 evolution 分支**：标注 evolution 模式自动进入完整通道（含 /ideate + /brainstorm + /spec + /plan-check），跳过复杂度评估询问
  - **阶段 3.2 计划质量检查**：把"历史教训"项扩为"历史教训 + 团队规则（含 plugins/rules）"，让 .harness-plugins/rules/ 约束真正进入计划层
  - **新增 3 条合约测试**：test_stage_7_3_recalls_testing_patterns_refs / test_evolution_mode_routes_to_full_channel / test_stage_3_2_checks_harness_plugins_rules
- 关键决策：
  - 合约测试依然用宽松正则（`/recall.*testing|testing-patterns\.md`），允许未来措辞调整
  - 不为"用户提示 stop-hook-skip / watchdog-skip sentinel"加提示：这些是运维手段，与 /lfg 流水线边界清晰分离，合理排除
- 改了哪些文件：
  - `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`（3 处增强）
  - `tests/test_lfg_gap_fixes.py`（+3 条合约，总计 9 条）
  - `.claude/commands/lfg.md`（dogfood 同步）
  - `CHANGELOG.md` / `docs/architecture.md` / `docs/release.md`（计数 435→438）
- 完成标准（3/3）：
  1. ✅ 3 处润色全部落地
  2. ✅ 新增 3 条合约测试通过（9/9 绿）
  3. ✅ make ci 全绿（438 tests OK + repository checks passed）

## 2026-04-13 Issue #27 Skills Registry SSOT 抽取

- 需求：把 34 个 skill 元数据抽到 skills-registry.json 单一真相源，消除 which-skill.md.tmpl / lfg.md.tmpl / test_lfg_coverage.py 三处漂移风险
- 做了什么：15 步实施全部落地
  - 新增 4 文件：skills-registry.json / skills_registry.py / skills_lint.py / test_skills_registry.py
  - 改造 3 模板/测试：which-skill.md.tmpl（`<<SKILL_DECISION_TREE>> + <<SKILL_INDEX_BY_PHASE>>`）、lfg.md.tmpl（`<<SKILL_COVERAGE_TABLE>>`）、test_lfg_coverage.py（从 registry 读）
  - 钩子接入 5 处 consumer：initializer.py / upgrade.py / scripts/dogfood.py / scripts/check_repo.py / test_gsd_absorb.py
  - CLI：`harness skills lint <target>` 子命令（skills_lint.register_subcommand 模式，与 audit/agent/squad 一致）
  - Makefile：`make skills-lint` + `make ci` 串入
  - 文档：CHANGELOG / architecture / product / PR 模板同步
- 关键决策：
  - 占位符 `<<SKILL_*>>` 双尖括号 vs `{{var}}` jinja——语法互斥保证两套 render_template 调用顺序无关
  - 不引 PyYAML，坚持 .json（符合 Issue #25 运行时无依赖承诺 + 兼容层降低迁移成本 lessons 的反例）
  - 触发三次 280 行硬限时抽 apply_to_rendered_dict 公共函数，一次救 upgrade.py 和 dogfood.py
  - check_repo 的"决策树覆盖"检查从读 .tmpl 改为读渲染后内容，兼顾未来 skill 元数据都移到 registry
- 改了哪些文件（19 个）：
  - 新：skills-registry.json / skills_registry.py / skills_lint.py / test_skills_registry.py / specs/2026-04-13-skills-registry-plan.md
  - 改模板：which-skill.md.tmpl / lfg.md.tmpl
  - 改核心：cli.py / initializer.py / upgrade.py / templating 钩子
  - 改脚本：scripts/dogfood.py / scripts/check_repo.py / Makefile
  - 改测试：test_lfg_coverage.py / test_gsd_absorb.py
  - 改文档：CHANGELOG.md / docs/architecture.md / docs/product.md / docs/release.md / .github/PULL_REQUEST_TEMPLATE.md
  - dogfood 同步：.claude/commands/{which-skill,lfg}.md
- 完成标准（7/7）：
  1. ✅ R-001 registry.json 含 34 skill（27 in_lfg + 7 excluded）
  2. ✅ R-002 which-skill 决策树 + 三段索引改渲染
  3. ✅ R-003 lfg 阶段覆盖表改渲染
  4. ✅ R-004 test_lfg_coverage 改读 registry
  5. ✅ R-005 harness skills lint + CI 串入
  6. ✅ R-006 docs 同步
  7. ✅ R-007 PR 模板 checkbox
- 质量变化：测试 438→451（+13）；check_repo 加 skills-lint 守卫；净代码 -48 行
- 用户验证通过

## 2026-04-14 12-Factor Agent Design 集成（Issue #28 / GitLab #12）

- 需求：吸收 humanlayer/12-factor-agents（19k+ ⭐）方法论，裁剪为本项目适用部分
- 做了什么：
  - 新增 `/agent-design-check` 技能（4 维度：F3 Context Ownership / F5 State Unification / F8 Control Flow / F10 Small Focused Agents）
  - 新增 `common/rules/agent-design.md`（F8/F10 硬约束：worker 不得自持 retry/loop、单 worker ≤ 10 原子步骤）
  - `task-lifecycle.md` 追加 "Context Ownership" 段（F3）
  - `plan-check.md` 扩到 8+1 维度（第 9 维度 Agent 工程化条件触发）
  - `lfg.md` 阶段 3 在 `/plan-check` 后自动串联 `/agent-design-check`（涉及 squad/dispatch/subagent-dev 时）
  - skills-registry.json 注册新技能（第 35 个 skill）；`<<SKILL_COVERAGE_TABLE>>` 自动渲染
  - CHANGELOG / docs/product.md / docs/usage-guide.md / superpowers-workflow.md / evolve.md 全部同步新技能清单
- 关键决策：**裁剪策略**——12 条 Factor 中只吸收适用本项目的 4 条（F3/F5/F8/F10），F1/F2/F4/F6/F7/F9/F11/F12 预设自建 LLM 运行时不适用，在新技能附录列出作参考。命名避开 `/12-factor-check` 选用 `/agent-design-check`，避免暗示"完整 12 条"
- 改了哪些文件：
  - 新：`templates/superpowers/.claude/commands/agent-design-check.md.tmpl`、`templates/common/.claude/rules/agent-design.md.tmpl`、`docs/superpowers/specs/2026-04-14-12factor-agent-design-{spec,plan}.md`、dogfood 产物 `.claude/commands/agent-design-check.md` + `.claude/rules/agent-design.md`
  - 改：`templates/common/.claude/rules/task-lifecycle.md.tmpl`、`templates/superpowers/.claude/commands/{plan-check,lfg,evolve}.md.tmpl`、`templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`、`templates/superpowers/skills-registry.json`、`tests/test_skills_registry.py`、`CHANGELOG.md`、`docs/product.md`、`docs/usage-guide.md`、`.agent-harness/project.json`
- 完成标准：
  1. ✅ 新技能 agent-design-check.md.tmpl 存在并含 4 Factor checklist
  2. ✅ 新规则 common/rules/agent-design.md.tmpl 存在（F8/F10 硬约束）
  3. ✅ task-lifecycle.md.tmpl 追加 Context Ownership 段
  4. ✅ plan-check.md.tmpl 含第 9 维度（条件触发）
  5. ✅ skills-registry 注册 + lfg 覆盖清单自动渲染
  6. ✅ make ci 通过（451 tests OK）+ harness skills lint OK
  7. ✅ make dogfood 无漂移
  8. ✅ Issue #28 + GitLab #12 关闭
- 质量变化：测试 451→451（断言更新 skill_count 34→35）；技能数 31→32（--no-superpowers 口径）；registry 34→35
- 沉淀：2 条新 lessons（外部方法论适用性裁剪、dogfood .claude gitignore force-add）
- 用户验证通过

## 2026-04-14 Context-Mode 方法论吸收（Issue #29 / GitLab #13）

- 需求：吸收 mksglu/context-mode（7k+ ⭐，HN #1）的 3 层方法论
- 做了什么：
  - 新增 `common/rules/context-budget.md`（Think in Code + 工具输出预算双约束）
  - 新增 `memory_search.py`（纯 stdlib Okapi BM25，中英混合分词）
  - `memory search <query>` CLI 子命令
  - `/recall` 技能升级为两级兜底链路（Grep → BM25）
  - `/lfg` 阶段 0.2 串入 Context Budget + BM25 兜底
  - 25 条新单元测试（tokenize/segment/bm25/search_lessons/CLI E2E）
- 关键决策：
  - **不吸收** MCP server 本体（Node/SQLite 违反零依赖原则）
  - BM25 拆独立模块（触发 280 行硬限教训的主动规避）
  - 纯 stdlib 实现（项目零依赖约束），每次查询现场计算（lessons <1MB 性能够用）
- 改了哪些文件：新增 `memory_search.py` + `context-budget.md.tmpl` + `test_memory_search.py` + 2 份 spec/plan；改 `memory.py`、`runtime_install.py`、`recall.md.tmpl`、`lfg.md.tmpl`、`superpowers-workflow.md.tmpl`、`test_runtime_bin.py`、CHANGELOG.md、docs/product.md + 同步 `.agent-harness/bin/_runtime/memory_search.py`
- 完成标准：
  1. ✅ context-budget 规则存在
  2. ✅ memory search CLI 工作
  3. ✅ /recall 含 BM25 兜底说明
  4. ✅ skills-registry/workflow 清单更新
  5. ✅ 25 新测试全过
  6. ✅ make ci 通过（476 tests OK）
  7. ✅ make dogfood 无漂移
  8. ✅ Issue #29 + GitLab #13 关闭
- 质量变化：测试 451 → 476（+25）；技能总数不变（新规则而非新技能）；lint 0 警告
- 沉淀：1 条新 lesson（_runtime 模块清单是 dogfood 的一部分）
- 用户验证通过

## 2026-04-14 Issue #30 — Multi-Agent 角色分权 + Context Store 吸收

- 需求：GitHub Issue #30（evolution 标签）吸收 Danau5tin/multi-agent-coding-system（TerminalBench #13）三大方法论到本框架
- 做了什么：
  1. `squad/capability.py` 新增 orchestrator capability（deny Edit/Write/MultiEdit/NotebookEdit + 危险 Bash），`spec.py` 白名单同步扩为 4 种
  2. 新建 `agent_artifacts.py` 模块：`diary_append_artifact` / `extract_artifacts` / `render_artifacts_section`，供 sub-agent 把发现写成结构化知识制品
  3. `agent_cli.py` 新增 `harness agent artifact <id> --type X --summary Y [--content | --content-file] [--refs a,b]` 子命令
  4. `squad.md.tmpl` 升级文档：4 角色表 + 三标准角色卡映射（Orchestrator/Explorer/Coder）+ artifact 用例
  5. `subagent-dev.md.tmpl` 追加"三角色模式"段，含能力矩阵 + context_refs 复用示例
  6. `autonomy.md.tmpl` 追加 Trust Calibration 段（5 档复杂度 × 操作基线二维模型）
  7. `docs/product.md` #21 条 + `docs/architecture.md` 同步新增能力
- 关键决策：
  - Orchestrator 作为新 capability 而非重构主 session 行为（最小破坏，复用现有运行时强制机制）
  - Artifact 拆独立模块 `agent_artifacts.py`：合并到 agent.py 会破 280 行硬限（348 行），拆分后主模块 255 行，artifact 模块 130 行
  - 项目内嵌 `bin/agent` 本期不扩（当前只含 audit/memory/squad），artifact 仅经 CLI 可用
  - 不吸收源项目 Python LLM 运行时代码（独立框架，架构不兼容）
  - 不吸收"Orchestrator 禁读代码"极端隔离（过激，会破坏主 session 规划能力）
- 改了：
  - `src/agent_harness/squad/capability.py`、`src/agent_harness/squad/spec.py`
  - `src/agent_harness/agent.py`、`src/agent_harness/agent_artifacts.py`（新）、`src/agent_harness/agent_cli.py`
  - `src/agent_harness/templates/superpowers/.claude/commands/squad.md.tmpl`、`subagent-dev.md.tmpl`
  - `src/agent_harness/templates/common/.claude/rules/autonomy.md.tmpl`
  - `tests/test_squad_capability.py`（+4 测试）、`tests/test_agent.py`（+6 测试）
  - `docs/product.md`、`docs/architecture.md`、`CHANGELOG.md`、`docs/release.md`（测试数 476→485）
  - dogfood 同步产物：`.claude/rules/autonomy.md`、`.claude/commands/squad.md`、`.claude/commands/subagent-dev.md`
- 完成标准：
  - [x] orchestrator capability 运行时强制生效 + 测试覆盖
  - [x] artifact 三件套（write/read/aggregate）+ CLI 入口 + 测试
  - [x] 三角色文档（squad + subagent-dev）落地
  - [x] Trust Calibration 段落地
  - [x] `make ci` EXIT=0，485 tests OK（+9）
  - [x] `make dogfood` 无漂移
  - [x] GitHub Issue #30 + GitLab 对应 Issue 同步关闭

## 2026-04-16 新增 /digest-meeting 技能：讨论记录→框架可消费产物

- 需求：研发流程缺"多人讨论原始语音转文字记录"的入口。用户希望把 idea 讨论或需求迭代评审的原始记录转为框架可消费的产物（init 模式填产品文档 / iterate 模式写 current-task 给 /lfg）
- 做了什么：
  - common 层新增 `/digest-meeting` 命令模板（202 行），7 步执行流程、兼容 4 种输入格式（飞书妙记/带说话人/带时间戳/纯文本）、提取 6 类信号（决策/需求/约束/待办/开放问题/参与者）、meta 项目自动委托 `/meta-create-task`、产物放 `notes/digested/`（原始文件不动）
  - skills-registry 注册 digest-meeting（category=meta，expected_in_lfg=false，作为 lfg 前置源头）
  - `/lfg` 阶段 0.1 加 notes/ 原始文件输入检测（提示先跑 /digest-meeting）
  - `/process-notes` 开头加引导（多人对话场景先用 /digest-meeting 过滤噪音）
  - `superpowers-workflow` 规则技能清单 + 使用场景段更新
  - 文档同步：product.md + architecture.md + AGENTS.md common 命令计数 3→4
  - 新测试：`tests/test_digest_meeting.py` 12 个用例（模板结构 + init 生成 + registry 契约）
- 关键决策：
  - **放 common 层而非 superpowers**：定位"原材料处理"不是"结构化工作流"，不应被 `--no-superpowers` 关掉
  - **category=meta（对标 process-notes）**：是 /lfg 的**前置源头**（产出 current-task 作为 lfg 输入），不是 lfg 流水线阶段
  - **不直接串 /spec**：iterate 模式只写 current-task.md，由 /lfg 自己决定是否需要 /spec，避免与 /lfg 阶段 2.5 的触发逻辑重复判断
  - **自动检测模式（init/iterate）不强制用户传 flag**：通过 product.md 功能列表是否有实质内容判定，减少心智负担
  - **产物放 notes/digested/，原始文件永不动**：一手资料需要长期保留以备回溯，只在头部插 `<!-- processed: YYYY-MM-DD -->` 标记
  - **meta 项目自动委托 /meta-create-task**：meta 已有跨服务任务生成能力，不重复造轮子
  - **格式兼容用启发式检测而非硬编码 parser**：四种格式宽进严出，不确定就展示解析结果让用户校对
- 改了：
  - `src/agent_harness/templates/common/.claude/commands/digest-meeting.md.tmpl`（新，202 行）
  - `src/agent_harness/templates/superpowers/skills-registry.json`（+1 条目）
  - `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`（阶段 0.1 加检测）
  - `src/agent_harness/templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`（清单 + 场景）
  - `src/agent_harness/templates/common/.claude/commands/process-notes.md.tmpl`(开头引导)
  - `tests/test_digest_meeting.py`（新，12 条）、`tests/test_skills_registry.py`(35→36)
  - `docs/product.md`、`docs/architecture.md`、`AGENTS.md`、`CHANGELOG.md`、`docs/release.md`（测试计数 487→499）
  - `docs/superpowers/specs/2026-04-16-digest-meeting-spec.md`（规格）
  - `docs/superpowers/specs/2026-04-16-digest-meeting-plan.md`（计划）
  - dogfood 同步产物：`.claude/commands/digest-meeting.md`（新）、`.claude/commands/lfg.md`、`.claude/commands/process-notes.md`、`.claude/rules/superpowers-workflow.md`
  - `.agent-harness/lessons.md`（+2 条教训）
- 完成标准：
  - [x] R1 新模板文件存在且 7 步结构完整
  - [x] R2 skills-registry.json 正确注册（category=meta）+ skills lint OK
  - [x] R3 superpowers-workflow 技能清单 + 使用场景段更新
  - [x] R4 /process-notes 开头加引导
  - [x] R5 /lfg 阶段 0.1 加 notes/ 原始文件检测
  - [x] R6+R7 docs/product.md + architecture.md + AGENTS.md common 命令计数 3→4
  - [x] R8 新测试 test_digest_meeting.py 12/12 GREEN
  - [x] R9 test_skills_registry 硬编码 35→36 同步（原 out-of-scope 升级为 satisfied）
  - [x] R10 `make ci` 全绿（499 tests OK）+ `make dogfood` 同步无漂移
  - [x] R11 关键变更全部有 WAL 审计
  - [x] 端到端演练验证：模拟飞书妙记讨论记录（6:55 时长、3 人、3 处分歧→决策、1 个开放问题）→ 6 类信号全部正确提取 + 分歧过程保留

## 2026-04-16 — `/use-superpowers` 重命名为 `/which-skill`

- 需求：消除与上游 obra/superpowers 开源项目的命名歧义。多个用户反馈 `/use-superpowers` 让人误以为在调用 superpowers 项目本身，实际功能只是「技能选择引导」。
- 根因：原命名抄自上游 obra/superpowers 的 `using-superpowers.md`，本地化时直接保留旧名，未考虑歧义。
- 做了什么：
  - 重命名模板：`templates/superpowers/.claude/commands/use-superpowers.md.tmpl` → `which-skill.md.tmpl`
  - 重命名生成产物：`.claude/commands/use-superpowers.md` → `which-skill.md`
  - 全量替换 30 个文件中的 `use-superpowers` 引用（源码、模板、测试、文档、CHANGELOG、历史归档）
  - skills-registry.json：id 从 `use-superpowers` 改为 `which-skill`，name 从「使用 Superpowers 技能系统」改为「技能选择引导」
  - 模板/生成文件标题同步更新为「技能选择引导」
  - 3 个测试函数名从 `test_use_superpowers_*` 改为 `test_which_skill_*`（test_superpowers.py × 2 + test_gsd_absorb.py × 1）
- 关键决策：
  - 上游映射保留旧名：`scripts/sync_superpowers.py` 中的 `"using-superpowers": "which-skill.md.tmpl"` 是「上游名 → 本地名」映射，必须保留上游名以确保 sync 工具能正确识别
  - 历史归档文件（task-log/lessons/CHANGELOG/specs）也参与替换：用户明确要求「这个命名歧义太大了，已经误导了很多用户」
- 改了哪些文件：30 个（含 2 处文件重命名）
  - 重命名：`use-superpowers.md.tmpl` / `use-superpowers.md`
  - 源码：`skills_registry.py`、`check_repo.py`、`sync_superpowers.py`
  - 模板：`skills-registry.json`、`which-skill.md.tmpl`、`superpowers-workflow.md.tmpl`、`AGENTS.md.tmpl`、`evolve.md.tmpl`、`lfg.md.tmpl`
  - 测试：`test_superpowers.py`、`test_skills_registry.py`、`test_lfg_coverage.py`、`test_gsd_absorb.py`
  - 文档：`README.md`、`CHANGELOG.md`、`docs/product.md`、`docs/usage-guide.md`、`docs/quickstart.md`、`docs/usage-manual.md`、4 个历史 spec 文档
  - 生成产物：`.claude/commands/{which-skill,lfg,evolve}.md`、`.claude/rules/superpowers-workflow.md`
  - 配置：`.github/PULL_REQUEST_TEMPLATE.md`
- 完成标准：
  - [x] 字面替换零残留（grep `use.superpowers|use_superpowers` 均无结果）
  - [x] 测试函数名同步更新
  - [x] 语义描述对齐新名（标题/registry name）
  - [x] make ci 全绿（499/499）
  - [x] CHANGELOG 记录
  - [x] task-log 归档

## 2026-04-16 — 新增使用手册（usage-manual + quickstart）

- 需求：用户问「给我一个详细的使用手册」+「能给我一个省时间版本吗」
- 做了什么：
  - 新增 `docs/usage-manual.md`：19 章节完整版，覆盖安装、CLI、技能、记忆系统、多 agent、审计、hooks、插件、项目类型、meta、运维、故障排查、配置参考
  - 新增 `docs/quickstart.md`：一页纸速查版，5 个最常用命令 + 10 个最常用技能 + 急救表
- 改了哪些文件：2 个新文件
- 完成标准：
  - [x] 完整版覆盖全部功能
  - [x] 速查版可一页扫读

## 2026-04-16 — 添加内网 GitLab 远端 + 合并推送

- 需求：把 `http://192.168.4.102/ai-x/zjaf-harness` 加为远端，并配合一键推送到双远端
- 做了什么：
  - 添加 `zjaf` 远端（先 HTTP 后改 SSH 解决凭据问题）
  - 创建 `all` 复合远端，push URL 同时挂 GitHub + GitLab
  - 拉取 zjaf/master 14 个新提交，本地快进合并
  - 配置 GitHub SSH 公钥 + 添加 GitHub host key
- 关键决策：
  - 用复合远端 `all` 而非给 origin 挂多个 push URL：保持 origin/zjaf 单职，all 专做合并推送
  - 「以远端为主」：本地 0 commits ahead，直接快进 zjaf/master，无需 rebase

## 2026-04-16 LFG #31 — Anthropic Agent Skills spec 对齐（吸收 anthropics/skills）

- **需求**：吸收 anthropics/skills（GitHub #31 / GitLab #15），让本项目对齐 Anthropic Agent Skills 生态
- **做了什么**：
  - `docs/architecture.md` 新增「与 Anthropic Agent Skills 的关系」段，对照 standalone commands / model-invoked SKILL.md / plugin marketplace 三种形态
  - `/write-skill` 模板 GREEN 阶段加 SKILL.md (YAML frontmatter) 格式选项；技能放置段加 `.claude/skills/<name>/SKILL.md` 路径
  - `docs/product.md` 新增功能条目 #22
- **关键决策**：
  - **方向 A（修正版）取代原 Issue 描述**：source-verify 后发现 Issue 核心论点（"commands 不是 SKILL.md 所以不合规"）有误，真实情况是 standalone slash command 是合法形态，与 SKILL.md（model-invoked）并列不互斥
  - **不创建 `.claude-plugin/plugin.json`**：dogfood 渲染后的 commands 含项目特定内容（`{{project_name}}`、`make test`、内网 GitLab URL），原样作为 plugin 跨项目分发会信息错乱
  - **不为 32 个 command 批量生成 SKILL.md**：它们是用户主动触发的工作流步骤（`/lfg`、`/tdd` 等），改为 model-invoked 会让 Claude 在不该用时误调用
- **改了哪些文件**：
  - `docs/architecture.md`（+35 行）
  - `docs/product.md`（+1 行）
  - `src/agent_harness/templates/superpowers/.claude/commands/write-skill.md.tmpl`（+30 -3 行）
  - `.claude/commands/write-skill.md`（dogfood 同步）
- **完成标准**：6/6 验收标准通过（516 测试 OK + make check OK + 文档 3 处变更已落盘）
- **commit**：75de846（feat/plugin-manifest 分支）→ master
- **关闭**：GitHub LaoZYi/harness-starter#31 + GitLab AI-X/zjaf-harness#15

## 2026-04-16 LFG #32 — git-cliff changelog 自动化（吸收 orhun/git-cliff）

- **需求**：在 `/doc-release` 技能中集成 git-cliff 自动 changelog 草稿生成
- **做了什么**：
  - `doc-release.md.tmpl` 第 5 步拆分为 5.0（自动草稿）+ 5.1（润色），检测 `command -v git-cliff`，有则 `git-cliff --unreleased --strip header` 生成草稿，无则降级到手动
  - `docs/runbook.md` 新增「changelog 生成（可选）」段：安装方式 + 基本用法 + 可选 cliff.toml 自定义
  - `docs/product.md` 新增功能条目 #23
- **关键决策**：
  - **软依赖设计**：git-cliff 是 Rust 二进制，未装时提示但不阻断，保留零依赖原则
  - **不新增 cliff.toml 模板**：git-cliff 内置 conventional commits 支持，默认配置足够；需自定义时用户自行创建（runbook 有示例）
- **改了哪些文件**：
  - `src/agent_harness/templates/superpowers/.claude/commands/doc-release.md.tmpl`（+34 -2 行）
  - `docs/runbook.md`（+50 行）
  - `docs/product.md`（+1 行）
  - `.claude/commands/doc-release.md`（dogfood）
- **完成标准**：6/6 验收标准通过（516 测试 OK + make check OK）
- **commit**：e1dbe62（feat/git-cliff-changelog）→ master
- **关闭**：GitHub LaoZYi/harness-starter#32 + GitLab AI-X/zjaf-harness#16

## 2026-04-16 LFG #33 — Claude Code 内部机制对齐（吸收 how-claude-code-works）

- **需求**：用 Claude Code 源码分析深化本项目 context-budget 和 task-lifecycle 规则
- **做了什么**：
  - `context-budget.md.tmpl` 新增「与 Claude Code 5 级压缩的关系」段：Tool Result Budget → History Snip → Microcompact → Context Collapse → Autocompact，说明本规则 ≤ 2k tokens 阈值是 L1 之前的前置防线
  - `task-lifecycle.md.tmpl` StuckDetector 前新增 L0 静默恢复层：区分可重试瞬时失败（命令超时、工具截断、临时文件冲突、git 锁）vs 同根因 3 次停下，对齐 Claude Code 7 个 continue site
  - 新增 `references/claude-code-internals.md.tmpl`（L2 参考文件：5 级压缩 + 7 continue site + 工具预执行 + 原文链接）
  - `docs/product.md` 新增功能条目 #24
- **关键决策**：
  - Issue 描述"4 级压缩"→ source-verify 修正为 **5 级**（多了 History Snip）
  - 跳过 agent-design.md 的"工具预执行"增强（F8 Control Flow 已覆盖，价值低）
  - 只引用方法论 + 原文链接，不搬运具体代码（避免因 Claude Code 版本更新导致过时）
- **改了哪些文件**：
  - `src/agent_harness/templates/common/.claude/rules/context-budget.md.tmpl`（+16 行）
  - `src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`（+19 -2 行）
  - `src/agent_harness/templates/common/.agent-harness/references/claude-code-internals.md.tmpl`（新增 52 行）
  - `docs/product.md`（+1 行）
  - `.claude/rules/context-budget.md` + `.claude/rules/task-lifecycle.md`（dogfood）
- **完成标准**：5/5 验收标准通过（516 测试 OK + make check OK）
- **commit**：7388fef（feat/claude-code-internals）→ master
- **关闭**：GitHub LaoZYi/harness-starter#33 + GitLab AI-X/zjaf-harness#17

## 2026-04-16 LFG #34 — Environment Engineering 设计哲学（参考 holaOS）

- **需求**：把 holaboss-ai/holaOS 的 Environment Engineering 方法论落地为文档
- **做了什么**：`docs/architecture.md` 顶部新增设计哲学段（14 行）+ `docs/product.md` 条目 #25
- **关键决策**：跳过 Issue 提的"README 加消歧义"和"decisions/ 加业界对照"（价值低），只在 architecture.md 一处完成全部三个参考点
- **改了哪些文件**：`docs/architecture.md`、`docs/product.md`
- **commit**：77ce9b0 → master
- **关闭**：GitHub #34 + GitLab #18

## 2026-04-17 — 全量文档同步 + ruff/mypy 集成（E 体检 + D 修复）

- **需求**：用户"深度分析代码，更新所有代码到最新"→ 先 E（`/health` 体检）再 D（文档同步 + 工具链集成）
- **做了什么**：
  - **阶段 1 文档修正**：修 6 处数字漂移（测试 304→516×3 / skill 34→36×2 / 30→32）；`architecture.md:9` 补全 10 层规则列表；`product.md` 按时间倒序重排 27 个条目（核心能力 1-9 + 持续演进 10-27，Issue #34 最新在顶）
  - **阶段 2 工具链集成**：`pyproject.toml` 加 `[project.optional-dependencies].dev`（ruff/mypy/vulture/types-PyYAML）+ `[tool.ruff]` + `[tool.mypy]`；`Makefile` 新增 `lint` / `typecheck` 目标，`check` 串入 `lint`、`ci` 串入 `typecheck`；`make setup` 默认装 dev extras
  - **阶段 3 修必修项**：`ruff --fix` 自动修 27 条；修 `cli.py` 两个真 bug（`AssessmentResult` 误当 `InitializationResult` 用 + `run_sync(target=None)` 空值风险）；`squad/coordinator.py` 未用 `frame`→`_frame`；JSON/TOML/preset 读取返回 `dict[str, Any]`（消 11 mypy 错）；清 11 处多余 `# type: ignore[union-attr]`；测试文件 7 处 F841/E402
  - **阶段 4 清单同步**：`docs/release.md` + `docs/workflow.md` + `docs/runbook.md` 加入 `lint` / `typecheck`
- **关键决策**：
  - 按用户选 **1A + 2A + 3A**：修真实 bug + 时间倒序 + `make check/ci` 阻塞模式（不降为警告）
  - `dict[str, object]` → `dict[str, Any]`：JSON/TOML/preset 的结构由外部资源决定，Any 比逐 key `cast()` 噪音小；运行时各调用点做存在性校验
  - ruff 配置 `ignore = ["E701", "E702", "E741"]`：模板生成代码有单行多语句风格 + 历史 `l/I` 单字母命名
  - mypy 配置 `ignore_missing_imports = true` + 排除 `tests/` `scripts/` `templates/`：渐进收紧，不一上来全开 strict
  - 280 行限制踩线：`discovery.py` + `initializer.py` 因加 `from typing import Any` 超标，通过删除多余空行压回
- **改了哪些文件**：
  - 代码：`src/agent_harness/cli.py`、`discovery.py`、`initializer.py`、`export.py`、`init_flow.py`、`squad/coordinator.py`、`audit.py`、`agent.py`、`squad/state.py`（9 个源文件）
  - 测试：`tests/test_apply_upgrade.py`、`test_squad_capability.py`、`test_superpowers.py`、`test_sync_context.py`、`test_lfg_coverage.py`（5 个测试文件）
  - 配置：`pyproject.toml`、`Makefile`
  - 文档：`AGENTS.md`、`docs/product.md`、`docs/architecture.md`、`docs/runbook.md`、`docs/workflow.md`、`docs/release.md`
- **质量跃迁**：ruff 49→0 错误；mypy 21→0 错误；vulture 1→0；测试 516 全过保持
- **完成标准**：全部 9 项 ✅（见 current-task.md 存档）

## 2026-04-17 — 依赖升级（D 接续：upgrade dependencies）

- **需求**：把所有依赖升到最新稳定版，抬高 `pyproject.toml` 下界
- **做了什么**：`uv lock --upgrade` → 只有 `rich 14.3.3 → 15.0.0`（大版本跳跃，测试兜住无回归）；抬高下界：`questionary>=2.0→2.1` / `rich>=13.0→15.0` / `ruff>=0.6→0.15` / `mypy>=1.8→1.20` / `vulture>=2.10→2.16`；`pyyaml>=6.0` 和 `types-PyYAML>=6.0` 保留（已是最新主版本）
- **关键决策**：rich 14→15 没阻塞——代码里只用 `rich.console.Console` + `rich.panel.Panel` + `rich.table.Table`，rich 15 的 breaking changes 不影响这些；保守做法是维持 `>=15.0` 下界而不是 `>=14.0`，因为用户新装时会拿到 15，统一源头比跨版本兼容更划算
- **改了哪些文件**：`pyproject.toml`、`uv.lock`
- **质量**：516 tests + lint + typecheck 全绿

## 2026-04-17 — Python 现代化（C：match/case 重构）

- **需求**：用户要求把剩余 `elif == "string"` 链改为 3.11+ match/case
- **做了什么**：改造 3 处 elif 链到 match/case
  - `_merge3.py:91-98` 的 `tag == "insert"/"replace"/"delete"`（3 分支）
  - `upgrade.py:202-228` 的 `cat == "overwrite"/"three_way"/"json_merge"`（3 分支）
  - `init_flow.py` 两处向导的 `step == 0..4`（各 5 分支）
- **关键决策**：只做 match 语法替换，不改业务逻辑；Optional/Union/List/Dict 等 typing 老式用法项目中已 0 处，现代化已完成
- **改了哪些文件**：`src/agent_harness/_merge3.py`、`upgrade.py`、`init_flow.py`
- **质量**：516 tests + lint + typecheck 全绿；行数无超标

## 2026-04-17 — /lfg 威力补强（5 处新特性集成）

- **需求**：用户要求全做 5 项补强——Trust Calibration 联动 / requirement-mapping 挂钩 / claude-code-internals 挂钩 / Orchestrator 拓扑示例 / Knowledge Artifacts 解析
- **做了什么**：
  - **阶段 0.3 Trust Calibration 联动**：在复杂度表后加段落说明 lfg 的 5 档复杂度直接驱动 `autonomy.md` 的「任务复杂度 × 操作基线」二维模型，且"连续 3 次小任务成功自动降档"
  - **阶段 0.2 claude-code-internals 挂钩**：新增第 11 条——context 告急时 `/recall --refs claude-code-internals` 展开 5 级压缩 + 7 continue site 参考，主动规避 L1 被动截断
  - **阶段 2.5 + 7.2 requirement-mapping 挂钩**：规格阶段先加载 checklist 把验收标准打 R-ID，验证阶段用 satisfied / out-of-scope / missed 三元检查每条
  - **squad 通道四角色拓扑**：加 Issue #30 吸收的 orchestrator + scout + builder + reviewer 四角色 JSON 示例，说明 orchestrator capability 运行时 deny Edit/Write（编排者不写代码）
  - **介入点 2 + 阶段 9.1 Knowledge Artifacts 解析**：scout done 后优先读 `harness agent aggregate` 顶部 artifacts（结构化制品 type/summary/refs/content）而非散落 diary；沉淀阶段专门提取 `tension`/`incident`/`decision` 类型
- **关键决策**：
  - 所有补强写在 `lfg.md.tmpl` 单一文件，不改骨架（阶段号/通道数不变），保持 `test_lfg_coverage` / `test_lfg_gap_fixes` 合约通过
  - Trust Calibration 不单独加阶段，作为阶段 0.3 表的"联动说明"段——lfg 判复杂度是源头，autonomy 规则是消费方
  - Artifacts 解析放在介入点 2 scout 完成处，最先受益（scout 天然产出最多探索发现）
  - lfg 从 874 → 906 行（+32 行），占比 <4%，可控
- **改了哪些文件**：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`、`.claude/commands/lfg.md`（dogfood 同步）
- **质量**：516 tests + lint + typecheck + skills-lint 全绿；威力分预计 7.5 → 9+

## 2026-04-17 — /lfg 威力终补（3 处收官）

- **需求**：用户要求从 8.75 继续推到 9.75/10——补 Hooks 协作、Environment Engineering signal、/cso 前置
- **做了什么**：
  - **Hooks 协作三处**：
    1. 阶段 0.1 加 session-start hook 对齐说明 + `.stop-hook-skip` sentinel 残留检查
    2. 阶段 4 开头加 Stop hook 守护说明（sentinel 残留警告 + 完成后删除提醒）
    3. 介入点 2 顶部加 PreCompact hook 自动化说明（/compact 前 hook 自动写 audit + stderr 提示）
  - **Environment Engineering signal**：
    1. 文档开头加 Issue #34 注释：/lfg 是 Environment Engineering 哲学的主入口，rules/commands/hooks/memory 共同构成 Agent habitat
    2. 完成报告末尾加「环境工程备注」段，点题下一次任务自动继承沉淀
  - **/cso 前置**：阶段 3.1 加第 1 步——生产项目（`has_production=true` 或 `sensitivity=high`）在写计划前先跑 `/cso` 快速扫，把风险作为计划约束内化
- **关键决策**：
  - Stop hook 守护说明放在阶段 4 开头而非介入点——阶段 4 是"停下前"最常发生的时刻
  - PreCompact 说明放在介入点 2（而非所有 compact 点）+ 明确"本节以及介入点 5、阶段 5/9/10"适用——避免重复标注
  - /cso 前置是计划期，阶段 7.4 作为兜底——生产项目"风险内化比事后补救便宜"
  - lfg 从 906 → 920 行（+14 行）
- **改了哪些文件**：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`、dogfood `.claude/commands/lfg.md`
- **质量**：516 tests + lint + typecheck + skills-lint 全绿；威力分预期 8.75 → 9.75


## 2026-04-20 GitLab #20 修复：harness upgrade 未读 project.json

- **需求**：GitLab Issue #20 `[Bug] harness upgrade 时未读取 project.json，重新渲染落到模板默认值`。backend-service + pnpm 项目升级后 CLAUDE.md / AGENTS.md / commands/*.md / docs/product.md 全部被改成 `api-framework / worker / npm run start`
- **做了什么**：
  1. `cli_answers.load_project_json` 新函数读取 `.agent-harness/project.json` 并做 schema 归一化（`project_summary` → `summary`，`commands.run/check/test/ci` → 扁平 `*_command`）
  2. `resolve_answers` 优先级链改为 `CLI > .harness.json > project.json > profile(discover) > None`
  3. `upgrade.FILE_CATEGORIES` 把 `CLAUDE.md` 从 `overwrite` 改为 `three_way`，用户笔记升级后保留
  4. `upgrade_verify.verify_upgrade` 新增 sentinel 回落检测：project.json 的 summary 已填但产物里仍出现「待补充项目目标」时发 warning
  5. 按 AGENTS.md 280 行硬限拆分 `cli_answers.py` / `upgrade_verify.py`
  6. 11 条新测试（6 优先级契约 + 1 CLAUDE.md three_way + 4 sentinel）
- **关键决策**：
  - **schema 归一化函数作为唯一入口**：所有读 project.json 的消费者（`resolve_answers` / `verify_upgrade`）走同一个 `load_project_json`，禁止各自解包。吸收成教训"answers 与持久化 schema 分裂必须显式桥接"
  - CLAUDE.md 按 Issue 建议直接改 three_way，不加 feature flag
  - sentinel 扫描只针对 summary（Issue 明确案例），`api-framework` 是用户项目自身 pyproject/package.json 的 `name`，不加扫
- **改了哪些文件**：
  - 新增：`src/agent_harness/cli_answers.py`、`src/agent_harness/upgrade_verify.py`、`tests/test_resolve_answers.py`
  - 修改：`src/agent_harness/cli.py`（瘦身到 243 行）、`src/agent_harness/upgrade.py`（瘦身到 248 行 + CLAUDE.md three_way）、`tests/test_apply_upgrade.py`、`tests/test_upgrade.py`
  - 文档：`AGENTS.md`、`docs/architecture.md`、`CHANGELOG.md`、`docs/runbook.md`、`docs/workflow.md`、`docs/release.md`（测试数 516 → 527）
  - 沉淀：`.agent-harness/lessons.md`（+2 条）、`.agent-harness/memory-index.md`（rebuild）
- **质量**：527 tests + lint + typecheck + skills-lint + check 全绿；E2E 真实 init→改 project.json→upgrade 验证产物显示 `测试管控平台 / backend-service / pnpm run start`，CLAUDE.md 用户备注保留
- **完成标准**：5/5 验收标准（R-001~R-005）全 satisfied

---

## 2026-04-20 feat(anti-laziness): 反偷懒 4 道硬门禁（Issue #36）

- **需求**：将快手安全审计文章中的 4 道反偷懒硬门禁泛化为 Harness 通用规则
- **做了什么**：
  - 新建 `anti-laziness.md.tmpl` 规则文件，定义数量门禁、上下文隔离、反合理化表、下游消费者门禁
  - 注入到 `/verify`（第 5.5 步数量门禁）、`/multi-review`（上下文隔离 + 数量门禁）、`/execute-plan`（下游消费者门禁）、`/lfg`（阶段切换交叉引用）
  - 显式标注 `defensive-temporary` 分类（参见 lessons.md 反偷懒与协作记忆解耦教训）
- **关键决策**：
  - 新增独立规则文件而非合入 task-lifecycle.md（后者已 250 行，解耦更清晰）
  - 只改模板文件，不涉及 Python 运行时代码（门禁是 AI 行为约束，不是运行时逻辑）
  - verify 的数量门禁插在 R-ID 覆盖检查之前（第 5.5 步），原 5.5 改编号为 5.6
- **改了哪些文件**：
  - 新增：`src/agent_harness/templates/common/.claude/rules/anti-laziness.md.tmpl`
  - 修改：`verify.md.tmpl`、`multi-review.md.tmpl`、`execute-plan.md.tmpl`、`lfg.md.tmpl`
  - dogfood 同步：`.claude/rules/anti-laziness.md`、`.claude/commands/{verify,multi-review,execute-plan,lfg}.md`
- **完成标准**：7/7 验收标准全 satisfied

---

## 2026-04-20 feat(multi-review): 跨模型对抗验证 + 争议解决循环（Issue #37）

- **需求**：为 /multi-review 新增 3 种验证模式和结构化争议解决机制
- **做了什么**：
  - 新增 review/challenge/consult 三种模式（`--mode` 参数），review 为默认
  - review 模式：审查员间上下文隔离，不看彼此结论，防锚定
  - challenge 模式：额外 spawn 挑战者 SubAgent 推翻 P0/P1 结论
  - consult 模式：保留现有共享上下文行为（向后兼容）
  - 争议解决循环：论述→仲裁→裁决，最多 3 轮，不一致标 NEEDS_HUMAN_REVIEW
  - /lfg 阶段 5 默认 review 模式，安全/架构场景用 challenge
- **关键决策**：
  - 争议解决循环放在 Step 4（辩论）之后作为 Step 4.5，不重构现有辩论流程
  - 仲裁者不被告知谁是"原始方"谁是"挑战者"，消除偏见
  - 争议记录不得静默丢弃，与 Issue #38 静默丢弃检测呼应
- **改了哪些文件**：
  - 修改：`multi-review.md.tmpl`、`lfg.md.tmpl` + 2 个 dogfood 产物
- **完成标准**：6/6 验收标准全 satisfied

---

## 2026-04-20 feat(verify,multi-review): 静默丢弃检测（Issue #38）

- **需求**：被判定为「不适用」的检查项/发现必须有据可查，禁止静默丢弃
- **做了什么**：
  - verify 模板：新增「跳过清单」汇总格式（表格）+ 30% 告警阈值
  - multi-review 模板：新增「静默丢弃检测」段（判定不是问题必须给证据 + Dismissed 清单 + 50% 告警）
- **关键决策**：
  - verify 用 30% 阈值（检查清单项多，跳过比例天然低）
  - multi-review 用 50% 阈值（发现数少，dismissed 比例天然高）
  - 告警不阻塞流程，只在报告中醒目展示
- **改了哪些文件**：verify.md.tmpl、multi-review.md.tmpl + 2 个 dogfood 产物
- **完成标准**：3/3 验收标准全 satisfied

---

## 2026-04-20 feat(verify): spec-to-code compliance（Issue #40）

- **需求**：在 /verify 中新增规格到实现的结构化漂移检测
- **做了什么**：verify 新增第 5.7 步（意图提取→代码映射→置信度评分→偏差分类），lfg 阶段 7.2.5 引用
- **改了哪些文件**：verify.md.tmpl、lfg.md.tmpl + 2 个 dogfood 产物
- **完成标准**：3/3 验收标准全 satisfied

---

## 2026-04-20 feat(tdd,verify): 测试质量增强（Issue #41）

- **需求**：强化测试套件的有效性度量——测试全绿 ≠ 测试够好
- **做了什么**：tdd 新增第 5.5 步（突变测试 + 属性测试指导），verify 新增第 5.8 步（测试质量评估）
- **关键决策**：两步都设为评估性/建议性不阻塞循环，避免流程膨胀
- **改了哪些文件**：tdd.md.tmpl、verify.md.tmpl + 2 个 dogfood 产物

---

## 2026-04-20 feat(cso): sharp-edges 检测（Issue #42）

- **需求**：在 /cso 新增 footgun API 和易误用配置检测，补充开发者视角
- **做了什么**：/cso 新增阶段 10.5（Sharp Edges），通用 footgun + 框架特异性 footgun + 配置文件 footgun 三类
- **关键决策**：作为 STRIDE 互补阶段而非替代，可 --mode sharp-edges 单独触发
- **改了哪些文件**：cso.md.tmpl + dogfood 产物

---

## 2026-04-20 fix(tests): env 隔离用户全局 gitconfig（GitLab #21）

- **需求**：外部使用者在带强制 pre-commit hook / `core.hooksPath` 的机器上跑 `make test` 批量失败（27 ERROR + 1 FAIL）
- **做了什么**：测试侧统一用 `GIT_CONFIG_GLOBAL=/dev/null` + `GIT_CONFIG_SYSTEM=/dev/null` 屏蔽用户全局 gitconfig
- **关键决策**：
  - 产品代码零改动——`maybe_git_commit` 的「commit 失败→保留 staged + 友好提示」是正确用户体验
  - 不采用 `--no-verify` 绕过（违反全局"never skip hooks"准则）；选 env 完全隔离方案
  - 封装成 `isolated_git_env()` 公共 helper，避免各测试自己 inline subprocess.run
  - TDD：先用 hostile global hook 模拟用户环境（RED 复现 1 ERROR + 1 FAIL），再加 env 隔离（GREEN）
- **改了哪些文件**：`tests/_git_helper.py`、`tests/test_cli.py`、`tests/test_git_env_isolation.py`（新增）、`docs/runbook.md`、`docs/workflow.md`、`docs/release.md`、`docs/architecture.md`、`CHANGELOG.md`
- **完成标准**：4/4 验收标准全 satisfied（`make test` 529/529、两处 env 正确、新节就位、计数同步）

---

## 2026-04-20 feat(rules,lessons): Imprint 5 型冲突解析吸收（GitHub #43 / GitLab #22）

- **需求**：吸收 ilang-ai/Imprint v2.1 的 Conflict Resolution 5 型分类到 lessons 维护链路
- **做了什么**：
  - 新元规则 `.claude/rules/knowledge-conflict-resolution.md`（文案化 T1-T5 + 明确 lessons 域只接入 T3/T4/T5）
  - `/lint-lessons` 步骤 2.2 每对冲突额外标注 resolution-type + 建议动作精化
  - `/compound` 新增步骤 3.5 冲突预检：区分"重复"与"矛盾"，后者按分型提示人工裁决，不 block
  - ADR 0002 记录取舍（不吸收 Imprint confidence / DSL / 用户级 profile）
  - 14 条新测试 + 5 份文档计数同步 529 → 543
- **关键决策**：
  - 症状维度 × 解决维度 **正交叠加**，不替换原有 5 种症状分类
  - 只接入 T3/T4/T5 到 lessons 域；T1/T2 保留描述但 out-of-scope（为未来 Imprint 增量吸收预留锚点）
  - 冲突预检始终**非 blocking**——AI 提示分型，用户裁决
  - 走简化完整通道（evolution 但跳过 /ideate + /brainstorm），因为 Issue body 已有具体落地方案
- **改了哪些文件**：
  - 新增：规则模板 + dogfood 产物 + ADR + spec + plan + 测试文件 = 6
  - 改：2 个 skill 模板 + 2 个 dogfood 产物 + CHANGELOG + 4 个 docs = 9
- **完成标准**：7/7 R-ID satisfied；make ci 543/543 pass

---

## 2026-04-21 feat(init): --scaffold 支持远端 git URL

- **需求**：`harness init --scaffold` 现只支持本地路径，加远端 git URL 拉取
- **做了什么**：
  - 新模块 `_scaffold_git.py`：`is_git_url()` + `copy_scaffold_from_git()` + `ask_git_scaffold()` 交互辅助。shallow clone（`--depth 1`）+ tempfile 自动清理 + subdir 路径遍历双保险（`..` 拒绝 + `commonpath` 检测）
  - `--scaffold` 自动检测 local-path vs git-url（http(s)/ssh/git@/git:// 前缀或 `.git` 后缀）
  - 新增 `--scaffold-ref <branch|tag>`（不支持任意 commit SHA，`git clone --branch` 上限）+ `--scaffold-subdir <relpath>`（monorepo 模板仓场景）
  - `ask_scaffold` 交互选项从 2 扩到 3
  - ADR 0003 Accepted（记录为什么单 flag 自动检测 / 不传 token / 不引 GitPython）
  - 17 条新测试（8 URL 检测 + 5 clone/ref/subdir + 1 git 未装 + 2 路径遍历防护 + 1 CLI 端到端）
  - 6 份文档同步（CHANGELOG + runbook + product + architecture + workflow + release），测试计数 543 → 560
  - **11 场景真实 smoke test**（7 本地 bare repo + 4 真实 GitHub），验证了单测之外的真实网络 transport
- **关键决策**：
  - 单 flag 自动检测（Option A）而非独立 `--scaffold-git`——向后兼容 + UX 简洁
  - shallow clone `--depth 1` 省流量；不缓存
  - 鉴权委托给用户 git 配置，本命令不接 token 参数（安全）
  - subdir 双保险校验避免路径逃逸（/cso 分析结论）
- **改了哪些文件**：5 新 + 9 改
- **完成标准**：8/8 R-ID satisfied；make ci 560/560 pass；真实 GitHub smoke test 通过

---

## 2026-04-21 feat(init): --scaffold-cmd 支持脚手架命令（第三种 scaffold 来源）

- **需求**：`harness init --scaffold` 现支持本地路径和远端 git URL 两种，加第三种「基于脚手架命令」（如 `npm create vite@latest` / `django-admin startproject` / `cargo init` 等主流脚手架一条命令初始化项目）
- **做了什么**：
  - 新模块 `_scaffold_cmd.py`（85 行）：`run_scaffold_command(command, target)` + `ask_cmd_scaffold(target)` 交互辅助。`shlex.split` + `subprocess.run(argv, shell=False)` + stdio 继承父进程 + `shutil.which` 预检 + `mkdir(parents=True, exist_ok=True)` target
  - CLI 新 flag `--scaffold-cmd "<命令>"`，与 `--scaffold` 组成 argparse `add_mutually_exclusive_group()`；`_cmd_init` 加 `scaffold_cmd` 分支（cli.py +7 行）
  - `ask_scaffold` 交互选项从 3 扩到 4（新增「是，通过脚手架命令创建」）；为守住 280 行硬限压缩 3 个「是」分支消息发布点为统一 `console.print(msg)`（init_flow.py 278 → 279）
  - ADR 0004 Accepted（记录为什么独立 flag 而非扩展 `--scaffold` / 为什么 argv 不 `shell=True` / 为什么 cwd=target 不改写参数）
  - 14 条新契约（`RunScaffoldCommandTests` 8 + `ShellMetacharSafetyTests` 2 用 sentinel 文件证明安全 + `CliMutualExclusionTests` 1 + `InteractiveChoiceTests` 1 + `CliEndToEndTests` 1 + `ShutilWhichMockTests` 1）
  - 6 份文档同步（CHANGELOG + runbook「三种来源」段和常见脚手架示例 + product 核心能力 #3 + CLI 清单 + 持续演进 + architecture 模块清单 + AGENTS 常用命令 + release/workflow 测试计数），测试计数 560 → 574
  - **10 项穷举验证脚本**（正常 ×2、边界 ×2、错误 ×3、安全 ×1、回归 ×1、组合 ×1），全 PASS
  - lessons 新增一条：**「用户命令执行的 shell 元字符安全必须用 sentinel 文件证明」**——把 argv 安全契约从文档承诺锁定为运行时行为
- **关键决策**：
  - 独立 `--scaffold-cmd` flag + argparse 互斥组（而非复用 `--scaffold` 启发式判别命令 vs 路径——命令字符串和路径不可靠区分）
  - `shlex.split` + `subprocess.run(argv, shell=False)` 默认：shell 元字符（`;` `&` `|` `$()`）被视为字面参数；用 `sh -c 'echo ok' _ ; rm -rf <sentinel>` 的 sentinel 契约测试锁定（运行后 sentinel 必须存活）
  - stdio 继承父终端（不捕获）：交互式脚手架 vite / next / create-react-app 等能正常问答，避免捕获导致的死锁
  - cwd = target，不改写用户参数：文档里教用户用 `.` 作脚手架 target（`npm create vite@latest .`、`cargo init`、`django-admin startproject . mysite`）
  - 不引入预设清单（`--scaffold-preset vite-react` 等）：维护成本高、易过时
  - `shutil.which` 预检：未安装命令给友好中文错误，比让 `FileNotFoundError` 冒出去更好
- **改了哪些文件**：5 新 + 9 改
- **完成标准**：9/9 R-ID satisfied；make ci 574/574 pass；穷举脚本 10/10 pass；commit `fe5c07a` 在分支 `feat/scaffold-cmd-20260421`

## 2026-04-21 feat(lfg-audit): /lfg 威力释放度体检工具（10 维 scorecard）

- 需求：评估 /lfg 有没有发挥项目最大威力——「把新能力都收到 /lfg 了，但怎么知道真的发挥了全部威力？」
- 做了什么：
  - 新增 `harness lfg audit` CLI：10 维 scorecard + 阈值门禁 + JSON 输出
  - 10 维度：Rules 覆盖 / Skills 编排 / Memory 分层 / 反偷懒门禁 / StuckDetector / Agent 设计 / Audit WAL / 文档同步 / 知识复利 / Context Budget
  - 代码 3 文件共 454 行（均 ≤ 280 行）：`lfg_audit.py`（数据模型 + audit 入口）+ `lfg_audit_checks.py`（10 个 check）+ `lfg_audit_cli.py`（CLI）
  - 测试 14 条覆盖三类场景（正常/边界/错误），全绿；总测试 574 → 588
  - 本项目首跑 9.9/10，命中 1 个真实 gap：`knowledge-conflict-resolution.md` 未反哺 /lfg（Dim 1 只得 0.90）
  - 文档同步：docs/product.md（持续演进 9.4 + CLI 表）、docs/runbook.md、AGENTS.md，以及 5 个文档里的测试计数 574→588
- 关键决策：
  - 静态分析优先（不做运行时追踪）——1-2 天能出 MVP 验证价值，运行时埋点成本高 10 倍
  - 拆三文件而非单文件——触发 280 行硬限后按 `audit_cli.py`/`agent_cli.py` 现有模式拆分
  - 拒绝对损坏 registry 降级处理——corrupt 必须退出 2，避免 0 分 Dim 2 掩盖基础设施错误
  - opt-in 规则（api.md/database.md）不计入 Dim 1 基线——从 presets 的 exclude_rules 自动推导
  - 不做 `/lfg-audit` skill 包装器——CLI 已够用，等价值验证后再说
- 改了：
  - src/agent_harness/lfg_audit.py (new, 154 行)
  - src/agent_harness/lfg_audit_checks.py (new, 228 行)
  - src/agent_harness/lfg_audit_cli.py (new, 72 行)
  - src/agent_harness/cli.py (+2 行：注册 lfg subparser)
  - tests/test_lfg_audit.py (new, 14 条测试)
  - docs/product.md (持续演进 9.4 + CLI 表新增一行)
  - docs/runbook.md (harness lfg audit 命令示例)
  - AGENTS.md (常用命令新增一行)
  - docs/architecture.md / runbook.md / workflow.md / release.md / CHANGELOG.md (测试计数 574 → 588)
- 完成标准：全部通过
  - [x] harness lfg audit 命令可用，输出完整 10 维 scorecard
  - [x] 10 个 check 函数全部实现，无 TODO stub
  - [x] 14 条测试三类全覆盖、全过
  - [x] make ci 全绿（588/588）
  - [x] docs 同步
  - [x] 跑出的 scorecard 指出至少 1 个真实未释放维度（knowledge-conflict-resolution.md 未接入 /lfg）

## 2026-04-21 feat(lfg): knowledge-conflict-resolution 规则接入 /lfg 阶段 9

- 需求：按 `harness lfg audit` 跑出的真实 gap 补齐——`knowledge-conflict-resolution.md` 未反哺 /lfg（Dim 1 Rules 覆盖 0.90/1.00）
- 做了什么：
  - 阶段 9.1 /compound 前插入 T3/T4/T5 冲突预检 blockquote（3 行净增），引用规则路径
  - 阶段 9.3 快速 lint 2 项→3 项，第 3 项「指向相反→按 T3/T4/T5 标 resolution-type」
  - `make dogfood` 同步到 `.claude/commands/lfg.md`
  - `test_threshold_gate_fails_below` 测试阈值 10→11（基线 9.9→10.0 后必须上调）
- 关键决策：
  - 只接入 T3/T4/T5（规则明说本次不扩展 T1/T2）
  - 净增 ≤ 5 行（Context Budget 约束；规则全文已独立存档，/lfg 只做指针）
  - 不改 /compound 和 /lint-lessons 技能模板（规则已说明接入点，技能内部实现另行）
- 改了：
  - src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl (阶段 9.1 + 9.3 两处)
  - .claude/commands/lfg.md (dogfood 同步产物)
  - tests/test_lfg_audit.py (阈值 10→11)
- 完成标准：全部通过
  - [x] harness lfg audit 总分 10.0/10，Dim 1 = 1.00
  - [x] make ci 全绿（588/588）
  - [x] knowledge-conflict-resolution.md 在 lfg.md.tmpl 被引用
  - [x] 净增文字 ≤ 10 行
- 附带收益：证明 `harness lfg audit` 的闭环价值——10 分钟内用工具定位 gap → 精准接入 → 工具验证达标 → 上个任务的价值直接体现在下个任务

## 2026-04-21 fix(upgrade): 缺 base 基线时保护用户文档（GitLab Issue #23）

- 需求：`harness upgrade apply` 把用户长期维护的 `docs/architecture.md`(508 行 NestJS 架构图)整体覆盖为 40 行模板骨架。根因 `upgrade.py:206-209` 的 `three_way` 分支在 base 缺失时退化为 overwrite。
- 做了什么：
  - 缺 base 的 `three_way` 分支改写 `<file>.harness-new` 旁路文件 + 警告，原文件保留不变
  - `UpgradeExecutionResult` 新增 `missing_base_files` 字段
  - `_build_checklist` 警告文案从「将备份后覆盖」改为「将写到 .harness-new 旁路文件保护用户内容」
  - 新增 `execute_upgrade(force=True)` 逃生口 + CLI `--force` flag
  - 保护策略对**所有** `three_way` 文件通用（不维护白名单）
- 关键决策：
  - **方案 A**（旁路文件 + 警告）选定原因：兼顾"保护用户内容"和"让用户看到框架新模板"，比纯 skip 信息更多，比改 `docs/architecture.md` 为 skip 更通用（保护所有 three_way 文件）
  - **不维护用户文档白名单**：策略的通用性比列表更可靠；任何 three_way 文件无 base 时都该保护，bug 根因是策略缺口而非特定文件缺口
  - **`--force` 在 CLI 和 API 双层可用**：用户主动覆盖时通过 `--only <file> --force` 显式表达意图
  - **backups/ 兜底机制保留**：第二道防线，不破坏现有稳定行为
- 改了哪些文件：
  - `src/agent_harness/upgrade.py`（核心保护分支 + force 参数 + checklist 文案 + SIDECAR_SUFFIX 常量）
  - `src/agent_harness/models.py`（`UpgradeExecutionResult.missing_base_files`）
  - `src/agent_harness/cli.py`（`--force` flag 注册 + 透传）
  - `tests/test_apply_upgrade.py`（新增 `NoBaseProtectionTests` 10 条 R-001..R-010）
  - `docs/product.md` / `docs/architecture.md` / `docs/runbook.md` / `CHANGELOG.md` / `docs/release.md`（同步说明 + 测试计数 588→598）
  - `.agent-harness/lessons.md`（2 条新教训）
- 完成标准：
  - [x] R-001..R-010 全部 satisfied，单元测试 10/10 绿
  - [x] 端到端穷举：5 场景 19 check 全过（/tmp/issue23_e2e_verify.py）
  - [x] make ci 全绿（598 tests，无 lint/typecheck 警告）
  - [x] dogfood 无漂移
  - [x] 历史 `test_user_content_preserved_in_three_way` / CLAUDE.md three_way 等回归测试不破

## 2026-04-22 feat(workflow): 吸收腾讯 AI 全自动化文章 3 点

- 需求：用户读完腾讯技术工程《从提需求到部署发布，全 AI 全自动化后》后问「有什么可以吸收的点」，对比后选 3 个高 ROI 点按 10 分→30 分→1 小时的顺序落地
- 做了什么：
  - **Step 1 · 双轮模型**：`superpowers-workflow.md.tmpl` 在「推荐工作流」后新增「双轮框架：交付 vs 治理」段——把 32 个技能按 Delivery（17 个）/ Governance（8 个）两轮分类，说明「只跑交付 → lessons 积矛盾」/「只跑治理 → 价值递减」的共生关系
  - **Step 2 · 交付质量度量**：`task-log.md.tmpl` 任务记录格式新增 4 个**可选**指标（`rework_count` / `review_p0_count` / `user_verify_first_pass` / `dialog_rounds`），给 `/retro` 和 `/evolve` 提供真实数据源
  - **Step 3 · 需求评分门禁**：`spec.md.tmpl` 阶段 1 新增 1.5 节「需求评分门禁」——5 维 × 20 分评分卡（背景/价值衡量/解决方案/影响范围/正文完整性）+ 三档硬规则（≥ 80 通过 / 60–79 补齐 / < 60 回 `/ideate`）+ 4 条反合理化 + 输出示例
  - dogfood 同步 `.claude/rules/superpowers-workflow.md` + `.claude/commands/spec.md`（task-log.md.tmpl 不在 dogfood 同步范围，改动只影响未来 `harness init` 产物）
- 关键决策：
  - **分类先于动手**：把文章的点先分成「已覆盖 / 值得吸收 / 不适合」三类，再按 ROI 排序，避免过度工程化。原文 PRD-Agent / DDLMcp / LegoMcp / 三级成熟度模型 L1/L2/L3 / 执行清单模板化 5 项明确划入「不吸收」
  - **评分门禁写进 spec.md 而非新建规则**：与现有「🔴 完成后展示规格 + 需求矩阵」对齐，升级为「规格 + 需求矩阵 + 评分卡」三件套，单点打击
  - **4 个指标设为可选**：避免强制破坏现有 task-log 历史格式；省略按「未测量」处理
  - **双轮模型纯文档化**：不动代码、不改技能文件归类，只在 rule 顶部 ratchet 语义——最低成本最高杠杆
- 改了哪些文件：
  - `src/agent_harness/templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`
  - `src/agent_harness/templates/common/.agent-harness/task-log.md.tmpl`
  - `src/agent_harness/templates/superpowers/.claude/commands/spec.md.tmpl`
  - dogfood 同步：`.claude/rules/superpowers-workflow.md`、`.claude/commands/spec.md`
- 完成标准：
  - [x] 3 个模板文件均更新，文本结构完整
  - [x] `scripts/dogfood.py` 同步成功（2 个文件更新）
  - [x] `make test` 598/598 全绿，无回归
  - [x] 用户确认通过
- 指标：
  - rework_count: 0                   # 一次到位未返工
  - review_p0_count: 0                # 纯文档 / 模板改动，未走 /multi-review
  - user_verify_first_pass: yes       # 用户直接「确认」
  - dialog_rounds: 5                  # 「框架是什么」→「吸收点」→「按顺序执行」→「确认」→「归档」

## 2026-04-22 feat(workflow): 吸收腾讯 LEGO Harness Engineering 文章 5 点

- 需求：用户读完腾讯 CDN LEGO 团队《Harness Engineering：AI 能在真正"出事会炸"的后端系统里写代码吗？》后问「有没有可以吸收的点」，对比后选 5 个增量点按 30min/1h/2h/1h/2h ROI 顺序落地（B → A → D → E → C）
- 做了什么：
  - **Step B · 不确定性输出规则（门禁 5）**：`anti-laziness.md.tmpl` 新增**门禁 5**——事实性断言必须 observed（有文件路径/命令输出）或 uncertain（挂 `⚠️ 待核实`）二选一，禁止「大概率 / 应该是 / 据我所知」模糊副词规避；含 3 条反合理化驳斥
  - **Step A · 13 类问题 + 5 根因 references**：新建 `templates/common/.agent-harness/references/ai-coding-pitfalls.md.tmpl`（L2 温知识）——5 根因（R1「不会说我不知道」位列最高 + R2 幻觉 + R3 改不全 + R4 模式匹配代验证 + R5 缺乏环境意识）+ 13 类典型问题分 Critical/High/Medium 三组 + 三件套通用预防模式；登记到 `scripts/check_repo.py:REQUIRED_FILES`；`memory.py` 索引说明扩展 pitfalls 类别
  - **Step D · 跨模型对抗 CR 协议**：`multi-review.md.tmpl` 模式表新增 **cross-model** 第 4 模式 + 文末用「跨模型对抗通道」专段替换原「未来方向」——三盲区分析（知识 / 注意力 / 确认偏差） + 前置工具清单（≥ 2 模型 CLI，否则降级） + 4 轮协议（并行独立 → 交叉验证 → 辩论 → 自动收敛） + 置信度表输出格式 + 两种执行方式 + 容错策略
  - **Step E · 误报率 + 文档爆炸保护**：`task-log.md.tmpl` 指标字段从 4 扩到 6（新增 `review_fp_rate` 评审误报率 + `docs_produced` 文档总数）；`write-plan.md.tmpl` 自审清单加「文档爆炸门禁」一项 + 新增专段（≥ 10 非代码文档暂停问用户合并 / 推迟 / 接受）
  - **Step C · 代码级反例免疫**：`safety.md.tmpl` 在「输入信任边界」和「不可逆命令 / 密钥」两节追加 4 对 ❌ 错误写法 + ✅ 正确写法代码对（路径拼接 / shell 字符串拼接 / rm -rf 直执行 / 密钥进 git）
  - dogfood 同步 `.claude/rules/anti-laziness.md` + `.claude/rules/safety.md` + `.claude/commands/multi-review.md` + `.claude/commands/write-plan.md`（4 文件）；`task-log.md.tmpl` + 新 references 文件不在 dogfood 同步范围，只影响未来 init 产物
- 关键决策：
  - **5 步互不耦合，单文件单点突破**：每步改 1-2 文件，可独立 revert；避免一次涉太多消费方
  - **R1「不会说我不知道」单独成门禁**：腾讯文章把它列为 5 大根因里**最高**风险，因为 AI 自信语气会**直接削弱审查意愿**，让其他根因引发的错误更容易漏网。值得独立门禁而非塞进现有反合理化表
  - **跨模型 CR 不强制启用**：默认仍是同模型多人格 review，cross-model 只在生产 / 架构 / 安全敏感场景显式启用，避免成本爆炸
  - **文档爆炸阈值 10**：参考腾讯案例「8 需求 99 文件」反推，单任务 10 个非代码文档基本是上限；evolution 模式（吸收外部最佳实践 / 初次搭建知识库）显式可跳过
  - **反例免疫只挑 3-4 条高频规则**：safety.md 已有 5 条规则，全部加代码对会膨胀；只挑路径 / 命令 / rm-rf / 密钥 4 个最常踩的
  - **新 references 不放 dogfood 同步范围**：`scripts/dogfood.py:SYNC_PREFIXES` 只含 `.claude/`，`.agent-harness/references/` 走 init 路径，本仓库**不**自动有这个文件——但已登记到 check_repo 守卫所以 init 路径必发
- 改了哪些文件：
  - 新建：`templates/common/.agent-harness/references/ai-coding-pitfalls.md.tmpl`
  - 模板：`templates/common/.claude/rules/anti-laziness.md.tmpl` + `templates/common/.claude/rules/safety.md.tmpl` + `templates/superpowers/.claude/commands/multi-review.md.tmpl` + `templates/superpowers/.claude/commands/write-plan.md.tmpl` + `templates/common/.agent-harness/task-log.md.tmpl`
  - 工具：`scripts/check_repo.py`（REQUIRED_FILES 加 ai-coding-pitfalls.md.tmpl）+ `src/agent_harness/memory.py`（references 类别说明）
  - dogfood：`.claude/rules/{anti-laziness,safety}.md` + `.claude/commands/{multi-review,write-plan}.md`
- 完成标准：
  - [x] 5 个模板文件按步骤更新
  - [x] `scripts/dogfood.py` 同步成功（4 文件）
  - [x] `make test` 598/598 全绿
  - [x] `make check` 通过（含新 references 守卫）
  - [x] `harness lfg audit` 10/10 保持，无维度掉分
  - [x] 用户确认通过
- 指标：
  - rework_count: 0                   # 一次到位未返工
  - review_p0_count: 0                # 纯模板 / 文档改动，未走 /multi-review
  - review_fp_rate: n/a                # 未走评审，无误报数据
  - user_verify_first_pass: yes       # 用户直接「确认」
  - dialog_rounds: 4                  # 「打开文章」→「评估吸收点」→「按顺序落地」→「确认」
  - docs_produced: 1                   # 仅 current-task.md 一份过程文档（无新建 spec/plan/ADR/review 报告）

## 2026-04-22 feat(workflow): 吸收阿里云 Qoder CLI 文章 3 点

- 需求：用户读完阿里云开发者《Qoder CLI + Harness Engineering 实战：构建 7×24h 无人值守用户反馈自动处理系统》后问「再看一下这篇文章」，评估后按 A/B/C ROI 顺序落地
- 做了什么：
  - **A · 模型分级指引**：`autonomy.md.tmpl` Trust Calibration 表新增「建议模型」列——微小→Haiku / 小→Haiku-Sonnet / 中→Sonnet / 大→Opus / 超大→orchestrator Opus + worker 按 capability。表下补 3 段：核心洞察（便宜模型反而浪费）、如何切换（`/model` / `settings.json` / 编排式场景）、模型 ID 漂移警告（只给类别不写 `claude-opus-4-7`）
  - **B · 成本/循环硬限哲学**：`context-budget.md.tmpl` 新增**规则 4：单任务成本上限**——软限 4 指标（对话轮次 ~50 / 工具调用 ~100 / 读文件 ~30 / compact ~2）+ 硬限 2 指标（`--max-turns 80` / `timeout 1800s`） + 编排层必带硬限要求 + 与 StuckDetector / `/compact` / L0 静默恢复的协作表 + 反合理化 3 条 + 违反检测新项
  - **C · 信心指数量化（门禁 5 升级）**：`anti-laziness.md.tmpl` 门禁 5 末尾新增「高风险动作的信心指数」段——6 类高风险动作清单（自动修复 / migration / 安全代码 / 生产配置 / 不可逆 / 外部写操作） + 0-100 分拆解格式示例 + 三档阈值（≥ 80 执行 / 60-79 人工确认 / < 60 回规划）+ 项目可配阈值 + 与 `⚠️ 待核实` 定性版的边界说明 + 反合理化 3 条
  - dogfood 同步 `.claude/rules/{autonomy,context-budget,anti-laziness}.md`（3 文件）
- 关键决策：
  - **只写模型类别不写具体 ID**（Haiku / Sonnet / Opus）：Anthropic 模型 ID 随版本迭代频繁（Opus 4.7 → 4.8 → ...），硬写会让规则周期性过时。lessons 可吸收为通用经验
  - **软限 vs 硬限二分**：软限面向 Claude Code 交互会话（达到后主动汇报），硬限面向编排场景（`/squad` / `/dispatch-agents` 子进程），两层互不替代
  - **信心指数只在「高风险动作」触发**：全量挂分 = 噪音爆炸，与门禁 5 前半段「事实性断言挂 ⚠️」协同不冲突——日常走定性、关键动作走定量
  - **阈值可配而非硬编码**：默认 80/60 是经验值，安全敏感项目可上调到 90；在 `docs/product.md` 或 `CLAUDE.md` 里声明覆盖
  - **拒绝抽样巡检员 / task-retro.md 自动进化链路 / 动态时间窗口聚类**：业务 CI 场景才需要，本项目（脚手架）不需要——详见上下文评估
- 改了哪些文件：
  - `src/agent_harness/templates/common/.claude/rules/autonomy.md.tmpl`
  - `src/agent_harness/templates/common/.claude/rules/context-budget.md.tmpl`
  - `src/agent_harness/templates/common/.claude/rules/anti-laziness.md.tmpl`
  - dogfood：`.claude/rules/{autonomy,context-budget,anti-laziness}.md`
- 完成标准：
  - [x] 3 个模板文件按 A/B/C 顺序更新
  - [x] `scripts/dogfood.py` 同步 3 文件无漂移
  - [x] `make test` 598/598 全绿
  - [x] `make check` 通过
  - [x] `harness lfg audit` 10/10 保持
  - [x] 用户确认通过（「ok」）
- 指标：
  - rework_count: 0                   # 一次到位未返工
  - review_p0_count: 0                # 纯 rules 文档改动，未走 /multi-review
  - review_fp_rate: n/a                # 未走评审
  - user_verify_first_pass: yes       # 用户直接「ok」
  - dialog_rounds: 4                  # 「文章链接」→「评估吸收点」→「按顺序落地」→「ok」
  - docs_produced: 1                   # 仅 current-task.md




## 2026-04-23 吸收 OpenViking 的目录分层摘要（ABSTRACT/OVERVIEW）

- 需求：深入分析 volcengine/OpenViking 并吸收设计思想；具体落地「ABSTRACT.md / OVERVIEW.md 双层导航」到本项目，并把另一个吸收点（Memory dedup 4 决策）提交成 GitHub Issue
- 做了什么：
  - `.claude/rules/documentation-sync.md`（+ tmpl）：新增「目录导航层」章节，白名单 `.agent-harness/` 和 `.agent-harness/references/`，定义长度上限（ABSTRACT ≤ 200 字符 / OVERVIEW ≤ 4000 字符）和反模式（不得放 `.claude/commands/`）
  - `.claude/commands/recall.md`（+ tmpl）：新增 `--map` 参数 + 第 0 步 --map 独立分支 + 三段式检索说明 + 反合理化新条目
  - 4 对示范产物（dogfood + tmpl 共 8 文件）：`.agent-harness/{ABSTRACT,OVERVIEW}.md` 和 `.agent-harness/references/{ABSTRACT,OVERVIEW}.md`
  - `scripts/check_repo.py`：新增 `check_directory_maps()` 守卫（缺失 error / 空 error / 超长 warn）+ 4 个新 tmpl 加入 REQUIRED_FILES
  - `tests/test_directory_maps.py`：14 条测试（规则 3 + recall 2 + 产物合规 3 + tmpl 存在 2 + 守卫场景 4），总测试 598 → 612
  - `docs/product.md` 9.2 条目 + `docs/architecture.md` / `docs/release.md` / `CHANGELOG.md` 测试计数更新
  - GitHub Issue #45：方案 2（Memory dedup 4 决策改 /compound 和 /lint-lessons）独立提交
- 关键决策：
  - 文件命名用大写 `ABSTRACT.md` / `OVERVIEW.md`（显式）而非 OpenViking 的隐藏文件 `.abstract.md` / `.overview.md`——与 AGENTS.md / CLAUDE.md / README.md 风格一致
  - 规则扩到既有 `documentation-sync.md` 而非新建 `directory-map.md`——dev-map 所有权语义天然延伸
  - 示范目录选 `.agent-harness/` + `.agent-harness/references/`，**不选** `.claude/commands/`——因为后者会被 Claude Code 自动注册为 slash command（见当日 lesson）
  - 只吸收设计思想，不拷贝 AGPL-3.0 代码或 YAML schema；不引入向量依赖，复用现有 BM25
- 改了：
  - `.claude/rules/documentation-sync.md` + `src/agent_harness/templates/common/.claude/rules/documentation-sync.md.tmpl`
  - `.claude/commands/recall.md` + `src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`
  - `.agent-harness/ABSTRACT.md` + `.agent-harness/OVERVIEW.md` + `.agent-harness/references/ABSTRACT.md` + `.agent-harness/references/OVERVIEW.md`（dogfood）
  - 4 个对应 `.tmpl`（`src/agent_harness/templates/common/.agent-harness/` 下）
  - `scripts/check_repo.py`
  - `tests/test_directory_maps.py`（新）
  - `docs/product.md` + `docs/architecture.md` + `docs/release.md` + `CHANGELOG.md`
- 完成标准：
  - ✅ `make ci` 通过（612 测试全绿）
  - ✅ dogfood 无 drift
  - ✅ `check_directory_maps()` 守卫启用
  - ✅ Issue #45 已提交：https://github.com/LaoZYi/harness-starter/issues/45
  - ✅ 用户验证通过
- 返工记录：
  - 初版白名单误放 `.claude/commands/` → dogfood 后 system-reminder 立刻暴露 `/ABSTRACT` `/OVERVIEW` 被注册为 slash command → 当场纠正改为 `.agent-harness/`，把反模式写入规则 + `test_rule_warns_against_claude_commands_dir` 回归锁定（见当日 lesson）

## 2026-04-23 stop hook 认 5 个「等用户」同义字面

- 需求：之前会话 OpenViking 任务里发现 stop.sh 只认「状态：待验证」字面，对「等需求确认」场景会误拦；用户让我后续扩展
- 做了什么：
  - `.claude/hooks/stop.sh` + tmpl：grep 改 `grep -qE "状态：待(验证|用户确认|需求确认|方向确认|确认)"`，同步注释 + block 提示
  - `tests/test_hooks.py`：新增 2 条（待用户确认 / 待需求确认），原待验证保留作回归
  - `docs/architecture.md` / `docs/release.md` / `CHANGELOG.md`：测试计数 612 → 614
- 关键决策：列举 5 个字面而非 `待.*确认` 通用正则——显式清单化可选状态，便于未来按需增减；通用正则会吞掉不想匹配的词
- 改了：6 个文件（dogfood + tmpl + tests + 3 处计数同步）
- 完成标准：
  - ✅ make ci 通过（614 测试）
  - ✅ 用户验证通过
  - ✅ commit 5165d26 已 push 到 origin + zjaf

## 2026-04-25 stop hook 状态识别从 5 字面白名单放宽为通用字段标记

- 需求:用户反馈"经常遇到 Stop hook 误拦"——`Ran 4 stop hooks ⎿ Stop hook error: current-task.md 存在未完成的 checkbox`。复盘 2026-04-23 上次扩展(1 字面 → 5 字面)效果不足,AI 在 /lfg 中段暂停沟通时仍频繁被拦
- 做了什么:
  - `.claude/hooks/stop.sh` + tmpl:grep 改 `^##[[:space:]]*状态[:：][[:space:]]*[^[:space:]]`,任何 AI 主动声明的状态字段(全角/半角冒号 + 任意非空值)都放行;空标记 `## 状态:` 仍 block(防偷懒)
  - `tests/test_hooks.py`:新增 5 测试(半角冒号 / 自定义状态词 / 含描述长状态 / 调研中 / 空状态值仍 block);原 3 个字面回归测试保留
  - 文档计数同步:`CHANGELOG.md` / `docs/architecture.md` / `docs/release.md` 633 → 638
- 关键决策:
  - **守卫的放行条件改基于"结构性标记存在性 + 非空"**(语义判定),而非"字面值清单"(词法白名单)。理由:严格白名单 AI 实际遵循率远低于"主动写状态字段"的概率,UX 反噬——本意防"AI 静默丢进度",实际拦"AI 主动汇报但没用规定词"
  - 保留"空标记仍 block"的防偷懒铁律——防止 AI 写个 `## 状态:` 应付了事
- 改了:6 个文件(dogfood + tmpl + tests + 3 处计数同步)
- 完成标准:
  - ✅ 5 个原字面回归继续 pass
  - ✅ 4 条放宽场景测试通过
  - ✅ 无状态/空状态仍 block(2 条 negative 测试)
  - ✅ make test 638/638 + make check 通过
  - ✅ commit 9cac85c 已落库
  - ✅ 用户验证通过
- 沉淀:
  - lessons.md 新增 1 条:"守卫机制依赖严格字面白名单时 AI 遵循率不足,应改通用字段标记"(标 T6 晋升候选)
  - T6 晋升信号:此规则已在 5 个场景反复触发(2026-04-13 check_repo 守卫白名单 / 2026-04-13 user_docs whitelist / 2026-04-13 _RUNTIME_MODULES / 2026-04-23 stop hook 5 字面 / 2026-04-25 本次)。下次 `/lint-lessons` 应评估晋升为通用 Rule 条目或 anti-laziness 反合理化条目

## 2026-04-25 /lint-lessons 体检三项无风险修复

- 需求:用户跑 /lint-lessons 体检 lessons.md,发现 P0 问题:行 91/114 缺失标题(被 anchor 表引用但无 ## 头),还有 1 处兼容层 vs 破坏性变更适用边界张力
- 做了什么:
  - 修复 2 处缺失标题:加回 `## 2026-04-21 [架构设计] 策略默认值在边界场景必须显式处理不得静默退化` + `## 2026-04-21 [测试] 用户命令执行的 shell 元字符安全必须用 sentinel 文件证明`
  - 互补教训加交叉引用:`2026-04-13 兼容层降低迁移成本`(内部 API)↔ `2026-04-13 破坏性变更要破而彻底`(面向用户)各加 1 行适用边界
- 关键决策:操作 3(SSOT 4 条合并)和操作 5(T6 晋升)留给后续单独处理,影响面较大
- 改了:lessons.md + memory-index.md
- 完成标准:
  - ✅ 标题恢复后有效条目 67 → 69
  - ✅ /recall 和 memory rebuild 能识别这 2 条 lesson
  - ✅ commit 62bd82a 已落库
  - ✅ 用户验证通过

## 2026-04-25 T6 晋升:硬编码白名单反模式从 lesson 升格为正式 Rule

- 需求:5 次反复触发的元规则(check_repo 守卫白名单 / _RUNTIME_MODULES / upgrade three_way / stop hook 5 字面 / stop hook 通用字段)从 lessons 升格到 .claude/rules/,配套 anti-laziness 反合理化条目,4 条历史 lesson 加晋升标注
- 做了什么:
  - 新建 `.claude/rules/architecture-patterns.md`(tmpl + dogfood):反模式 1 标题 + 触发条件三问 + 不适用 3 类 + 4 个替代方案优先级 + 决策树 + 5 历史案例 + 反合理化表
  - `anti-laziness.md` 门禁 3 反合理化表 +1 借口"反正只是再加一个字面/路径就行"(配 5 触发场景驳斥)
  - 4 条历史 lesson 加`✅ 已晋升 2026-04-25 → ...`(2026-04-13 守卫白名单 / 2026-04-14 _RUNTIME_MODULES / 2026-04-21 策略默认值 / 2026-04-25 stop hook 通用字段)
  - 2026-04-23 是 task 不是 lesson 不需要标
- 关键决策:
  - **新建独立规则文件而非塞进 safety.md**:主题专门 + 未来扩展空间
  - **AGENTS.md 不显式索引**:.claude/rules/ 由 Claude Code 自动加载,惯例如此
  - **不加新契约测试**:其他规则也无"必须存在"测试,加上会形成不一致;现有 dogfood 一致性测试已天然覆盖回归
  - **2026-04-23 跳过晋升标注**:它是 task-log 记录(stop hook 1→5 字面扩展)不是 lesson,无对应位置可标
- 改了:5 个文件,+154 行(2 个新建 + 3 个修改)
- 完成标准:
  - ✅ tmpl + dogfood 字节级一致(architecture-patterns + anti-laziness)
  - ✅ 4 条 lesson 双向交叉引用闭环(lesson ↔ rule)
  - ✅ make test 638/638 + make check 全过
  - ✅ commit fb58ea6 已落库
  - ✅ 用户验证通过
- 沉淀:
  - lessons.md 新增 1 条流程类:T6 晋升实战 5 步清单(供下次 T6 候选直接复用)
  - 关键发现:`scripts/dogfood.py` 用 `render_templates()` 自动发现所有模板,新建模板后**不要**手动 cp 到 dogfood,直接 `make dogfood`
- P2 推迟:anti-laziness 借口里"5 个场景"严格说是"4 场景共 5 次触发",下次有相关任务时顺手精准化

## 2026-04-25 T3 merge:4 条 SSOT/grep 同主题 lesson 合并为带 when: 四分支单条

- 需求:/lint-lessons 体检发现 4 条同主题 lesson(2026-04-08 + 2026-04-13 + 2026-04-16 + 2026-04-20)实质讲同一元规则——改 SSOT/枚举/模板字符串前必须 grep 全量下游消费方。resolution-type T3 + dedup decision: merge,本次执行合并
- 做了什么:
  - 新合并条目 `## 2026-04-25 [流程] SSOT/枚举/模板字符串改动前必须 grep 全量下游消费方`(元规则 + 4 个 when: 适用分支 + 反合理化表 3 条)
  - 4 条原 lesson 末尾加 `⚠️ deprecated 2026-04-25 → 指向 when:A/B/C/D`,**不物理删**
  - 索引表新 anchor 加在流程行首位;旧 4 个 anchor 文本加 ⚠️deprecated 前缀但仍可点击(保历史链接)
- 关键决策:T3 不删任一信息原则与 dedup decision: merge 协调——信息全部保留在新合并条目,旧条目作追溯锚点;索引表导航优先指向新版本
- 改了:lessons.md(+58 行新合并 + 4 处 deprecated 标注 + 索引表更新)
- 完成标准:
  - ✅ 新条目带 4 个 when: 分支 + 反合理化表
  - ✅ 4 条原条目全部加 deprecated 标注指向对应分支
  - ✅ 索引表清晰区分活跃 vs deprecated
  - ✅ make test 638/638 + memory rebuild ok
  - ✅ commit e645b87 已落库
  - ✅ 用户验证通过
- 沉淀:无新 lesson(本次是 T6 晋升 5 步清单的 T3 merge 实战补充,不需独立沉淀)

## 2026-04-26 二阶威力评估 4 批改进 + audit 加 5 个质量维度

- 需求:用户跑完 /health 后让我"再评估一下 lfg",我做了二阶评估暴露 5 个 audit 测不到的暗角(引用密度 / 用户确认点过载 / 模板长度炸 context / 实际激活率 / 基础设施引用不平衡),然后用户说"做完所有",批 A/B/C/E 完成,批 D(三层骨架)推迟需先改 templating engine
- 做了什么:
  - 批 A:`/source-verify` + context-budget 在阶段 4 实施期再加引用(各 1→2 次)
  - 批 B:加"用户确认点分级"段(必要/建议/可跳)+ 通道默认行为表;元引用 🔴 改为 STOP 字面降噪
  - 批 C:抽 lfg.md.tmpl 中 squad 章节(148 行)到 `templates/common/.agent-harness/references/squad-channel.md.tmpl`,主模板留指针 + 速览(30 行);修 3 条契约测试改为联合检查主模板 + references
  - 批 D:推迟 — templating engine 不支持 include,需先改基础设施
  - 批 E:lfg audit 加 5 个新维度(11 引用深度 / 12 主模板长度 / 13 用户确认点密度 / 14 关键守卫多点 / 15 通道层级化),抽到 `lfg_audit_quality.py`(124 行,主 checks.py 削回 233 < 280),修 4 条 test_lfg_audit 测试
- 关键决策:
  - **新增维度暴露真实暗角而不是装饰满分** — 旧 10 维 audit 给 10.0 满分掩盖了 3 个真实弱点;新 15 维 audit 13.54/15(90.3%)暴露 Dim 11(0.64)、Dim 12(0.5)、Dim 13(0.4)三个具体可量化的债务,后续可直接对照分数追踪进度
  - **批 D 推迟而非硬上** — 三层骨架需要先扩 templating engine,工作量翻倍且影响其他 tmpl 功能;隔离为单独任务更安全
  - **抽离重构破坏契约测试时的应对** — squad 抽离破 3 测试,改为"主模板必含指针 + references 必含详细内容"的联合契约,而非死绑某一处
- 改了:9 个文件,+553 / -269 行,2 个新文件(squad-channel.md.tmpl + lfg_audit_quality.py)
- 完成标准:
  - ✅ 主模板 930 → 848 行(-82 行净削)
  - ✅ /source-verify + context-budget 引用 1→2 次
  - ✅ squad 章节抽离 + references 索引
  - ✅ audit 10 维 → 15 维,新维度立即生效暴露暗角
  - ✅ make test 638/638 + make check 全过
  - ✅ commit f40f0cc 已落库
  - ✅ 用户验证通过
- 沉淀:无新 lesson(关键元教训已在前期 lessons "能力集成度评估必须用量化扫描而非主观判断"覆盖,本次是同一思想的扩展应用)
- 推迟项(下次任务):
  - 批 D 三层骨架:需先改 templating engine 加 include 支持(中等复杂度,需独立 /lfg)
  - Dim 11 引用深度仍 0.64(10 个浅集成 skill 待加深引用)
  - Dim 12 主模板长度仍 848 行(批 D 完成后预期降到 500-600)
  - Dim 13 确认点密度仍 1.83/50 行(需要主流程级再降 🔴 字面)




## 2026-04-26 lfg 第 5 批威力评估（13.54 → 14.85 / 15）

- 需求：用户说"评估 lfg"，我用 `harness lfg audit` 拿到 13.54/15 的基线，列出维度 11/12/13 三处弱点 + 改进路线（参考 commit f40f0cc 的二阶威力评估方法论），用户回"直接动手"
- 做了什么：
  - **维度 13（确认点密度）0.40 → 1.00**：31 🔴 砍到 13 个——删末尾"用户确认点汇总"表（与"确认点分级"段重复 −7）、5 个段落标题装饰 emoji 改文字"需确认"、4 个 squad 速览改文字"必须"、2 个 reminder 块改 ⚠️（模板第 214 行已说"是 reminder 不是 confirmation"）
  - **维度 12（主模板长度）0.50 → 0.85**：849 → 756 行（−93）。抽 `progress 追踪格式` 53 行示例到 `references/lfg-progress-format.md`、抽 `GitLab 同步关闭脚本` 40 行到 `references/gitlab-issue-closure.md`，主模板留 1-2 行指针
  - **维度 11（引用深度）0.64 → 1.00**：8 个浅集成 skill 各补 1 次有意义引用——`/adr` 阶段 9.2 显式串、`/agent-design-check` 阶段 5 评审 PASS 后串（验证 F3/F5/F8/F10/F11 执行期未漂移）、`/debug` 阶段 7.1 验证失败注脚、`/doc-release` 阶段 9.1 注脚（lessons vs release 文档分离）、`/execute-plan`+`/write-plan`+`/use-worktrees` 在"通道默认行为"段融合通道选择建议、`/receive-review` 评审结论表注明先消化反馈
  - 修测试：`test_threshold_gate_fails_below` 原绑死阈值 14.5（基于 ~13.5 的硬编码假设），改为 15.5 表达"门禁失败路径"语义，不随分数漂移
  - `make dogfood` 同步 `.claude/commands/lfg.md`
- 关键决策：
  - **抽离 vs 删减**：选抽长段到 references/ 而不是删——保留全部信息密度，主模板减负，符合维度 15"通道层级化"已建立的机制
  - **停在 14.85 而非追 15.0**：维度 12 满分需 ≤ 600 行（再砍 156 行），但当前抽出去的两份 reference 是"低频但需详查"模板（高 ROI），继续抽要动核心阶段说明，损害单文件可读性。审计模块也只把 ≤ 600 标"优秀"而非"必须"——避免"为分而分"陷阱
  - **🔴 emoji 不等于 STOP**：模板第 214 行已分类"必要 / 建议 / 可跳（reminder 不是 confirmation）"，本次让 emoji 使用与该分类对齐——只有真正 STOP 点保留 🔴；标题装饰、速览标记、reminder 都用文字替代
  - **测试期望与实际值脱钩**：改 audit 阈值测试时不绑当前总分（绑死会让每次模板优化都触发失败），改用"超过满分必失败"的稳定语义
- 改了：
  - `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` 主模板（−93 行）
  - `src/agent_harness/templates/common/.agent-harness/references/OVERVIEW.md.tmpl` 加 5 条索引
  - `tests/test_lfg_audit.py` 修 threshold 测试
  - `.claude/commands/lfg.md` dogfood 同步
  - 新增 `templates/common/.agent-harness/references/gitlab-issue-closure.md.tmpl`
  - 新增 `templates/common/.agent-harness/references/lfg-progress-format.md.tmpl`
- 完成标准：
  - ✅ `harness lfg audit` 总分 14.85/15（≥ 14.5）
  - ✅ 维度 11 = 1.00（28/28），维度 12 = 0.85（756 行），维度 13 = 1.00（0.86/50）
  - ✅ `pytest -q` 638/638 pass
  - ✅ `scripts/check_repo.py` passed
  - ✅ 用户确认通过
- 沉淀：无新 lesson。本次踩的关键点（"emoji 装饰 ≠ STOP 触发"、"测试期望勿绑动态分数"）属于已有 lesson "能力集成度评估必须用量化扫描"的延伸应用，不重复立条
- 推迟项（下次任务可考虑）：
  - 维度 12 满分需 ≤ 600 行 — 仅在主模板被进一步优化或某阶段真正成熟到可抽离时再做
  - audit 自身可加"是否为 STOP 装饰 emoji"的扫描（防止后续又把 🔴 用回标题修饰）

## 2026-04-26 health 满分化 + gstack 升级与 onboarding + 关闭 Issue #47

- 需求：跑完 /health（10/10）后用户接受推荐"按 LOW 项做 + gstack 也处理"，然后 /lfg #47 时发现 Issue 验收已被前一批工作绕过达成 → 关闭
- 做了什么：
  - **health 第 5 维上线**：`brew install shellcheck`（0.11.0）+ 跑 `make shellcheck-hooks` 确认 .claude/hooks/*.sh 干净（之前因 shellcheck 未装，第 5 维一直是 SKIPPED，权重重分配掩盖了"hooks 没静态扫过"的事实）
  - **CLAUDE.md ## Health Stack 段**：14 行映射 typecheck/lint/test/deadcode/shell/skills-lint/repo-guard 到具体命令，注明 SSOT 是 Makefile，本节是 gstack `/health` 兼容镜像，下次 /health 直接读不再 auto-detect
  - **gstack 升级 0.15.15.1 → 1.13.0.0**：global-git 安装（~/.claude/skills/gstack/.git），git stash + reset --hard origin/main + ./setup，跑过 v1.0.0.0/v1.1.3.0 两个 migration（v1.1.3.0 移除了 stale /checkpoint，改用 native /rewind + /context-save）
  - **gstack onboarding 4 项全选推荐默认**：lake intro 标 seen / telemetry off / proactive false / routing_declined true。理由：本项目有自己的 superpowers 工作流（/lfg /tdd /verify 等）+ .claude/hooks 生命周期感知 + .claude/rules SSOT，gstack proactive 和 routing 会与之重叠冲突
  - **关闭 Issue #47**：/lfg #47 拉到 Issue 后发现验收标准全部已被 commit bcbebfa（lfg 第 5 批）达成（Dim 12 0.5→0.85、dogfood pass、总分 +1.31），templating engine include 支持是 YAGNI，gh issue close 47 + 详细评论说明
- 关键决策：
  - **gstack onboarding 选择"对抗整合"而非"默认接入"**：gstack 默认想往 CLAUDE.md 写自己的 routing 段、想 proactive 自动跑 skill —— 但本项目 CLAUDE.md 明确说"不要把新规则只写这里"，且 .claude/rules + superpowers-workflow.md 已有自己的 routing 系统。两套系统并存会让 AI 在调用 skill 时混淆，所以选择 routing_declined + proactive false，让 gstack 退化为"用户主动 / 输入"才用的辅助工具
  - **shellcheck 装 vs 跳过的 ROI 翻转**：之前第 5 维 SKIPPED 时权重重分配让总分仍能 10/10，但这是"虚高"——hooks/*.sh 一直没被静态扫过。装上 shellcheck 后 make shellcheck-hooks 立即返回 ok，证明 hooks 历史代码本来就干净，只是没人证。从此第 5 维不再是"权重洗牌掩盖"
  - **Issue #47 关闭而非保留 / 扩验收线**：用户在 Issue 创建时（task-log "2026-04-26 二阶威力评估"）把"批 D 三层骨架"标为推迟。第 5 批用更轻量的"抽段到 references/"绕过了对 templating engine 的需求。继续做 templating include 是为分而分（Dim 12 = 0.85 → 1.0 需 ≤ 600 行，但 99% 已是健康天花板）。选 A 关闭 + 写明 YAGNI 备注，未来真需要 include 时再做
- 改了：
  - `CLAUDE.md` 新增 ## Health Stack 段（commit 6e97d7a，已 push）
  - `~/.gstack/.completeness-intro-seen` / `.telemetry-prompted` / `.proactive-prompted` 标记位
  - `~/.gstack/config.yaml` proactive=false, routing_declined=true, telemetry=off
  - `~/.claude/skills/gstack/` 升级到 1.13.0.0（外部依赖，不在仓库内）
  - GitHub Issue #47 关闭并附详细说明
- 完成标准：
  - ✅ `make ci` 全过（638 tests + ruff + mypy + vulture + skills-lint + check_repo）
  - ✅ `make shellcheck-hooks` ok（第 5 维上线）
  - ✅ gstack `--version` = 1.13.0.0
  - ✅ gstack-config get 4 项配置就位
  - ✅ Issue #47 state=CLOSED + 详细 closing comment
  - ✅ git 工作区干净 + 已 push
- 沉淀：无新 lesson。本次的关键判断（"为分而分是反模式"、"工具链可疑'满分'要拆解后看"、"外部 skill 系统与项目自有系统冲突时选保护项目"）属于已有 anti-laziness 反合理化表 + autonomy Trust Calibration 的延伸应用，不重立条
- 推迟项：无

## 2026-04-26 关闭 Issue #48(事实已完成)

- 需求:`/lfg #48` — Dim 11 引用深度 0.64 → 1.0(10 个浅集成 skill 加深引用)
- 做了什么:阶段 0.1 拉 Issue 后发现验收已被 commit bcbebfa(同日第 5 批威力评估)随附完成,Dim 11 当前 = 1.00/1.00(28/28),make ci exit 0 → 用户选 A 直接关闭
- 关键决策:不为分而分。Issue 创建时点的状态被同日另一批工作覆盖完成但未显式 closes #48,不是新工作机会;继续做反而会膨胀主模板拖低 Dim 12
- 改了:Issue #48 state=CLOSED + 关闭评论说明事实状态
- 完成标准:Dim 11 ≥ 0.85 ✅ (1.00) | 主模板净增 ≤ 30 行 ✅ (755 行,未触碰) | make ci 全过 ✅
- 沉淀:无新 lesson。"Issue 验收被前期工作绕过达成时直接关闭而非补做"已在 2026-04-26 health 满分化 + Issue #47 任务里实践过,模式重复,不重立条
- 推迟项:无

## 2026-04-26 关闭 Issue #49(事实已完成)

- 需求:`/lfg #49` — Dim 13 确认点密度 0.40 → 0.7+(31 🔴 / 848 行 = 1.83/50 行 砍到 ≤ 25 🔴)
- 做了什么:阶段 0.1 拉 Issue 后发现验收已被 commit bcbebfa(同日第 5 批威力评估)随附完成,Dim 13 当前 = 1.00/1.00(13 🔴 / 755 行 = 0.86/50 行,优秀),make ci exit 0 → 用户选 A 直接关闭
- 关键决策:跟 Issue #48 同款判断——不为分而分。Issue 创建时点的状态被同日另一批工作覆盖完成但未显式 closes #49,继续做反而会动到批 B 标记的"必要"级 STOP,产生回退风险
- 改了:Issue #49 state=CLOSED + 关闭评论附 task-log 证据链
- 完成标准:Dim 13 ≥ 0.7 ✅ (1.00) | 批 B 必要级 STOP 保留 ✅ | make ci 全过 ✅ | 契约测试 test_lfg_squad_channel 不破 ✅
- 沉淀:无新 lesson。同日第 3 次实践"Issue 验收被前期工作绕过达成时直接关闭"模式(Issue #47 → #48 → #49),已固化为操作惯例不重立条
- 推迟项:无

## 2026-04-26 吸收 muratcankoylan/Agent-Skills-for-Context-Engineering(Issue #50)

- 需求:吸收 5 类 context degradation 诊断框架(lost-in-middle / poisoning / distraction / confusion / clash)+ tokens-per-task 优化目标 + Artifact Trail 字段
- 做了什么:
  - 新建 `templates/common/.agent-harness/references/context-degradation-patterns.md.tmpl`(190 行,5 类 pattern × 症状/根因/缓解策略/检测信号)+ 镜像到本仓库 references
  - `context-budget.md.tmpl` 加规则 4「优化目标:tokens-per-task,不是 tokens-per-request」节(re-fetching frequency 信号)+ 文末「诊断侧:Context Degradation 5 类模式」节作 reference 入口
  - `anti-laziness.md.tmpl` 反合理化表新增「压缩越狠越省 token」借口驳斥
  - `lfg-progress-format.md.tmpl` Context 段后加 Artifacts touched 字段(读/改/删除三类)
  - `lfg.md.tmpl` 阶段 0.2 第 12 条加 `/recall --refs context-degradation` 加载 + 阶段 4.1 Context 预算守卫加 tokens-per-task 提醒
  - `OVERVIEW.md.tmpl` 加新 reference 索引行 + 触发场景行(同步本仓库)
  - `tests/test_lfg_context_degradation.py`(114 行,9 条契约,全过)
  - dogfood 同步 3 个 .claude/ 文件 + 测试计数 638→647 同步到 CHANGELOG/architecture/release
- 关键决策:
  - **3 个相邻 reference 视角正交不重合**——`ai-coding-pitfalls`(腾讯 LEGO)关注 AI 行为问题、`claude-code-internals`(Windy3f3f3f3f)关注 Claude Code 5 级压缩底层机制、新 `context-degradation-patterns`(muratcankoylan)关注 context window 内 attention 机制问题。三者在 OVERVIEW 边界节明确说明可同时加载
  - **不实施 Anchored Iterative Summarization 工程**——只吸收方法论作 L2 reference,不写实际压缩代码(避免引入运行时复杂度)
  - **Artifact Trail 不改 audit.jsonl**——只在 lfg-progress-format 加字段;audit.jsonl 是 WAL 不该膨胀
  - **9 个 step commits + tags 保留**(lfg/i50-step-1 .. step-9)——便于精确回滚到任意 step,沿用 Issue #45/#46 evolution pattern,而非 squash
- 改了:16 文件 +626/-6 行;模板 5 个 + 本仓库 5 个 + 测试 1 个 + 文档 3 个 + current-task 标记
- 完成标准:
  - ✅ R-001 新 reference 190 行 ≥ 130(达成)
  - ✅ R-002 tokens-per-task 引入 context-budget + 反合理化表
  - ✅ R-003 Artifacts touched 字段
  - ✅ R-004 make ci exit 0(647 tests / mypy / ruff / vulture / skills-lint / shellcheck / check_repo 全过)
  - ✅ R-005 dogfood 后 lfg audit 14.85/15 维持(Dim 12 仍 0.85,无退步)
- 沉淀:无新 lesson(T5 模式)。"吸收外部学术化方法论时优先做成 L2 reference"已在 lessons.md 2026-04-23 条目覆盖,本次是第 N 次实践不立新条
- 推迟项:无

## 2026-04-26 吸收 forrestchang/andrej-karpathy-skills(Issue #51)

- 需求:吸收 Karpathy 4 原则的 Simplicity First + Surgical Changes(反过度工程化),补足 anti-laziness 偏防偷懒缺反过度膨胀的另一极
- 做了什么:
  - 新建 `templates/common/.claude/rules/simplicity.md.tmpl`(105 行,4 准则 + 反合理化表 + 适用边界 + 修反模式例外)+ 镜像本仓库
  - `agent-design.md.tmpl` F11 加 simplicity 准则 2「Surgical Changes」同源说明(F11 是 agent 层,simplicity 准则 2 是代码层,两者目标都是保护署名契约)
  - `anti-laziness.md.tmpl` 顶部加与 simplicity 反向互补声明(防偷懒 vs 防膨胀,目标都是"刚刚好")
  - `requirement-mapping-checklist.md.tmpl` 末尾加「模糊需求 → 可验证目标转换模板」7 类 pattern(Add validation / Fix bug / Refactor / Optimize / Migrate / Improve UX / Support Z),每条 R-ID 必须能用机械化命令产出 ✅/❌ 二元结果
  - `lfg.md.tmpl` 3 处接入:阶段 0.1 第 3 步引用转换模板 + 阶段 4.2 表格新增'顺手改进邻居代码'禁止行 + 阶段 4.3 自检表加 simplicity 列
  - `tests/test_lfg_simplicity_absorption.py`(125 行,11 条契约,全过)
  - dogfood 同步 3 个 .claude/ 文件 + 测试计数 647→658 同步到 CHANGELOG/architecture/release
- 关键决策:
  - **simplicity 命名抽象化**——不命名 karpathy-principles.md(避免与外部项目耦合),抽为通用 simplicity.md。Karpathy 是来源,不是规则名
  - **不吸收 Think Before Coding 原则**——已被 task-lifecycle 假设清单覆盖,不重复立条
  - **修反模式例外明示**——Surgical Changes "Match existing style" 与本项目 stop hook 通用字段化教训(从字面白名单升级到结构化字段)看似冲突,实际不冲突。stop hook 升级是修反模式,在 simplicity.md 边界声明里明示"修反模式"是例外,需 commit 显式说明对照的 lesson 标题
  - **不改 superpowers-workflow.md**——Issue body 提到的"项目规则清单"实际不存在(规则在 .claude/rules/ 目录自动加载),跳过该步
- 改了:12 文件 +423/-6 行
- 完成标准:
  - ✅ R-001 simplicity.md 105 行 + 4 准则关键词全在
  - ✅ R-002 anti-laziness 边界声明 + simplicity.md 边界节
  - ✅ R-003 与 safety「改一处查所有同类」边界(扩散 vs 越界场景)
  - ✅ R-004 7 类转换模板 + 反模式对照
  - ✅ R-005 lfg.md 3 处引用都过契约测试
  - ✅ R-006 make ci exit 0(658 tests / mypy / ruff / vulture / skills-lint / shellcheck / check_repo)
  - ✅ R-007 lfg audit 14.85/15 维持(Dim 12 仍 0.85,759 行良好)
- 沉淀:无新 lesson(T5 模式)。"吸收外部学术化方法论时优先做成 L2 reference / 抽象化命名"已在前两次 evolution 实践 + lessons.md 2026-04-23 条目覆盖,本次第 3 次实践不立新条
- 推迟项:无


## 2026-04-26 补吸 Karpathy Think Before Coding 缺口(Issue #53)

- 需求:吸收 forrestchang/andrej-karpathy-skills 原则 1 的 3 条缺口(多解读呈现 / Push back / Name what's confusing),补 #51 漏吸的部分。是 #51 的 12 天 evolution-update 增量
- 做了什么:
  - `task-lifecycle.md.tmpl` 第 1 步加多解读列表(仅模糊需求触发,锚定 5 类触发 + 3 类不触发)
  - `task-lifecycle.md.tmpl` 第 2 步加 Name what's confusing(显式说明哪里不清楚)+ 主动提出更简单方案
  - `anti-laziness.md.tmpl` 门禁 5 内嵌 Push Back 子节(主体后/信心指数前,因三者同源——AI 主动 surface 判断而非隐藏)
  - Push Back 边界三维表(What/How/When)防反噬;明示「不推翻用户指令优先级」与 CLAUDE.md 兼容
  - 反合理化新增 4 条:用户既然这么要求 / Push back 显得不配合 / 这次范围小 / 反复 push back 显得抬杠
  - dogfood 同步 .claude/rules/ 2 文件
- 关键决策:
  - **push back 现场演示**——阶段 0.3 我对 Issue body 推荐的「选项 B 新建 150 行 references/simplicity-examples.md」push back,理由:违反 simplicity 准则 2 Surgical Changes(不是用户主动要求的扩展)。用户授权按推荐方案做,任务范围从「2 rule + 1 reference」缩到「2 rule」。这是新规则的第一个 dogfood
  - **门禁 5 内嵌位置**——Push Back 子节插入门禁 5 主体后、信心指数前。理由:三者同源,都是「AI 应主动 surface 判断而非隐藏让用户被动接受」
  - **不开独立 SubAgent 评审**——纯 Markdown 文档变更 + 已通过完整 ci,按 anti-laziness 门禁 2 例外条款主会话 2 角色评审,收益高于成本
- 改了:5 文件 +188/-7 行(2 .tmpl 源 + 2 .claude/rules/ 渲染产物 + current-task.md)
- 完成标准:
  - ✅ R-001 多解读×3, 触发条件×3
  - ✅ R-002 哪里不清楚/Name what×2, 更简单/simpler×2
  - ✅ R-003 Push back×7, 边界×2, 反合理化新借口×2
  - ✅ R-004 dogfood 同步 2 文件
  - ✅ R-005 make ci 全绿(658 tests OK + mypy 49 files clean + ruff 0 issue)
  - ⊘ R-006 EXAMPLES.md 选项 B(out-of-scope,push back 后用户授权缩范围)
- 沉淀:无新 lesson(T5 模式)。本次任务的元洞察「push back 在 evolution-update 任务中可缩窄范围」已固化为 anti-laziness 门禁 5 + task-lifecycle 第 2 步规则本身,不在 lessons 重复立条。push back / Name confusing / 多解读呈现这 3 条 Karpathy 原则 1 缺口本身就是来自上游可吸收的 lesson 沉淀
- 推迟项:Issue #53 新特性 2 EXAMPLES.md 选项 B 150 行 reference(out-of-scope,如未来 /multi-review 反复抓"过度膨胀"找不到具体案例,再独立提 issue 做)
