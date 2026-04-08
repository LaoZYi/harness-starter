# 执行计划

按照已审批的计划逐步执行任务。严格遵循计划，遇到阻塞立即停止。

## 执行流程

### 第一步：加载并审查计划

1. 读取 `.agent-harness/plan.md` 中的完整计划
2. 批判性审查：确认每个任务的前置条件、预期输出和验证标准都明确
3. 如果计划存在歧义或缺失信息，**立即停止**并请求澄清
4. 确认当前分支不是 main/master（除非获得明确授权）

### 第二步：逐步执行

对每个任务：

1. 在 `.agent-harness/current-task.md` 中标记当前任务为 `in_progress`
2. 严格按照计划描述实现，不擅自扩展范围
3. 每完成一个原子操作就保存进度
4. 使用 `python -m unittest discover -s tests -v` 运行验证
5. 使用 `python scripts/check_repo.py` 检查代码质量

### 第三步：验证

每完成一步后必须验证：

- 运行 `python -m unittest discover -s tests -v` 确保测试通过
- 确认变更符合 Agent Harness Framework 的代码规范
- 检查是否引入了意外的副作用
- 确保 python 类型检查（如适用）通过

### 第四步：完成并过渡

所有任务完成后：

1. 在 `.agent-harness/current-task.md` 中标记为 `completed`
2. 编写变更摘要
3. 过渡到 `/finish-branch` 完成收尾工作

## 强制停止条件

遇到以下情况必须**立即停止**，不得猜测或绕过：

- **阻塞问题**：依赖的服务不可用、权限不足、环境配置缺失
- **缺失依赖**：计划引用了不存在的模块、接口或配置
- **测试失败**：`python -m unittest discover -s tests -v` 失败且原因不在当前任务范围内
- **指令不清**：任务描述存在多种合理解读
- **范围溢出**：发现需要修改计划未涉及的代码

## 关键原则

- 绝不在 main/master 上直接工作（除非明确授权）
- 绝不猜测缺失的需求——停下来问
- 绝不跳过验证步骤
- 绝不擅自扩大任务范围
- 每个任务都是原子的：要么完成，要么回退
- 项目类型：cli-tool，语言：python
- 启动命令：`PYTHONPATH=src python -m agent_harness.cli`

## 进度记录格式

```markdown
## 当前任务
- [ ] 任务名称
- 状态：in_progress | completed | blocked
- 开始时间：YYYY-MM-DD HH:MM
- 阻塞原因：（如有）
```
