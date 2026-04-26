# Context Degradation 5 类诊断模式

> L2 温知识层 — 与 `.claude/rules/context-budget.md` 配合使用。`context-budget` 是**预防侧**(Think in Code / 单次输出预算 / 任务总消耗等),本文件是**诊断侧**:AI 在长会话表现退化时按 5 类 pattern 自检。
>
> **来源**:[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering),已被北大 GAI 实验室 2026 年论文《Meta Context Engineering via Agentic Skill Evolution》引为基础工作(arxiv:2601.21557)。
>
> **使用方式**:`/recall --refs context-degradation` 加载;或 AI 出现"明明上下文里有但回答忽略"、"被某个错误结论带偏"、"多任务混淆"等症状时主动加载。

## 与其他 reference 的边界

| Reference | 视角 |
|---|---|
| **本文件** | Context window 内 attention 机制问题 — lost-in-middle / poisoning / clash 等 |
| `ai-coding-pitfalls.md` | AI 编码**行为**问题 — 幻觉 / 改不全 / 模式匹配 等 |
| `claude-code-internals.md` | Claude Code 5 级压缩**底层机制** — L1-L5 截断 / 7 个 continue site |

三者正交互补,可同时加载。

---

## Pattern 1:Lost-in-Middle(中间丢失)

### 症状

- 信息明明在上下文里,模型回答时忽略
- 长文档 / 长对话历史的中间段内容被"跳过"
- 列表中第 5-10 项响应质量明显低于首尾

### 根因

U 形注意力曲线(Liu et al. 2023):开头 / 结尾位置 attention 可靠,中间位置 recall 准确率下降 **10-40%**。这不是模型 bug,而是 attention 机制本身的特性——首 token (BOS) 作为 "attention sink" 吸收过多注意力预算,中间 token 注意力稀缺。

上下文超过 4K tokens 时此效应显著。

### 缓解策略

- **关键信息放首尾**:critical assumptions / decisions / constraints 永远放在 prompt 开头或结尾,不放中间
- **Summary 在前,细节在后**:长文档 prepend "key points" + append "conclusions",中间放 raw content
- **结构化锚点**:加 `## ` 标题、显式 "重要:" / "约束:" 标记,作为 attention anchor
- **拆分超长上下文**:> 4K tokens 时拆为多次工具调用,每次只加载相关段

### 检测信号

```
症状:用户问"X 模块在 src/foo/bar.py:42",AI 回答"找不到该位置"
但 grep 一查 src/foo/bar.py:42 确实存在,且这条信息曾在上下文中出现过
```

→ 上一轮把 src 路径放在中间长 list 里被忽略 → 下次把路径单独段放尾部

---

## Pattern 2:Context Poisoning(上下文中毒)

### 症状

- 一个错误结论 / 幻觉数据进入上下文后,后续所有决策围绕它展开,越走越偏
- AI 反复引用同一条错误信息("如前所述...")
- 修正后仍然回退到错误版本

### 根因

幻觉 / 工具错误 / 错误检索结果一旦进入 context,通过自我引用**复合放大**(self-reference compounding)。被 poisoned 的 goals / assumptions / facts 让每个下游决策强化错误前提。

### 缓解策略

- **截断到 poisoning 之前**:发现错误源头后,**不能**靠"再对它说一次正确答案"修正——必须截断当前 session 上下文,从已验证状态重启
- **声明可信度边界**:已验证的事实 vs 待核实假设要在上下文里**显式分开**(对应 anti-laziness.md 门禁 5 不确定性输出)
- **追踪 claim provenance**:重要结论标注来源("根据 file.py:42")—— 推理时能识别哪些是脚注引用 vs 凭记忆
- **circuit breaker**:连续 3 次返回引用同一可疑结论 → 强制 `/compact` 或开新会话

### 检测信号

```
AI 重复使用同一个错误数据(比如"PyYAML 5.1 默认拒绝任意对象") 5 次
即使你纠正了"实际是 5.4 版本默认拒绝",下次仍回到 5.1
```

→ poisoning 已扎根,纠正在已 poisoned context 里无效 → 必须开新会话/截断

---

## Pattern 3:Context Distraction(注意力分散)

### 症状

- 加入一份"可能相关"的文档后,任务完成质量下降
- 多个候选 reference 同时加载,AI 回答含糊不切题
- 上下文越长,响应越泛

### 根因

无关信息会**强制竞争注意力预算**。模型不能"跳过"无关内容,必须给所有内容分配 attention,造成相关 / 无关之间互相挤占。**单一**无关文档即可显著降低相关任务表现。

### 缓解策略

- **激进过滤**:不要"以防万一"加载——能确认相关的才加载,模糊的留给工具调用按需取
- **Tool 而非预加载**:可能用到的资料放工具调用后取(/recall on-demand),不放 system prompt
- **/recall --refs 而非整段 cat**:用 `/recall` 的 grep + BM25 兜底取关键节,而不是 cat 整个 reference 进上下文
- **N=3 上限**:并行 /recall --refs 同时加载不超过 3 个 reference

### 检测信号

```
你刚加载 3 个 reference + 4 个 ADR,然后问"代码该怎么改",AI 给出泛泛的方案
```

→ distraction 已发生 → 关掉 2-3 个不直接相关的 reference 重问

---

## Pattern 4:Context Confusion(任务混淆)

### 症状

- 多任务上下文混合时,模型借用错误任务的约束
- 调用了**别**任务里才用的工具
- 返回值的 schema / 输出格式跨任务串味

### 根因

context 包含多个任务类型 / 切换目标时,模型无法清晰区分边界,会**跨任务复用**约束 / 工具 / 模式。例:你先做了"加 endpoint",再做"修 bug",AI 把 endpoint 的"必加分页参数"约束错误用到 bug 修复上。

### 缓解策略

- **显式任务分段**:明确说"任务 1 已完成,以下是任务 2,前一任务约束不再适用"
- **独立 context window**:重大任务切换时直接 /clear 或开新会话,不依赖语义切割
- **task scope 标记**:子任务在 prompt 里加 `[Task: <名>]` 前缀,LLM 显式识别边界
- **N+1 任务规则**:同一会话里超 1 个完成态任务 + 1 个进行中任务 = 必须 /compact 或 /clear

### 检测信号

```
你刚在前一个任务里说"用 React useState",
现在做后端任务,AI 在 Python 代码里写 "useState" 类似的 hooks
```

→ confusion 发生 → 立刻 /clear 或开新会话

---

## Pattern 5:Context Clash(矛盾冲突)

### 症状

- 多个正确但矛盾的源同时存在,AI 无法判断哪条适用
- 版本冲突("v1 文档说 X,v2 说 Y")
- 多源检索返回不一致结论

### 根因

多个**正确但矛盾**的源(版本冲突 / 视角冲突 / 多源 retrieval) 同时进入 context 时,模型无法判优——它会"调和"两者(产生错误折中)或随机选一。这跟 poisoning 不同:poisoning 是错的,clash 是都对但不能并存。

### 缓解策略

- **显式标矛盾**:把冲突源贴上"⚠️ 矛盾" 标签,提示模型"二选一,不要折中"
- **建立优先级**:声明 "rule A 优先 rule B" / "v2 优先 v1" / "本地配置优先全局"
- **过滤过时版本**:加载文档前先看创建日期,过时版本不进 context
- **应对历史 lessons 的 T3 冲突**:本项目 lessons.md 同领域"两条 confirmed lesson 互斥"按 `.claude/rules/knowledge-conflict-resolution.md` T3 处理(转 `when:` 条件分支),而非两条都进 context

### 检测信号

```
当前 context 同时有:
- "用 useEffect 不要在 render 里 setState"(React 17 经验)
- "用 useEffect 可在 render 里 dispatch"(React 19 + automatic batching)
AI 给出"折中"建议,既不正确也不实用
```

→ clash 发生 → 显式声明用哪个 React 版本,删除另一个 context 段

---

## 综合速查

| Pattern | 一句话识别 | 一句话修复 |
|---|---|---|
| Lost-in-Middle | 信息在中间被忽略 | 关键信息放首尾,加结构锚点 |
| Poisoning | 错误结论自我增强 | 截断/开新会话,标 claim provenance |
| Distraction | 无关文档拖累相关任务 | 激进过滤,工具按需取 |
| Confusion | 多任务串味 | 任务切换 /clear 或加 [Task:] 标记 |
| Clash | 多源矛盾,模型折中 | 显式标矛盾 + 建优先级 |

## 反合理化(扩展 anti-laziness 门禁 3)

| 借口 | 驳斥 |
|---|---|
| 「再加一份 reference,以防万一」 | distraction pattern——无关文档单一即可显著降低相关任务质量 |
| 「错误结论我已经纠正了,继续就行」 | poisoning 不是靠纠正能解的,必须截断或开新会话 |
| 「多个版本文档都贴上让 AI 自己选」 | clash pattern——AI 会折中或随机选,必须显式优先级 |
