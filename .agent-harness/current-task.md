# Current Task

## LFG 进度

### Goal（目标）
`harness init --scaffold` 扩展到支持远端 git 仓库 URL，自动检测 local-path vs git-url，加 `--scaffold-ref` 和 `--scaffold-subdir`。

### Context（上下文）
复杂度：中 | 通道：标准 | 基线 commit：6b37b54 | 工作分支：feat/scaffold-from-git-20260421

### Assumptions（假设清单）
- 假设：单 flag 自动检测（Option A）| 依据：向后兼容 + UI 简洁
- 假设：shallow clone (`--depth 1`) | 依据：模板不需要历史
- 假设：鉴权走 git 全局配置（SSH key / credential helper），不传 token | 依据：安全 + 零依赖
- 假设：临时目录 clone + 复制后清理 | 依据：不在 target 留 .git
- 假设：失败清晰报错，不 fallback | 依据：明确失败优于静默降级
- 假设：测试用本地 bare repo 模拟远端 | 依据：CI 无外网

### Acceptance（验收标准）
- R-001 `--scaffold <value>` 自动检测 git URL（`http(s)://` / `git@` / `ssh://` / `git://` 前缀或 `.git` 后缀）
- R-002 `--scaffold-ref <branch|tag|commit>` 可指定 git ref（默认仓库默认分支）
- R-003 `--scaffold-subdir <relpath>` 可指定 clone 仓的子目录作为模板源（默认仓根）
- R-004 `copy_scaffold_from_git()` 实现：shallow clone → 可选 checkout ref → 可选截取 subdir → 复制 → 删 tmpdir
- R-005 5 类失败路径中文报错：git 未装 / 网络 / 仓库 404 / ref 不存在 / subdir 不存在
- R-006 `ask_scaffold` 新增「是，从远端 git 仓库拉取」分支
- R-007 测试用本地 bare repo 模拟远端；正常路径 + ref + subdir + 4 类失败各至少 1 条
- R-008 文档：CHANGELOG + docs/runbook.md + docs/architecture.md（测试计数）+ docs/product.md（功能列表）

### Quality Baseline（质量基线）
- 测试：543 个，100% 通过
- make test：12.8s
- make check / lint / typecheck：全绿

### Progress（阶段进度）
- [x] 理解与评估 — 复杂度：中，通道：标准
- [x] 环境准备 — 分支 feat/scaffold-from-git-20260421，基线 543/543
- [x] 规格 — docs/superpowers/specs/2026-04-21-scaffold-from-git-spec.md
- [x] 计划 + /plan-check — docs/superpowers/specs/2026-04-21-scaffold-from-git-plan.md
- [x] /cso 快速扫 — subdir 路径遍历作为安全约束写入 Step 4
- [x] ADR 0003 — Accepted
- [x] 实施 — _scaffold_git.py（131 行）+ cli.py 分派 + ask_scaffold 扩展 + 17 条测试 + 6 份文档同步
- [x] 自检 + 验证 — R-ID 8/8 satisfied；make ci 560/560 pass
- [ ] 提交
- [ ] 待用户确认

## 状态：待验证
