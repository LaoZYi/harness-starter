# Context-Mode 方法论吸收 — Plan

对应 spec：`2026-04-14-context-mode-spec.md`

## Step 1 — 新增 context-budget 规则

**文件**：`src/agent_harness/templates/common/.claude/rules/context-budget.md.tmpl`
**内容**：Think in Code 范式 + 工具输出预算双约束（2k tokens 阈值 + pipe 处理例子）
**验证**：`ls` 确认存在
**提交**：`feat(rules): add context-budget.md (Think in Code + output budget) from context-mode [plan step 1]`

## Step 2 — memory.py 新增 tokenize + bm25 + search_lessons

**文件**：`src/agent_harness/memory.py`
**新增函数**：
- `_tokenize(text: str) -> list[str]`：re-based，英文 `\w+` + 中文字符独立 token，lowercase
- `_segment_document(text: str) -> list[tuple[str, str]]`：按 `## ` 标题切段，返回 `[(title, body)]`
- `bm25_search(query: str, docs: list[tuple[str, str]], top: int, k1: float, b: float) -> list[tuple[float, str, str]]`：Okapi BM25，返回 `[(score, title, first_lines)]` 降序排序
- `search_lessons(target: Path, query: str, scope: str, top: int) -> list[tuple[float, str, str]]`：组合加载 lessons/task-log 段落 + 调用 bm25

**验证**：`.venv/bin/python -c "from agent_harness.memory import bm25_search; print(bm25_search('test', [('a','hello world'), ('b','test document')], 5, 1.5, 0.75))"`
**提交**：`feat(memory): add pure-stdlib BM25 search helpers [plan step 2]`

## Step 3 — memory CLI 新增 search 子命令

**文件**：`src/agent_harness/memory.py` 的 `main()`
**新增**：`memory search <query> [--target .] [--scope all|lessons|history] [--top 5]`
**输出格式**：
```
[memory] 搜索 "<query>" (scope=all, top=5)
  1. [0.85] ## 2026-04-13 [架构设计] ...
     (首 2 行正文)
  2. [0.64] ## 2026-04-12 [流程] ...
     (首 2 行正文)
  ...
```

**验证**：`.agent-harness/bin/memory search "记忆"` 返回 Top-5 相关段落
**提交**：`feat(memory): add 'search' subcommand with BM25 ranking [plan step 3]`

## Step 4 — 单元测试

**文件**：`tests/test_memory_search.py`
**覆盖**：
- tokenize：中英混合、全空格、emoji、标点
- _segment_document：多段落 + 无段落 + 单段落
- bm25_search：完全匹配 score > 部分匹配；Top-K 截断；空查询；无匹配
- CLI E2E：用 tmp 目录的 lessons.md 跑 `memory search`

**验证**：`.venv/bin/python -m unittest tests.test_memory_search`
**提交**：`test(memory): cover BM25 tokenize/score/CLI [plan step 4]`

## Step 5 — recall 模板升级 + workflow 清单

**文件**：
- `src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`：新增"二级兜底"段，说明 memory-index 未命中 → `memory search` BM25 兜底
- `src/agent_harness/templates/superpowers/.claude/rules/superpowers-workflow.md.tmpl`：新规则说明

**验证**：`grep "BM25\|memory search" src/agent_harness/templates/common/.claude/commands/recall.md.tmpl`
**提交**：`feat(skills): upgrade /recall with BM25 fallback; document context-budget [plan step 5]`

## Step 6 — lfg 阶段 0.2 兜底链路

**文件**：`src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` 阶段 0.2
**改动**：在"按需检索 L2/L3"的第 7 条加"memory-index 未命中时运行 `memory search <关键词>` BM25 兜底"

**验证**：`grep "BM25" src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`
**提交**：`feat(lfg): wire memory search fallback at stage 0.2 [plan step 6]`

## Step 7 — dogfood + docs + CHANGELOG

**改动**：
- `make dogfood` → 同步 `.agent-harness/bin/_runtime/memory.py`
- `docs/product.md` 新增第 20 条功能描述
- `docs/usage-guide.md` 更新 `/recall` 说明
- `CHANGELOG.md` 顶部加 Unreleased 条目

**验证**：`make ci` 全绿
**提交**：`docs: sync context-mode absorption (Issue #29) [plan step 7]`

## 依赖与顺序

严格顺序 1 → 7。step 2 的函数是 step 3 CLI 的基础；step 4 测试依赖 step 2 + 3；step 5/6 引用 step 3 的 CLI 命令名。

## 风险

- BM25 中文分词粗糙（按字符 1-gram）在常见场景够用，但长查询精度一般 → MVP 可接受；真需要 jieba 再迭代
- `_runtime/memory.py` 是 dogfood 产物，改完 src 版要同步跑 `make dogfood`（教训 #2026-04-14 dogfood force-add 适用此处，虽然 _runtime/ 未必 gitignore）
