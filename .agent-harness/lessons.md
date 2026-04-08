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

## 2026-04-08 新增技能时文档散布计数需全量扫描

- 错误：新增 `/spec` 技能后，技能数从 27 变 28，但 12+ 处散布的计数引用容易遗漏
- 根因：技能计数硬编码在 CHANGELOG、README、docs/、templates/ 等多个文件中，没有单一来源
- 规则：新增技能后必须 `grep "N 个"` 全量扫描确认无遗漏。长期可考虑在 check_repo.py 中加计数一致性校验

