# Current Task

## 任务目标

Issue #21（合并了原 #20 + 原 #21）：SQLite mailbox 数据层 + 最小可用 coordinator 常驻进程（`harness squad watch`）。JSONL 作为调试 dump 格式保留。

## LFG 进度

### Context
复杂度：大 | 通道：标准（合并版已简化，跳过构思）| 基线 commit：940d21a | 工作分支：feat/squad-mailbox-coordinator-issue-21 | 基线 364/364

### Source-Verify 结论
- `sqlite3` WAL 模式：`PRAGMA journal_mode=WAL` 返回 `wal` 字符串，副文件 `.db-wal` / `.db-shm`
- `check_same_thread=False` 允许跨线程 Connection（但需自己加锁）
- Row factory：`conn.row_factory = sqlite3.Row`
- 跨 connection 读能看到已 commit 数据（WAL 的核心特性）

### Assumptions
- 一刀切迁移，status.jsonl 不再写，已有文件保留供 dump
- 4 类事件 + info/error = 6 个 type 值，预留可扩展
- coordinator 用 `subprocess.Popen + nohup`，不做真 daemon
- SIGTERM 处理 = 关 db connection + 退出，无 PID 文件
- watch 单 task_id，多 squad 多进程

### Acceptance
1. mailbox.py 存在，WAL 模式可用
2. state.py 签名不变，内部切换
3. coordinator.py 新增 cmd_watch 常驻
4. cmd_watch 轮询 → 自动 advance（mock 测试）
5. harness squad dump 导出 JSONL
6. .gitignore 规则
7. 19a 的 17 条不 regression
8. 新增 12+ 测试
9. 文档同步

### Progress
- [x] A 环境准备 + source-verify（WAL/thread/row 通过）
- [ ] B mailbox.py 核心
- [ ] C state.py 适配
- [ ] D cmd_watch 常驻进程
- [ ] E cmd_dump + .gitignore
- [ ] F 测试
- [ ] G 文档
- [ ] H 归档 + merge + 关 Issue
