# 使用 Git Worktree 进行隔离开发

你的任务是为当前任务创建一个干净的 Git worktree 工作环境，确保主分支不受影响。

项目：`Agent Harness Framework`（cli-tool，python）

## 铁律

- **绝不跳过 .gitignore 验证**——worktree 目录必须被 git 忽略
- **基线测试失败时，必须获得用户许可才能继续**

## 第 1 步：选择 Worktree 存放目录

按以下优先级系统性地选择目录：

1. **检查已有约定**：查找项目根目录下是否存在 `.worktrees/` 或 `worktrees/` 目录
2. **检查 CLAUDE.md**：读取 CLAUDE.md 中是否有 worktree 目录偏好设置
3. **默认位置**：使用 `.worktrees/`
4. 如果以上都不明确，**询问用户**偏好

## 第 2 步：安全验证

确认 worktree 目录被 git 忽略：

```bash
git check-ignore -q <选定目录>
```

- 如果**未被忽略**：将该目录追加到 `.gitignore`，然后再次验证
- 如果验证仍失败，**停止并报告问题**，不要继续

## 第 3 步：检测项目名称与分支

1. 从当前目录名或 `package.json` / `pyproject.toml` 等配置文件中检测项目名称
2. 确认当前所在分支（记录为基础分支）
3. 根据任务描述生成分支名，格式：`wt/<简短描述>`

## 第 4 步：创建 Worktree

```bash
git worktree add <目录>/<分支名> -b <分支名>
```

创建后立即验证：
- worktree 目录存在
- 新分支已创建
- 工作目录已切换到 worktree

## 第 5 步：项目初始化

在 worktree 中执行项目安装：

- **Node.js**：`npm install` 或 `pnpm install`
- **Python**：`pip install -e .` 或 `poetry install`
- **其他**：根据 cli-tool 执行对应的安装命令
- 如果项目有 `PYTHONPATH=src python -m agent_harness.cli`，确认能正常启动（快速验证后停止）

## 第 6 步：基线测试

运行基线测试确保 worktree 环境健康：

```bash
python -m unittest discover -s tests -v
```

根据测试结果：
- **全部通过**：报告成功，准备开始开发
- **有失败**：列出失败的测试，**询问用户是否继续**（可能是已知问题）
- 未经用户许可，**绝不在测试失败时默认继续**

## 第 7 步：状态报告

向用户展示完整报告：

```
## Worktree 创建完成

- 位置：<完整路径>
- 分支：<分支名>（基于 <基础分支>）
- 安装状态：成功/失败
- 基线测试：N 通过 / M 失败
- 下一步建议：开始实现 / 先修复失败测试
```

## 注意事项

- 完成工作后使用 `/finish-branch` 命令处理分支合并和清理
- 如果需要同时进行多个任务，可以创建多个 worktree
- worktree 之间共享 git 历史，但工作目录完全隔离
