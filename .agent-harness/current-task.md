# Current Task

## 任务目标

吸收 gsd-build/get-shit-done 的三件套（上下文监控 Hook + /plan-check + 需求 ID 映射）+ OpenSwarm 加料（StuckDetector + 矛盾检测），全部一次性落地。Issue #17。

## LFG 进度

### Context
复杂度：大 | 通道：完整 | 基线 commit：fb2607e | 工作分支：feat/gsd-absorb-issue-17 | 基线测试：329/329

### Assumptions
- Hook 用 shell 不用 JS | 依据：本项目 hook 统一 shell
- R-ID 用 R1/R2；测试 ID 复用 R-ID | 依据：Issue 未指定，从简
- /plan-check 采用 Issue 原文 8 维度 | 依据：用户同意按建议
- Claude Code statusline 若不支持 context remaining → 第 1 项标 out-of-scope | 依据：降级不 hack
- 每阶段一个 atomic commit + lfg/step-N tag | 依据：可精确回滚

### Acceptance
1. StuckDetector 规则在 task-lifecycle / tdd / debug 三处生效
2. /lint-lessons 能检出矛盾候选
3. /spec 产出需求矩阵（R-ID）
4. /write-plan 每步标 R-ID
5. /verify 硬检查 R-ID 覆盖
6. /plan-check 能检出 bad plan
7. Hook 若 API 支持则落地；否则明确标 out-of-scope
8. 所有新增/修改技能同步到 /lfg 覆盖表
9. 测试数同步（329→~345）
10. make ci 全绿

### Progress
- [x] A 准备环境
- [ ] B StuckDetector 规则
- [ ] C /lint-lessons 矛盾检测
- [ ] D 需求 ID 三元映射
- [ ] E /plan-check 新技能
- [ ] F Hook（含 source-verify）
- [ ] G 测试新增
- [ ] H 文档同步
- [ ] I 沉淀 + 归档 + 关 Issue
