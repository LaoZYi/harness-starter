# LFG-Doc — 从需求到定稿的全自动文档流水线

铁律：**先有规格，再动手。文档场景没有例外。**

> **`/lfg-doc` 是 `/lfg` 的文档场景同源版本**：与 `/lfg`（写代码）共享分层记忆 / 反偷懒门禁 / agent 设计 / context budget 等下层规则（由 `.claude/rules/` 自动加载，不需要内联），但**阶段顺序、调用 skill、验收语义全部按文档场景调整**。
>
> **不调用**：`/tdd` / `/git-commit` / `/finish-branch` / `/multi-review` / `/verify` / `/debug` / `/health` / `/cso` / `/squad`（写文档不需要这些代码场景能力）

当前项目：`Agent Harness Framework`（cli-tool / python）

---

## 阶段 0：任务理解

### 0.1 检查 current-task

收到任务后第一动作：检查 `.agent-harness/current-task.md`：

- 有未完成任务 → **🔴 停下来问用户**：继续未完成任务还是替换？
- 处于"待验证"且 checkbox 全勾 → 先归档 `task-log.md` 再继续
- 为空或无进行中 → 继续

### 0.2 复述任务 + 明确验收标准

1. 用自己的话重新描述文档目标 + 目标读者画像 + 字数下限
2. 列出 3-5 条可验证的验收标准（可机械判定）
3. 模糊词（"高质量"、"专业"、"详细"）→ **🔴 停下来问用户**

### 0.3 加载 L1 热索引（同 `/lfg`）

- 读 `.agent-harness/memory-index.md` — 最近教训 + 最近任务
- 读 `AGENTS.md` — 硬规则
- 读 `.claude/rules/` 全部规则（自动加载）
- 命中相关话题 → `/recall <关键词>` 定向检索 lessons / task-log

**不读**：squad-channel reference（写文档不走多 agent 通道）。

### 0.4 复杂度评估（简化版）

写文档场景的复杂度按"字数 + 章节数 + 引用源数量"判：

| 级别 | 判断 | 通道 |
|---|---|---|
| **简单** | < 500 字、< 3 章、无外部引用 | 跳过 ideate / spec，直接 outline → draft → finalize |
| **常规** | 500-3000 字、3-10 章、≤ 5 引用 | 标准通道（spec → outline → plan → draft → review → finalize → compound） |
| **大型** | ≥ 3000 字、> 10 章、多源对比 / 客户证言 / 数据图表 | 完整通道（含 ideate / brainstorm） |

输出格式：

```
复杂度判断：常规
理由：标书项目，估算 5000 字，8 章，3 个外部引用
通道：标准通道（spec → outline → plan → draft → review → finalize → compound）

假设清单：
- 假设：目标读者为评委，专业背景中等 | 依据：用户原话
- 假设：字数下限 5000 字 | 依据：标书招标文件要求

确认走标准通道？假设是否准确？
```

---

## 阶段 1：构思（仅大型文档）

仅"大型"复杂度执行：

1. `/ideate` — 多角度生成候选大纲方向（如标书可走"技术领先派" vs "性价比派" vs "服务保障派"）
2. **🔴 等用户选方向**
3. `/brainstorm` — 深入设计选定方向

---

## 阶段 2：规格（必做）

1. `/spec` — 把模糊需求转为含 R-ID 的可测试验收标准
2. 文档场景的"验收"语义：
   - 每条 R-ID 在文档中至少出现 1 次且可定位
   - 每条 R-ID 在 outline 中有对应章节归属
   - 整份文档无 TODO / TBD / 待补充
   - 评审 P0/P1 全部 close
3. 规格写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-spec.md`
4. **🔴 展示规格，等用户确认**

---

## 阶段 3：大纲 + 计划（必做）

### 3.1 拟大纲

`/outline-doc` — 章节树 + 字数估算 + R-ID 覆盖 + 引用占位 + 章节定位句

### 3.2 写计划

`/write-plan` — 把 outline 拆成可执行写作步骤（每章一个 task，2-5 分钟粒度——本步指"开始写"，不是"写完"）

### 3.3 计划校验（条件触发）

- 文档涉及 ≥ 5 章 或 ≥ 3 个引用源 → `/plan-check` 8+1 维度校验
- 简单文档跳过

### 3.4 展示计划

**🔴 展示 outline + plan，等用户确认**。

---

## 阶段 4：草稿（必做）

`/draft-doc` 两段法：

1. **outline-pass**：每章 3-5 行（主张 + 关键论点 + 依据占位）
2. **draft-pass**：按 outline-pass 骨架展开，**一次只展开一章**

每章产出后立即 grep 自检（R-ID 覆盖 / 占位保留 / 无 TODO / 术语定义）。

**不**调 `/tdd` —— 写文档不是写测试，逻辑不一样。

---

## 阶段 5：评审（必做）

`/review-doc` — 4 人格独立 SubAgent 并行：

| 人格 | 检查 |
|---|---|
| 准确性审查员 | 事实 / 数字 / 引用是否可追溯 |
| 可读性审查员 | 段落长短 / 术语定义 / 衔接自然 |
| 术语统一审查员 | 同义词 / 大小写 / 缩写 一致性 |
| 完整性审查员 | R-ID 覆盖矩阵 |

P0 / P1 必须逐条回应（接受 / 质疑 / 推迟），不批量 dismiss（数量门禁，门禁 1）。

P0 / P1 全部 close 才能进阶段 6。否则回阶段 4 改。

**不**调 `/multi-review` —— 评审角度不同，硬塞会让审查员迷路。

---

## 阶段 6：定稿（必做）

`/finalize-doc` — 8 项必检：

1. 无占位符（TODO / TBD / 待补充）
2. R-ID 全覆盖
3. 引用占位全部解析为真实出处
4. 术语全文统一
5. 字数符合 outline 估算 ±20%
6. 评审 P0/P1 全 close
7. Markdown 格式正确
8. 文档元信息（frontmatter）完整

每项必给三态：✅ / ⚠️ skipped（附理由 + 用户确认）/ ❌

产出：定稿文件 + finalize-report.md（+ known-issues.md 如有 P2 推迟）。

**不**调 `/verify` —— 文档版"verify"就是上述 8 项内嵌检查。
**不**调 `/git-commit` / `/finish-branch` —— 由用户决定是否进 git 流程，本 skill 不自动触发。

---

## 阶段 7：沉淀（必做）

`/compound` — 把本次写作教训沉淀到 `lessons.md`：

- 哪类章节最难写？为什么？
- 哪些引用源应该早点找而不是临时拼？
- 哪些术语在本项目已统一可加进术语表？

---

## 阶段 8：状态切换 + 用户验证

1. 在 `current-task.md` 顶部标 `## 状态：待验证`
2. 告知用户验证方式（读哪份文档、对照哪些 R-ID、跑哪些命令）
3. **保留 current-task.md 不动**，等用户反馈
4. 用户确认通过 → 写 `task-log.md` + 清空 current-task + 更新 memory-index

---

## 不做的事（明示 R4）

以下能力**不**在 `/lfg-doc` 流水线中调用——它们是写代码场景的能力，硬塞进文档场景会让流水线绕弯路：

- `/tdd` —— 写测试驱动开发，文档没"测试"概念
- `/git-commit` —— 文档可能不走 git；如要可手动调
- `/finish-branch` —— 同上
- `/multi-review` —— 代码评审角度不适用，用 `/review-doc` 替代
- `/verify` —— 跑测试 / lint / 跨平台，不适用文档；用 `/finalize-doc` 8 项必检替代
- `/debug` —— 文档不"调试"
- `/health` —— 代码质量仪表盘
- `/cso` —— 代码安全审计
- `/squad` —— 多 agent 并行写代码；文档单 agent 写更顺

如需对应能力（如 git 提交），由用户**显式**手动调，不通过本流水线触发。

---

## 复用的下层规则（自动加载）

- `.claude/rules/anti-laziness.md` —— 7 道反偷懒门禁（数量 / 上下文隔离 / 反合理化 / 下游消费者 / 不确定性 / 基线 / 压力测试）
- `.claude/rules/context-budget.md` —— Think in Code、单次工具输出 ≤ 2k tokens、单任务成本上限
- `.claude/rules/task-lifecycle.md` —— L0-L3 分层加载、StuckDetector、WAL 审计
- `.claude/rules/agent-design.md` —— F3/F5/F8/F10/F11 多 agent 约束（如需用 `/dispatch-agents` 派子代理收集资料时适用）
- `.claude/rules/documentation-sync.md` —— dev-map + ABSTRACT/OVERVIEW 维护规则

这些规则在每次会话由 Claude Code 自动加载，**本模板不重复内联**——避免 `/lfg-doc` 与 `/lfg` 同步演化时分裂。

---

## 与 `/lfg` 的关系

| 维度 | `/lfg`（写代码） | `/lfg-doc`（写文档） |
|---|---|---|
| 适用场景 | 代码改动、bug 修复、新功能开发 | 标书 / 规范 / 白皮书 / 报告 / 技术方案 |
| 阶段命名 | spec → plan → execute → verify → review → commit → compound | spec → outline → plan → draft → review → finalize → compound |
| 关键 skill | `/tdd` `/multi-review` `/verify` `/git-commit` | `/outline-doc` `/draft-doc` `/review-doc` `/finalize-doc` |
| 完成语义 | 测试通过 + lint 全绿 + 评审 close | R-ID 覆盖 + 8 项必检 + 评审 close |
| 是否走 git | 是（commit + finish-branch） | 否（用户显式决定） |
| 是否走多 agent | 大任务可走 squad 通道 | 单 agent 写更顺，不走 squad |

切换条件：

- 收到任务 → 自动判断：写代码 → `/lfg`，写文档 → `/lfg-doc`
- 任务边界模糊（既改代码又改文档）→ 拆成 2 个任务：先 `/lfg` 改代码、再 `/lfg-doc` 写对应文档

---

## 一句话总结

**`/lfg-doc` 不是 `/lfg` 的精简版，是 `/lfg` 的文档同源版——同一套下层规则 + 不同的上层流水线 + 不同的验收语义。**
