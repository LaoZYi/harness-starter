---
description: 控制工具输出和上下文窗口流入的双约束（Think in Code + 输出预算）
---

# Context Budget 规则

本规则适用所有任务。目标：防止工具调用的原始输出塞爆上下文窗口，把 AI 从"数据处理者"逼回"代码生成者"。

灵感自 [mksglu/context-mode](https://github.com/mksglu/context-mode)（HN #1，7k+ ⭐）的三层解决方案：Context Saving + Session Continuity + **Think in Code**。本项目不引入其 MCP server 本体（Node/SQLite 依赖违反零依赖原则），只吸收方法论为规则。

## 规则 1：Think in Code — 搜索/统计/过滤用脚本，不拉原始数据

以下场景**禁止**把原始数据读进上下文窗口，必须先写脚本，只返回处理后的结果：

| 场景 | ❌ 反模式 | ✅ 正确做法 |
|---|---|---|
| 统计文件数量 | 读 20 个文件全文 | `find . -name "*.py" \| wc -l` |
| 查找某模式出现次数 | 读多个文件后人工数 | `grep -rc "pattern" src/ \| awk -F: '{s+=$2} END{print s}'` |
| 过滤大 JSON 取字段 | 读完整 JSON 再人工筛 | `jq '.items[] \| select(.status=="done") \| .id'` |
| 对比两版文件差异 | 读两个文件全文再对比 | `diff -u a.md b.md \| head -50` |
| 统计某函数被调用次数 | 读调用方源码人工数 | `grep -rn "foo(" src/ \| wc -l` |

判断口诀：**如果结果能在 1 行 shell 管道或 5 行 Python 脚本内得出，就一定不要读全量数据进上下文**。

## 规则 2：单次工具输出大小预算

`Bash` / `Read` / `Grep` 输出超过 **2000 tokens**（约 ~8 KB 中英混合）时，必须先做预处理再返回：

| 工具 | 预算超阈值时的处理 |
|---|---|
| `Bash`（`cat`、`curl`、`docker logs` 等） | 改成 `\| head -N`、`\| grep PATTERN`、`\| jq '.关键字段'`、`\| tail -N`，按需截取 |
| `Read`（大文件） | 传 `offset` + `limit` 参数只读目标行段，不默认全文 |
| `Grep` | 用 `head_limit` 参数 + `output_mode=count` 或 `files_with_matches` 而非 `content` |
| 自己写脚本 | 脚本末尾 `print()` 只输出汇总结论，不输出明细 |

**例外**：结果本身就 < 2k tokens（如 `git log --oneline -10`）不受此限。

## 规则 3：会话连续性靠 memory-index + BM25 兜底，不靠回灌

`/compact` 前追加关键决策到 `.agent-harness/current-task.md` 或 `lessons.md`，`memory-index.md` 做热索引，`memory search <关键词>` 做 BM25 兜底检索。**不要**把大段历史 dump 回当前窗口作为"记忆复原"——那是 anti-pattern。

## 触发示例

```
❌ 需求：告诉我 tests/ 下哪些测试类有 4 个以上方法
   错误做法：读 tests/ 下每个文件全文（~30 文件 × 2-5k tokens = 60k tokens）
   正确做法：
     grep -l "def test_" tests/*.py | while read f; do
       count=$(grep -c "def test_" "$f")
       [ "$count" -ge 4 ] && echo "$f: $count"
     done

❌ 需求：分析日志里的 ERROR 类型分布
   错误做法：cat logs/app.log（可能 10+ MB）
   正确做法：grep ERROR logs/app.log | awk '{print $3}' | sort | uniq -c | sort -rn | head -20
```

## 违反检测

- 工具调用结果 > 2k tokens 且未预处理 → 是违反规则 2 的信号
- 为同一问题反复读 3+ 个文件 → 是违反规则 1 的信号
- `/lfg` 阶段 0.2 "加载历史知识" 和 4.1 "实施"会定期提醒检查预算
