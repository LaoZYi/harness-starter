# Current Task

## 状态：进行中

## LFG 进度

### Goal
深入分析代码发现潜在问题并修复，最后全量同步文档。

### Context
复杂度：中 | 通道：标准 | 基线 commit：eaa31b2 | 工作分支：fix/code-health-audit-2026-04-13

### Acceptance
1. squad/cli.py ≤ 280 行
2. check_repo.py 自动覆盖 src/agent_harness/ 下所有 .py（含 squad/）
3. 新增回归测试锁死"新模块自动入检"契约
4. tmux.py 使用 shutil.which 的返回路径
5. make ci 全通过（234 → 235+）
6. docs/architecture.md、CHANGELOG、lessons 同步更新

### Progress
- [x] 理解与评估
- [x] 环境准备（分支 fix/code-health-audit-2026-04-13）
- [ ] 实施 step 1：拆分 squad/cli.py
- [ ] 实施 step 2：改 check_repo.py 自动扫描
- [ ] 实施 step 3：修 tmux.py which
- [ ] 实施 step 4：新增契约测试
- [ ] 自检 + 评审 + 验证
- [ ] 文档同步
- [ ] 沉淀 + 归档
