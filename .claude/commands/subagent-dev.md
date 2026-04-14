# 子代理驱动开发

将已定稿的计划拆分为独立任务，逐个委派给全新的子代理执行，通过双阶段审查确保质量。

## 适用场景

- 已有经过审批的完整计划
- 任务之间大部分是独立的
- 每个任务有明确的输入和输出边界
- 项目：Agent Harness Framework（cli-tool，python）

## 不适用场景

- 计划尚未定稿
- 任务之间存在复杂的依赖链
- 需要跨任务共享大量上下文

## 每个任务的执行流程

### 1. 派遣实现者子代理

为每个任务创建**全新的**子代理。派遣时必须使用以下**角色声明格式**，明确子代理的能力边界：

```markdown
## 子代理角色声明

**角色**：<implementer | fixer | researcher>
**任务**：<精确描述和验收标准>
**允许的工具**：<file_read, file_write, file_edit, bash, grep, glob, test_command, check_command>
**禁止的工具**：<delegate, ask_user, memory_write, git_push, file_delete>
**可修改文件**：<文件路径列表>
**禁止修改文件**：<文件路径列表>
**步骤预算**：<N 步（不超过总预算 30%）>
**测试命令**：`make test`
**检查命令**：`make check`
```

每个子代理**必须**包含完整的角色声明，不得省略任何字段。这确保子代理从诞生起就有明确的能力边界，而非依赖自由裁量。

### 2. 接收实现结果

子代理必须返回以下状态之一：

| 状态 | 含义 | 后续动作 |
|------|------|----------|
| `DONE` | 任务完成，所有测试通过 | 进入审查 |
| `DONE_WITH_CONCERNS` | 完成但有疑虑 | 记录疑虑，进入审查 |
| `NEEDS_CONTEXT` | 缺少必要上下文 | 补充上下文后重新派遣 |
| `NEEDS_PERMISSION` | 需要确认类操作（删除文件、修改配置等） | 父代理决策：批准并补充到角色声明，或拒绝并调整方案 |
| `BLOCKED` | 遇到无法解决的阻塞 | 停止，上报阻塞问题 |

> **权限上报机制**：子代理遇到超出角色声明范围的操作时，不得自行执行，必须返回 `NEEDS_PERMISSION` 并说明需要什么权限、为什么需要。父代理作为唯一的用户交互入口，决定是否批准。

### 3. 双阶段审查（严格顺序）

**第一阶段：规格合规审查**

- 实现是否满足任务描述的所有要求
- 是否符合 Agent Harness Framework 的接口约定
- 是否遗漏了边界情况
- `make test` 是否全部通过

**第二阶段：代码质量审查**

- 代码风格是否符合项目规范
- 是否存在不必要的复杂性
- 是否有性能或安全隐患
- `make check` 是否通过

**绝不跳过或调换两个审查阶段的顺序。**

### 4. 修复循环

如果审查发现问题：

1. 创建修复任务描述，包含具体问题和期望修复
2. 派遣**新的修复子代理**——绝不手动修复
3. 修复后重新执行双阶段审查
4. 重复直到两个阶段都通过

### 5. 标记完成

审查通过后在 `.agent-harness/current-task.md` 中标记完成。

## 核心规则

- **父代理角色分离**：父代理只做三件事——**理解需求、分发任务、审查结果**。不直接编写业务代码。如果审查发现问题，派遣修复子代理而非自己动手
- **隔离性**：子代理之间不共享状态，每个子代理从干净的上下文开始
- **不手动修复**：发现问题永远派遣修复子代理，不自己动手改
- **审查顺序**：先规格合规，再代码质量，绝不反过来
- **完整上下文**：派遣时提供自包含的完整信息，不依赖子代理自行探索
- **状态追踪**：每个任务的状态变化都记录在进度文件中

## 安全约束

### 工具黑名单

子代理**禁止**执行以下操作，防止递归委派和不可控副作用：
- 再次委派子代理（禁止递归派遣）
- 向用户提问（clarify/ask，由父代理统一协调）
- 写入 memory/lessons（由父代理在任务完成后统一沉淀）
- 执行 git push、关闭 Issue 等影响远端状态的操作
- 删除文件或目录（只能创建和修改）

### 深度限制

最多 2 层委派：父代理 → 子代理 → **禁止再派遣**。如果子代理遇到需要进一步拆分的问题，必须返回 `NEEDS_CONTEXT` 由父代理处理。

### 预算共享

父代理和所有子代理共享同一个迭代预算。派遣子代理时必须分配明确的步骤上限（建议：单个子代理不超过总预算的 30%）。子代理耗尽预算时必须返回当前进度，不得静默停止。

## 进度追踪

```markdown
## 任务 [编号]: [名称]
- 实现者状态：DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- 规格审查：通过 | 未通过（原因）
- 质量审查：通过 | 未通过（原因）
- 修复轮次：0
- 最终状态：completed | blocked
```

## 子 agent 日志隔离（Issue #14）

计划者（主 agent）读 current-task，实现者（子 agent）写自己的 diary：

```bash
# 实现者启动时
harness agent init impl-<taskN>
harness agent status impl-<taskN> "开始实现任务 N"

# 实现过程中
harness agent diary impl-<taskN> "读完了 src/foo.py，准备改 bar 函数"
harness agent diary impl-<taskN> "测试 test_bar_x 失败，原因 <分析>"

# 完成后
harness agent status impl-<taskN> "DONE，待审查"
```

计划者（主 agent）回读：

```bash
harness agent list                     # 看所有实现者状态
harness agent aggregate impl-task1 impl-task2   # 读指定实现者 diary
```

**禁止**子 agent 直接写 current-task.md / task-log.md — 主 agent 基于 aggregate 决定哪些要归档进主档。

## 三角色模式（Orchestrator / Explorer / Coder，Issue #30）

复杂任务可采用更严格的**三角色分权模式**（吸收自 multi-agent-coding-system，TerminalBench #13）。与 `/squad` 的 capability 分权对齐：

| 子代理角色 | 能做什么 | **禁止** |
|---|---|---|
| **Orchestrator**（父代理） | 理解需求、派工、维护 context store、审查 | 直接读写业务代码（角色纪律） |
| **Explorer**（调查员子代理） | Read/Grep/Glob/Bash 只读探查 | Write/Edit/MultiEdit/NotebookEdit |
| **Coder**（实现者子代理） | 聚焦任务的读写实现 | 不看全局、不做架构决策 |

**何时采用**：任务涉及 5+ 文件、跨模块、或需要先探索后实现。简单任务仍用原"实现者 + 审查"双阶段即可。

**知识制品（context store）**：子代理完成时返回**结构化 artifact**，而不是自由日志。父代理用 `harness agent aggregate` 读取顶部 Artifacts 段，在派下一个子代理时按 summary 挑选需要复用的制品，在 prompt 中显式引用（`context_refs: [explorer-auth/exploration-1]`）。

```bash
# Explorer 子代理完成探索后
harness agent artifact explorer-auth \
  --type exploration \
  --summary "auth 模块走 JWT HS256，密钥从 env 读" \
  --content "详细发现..." \
  --refs "src/auth/jwt.py,src/auth/__init__.py"

# Coder 子代理启动前，父代理回读并在 prompt 注入
harness agent aggregate explorer-auth
```

这是"并行干活 → 累积智能"的关键：每个子代理的发现都可被后续子代理 refs 复用，不用重复 grep。
