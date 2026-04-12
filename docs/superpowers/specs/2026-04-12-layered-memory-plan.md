# 实施计划：分层记忆加载

> 对应 Spec：`docs/superpowers/specs/2026-04-12-layered-memory-spec.md`
> 对应 ADR：`docs/decisions/0001-layered-memory-loading.md`
> 分支：`feat/layered-memory` | 基线 commit：`49d48244`

## 执行顺序与依赖

每步完成后打 tag `lfg/step-N`，创建原子 commit。

### 步骤 1：新建 memory-index.md 模板

**文件**：`src/agent_harness/templates/common/.agent-harness/memory-index.md.tmpl`（新建）

**内容**：初始骨架（标题 + 说明 + 三段占位 + 使用提示）

**验证**：
- 文件存在
- `grep -l "memory-index" src/agent_harness/templates/common/.agent-harness/memory-index.md.tmpl`
- 骨架包含三段标题："最近教训"、"最近任务"、"主题索引"

---

### 步骤 2：upgrade 策略登记 memory-index.md

**文件**：`src/agent_harness/upgrade.py`

**改动**：在 `FILE_POLICIES` 字典中加入 `".agent-harness/memory-index.md": "skip"`（紧挨现有 `.agent-harness/lessons.md` 行）

**验证**：
- grep 确认行已加
- `make test` — 升级测试不出错

---

### 步骤 3：initializer 生成 memory-index.md（验证 common 模板自动覆盖）

**文件**：可能无需代码改动——`materialize_templates()` 遍历 common 模板树，新 `.tmpl` 文件会自动被渲染。但需确认。

**验证**：
- 写一个临时脚本：`harness init /tmp/memtest --non-interactive`，检查 `/tmp/memtest/.agent-harness/memory-index.md` 存在
- 如果不存在 → 排查 templating.py 的发现逻辑

---

### 步骤 4：新建 /recall 技能模板

**文件**：`src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`（新建）

**内容**：
- description frontmatter
- 用途段（按关键词搜索 lessons/task-log）
- 参数说明（`<关键词>` 或 `--history <关键词>`）
- 执行步骤（grep 文件 → 定位二级标题 → 返回相关节）
- 使用示例

**验证**：
- 文件存在
- 含 description frontmatter
- 含 "lessons.md" 和 "task-log.md" 字样

---

### 步骤 5：修改 task-lifecycle 规则

**文件**：`src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`

**改动**：
- 第 0 步读取表：删除 `lessons.md` 和 `task-log.md（最近 5 条）` 两行
- 新增一行 `.agent-harness/memory-index.md | 热知识精华索引（默认读这个）`
- 表格下方新增"深入搜索"说明段，指向 `/recall` 技能

**验证**：
- grep 确认 `memory-index` 在规则中出现
- grep 确认"默认读这个"或类似措辞存在
- 原始 lessons.md / task-log.md 的强制读取被移除

---

### 步骤 6：修改 /compound 技能维护 index

**文件**：`src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl`

**改动**：在"写入 lessons.md"步骤之后新增一段"同步更新 memory-index.md"：
- 在 index 的"最近教训"段顶部插一行新教训
- 若该段超过 10 条，删除最老的一条
- 类似逻辑用于任务归档（最近任务段，超过 5 条裁剪）

**验证**：
- grep 确认模板中含 "memory-index.md" 和 "最近 10 条"（或等价表述）
- 技能文档自洽（AI 能读懂如何维护）

---

### 步骤 7：新建 memory.py 模块 + rebuild 函数

**文件**：`src/agent_harness/memory.py`（新建，目标 < 120 行）

**导出**：
- `rebuild_index(target_path: Path, *, force: bool = False) -> RebuildResult`
  - 从 `target_path/.agent-harness/lessons.md` 扫 `##` 标题，取末尾 10 条
  - 从 `target_path/.agent-harness/task-log.md` 扫 `##` 标题，取末尾 5 条
  - 写入 `target_path/.agent-harness/memory-index.md`
  - 若文件已存在且非 `--force` → 返回拒绝结果
- `RebuildResult` dataclass: `{status, lessons_count, tasks_count, message}`

**约束**：
- 复用 `_shared.py` 的 `require_harness()` 做路径守卫
- 不调用 templating（不渲染模板，直接写明文）
- 处理 lessons/task-log 缺失的情况（两者都缺 → 写空骨架）

**验证**：
- `python -c "from agent_harness.memory import rebuild_index; print('ok')"`
- 模块行数检查（< 280 行硬上限）

---

### 步骤 8：CLI 注册 `harness memory rebuild`

**文件**：`src/agent_harness/cli.py`

**改动**：
- 新增 `memory` 子命令（argparse）
- 子命令下 `rebuild` 动作：`harness memory rebuild <target> [--force]`
- handler 调用 `memory.rebuild_index()`，输出结果到 rich

**验证**：
- `harness memory rebuild --help` 返回正常
- cli.py 行数未超 280 行

---

### 步骤 9：编写单元测试

**文件**：`tests/test_memory.py`（新建）

**测试用例**：
1. `test_rebuild_creates_index_when_missing` — lessons/task-log 存在，index 不存在 → 创建
2. `test_rebuild_refuses_without_force` — index 已存在 → 返回 refused 状态，不覆盖
3. `test_rebuild_force_overwrites` — `--force` → 覆盖
4. `test_rebuild_limits_to_10_lessons` — lessons 含 15 条 → 只保留最新 10 条
5. `test_rebuild_limits_to_5_tasks` — task-log 含 7 条 → 只保留最新 5 条
6. `test_rebuild_handles_empty_sources` — lessons / task-log 为空或缺失 → 生成空骨架
7. `test_rebuild_skips_malformed_headings` — 跳过非 `##` 行（健壮性）

**文件**：`tests/test_initializer.py` 或 `test_cli_integration.py` 追加 2 个
8. `test_init_generates_memory_index` — init 后 memory-index.md 存在
9. `test_upgrade_skips_existing_memory_index` — 用户编辑过的 index 升级后不被覆盖

**文件**：`tests/test_superpowers.py` 或新增 `test_recall_skill.py`
10. `test_recall_skill_template_exists`
11. `test_task_lifecycle_references_memory_index`
12. `test_compound_maintains_memory_index`

**验证**：`make test` 新增 ≥ 8 测试全绿；总数 176 → ≥ 184

---

### 步骤 10：check_repo.py 加守卫

**文件**：`scripts/check_repo.py`

**改动**：新增两项检查
- `memory-index.md.tmpl` 存在于 common 模板
- `recall.md.tmpl` 存在于 common commands 模板

**验证**：`make check` 通过

---

### 步骤 11：文档同步 — product.md

**文件**：`docs/product.md`

**改动**：
- "框架提供什么" 追加条目 10："分层记忆加载（L0-L3），`memory-index.md` 为热索引，`/recall` 按需检索"
- CLI 命令清单表追加 `harness memory rebuild <target>` 一行
- 技能数：29 → 30（因为新增 /recall）；确认新数字

**验证**：grep "30" 在 product.md 中

---

### 步骤 12：文档同步 — architecture.md

**文件**：`docs/architecture.md`

**改动**：
- 模块职责"辅助层"新增 `memory.py` 一行
- "推荐扩展方式"保留即可
- 测试数：176 → ≥ 184，更新数字

**验证**：grep 新数字和 `memory.py` 均命中

---

### 步骤 13：文档同步 — AGENTS.md / runbook.md / CHANGELOG

**文件**：
- `AGENTS.md` — 快速地图加 `memory.py` 和 `harness memory rebuild` 命令
- `docs/runbook.md` — 新增 "分层记忆" 小节，含使用示例和故障排查
- `CHANGELOG.md` — 新增条目：feat(memory): 引入分层记忆加载（L0-L3）

**验证**：grep 各文件均命中新内容

---

### 步骤 14：dogfood 同步

**命令**：`make dogfood`（将框架自身作为目标项目，重新生成 `.agent-harness/` 和 `.claude/`）

**验证**：
- 本仓库 `.agent-harness/memory-index.md` 被创建
- 本仓库 `.claude/commands/recall.md` 被创建
- 本仓库 `.claude/rules/task-lifecycle.md` 已是新版
- `make ci` 全绿

---

### 步骤 15：bootstrap 本仓库的 memory-index.md（验证 rebuild）

**命令**：`harness memory rebuild . --force`

**验证**：
- `.agent-harness/memory-index.md` 顶部含最近 10 条 lessons（含刚写的分层加载教训）
- 含最近 5 条 task-log

（此步验证 rebuild CLI 能工作在真实项目上）

---

### 步骤 16：写入本次教训到 lessons.md

**文件**：`.agent-harness/lessons.md`

**追加内容**：`## 2026-04-12 分层记忆：索引+按需展开优于全量读取`（含根因、规则，≥ 3 行）

（然后重新运行 rebuild 让 index 包含这条）

**验证**：`grep "分层记忆" .agent-harness/lessons.md`

---

## 边界与错误处理清单

| 场景 | 处理 |
|------|-----|
| lessons.md 不存在 | rebuild 生成空"最近教训"段，不报错 |
| lessons.md 为空文件 | 同上 |
| lessons.md 格式异常（无 `##` 标题） | 跳过该节，继续 task-log |
| target_path 非项目目录 | `require_harness()` 抛错，CLI 给友好提示 |
| memory-index.md 已存在 | 默认 refuse（status + 信息），`--force` 才覆盖 |
| lessons 含中文标题 | 保留原样（测试要覆盖） |
| 并发写入 | 本次不考虑（脚手架工具是单次调用） |

## 历史教训引用

- `lessons.md` "命令重命名后模板要全量扫描" — 本次新增 `memory-index`、`/recall`、`memory.py` 后，grep 全仓库确认所有引用一致
- `lessons.md` "新增技能时文档散布计数需全量扫描" — 29 → 30 要 grep 全仓库

## 回滚锚点

- 任意步骤失败 → `git reset --hard lfg/step-<N-1>` 回到上一步
- 全量回滚 → `git reset --hard 49d48244`（基线）

## 预计产出

- 新文件：5（memory-index.md.tmpl, recall.md.tmpl, memory.py, test_memory.py, ADR）
- 修改文件：~12（upgrade, compound, task-lifecycle, cli, check_repo, product, architecture, AGENTS, runbook, CHANGELOG, lessons, test_initializer）
- 新增测试：≥ 8
- commit 数：~16（每步一个）
