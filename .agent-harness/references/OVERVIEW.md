# References 导航

## 职责

承载本项目的 L2 温知识——与代码强相关的专业领域检查清单。不在 L0/L1 默认加载，AI 判断当前任务涉及对应领域时用 `/recall --refs <关键词>` 按需打开，或直接 grep。

## 关键文件

- `accessibility-checklist.md` — WCAG 2.1 AA：键盘导航、屏幕阅读器、颜色对比度、表单标签
- `context-degradation-patterns.md` — Context 5 类 attention 诊断模式（lost-in-middle / poisoning / distraction / confusion / clash），context-budget 的诊断侧
- `performance-checklist.md` — Core Web Vitals（LCP / INP / CLS）+ 前后端性能反模式
- `requirement-mapping-checklist.md` — R-ID 贯穿 `/spec` → `/write-plan` → `/verify` 的三元映射
- `security-checklist.md` — OWASP Top 10 + 认证 / 加密 / CORS / 敏感数据日志
- `testing-patterns.md` — AAA / given-when-then / 合约测试 / 夹具策略
- `squad-channel.md` — /lfg squad 通道完整工作流(从主模板抽出,含 6 个介入点 / 4 种拓扑模板 / 失败兜底矩阵)

## 触发场景

| 当前任务涉及 | 先读这份 checklist |
|---|---|
| UI / 前端交互 | `accessibility-checklist.md` + `performance-checklist.md` |
| API / 后端接口 | `security-checklist.md` |
| 写测试或改测试策略 | `testing-patterns.md` |
| 规划含多需求的任务 | `requirement-mapping-checklist.md` |
| 进入 /lfg squad 通道(超大-可并行任务) | `squad-channel.md` |
| AI 长会话退化(明明有却忽略 / 反复引错 / 多任务串味) | `context-degradation-patterns.md` |

## 使用方式

```
/recall CORS --refs       # 找 security-checklist 的 CORS 节
/recall LCP --refs        # 找 performance-checklist 的 LCP 节
/recall --refs --all      # 列全部节摘要
```

## 扩展

新增自定义 checklist 放到本目录下，命名遵循 `<主题>-checklist.md` 或 `<主题>-patterns.md`，并在本文件的关键文件列表里补一行。更新后 `/recall --refs` 自动纳入搜索范围。
