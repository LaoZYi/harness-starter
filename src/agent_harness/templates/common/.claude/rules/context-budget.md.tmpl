---
description: 控制工具输出和上下文窗口流入的双约束（Think in Code + 输出预算）
---

# Context Budget 规则

本规则适用所有任务。目标：防止工具调用的原始输出塞爆上下文窗口，把 AI 从"数据处理者"逼回"代码生成者"。

灵感自 [mksglu/context-mode](https://github.com/mksglu/context-mode)（HN #1，7k+ ⭐）的三层解决方案：Context Saving + Session Continuity + **Think in Code**。本项目不引入其 MCP server 本体（Node/SQLite 依赖违反零依赖原则），只吸收方法论为规则。

## 与 Claude Code 内部压缩机制的关系

Claude Code 内部有 **5 级渐进式压缩流水线**（源自 [how-claude-code-works](https://github.com/Windy3f3f3f3f/how-claude-code-works) 的源码分析，以官方实现为准）：

| 级别 | 名称 | 机制 | 成本 |
|------|------|------|------|
| L1 | Tool Result Budget | 超过 ~50K 字符的工具结果写磁盘，上下文只保留预览 | 零（纯本地） |
| L2 | History Snip | 剪裁历史消息冗余部分释放 Token | 零 |
| L3 | Microcompact | 清理旧工具结果（5 分钟 TTL 冷缓存路径 / 缓存编辑路径） | 极低 |
| L4 | Context Collapse | 投影式只读折叠视图，不修改原始消息 | 低 |
| L5 | Autocompact | fork 子 Agent 生成摘要，**不可逆** | 高（API 调用） |

**本规则与 L1 的关系**：规则 2 的"单次工具输出 ≤ 2k tokens"是**在 L1 之前的前置防线**——在 AI 决定调用工具时就控制输出规模，而不是等 Claude Code 内部的 L1 被动截断。提前控制比被动截断保留更多语义。

**`/compact` 时机与 L3 的关系**：L3 Microcompact 在提示词缓存过期（5 分钟 TTL）后会清理旧工具结果。这意味着长时间暂停后恢复工作时，上下文已被部分清理——此时 `/compact` 的边际收益降低，不必重复操作。

## 规则 1：Think in Code — 搜索/统计/过滤用脚本，不拉原始数据

### Tool Decision Matrix（数据类型 → 处理方式分类学）

> 来源：mksglu/context-mode BENCHMARK.md（21 真实场景验证 96% 上下文节省）。原话：「`'5 code blocks, 3 sections about cleanup'` → useless for coding；返回完整 `useEffect(() => {...}, [deps])` block → actually useful」——汇总和精确召回各有不可替代场景，错配比不处理更糟。

按数据类型选处理方式，**不要全部一刀切「写脚本汇总」**：

| 数据类型 | 处理方式 | 工具示例 | 为什么 |
|---|---|---|---|
| 文档 / API refs / 大型规则文件 | **精确召回**（返回完整片段） | `grep -A 20 "## 章节" rules.md` / `memory search "<关键词>"` BM25 | 需要完整代码块 / API 签名，汇总成 "5 sections about X" 对编码没用 |
| 工具签名 / 函数定义 | **精确召回** | `grep -A 5 "^def funcname" src/` | 需要精确参数、返回类型 |
| Skills / lessons / references 内容 | **精确召回** | `/recall <关键词>` 或 `memory search` | 完整教训内容，不是「这个 lesson 大概讲什么」 |
| 日志 / 测试输出 / 编译错误 | **脚本汇总** | `grep ERROR \| awk '{print $3}' \| sort \| uniq -c \| head` | 需要聚合统计，不是逐行原文 |
| CSV / 分析数据 | **脚本汇总** | `awk -F, '{sum+=$3} END{print sum}'` | 需要计算后的指标 |
| 构建输出 | **脚本汇总** | `grep -c "error\|warning" build.log` | 需要错误数量，不是完整输出 |
| Browser snapshot / DOM tree | **脚本汇总** | 写脚本提取关键结构 | 需要页面结构摘要 |

**分类口诀**：
- 「需要原文 / 完整代码 / 精确签名」 → 精确召回
- 「需要计数 / 统计 / 聚合」 → 脚本汇总

### 反模式速查表

以下场景**禁止**把原始数据读进上下文窗口，必须先写脚本，只返回处理后的结果：

| 场景 | ❌ 反模式 | ✅ 正确做法 |
|---|---|---|
| 统计文件数量 | 读 20 个文件全文 | `find . -name "*.py" \| wc -l` |
| 查找某模式出现次数 | 读多个文件后人工数 | `grep -rc "pattern" src/ \| awk -F: '{s+=$2} END{print s}'` |
| 过滤大 JSON 取字段 | 读完整 JSON 再人工筛 | `jq '.items[] \| select(.status=="done") \| .id'` |
| 对比两版文件差异 | 读两个文件全文再对比 | `diff -u a.md b.md \| head -50` |
| 统计某函数被调用次数 | 读调用方源码人工数 | `grep -rn "foo(" src/ \| wc -l` |
| 找文档里某 API 用法 | 让脚本汇总「有 N 个示例」 | **精确召回**：`grep -A 20 "useEffect" docs.md` 拿完整代码块 |

判断口诀：**如果结果能在 1 行 shell 管道或 5 行 Python 脚本内得出，就一定不要读全量数据进上下文**。

## 规则 2：单次工具输出大小预算

`Bash` / `Read` / `Grep` 输出超过 **2000 tokens**（约 ~8 KB 中英混合）时，必须先做预处理再返回：

| 工具 | 预算超阈值时的处理 |
|---|---|
| `Bash`（`cat`、`curl`、`docker logs` 等） | 改成 `\| head -N`、`\| grep PATTERN`、`\| jq '.关键字段'`、`\| tail -N`，按需截取。**长错误日志 / 测试输出 / 编译错误**用 Smart Truncation 头尾保留（见下文） |
| `Read`（大文件） | 传 `offset` + `limit` 参数只读目标行段，不默认全文 |
| `Grep` | 用 `head_limit` 参数 + `output_mode=count` 或 `files_with_matches` 而非 `content` |
| 自己写脚本 | 脚本末尾 `print()` 只输出汇总结论，不输出明细 |

**例外**：结果本身就 < 2k tokens（如 `git log --oneline -10`）不受此限。

### Smart Truncation：头尾保留（防丢尾部错误信息）

> 来源：mksglu/context-mode BENCHMARK.md Part 3。原话：「Blindly keeps first N bytes / Error messages at end: **LOST**」 vs 「Keeps head + tail / Error messages: **PRESERVED**」。

长错误日志 / 编译报错 / 测试输出的**关键信息几乎都在尾部**（`FATAL` / `exit 1` / `Stack trace`）。**单方向截断（仅 `| head`）等于扔掉诊断**——AI 看到的是「初始化正常」假象，无法定位真实错误。

**反模式**：

```bash
make test 2>&1 | head -30      # ❌ 尾部 FAILED 行被丢，AI 以为通过
docker logs <id> | head -50    # ❌ 尾部崩溃 stack trace 丢失
```

**正确做法**——用 shell 一行同时保留首尾：

```bash
# 长输出截断模板（单文件）
{ head -30 big_output.log; echo "... [truncated middle] ..."; tail -30 big_output.log; }

# 管道场景（用 awk 或临时文件）
make test 2>&1 | tee /tmp/out.log
{ head -30 /tmp/out.log; echo "... [truncated] ..."; tail -30 /tmp/out.log; }

# 或纯管道（仅 GNU sed/awk 兼容时）
make test 2>&1 | awk 'NR<=30 {print} NR==31 {print "... [truncated middle] ..."} END {}'
```

**典型场景**：

```
line 0-11: 初始化 / config 加载
... [truncated middle] ...
line 92: connection timeout
line 95: Stack trace: Error at connect()
line 96: exit code: 1
```

LLM 同时看到**初始上下文**和**真实错误**，不会被「初始化正常」误导。

**判定**：

| 输出类型 | 截断策略 |
|---|---|
| 错误日志 / 测试输出 / 编译报错 / docker logs | **必须**头尾保留（关键信息在尾部） |
| 文档 / 长文本 / 配置文件 | 用 `Read offset+limit` 只读目标行段，不需要头尾保留 |
| 列表型输出（`ls -la` / `git log --oneline`） | `head -N` 即可（首尾顺序无差） |

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

## 规则 4：单任务成本上限（Task-Level Budget）

> 来源：阿里云 Qoder CLI 团队《Harness Engineering 实战》——程序化调用 LLM 时必须设 `--max-turns` 和 `timeout`，否则异常情况下会「烧尽 credits」。

Context Budget 管**单次调用**的上下文流入；本规则管**单任务总消耗**的上限。两者互补。

### 优化目标:tokens-per-task,不是 tokens-per-request

> 来源:muratcankoylan/Agent-Skills-for-Context-Engineering(Issue #50 吸收)。

度量目标是**完成整个任务总 token**,不是每次请求节省的 token。压缩 / 截断太狠 → 丢失文件路径 / 错误信息 / 决策理由 → 后续要 re-explore / re-read / re-derive,反而比一开始保留花更多 token。

**信号:re-fetching frequency**——AI 反复要求重读已处理的文件 = 上一轮压缩太狠。比"每次请求节省 0.5%"重要 40 倍的指标。

**应用**:做 `/compact` / 缩减历史 / 删除 reference 时,先问"删了这条以后会不会引发 re-explore"。会的话 → 不删。

### 软限（到达后警示，不强制中断）

| 指标 | 单任务软限 | 越限后的动作 |
|------|------------|--------------|
| 对话轮次（user ↔ assistant） | ~50 轮 | 主动建议用户：是否 `/compact` 或拆任务 |
| 工具调用总数 | ~100 次 | 检查是否在盲目试错（可能触发 StuckDetector） |
| 读文件累计次数 | ~30 次 | 检查是否重复读同一文件、是否缺 Think in Code |
| `/compact` 次数 | ~2 次 | 两次压缩后仍未完成 → 任务颗粒度过大，建议拆分 |

**软限不是硬停**。这些数字是经验值，**达到后应主动汇报并询问用户**，不擅自继续消耗。

### 硬限（到达后强制停下，由编排层保障）

针对**程序化调用 Agent CLI** 的场景（如 `/squad` worker、`/dispatch-agents` 子代理、CI 流水线）：

| 硬限类型 | 推荐值 | 实现方式 |
|---------|-------|---------|
| 最大对话轮次 | 80 | CLI 层 `--max-turns 80`（如可用）或编排层计数 |
| 最大运行时长 | 1800 秒（30 分钟） | `timeout 1800 claude -p "..."` |
| 单任务 token 预算 | 项目级设置 | 无上限时通过对话轮次间接控制 |

**编排层必带硬限**：`/squad` 的 worker、`/dispatch-agents` 的子代理，prompt 里**必须**声明任务边界 + 超时后的后备动作（写 mailbox / diary / 报告失败）。

### 与现有机制的协作

| 机制 | 负责的维度 |
|------|-----------|
| 规则 1-3（本文前）| 单次调用 context 输入控制 |
| 规则 4（本段）| 单任务总消耗控制 |
| `StuckDetector`（task-lifecycle）| 同错误 3 次停下（错误循环） |
| `/compact` 介入点（`/lfg` 阶段 2/5/9）| 阶段切换处主动压缩 |
| L0 静默恢复（task-lifecycle）| 瞬时失败的重试额度（1 次） |

### 反合理化

| 借口 | 驳斥 |
|------|------|
| 「调用 Claude 本来就不花我钱」 | 哪怕对个人用量，每次误推都是时间浪费。复杂任务盲试 1 小时 ≠ 一次正确推理 10 分钟 |
| 「任务快完成了，再跑几轮就好」 | 经验值：超出软限仍未完成时，**继续推进**的成功率显著下降。更好的策略是 `/compact` 或拆任务 |
| 「在编排场景硬限太死板」 | 硬限是**兜底**，正常情况下远达不到。达到硬限说明任务超范围，应回头调规格 |
| 「压缩越狠越省 token」 | tokens-per-task 视角下错的:压狠了丢路径/错误信息/决策理由 → AI 后续 re-explore/re-read,总开销反而上涨 40 倍。看 re-fetching frequency,不看 per-request 节省 |

## 诊断侧:Context Degradation 5 类模式

> 与本规则 1-4 的边界:本规则是**预防侧**(怎么不让 context 失控);本节是**诊断侧**(失控了怎么识别)。

AI 在长会话出现以下症状时,运行 `/recall --refs context-degradation` 加载 5 类 attention 诊断模式自检:

- **明明上下文里有信息,AI 回答却忽略** → Lost-in-Middle(关键信息被埋中间)
- **AI 反复引用同一错误结论,纠正不动** → Context Poisoning(错误自我增强)
- **加载越多 reference,响应反而越泛** → Context Distraction(无关挤占注意力)
- **多任务串味,跨任务复用约束/工具** → Context Confusion(任务边界模糊)
- **多源矛盾,AI 给折中建议** → Context Clash(无优先级)

详细诊断 / 缓解策略 / 检测信号见 `.agent-harness/references/context-degradation-patterns.md`。

## 违反检测

- 工具调用结果 > 2k tokens 且未预处理 → 是违反规则 2 的信号
- 为同一问题反复读 3+ 个文件 → 是违反规则 1 的信号
- 单任务跑到 50+ 轮未完成 → 是违反规则 4 的信号，应立即停下评估
- `/lfg` 阶段 0.2 "加载历史知识" 和 4.1 "实施"会定期提醒检查预算
