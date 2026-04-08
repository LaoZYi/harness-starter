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

