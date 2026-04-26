# Current Task

## 状态:待验证

## LFG 进度

### Goal(目标)
吸收 forrestchang/andrej-karpathy-skills 的 Simplicity First + Surgical Changes 原则,补足 anti-laziness 偏"防偷懒"缺"反过度工程化"的另一极(GitHub #51 / GitLab #25)。

### Context(上下文)
复杂度:中-大 | 通道:完整(evolution) | 基线 commit:e5271e6 | 工作分支:feat/evolution-51-simplicity

### Acceptance(验收标准)
1. R-001 新 rule simplicity.md 存在 + Karpathy 4 原则核心
2. R-002 与 anti-laziness 边界明确(反偷懒 vs 反过度工程化)
3. R-003 与 safety「改一处查所有同类」边界明确
4. R-004 转换模板进入 requirement-mapping-checklist
5. R-005 lfg.md 3 处引用
6. R-006 make ci exit 0 + 测试计数同步
7. R-007 lfg audit 不退步(基线 14.85/15)

### Quality Baseline(质量基线)
- 测试:647 passed | mypy clean | ruff clean
- audit Dim:14.85/15

### Files(涉及文件)
- 新建:`templates/common/.claude/rules/simplicity.md.tmpl` + `.claude/rules/simplicity.md`
- 改:`templates/common/.claude/rules/{agent-design,anti-laziness}.md.tmpl`
- 改:`templates/common/.agent-harness/references/requirement-mapping-checklist.md.tmpl`
- 改:`templates/superpowers/.claude/commands/lfg.md.tmpl`
- 加测试:`tests/test_lfg_simplicity_absorption.py`

### Artifacts touched(本次操作过的产物路径)
(实施期填充)

### Progress(阶段进度)
- [x] 0.1 任务理解 — evolution 模式
- [x] 0.2 历史加载
- [x] 1 环境准备 — feat/evolution-51-simplicity,基线 647 tests pass
- [x] 3 计划 — 7 步,用户确认"走"
- [x] 4.1 步骤 1:新建 simplicity.md.tmpl
- [x] 4.2 步骤 2:改 agent-design.md.tmpl F11
- [x] 4.3 步骤 3:改 requirement-mapping-checklist.md.tmpl
- [x] 4.4 步骤 4:改 anti-laziness.md.tmpl 边界声明
- [x] 4.5 步骤 5:改 lfg.md.tmpl 3 处
- [x] 4.6 步骤 6:加契约测试
- [x] 4.7 步骤 7:dogfood + make ci
- [ ] 9 沉淀
- [ ] 10 收尾
