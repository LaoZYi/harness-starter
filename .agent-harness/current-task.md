# Current Task

## 任务目标

吸收 CCGS（Donchitos/Claude-Code-Game-Studios）的 P0 — `/team-*` 场景化编队模式，为本项目预制 4 个 team skill。

**Issue**：#55（evolution 标签，P0 only，用户确认 A 方案）

**为什么做**：
- CCGS 9 个 team skill 把多 agent 编排从「通用调度器」升级为「场景化预制流水线」，减少 orchestrator 临时决策成本
- 对应 simplicity.md 准则 1（不重复造决策）+ context-budget tokens-per-task（固定流水线减少 worker prompt 漂移）
- 本项目目前只有 `/dispatch-agents`（通用一次性 map-reduce）和 `/squad`（通用长任务并行框架）—— 缺「常见组合拳」预制

## 范围（4 个 team skill）

| Skill | 串联现有 skill | 适用场景 |
|---|---|---|
| `/team-spec` | spec → plan-check → adr | 复杂需求规格化（≥3 文件 / 含模糊词 / 涉及架构决策） |
| `/team-implement` | write-plan → execute-plan → tdd → verify | 标准实施（已有规格，需写代码并验证） |
| `/team-review` | multi-review → cso → receive-review | 完整评审（含安全审计 + 结构化消化反馈） |
| `/team-doc` | outline-doc → draft-doc → review-doc → finalize-doc | 文档场景独立调用入口（覆盖 lfg-doc 内部已有链路） |

## 设计原则（吸收前任教训）

- **D 方案：先抄 + 留位置**（来自 lessons.md 2026-04-27 教训）
  - 4 个 skill 各自完整写一遍流水线，**不**抽共享 base
  - 等真出现 3+ skill 长得很像了再考虑抽象
  - 每个 skill 独立可读，新人不用跨文件理解
- **不放进 `.claude/commands/`**：模板源在 `templates/superpowers/.claude/commands/*.md.tmpl`，由 `make dogfood` 同步（来自 lessons.md 2026-04-23「`.claude/commands/` 下任何 .md 都会被 Claude Code 注册为 slash command」）
- **保留 CCGS 6 阶段骨架**：Argument check → Team Composition → Pipeline → Error Recovery Protocol → File Write Protocol → Output verdict → Next Steps

## 假设清单

- 假设：4 个 skill 都放在 `templates/superpowers/.claude/commands/team-*.md.tmpl` | 依据：现有 39 个 skill 都在该位置 + evolution 集成规范
- 假设：每个 skill 用 `{{project_name}}` / `{{project_type}}` / `{{language}}` 模板变量 | 依据：现有 skill 模板都用这些变量
- 假设：skills-registry.json 加 4 条记录，category 选 `process`（spec）/ `implementation`（implement）/ `review`（review/doc） | 依据：registry 现有分类
- 假设：`expected_in_lfg: false`（team-* 是局部编队，不是 lfg 阶段技能） | 依据：team-* 跟现有 lfg 阶段调用的原子 skill 是「打包 vs 单调」关系，不应被 lfg 阶段直接调用
- 假设：team-* 是**用户显式调用**而非 AI 自动选择 | 依据：CCGS 设计就是用户打 `/team-combat` 触发

## 完成标准（可验证）

1. **文件存在**：`ls templates/superpowers/.claude/commands/team-*.md.tmpl` 输出 4 个文件
2. **结构合规**：每个 skill 有 frontmatter（name / description / argument-hint / user-invocable / allowed-tools）+ 6 节骨架
3. **registry 同步**：`jq '.skills | map(select(.id | startswith("team-")))' templates/superpowers/skills-registry.json` 输出 4 条
4. **dogfood 无漂移**：`make dogfood` 跑完后 `git status` 显示 `.claude/commands/` 下新增 4 个文件
5. **CI 通过**：`make ci`（含 skills-lint）全绿
6. **文档同步**：`.claude/rules/superpowers-workflow.md` 「所有可用技能」表新增 4 行；`docs/product.md` 功能列表追加
7. **lessons 沉淀**：`/compound` 写入「team-* 场景化编队」相关教训 + memory rebuild 刷新 L1

## 计划步骤

- [x] 1. 探查现有 skill 模板的 frontmatter 和文件命名约定（看 1-2 个 .tmpl 示例）
- [x] 2. 写 `team-spec.md.tmpl`（spec → plan-check → adr 三阶段）
- [x] 3. 写 `team-implement.md.tmpl`（write-plan → execute-plan → tdd → verify 四阶段）
- [x] 4. 写 `team-review.md.tmpl`（multi-review → cso → receive-review 三阶段）
- [x] 5. 写 `team-doc.md.tmpl`（outline → draft → review → finalize 四阶段）
- [x] 6. 更新 `templates/superpowers/skills-registry.json`（加 4 条记录）
- [x] 7. 更新 `superpowers-workflow.md.tmpl`（技能列表 + 何时使用）+ evolve.md.tmpl + usage-manual.md
- [x] 8. 更新 `docs/product.md`（追加 8.10 项 P0 落地的功能描述）
- [x] 9. 跑 `make dogfood` 同步模板（无漂移）
- [x] 10. 跑 `make ci` 验证全绿（694 tests pass + skills-lint OK + check_repo OK）
- [ ] 11. 关闭 Issue #55 + 更新 task-log + /compound 沉淀教训

## 状态：待验证

实施完成。完成标准核验：
1. ✅ 文件存在：4 个 team-*.md.tmpl 全部到位
2. ✅ 结构合规：6 节骨架（参数检查 / 适用场景 / 编队组成 / 流水线 / 错误恢复 / 文件写入约定 / 输出 / 下一步）
3. ✅ registry 同步：42 → 46 条（jq 验证 4 个 team-* 都在）
4. ✅ dogfood 无漂移：`make dogfood` 后 .claude/commands/ 自动同步 4 个 team-*.md
5. ✅ CI 通过：`make ci` 全绿（694 tests pass / skills-lint OK / deadcode OK / shellcheck OK / check_repo OK）
6. ✅ 文档同步：superpowers-workflow.md.tmpl + docs/product.md (8.10 项) + evolve.md.tmpl + docs/usage-manual.md 都已更新
7. ⏳ lessons 沉淀：进入阶段 9 / compound

## 实施摘要

- **新增 4 个 team-* skill**（templates/superpowers/.claude/commands/）
  - team-spec.md.tmpl：spec → plan-check → adr
  - team-implement.md.tmpl：write-plan → execute-plan / tdd → verify
  - team-review.md.tmpl：multi-review → cso → receive-review
  - team-doc.md.tmpl：outline → draft → review → finalize
- **同步 5 处文档**：skills-registry.json / superpowers-workflow.md.tmpl / evolve.md.tmpl / usage-manual.md / product.md
- **修计数漂移**：批量 38 → 42（README + CHANGELOG + product + architecture + usage-manual + project.json）
- **修测试期望**：test_skill_count_is_42 → test_skill_count_is_46（含 +4 团队 skill 注释）；test_in_lfg_count_matches_excluded 14 → 18

## 历史参考

- lessons.md 2026-04-27「上层 skill 多场景化先走 D 方案（先抄 + 留位置）」→ 不抽共享 base
- lessons.md 2026-04-23「`.claude/commands/` 下任何 .md 都会被 Claude Code 注册为 slash command」→ 模板放 templates/ 不放 .claude/
- lessons.md 2026-04-21「入口技能 gap 先用工具量化再动手」→ 4 个 team-* 都是「现有 skill 的固定串联」，复杂度可控

## 基线

- 分支：master（clean）
- HEAD：2264cee Merge branch 'feat/doc-scenario-skeleton'
- 测试基线：待跑 `make test` 记录
