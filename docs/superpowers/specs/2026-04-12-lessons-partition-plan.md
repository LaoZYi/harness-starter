# 实现计划：lessons.md 结构化分区（Issue #11）

> 来源：GitHub Issue #11 — 灵感来自 MemPalace Wing/Hall/Room，选最小实现

## 目标与范围

将 `.agent-harness/lessons.md` 从平铺列表升级为"顶部分类索引 + 条目标题嵌分类前缀"结构，同步更新 `/compound` 技能和模板，使后续新条目自动遵循新格式。不破坏 `memory.py` 的 rebuild 逻辑。

**不做**：
- 不拆分为多文件（最小实现原则）
- 不改 `memory.py`（新格式对其透明）
- 不给 /recall 加 `--category` 参数（grep 已够用）

## 历史教训引用

- **2026-04-12「脚手架项目吸收外部思想要选最小实现」**：MemPalace 的分层是运行时动态 rotate，我们是约束 AI 读什么。选最轻方案（单文件改标题格式）。
- **2026-04-09「命令重命名后模板文件也要全量扫描」**：更新 `/compound` 文案时，记得同步 dogfood 的 `.claude/commands/compound.md`。
- **2026-04-08「新增技能时文档散布计数需全量扫描」**：docs/product.md、CHANGELOG.md 都要同步。

## 分类定义（6 类）

从现有 10 条教训聚类得出：

| 分类 | 适用场景 | 现有样本数 |
|------|---------|-----------|
| `测试` | 测试策略、覆盖率、断言、测试环境 | 0 |
| `模板` | templates/ 渲染、占位符、模板变量、dogfood | 2 |
| `流程` | 工作流、任务生命周期、知识库维护 | 3 |
| `工具脚本` | scripts/、Makefile、CLI、check_repo | 2 |
| `架构设计` | 模块边界、设计权衡、技术选型 | 1 |
| `集成API` | 外部 API（gh/GitLab）、网络依赖 | 2 |

若将来出现不属于这 6 类的教训，`/compound` 会提示新增分类而非强塞进已有类。

## 新格式约定

### 条目 heading
```
## YYYY-MM-DD [分类] 一句话标题
```

### 顶部分类索引（位于 `# Lessons Learned` 开头段之后）
```markdown
## 按分类索引

> 快速定位某领域教训。新增条目后请同步此索引。

- **测试**: （暂无）
- **模板**: [#模板-占位符语法会被模板引擎吞掉](#2026-04-09-模板-模板中的文档占位符语法会被模板引擎吞掉), ...
- **流程**: ...
- ...
```

### GFM anchor 规则
- Markdown heading `## 2026-04-09 [模板] 模板中的文档占位符语法会被模板引擎吞掉` 的 anchor id 为 `#2026-04-09-模板-模板中的文档占位符语法会被模板引擎吞掉`
- GFM 自动把空格替换为 `-`，保留中文字符和方括号则去掉
- 验证方式：GitHub 渲染页面目录能跳转；本地用 grep heading 行与链接比对

## 执行步骤

### 步骤 1：写实现计划（本文件）
- 输出：`docs/superpowers/specs/2026-04-12-lessons-partition-plan.md`
- 验证：文件存在

### 步骤 2：更新 `compound.md.tmpl`（先模板后数据）
文件：`src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl`

改动点：
1. **第 4 步「写入知识库」** 的条目格式示例：
   - 从 `## [分类] 问题标题 (YYYY-MM-DD)` 改为 `## YYYY-MM-DD [分类] 问题标题`
   - 添加：「**分类前缀必须放在日期后**（memory-index 扫描依赖此顺序）」
2. **第 4 步「可用分类」** 表格替换为 6 类并说明可扩展：
   - 测试 / 模板 / 流程 / 工具脚本 / 架构设计 / 集成API
   - 备注：若不属于这 6 类，新增分类并同步更新本指令表格
3. **新增"第 4.5 步：更新顶部分类索引"**：
   - 给出具体插入规则（把新条目 anchor 加到对应分类那行）
   - 强调"条目标题 + 索引链接 + memory-index 三处一致"
4. 第 3 步「查重」grep 示例保持不变（分类前缀不影响搜索）

验证：
- `grep -c "^## YYYY-MM-DD \[分类\]" compound.md.tmpl` ≥ 1
- `grep "分类索引" compound.md.tmpl` 有命中

### 步骤 3：更新 `lessons.md.tmpl`
文件：`src/agent_harness/templates/common/.agent-harness/lessons.md.tmpl`

替换模板全文为：
```markdown
# Lessons Learned

从错误和返工中提炼的教训。每条教训对应一个曾经犯过的错，包含根因和防止再犯的规则。

agent 开始任务前应快速浏览本文件，避免重蹈覆辙。

## 按分类索引

> 新增条目时在对应分类追加 anchor 链接。若出现新分类，在此表新增一行并同步 `/compound` 指令。

- **测试**: （暂无）
- **模板**: （暂无）
- **流程**: （暂无）
- **工具脚本**: （暂无）
- **架构设计**: （暂无）
- **集成API**: （暂无）

## 条目格式

```
## YYYY-MM-DD [分类] 一句话标题

- 错误：发生了什么
- 根因：为什么会发生
- 规则：以后怎么避免
```

---

```

验证：`grep "按分类索引" lessons.md.tmpl` 命中

### 步骤 4：迁移现有 10 条教训到 `.agent-harness/lessons.md`
文件：`.agent-harness/lessons.md`

分类映射：
| # | 原标题 | 分类 |
|---|--------|------|
| 1 | dogfood 命令展平 | 工具脚本 |
| 2 | 进化去重必须覆盖已关闭 Issue | 流程 |
| 3 | GitLab Issue 搜索禁用 search 参数 | 集成API |
| 4 | 新增技能时文档散布计数需全量扫描 | 流程 |
| 5 | 新任务覆盖前必须先关闭旧任务 | 流程 |
| 6 | 重复工具函数提取后必须删除原始定义 | 工具脚本 |
| 7 | 模板中的文档占位符语法会被模板引擎吞掉 | 模板 |
| 8 | 命令重命名后模板文件也要全量扫描 | 模板 |
| 9 | 同一项目的增量吸收用 evolution-update 标签 | 流程 |
| 10 | 脚手架项目吸收外部思想要选最小实现 | 架构设计 |

改动：
- 将每条 heading 从 `## YYYY-MM-DD 标题` 改为 `## YYYY-MM-DD [分类] 标题`
- 顶部插入"按分类索引"区块，每类列出 anchor 链接
- 条目内容保持不变

验证：
- `grep -c "^## 2026" lessons.md` == 10
- `grep -c "^## 2026-.* \[" lessons.md` == 10（10 条都加了分类）
- 目测顶部索引 6 类各有对应数量：测试 0 / 模板 2 / 流程 4 / 工具脚本 2 / 架构设计 1 / 集成API 1

### 步骤 5：dogfood 同步 `.claude/commands/compound.md`
命令：`python scripts/dogfood.py`（或 `make dogfood`）

验证：
- `diff .claude/commands/compound.md src/agent_harness/templates/superpowers/.claude/commands/compound.md.tmpl` 仅差别为模板变量替换
- `make check`（含 check_repo.py）通过

### 步骤 6：重建 memory-index 验证兼容
命令：`harness memory rebuild . --force`

预期：
- `.agent-harness/memory-index.md` 中「最近教训」10 条都带 `[分类]` 前缀，格式如：
  ```
  - 2026-04-12 [架构设计] 脚手架项目吸收外部思想要选最小实现
  ```
- rebuild 退出码 0

验证：
- `harness memory rebuild . --force` 成功
- `grep "\[" .agent-harness/memory-index.md | wc -l` ≥ 10

### 步骤 7：新增测试用例
文件：`tests/test_memory_index.py`

新增测试 `test_category_prefix_preserved_in_index`：
- 构造含 `## 2026-04-12 [测试] xxx` 格式的 lessons.md 的临时项目
- 调用 `rebuild_index()`
- 断言生成的 memory-index.md 包含 `[测试] xxx` 字样

验证：
- `make test` 测试数 203 → 204，全过
- 新测试独立运行通过

### 步骤 8：更新 `docs/product.md`
文件：`docs/product.md`

在"框架提供什么"第 10 条「分层记忆加载」下补一句或新增第 12 条：

```
12. **分类索引**：`.agent-harness/lessons.md` 按 6 类（测试/模板/流程/工具脚本/架构设计/集成API）组织，顶部索引快速定位。新增条目自动归类，`/compound` 技能维护索引一致性。
```

验证：`grep "分类索引" docs/product.md` 命中

### 步骤 9：更新 `CHANGELOG.md`
在最新未发布段（或新增 Unreleased）添加：

```
### Changed
- lessons.md 改为"顶部分类索引 + 条目标题嵌分类前缀"结构，/compound 同步更新 (#11)
- 现有 10 条教训按 6 类迁移归档
```

验证：`grep "#11" CHANGELOG.md` 命中

### 步骤 10：`make ci` 全量验证
命令：`make ci`

预期：check + test 全过，测试数至少 204。

### 步骤 11：多视角快速评审
运行 `/multi-review`（启用正确性 + 测试完整性 2 个审查员）。

### 步骤 12：生成完成报告 + 验收逐条核验
按 LFG 阶段 7/10 要求输出完成报告，等用户确认。

## 边界情况与风险

| 风险 | 缓解 |
|------|------|
| 中文 anchor 在某些渲染器不可点 | GFM（GitHub/VS Code Preview）原生支持；本地 VS Code 已测。若发现不兼容再退化为纯文本分组 |
| 新条目作者忘打分类前缀 | `/compound` 指令第 4 步强制要求；未来可加 check_repo.py 校验规则 |
| 分类聚类随时间漂移 | 预留"可扩展"机制：`/compound` 指令明说允许新增分类 |
| memory.py 未来扩展可能假设旧格式 | 新增测试 `test_category_prefix_preserved_in_index` 锁死契约 |
| anchor 与 heading 不匹配（空格/大小写） | 步骤 4 完成后手动 grep 校验 heading 行与索引链接一一对应 |

## 完成标准（对齐 Acceptance）

- [ ] lessons.md 10 条全部带 `[分类]` 前缀；顶部索引 6 类完整
- [ ] compound.md.tmpl 和 lessons.md.tmpl 均已更新；dogfood 同步
- [ ] `harness memory rebuild . --force` 成功，memory-index 含分类前缀
- [ ] 测试数 ≥ 204，新增测试通过；make ci 全过
- [ ] docs/product.md 和 CHANGELOG.md 更新
