# 发布清单

框架发布前，重点是"能否稳定初始化别人项目"和"新功能是否有测试覆盖"。

## 发布前检查

1. `make ci` 是否通过（含 `check` + `lint` + `typecheck` + `skills-lint` + `test`，当前 620 个测试）。
2. `make lint` 无残余 ruff 错误。
3. `make typecheck` 无残余 mypy 错误。
4. `VERSION` 文件是否已 bump。
5. `README.md` 是否准确描述所有命令。
6. `docs/runbook.md` 是否覆盖最新命令。
7. `docs/product.md` 是否反映最新功能清单。
8. `docs/architecture.md` 是否反映最新模块结构。
9. `src/agent_harness/templates/common/` 是否仍然通用，没有带入样例业务。
10. `src/agent_harness/presets/` 是否覆盖当前支持的 9 种项目类型。
11. 在临时目录里跑一次完整的 init + doctor + export + stats 验证。

## 发布动作

1. 说明本次影响了哪些生成文件或探测字段。
2. 说明是否会影响已接入项目的升级策略。
3. 如果修改了模板，附上至少一个生成结果摘要。
4. 如果新增了 CLI 命令，附上命令用法示例。

## 版本号规则

- 修 bug 或补文档：patch（1.0.0 → 1.0.1）
- 新增功能或命令：minor（1.0.0 → 1.1.0）
- 生成文件结构不兼容变更：major（1.0.0 → 2.0.0）
