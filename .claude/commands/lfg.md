# LFG — 从需求到交付的全自动流水线

铁律：**先有计划，再动手。没有例外。**

> **/lfg 是 Environment Engineering 的主入口（Issue #34）**：本项目的设计哲学是优化 Agent 的**运行环境**而非 prompt——`.claude/rules/`（行为约束）+ `.claude/commands/`（工具集）+ `.agent-harness/`（记忆 + 审计）+ `.claude/hooks/`（生命周期感知）共同组成 Agent 的 habitat。跑一次 /lfg = 用全套环境完成一轮完整工作；缺任何一层，流水线威力会打折。
>
> **与 task-lifecycle 规则的关系**：当通过 /lfg 执行任务时，/lfg 的阶段替代 task-lifecycle 的对应步骤：
> - Phase 0.1 替代 task-lifecycle 第 0 步（读取项目知识）和第 1 步（写 current-task.md）
> - Phase 0.3 替代 task-lifecycle 第 2 步（展示并等待用户确认）和第 3 步（判断是否需要 /spec）
> - Phase 10.3 替代 task-lifecycle 的"待验证"状态
> - Phase 10.5 替代 task-lifecycle 的"用户验证通过"流程
>
> task-lifecycle 的核心约束（假设清单、用户确认、待验证状态、task-log 归档）仍然生效，由 /lfg 对应阶段保障。

当前项目：`Agent Harness Framework`（cli-tool / python）
测试命令：`make test`
检查命令：`make check`
启动命令：`harness`

---

## 阶段 0：任务理解与复杂度评估

### 0.1 理解任务（自动）

收到任务后，**第一个动作**是检查 `.agent-harness/current-task.md`：
- 如果存在未完成任务（有 checkbox 未勾选或标记为"待验证"），**🔴 停下来询问用户**：继续未完成任务还是替换为新任务？
- 如果未完成任务已处于"待验证"且所有 checkbox 已完成，先将其写入 `task-log.md` 归档，再继续新任务
- 如果为空或无进行中任务，继续

> **与 session-start hook 对齐（Issue #13）**：`.claude/hooks/session-start.sh` 在会话启动时已自动展示过未完成任务。/lfg 这里是再次保险——session-start 只提示，/lfg 做决策。若发现 `.agent-harness/.stop-hook-skip` sentinel 存在（之前人工放行过 Stop hook），**告知用户该 sentinel 仍在生效**，询问是否删除——sentinel 残留会让后续任务完成时不再被 Stop hook 守护（current-task 有未勾 checkbox 也能直接停）。

然后判断输入类型：

**如果输入是 Issue 编号**，根据前缀判断来源：

- `gl#42` → **GitLab Issue**（内网）：
  ```bash
  curl -sS --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "http://192.168.4.102/api/v4/projects/ai-x%2Fzjaf-harness/issues/42"
  ```
  > 如果 `GITLAB_TOKEN` 未设置 → **🔴 停下来提示用户**：`export GITLAB_TOKEN=<your-token>`

- `gh#42`、`#42` 或 `42` → **GitHub Issue**（默认）：
  ```bash
  gh issue view <编号> --json title,body,labels
  ```
  > 如果 `gh` 命令失败（Issue 不存在、未认证、网络错误）→ **🔴 停下来告诉用户**具体错误，不要猜测 Issue 内容

读取 Issue 内容作为任务描述。如果 Issue 有 `evolution` 标签，自动进入**进化集成模式**：
- 从 Issue 中提取目标项目链接
- 任务目标：分析该项目，将可模板化的独特技能融合到本框架
- 集成规范：改写为中文命令模板 → 放入 `templates/superpowers/.claude/commands/` → 更新 workflow 规则和决策树 → 更新 preset → 更新测试 → 更新文档 → `make dogfood` 同步 → `make ci` 验证
- 自动设定验收标准：新技能模板存在、测试通过、文档数字同步、dogfood 无漂移
- **通道选择**：evolution 模式自动走**完整通道**（含 /ideate + /brainstorm + /spec + /plan-check），跳过阶段 0.3 的复杂度评估询问。理由：吸收外部项目思想天然属于"大"复杂度，影响模板 + 测试 + 文档多个层面，需设计先行

**如果输入是文件路径且指向 `notes/` 下的原始讨论记录**（路径以 `notes/` 开头，以 `.md` 或 `.txt` 结尾，且**不**在 `notes/digested/` 下；文件头也不含 `<!-- processed:` 标记）：

→ **🔴 停下来告诉用户**：这看起来是未处理的原始讨论记录。建议先跑 `/digest-meeting` 做结构化摘要。它会根据项目文档状态自动分叉：

- **init 模式**（docs/product.md 尚为占位）→ 产出 `notes/digested/meeting-<date>-<topic>.md`，再用 `/process-notes` 填充框架文档
- **iterate 模式**（docs/product.md 已有实质内容）→ 直接写入 `.agent-harness/current-task.md`，然后你可以再次调用 `/lfg`

退出 /lfg；不属于此情况 → 继续下一步。

**如果输入是普通文本描述**：

0. **先检查项目类型**——读 `.agent-harness/project.json` 的 `project_type` 字段：
   - 若为 `meta`（微服务中央大脑项目）→ **告知用户走 meta 专属命令**（`/meta-sync` / `/meta-populate` / `/meta-create-task` / `/meta-activate-task`）而非 /lfg，退出。meta 项目不含业务代码，走单任务流水线会错。
   - 文件不存在或 project_type 不是 meta → 继续下一步
   - `/meta-activate-task` 激活的跨服务任务会注入到具体服务仓库的 current-task.md，在**服务仓库**里跑 /lfg 才合适

1. **再判断是不是运维/元任务**——如果是，告知用户走 CLI 不走 /lfg：

   | 用户意图 | 正确入口 | 为什么不走 /lfg |
   |---|---|---|
   | 初始化新项目 / 给其他仓库接入 | `harness init <target>` | /lfg 是日常开发流水线，不做脚手架生成 |
   | 升级已接入项目的模板 | `harness upgrade plan/apply <target>` | 同上 |
   | 检查项目健康度 / 看统计 | `harness doctor / export / stats <target>` | 诊断类，非任务流 |
   | 同步 meta 仓库上下文到服务 | `harness sync --all` / `harness sync <target>` | 运维类 |
   | 重建分层记忆索引 | `.agent-harness/bin/memory rebuild . --force`（项目自带）或 `harness memory rebuild <target>`（维护者） | 工具类 |
   | 并行派遣多个常驻 agent | `.agent-harness/bin/squad create <spec.json>` 或 /squad | 不是单任务流 |
   | 周期性代码体检 / 工程回顾 / 知识库 lint | `/health` / `/retro` / `/lint-lessons` | 元技能，lfg 阶段 9.3 有快速版 |
   | 自我进化搜索 | `/evolve` | 元技能，会反向触发 lfg |

   属于上表任一项 → 告知对应命令，退出 /lfg；不属于 → 继续下一步

2. **复述任务**：用自己的话重新描述任务目标，确认理解正确
3. **明确验收标准**：这个任务做到什么程度算"完成"？列出 3-5 条可验证的标准
4. 如果任务描述模糊 → **🔴 停下来向用户提问**，直到验收标准清晰

### 0.2 加载历史知识（自动，分层加载）

**在制定任何计划之前**，按分层记忆规则从 L0/L1 开始读，只在需要时才下沉到 L2/L3：

**必读（L0/L1 常驻）**：

1. 读 `.agent-harness/memory-index.md` — L1 热索引（最近 10 教训 + 5 任务 + references 清单 + 主题索引）
2. 读 `AGENTS.md` — L0 硬规则约束，不可违反
3. 读 `docs/architecture.md` — L0 模块边界，避免在错误的位置写代码
4. 读 `docs/product.md` — L0 现有功能，避免与已有功能冲突
5. 读 `docs/decisions/` 目录列表 — 扫一眼已有 ADR 标题，相关的才展开读
6. **扫描 `.harness-plugins/rules/` 目录**（如存在）—— 用户或团队的自定义规则扩展。发现 `.md` 文件则全部读入，与官方规则同等级合规约束。不存在或目录为空 → 跳过。这是项目的插件机制入口，遗漏会让团队规则被忽视。

**按需检索（L2/L3，禁止默认全量读）**：

7. 如果 memory-index 命中相关话题，或任务描述涉及历史踩坑 → 运行 `/recall <关键词>` 做定向检索（后台会搜 `lessons.md` + `task-log.md`）
8. 如果任务涉及专业维度（安全 / 性能 / 无障碍 / 测试设计）→ 运行 `/recall --refs <关键词>` 加载对应 checklist（`.agent-harness/references/`）
9. 如果 /recall 返回明确相关条目，**必须在计划中显式引用教训标题**，说明如何避免重蹈覆辙
10. **BM25 兜底（二级检索）**：若 memory-index 未命中 + `/recall` 的 Grep 也返回空，`/recall` 技能会自动串 `.agent-harness/bin/memory search "<关键词>"` 做 BM25 相关性兜底（纯 stdlib，灵感自 [context-mode](https://github.com/mksglu/context-mode)）。这解决"关键词写错/用同义词"时 Grep 漏召的问题，是 /recall 的内置行为而非单独步骤
11. **上下文预算告急时（Issue #33）**：若 context-monitor hook 提示工具调用计数接近阈值（50/100/150），或任务本身涉及大量工具输出，**运行 `/recall --refs claude-code-internals`** 展开 `.agent-harness/references/claude-code-internals.md`——了解 Claude Code 的 5 级渐进式压缩机制（L1 Tool Result Budget → L5 Autocompact）和 7 个 continue site，能让你提前用 Think in Code 规避 L1 被动截断，而不是等 L5 `/compact` 兜底丢失上下文

> **禁止**：直接全文读 `lessons.md` 或 `task-log.md`。违反分层加载会挤占 AI 上下文，把热知识（L1）、温知识（L2）、冷知识（L3）变成一锅粥。见 `docs/decisions/0001-layered-memory-loading.md`。
>
> **Context Budget（context-mode 吸收，Issue #29）**：本阶段以及后续所有工具调用都受 `.claude/rules/context-budget.md` 约束——搜索/统计/过滤类任务优先写脚本只返回结果（Think in Code），单次工具输出 > 2k tokens 必须先 pipe 处理。

### 0.3 评估复杂度（自动，用户可覆盖）

通过任务描述 + 代码扫描 + 关键词检测，判断复杂度并告知用户。

**复杂度信号关键词**（出现以下关键词时，倾向于提升一级复杂度判断）：
- 架构类：重构、迁移、拆分、合并、微服务、中间件、抽象层
- 实现类：并发、异步、缓存、事务、锁、队列、流式
- 安全类：认证、授权、加密、CORS、CSRF、注入
- 测试类：集成测试、端到端、性能测试、压力测试
- 运维类：部署、CI/CD、监控、日志、告警
- **并行类**（触发超大-可并行档）：同时、并行、分头、三方面、兵分、多管齐下、并发开发、三条线、scout-builder-reviewer、调研并实现

| 级别 | 判断标准 | 走哪条通道 |
|------|---------|-----------|
| **微小** | 改 1-2 个文件，无行为变化（typo、配置、格式） | 快速通道 |
| **小** | 改 1-2 个文件，行为变化明确（bug fix、加字段） | 轻量通道 |
| **中** | 改 3+ 个文件，需要设计（新功能、新接口） | 标准通道 |
| **大** | 跨模块、需要架构决策、影响面广 | 完整通道 |
| **超大-可并行** | 含「并行类」关键词 **或** 可拆 3+ 互不强依赖子任务 **或** 经典「调研→实现→评审」三段 **或** 单 agent 估时 > 4 小时 | **squad 通道**（自动起 tmux 多 worker） |

**与 Trust Calibration 联动（Issue #30，`.claude/rules/autonomy.md`）**：复杂度判定结果直接驱动 autonomy 的「任务复杂度 × 操作基线」二维模型——

- **微小/小**：跳过 `/spec`、`/plan-check`、多轮评审；谨慎级操作完全自主、不每步汇报
- **中**：谨慎级操作"完全自主但每步汇报"；改业务代码**前必须**先让 Explorer（`/dispatch-agents` 派只读子代理或 squad 的 scout）读相关模块
- **大**：首次改动前汇报方向；Explorer 强制
- **超大-可并行**：orchestrator/scout/builder/reviewer 按 capability 运行时强制（`settings.local.json` 的 `permissions.deny`），编排者连代码都不碰

**连续 3 次小任务成功后，同类任务的「谨慎操作」阈值自动下调到「自由」**（同一会话有效）。这让简单任务不被流程绊脚，复杂任务必须先探路。

输出格式：
```
复杂度判断：中
理由：需要修改 models、views、serializers 和 tests 共 5 个文件，涉及新增 API 端点
通道：标准通道（环境准备 → 计划 → 实施 → 评审 → 验证 → 沉淀 → 收尾）
历史参考：lessons.md 中有 1 条相关记录（API 端点需注意分页参数验证）

假设清单：
- 假设：使用 REST 风格而非 GraphQL | 依据：现有 API 均为 REST
- 假设：新端点不需要认证 | 依据：待确认

确认走标准通道？假设清单是否准确？（用户可回复"走完整通道"/"轻量通道"/"走单 agent 不要并行"覆盖）
```

**如果判定为"超大-可并行"档**，输出格式额外增加 squad 拓扑草稿（见下文 squad 通道章节）并等用户确认；用户若回"不要并行" → 自动降级到**完整通道**（单 agent 跑大任务，不起 tmux）。

**假设清单是必填项**。列出所有隐含假设（技术选型、范围边界、用户意图的理解），格式：`- 假设：... | 依据：...`。没有依据的假设标注"待确认"。

---

## squad 通道（超大-可并行任务）— 详见 references/squad-channel.md

**进入条件**：阶段 0.3 判定为"超大-可并行"档，用户确认拓扑。

> **完整工作流已抽到 `.agent-harness/references/squad-channel.md`**(148 行,含拓扑模板 / 介入点 1-6 / 失败兜底)。本主模板只保留概要 + 入口指针——非超大任务不必加载,降低主模板每次启动的 context 开销。
>
> **加载方式**:进入 squad 通道时,运行 `/recall --refs squad-channel` 加载完整工作流;或直接 `cat .agent-harness/references/squad-channel.md`。

**核心思想速记**:`/lfg` 主会话扮演**协调员**——起 squad、实时翻译 mailbox 状态、关键节点拉用户介入。worker 在 tmux 后台并行干活。用户可随时 `tmux attach` 介入调试。

**6 个用户介入点速览**(详细见 references/squad-channel.md):

1. **拓扑确认**(必须):展示 worker 拓扑给用户,等"可以"再起
2. **scout → builder 切换**(必须 + 强制 compact):scout 完成后展示制品,等用户确认
3. **worker 失联**(watchdog 触发):重启 / 跳过 / 终止三选一
4. **worker 卡死**:attach 调试 / 调整方向 / 跳过手工接管
5. **reviewer PASS → 合并**(必须 + 强制 compact):合并 / 回退 / 手动检查
6. **/finish-branch 合并 + push**(必须):4 种去向（合并 / 创建 PR / 保留分支 / 丢弃）

**核心命令速览**:
```bash
.agent-harness/bin/squad create spec.json   # 起 squad
.agent-harness/bin/squad watch &            # 后台 watchdog + advance
.agent-harness/bin/squad stop all           # 中止保留 worktree
```

**硬规则回顾**:worker 内**不得**调用 `/squad create` / `/dispatch-agents` / 完整 `/lfg`(防递归资源爆炸)。详见 AGENTS.md。

完整规格、拓扑模板(经典三段 / 多端点 / 重构迁移 / 四角色重型)、各介入点交互模板、失败兜底矩阵——见 `.agent-harness/references/squad-channel.md`。

---

## 用户确认点分级(降密度,防疲劳)

主模板有 18-20 个独立 STOP 确认点。不是所有都需要在每个通道都触发。按"必要 / 建议 / 可跳"分级:

**必要(任何通道都不可跳,跳了会出事故)**:

- ⚠️ 任务流转类:覆盖未完成任务(行 27)、Issue 元数据获取失败(行 42/48)、原始讨论记录误读(行 59)、任务描述模糊(行 90)
- ⚠️ 安全/数据类:基线测试失败(行 359)、Critical/High 安全发现(行 625)、out-of-scope R-ID 确认(行 603)
- ⚠️ 流程关键节点:计划摘要确认(行 431)、规格确认(行 394)、卡死/3 轮未收敛(行 501/555)、待验证(行 750)、收尾合并方式(行 695)
- ⚠️ squad 通道介入点(行 222/247/277/292):4 个均必要

**建议(可在轻量/快速通道默认跳过,但应在 commit 消息或完成报告中告知用户)**:

- 构思方向选择(行 375):仅完整通道触发——轻量通道不进入此阶段
- 复杂度评估展示(行 910):快速通道判定为"微小"时可不展示,直接进入

**可跳(主模板 reminder 类,不是真"等用户"——AI 自我提醒即可)**:

- 阶段 4 实施期双守卫提醒(行 463):是 reminder 不是 confirmation
- 并行子 agent 隔离硬规则(行 476):是 reminder
- 阶段 7.2 R-ID 三态(行 603):仅 missed 状态触发"等用户"

**通道默认行为**:

- **快速通道**:仅触发"必要"级确认 ≈ 1-2 个(任务流转 + 验证完成)。改 1-2 文件无行为变化的微小任务直接 `/execute-plan` 推进
- **轻量通道**:触发"必要" + 部分"建议" ≈ 3-5 个。明确行为变化的小任务用 `/tdd` + 简化 `/write-plan`(3-5 行步骤)
- **标准/完整通道**:触发全部"必要" + 全部"建议" ≈ 8-12 个。`/write-plan` 全量 + `/plan-check` 8 维度
- **squad 通道**:6 个介入点 + 完整阶段 ≈ 12-16 个;长任务建议先 `/use-worktrees` 隔离再起 squad

如果某个 STOP 在适用通道里**未被显式触发**,AI 应**自己处理**(写完整报告 / 自检 / 跑工具),不询问用户。

## 快速通道（微小任务）

```
理解 → 记录 → 修改 → 测试 → 提交 → 通知
```

1. 在 `.agent-harness/current-task.md` 写 1-2 行记录（任务目标 + 改什么文件）
2. 直接修改代码
3. `make test` + `make check` 验证
4. `/git-commit` 提交
5. 告知用户完成结果（改了什么、测试是否通过），等待用户确认无误
6. 用户确认后清空 current-task.md，写入 task-log.md
7. 如有值得记录的发现 → `/compound`

---

## 轻量通道（小任务）

```
理解 → 计划(简) → 实施 → 快速评审 → 验证 → 提交 → 通知 → 沉淀
```

1. 在 `.agent-harness/current-task.md` 写简要计划（任务目标、假设清单、3-5 行步骤、完成标准）
2. `/tdd` 实施
3. **快速评审**：运行 `/multi-review`，但只启用正确性 + 测试完整性 2 个审查员（跳过其他 4 个）
4. `make test` + `make check` 验证
5. **自检**：回头看验收标准，每条都满足了吗？
6. `/git-commit` 提交
7. 告知用户完成结果，等待确认
8. 用户确认后清空 current-task.md，写入 task-log.md
9. `/compound` 沉淀（如果解决了值得记录的问题）

---

## 标准/完整通道

### 阶段 1：环境准备（自动 | 标准+完整通道）

1. 记录当前分支和 HEAD commit → 存入 `current-task.md`（用于回滚）
2. **创建隔离环境**（完整通道必须，标准通道推荐）：
   - 长任务 / 风险任务 / 并行任务 → 运行 `/use-worktrees` 创建独立 worktree（推荐），避免污染主工作区
   - 短任务 / 单文件改动 → `git checkout -b <feat/fix>/<topic>-<date>` 建工作分支即可
   - 涉及生产环境数据或"危险操作"（rm -rf / drop table / force push）→ 先运行 `/careful` 做一轮安全拦截
   - 运行 `make test` 确认基线测试通过
   - 基线测试失败 → **🔴 停下来告诉用户**，不在有问题的基础上工作
3. **记录质量基线**：
   - 测试数量和通过率：`make test` 的输出
   - 代码检查结果：`make check` 的输出
   - 记录到 `current-task.md` 的 LFG 进度区

> 用户可以说"不用 worktree"跳过隔离环境，直接在当前分支工作。

---

### 阶段 2：构思（需确认 | 仅完整通道）

仅在**复杂度为"大"**时执行，标准通道跳过。

1. 运行 `/ideate` — 多角度生成候选方案
2. 展示 5-7 个候选方案，每个标注优劣
3. **🔴 等待用户选择方向**
4. 运行 `/brainstorm` — 深入设计选定方案
5. 设计文档写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

---

### 阶段 2.5：规格定义（⚙️ 自动 → 需确认 | 标准+完整通道）

满足以下**任一条件**时执行：
- 需求描述超过两句话
- 预计涉及 3 个以上文件
- 包含模糊词（"优化"、"改进"、"支持"、"更好"等无明确标准的词）
- 涉及新模块或新架构模式

1. **先加载需求映射清单**：运行 `/recall --refs requirement-mapping` 展开 `.agent-harness/references/requirement-mapping-checklist.md`（GSD Issue #17 吸收）。了解 R-ID 三元映射规则（每条需求最终必须是 `satisfied` / `out-of-scope` / `missed` 三态之一，missed 阻断完成），在写规格时就把每条验收标准打上 R-ID，不要等到阶段 7 验证才发现漏项
2. 运行 `/spec` — 规格驱动开发流程
3. 产出结构化规格文档：目标、命令、项目结构、代码风格、测试策略、边界
4. 将模糊需求转化为可测试的验收标准
5. 规格文档写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-spec.md`（含 R-ID 列表）
6. **🔴 展示规格，等待用户确认**

> 如果任务已有明确的验收标准（如 Issue 中已详细列出），可跳过此阶段。

---

### 阶段 3：计划（需确认）

**通过门：计划存在 + 通过质量检查 + 用户确认**

#### 3.1 生成计划

1. **生产项目预警**：读 `.agent-harness/project.json`，若 `has_production=true` 或 `sensitivity=high`，在写计划前**先跑 `/cso` 快速扫**——识别本次任务涉及的潜在高风险区（认证/授权/SQL/文件读写/外部 API），把结论作为计划约束写进 Non-goals 或专门的「安全约束」段。阶段 7.4 的 `/cso` 完整审计作为兜底，但生产项目在计划期就把风险内化成步骤约束，比事后补救便宜。非生产项目跳过此步
2. 检查 `docs/superpowers/specs/` 是否已有适用的计划或规格
3. **如果没有**：运行 `/write-plan` 生成计划
4. **如果有**：阅读已有计划/规格，评估是否仍然适用
5. **如果计划涉及架构选择**（技术选型、模式选择、关键设计决策）：运行 `/adr` 记录决策，ADR 存入 `docs/decisions/`
6. **如果计划引用了框架/库的具体 API、CLI flag、配置项**（如 "使用 React useState"、"传 --foo flag"）：运行 `/source-verify` 从官方文档验证，防止凭训练数据编 API。教训来自 lessons.md 的"CLI flag 假设在 plan 阶段必须 source-verify"
7. **如果任务可拆成多个 2-5 分钟粒度的子步骤**：在计划中生成对应的 `/todo` 清单，写到 current-task.md 的 Progress 段；执行阶段逐项勾选
8. **标准/完整通道下**：计划生成后立即运行 `/plan-check` 做 8 维度结构化校验（需求覆盖 / 原子性 / 依赖排序 / 文件作用域 / 可验证性 / 上下文适配 / 缺口检测 / Nyquist 合规）+ 最多 3 轮修订循环。**快速/轻量通道跳过此步**
9. **如果计划涉及多 agent 协作**（`/squad`、`/dispatch-agents`、`/subagent-dev`、自定义 worker prompt 或 capability 分权）：在 `/plan-check` 通过后额外运行 `/agent-design-check` 做 4 维度体检（F3 Context Ownership / F5 State Unification / F8 Control Flow / F10 Small Focused Agents），对应 `plan-check` 的第 9 维度。来源：[12-factor-agents](https://github.com/humanlayer/12-factor-agents)。**非多 agent 场景跳过此步**
10. **如果计划想引入硬编码字面/路径白名单**（如 `ALLOWED_X = [...]`、`KNOWN_PATHS = [...]`、特定状态字面清单等用于"边界守卫"决定允许/拒绝/触发/跳过）：先读 `.claude/rules/architecture-patterns.md` 反模式 1 的**三问决策树**（外部行为驱动？/ 不可机械证明完整性？/ 漏项静默退化？),三问全中即是反模式,优先选自动发现 / 字段标记 / 策略统一化,而非维护清单。教训来自 lessons.md 5 次反复触发(check_repo / _RUNTIME_MODULES / upgrade three_way / stop hook 5 字面 / stop hook 通用字段)

#### 3.2 计划质量检查（必须通过才能继续）

若已跑 `/plan-check` 且全 8 维度（+ 第 9 维度如触发）PASS，跳过本节；否则逐条检查，**不通过就修正计划**：

- [ ] **覆盖度**：验收标准的每一条在计划中都有对应步骤（若有 `/spec` R-ID：每个 R-ID 必须映射到 task 或标 out-of-scope）
- [ ] **具体性**：每个步骤有精确的文件路径（不是"相关文件"）
- [ ] **可验证性**：每个步骤有验证命令和预期结果
- [ ] **代码完整性**：代码块不含 `// TODO`、`...` 省略、`TBD`
- [ ] **边界覆盖**：列出了边界情况和错误场景的处理
- [ ] **历史教训 + 团队规则**：如果 lessons.md 或 `.harness-plugins/rules/*.md`（团队自定义规则）有相关记录，计划中显式说明如何引用 / 避免
- [ ] **依赖明确**：步骤之间的依赖关系和执行顺序清楚

#### 3.3 用户确认

**🔴 展示计划摘要等用户确认**：

```
## 计划摘要

目标：<一句话>
步骤数：<N> 步
涉及文件：<文件列表>
预计影响范围：<模块/功能>
历史参考：<引用的 lessons.md 条目，或"无">
验收标准：
1. <标准 1>
2. <标准 2>
3. ...

确认开始执行？
```

**绝对禁止**：没有计划就写代码，口头描述代替书面计划，不检查就执行。

---

### 阶段 4：实施（⚙️ 自动，遇阻停下）

**通过门：所有计划步骤完成 + 测试通过**

> **反偷懒门禁（Issue #36，`.claude/rules/anti-laziness.md`）**：阶段切换时 4 道门禁生效——数量门禁（每项检查有明确状态）、上下文隔离（评审在独立 SubAgent）、反合理化表（跳过必须给具体理由）、下游消费者门禁（前置产物存在且非空）。各 skill 在自身文档中落地具体检查逻辑。

> **Stop hook 守护（Issue #13）**：阶段 4 期间若 AI 试图停止但 `current-task.md` 仍有未勾选 checkbox，`.claude/hooks/stop.sh` 会 block 并要求先更新进度。若发现 `.agent-harness/.stop-hook-skip` sentinel 存在，**先询问用户**是否允许跳过——sentinel 残留会让守护机制失效。完成任务后务必删除 sentinel（`rm -f .agent-harness/.stop-hook-skip`），让下次任务重新受保护。

#### 4.1 按步执行

> **⚠️ 实施期双守卫提醒(必读，AI 自我提醒，不停下等用户)**:
> - **API/CLI flag 幻觉守卫**:本阶段写代码若引用框架/库具体 API、CLI flag、配置项,且**计划阶段未跑 `/source-verify`**(快速/轻量通道常跳过),实施期**遇到第一处不确定的 API 调用立即跑 `/source-verify`**——AI 凭记忆写 API 是 1 类常见幻觉源。教训:lessons.md "CLI flag 假设在 plan 阶段必须 source-verify"
> - **Context 预算守卫**:本阶段工具调用爆发(grep / Read / Bash)易爆 context。**单次输出 > 2k tokens 必须先 pipe**(`| head -N` / `| grep PATTERN` / `| jq '.关键字段'`),搜索/统计/过滤类任务先写脚本只返回结果(Think in Code)。详见 `.claude/rules/context-budget.md`

对计划中的每一步：

1. **选择执行方式**：
   - 写功能代码 → `/tdd`（先写测试再实现）
   - 配置/迁移/文档 → `/execute-plan`（直接执行）
   - 计划和执行需要分离（规划者/执行者角色） → `/subagent-dev`（计划在主 agent，执行下放子代理）
   - 3+ 独立短子任务（无共享状态） → `/dispatch-agents`（一次性 map-reduce）
   - 长任务需角色分权 + 实时观察 + 多 worktree 并行 → **squad 通道已在阶段 0.3 自动选择**，见 `## squad 通道` 章节（用 `.agent-harness/bin/squad create spec.json`）

   > **⚠️ 并行子 agent 隔离（硬规则，AI 自我提醒）**：选 `/dispatch-agents` 或 `/subagent-dev` 时，主 agent **必须**先为每个子 agent 建立独立日志空间，禁止并发写共享 `current-task.md`：
   > ```bash
   > .agent-harness/bin/agent init <agent-id>          # id: ^[a-z0-9][a-z0-9-]{0,30}$
   > .agent-harness/bin/agent diary  <agent-id> "..."  # 子 agent 过程日志
   > .agent-harness/bin/agent status <agent-id> "..."  # 子 agent 当前状态
   > .agent-harness/bin/agent aggregate                # 主 agent 收尾时汇总
   > ```
   > 理由：并发写同一个 current-task 会互相覆盖。详见 `.claude/rules/task-lifecycle.md` "并行子 agent 的日志隔离"节。不适用于 `/squad`（squad 有自己的 `squad/<task>/workers/<name>/` 隔离）。
2. **执行该步骤**
3. **验证**：运行步骤中指定的验证命令
4. **回归检查**：运行 `make test` 确认没有破坏已有功能
5. **提交并打快照 tag**：创建原子 commit，消息格式 `<type>(<scope>): <描述> [plan step N]`，然后打一个轻量 tag `lfg/step-N`（用于精确回滚到任意步骤）
6. **更新进度并写 audit**：在 `current-task.md` 中勾选该步骤；随后追加一条 WAL 审计（task-lifecycle 硬要求）：
   ```bash
   .agent-harness/bin/audit append --file current-task.md --op update \
     --summary "plan step N 完成：<一句话摘要>"
   ```
   audit 目录不存在时命令会自然失败，属预期；出现在日常项目中应正常写入。

#### 4.2 遇到问题时的处理

| 情况 | 处理方式 |
|------|---------|
| 步骤执行失败但原因清楚 | 修复后继续，在 commit 消息中说明 |
| 步骤执行失败且原因不清 | 运行 `/debug` 排查，找到根因后修复 |
| 连续 3 步失败 | **🔴 停下来**，可能计划本身有问题，需要回到阶段 3 重新制定 |
| 发现计划遗漏了重要场景 | **暂停实施**，补充计划步骤，然后继续 |
| 需要做计划外的改动 | 记录原因，创建独立 commit 标注为 `unplanned:` |

#### 4.3 自我检查（实施完成后、评审前）

在请求评审之前，先自己检查一遍：

1. **回顾验收标准**：每一条都满足了吗？逐条对照
2. **回顾计划**：所有步骤都做了吗？有没有跳过的？
3. **完整性检查**：`make test` 全部通过？`make check` 没有新增警告？
4. **公共规则合规检查**：逐条核对项目规则，确认没有违反

   | 规则 | 检查什么 |
   |------|---------|
   | **testing** | 三类测试场景（正常/边界/错误）都覆盖了？先写测试再写实现？ |
   | **documentation-sync** | 每个功能点都同步更新了对应文档？docs/ 中没有遗漏？ |
   | **safety** | 没有提交密钥/token？没有引入不必要的依赖？ |
   | **error-attribution** | 如果过程中有返工，task-log 和 lessons 都记录了？ |
   | **autonomy** | 需要用户确认的操作都确认了？没有越权执行？ |

5. 如果发现遗漏 → 补做再继续，不要带着已知问题进入评审

---

### 阶段 5：评审（⚙️ 自动）

**通过门：评审结论为 PASS**

1. 运行 `/request-review` — 整理本次变更的 diff 摘要、关键决策、验收标准，形成结构化评审材料（评审员可直接拿去用）
2. 运行 `/multi-review` — 6 角色并行评审所有变更（以 `/request-review` 产出为输入）。默认使用 `review` 模式（审查员间上下文隔离，防锚定）；涉及安全或架构决策时用 `--mode challenge`（对抗验证）；复杂权衡用 `--mode consult`（共享上下文）
3. 收集评审报告

| 结论 | 下一步 |
|------|--------|
| **PASS**（无 P0/P1） | → 阶段 7（验证） |
| **PASS WITH CONDITIONS**（有 P1） | → 阶段 6（修复，先跑 `/receive-review` 结构化消化反馈） |
| **FAIL**（有 P0） | → 阶段 6（修复，先跑 `/receive-review` 结构化消化反馈） |

> **多 agent 任务复盘**：本次任务若走 squad 或 `/dispatch-agents`，评审 PASS 后建议再串一次 `/agent-design-check`，对照计划期的体检结果——验证 F3/F5/F8/F10/F11 在执行期是否漂移（worker 越权改上游产物 / orchestrator 越界专业判断 / 状态同步点漏接 等）。非多 agent 跳过。

---

### 阶段 6：修复循环（⚙️ 自动 → 可能需确认）

**通过门：重新评审 PASS，或达到 3 轮上限**

每一轮：
1. 运行 `/receive-review` — 结构化消化评审反馈：分类（接受 / 质疑 / 推迟）、按 P0→P1 排序、标记有争议项
2. **分析根因**：不是直接改代码，先理解评审员为什么标记这个问题
3. 按 P0 → P1 优先级修复
4. 每个修复创建独立 commit：`fix: <问题描述> [review round N]`
5. 运行 `make test` 确认修复没有引入新问题
6. 重新运行 `/multi-review`
7. PASS → 结束循环

**3 轮后仍有 P0/P1 → 🔴 停下来**：

```
⚠️ 修复循环未收敛（已执行 3 轮）

仍存在的问题：
- [P0] file.py:42 — <描述>
- [P1] api.py:88 — <描述>

根因分析：
- 问题 1 可能是因为 <分析>
- 问题 2 反复出现，可能需要 <分析>

选项：
1. "继续" — 再试 3 轮修复（绝对上限 6 轮，超过后此选项不可用）
2. "回退" — 撤销所有变更回到基线 commit
3. "跳过" — 接受当前状态，将问题记录到 current-task.md 的"已知问题"段
```

---

### 阶段 7：验证（⚙️ 自动 → 可能需确认）

**通过门：所有验证通过**

#### 7.1 技术验证

运行 `/verify` — 完成前验证技能，输出证据链（不只是"跑通"而是"证明跑通"）：

1. `make test` — 全部测试通过（记录测试数、耗时、新增测试）
2. `make check` — 代码质量检查通过（记录警告数变化）
3. `/verify` 还会产出结构化报告：验收标准对照 + 测试证据 + 未覆盖边界提示，作为阶段 7.2 的输入

> 验证失败且原因不清 → 立刻串 `/debug` 定位根因（不要在不理解的情况下尝试修复，与阶段 4.2 同一原则）。

#### 7.2 验收标准核验

**先加载需求映射清单**：运行 `/recall --refs requirement-mapping` 复习 R-ID 三元映射硬规则（若阶段 2.5 已加载过可跳过）——每条规格 R-ID **必须**落到 `satisfied` / `out-of-scope` / `missed` 之一，不允许"差不多"。`missed` 状态阻断完成。

逐条核验阶段 0 定义的验收标准 + 阶段 2.5 打上的 R-ID：

```
## 验收标准核验

- [x] R-001 标准 1：<描述> — ✅ satisfied（证据：测试 test_xxx 覆盖）
- [x] R-002 标准 2：<描述> — ✅ satisfied（证据：手动验证输出正确）
- [ ] R-003 标准 3：<描述> — ❌ missed（原因：<说明>）→ 回阶段 4
- [—] R-004 标准 4：<描述> — ⊘ out-of-scope（原因：<说明>，用户确认后放行）
```

有 `missed` 的 R-ID → 回到阶段 4 补充实施；有 `out-of-scope` 的 → 🔴 展示给用户确认。

#### 7.2.5 Spec-to-Code Compliance（Issue #40）

如果上游 `/spec` 产出过规格文档，在 R-ID 核验后执行 `/verify` 的第 5.7 步——逐条检查实现是否忠实匹配规格意图（aligned / drifted / missing）。`missing` 等同于 R-ID missed，回阶段 4；`drifted` 展示给用户判断。无 `/spec` 产出则跳过。

#### 7.3 穷举验证（关键路径）

如果本次改动涉及**数据安全、用户内容、文件读写、升级迁移**等关键路径，必须做穷举端到端验证：

0. **先加载测试模式清单**：运行 `/recall --refs testing` 展开 `.agent-harness/references/testing-patterns.md`，把项目沉淀的测试模式（边界值策略、并发脚本骨架、错误注入姿势等）作为穷举脚本的参考基线。跳过这一步容易漏覆盖项目历史上踩过的坑
1. 写一个一次性脚本，在临时目录中模拟真实使用场景
2. 覆盖五类场景：正常路径、边界情况、错误路径、冲突/竞争、组合场景
3. 每项检查输出一行 ✅/❌，末尾汇总通过/失败数
4. 全部通过才继续；有失败项 → 回到阶段 4 修复

> 不涉及上述关键路径的改动可跳过此步骤。

#### 7.4 安全审计（生产项目）

如果项目有生产环境：
1. 运行 `/cso` 做安全审计
2. 发现 Critical/High → **🔴 停下来告诉用户**
3. Medium/Low → 记录到完成报告

**验证失败 → 回到阶段 6 修复（计入修复轮次）。**

---

### 阶段 8：质量对比（⚙️ 自动）

将当前结果与阶段 1 记录的质量基线对比：

```
## 质量变化

| 指标 | 之前 | 之后 | 变化 |
|------|------|------|------|
| 测试数 | 42 | 48 | +6 ✅ |
| 测试通过率 | 100% | 100% | — |
| Lint 警告 | 3 | 2 | -1 ✅ |
| 类型错误 | 0 | 0 | — |
```

质量退步项（测试减少、警告增多、覆盖率下降）会被标记到完成报告中。不阻塞流程，但会提醒用户注意。

---

### 阶段 9：沉淀与知识维护（⚙️ 自动）

#### 9.1 提炼经验

**若本次任务走 squad 或 /dispatch-agents/subagent-dev**：先运行 `harness agent aggregate` 汇总所有 sub-agent 的 artifacts + diary（Issue #30 结构化知识制品会集中显示在顶部），把值得沉淀的发现作为 `/compound` 的输入——比只看 current-task.md 能捕获更多 sub-agent 遇到过的坑。

> **冲突预检（`.claude/rules/knowledge-conflict-resolution.md`）**：/compound 写入新 lesson 前，若本次任务踩的坑与已有 lesson **指向相反**，按 T3/T4/T5 分型——T3（两条 confirmed lesson 互斥）→ 推荐转 `when:` 条件分支合并而非新建；T4（多 agent 结论不一致，来自 squad/aggregate）→ 两条都标 tentative 等用户选；T5（lesson 只是风险警告不是实际教训）→ 别写新 lesson，只在 current-task 里记一次风险提醒。规则不自动执行，`/compound` 只做提示。

运行 `/compound` 提炼经验教训：
- 评审中被发现的问题（说明下次如何在实施阶段就避免）
- 实施中走过的弯路（说明下次的更优路径）
- 修复循环中反复出现的模式（说明根因和预防方法）
- sub-agent artifacts 里标记为 `tension` / `incident` / `decision` 类型的制品（优先沉淀）
- 写入 `.agent-harness/lessons.md`

> 与 `/doc-release` 联动：阶段 10.2 的文档同步只改对外 README/product/architecture；本步骤的 lessons 沉淀是对内的"为什么这样改"——两者是互补输出，不要把 lessons 内容塞进 release 文档。

`/compound` 完成后**必须**两步闭环（不做的话下次 /lfg 读到的 L1 热索引是过时的、WAL 也缺一条）：

```bash
# 1. 刷新 L1 热索引——memory-index.md 里的"最近教训"自动同步
.agent-harness/bin/memory rebuild . --force

# 2. 记录 WAL 审计（对 lessons.md 的变更必须登记）
.agent-harness/bin/audit append --file lessons.md --op append \
  --summary "/compound 写入 N 条教训：<标题关键词>"
```

#### 9.2 ADR 状态维护（/adr 收尾）

浏览 `docs/decisions/` 目录，检查架构决策记录状态：
- 如果有 `Proposed` 状态的 ADR 与本次任务相关（不论是阶段 3 创建的还是之前手动创建的）：确认是否应更新为 `Accepted`
- 如果本次变更影响了已有 ADR 的前提条件：标记该 ADR 为 `Deprecated` 或创建 superseding ADR
- **如果评审/实施中暴露了阶段 3 未捕捉到的隐性架构决策**（评审员追问"为什么用 X 不用 Y"时）→ 立即串 `/adr` 补登记，避免决策理由只留在评审 thread 里
- 如果 `docs/decisions/` 为空或无相关 ADR：跳过此步骤

#### 9.3 知识库健康检查

对知识库做快速体检（**不要**运行完整的 `/lint-lessons`，只手动检查以下 3 项，对齐 `.claude/rules/knowledge-conflict-resolution.md`「叠加使用症状维度和解决维度」）：
- 新写入的条目是否与已有条目重复？如果是 → 合并
- 是否存在过时的条目（引用的文件已不存在）？如果是 → 标记
- 新条目与已有条目**指向相反**？按 T3/T4/T5 标 resolution-type，交由用户裁决（不自动合并）

> 完整 6 项 `/lint-lessons` 检查建议每 1-2 周手动运行。

---

### 阶段 10：收尾与文档（⚙️ 自动 → 需确认）

#### 10.1 代码收尾

- 在工作分支 / worktree 中 → 运行 `/finish-branch` 技能处理：
  - 技能会依次检查：未提交改动、基分支同步、冲突预检、PR/合并方式选择、远端推送策略
  - 涉及 `git reset --hard` / `git push --force` / `rm -rf` 等危险动作前，自动串 `/careful` 做拦截确认
  - 用户可在技能交互中选四种去向：合并到主分支 / 创建 PR / 保留分支不合并 / 丢弃所有变更
- 在主分支 → `/git-commit` 确保所有变更已提交（不允许在 master 上 `git reset --hard`，如需撤销用 `git revert`）

#### 10.2 文档同步

运行 `/doc-release`：
- 检查 README、docs/product.md、docs/architecture.md 是否需要更新
- 自动修正事实性内容，叙述性变更交给用户确认

#### 10.3 完成报告

```
## ✅ LFG 完成报告

任务：<任务描述>
复杂度：<微小/小/中/大>
通道：<快速/轻量/标准/完整>

### 验收标准
- [x] <标准 1>
- [x] <标准 2>
- [x] <标准 3>

### 执行摘要
计划：<计划文件路径>
提交：<N> 个 commit（<首个SHA>..<末个SHA>）
评审：<PASS / PASS 第N轮>
安全：<通过 / 发现N个Medium / 未执行>

### 质量变化
测试：<之前> → <之后>（<变化>）
Lint：<之前> → <之后>（<变化>）

### 沉淀
- <写入 lessons.md 的条目标题>

### 文档更新
- <更新的文档列表，或"无需更新">

### 历史参考（本次引用的经验教训）
- <引用的 lessons.md 条目，或"无">

### 环境工程备注
本次跑完 /lfg = 用了整套 Agent 运行环境（rules + commands + hooks + 分层记忆 + 审计 WAL）。
下一次任务会自动继承本次沉淀的教训（memory-index 已刷新）和变更审计（audit.jsonl 新增 N 条）。
— Environment Engineering 视角（Issue #34 / holaOS）
```

#### 10.4 待验证（需确认）

在 current-task.md 顶部标记 `## 状态：待验证`，向用户展示上面的完成报告并等待确认。
用户确认通过后，才执行 10.5（归档）和 10.6（关闭 Issue）。
用户反馈有问题 → 回到阶段 4 返工，不是新任务。

#### 10.5 归档与关闭

用户确认通过后：
1. 在 `.agent-harness/task-log.md` 追加完成记录（需求、做了什么、关键决策、改了哪些文件、完成标准）
2. 清空 `.agent-harness/current-task.md`（只保留标题和空模板）
3. **记录 WAL 审计**（两条都要写，task-lifecycle 硬要求）：
   ```bash
   .agent-harness/bin/audit append --file task-log.md --op append \
     --summary "归档任务：<任务一句话摘要>"
   .agent-harness/bin/audit append --file current-task.md --op update \
     --summary "清空，任务已归档到 task-log"
   ```

#### 10.6 关闭源 Issue（仅 Issue 驱动时）

如果本次 LFG 是由 Issue 编号触发的（`#N`、`gh#N` 或 `gl#N`），完成报告输出后**必须同步关闭所有远端的对应 Issue**：

**GitHub Issue**：
```bash
gh issue close <编号> --comment "✅ 已通过 /lfg 集成完成。提交：<首个SHA>..<末个SHA>"
```

**GitLab Issue 同步关闭**：完整脚本（按标签 + 标题匹配定位编号 → 评论 → 关闭）抽到 `.agent-harness/references/gitlab-issue-closure.md`。GitLab 触发的任务执行 `/recall --refs gitlab-issue-closure`，按脚本同步关闭。

> **禁止使用 GitLab API 的 `search=` 参数**——该参数对中文标题不可靠，必须用 `labels` 过滤后在本地做标题匹配（详见 reference）。
> 如果 `GITLAB_TOKEN` 未设置或 API 调用失败，告知用户"GitHub Issue 已关闭但 GitLab 同步失败"。

---

## 进度追踪与中断恢复

在 `.agent-harness/current-task.md` 中实时记录完整上下文。完整结构化字段示例（含 Goal / Context / Assumptions / Acceptance / Decisions / Files / Quality Baseline / Progress 共 8 段）已抽到 `.agent-harness/references/lfg-progress-format.md`。

加载方式：进入阶段 4 实施或恢复中断时，运行 `/recall --refs lfg-progress-format` 复制结构。`/todo` 在阶段 3 生成的子步骤清单写入 Progress 段，逐项勾选。

**中断恢复**：下次打开 Claude Code 时，AI 读取 `current-task.md` 中的 LFG 进度块，从最后一个未完成阶段继续。验收标准、质量基线、计划路径等关键信息从 Context 段恢复，确保无缝衔接。

---

## 回滚机制

任何阶段都可以回滚。用户说"回退"时：

> **先串 `/careful`**：回滚都要用 `git reset --hard`，属于不可逆操作。每次回滚前先运行 `/careful` 做安全拦截确认——列出将被丢弃的 commit、未推送的改动、未保存的 worktree 文件，让用户肉眼过一遍再执行。

### 精确回滚（回退到某一步）

如果用户说"回退到第 N 步"：
1. 运行 `/careful`：展示 step-N 之后的 commit 列表，确认要丢弃
2. 在回滚前先打一个快照 tag `lfg/pre-rollback`（保护当前状态，让回滚本身也可撤销）
3. `git reset --hard lfg/step-N`（在工作分支上）
4. 更新 `current-task.md` 进度，将第 N+1 步之后的 checkbox 改回 `[ ]`
5. 从第 N+1 步继续

### 全量回滚（回退到任务开始前）

1. 运行 `/careful`：展示整个任务的 commit 列表 + 未提交改动，确认要丢弃
2. 在回滚前先打一个快照 tag `lfg/pre-rollback`
3. 读取 `current-task.md` 中记录的基线 commit
4. `git reset --hard <基线commit>`（在工作分支上）或删除 worktree
5. 清理 `current-task.md` 中的 LFG 进度和所有 `lfg/*` tag
6. 告知用户已回退到任务开始前的状态

### 撤销回滚

如果回滚后发现不应该回滚，可以 `git reset --hard lfg/pre-rollback` 恢复到回滚前的状态。

**绝不在主分支上执行 `git reset --hard`。** 如果在主分支工作且需要回滚，使用 `git revert` 逐个撤销 commit。

---

## 技能覆盖清单（自检用）

本流水线在各阶段串起下列技能，形成"单入口驱动全框架"的闭环。**新增技能只改 `templates/superpowers/skills-registry.json`，不要直接编辑此处**——下表由 registry 自动渲染。

| 阶段 | 调用的技能 |
|---|---|
| 0.2 历史加载 | `/recall` |
| 1 环境准备 | `/use-worktrees`、`/careful` |
| 2 构思 | `/ideate`、`/brainstorm` |
| 2.5 规格 | `/spec` |
| 3 计划 | `/adr`、`/write-plan`、`/plan-check`、`/agent-design-check`、`/todo`、`/source-verify` |
| 4 实施 | `/debug`、`/tdd`、`/execute-plan`、`/dispatch-agents`、`/squad`、`/subagent-dev` |
| 5 评审 | `/multi-review`、`/request-review` |
| 6 修复 | `/multi-review`、`/receive-review` |
| 7 验证 | `/verify`、`/cso` |
| 7.3 穷举验证 | `/recall` |
| 9 沉淀 | `/compound`、`/lint-lessons` |
| 10 收尾回滚 | `/careful` |
| 10 收尾 | `/git-commit`、`/doc-release`、`/finish-branch` |
| 元任务（非单任务流，不由 /lfg 驱动） | `/lfg`（self-reference would be infinite recursion）、`/which-skill`（meta skill-selector, peer to /lfg）、`/write-skill`（manually invoked when authoring new skills）、`/evolve`（periodic self-evolution, reverse-triggers /lfg via evolution Issues）、`/health`（periodic code-quality snapshot, not part of single-task flow）、`/retro`（periodic engineering retrospective）、`/process-notes`（product-notes processing, different domain）、`/digest-meeting`（meeting-transcript processing, upstream of /lfg (produces current-task.md as input, not a pipeline stage)）、`/pressure-test`（periodic skill TDD (monthly + on anti-rationalization table additions), orthogonal to /lfg single-task pipeline） |

> 如果用户问"某某能力在 /lfg 里怎么用"，查本表；找不到说明这个能力不走 /lfg，按上表最后一行处理或直接用 CLI（`harness init/upgrade/doctor/export/stats/sync/memory rebuild/squad`）。
> 一致性由 `harness skills lint .` 在 CI 中强制保证。
