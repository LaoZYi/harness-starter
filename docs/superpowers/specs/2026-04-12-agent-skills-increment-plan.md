# 实施计划：agent-skills 增量吸收

> Spec：`docs/superpowers/specs/2026-04-12-agent-skills-increment-spec.md`
> 分支：`feat/agent-skills-increment` | 基线 commit：`9959249`

## 步骤

每步 → 原子 commit。不打 tag（上次清理过，简化流程）。

### 1. 新建 `/source-verify` 技能模板

`src/agent_harness/templates/common/.claude/commands/source-verify.md.tmpl`

内容：`DETECT → FETCH → IMPLEMENT → CITE` 四阶段、依赖文件映射表、源权威层级、反合理化表（6 条）。

验证：grep "DETECT" + 占位符完整性。

### 2. 新建 references/ 目录 + 4 个 checklist 模板

路径：`src/agent_harness/templates/common/.agent-harness/references/`

- `accessibility-checklist.md.tmpl` — a11y（从上游原文保留 + 汉化序言 + 框架关联说明）
- `performance-checklist.md.tmpl` — perf
- `security-checklist.md.tmpl` — security
- `testing-patterns.md.tmpl` — testing patterns

每个文件顶部新增：
```
> 本清单与 /cso（或对应技能）配合使用；分层加载时属于 L2 温知识，按需通过 /recall --refs 加载
```

验证：init 后目标项目含 4 文件；英文术语保留（grep "LCP"、"TTFB"、"INP" 等）。

### 3. 更新 upgrade 策略

`src/agent_harness/upgrade.py` — FILE_CATEGORIES 新增：
```python
".agent-harness/references/*": "three_way",
```
默认三方合并，允许用户做类型专属定制。

### 4. 扩展 `/recall` 支持 `--refs`

`src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`

参数表新增：
- `--refs`：在 `.agent-harness/references/*.md` 中检索
- `--all`：也扩展到 references/

使用示例新增 `/recall 可访问性 --refs`。

### 5. 扩展 `memory.py` 和 `memory-index.md` 的参考资料段

`src/agent_harness/memory.py`：
- 在 `_render_index()` 增加 `references` 段；传参给函数
- 在 `rebuild_index()` 扫描 `.agent-harness/references/*.md`，若目录存在则提取文件名和 H1 标题

`src/agent_harness/templates/common/.agent-harness/memory-index.md.tmpl`：
- 新增 `## 参考资料（.agent-harness/references/）` 段，列出 4 个 checklist 的说明

### 6. task-lifecycle.md.tmpl 新增 Context Hierarchy 章节

加在 `# 任务生命周期` 和 `## 收到新任务时（最高优先级）` 之间，新增 `## 上下文分层原则`（约 30 行）：
- 为什么分层加载（context 是质量最大杠杆）
- 5 级层级（rules > specs > source > errors > history）
- 对应项目文件的 L0/L1/L2/L3 映射
- Rules Files 高杠杆定位

保持原表格不变。

### 7. 类型规则引用 references

- `src/agent_harness/templates/backend-service/.claude/rules/backend-service.md.tmpl` — 追加一行提示 security + performance checklist
- `src/agent_harness/templates/web-app/.claude/rules/web-app.md.tmpl` — 追加 a11y + performance checklist 引用

验证：grep references-checklist 出现。

### 8. 更新决策树引用

`src/agent_harness/templates/superpowers/.claude/commands/use-superpowers.md.tmpl`：
- 决策树新增 `/source-verify` 触发条件（写框架代码、跨迁移前）
- 命令表新增 `/source-verify`

`src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md.tmpl`（若存在）：
- 类似更新

`src/agent_harness/templates/superpowers/.claude/commands/evolve.md.tmpl`：
- 对比表更新（增量吸收记录）

### 9. check_repo.py 加守卫

`scripts/check_repo.py`：
- REQUIRED_FILES 增加 5 文件（source-verify + 4 references）
- 如有技能计数自动校验，更新为 31（29 + /recall + /source-verify — 但 /recall 已算在 30 中）— 需确认

### 10. 测试（≥ 8 新增）

- `tests/test_references.py`（新建）— 4 个测试
- `tests/test_superpowers.py` 追加 — /source-verify 测试 × 3
- `tests/test_memory.py` 追加 — references 索引测试 × 2
- `tests/test_cli.py` 或 `test_superpowers.py` 追加 — /recall --refs 测试 × 1

### 11. 文档同步

- `docs/product.md` — 技能数 30 → 31（若 /recall 已算）或 29 → 31；引用 references 机制
- `docs/architecture.md` — 模板树新增 references/；测试数 192 → ≥ 202
- `docs/runbook.md` — 分层记忆章节补 L2 温知识 = references
- `AGENTS.md` — 快速地图加 references/ 说明
- `CHANGELOG.md` — Unreleased 段新增条目
- `.agent-harness/lessons.md` — 本次教训

### 12. dogfood 同步

`make dogfood` — 同步本仓库 .claude/ 产物，以及本仓库的 `.agent-harness/references/` 首次落地

### 13. 归档

- task-log.md 写入
- current-task.md 清空
- memory-index.md 重建（含本次任务）
- GitHub Issue #16 关闭

## 回滚锚点

- 任意步骤失败 → `git reset --hard <上一 commit>`
- 全量回滚 → `git reset --hard 9959249`

## 预计产出

- 新建文件：~9（source-verify.md.tmpl、4 references tmpl、test_references.py、spec、plan）
- 修改文件：~15
- 测试：192 → ≥ 202
- commit 数：~13
