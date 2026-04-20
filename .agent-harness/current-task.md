# Current Task

## LFG 进度

### Goal（目标）
修复 gl#21：`make test` 在用户本地 git 配置（强制 worktree / 全局 hook）下报 27 ERROR + 1 FAIL。
通过在测试侧隔离全局 git config 让测试对本地环境健壮，并补文档防后来者踩坑。

### Context（上下文）
复杂度：小 | 通道：轻量 | 基线 commit：f06d734 | 工作分支：fix/test-git-env-isolation-20260420

### Assumptions（假设清单）
- 假设：27 ERROR 全部源自 `_git_helper.init_git_repo` 的 `git commit --allow-empty` 被用户全局 hook / `core.hooksPath` 拦截 | 依据：27 条栈帧完全重合
- 假设：1 FAIL (`test_git_commit_flag`) 同根因——`harness init --git-commit` 内部 `git commit` 被拦 → `cli_utils.py:201` 捕获后降级为 warning | 依据：现有 `test_git_commit_missing_identity_is_graceful` 已用 `GIT_CONFIG_GLOBAL=/dev/null` 隔离，有先例
- 假设：只改测试侧不改产品代码 | 依据：`maybe_git_commit` 失败时「保留 staged + 打印提示」本身是正确用户体验

### Acceptance（验收标准）
1. `make test` 全绿（527/527 pass）
2. `tests/_git_helper.py` 中所有 `subprocess.run` 均带 `env=_isolated_env()`
3. `tests/test_cli.py::_run_harness` env 含 `GIT_CONFIG_GLOBAL=/dev/null` + `GIT_CONFIG_SYSTEM=/dev/null`
4. `docs/runbook.md` 新增「本地 git 全局配置与测试」一节，指向 `_git_helper.py` 模式

### Progress（阶段进度）
- [x] 理解与评估 — 复杂度：小，通道：轻量
- [x] 环境准备 — 分支 fix/test-git-env-isolation-20260420
- [x] 实施 — `tests/_git_helper.py` + `tests/test_cli.py` + 新增 `tests/test_git_env_isolation.py`（2 条 TDD 契约，RED→GREEN 验证）+ `docs/runbook.md`「本地 git 全局配置与测试」节 + 测试计数 527→529 同步
- [x] 自检 — 验收 4/4 全过（make test 529/529、两处 env 带 GIT_CONFIG_GLOBAL=/dev/null、runbook 新节就位）
- [x] 快速评审 — 自审：TDD 有 RED/GREEN 证据、mechanical 变更、跳过子 agent 评审
- [x] 验证 — make test 529 pass / make check pass / make lint pass / mypy Success no issues
- [ ] 提交
- [ ] 待用户确认

## 状态：待验证（用户）
