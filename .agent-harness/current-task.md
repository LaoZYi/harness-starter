# Current Task

## LFG 进度

### Goal（目标）
Issue #18：实现 `/squad` MVP — tmux + worktree + capability 分权的多 agent 常驻协作能力。

### Context（上下文）
复杂度：大 | 通道：完整（跳过阶段 2/2.5/3，spec+plan 已有）| 基线 commit：`60d4a07` | 工作分支：`feat/squad-mvp`
Spec：`docs/superpowers/specs/2026-04-12-squad-mvp-spec.md`
Plan：`docs/superpowers/specs/2026-04-12-squad-mvp-plan.md`

### Assumptions（假设清单）
- 假设：Claude Code CLI 有 `--prompt-file` 或等价的 prompt 注入方式 | 依据：待步骤 0 /source-verify 验证
- 假设：pyyaml 已在依赖中 | 依据：待验证 pyproject.toml
- 假设：tmux ≥ 3.0 可作为硬依赖 | 依据：主流 macOS/Linux 标配
- 假设：`permissions.deny` 字段能阻止指定工具 | 依据：Claude Code 原生能力（已在 spec 中引用）
- 假设：`/dispatch-agents` 不替换，两者并存 | 依据：spec 决策
- 假设：worker 禁写共享 lessons.md（只能写 workers/<name>/lessons.pending.md）| 依据：避免写入冲突

### Acceptance（验收标准）
见 spec "验收标准" 10 条 + plan "完成标准"

### Decisions（关键决策）
- YAML 格式 spec 文件；worker prompt 强制注入 squad 上下文前缀
- `/squad create` 不自动跑 /spec；禁止嵌套 squad
- 自研 MVP（不包 claude-squad）；JSONL + fcntl（不引入 SQLite）
- tmux 硬依赖，阶段 1 不降级
- 历史参考：2026-04-12「脚手架项目吸收外部思想要选最小实现」/「新增技能时文档散布计数需全量扫描」；memory: LFG must integrate new skills、测试必须一次性穷举

### Files（涉及文件）
模板：
- `src/agent_harness/templates/superpowers/.claude/commands/squad.md.tmpl`
- `src/agent_harness/templates/common/scripts/squad/squad.py.tmpl`
- `src/agent_harness/templates/common/scripts/squad/capability_templates/{scout,builder,reviewer}.json.tmpl`
- `src/agent_harness/templates/common/.agent-harness/squad/README.md.tmpl`

决策树/流程：
- `src/agent_harness/templates/superpowers/.claude/commands/use-superpowers.md.tmpl`
- `src/agent_harness/templates/superpowers/.claude/commands/lfg.md.tmpl`
- `src/agent_harness/templates/common/.claude/rules/superpowers-workflow.md.tmpl`

文档：
- `docs/product.md` / `docs/architecture.md` / `docs/runbook.md` / `AGENTS.md` / `CHANGELOG.md`

测试：
- `tests/test_squad_spec_parse.py`
- `tests/test_squad_capability.py`
- `tests/test_squad_tmux_mock.py`

### Quality Baseline（质量基线）
- 测试：待步骤 1 基线收集
- Lint / check：待步骤 1 基线收集

### Progress（阶段进度）
- [x] 理解与评估 — 复杂度：大，通道：完整（跳过构思/规格/计划阶段）
- [ ] 环境准备 — 基线测试 + source-verify
- [x] 规格定义 — `2026-04-12-squad-mvp-spec.md`（已 commit 60d4a07）
- [x] 计划 — `2026-04-12-squad-mvp-plan.md`（已 commit 60d4a07）
- [ ] 实施（plan 13 步，当前步骤 2 进行中）
  - [x] 步骤 0：source-verify + 依赖摸底（发现 --prompt-file 不存在，改用 --append-system-prompt + positional arg；tmux 3.6a / pyyaml>=6.0 OK；基线 206 测试）
  - [x] 步骤 1：TDD RED — 测试骨架（3 文件、20 用例、全部 ImportError 确认 RED）
  - [x] 步骤 2：squad 核心实现（spec/capability/tmux/state/cli 5 模块 + harness CLI 注册）
  - [x] 步骤 3：capability 渲染（合并进 capability.py，不再需要独立 JSON 模板文件 — plan 偏离记入附录）
  - [ ] 步骤 4：squad.md 技能
  - [ ] 步骤 5：决策树 + LFG 流水线更新
  - [ ] 步骤 6：TDD GREEN
  - [ ] 步骤 7：dogfood 同步
  - [ ] 步骤 8：文档全量同步
  - [ ] 步骤 9：make ci 验证
  - [ ] 步骤 10：冒烟验证（可选）
  - [ ] 步骤 11：/multi-review
  - [ ] 步骤 12：完成报告 + 验收核验
  - [ ] 步骤 13：归档与收尾
- [ ] 自检
- [ ] 评审
- [ ] 修复（如需要）
- [ ] 验证
- [ ] 质量对比
- [ ] 沉淀
- [ ] 完成报告
- [ ] 待验证
- [ ] 归档与收尾
