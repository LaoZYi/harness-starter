# Current Task

## 状态：进行中

## 任务目标

新增 `slide-deck` 项目类型，作为第 2 个非代码场景，推进 Issue #56 触发条件 1（场景数 ≥ 2）。本次按 D 方案「先抄 + 留位置」执行：占位脚手架 + 独立入口 `/lfg-slide`，**不**新开底层 5 个 slide skill，**不**实施 #56 黑名单。

## 假设清单

- 假设：slide-deck 产物形态默认为 markdown（Marp / Reveal.js），章节 = 幻灯片 | 依据：D 方案「先抄 + 留位置」
- 假设：本期不动 `discovery.py` 的 `_detect_project_type` 自动检测逻辑 | 依据：仅 1 场景看不清自动识别 trigger 应当是什么
- 假设：`/lfg-slide` 与 `/lfg-doc` 严格平行（同样 4 阶段：outline → draft → review → finalize），底层调用相同的 doc skill | 依据：用户回复「严格平行吧」
- 假设：slide-deck 的「视觉评审维度 / 演讲稿填充」本期只写在 `/lfg-slide.md.tmpl` 注释里，不传 context 参数给 review-doc | 依据：D 方案精神

## 验收标准

1. `harness init --project-type slide-deck <dir>` 成功，产物含 conventions + lfg-profiles + 5 个 doc skill commands + lfg-slide.md
2. `make ci` 全过；新契约测试 9+ 项全通；既有 `test_doc_scenario_scaffold.py` 不回退
3. `harness lfg audit` total ≥ 7.0
4. Issue #56 触发条件 1（场景数 ≥ 2）已满足

## 计划步骤（TDD：先写测试 → RED → 实施 → GREEN）

- [x] 0. 建工作分支 `feat/slide-deck-project-type`，记录基线 HEAD `cfbaecba`，`make test` 694 pass
- [x] 1. 写 `tests/test_slide_deck_scenario_scaffold.py` 契约测试（R1-R11），跑失败证明有效
- [x] 2. `discovery.py:19-22` PROJECT_TYPES 加 `"slide-deck"`
- [x] 3. `init_flow.py:19-22` PROJECT_TYPE_CHOICES 加 `"slide-deck"`
- [x] 4. 新建 `templates/slide-deck/.claude/rules/slide-conventions.md.tmpl`
- [x] 5. 新建 `templates/common/.agent-harness/lfg-profiles/slide-deck.yaml.tmpl`
- [x] 6. 新建 `templates/superpowers/.claude/commands/lfg-slide.md.tmpl`
- [x] 7. 更新 `templates/superpowers/skills-registry.json` 注册 `lfg-slide`
- [x] 8. 新建 `presets/slide-deck.json`
- [x] 9. 更新 `lfg-profiles/README.md.tmpl` + workflow rule + evolve + usage-manual + 计数同步（42→43, 694→707）+ dogfood
- [x] 10. 跑测试：13 新契约测试全过 + `make ci` 707 tests OK
- [x] 11. 文档同步：`docs/product.md` 加 8.11、`docs/architecture.md` 模板列表更新
- [ ] 12. 最终验证 + `/git-commit`

## 不做的事

- ❌ 不开 `/outline-slide` / `/draft-slide` / `/review-slide` / `/finalize-slide` / `/team-slide`
- ❌ 不实施 Issue #56 黑名单
- ❌ 不动 `_detect_project_type` 自动识别
- ❌ 不关闭 Issue #56（仍 long-term tracking，仅推进条件 1）

## 基线快照

- HEAD: cfbaecba96b3b02adba8c7e14be766c133bb6b17
- Tests: 694 pass
- Branch: feat/slide-deck-project-type
