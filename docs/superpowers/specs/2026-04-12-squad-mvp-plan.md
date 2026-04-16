# 实现计划：/squad MVP（阶段 1）

> 对应 Spec：`docs/superpowers/specs/2026-04-12-squad-mvp-spec.md`
> 对应 Issue：[GitHub #18](https://github.com/LaoZYi/harness-starter/issues/18)
> 基线 commit：`f69b975` | 分支：`feat/squad-mvp`

## 目标与范围

在 tmux 中起 N 个独立 Claude Code 进程（各自绑定一个 git worktree），按 capability（scout/builder/reviewer）强制工具权限，coordinator 通过 JSONL 文件观察 worker 状态。提供 `/squad create|status|attach|stop` 子命令。

**不做**（阶段 2/3 处理）：SQLite mailbox、FIFO 合并队列、AI 冲突裁决、AgentRuntime 抽象、tmux 降级、Windows 原生支持。

## 开放问题决策（已敲定）

1. spec 文件格式 → **YAML**
2. worker prompt 强制注入 squad 上下文前缀 → **是**
3. `/squad create` 自动跑 `/spec` → **否**
4. 允许嵌套 squad → **禁止**（对齐 dispatch-agents 递归禁令）

## 历史教训引用

- **2026-04-12「脚手架项目吸收外部思想要选最小实现」**：不包 claude-squad、不引入 SQLite，只做最轻验证层
- **2026-04-12「新增技能时文档散布计数需全量扫描」**：docs/product、architecture、runbook、AGENTS、CHANGELOG、which-skill 决策树、lfg 流水线必须同步
- **2026-04-09「命令重命名后模板文件也要全量扫描」**：squad.md.tmpl 改动后必须 dogfood 同步到 `.claude/commands/squad.md`
- **memory: LFG must integrate new skills**：`/squad` 必须出现在 `/lfg` 和 `/which-skill` 的决策路径里
- **memory: 测试必须一次性穷举**：tests 覆盖规格解析、依赖循环、capability 渲染、tmux 命令构造

## 依赖与前置验证

- **`claude --prompt-file` 是否存在**：`/source-verify` 验证 Claude Code CLI 的 prompt 注入方式；若 flag 不同，改为 `claude < prompt.md` pipe 或 `--append-system-prompt` 方案
- **tmux 版本**：要求 ≥ 3.0（`tmux -V`），否则 `/squad create` 拒绝启动
- **Python 版本**：沿用项目现有 `pyproject.toml` 约束
- **不新增重量依赖**：JSONL + `fcntl.flock`（stdlib），`yaml` 用 `pyyaml`（已在依赖里，需确认）

## 执行步骤

### 步骤 0：源验证 + 依赖摸底
命令：
```
/source-verify --topic "claude code cli prompt injection flags"
grep pyyaml pyproject.toml uv.lock  # 确认 pyyaml 已在依赖
tmux -V
```
产出：在 plan 底部附录记录 Claude Code 的正确启动 prompt 注入方式。

### 步骤 1：TDD RED — 先写测试骨架
文件：
- `tests/test_squad_spec_parse.py`
- `tests/test_squad_capability.py`
- `tests/test_squad_tmux_mock.py`

测试用例（阶段 1 至少 6 个）：

**test_squad_spec_parse.py**
1. `test_parse_valid_yaml_spec` — 合法 YAML 能解析出 workers 列表
2. `test_reject_circular_dependency` — `depends_on` 成环抛明确错误
3. `test_reject_unknown_capability` — capability 不是三选一抛错

**test_squad_capability.py**
4. `test_scout_settings_denies_write` — scout 模板渲染后 `permissions.deny` 包含 `Write`、`Edit`
5. `test_builder_settings_denies_remote_git` — builder 禁 `git push`、`rm -rf`
6. `test_reviewer_settings_denies_write` — reviewer 禁所有写操作

**test_squad_tmux_mock.py**
7. `test_tmux_command_construction` — mock `subprocess.run`，验证 `tmux new-session / new-window` 命令参数正确
8. `test_missing_tmux_raises` — `which tmux` 失败时抛友好错误

跑 `make test` 确认**全失败**（RED）。

### 步骤 2：实现 squad.py 核心
文件：`src/agent_harness/templates/common/scripts/squad/squad.py.tmpl`

结构：
```python
# 入口：python scripts/squad/squad.py <subcommand> [args]
# 子命令：create / status / attach / stop / gc
def cmd_create(spec_path: Path) -> int: ...
def cmd_status() -> int: ...
def cmd_attach(worker: str) -> int: ...
def cmd_stop(target: str) -> int: ...

# 内部模块
spec.py       # YAML 解析、循环检测
capability.py # settings.local.json 渲染
tmux.py       # tmux 命令封装（subprocess）
state.py      # manifest.json / status.jsonl 读写（fcntl.flock）
```

实现顺序：spec → capability → state → tmux → 子命令。每完成一个模块跑对应测试转 GREEN。

### 步骤 3：capability 模板
文件：
- `src/agent_harness/templates/common/scripts/squad/capability_templates/scout.json.tmpl`
- `src/agent_harness/templates/common/scripts/squad/capability_templates/builder.json.tmpl`
- `src/agent_harness/templates/common/scripts/squad/capability_templates/reviewer.json.tmpl`

每个文件是一份 `.claude/settings.local.json` 片段，`permissions.deny` 按 spec 的权限表填充。

### 步骤 4：写 `/squad` 技能
文件：`src/agent_harness/templates/superpowers/.claude/commands/squad.md.tmpl`

结构：
- 适用场景（长任务、需实时观察、需分权 — 对比 `/dispatch-agents` 的短独立子任务）
- 不适用场景（单 agent 够用、无 tmux 环境）
- spec YAML 格式规范（含示例）
- 4 个子命令用法
- 安全约束（嵌套禁令、capability 不可自行升级、worker 禁写共享 lessons.md）

### 步骤 5：更新决策树和 LFG 流水线
文件：
- `src/agent_harness/templates/superpowers/.claude/commands/which-skill.md.tmpl` — 加入 `/squad` 条目，明确与 `/dispatch-agents` 的选择标准
- `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl` — 在"实施阶段"章节加入：复杂任务可启动 `/squad` 分权并行
- `.claude/rules/superpowers-workflow.md`（模板：`src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md.tmpl`）— 技能表新增 `/squad` 行

### 步骤 6：TDD GREEN — 跑通所有测试
```
make test
```
所有 6+ 个新测试通过；现有 204 测试仍全过。

### 步骤 7：dogfood 同步
```
python scripts/dogfood.py
# 或 make dogfood（若有）
```
验证：
- `.claude/commands/squad.md` 出现
- `scripts/squad/squad.py` + capability_templates/ 出现
- `.agent-harness/squad/.gitkeep` 出现
- `diff` 与模板仅差模板变量

### 步骤 8：文档同步（全量扫描）
- `docs/product.md` — "框架提供什么"新增一条：多 agent 常驻协作（/squad）
- `docs/architecture.md` — 新增 `.agent-harness/squad/` 和 `scripts/squad/` 说明
- `docs/runbook.md` — 新增章节：tmux 安装 + `/squad create` 示例 + 故障排查
- `AGENTS.md` — 硬规则新增：禁止嵌套 squad；worker 禁写共享 lessons.md（只能写 `workers/<name>/lessons.pending.md`）
- `CHANGELOG.md` — Unreleased 段新增 `Added`：`/squad` MVP (#18)

### 步骤 9：check_repo + CI 全量验证
```
make check
make test
make ci
```
所有通过，新增测试至少 6 个，总数 ≥ 210。

### 步骤 10：冒烟验证（手动）
```
# 建一个 2-worker squad 跑最简任务
cat > /tmp/squad-smoke.yaml <<EOF
task_id: smoke
base_branch: feat/squad-mvp
workers:
  - name: scout-smoke
    capability: scout
    prompt: "echo scout ready > report.md"
EOF
python scripts/squad/squad.py create /tmp/squad-smoke.yaml
python scripts/squad/squad.py status
# tmux attach -t squad-smoke  # 手动观察
python scripts/squad/squad.py stop all
```
验证：tmux session 存在、worker 启动、状态更新、清理无残留。

> 若机器无 tmux，跳过此步，标注为"待环境验证"。

### 步骤 11：/multi-review
运行 `/multi-review`（正确性 + 测试完整性 + 安全 3 个审查员）。
重点审查：
- capability 的 deny 字段是否真能阻止越权（settings.local.json 字段名和语法）
- YAML 解析的输入信任边界（路径遍历、恶意 spec）
- tmux 命令构造是否有注入风险（worker 名含特殊字符）

### 步骤 12：完成报告 + 验收逐条核验
按 spec 的 10 条验收标准逐条核验 → 生成完成报告 → 等用户验证。

### 步骤 13：归档与收尾
- current-task.md 清空
- `.agent-harness/task-log.md` 追加一条
- `/compound` 提炼本次教训
- 合并到 master，关闭 Issue #18

## 风险与预案

| 风险 | 预案 |
|------|------|
| Claude Code `--prompt-file` 行为与假设不符 | 步骤 0 源验证兜底；备选 pipe / append-system-prompt |
| worker prompt 中 squad 上下文注入破坏 agent 正常推理 | 注入内容控制在 10 行内，只说"你是 squad 成员、capability=X、状态文件路径" |
| tmux 命令注入（worker 名含 `;` 或反引号） | `spec.py` 校验 worker 名正则 `^[a-z0-9][a-z0-9-]{0,30}$` |
| 多 worker 同时写 `.agent-harness/lessons.md` | AGENTS.md 规则禁止；worker 只能写 `workers/<name>/lessons.pending.md` |
| 旧项目 upgrade 时 `.agent-harness/squad/` 目录冲突 | `upgrade.py` 按 `three_way` 策略，默认跳过用户数据 |
| 测试环境无 tmux 导致 CI 失败 | tmux 测试全部 mock `subprocess`；冒烟步骤 10 允许跳过 |
| dogfood 后 `scripts/squad/` 被误认为模板源导致二次渲染 | dogfood.py 已处理；新增后验证 `.claude/commands/squad.md` 不含 `{{...}}` |

## 完成标准（对齐 spec Acceptance）

- [ ] `tmux` 未装时 `/squad create` 友好报错
- [ ] `depends_on` 循环被检测并拒绝
- [ ] scout/builder/reviewer 的 `settings.local.json` 经单元测试验证权限字段
- [ ] `/squad status` 无活跃 squad 时不崩
- [ ] worker worktree 完整独立
- [ ] 测试数 ≥ 210，新增 ≥ 6 个，`make ci` 全过
- [ ] docs/product + architecture + runbook + AGENTS + CHANGELOG 同步
- [ ] dogfood 无漂移（`scripts/dogfood.py --check` 通过）
- [ ] `/squad` 出现在 which-skill 决策树 + lfg 流水线
- [ ] spec 文档中 `/dispatch-agents` vs `/squad` 的选择标准清晰

## 附录：待步骤 0 填入

- Claude Code CLI prompt 注入的权威方式：**（步骤 0 完成后填）**
- tmux 最低版本：**（步骤 0 完成后填）**
- pyyaml 依赖状态：**（步骤 0 完成后填）**
