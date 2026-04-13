# Current Task

## 任务目标

/squad 阶段 2 的第一部分：依赖触发 + 拓扑序启动（Issue #19 的 19a 子范围）。其他 3 项（SQLite mailbox / 持久 coordinator / watchdog）拆为 #19b/c/d，由本次完成后创建。

## LFG 进度

### Context
复杂度：中 | 通道：标准 | 基线 commit：2c2a27f | 工作分支：feat/squad-dependency-issue-19a | 基线 347/347

### Assumptions
- done 是显式事件（worker 写 status.jsonl 或 `harness squad done` 命令），不监听 tmux 窗口 exit
- manifest 不持久化 worker 状态，用三者对账（spec / status.jsonl / tmux 窗口）推导
- advance 幂等（tmux 已启动 → 跳过）
- 超时只警告不终止（kill 降级属 19c/d）

### Acceptance
1. 线性依赖链 scout→builder→reviewer 正确按顺序启动
2. 菱形依赖 scout→{builder,linter}→reviewer 的 reviewer 需两个前置都 done
3. advance 幂等
4. status 三态 + 阻塞时长 + 30min 超时警告
5. 阶段 1 测试 28/28 不 regression + 新增 10 条
6. 文档同步

### Progress
- [x] A 环境准备
- [ ] B tmux/state helper
- [ ] C cmd_create 改造
- [ ] D advance/done 命令
- [ ] E status 增强
- [ ] F 测试
- [ ] G 文档
- [ ] H 归档 + 拆分 + 关闭
