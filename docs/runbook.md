# 运行手册

## 常用命令

- `make check`：校验框架仓库结构、模板入口和 Python 语法。
- `make test`：运行框架级回归测试。
- `make ci`：串联 `check` 和 `test`。
- `make discover TARGET=/path/to/repo`：扫描目标项目。
- `make assess TARGET=/path/to/repo`：输出接入评估和建议。
- `make upgrade-plan TARGET=/path/to/repo ARGS="..."`：预览升级会新增和改动哪些文件。
- `make upgrade-apply TARGET=/path/to/repo ARGS="..."`：执行升级并自动备份被覆盖文件。
- `make init TARGET=/path/to/repo ARGS="..."`：初始化目标项目。

## 直接运行脚本

```bash
python scripts/discover_project.py /path/to/repo
python scripts/assess_project.py /path/to/repo
python scripts/plan_upgrade.py --target /path/to/repo
python scripts/apply_upgrade.py --target /path/to/repo
python scripts/init_project.py --target /path/to/repo
python scripts/init_project.py --target /path/to/repo --config examples/init-config.example.json --non-interactive
```

## 初始化建议流程

1. 先跑 `scripts/discover_project.py` 看预填信息。
2. 再跑 `scripts/assess_project.py` 看接入缺口和建议。
3. 如果仓库已经接入过旧版本 harness，先跑 `scripts/plan_upgrade.py` 看哪些文件会变。
4. 如果接受这些变化，再运行 `scripts/apply_upgrade.py`，它会先备份被覆盖文件。
5. 如有需要先用 `--dry-run` 预演初始化结果。
6. 再运行 `scripts/init_project.py`，补充项目目标、命令和部署信息。
7. 初始化后进入目标项目，检查生成的 `AGENTS.md`、`docs/`、`.agent-harness/project.json` 和 `.agent-harness/init-summary.md`。

## 常见问题

1. 初始化时很多文件被跳过
   默认不会覆盖已有文件；如果确认需要覆盖，请加 `--force`。
2. 探测结果不准确
   这属于框架允许的情况，初始化阶段应该人工确认关键字段。
3. 新项目类型不适配
   先补 `presets/`，再补模板和测试。
4. 团队想把初始化参数标准化
   直接维护一个 JSON/TOML 配置文件，并通过 `--config` 执行初始化。
5. 自动升级覆盖了本地自定义内容
   先到 `.agent-harness/backups/<timestamp>/` 找回旧文件，再决定如何合并。
