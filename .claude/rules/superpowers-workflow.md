# Superpowers 工作流

本项目启用了 superpowers 结构化开发工作流。处理开发任务时，优先按以下流程使用技能命令。

## 推荐工作流

1. **构思阶段** — 运行 `/ideate` 多角度生成方案，或 `/brainstorm` 结构化设计对话
2. **规格阶段** — 运行 `/spec` 定义需求规格和验收标准（需求模糊时必做）
3. **设计决策** — 运行 `/adr` 记录架构决策（涉及技术选型或架构模式时）
4. **计划阶段** — 运行 `/write-plan` 编写实现计划（2-5 分钟粒度的任务）；复杂任务紧接着运行 `/plan-check` 做 8 维度校验
5. **执行阶段** — 运行 `/execute-plan` 按计划逐步实施，或 `/tdd` 进行测试驱动开发
6. **验证阶段** — 运行 `/verify` 在告知用户"完成"之前做全面验证
7. **评审阶段** — 运行 `/multi-review` 多人格评审，或 `/request-review` 准备评审请求
8. **沉淀阶段** — 运行 `/compound` 提炼经验写入知识库

> 想全自动完成？运行 `/lfg` 一键串联上述全部阶段。

## 双轮框架：交付 vs 治理

本工作流的 32 个技能并行分布在两条互补链路上：

| 轮 | 职责 | 典型技能 |
|---|---|---|
| **交付轮**（Delivery） | 把需求推进到发布：构思 → 规格 → 计划 → 执行 → 验证 → 沉淀 | `/ideate`、`/brainstorm`、`/spec`、`/adr`、`/write-plan`、`/plan-check`、`/execute-plan`、`/tdd`、`/debug`、`/verify`、`/multi-review`、`/request-review`、`/receive-review`、`/compound`、`/git-commit`、`/finish-branch`、`/lfg` |
| **治理轮**（Governance） | 让知识库、技能和代码库持续健康：体检、回顾、安全、一致性 | `/health`、`/retro`、`/lint-lessons`、`/cso`、`/doc-release`、`/evolve`、`/careful`、`/source-verify`、`/pressure-test` |

两条链路**并行、互不替代**：

- 只跑交付轮 → 短期快，但 lessons 会积矛盾、skills 会老化、在线故障会失控
- 只跑治理轮 → 知识库整洁，但没有新交付喂养它，价值递减

**触发时机**：
- 交付轮：收到需求时进入（单条任务 / `/lfg` 全流程）
- 治理轮：周期性或触发式（发布后 `/doc-release`、knowledge drift 时 `/lint-lessons`、重大改动前 `/cso`、回顾时 `/retro`、吸收外部最佳实践时 `/evolve`）

> 灵感来源：腾讯技术工程在内容审核 AI 交付实践中提出的「交付驱动效率，治理保障质量」双轮驱动模型。

## 项目重点技能

CLI 工具重点技能：`/tdd`（命令行为与退出码契约测试）、`/write-plan`（子命令与参数体系规划）、`/verify`（跨平台行为验证）、`/git-commit`（结构化提交）、`/debug`（管道集成排障）、`/multi-review`（用户视角可用性评审）

## 所有可用技能

| 命令 | 用途 |
|------|------|
| `/brainstorm` | 结构化头脑风暴，设计先行 |
| `/spec` | 规格驱动开发（先定义验收标准再动手） |
| `/adr` | 架构决策记录（记录技术选型和设计决策的理由） |
| `/write-plan` | 编写实现计划 |
| `/plan-check` | 8+1 维度计划校验（需求覆盖 / 原子性 / 依赖 / 文件作用域 / 可验证 / 上下文 / 缺口 / Nyquist / Agent 工程化条件触发）+ 3 轮修订循环 |
| `/agent-design-check` | Agent 设计体检——4 维度（F3/F5/F8/F10）校验涉及多 agent 的计划（来自 12-factor-agents） |
| `/tdd` | 测试驱动开发（RED-GREEN-REFACTOR） |
| `/debug` | 系统性排障（根因优先） |
| `/execute-plan` | 按计划逐步执行 |
| `/subagent-dev` | 子代理协作开发 |
| `/dispatch-agents` | 并行分发独立任务（短，一次性 map-reduce） |
| `/squad` | 常驻多 agent 协作（tmux + worktree + capability 分权，长任务/需实时观察） |
| `/request-review` | 请求代码评审 |
| `/receive-review` | 处理评审反馈 |
| `/use-worktrees` | Git worktree 隔离开发 |
| `/finish-branch` | 完成开发分支 |
| `/write-skill` | 编写新技能 |
| `/verify` | 完成前验证 |
| `/which-skill` | 选择合适的技能 |
| `/ideate` | 多角度结构化构思 |
| `/compound` | 完成后提炼经验到知识库 |
| `/multi-review` | 多人格并行代码评审 |
| `/lfg` | 全自主流水线（plan→work→review→compound） |
| `/git-commit` | 结构化 git 提交 |
| `/todo` | 结构化任务拆分和管理 |
| `/cso` | 安全审计（OWASP + STRIDE + 供应链） |
| `/health` | 代码质量仪表盘（0-10 综合评分） |
| `/retro` | 工程回顾（git 历史分析） |
| `/doc-release` | 发布后文档同步 |
| `/careful` | 危险命令安全拦截 |
| `/lint-lessons` | 知识库健康检查（去重/矛盾/过时） |
| `/evolve` | 自我进化（搜索新项目 → 评估 → 创建 Issue 提案） |
| `/recall` | 按需检索 lessons / task-log / references/ 历史（含 BM25 兜底） |
| `/source-verify` | 从官方文档验证框架 API，防止凭记忆编 |
| `/digest-meeting` | 把多人讨论的原始语音转文字记录转为结构化产物（`/lfg` 前置源头） |
| `/lfg-doc` | 写文档场景的端到端流水线（标书 / 规范 / 白皮书 / 报告，与 `/lfg` 同源不同流水线） |
| `/outline-doc` | 拟文档大纲（章节树 + 字数估算 + R-ID 覆盖 + 引用占位） |
| `/draft-doc` | 写文档草稿（两段法：outline-pass + draft-pass） |
| `/review-doc` | 文档评审（4 人格并行：准确性 / 可读性 / 术语统一 / 完整性） |
| `/finalize-doc` | 文档定稿（8 项必检；不调 git-commit / finish-branch） |
| `/team-spec` | 规格制定编队（spec → plan-check → adr 串联，吸收 CCGS team-* 模式） |
| `/team-implement` | 实施编队（write-plan → execute-plan / tdd → verify 串联） |
| `/team-review` | 评审编队（multi-review → cso → receive-review 串联） |
| `/team-doc` | 文档场景编队（outline → draft → review → finalize 串联，跳过 lfg-doc 前置探索） |

## 何时使用哪个技能

- 需要探索方向和创意 → `/ideate`
- 不确定从哪里开始 → `/which-skill` 或 `/brainstorm`
- 需求模糊需要明确规格 → `/spec`
- 面临架构决策需要记录 → `/adr`
- 任务复杂需要规划 → `/write-plan` → `/plan-check`（复杂任务） → `/execute-plan`
- 想全自动完成 → `/lfg`
- 需要写新功能 → `/tdd`
- 遇到 bug → `/debug`
- 多个独立子任务（短，一次性） → `/dispatch-agents`
- 长任务需常驻多 agent + 角色分权 + 实时观察 → `/squad`
- 子代理驱动开发（规划 + 执行分离） → `/subagent-dev`
- 实现完成 → `/verify` → `/multi-review`
- 需要提交代码 → `/git-commit`
- 任务完成想沉淀经验 → `/compound`
- 需要安全审计 → `/cso`
- 需要代码质量检查 → `/health`
- 发布后更新文档 → `/doc-release`
- 想做工程回顾 → `/retro`
- 知识库需要体检 → `/lint-lessons`
- 想搜索新的可吸收项目 → `/evolve`
- 分支工作完成 → `/finish-branch`
- 需要检索历史教训 / 任务记录 / 参考清单 → `/recall`
- 写框架/库特定代码前想防止 API 幻觉 → `/source-verify`
- 收到多人讨论的原始语音转文字记录（idea 讨论 / 需求评审）→ `/digest-meeting`
- 写文档场景（标书 / 规范 / 白皮书 / 报告）→ `/lfg-doc`（替代 `/lfg`）；阶段细分：拟提纲 `/outline-doc` → 写草稿 `/draft-doc` → 评审 `/review-doc` → 定稿 `/finalize-doc`
- 想用「场景化预制流水线」替代临时编排 → `/team-spec`（规格段）/ `/team-implement`（实施段）/ `/team-review`（评审段）/ `/team-doc`（文档段）。这些是 `/lfg` 部分阶段的独立入口，避免 orchestrator 临时拼装 skill 导致漂移（吸收 CCGS team-* 模式，Issue #55）

## 核心原则

1. **设计先于编码** — 不要跳过构思直接写代码
2. **测试先于实现** — 先写失败测试，再写实现代码
3. **根因先于修复** — 不要在不理解问题的情况下尝试修复
4. **证据先于声明** — 不要在没有运行验证的情况下声称"完成"
5. **知识要沉淀** — 每次解决问题后运行 `/compound` 记录经验，让下次更快
6. **安全要审计** — 发布前运行 `/cso` 检查安全风险，执行危险命令前三思

## 外部工具集成

以下外部插件安装后可与本工作流配合使用：

- [codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — 安装后可用 `/codex:review` 获取 Codex AI 的独立代码评审，与 `/multi-review` 互补
