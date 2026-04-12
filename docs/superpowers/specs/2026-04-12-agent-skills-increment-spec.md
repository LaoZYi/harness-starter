# Spec：吸收 addyosmani/agent-skills 增量更新

> Issue：GitHub #16 | 来源：addyosmani/agent-skills（已在 Issue #6 吸收 /spec）
> 日期：2026-04-12 | 分支：feat/agent-skills-increment | 基线：9959249

## 目标

本次吸收 3 个新价值点：
1. `source-driven-development` → 新技能 `/source-verify`
2. `references/` 四个 checklist → `.agent-harness/references/` L2 温知识
3. `context-engineering` 方法论 → `task-lifecycle.md` 理论章节

## 非目标

- 3 个 subagent（code-reviewer / security-auditor / test-engineer）— 已被 /multi-review、/cso、/tdd 覆盖
- code-simplification / incremental-implementation / deprecation-and-migration — 延后
- session-start hook 增强 — 延后

## 1. `/source-verify` 新技能

### 文件
- `src/agent_harness/templates/common/.claude/commands/source-verify.md.tmpl`

### 核心流程
```
DETECT（识别 stack+版本）→ FETCH（抓官方文档）→ IMPLEMENT（按文档实现）→ CITE（代码/PR 标注来源）
```

### 关键内容
- 依赖文件映射表（package.json → JS/TS、pyproject.toml → Python、go.mod → Go 等）
- Source 权威层级：官方文档 > 官方博客 > web 标准 > 浏览器兼容性
- 明确拒绝：Stack Overflow、博客教程、AI 生成内容作为主源
- 反合理化表（6 条）— 符合 Issue #6 吸收的表格模板
- 集成点：LFG Phase 4 实施、/tdd 写实现前、跨语言/跨框架迁移时

### 决策树更新
- `use-superpowers.md.tmpl` 加入 `/source-verify`
- workflow rules 加入 `/source-verify`

## 2. `.agent-harness/references/` 四个 checklist

### 文件（模板）
- `src/agent_harness/templates/common/.agent-harness/references/accessibility-checklist.md.tmpl`
- `src/agent_harness/templates/common/.agent-harness/references/performance-checklist.md.tmpl`
- `src/agent_harness/templates/common/.agent-harness/references/security-checklist.md.tmpl`
- `src/agent_harness/templates/common/.agent-harness/references/testing-patterns.md.tmpl`

### 内容处理
- **保留原文 checklist 项**（LCP/TTFB/CLS 等术语保留英文，符合行业共识）
- **序言和章节标题汉化**
- **增加一行"何时使用本 checklist"** 指引与本框架的技能关联：
  - security → 与 /cso 配合
  - performance → web-app 类型使用
  - accessibility → web-app / mobile-app 类型使用
  - testing-patterns → 与 /tdd / testing rule 配合

### 上层联动
- `memory-index.md.tmpl` 新增"参考资料"段：
  ```
  ## 参考资料（.agent-harness/references/）
  - accessibility-checklist.md — a11y（Core Web Vitals、ARIA、键盘）
  - performance-checklist.md — perf（Core Web Vitals、Frontend/Backend）
  - security-checklist.md — 输入校验、认证、依赖
  - testing-patterns.md — 测试组织、mock、E2E
  ```

- `/recall` 扩展：
  - 新增 `--refs <关键词>` flag 查 references/
  - `--all` 也扩展到 references/
  - 默认行为不变（lessons + task-log）

- `upgrade.py`：references/*.md 列为 `three_way` 默认（用户可能做类型专属定制）

### 类型规则引用
- `backend-service.md.tmpl` 追加："性能或安全问题时查阅 `.agent-harness/references/security-checklist.md` 和 `performance-checklist.md`"
- `web-app.md.tmpl` 追加："新增 UI 前查阅 `accessibility-checklist.md`；部署前查阅 `performance-checklist.md`"

## 3. `context-engineering` → `task-lifecycle.md` 理论章节

### 文件
- `src/agent_harness/templates/common/.claude/rules/task-lifecycle.md.tmpl`

### 加在哪里
在文件顶部"收到新任务时"章节**之前**，新增 `## 上下文分层原则`（约 30 行）：

- 为什么分层加载：上下文是质量最大杠杆
- Context Hierarchy（5 级）：rules > specs > source > errors > history
- 对应到本项目的实际文件：
  - L0 = AGENTS.md + CLAUDE.md + .claude/rules/
  - L1 = current-task.md + memory-index.md
  - L2 = lessons.md + references/
  - L3 = task-log.md
- Rules Files 的高杠杆定位（为什么 AGENTS.md 硬规则 > .claude/rules/ 长指导 > memory-index 临时信号）

保留原有"第 0 步：读取项目知识"表格不变。

## 4. memory.py 扩展（轻量）

`rebuild_index()` 增加对 references/ 的索引：新增"## 参考资料"段，扫描 `.agent-harness/references/*.md` 列出标题。

如果 references/ 不存在（老项目）→ 跳过该段。

## 测试（新增 ≥ 8）

### `tests/test_references.py`（新建）
1. `test_four_checklists_generated_on_init` — init 后 4 个 md 都在
2. `test_checklists_have_zh_headings` — 序言汉化
3. `test_checklists_preserve_en_terms` — LCP/TTFB 等术语保留
4. `test_upgrade_preserves_user_edits_in_references` — three_way 保留用户修改

### `tests/test_superpowers.py` 追加
5. `test_source_verify_skill_present`
6. `test_source_verify_has_anti_rationalization_table`
7. `test_use_superpowers_references_source_verify`

### `tests/test_memory.py` 追加
8. `test_rebuild_includes_references_section_when_dir_exists`
9. `test_rebuild_skips_references_section_when_absent`

### `tests/test_cli.py` or new
10. `test_recall_skill_documents_refs_flag`

目标：192 → ≥ 202。

## 验收标准（映射到 Issue）

| # | 验收 | 验证 |
|---|------|------|
| 1 | /source-verify 技能存在 | grep + 占位符检查 |
| 2 | references/ 4 文件生成 | init 测试 |
| 3 | task-lifecycle 含 Context Hierarchy | grep 规则模板 |
| 4 | /recall --refs 可用 | recall.md.tmpl 更新 + 文档 |
| 5 | 类型规则引用 references | grep backend-service/web-app 规则 |
| 6 | 测试 ≥ 8 | make test 计数 |
| 7 | make ci 全绿 | CI 输出 |
| 8 | 文档同步 | product/architecture/CHANGELOG/runbook/AGENTS/lessons |
| 9 | dogfood 同步 | .claude/ 产物刷新 |
| 10 | Issue 关闭 | Phase 10.6 |

## 边界与风险

| 风险 | 缓解 |
|------|-----|
| references 模板过长（669 行总量） | 保留原始结构，不删减条目 |
| 中英混排可读性 | 序言和章节标题汉化，checklist 项保持英文术语 |
| /recall 逻辑增加后出错 | 新增 `--refs` flag 不改变默认行为，向后兼容 |
| task-lifecycle 头部膨胀 | 新增章节约 30 行，AGENTS.md 硬规则 120 行限制不受影响（lifecycle 不受该限制） |
| 类型规则引用 references 成为死链 | 测试覆盖引用文件存在；以条件措辞"如需"避免强制依赖 |

## 范围边界

**做**：上文列出的 3 大点 + 测试 + 文档。

**不做**：
- 3 个 subagent
- 未点名的 agent-skills 内容（code-simplification 等）
- session-start hook 增强
- 非 references 目录类的大改
