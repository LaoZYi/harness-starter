# Team-Implement — 实施编队

铁律：**先有计划，再写测试，再实现，最后验证。顺序不能颠倒。**

> **场景化预制流水线（吸收自 [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) `/team-*` 模式，Issue #55）**：
>
> 当任务进入「实施落地」阶段时，按本流水线串联 `/write-plan` → `/execute-plan` / `/tdd` → `/verify`，避免 orchestrator 临时编排导致漏步。
> 跟 `/lfg` 的关系：`/lfg` 是「需求 → 交付」全流程；`/team-implement` 是只覆盖**实施那一段**的局部编队，可独立调用，也可被 `/lfg` 阶段 3-4 引用。
> 走 D 方案：4 个 team-* skill 各自独立完整写一遍流水线，不抽共享 base（教训来自 lessons.md 2026-04-27）。

当前项目：`Agent Harness Framework`（cli-tool / python）
测试命令：`make test`
检查命令：`make check`

---

## 参数检查

如果 `$ARGUMENTS` 为空，输出：

> 用法：`/team-implement [任务目标 | 规格文档路径]` — 把已规格化的任务转为代码 + 测试 + 验证。

> 示例：`/team-implement docs/superpowers/specs/2026-04-27-multi-login-spec.md`、`/team-implement 加一个 healthcheck 端点`

然后**立即停止**，不进入流水线。

如果 `$ARGUMENTS` 是现有 spec 文档路径 → 直接读取作为输入；如果是文字描述 → 先确认有无 R-ID 验收标准，没有则建议先跑 `/team-spec`。

---

## 适用场景

- 已完成规格（含 R-ID 验收标准）的中等任务
- 改 3+ 文件，需要先排序步骤再动手
- 涉及业务逻辑 → 必须 TDD（先写测试再写代码）
- 配置 / 迁移 / 文档类改动 → 直接 execute-plan

**不适用**：
- 规格未定 → 先跑 `/team-spec`
- 单文件 typo / 配置值改动 → 直接改

---

## 编队组成

| 阶段 | 调用 skill | 产出 |
|---|---|---|
| 计划 | `/write-plan` | 计划文档（步骤、验证命令、文件清单） |
| 计划校验 | `/plan-check` | 8 维度结构化校验，最多 3 轮修订 |
| 实施 | `/tdd`（业务代码）/ `/execute-plan`（配置/迁移/文档） | 代码 + 测试 + commit |
| 验证 | `/verify` | 证据链报告（make test / make check / R-ID 核验） |

**注意**：`/tdd` 与 `/execute-plan` **二选一**——业务逻辑走 TDD，非业务改动走 execute-plan。本编队会按改动性质自动选择，也可由用户通过参数提示强制走某一路径。

---

## 流水线

### 阶段 1：计划

调用 `/write-plan`，输入是 `$ARGUMENTS`（spec 文档或任务描述）。

`/write-plan` 产出：
- 步骤清单（每步 2-5 分钟粒度）
- 文件清单（每步明确改哪些文件）
- 验证命令（每步有 make test / curl / grep 等可机械判定的检查）
- 完成标准（对照 R-ID 或验收条件）

### 阶段 2：计划校验

调用 `/plan-check`，输入是阶段 1 产出。

8 维度校验 + 最多 3 轮修订循环。3 轮未收敛 → **🔴 停下来**告诉用户阻塞点（计划本身有结构性问题，需重写或拆任务）。

**🔴 等用户确认计划**。计划不通过不进实施。

### 阶段 3：实施（路径分叉）

读计划，按改动性质选路径：

**路径 A：业务逻辑 / 算法 / 数据结构 → `/tdd`**
1. 先写测试（覆盖正常 / 边界 / 错误三类场景）
2. 跑测试 → 红
3. 写实现让测试变绿
4. 重构（保持测试绿）
5. 每步独立 commit + 打 tag `lfg/step-N`

**路径 B：配置 / 迁移 / 文档 / 依赖升级 → `/execute-plan`**
1. 按计划逐步执行
2. 每步跑验证命令
3. 每步独立 commit + 打 tag

**通用规则**：
- 每步执行后跑 `make test` 确认无回归
- 每步写一条 audit 日志（`.agent-harness/bin/audit append --file current-task.md --op update --summary "step N: <一句话>"`）
- 连续 3 步失败 → **🔴 停下来**回阶段 1 重做计划

**遇到「想顺手改邻居代码」的诱惑**：
- 禁止（违反 simplicity.md 准则 2 Surgical Changes）
- 提一句让用户决定，真要改走独立 `unplanned:` commit + 显式说明

### 阶段 4：验证

调用 `/verify`，产出证据链报告：
1. `make test` 全绿（记录测试数 / 耗时 / 新增测试）
2. `make check` 无新增警告
3. R-ID 三态核验（satisfied / out-of-scope / missed）
4. 关键路径穷举验证（如涉及数据安全 / 文件读写 / 升级迁移）

R-ID 任一为 `missed` → 回阶段 3 补实施。
R-ID 有 `out-of-scope` → 展示给用户确认。

### 阶段 5：签收

收集四阶段产物，输出 verdict：

```
## Team-Implement 编队报告

任务：<$ARGUMENTS>

### 阶段产出
- 计划：docs/superpowers/specs/<file>.md（步骤数：N）
- plan-check：PASS（第 X 轮通过）
- 实施路径：TDD / execute-plan
- Commit：<N> 个（首 SHA..尾 SHA）+ tag lfg/step-1..lfg/step-N
- 验证：make test 全绿（X tests）/ R-ID 核验（M satisfied，0 missed）

### 后续动作建议
- → `/team-review` 进入评审
- → 或直接 `/multi-review` 单步评审
```

---

## 错误恢复协议

任一阶段返回 BLOCKED / 错误 / 无法完成时：

1. **立即上报**：`[<阶段>]: BLOCKED — <理由>`
2. **评估依赖**：本阶段是否阻塞下一阶段？阻塞则不强行推进
3. **三选一让用户决策**：
   - **跳过当前阶段**：标注 gap，部分推进
   - **回退到上一阶段重试**：缩范围 / 改方向
   - **停下解决**：先排障再继续
4. **始终产出部分报告**

常见阻塞：
- 阶段 1：spec 缺关键信息 → 回 `/team-spec` 补规格
- 阶段 2：plan-check 3 轮未收敛 → 计划本身有结构性问题，回阶段 1 重写
- 阶段 3：连续 3 步失败 → 计划方向错，回阶段 1
- 阶段 4：R-ID missed → 回阶段 3 补实施；多次补仍 missed → 回阶段 1 重审 spec

---

## 文件写入约定

- 本编队**会**写代码 + 测试 + 文档同步
- 每个 sub-skill 自己负责文件写入；本编队串联调度
- 写入路径白名单：
  - `src/`、`tests/`（业务代码 + 测试）
  - `docs/superpowers/specs/`（计划文档）
  - `docs/`（文档同步，按 documentation-sync 规则）
  - `.agent-harness/current-task.md`、`audit.jsonl`（进度 + 审计）
- 禁止写入：`AGENTS.md`、`CLAUDE.md`、`.claude/rules/`（不是实施阶段该碰的元规则）

---

## 输出

**verdict 三态**：
- **COMPLETE** — 计划 + 实施 + 验证齐备，R-ID 全 satisfied，测试全绿
- **PARTIAL** — 部分 R-ID satisfied + 部分 out-of-scope（用户确认）
- **BLOCKED** — 在阶段 X 阻塞，需用户介入

---

## 下一步建议

- 实施完成 → `/team-review` 多视角评审 + 安全审计 + 反馈消化
- 紧急 hotfix 跳过评审 → 直接 `/git-commit` + `/finish-branch`（需用户显式授权）
- 走完整 lfg 流水线 → 把本编队产物作为 `/lfg` 阶段 4 输入
