# Current Task

## 状态：待验证

## 任务目标

将项目中分散的输入校验逻辑（agent.py `_AGENT_ID_RE`、squad/spec.py `_NAME_PATTERN`、各处 `is_relative_to` 路径检查）统一到新的 `src/agent_harness/security.py` 模块，提供 `sanitize_name` / `sanitize_path` / `sanitize_content` + `SecurityError`。来源：Issue #15（吸收自 MemPalace）。

## LFG 进度

### Context
复杂度：中 | 通道：标准 | 基线 commit：5a3f694 | 工作分支：feat/security-sanitize-issue-15

### Assumptions
- 假设：只做代码化，不加新校验维度 | 依据：最小实现原则
- 假设：sanitize_name 正则 `^[a-z0-9][a-z0-9-]{0,30}$` | 依据：与现有 agent/squad 对齐
- 假设：SecurityError 继承 ValueError | 依据：向后兼容现有 except 块
- 假设：oversize 抛异常、null 剥除、控制字符剥除（保留 `\n\t\r`）| 依据：用户确认
- 假设：本次不含 POSIX 权限检查 | 依据：跨平台风险
- 假设：改造点仅 agent.py + squad/spec.py | 依据：最小侵入

### Acceptance
1. 新增 security.py 导出三个函数 + SecurityError
2. agent.py + squad/spec.py 改用 sanitize_name
3. 新增 test_security.py 覆盖三类场景（正常/边界/错误）
4. 现有 304 测试 + make check 全绿
5. docs/architecture.md + docs/product.md 同步更新

### Progress
- [x] 环境准备 — 分支已建，基线 304/304 绿
- [x] current-task.md 已写
- [x] RED：tests/test_security.py（25 条）
- [x] GREEN：security.py 实现（119 行）
- [x] 重构 agent.py + squad/spec.py（去重重复正则）
- [x] 回归测试 + 文档同步（329/329 绿，docs 测试数从 304→329）
- [x] 穷举攻击验证（8/8 路径遍历向量全阻止）
- [x] 沉淀 2 条架构教训到 lessons.md + memory-index
- [ ] 用户验证 + 归档 task-log
