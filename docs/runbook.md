# 运行手册

## 本地运行

从标准输入读取一条 JSON 工单并输出路由结果：

```bash
printf '{"title":"service down","description":"api is unavailable","customer_tier":"enterprise","channel":"email"}' | make run
```

也可以直接传文件路径：

```bash
PYTHONPATH=src python3 -m ticket_router.cli /path/to/ticket.json
```

输入 JSON 必须包含：

- `title`
- `description`
- `customer_tier`
- `channel`

## 常用命令

- `make check`：校验仓库结构、文档入口和 Python 语法。
- `make test`：运行回归测试。
- `make ci`：串联 `check` 和 `test`。
- `make run`：读取标准输入中的 JSON 并执行一次路由。

## 常见问题

1. `ModuleNotFoundError`
   通常是忘了通过 `make run` 执行，或手动运行时没带 `PYTHONPATH=src`。
2. 输入解析失败
   请确认传入的是合法 JSON，且四个必填字段都存在。
3. 行为和预期不一致
   先检查 `docs/product.md` 是否已经描述了当前规则，再查看 `tests/test_router.py` 是否已有样例。
