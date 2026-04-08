---
description: 操作权限分级和自治边界
---

# 自治规则

操作按风险分为三级，级别越高越需要用户确认：

## 自由操作（无需确认）

- 读取任何项目文件
- 运行 `python -m unittest discover -s tests -v`、`python scripts/check_repo.py`
- 在 `.agent-harness/` 下更新 current-task.md、task-log.md、lessons.md
- 更新 `docs/` 下的 checkbox 打勾状态
- 填充文档中的"待补充"占位符

## 需要谨慎的操作（正常执行，但出错时必须归因）

- 创建新文件
- 修改现有业务代码
- 修改 `AGENTS.md` 或 `docs/` 中的规则和描述
- 安装新依赖
- 修改配置文件

## 需要用户确认的操作（禁止自行执行）

- 删除文件或目录
- 修改 `.env`、credentials 或密钥相关文件
- 执行 git push、git reset --hard、git rebase
- 修改 CI/CD 配置
- 修改数据库 migration 中的 DROP 操作
- 任何影响生产环境的操作
- 修改项目的权限、认证或安全相关逻辑

遇到不确定归属哪一级的操作时，默认按高一级处理。
