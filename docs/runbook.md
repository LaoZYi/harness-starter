# 运行手册

## 常用命令

- `make check`：校验框架仓库结构、模板入口和 Python 语法。
- `make test`：运行框架级回归测试。
- `make ci`：串联 `check` 和 `test`。
- `make discover TARGET=/path/to/repo`：扫描目标项目。
- `make init TARGET=/path/to/repo ARGS="..."`：初始化目标项目。

## 直接运行脚本

```bash
python scripts/discover_project.py /path/to/repo
python scripts/init_project.py --target /path/to/repo
```

## 初始化建议流程

1. 先跑 `scripts/discover_project.py` 看预填信息。
2. 再运行 `scripts/init_project.py`，补充项目目标、命令和部署信息。
3. 初始化后进入目标项目，检查生成的 `AGENTS.md`、`docs/` 和 `.agent-harness/project.json`。

## 常见问题

1. 初始化时很多文件被跳过
   默认不会覆盖已有文件；如果确认需要覆盖，请加 `--force`。
2. 探测结果不准确
   这属于框架允许的情况，初始化阶段应该人工确认关键字段。
3. 新项目类型不适配
   先补 `presets/`，再补模板和测试。
