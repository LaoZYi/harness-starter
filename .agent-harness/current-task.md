# Current Task

## 状态：待验证

## 任务目标
修复深度分析发现的全部问题（16 项），按优先级从高到低执行。

## 完成步骤
- [x] 创建 `_shared.py` 共享模块（打破循环导入、统一 slugify/正则/守卫）
- [x] 修复 `_merge3.py` CRLF 静默丢数据 + 行尾拼接 bug
- [x] 修复 `_merge3.py` 预存在冲突标记检测
- [x] 修复 shell 注入（settings.json.tmpl + initializer.py）
- [x] 修复 symlink 跟随（initializer.py + init_flow.py）
- [x] 修复 `git add -A` 过宽（cli.py 精确暂存）
- [x] 更新所有模块导入为 _shared（打破循环导入）
- [x] 修复 upgrade.py 双重渲染 + 升级事务标记
- [x] 扩展 verify_upgrade 扫描范围
- [x] 修复 cli_utils.py 类型标注
- [x] 修复 stats.py 双重 resolve
- [x] 修复 templating.py 缺 key 静默空串（改为 warning 日志）
- [x] 加强测试断言（test_merge3 + test_apply_upgrade）
- [x] 修复文档数字不一致
- [x] 运行 make check + make test 确认无回归 → 113 测试全部通过
