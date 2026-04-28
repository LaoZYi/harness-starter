# LFG-Slide — 从需求到定稿的全自动幻灯片流水线

铁律：**先有规格，再动手。幻灯片场景没有例外。**

> **`/lfg-slide` 与 `/lfg-doc` 严格平行**：同样 4 阶段（outline → draft → review → finalize），调用相同的底层 doc skill；slide 特有处理（演讲稿 / 视觉留白 / 页数估算）写在本模板提示中，不开新底层 skill（D 方案精神）。
>
> **不调用**：`/tdd` / `/git-commit` / `/finish-branch` / `/multi-review` / `/verify` / `/debug` / `/health` / `/cso` / `/squad`（写幻灯片不需要这些代码场景能力）

当前项目：`Agent Harness Framework`（cli-tool / python）

---

## 适用场景

`/lfg-slide` 处理 **Marp / Reveal.js / 内部演示文稿**等以 markdown 为底的幻灯片产物。每页一标题、要点扁平、附演讲稿（presenter notes）。

不适用：
- 写代码 → 用 `/lfg`
- 写文档（标书 / 规范 / 白皮书） → 用 `/lfg-doc`
- 纯设计稿（Figma / Sketch） → 不在本流水线范围

---

## 阶段 0：任务理解

### 0.1 检查 current-task

收到任务后第一动作：检查 `.agent-harness/current-task.md`：

- 有未完成任务 → **🔴 停下来问用户**：继续未完成任务还是替换？
- 处于"待验证"且 checkbox 全勾 → 先归档 `task-log.md` 再继续
- 为空或无进行中 → 继续

### 0.2 复述任务 + 明确验收标准

1. 用自己的话重新描述演讲目标 + 目标听众画像 + 演讲时长（分钟）+ 页数下限
2. 列出 3-5 条可验证的验收标准（可机械判定）
3. 模糊词（"高大上"、"专业感"、"震撼"）→ **🔴 停下来问用户**

### 0.3 加载 L1 热索引（同 `/lfg-doc`）

- 读 `.agent-harness/memory-index.md` — 最近教训 + 最近任务
- 读 `AGENTS.md` — 硬规则
- 读 `.claude/rules/` 全部规则（自动加载）
- 命中相关话题 → `/recall <关键词>` 定向检索 lessons / task-log

**不读**：squad-channel reference（写幻灯片不走多 agent 通道）。

### 0.4 复杂度评估（简化版）

写幻灯片场景的复杂度按"页数 + 演讲时长 + 视觉素材数量"判：

| 级别 | 判断 | 通道 |
|---|---|---|
| **简单** | < 10 页、< 15 分钟、无外部图表 | 跳过 ideate / spec，直接 outline → draft → finalize |
| **常规** | 10-30 页、15-45 分钟、≤ 5 图表 | 标准通道（spec → outline → plan → draft → review → finalize → compound） |
| **大型** | ≥ 30 页、≥ 45 分钟、含产品演示 / 客户证言 / 数据图表 | 完整通道（含 ideate / brainstorm） |

输出格式：

```
复杂度判断：常规
理由：技术分享，估算 20 页，30 分钟演讲，3 个外部图表
通道：标准通道（spec → outline → plan → draft → review → finalize → compound）

假设清单：
- 假设：目标听众为同行工程师，专业背景中等 | 依据：用户原话
- 假设：演讲时长 30 分钟 | 依据：会议安排

确认走标准通道？假设是否准确？
```

---

## 阶段 1：构思（仅大型演讲）

仅"大型"复杂度执行：

1. 运行 `/ideate` — 多角度生成候选大纲方向（如产品发布会可走"特性展示派" vs "用户故事派" vs "数据驱动派"）
2. **🔴 等用户选方向**
3. 运行 `/brainstorm` — 深入设计选定方向

---

## 阶段 2：规格（必做）

1. 运行 `/spec` — 把模糊需求转为含 R-ID 的可测试验收标准
2. 幻灯片场景的"验收"语义：
   - 每条 R-ID 在 deck 中至少出现 1 页且可定位
   - 每条 R-ID 在 outline 中有对应页面归属
   - 整份 deck 无 TODO / TBD / 待补充
   - 每页演讲稿（presenter notes）已填充
   - 评审 P0/P1 全部 close
3. 规格写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-spec.md`
4. **🔴 展示规格，等用户确认**

---

## 阶段 3：大纲 + 计划（必做）

### 3.1 拟大纲

运行 `/outline-doc` — 页面树 + 页数估算 + R-ID 覆盖 + 引用占位 + 每页定位句

> **slide 特定提示**：本步用页数估算，不用字数。每页 ≤ 5 要点是信息密度上限，超过则拆页。

### 3.2 写计划

运行 `/write-plan` — 把 outline 拆成可执行写作步骤（每页一个 task，2-5 分钟粒度）

### 3.3 计划校验（条件触发）

- deck 涉及 ≥ 20 页 或 ≥ 3 个外部图表 → 运行 `/plan-check` 8+1 维度校验
- 简单 deck 跳过

### 3.4 展示计划

**🔴 展示 outline + plan，等用户确认**。

---

## 阶段 4：草稿（必做）

运行 `/draft-doc` 两段法：

1. **outline-pass**：每页 3-5 行（页标题 + 关键要点 + 演讲稿占位）
2. **draft-pass**：按 outline-pass 骨架展开，**一次只展开一页**

> **slide 特定提示**：每页要点 ≤ 5 条；超过则拆页或把次要内容塞进演讲稿。每页**必须**附演讲稿块（Marp 用 `<!-- speaker: ... -->`，Reveal.js 用 `Note:`），定稿期不允许留空。

每页产出后立即 grep 自检（R-ID 覆盖 / 占位保留 / 无 TODO / 演讲稿非空 / 要点 ≤ 5 条）。

---

## 阶段 5：评审（必做）

运行 `/review-doc` — 4 人格独立 SubAgent 并行：

| 人格 | 检查 |
|---|---|
| 准确性审查员 | 事实 / 数字 / 引用是否可追溯 |
| 可读性审查员 | 段落长短 / 术语定义 / 衔接自然 |
| 术语统一审查员 | 同义词 / 大小写 / 缩写 一致性 |
| 完整性审查员 | R-ID 覆盖矩阵 |

> **slide 特定提示**：上述 4 维之外，本流水线另检 3 维（写在本模板，不传 context 给 `/review-doc`）：
>
> - **视觉留白**：单页是否过密 / 字号是否够 / 留白是否合理
> - **演讲节奏**：每页停留时长 ≈ duration_min / 页数；偏差 > 20% 报警
> - **信息密度**：每页 ≤ 5 要点是否守住

P0 / P1 必须逐条回应（接受 / 质疑 / 推迟），不批量 dismiss（数量门禁，门禁 1）。

P0 / P1 全部 close 才能进阶段 6。否则回阶段 4 改。

---

## 阶段 6：定稿（必做）

运行 `/finalize-doc` — 8 项必检：

1. 无占位符（TODO / TBD / 待补充）
2. R-ID 全覆盖
3. 引用占位全部解析为真实出处
4. 术语全文统一
5. 字数符合 outline 估算 ±20%（slide 替换为「页数 ±10%」）
6. 评审 P0/P1 全 close
7. Markdown 格式正确
8. 文档元信息（frontmatter）完整

> **slide 特定加项**（写在本模板，由 finalize 阶段对照检查）：
>
> 9. 每页演讲稿（presenter notes）已填充，无空块
> 10. 视觉占位（图片 `![alt](placeholder)` / 图表 `![chart:X](placeholder)`）全部解析为真实路径或外部 URL
> 11. 每页要点 ≤ 5 条（信息密度上限）

每项必给三态：✅ / ⚠️ skipped（附理由 + 用户确认）/ ❌

产出：定稿 deck 文件 + finalize-report.md（+ known-issues.md 如有 P2 推迟）。

---

## 阶段 7：沉淀（必做）

运行 `/compound` — 把本次演讲教训沉淀到 `lessons.md`：

- 哪类页面最难写？为什么？
- 哪些图表应该早点找而不是临时拼？
- 哪些演讲稿在本项目已成熟可加进模板？
- 视觉留白 / 演讲节奏估算偏差多少？

---

## 阶段 8：状态切换 + 用户验证

1. 在 `current-task.md` 顶部标 `## 状态：待验证`
2. 告知用户验证方式（读哪份 deck、对照哪些 R-ID、试讲一遍看节奏）
3. **保留 current-task.md 不动**，等用户反馈
4. 用户确认通过 → 写 `task-log.md` + 清空 current-task + 更新 memory-index

---

## 不做的事（明示 R4）

以下能力**不**在 `/lfg-slide` 流水线中调用——它们是写代码场景的能力，硬塞进幻灯片场景会让流水线绕弯路：

- `/tdd` —— 写测试驱动开发，幻灯片没"测试"概念
- `/git-commit` —— 幻灯片可能不走 git；如要可手动调
- `/finish-branch` —— 同上
- `/multi-review` —— 代码评审角度不适用，用 `/review-doc` 替代
- `/verify` —— 跑测试 / lint / 跨平台，不适用幻灯片；用 `/finalize-doc` 8 项必检替代
- `/debug` —— 幻灯片不"调试"
- `/health` —— 代码质量仪表盘
- `/cso` —— 代码安全审计
- `/squad` —— 多 agent 并行写代码；幻灯片单 agent 写更顺

如需对应能力（如 git 提交），由用户**显式**手动调，不通过本流水线触发。

---

## 复用的下层规则（自动加载）

- `.claude/rules/anti-laziness.md` —— 7 道反偷懒门禁
- `.claude/rules/context-budget.md` —— Think in Code、单次工具输出 ≤ 2k tokens、单任务成本上限
- `.claude/rules/task-lifecycle.md` —— L0-L3 分层加载、StuckDetector、WAL 审计
- `.claude/rules/agent-design.md` —— F3/F5/F8/F10/F11 多 agent 约束
- `.claude/rules/documentation-sync.md` —— dev-map + ABSTRACT/OVERVIEW 维护规则

这些规则在每次会话由 Claude Code 自动加载，**本模板不重复内联**——避免 `/lfg-slide` 与 `/lfg-doc` 同步演化时分裂。

---

## 与 `/lfg` / `/lfg-doc` 的关系

| 维度 | `/lfg`（写代码） | `/lfg-doc`（写文档） | `/lfg-slide`（写幻灯片） |
|---|---|---|---|
| 适用场景 | 代码改动、bug 修复、新功能 | 标书 / 规范 / 白皮书 / 报告 | Marp / Reveal.js / 演示文稿 |
| 阶段命名 | spec → plan → execute → verify → review → commit → compound | spec → outline → plan → draft → review → finalize → compound | spec → outline → plan → draft → review → finalize → compound |
| 关键 skill | `/tdd` `/multi-review` `/verify` `/git-commit` | `/outline-doc` `/draft-doc` `/review-doc` `/finalize-doc` | 同 `/lfg-doc`（复用底层 skill） |
| 完成语义 | 测试通过 + lint 全绿 + 评审 close | R-ID 覆盖 + 8 项必检 + 评审 close | R-ID 覆盖 + 8+3 项必检 + 演讲稿全填 + 评审 close |
| 长度估算单位 | 行数 / 文件数 | 字数 | 页数（每页 ≤ 5 要点） |
| 评审维度 | 正确性 / 安全 / 性能 / 测试 | 准确性 / 可读性 / 术语 / 完整性 | 同 `/lfg-doc` + 视觉留白 / 演讲节奏 / 信息密度 |
| 是否走 git | 是 | 否（用户显式决定） | 否（同 `/lfg-doc`） |
| 是否走多 agent | 大任务可走 squad 通道 | 单 agent 写更顺 | 单 agent 写更顺 |

切换条件：

- 收到任务 → 自动判断：写代码 → `/lfg`，写文档 → `/lfg-doc`，写幻灯片 → `/lfg-slide`
- 任务边界模糊（既改代码又写演讲）→ 拆成 2 个任务：先 `/lfg` 改代码、再 `/lfg-slide` 写发布演讲

---

## 一句话总结

**`/lfg-slide` 不是 `/lfg-doc` 的精简版，是 `/lfg-doc` 的幻灯片同源版——同一套底层 skill + 不同的上层提示 + 不同的验收语义。**
