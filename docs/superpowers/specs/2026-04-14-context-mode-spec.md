# Context-Mode 方法论吸收 — Spec

**Issue**：#29（GitHub）/ #13（GitLab）
**来源**：`/evolve` 提案吸收 mksglu/context-mode（7152⭐，HN #1）
**日期**：2026-04-14

## 目标

把 context-mode 的 3 层方法论内化为本框架规则 + 工具增强，**不引入 MCP server 本体**（Node/SQLite 违反零依赖原则）。

## 吸收三项

| 项 | 落地 | 理由 |
|---|---|---|
| Think in Code 范式 | `common/rules/context-budget.md` | 搜索/统计/过滤类任务先写脚本，不拉原始数据进上下文 |
| 单次工具输出大小预算 | 同上规则 | `Bash`/`Read` 输出 > 2k tokens 必须先 pipe 处理（head/grep/jq/awk） |
| BM25 兜底检索 | `memory search` CLI + `/recall` 技能升级 | 手工索引未命中时相关性检索 lessons/task-log |

## 需求

- **R1**：新规则 `context-budget.md`（适用所有项目类型，common 层）
- **R2**：`memory search <query> [--lessons | --history | --all] [--top N]` CLI，纯 stdlib 实现
- **R3**：BM25 评分：Okapi BM25（k1=1.5, b=0.75），中英混合分词
- **R4**：`/recall` 技能：手工索引未命中 → 提示串 `memory search` 兜底
- **R5**：`lfg.md.tmpl` 阶段 0.2 历史加载，说明 memory-index 未命中时的二级兜底链路
- **R6**：新增 `tests/test_memory_search.py`（tokenize + BM25 评分 + CLI E2E）
- **R7**：`superpowers-workflow.md` 清单新增说明
- **R8**：`docs/product.md` + `CHANGELOG.md` 同步

## 验收

- `.venv/bin/python -m agent_harness.memory search "<词>"` 返回 Top-K 段落 + score
- `make ci` 通过；`harness skills lint` OK；`make dogfood` 无漂移
- `/recall` 模板明确两级兜底顺序：memory-index → BM25 search

## 不做

- 不引入 MCP server 本体
- 不引入任何外部 Python 依赖（jieba / sklearn 等都禁止）
- 不改现有 L0-L3 分层架构
- 不持久化 BM25 索引（每次查询现场计算，lessons <1MB 性能够用）
