---
description: 数据库和数据模型变更约束
paths:
  - "**/migrations/**"
  - "**/models/**"
  - "**/schema/**"
  - "**/entities/**"
---

# 数据库规则

- 禁止在 migration 中执行 DROP TABLE 或 DROP COLUMN，除非用户明确要求并确认数据可丢弃。因为生产环境的数据删除不可逆。
- 每次 migration 必须可回滚。创建 migration 后，验证 up 和 down 都能正常执行。
- 修改表结构时，必须同步更新 `docs/architecture.md` 中的数据模型说明。
- 禁止在业务代码中直接拼接 SQL。使用 ORM 或参数化查询，因为 SQL 注入是 OWASP Top 1 漏洞。
- 新增索引前评估对写入性能的影响。在 `docs/architecture.md` 中记录索引策略。
